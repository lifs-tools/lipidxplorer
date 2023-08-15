import logging
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="[%(asctime)s] {%(name)s:%(lineno)d} %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(Path(__file__).stem)
from ms_deisotope import MSFileLoader
from lx.spectraContainer import SurveyEntry, MSMSEntry


#========================

warnings.warn("this whoile module is depriated only use as reference", DeprecationWarning) 

#========================

def spectra_2_df_single(mzml, options, **kwargs):
    time_range = options["timerange"]
    ms1_mass_range = options["MSmassrange"]
    ms2_mass_range = options["MSMSmassrange"]

    polarity = options._data.get("lx2_polarity", None)
    drop_fuzzy = options._data.get("lx2_drop_fuzzy", None)

    include_text = options._data.get("lx2_include_text", None)
    exclude_text = options._data.get("lx2_exclude_text", None)

    spectra_df = path2df(
        mzml, *time_range, *ms1_mass_range, *ms2_mass_range, polarity, **kwargs
    )
    if drop_fuzzy:
        spectra_df = drop_fuzzy(spectra_df)

    if include_text:
        spectra_df = spectra_df.loc[
            spectra_df.filter_string.str.contains(exclude_text)
        ]

    if exclude_text:
        spectra_df = spectra_df.loc[
            ~spectra_df.filter_string.str.contains(exclude_text)
        ]

    return spectra_df


def spectra_2_df(options):
    mzmls = get_mz_ml_paths(options)
    print(mzmls)
    return [spectra_2_df_single(mzml, options) for mzml in mzmls]


def drop_fuzzy(spectra_df):
    fraction_of_average_intensity = 0.1
    spectras_sum_inty = (
        spectra_df.loc[spectra_df.precursor_id.isna()]
        .groupby("scan_id")["inty"]
        .sum()
    )
    sum_inty_mean = spectras_sum_inty.mean()
    spectras_sum_inty = spectras_sum_inty.to_dict()

    to_drop = []
    for (
        scan_id
    ) in spectra_df.scan_id.drop_duplicates():  # this maintains order
        if (
            spectras_sum_inty[scan_id]
            < sum_inty_mean * fraction_of_average_intensity
        ):  # one order
            to_drop.append(scan_id)
        else:
            break

    return spectra_df.loc[~spectra_df.scan_id.isin(to_drop)]


def get_mz_ml_paths(options):
    warnings.warn("use lx1 ref dataframe instead", DeprecationWarning) 
    p = Path(options["importDir"])
    mzmls = list(p.glob("*.[mM][zZ][mM][lL]"))
    if not mzmls:
        log.warning("no mzml files found in {}".format(p))
        log.warning("using all mzXML files in {}".format(p))
        mzmls = list(p.glob("*.[mM][zZ][xX][mM][lL]"))

    return mzmls


def recalibrate_mzs(mzs, cals):
    warnings.warn("use lx1 ref dataframe instead", DeprecationWarning)
    if not cals or mzs.empty:
        return mzs
    cal_matchs = [mzs.loc[mzs.sub(cal).abs().idxmin()] for cal in cals]
    cal_vals = [cal - cal_match for cal, cal_match in zip(cals, cal_matchs)]
    # prefilter
    if not any((v < 0.1 for v in cal_vals)):
        return mzs
    # find near tolerance
    cutoff = mzs.diff(-1).quantile(0.1)
    is_near = [v < cutoff for v in cal_vals]
    if not any(is_near):
        log.info("no valid calibration masses found")
        return mzs

    cal_matchs = [e for e, v in zip(cal_matchs, is_near) if v]
    cal_vals = [e for e, v in zip(cal_vals, is_near) if v]
    log.debug("recalibration info: {'\n'.join(zip(cal_matchs,cal_vals ))}")

    return mzs + np.interp(mzs, cal_matchs, cal_vals)


def find_msmslist(precurmass, precurs, msmslists, tol=0.5):  # tol in daltons
    dist, closest = min(
        (abs(e - precurmass), idx) for idx, e in enumerate(precurs)
    )
    if dist > tol:
        return []
    return msmslists[closest]


def precur_msmslists_from(ms2_df, samples, occupancy=1):
    # TODO Wes McKinney (pandas' author) in Python for Data Analysis, https://stackoverflow.com/questions/14734533/how-to-access-pandas-groupby-dataframe-by-key
    precurs = []
    msmslists = []

    add_group_no_ms2_df(ms2_df, occupancy=occupancy)
    for idx, g_df in ms2_df.groupby(level=0):
        precurs.append(idx)
        msms_list = [
            ms2entry_factory(mass, dictIntensity, samples, polarity)
            for mass, dictIntensity, polarity in mass_inty_generator_prec_ms2(
                g_df
            )
        ]
        msmslists.append(msms_list)
    return precurs, msmslists


def add_group_no_ms2_df(ms2_df, occupancy=1):
    # TODO try add group **after** groupby precursor
    # TODO make generic with add_group_no
    window_size = int(ms2_df.stem_first.nunique())
    ms2_df.set_index(
        pd.RangeIndex(0, ms2_df.shape[0]), append=True, inplace=True
    )
    ms2_df.reset_index(level=1, drop=True, inplace=True)
    ms2_df.sort_values(
        "mz_mean", ascending=False, inplace=True
    )  # decending because interpeak distance is going to zero
    ms2_df["mz_diff"] = ms2_df.sort_values("mz_mean", ascending=False)[
        "mz_mean"
    ].diff(-1)
    ms2_df["cummin"] = (
        ms2_df[ms2_df["mz_diff"] > 0]["mz_diff"]
        .rolling(window_size)
        .mean()
        .cummin()
        .shift(-window_size)
    )  # make the distance monotinoc and with the average and not zero to avoid outliers
    ms2_df["cummin"].ffill(inplace=True)  # fill the blanks from the shift
    ms2_df["mz_diff"].ffill(inplace=True)
    ms2_df["with_next"] = ms2_df["mz_diff"] <= ms2_df["cummin"]
    ms2_df["group_no"] = (
        ms2_df.with_next != ms2_df.with_next.shift()
    ).cumsum()  # add a group for the consecutive close peaks
    ms2_df.loc[
        ~ms2_df.with_next & ms2_df.with_next.shift(), "group_no"
    ] = ms2_df.group_no.shift()  # add the last item in the group_no
    # apply occupancy
    ms2_df.drop(
        ms2_df[
            ms2_df.groupby("group_no")["group_no"].transform("count")
            < window_size * occupancy
        ].index,
        inplace=True,
    )
    # cleanup
    ms2_df.drop("mz_diff cummin with_next".split(), axis=1, inplace=True)
    return None


def path2df(
    path,
    time_start=0,
    time_end=float("inf"),
    ms1_start=0,
    ms1_end=float("inf"),
    ms2_start=0,
    ms2_end=float("inf"),
    polarity=None,
    only_ms1_scans=True,
    only_ms2_scans=False,
):
    dfs = []
    with MSFileLoader(str(path)) as r:
        r.get_scan_by_time(time_start / 60)
        r.start_from_scan(r.get_scan_by_time(time_start / 60).id)
        _categorical_cols = [
            "stem",
            "scan_id",
            "filter_string",
            "precursor_id",
            "precursor_mz",
            "polarity",
        ]
        for b in r:
            if not (time_start / 60 < b.precursor.scan_time < time_end / 60):
                continue
            if polarity and b.precursor.polarity != polarity:
                continue

            if not only_ms2_scans:
                a = b.precursor.arrays
                df = pd.DataFrame(
                    {
                        "mz": a.mz.astype("float32"),
                        "inty": a.intensity.astype("float32"),
                        "stem": path.stem,
                        "scan_id": b.precursor.scan_id,
                        "filter_string": b.precursor.annotations[
                            "filter string"
                        ]
                        if b.precursor.annotations
                        else b.precursor._data["filterLine"],
                        "precursor_id": None,
                        "precursor_mz": 0,
                        "polarity": b.precursor.polarity,
                    }
                )
                df = df[df.mz.between(ms1_start, ms1_end) & df.inty > 0]
                for col in _categorical_cols:
                    df[col] = df[col].astype("category")
                dfs.append(df)
            if only_ms1_scans:
                continue
            for p in b.products:
                if not (time_start / 60 < p.scan_time < time_end / 60):
                    continue
                if not (ms1_start < p.precursor_information.mz < ms1_end):
                    continue
                a = p.arrays
                df = pd.DataFrame(
                    {
                        "mz": a.mz.astype("float32"),
                        "inty": a.intensity.astype("float32"),
                        "stem": path.stem,
                        "scan_id": p.scan_id,
                        "filter_string": p.annotations["filter string"]
                        if p.annotations
                        else p._data["filterLine"],
                        "precursor_id": b.precursor.scan_id,
                        "precursor_mz": p.precursor_information.mz,
                        "polarity": p.polarity,
                    }
                )
                df = df[(df.mz.between(ms2_start, ms2_end)) & df.inty > 0]
                # df["scan_id"] = p.scan_id  # TODO  make them categoriacal?
                # df["filter_string"] = p.annotations["filter string"]
                # df["precursor_id"] = b.precursor.scan_id
                dfs.append(df)
    df = pd.concat(dfs)
    log.info(f"spectra {path.stem}, size: {df.shape}")
    return df


# this code runs slower than add_group_no
# def add_group_no_hdbscan(ms1_peaks, occupancy=0.75, cleanup_cols=True, factor=100):
#     window_size = test_df.scan_id.unique().shape[0]

#     ms1_peaks['n_mz'] = (ms1_peaks['mz'] - ms1_peaks['mz'].min()) / (ms1_peaks['mz'].max() - ms1_peaks['mz'].min())
#     x_unit = ms1_peaks.sort_values('n_mz')['n_mz'].diff().replace(0,np.NAN).quantile(0.5)
#     l_inty = np.log(ms1_peaks['inty'])
#     y_unit = l_inty.sort_values().diff().replace(0,np.NAN).quantile(0.5)
#     ms1_peaks['n_inty'] = l_inty*x_unit/y_unit
#     ms1_peaks['n_mz'] = ms1_peaks['n_mz'] * factor

#     occup = max(int(window_size * occupancy), 2) # min samples to make a clusterer
#     X = ms1_peaks[['n_mz', 'n_inty']].to_numpy()

#     clusterer = hdbscan.hdbscan(X,occup)

#     ms1_peaks['group_no'] = clusterer[0]
#     ms1_peaks['group_prob'] = clusterer[1]
#     # cleanup
#     ms1_peaks.loc[ms1_peaks['group_prob'] < 0.85, 'group_no'] = -1 # these are the cluster outliers we prefer not to have them
#     # test_df['hdbs'].replace(-1, np.NAN).value_counts().max()
#     if cleanup_cols:
#         ms1_peaks.drop("n_mz n_inty group_prob".split(), axis=1, inplace=True)
#     return None


def add_group_no(ms1_peaks, occupancy=0, cleanup_cols=True):
    # TODO do it in memory with pipes?
    window_size = int(ms1_peaks.scan_id.nunique())
    if window_size == 1:
        log.warn("only one scan, no need to group, maybe its Peakstrainer")
        ms1_peaks["group_no"] = ms1_peaks.reset_index().index
        return None

    ms1_peaks.set_index(
        "scan_id", append=True, inplace=True
    )  # avoid duplicdate index error
    ms1_peaks.sort_values(
        "mz", ascending=False, inplace=True
    )  # decending because interpeak distance is going to zero
    ms1_peaks["mz_diff"] = ms1_peaks.sort_values("mz", ascending=False)[
        "mz"
    ].diff(-1)
    ms1_peaks["cummin"] = (
        ms1_peaks[ms1_peaks["mz_diff"] > 0]["mz_diff"]
        .rolling(window_size)
        .mean()
        .cummin()
        .shift(-window_size)
    )  # make the distance monotinoc and with the average and not zero to avoid outliers
    ms1_peaks["cummin"].ffill(inplace=True)  # fill the blanks from the shift
    ms1_peaks["mz_diff"].ffill(inplace=True)
    ms1_peaks["with_next"] = ms1_peaks["mz_diff"] <= ms1_peaks["cummin"]
    ms1_peaks["group_no"] = (
        ms1_peaks.with_next != ms1_peaks.with_next.shift()
    ).cumsum()  # add a group for the consecutive close peaks
    ms1_peaks.loc[
        ~ms1_peaks.with_next & ms1_peaks.with_next.shift(), "group_no"
    ] = ms1_peaks.group_no.shift()  # add the last item in the group_no
    # apply occupancy
    ms1_peaks.drop(
        ms1_peaks[
            ms1_peaks.groupby("group_no")["group_no"].transform("count")
            < window_size * occupancy
        ].index,
        inplace=True,
    )
    if cleanup_cols:
        ms1_peaks.drop(
            "mz_diff cummin with_next".split(), axis=1, inplace=True
        )
    ms1_peaks.reset_index(level=1, inplace=True)

    return None


def add_group_no_ms1_df(ms1_df, occupancy=1):
    # TODO make generic with add_group_no
    window_size = int(ms1_df.stem_first.nunique())
    ms1_df.index.rename("scan_group_no", inplace=True)
    ms1_df.set_index(
        "stem_first", append=True, inplace=True
    )  # avoid duplicdate index error
    ms1_df.sort_values(
        "mz_mean", ascending=False, inplace=True
    )  # decending because interpeak distance is going to zero
    ms1_df["mz_diff"] = ms1_df.sort_values("mz_mean", ascending=False)[
        "mz_mean"
    ].diff(-1)
    ms1_df["cummin"] = (
        ms1_df[ms1_df["mz_diff"] > 0]["mz_diff"]
        .rolling(window_size)
        .mean()
        .cummin()
        .shift(-window_size)
    )  # make the distance monotinoc and with the average and not zero to avoid outliers
    ms1_df["cummin"].ffill(inplace=True)  # fill the blanks from the shift
    ms1_df["mz_diff"].ffill(inplace=True)
    ms1_df["with_next"] = ms1_df["mz_diff"] <= ms1_df["cummin"]
    ms1_df["group_no"] = (
        ms1_df.with_next != ms1_df.with_next.shift()
    ).cumsum()  # add a group for the consecutive close peaks
    ms1_df.loc[
        ~ms1_df.with_next & ms1_df.with_next.shift(), "group_no"
    ] = ms1_df.group_no.shift()  # add the last item in the group_no
    # apply occupancy
    ms1_df.drop(
        ms1_df[
            ms1_df.groupby("group_no")["group_no"].transform("count")
            < window_size * occupancy
        ].index,
        inplace=True,
    )
    # cleanup
    ms1_df.drop("mz_diff cummin with_next".split(), axis=1, inplace=True)
    ms1_df.reset_index(level=1, inplace=True)
    return None


def agg_ms1_spectra_df(df, occupancy=1, calibration=None):
    ms1_peaks = df.loc[df.precursor_id.isna()]
    add_group_no(ms1_peaks, occupancy=occupancy)
    ms1_agg_peaks = ms1_peaks.groupby("group_no").agg(
        {
            "mz": ["count", "mean"],
            "inty": ["mean"],
            "stem": ["first"],
            "scan_id": "nunique",
            "polarity": ["first"],
        }
    )
    ms1_agg_peaks.columns = [
        "_".join(col).strip() for col in ms1_agg_peaks.columns.values
    ]

    if calibration:
        ms1_agg_peaks["mz_mean"] = recalibrate_mzs(
            ms1_agg_peaks["mz_mean"], calibration
        )
    return ms1_agg_peaks


def agg_ms2_spectra_df(df, occupancy=0, calibration=None):
    # TODO try this https://stackoverflow.com/questions/49799731/how-to-get-the-first-group-in-a-groupby-of-multiple-columns
    ms2_peaks = df.loc[~df.precursor_id.isna()]
    add_group_no(ms2_peaks, occupancy=0)  # no occipancy because its done below
    # TODO use https://github.com/mthh/jenkspy instead of rounding or https://github.com/perrygeo/jenks
    # NOTE in peakstrainer ms2 are gruuped by rounded(6 decimal places) precursor
    # NOTE in lx1 the ms2 grouping is base on a rolling avererage, if mean(group) - new_item < window_da, add to group
    ms2_peaks["scan_id_nunique"] = ms2_peaks.groupby(ms2_peaks.precursor_mz)[
        "scan_id"
    ].transform("nunique")
    ms2_agg_peaks = ms2_peaks.groupby(
        [ms2_peaks.precursor_mz.round(2), ms2_peaks.group_no]
    ).agg(  # TODO , as_index=False to removethe group as an index, see https://realpython.com/pandas-groupby/
        {
            "mz": ["count", "mean"],
            "inty": ["mean"],
            "stem": ["first"],
            "scan_id_nunique": "first",
            "polarity": ["first"],
        }
    )
    ms2_agg_peaks.columns = [
        "_".join(col).strip() for col in ms2_agg_peaks.columns.values
    ]
    ms2_agg_peaks.drop(
        ms2_agg_peaks[
            ms2_agg_peaks.mz_count
            < ms2_agg_peaks.scan_id_nunique_first * occupancy
        ].index,
        inplace=True,
    )
    if calibration:
        ms2_agg_peaks["mz_mean"] = recalibrate_mzs(
            ms2_agg_peaks["mz_mean"], calibration
        )

    return ms2_agg_peaks


def mass_inty_generator_ms1(ms1_df, occupancy=1):
    warnings.warn("use lx1 ref masterscan instead", DeprecationWarning)
    add_group_no_ms1_df(ms1_df, occupancy=occupancy)
    for _, df in ms1_df.groupby(ms1_df.group_no):
        msmass = float(df.mz_mean.mean())
        dictIntensity = df.set_index("stem_first")["inty_mean"].to_dict()
        polarity = df.polarity_first.to_list()[0]
        yield msmass, dictIntensity, polarity


def se_factory(msmass, dictIntensity, samples, polarity, massWindow=0):
    warnings.warn("use lx1 ref masterscan instead", DeprecationWarning)
    holder = {s: 0 for s in samples}
    holder.update(dictIntensity)
    se = SurveyEntry(
        msmass=msmass,
        smpl=holder,
        peaks=[],
        charge=None,
        polarity=polarity,
        dictScans={
            s: 1 for s in samples
        },  # needed for the intensity threshold (thrshl / sqrt(nb. of scans))
        msms=None,
        dictBasePeakIntensity={s: 1 for s in samples},
    )
    se.massWindow = (
        massWindow  # used for isotopic c orrection when no resolution is given
    )
    return se


def mass_inty_generator_prec_ms2(g_df):
    for _, inner_gdf in g_df.groupby("group_no"):
        mass = float(inner_gdf.mz_mean.mean())
        dictIntensity = inner_gdf.set_index("stem_first")[
            "inty_mean"
        ].to_dict()
        polarity = inner_gdf.polarity_first.to_list()[0]
        yield mass, dictIntensity, polarity


def ms2entry_factory(mass, dictIntensity, samples, polarity):
    holder = {s: 0 for s in samples}
    holder.update(dictIntensity)
    return MSMSEntry(
        mass=mass,
        dictIntensity=holder,
        peaks=[],
        polarity=polarity,
        charge=None,
        se=None,
        dictScanCount={s: 1 for s in samples},
        dictBasePeakIntensity={s: 1 for s in samples},
    )


def main():
    ''''this whole file is depricated us lx1_red datafram or mastersscan'''
    options = {  # NOTE to initialize Masterscan(options) a dictionalry is not enough
        "importDir": r"D:\fork\lipidxplorer-evaluation\190731_benchmark_data_files_infos\190731_mzML_no_zlib",
        "timerange": (33.0, 1080.0),
        "MSmassrange": (360.0, 1000.0),
        "MSMSmassrange": (150.0, 1000.0),
        "MScalibration": [680.4802],
        "MSMScalibration": None,
    }
    from LX1_masterscan import make_lx_masterscan

    scan = make_lx_masterscan(options, lx_version=2)
    if False:
        import pickle

        with open(options["importDir"] + r"\for_paper_from_df.sc", "wb") as fh:
            pickle.dum(scan, fh)
    return scan
