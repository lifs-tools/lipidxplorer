from pathlib import Path
import pandas as pd
import numpy as np
import logging, sys

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="[%(asctime)s] {%(name)s:%(lineno)d} %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(Path(__file__).stem)
from lx.spectraContainer import MasterScan, SurveyEntry, MSMSEntry
from ms_deisotope import MSFileLoader


def make_lx2_masterscan(options) -> MasterScan:
    log.info("Generating Masterscan from LX2 data")

    mzmls = mzml_paths(options)
    samples = [p.stem for p in mzmls]
    log.info("for the files... \n{}".format("\n".join(samples)))

    spectra_dfs = spectra_2_df(options)

    ms1_calibration = options._data.get(
        "MScalibration"
    )  # from _data otherwise missing value error
    ms2_calibration = options._data.get("MSMScalibration")

    if ms1_calibration and not ms2_calibration:
        log.warn("Using MS1 calibration on MS2 also")
        ms2_calibration = ms1_calibration

    occup_between_scans = options["MSfilter"]
    ms1_df = pd.concat(
        (
            agg_ms1_spectra_df(
                df, occupancy=occup_between_scans, calibration=ms1_calibration
            )
            for df in spectra_dfs
        )
    )
    occup_between_spectra = options["MSminOccupation"]
    listSurveyEntry = [
        se_factory(msmass, dictIntensity, samples)
        for msmass, dictIntensity in mass_inty_generator_ms1(
            ms1_df, occupancy=occup_between_spectra
        )
    ]

    occup_between_ms2_scans = options["MSMSfilter"]
    ms2_df = pd.concat(
        (
            agg_ms2_spectra_df(
                df, occupancy=occup_between_ms2_scans, calibration=ms2_calibration
            )
            for df in spectra_dfs
        )
    )
    occup_between_ms2_spectra = options["MSMSminOccupation"]
    precurs, msmslists = precur_msmslists_from(
        ms2_df, samples, occup_between_ms2_spectra
    )

    for se in listSurveyEntry:
        se.listMSMS = find_msmslist(se.precurmass, precurs, msmslists)

    # add data to masterscan
    scan = MasterScan(options)
    scan.listSurveyEntry = listSurveyEntry
    scan.listSurveyEntry[0].massWindow = 0.01  # to avoid bug

    # for printing we need
    scan.listSamples = samples
    return scan


def spectra_2_df(options):
    mzmls = mzml_paths(options)

    time_range = options["timerange"]
    ms1_mass_range = options["MSmassrange"]
    ms2_mass_range = options["MSMSmassrange"]

    # generaste ms1 data
    spectra_dfs = [
        path2df(mzml, *time_range, *ms1_mass_range, *ms2_mass_range) for mzml in mzmls
    ]

    return spectra_dfs


def mzml_paths(options):
    p = Path(options["importDir"])
    mzmls = list(p.glob("*.mzml"))
    return mzmls


def recalibrate_mzs(mzs, cals):
    if not cals:
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
    dist, closest = min((abs(e - precurmass), idx) for idx, e in enumerate(precurs))
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
            ms2entry_factory(*e, samples) for e in mass_inty_generator_prec_ms2(g_df)
        ]
        msmslists.append(msms_list)
    return precurs, msmslists


def add_group_no_ms2_df(ms2_df, occupancy=1):
    # TODO try add group **after** groupby precursor
    # TODO make generic with add_group_no
    window_size = int(ms2_df.stem_first.nunique())
    ms2_df.set_index(pd.RangeIndex(0, ms2_df.shape[0]), append=True, inplace=True)
    ms2_df.reset_index(level=1, drop=True, inplace=True)
    ms2_df.sort_values(
        "mz_mean", ascending=False, inplace=True
    )  # decending because interpeak distance is going to zero
    ms2_df["mz_diff"] = ms2_df.sort_values("mz_mean", ascending=False)["mz_mean"].diff(
        -1
    )
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
):
    dfs = []
    with MSFileLoader(str(path)) as r:
        r.get_scan_by_time(time_start / 60)
        r.start_from_scan(r.get_scan_by_time(time_start / 60).id)
        for b in r:
            if not (time_start / 60 < b.precursor.scan_time < time_end / 60):
                continue
            a = b.precursor.arrays
            df = pd.DataFrame(
                {
                    "mz": a.mz,
                    "inty": a.intensity,
                    "stem": path.stem,
                    "scan_id": b.precursor.scan_id,
                    "filter_string": b.precursor.annotations["filter string"],
                    "precursor_id": np.nan,
                    "precursor_mz": np.nan,
                }
            )
            df = df[(df.mz.between(ms1_start, ms1_end)) & (df.inty > 0)]
            # df["scan_id"] = b.precursor.scan_id
            # df["filter_string"] = b.precursor.annotations["filter string"]
            # df["precursor_id"] = np.nan
            dfs.append(df)
            for p in b.products:
                if not (time_start / 60 < p.scan_time < time_end / 60):
                    continue
                a = p.arrays
                df = pd.DataFrame(
                    {
                        "mz": a.mz,
                        "inty": a.intensity,
                        "stem": path.stem,
                        "scan_id": p.scan_id,
                        "filter_string": p.annotations["filter string"],
                        "precursor_id": b.precursor.scan_id,
                        "precursor_mz": p.precursor_information.mz,
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


def add_group_no(ms1_peaks, occupancy=1, cleanup_cols=True):
    # TODO do it in memory with pipes?
    window_size = int(ms1_peaks.scan_id.nunique())
    ms1_peaks.set_index(
        "scan_id", append=True, inplace=True
    )  # avoid duplicdate index error
    ms1_peaks.sort_values(
        "mz", ascending=False, inplace=True
    )  # decending because interpeak distance is going to zero
    ms1_peaks["mz_diff"] = ms1_peaks.sort_values("mz", ascending=False)["mz"].diff(-1)
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
        ms1_peaks.drop("mz_diff cummin with_next".split(), axis=1, inplace=True)
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
    ms1_df["mz_diff"] = ms1_df.sort_values("mz_mean", ascending=False)["mz_mean"].diff(
        -1
    )
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
        }
    )
    ms2_agg_peaks.columns = [
        "_".join(col).strip() for col in ms2_agg_peaks.columns.values
    ]
    ms2_agg_peaks.drop(
        ms2_agg_peaks[
            ms2_agg_peaks.mz_count < ms2_agg_peaks.scan_id_nunique_first * occupancy
        ].index,
        inplace=True,
    )
    if calibration:
        ms2_agg_peaks["mz_mean"] = recalibrate_mzs(
            ms2_agg_peaks["mz_mean"], calibration
        )

    return ms2_agg_peaks


def mass_inty_generator_ms1(ms1_df, occupancy=1):
    add_group_no_ms1_df(ms1_df, occupancy=occupancy)
    for _, df in ms1_df.groupby(ms1_df.group_no):
        msmass = df.mz_mean.mean().item()
        dictIntensity = df.set_index("stem_first")["inty_mean"].to_dict()
        yield msmass, dictIntensity


def se_factory(msmass, dictIntensity, samples):
    holder = {s: 0 for s in samples}
    holder.update(dictIntensity)
    return SurveyEntry(
        msmass=msmass,
        smpl=holder,
        peaks=[],
        charge=None,
        polarity=1,
        dictScans={
            s: 1 for s in samples
        },  # needed for the intensity threshold (thrshl / sqrt(nb. of scans))
        msms=None,
        dictBasePeakIntensity={s: 1 for s in samples},
    )


def mass_inty_generator_prec_ms2(g_df):
    for _, inner_gdf in g_df.groupby("group_no"):
        mass = inner_gdf.mz_mean.mean().item()
        dictIntensity = inner_gdf.set_index("stem_first")["inty_mean"].to_dict()
        yield mass, dictIntensity


def ms2entry_factory(mass, dictIntensity, samples):
    holder = {s: 0 for s in samples}
    holder.update(dictIntensity)
    return MSMSEntry(
        mass=mass,
        dictIntensity=holder,
        peaks=[],
        polarity=1,
        charge=None,
        se=None,
        dictScanCount={s: 1 for s in samples},
        dictBasePeakIntensity={s: 1 for s in samples},
    )


def main():
    options = {  # NOTE to initialize Masterscan(options) a dictionalry is not enough
        "importDir": r"D:\fork\lipidxplorer-evaluation\190731_benchmark_data_files_infos\190731_mzML_no_zlib",
        "timerange": (33.0, 1080.0),
        "MSmassrange": (360.0, 1000.0),
        "MSMSmassrange": (150.0, 1000.0),
        "MScalibration": [680.4802],
        "MSMScalibration": None,
    }
    scan = make_lx2_masterscan(options)
    if False:
        import pickle

        with open(options["importDir"] + r"\for_paper_from_df.sc", "wb") as fh:
            pickle.dum(scan, fh)
    return scan
