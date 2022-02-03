from collections import defaultdict
from pathlib import Path
import pandas as pd
import numpy as np
from lx.spectraContainer import MasterScan, SurveyEntry, MSMSEntry
from ms_deisotope import MSFileLoader


def make_lx2_masterscan(options) -> MasterScan:
    p = Path(options["importDir"])
    mzmls = list(p.glob("*.mzml"))
    samples = [p.stem for p in mzmls]

    time_range = options["timerange"]
    ms1_mass_range = options["MSmassrange"]
    ms2_mass_range = options["MSMSmassrange"]

    # generaste ms1 data
    spectra_dfs = [
        path2df(mzml, *time_range, *ms1_mass_range, *ms2_mass_range) for mzml in mzmls
    ]

    ms1_df = pd.concat((agg_ms1_spectra_df(df) for df in spectra_dfs))
    listSurveyEntry = [
        se_factory(msmass, dictIntensity, samples)
        for msmass, dictIntensity in mass_inty_generator_ms1(ms1_df)
    ]

    # generate ms2 data and add to ms1
    ms2_df = pd.concat((agg_ms2_spectra_df(df) for df in spectra_dfs))

    precurs, msmslists = precur_msmslists_from(ms2_df, samples)

    for se in listSurveyEntry:
        se.listMSMS = find_msmslist(se.precurmass, precurs, msmslists)

    # add data to masterscan
    scan = MasterScan(options)
    scan.listSurveyEntry = listSurveyEntry
    scan.listSurveyEntry[0].massWindow = 0.01  # to avoid bug

    # for printing we need
    scan.listSamples = samples

    return scan


def find_msmslist(precurmass, precurs, msmslists, tol=0.5):  # tol in daltons
    dist, closest = min((abs(e - precurmass), idx) for idx, e in enumerate(precurs))
    if dist > tol:
        return []
    return msmslists[closest]


def precur_msmslists_from(ms2_df, samples):
    # TODO Wes McKinney (pandas' author) in Python for Data Analysis, https://stackoverflow.com/questions/14734533/how-to-access-pandas-groupby-dataframe-by-key
    precurs = []
    msmslists = []
    for idx, g_df in ms2_df.groupby(level=0):
        precurs.append(idx)
        msms_list = [
            ms2entry_factory(*e, samples) for e in mass_inty_generator_prec_ms2(g_df)
        ]
        msmslists.append(msms_list)
    return precurs, msmslists


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

    return df


def add_group_no(ms1_peaks):
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
    ms1_peaks["with_next"] = ms1_peaks["mz_diff"] < ms1_peaks["cummin"]
    ms1_peaks["group_no"] = (
        ms1_peaks.with_next != ms1_peaks.with_next.shift()
    ).cumsum()  # add a group for the consecutive close peaks
    ms1_peaks.loc[
        ~ms1_peaks.with_next & ms1_peaks.with_next.shift(), "group_no"
    ] = ms1_peaks.group_no.shift()  # add the last item in the group_no
    # cleanup
    ms1_peaks.drop("mz_diff cummin with_next".split(), axis=1, inplace=True)
    ms1_peaks.reset_index(level=1, inplace=True)
    return None


def agg_ms1_spectra_df(df):
    ms1_peaks = df.loc[df.precursor_id.isna()]
    add_group_no(ms1_peaks)
    ms1_agg_peaks = ms1_peaks.groupby("group_no").agg(
        {
            "mz": ["count", "mean"],
            "inty": ["mean"],
            "stem": ["first"],
            "scan_id": "nunique",
        }
    )
    ms1_agg_peaks = ms1_agg_peaks.loc[ms1_agg_peaks.mz["count"] > 1]
    ms1_agg_peaks.columns = [
        "_".join(col).strip() for col in ms1_agg_peaks.columns.values
    ]
    process_agg_ms1_spectra(ms1_agg_peaks)
    return ms1_agg_peaks


def process_agg_ms1_spectra(ms1_agg_peaks):
    return ms1_agg_peaks.loc[ms1_agg_peaks.mz_count > 1]


def agg_ms2_spectra_df(df):
    # TODO try this https://stackoverflow.com/questions/49799731/how-to-get-the-first-group-in-a-groupby-of-multiple-columns
    ms2_peaks = df.loc[~df.precursor_id.isna()]
    add_group_no(ms2_peaks)
    ms2_agg_peaks = ms2_peaks.groupby(
        [ms2_peaks.precursor_mz.round(2), ms2_peaks.group_no]
    ).agg(  # TODO , as_index=False to removethe group as an index, see https://realpython.com/pandas-groupby/
        {
            "mz": ["count", "mean"],
            "inty": ["mean"],
            "stem": ["first"],
            "scan_id": "nunique",
        }
    )
    ms2_agg_peaks.columns = [
        "_".join(col).strip() for col in ms2_agg_peaks.columns.values
    ]

    ms2_agg_peaks = process_agg_ms2_spectra(ms2_agg_peaks)
    return ms2_agg_peaks


def process_agg_ms2_spectra(ms2_agg_peaks):
    ms2_agg_peaks = ms2_agg_peaks.loc[
        ms2_agg_peaks.mz_count > 1
    ]  # TODO does this always make sence
    # split ms2_agg_peaks.loc[ ms2_agg_peaks.mz_count - ms2_agg_peaks.scan_id_nunique > 0] # there are more peaks than scans
    return ms2_agg_peaks


def mass_inty_generator_ms1(ms1_df):
    for idx, df in ms1_df.groupby(ms1_df.index):
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
    for inner_idx, inner_gdf in g_df.groupby(level="group_no"):
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
    }
    scan = make_lx2_masterscan(options)
    if False:
        import pickle

        with open(options["importDir"] + r"\for_paper_from_df.sc", "wb") as fh:
            pickle.dum(scan, fh)
    return scan


if __name__ == "__main__":
    from time import perf_counter

    st = perf_counter()
    main()
    print(perf_counter - st)
