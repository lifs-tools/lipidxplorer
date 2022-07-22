from pathlib import Path
import pandas as pd
import logging, sys

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="[%(asctime)s] {%(name)s:%(lineno)d} %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(Path(__file__).stem)

from LX2_masterscan import mz_ml_paths, spectra_2_df
from lx.spectraContainer import MasterScan
from LX2_masterscan import se_factory, ms2entry_factory


def make_lx1_masterscan(options) -> MasterScan:
    # get spectra
    spectra_dfs = spectra_2_df(options)

    # agg ms1
    ms1_dfs = {}
    for df in spectra_dfs:  # first file, already teim range and mass range filtered
        ms1_peaks = df.loc[df.precursor_id.isna()]
        agg_df = ms1_peaks_agg(ms1_peaks, options)
        agg_df["stem"] = df.stem.iloc[0]
        ms1_dfs[df.stem.iloc[0]] = agg_df

    # agg ms2

    # map ms2 to ms1

    # make listSurveyEntry

    samples = [ms1_dfs.keys()]
    samples.extend([f"{k}_lx2" for k in samples])  # because we add both results
    return build_masterscan(options, listSurveyEntry, samples)


############################################ ms1 agg


def bin_linear_alignment(masses, options):
    # TODO assert masses are ordered
    up_to = None
    for _, mass in masses.iteritems():
        if up_to is None:
            # up_to = mass + tolerance.getTinDA(mass) this is how its done in some places, but reuslt are not identical to below
            up_to = mass + mass / options["MSresolution"].tolerance
        if mass <= up_to:
            yield up_to
        else:
            up_to = mass + mass / options["MSresolution"].tolerance
            yield up_to


def ms1_peaks_agg(ms1_peaks, options):
    ms1_peaks.sort_values("mz", inplace=True)

    # binning is done 3 times in lx1, between each fadi filter is performed, we do it at the end intead
    bins1 = list(bin_linear_alignment(ms1_peaks.mz, options))
    bins2 = list(
        bin_linear_alignment(ms1_peaks.groupby(bins1)["mz"].transform("mean"), options)
    )
    bins3 = list(
        bin_linear_alignment(ms1_peaks.groupby(bins2)["mz"].transform("mean"), options)
    )

    ms1_peaks["bin_mass"] = bins3

    # merge mutiple peaks from single scan
    g = ms1_peaks.groupby(["bin_mass", "scan_id"])
    ms1_peaks["scan_cumcount"] = g.cumcount()
    ms1_peaks["merged_mass"] = g["mz"].transform("mean")
    ms1_peaks["merged_inty"] = g["inty"].transform(
        "mean"
    )  # NOTE merge is NOT weighted average

    # aggregate results
    agg_df = (
        ms1_peaks.loc[
            ms1_peaks.scan_cumcount == 0
        ]  # use only the first of merged masses
        .assign(
            mass_intensity=lambda x: x.mz * x.merged_inty
        )  # for the weighted average intensity
        .groupby("bin_mass")
        .agg(
            {
                "merged_mass": ["mean", "count"],
                "merged_inty": ["mean", "sum"],
                "mass_intensity": "sum",
            }
        )
        .dropna()
    )
    agg_df.columns = ["_".join(col).strip() for col in agg_df.columns.values]

    # apply fadi filters, in lx1 its done between each bin  process
    fadi_denominator = ms1_peaks.scan_id.unique().shape[0]
    mask_ff = agg_df.merged_mass_count / fadi_denominator >= options["MSfilter"]
    agg_df = agg_df[mask_ff]

    # NOTE intensity threshold is do in add_Sample... but lets do it here
    MSthreshold = options["MSthreshold"]
    mask_inty = agg_df.merged_inty_mean > MSthreshold
    agg_df = agg_df[mask_inty]

    # for reference...weigted_mass shoud not be necesary
    agg_df["weigted_mass"] = agg_df.mass_intensity_sum / agg_df.merged_inty_sum
    # lx1 intensity is wrong because it uses the total number of scans, instead of the numebr of scans with a peak
    agg_df["lx1_bad_inty"] = agg_df.merged_inty_sum / fadi_denominator

    agg_df.rename(
        columns={"merged_mass_mean": "mz", "merged_inty_mean": "inty"}, inplace=True
    )
    return agg_df


################ ms2 agg


def build_masterscan(options, listSurveyEntry, samples):
    scan = MasterScan(options)
    scan.listSurveyEntry = listSurveyEntry
    scan.listSurveyEntry[0].massWindow = 0.01  # to avoid bug
    scan.sampleOccThr["MS"] = [(0.0, [])]  # to avoid bug at def checkOccupation
    scan.sampleOccThr["MSMS"] = [(0.0, [])]

    # for printing we need
    # samples.extend([f'{k}_lx2' for k in samples])
    scan.listSamples = samples
    return scan


if __name__ == "__main__":
    import pickle

    with open("optoins.pkl", "rb") as f:
        options = pickle.load(f)

    masterscan = make_lx1_masterscan(options)
    with open("tmp_lx1_and_lx2.sc", "wb") as f:
        pickle.dump(masterscan, f)

