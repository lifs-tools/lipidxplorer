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
    spectra_dfs = spectra_2_df(options)  # already teim range and mass range filtered

    # agg ms1 per spectra
    ms1_dfs = {}
    for df in spectra_dfs:  # first file, already teim range and mass range filtered
        ms1_peaks = df.loc[df.precursor_id.isna()]
        agg_df = ms1_peaks_agg(ms1_peaks, options)
        agg_df["stem"] = df.stem.iloc[0]
        ms1_dfs[df.stem.iloc[0]] = agg_df

    ms1_agg_peaks = pd.concat(ms1_dfs.values())
    # TODO recalibrate... see code below
    # agg ms1 acrosss spectra
    ms1_agg_peaks = ms1_scans_agg(ms1_agg_peaks, options)
    # ms1_agg_peaks.pivot(index='mass', columns='stem', values=['inty','lx1_bad_inty'])

    ##### agg ms2
    try:
        ms2_peaks = pd.concat((df.loc[~df.precursor_id.isna()] for df in spectra_dfs))
    except ValueError:
        log.info("no ms2 found")

    if not ms2_peaks.empty:
        precursors_df = grouped_precursors_df(ms2_peaks, options)
        precursors_bins = precursors_df.set_index("precursor_mz")["prec_bin"].to_dict()

        ms2_peaks["prec_bin"] = ms2_peaks.precursor_mz.map(precursors_bins)
        grouped_prec = ms2_peaks.groupby(["stem", "prec_bin"])
        ms2_agg_peaks = pd.concat(ms2_peaks_group_generator(grouped_prec, options))
        # TODO # collape_join_adjecent_clusters_msms(cluster)

    # make listSurveyEntry

    samples = [k for k in ms1_dfs.keys()]
    samples.extend([f"{k}_lx2" for k in samples])  # because we add both results
    polarity = spectra_dfs[0].polarity.iat[0]
    # TODO assert there is only one polarity
    listSurveyEntry = [
        se_factory(msmass, dictIntensity, samples, polarity)
        for msmass, dictIntensity, polarity in mass_inty_generator_ms1_agg(
            ms1_agg_peaks, polarity
        )
    ]
    if not ms2_peaks.empty:
        MS1_precurmass = pd.Series(
            [se.precurmass for se in listSurveyEntry], name="MS1_precurmass"
        )
        MS1_precurmass.sort_values(inplace=True)

        if ms2_peaks:
            MS2_dict = dict(MS2_dict_generator(ms2_agg_peaks, samples, polarity))
            MS2_dict_keys = pd.Series(list(MS2_dict.keys()), name="MS2_precurs")
            MS2_dict_keys.sort_values(inplace=True)

        # map ms2 to ms1
        tol = options["selectionWindow"] / 2
        precur_map_df = pd.merge_asof(
            MS1_precurmass,
            MS2_dict_keys,
            left_on="MS1_precurmass",
            right_on="MS2_precurs",
            direction="nearest",
            tolerance=tol,
        )
        precur_dict = precur_map_df.set_index("MS1_precurmass")["MS2_precurs"].to_dict()

        for se in listSurveyEntry:
            precursor = precur_dict[se.precurmass]
            se.listMSMS = MS2_dict.get(precursor, [])

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


############### ms1 agg accross spectra
def bin_mkSurveyLinear(masses, options):
    # TODO assert masses are ordered
    minmass = masses.iloc[0]
    up_to = None
    for _, mass in masses.iteritems():
        if up_to is None:
            # up_to = mass + tolerance.getTinDA(mass) this is how its done in some places, but reuslt are not identical to below
            deltatol = (
                options["MSresolution"].tolerance
                + (mass - minmass) * options["MSresolutionDelta"]
            )
            up_to = mass + (mass / deltatol)
        if mass <= up_to:
            yield up_to
        else:
            deltatol = (
                options["MSresolution"].tolerance
                + (mass - minmass) * options["MSresolutionDelta"]
            )
            up_to = mass + (mass / deltatol)
            yield up_to


def ms1_scans_agg(ms1_agg_peaks, options):
    ms1_agg_peaks.sort_values("mz", inplace=True)

    # binning is done 3 times in lx1, between each fadi filter is performed, we do it at the end intead
    bins1 = list(bin_mkSurveyLinear(ms1_agg_peaks.mz, options))
    bins2 = list(
        bin_mkSurveyLinear(
            ms1_agg_peaks.groupby(bins1)["mz"].transform("mean"), options
        )
    )
    bins3 = list(
        bin_mkSurveyLinear(
            ms1_agg_peaks.groupby(bins2)["mz"].transform("mean"), options
        )
    )

    ms1_agg_peaks["bins"] = bins3

    # check occupation spectracontainer.py masterscan.chekoccupation
    # occupation is the % of peak intensities abvove "thrsld: "
    threshold_denominator = ms1_agg_peaks.stem.unique().shape[0]  # same as len(res)
    threshold = options["MSminOccupation"]
    bin_peak_count = ms1_agg_peaks.groupby("bins")["inty"].transform("count")
    tf_mask = (bin_peak_count / threshold_denominator) >= threshold
    ms1_agg_peaks["above_threshold"] = tf_mask

    ms1_agg_peaks["mass"] = ms1_agg_peaks.groupby("bins")["mz"].transform("mean")
    # TODO collape_join_adjecent_clusters
    return ms1_agg_peaks


################ ms2 agg


def bin_linear_alignment_for_ms2(masses, telerance_da):
    # TODO assert masses are ordered
    up_to = None
    for _, mass in masses.iteritems():
        if up_to is None:
            # up_to = mass + tolerance.getTinDA(mass) this is how its done in some places, but reuslt are not identical to below
            up_to = mass + telerance_da
        if mass <= up_to:
            yield up_to
        else:
            up_to = mass + telerance_da
            yield up_to


def grouped_precursors_df(ms2_peaks, options):
    ms2_peaks.sort_values(["precursor_mz", "mz"], inplace=True)
    precursors_df = ms2_peaks[
        ["stem", "scan_id", "precursor_mz"]
    ].drop_duplicates()  # similar to unqie but return a series instead of an array
    # using "stem", 'scan_id' to replicate the numebr of instances for the averaging later

    bins1 = list(
        bin_linear_alignment_for_ms2(
            precursors_df.precursor_mz, options["selectionWindow"]
        )
    )
    bins2 = list(
        bin_linear_alignment_for_ms2(
            precursors_df.groupby(bins1)["precursor_mz"].transform("mean"),
            options["selectionWindow"],
        )
    )
    bins3 = list(
        bin_linear_alignment_for_ms2(
            precursors_df.groupby(bins2)["precursor_mz"].transform("mean"),
            options["selectionWindow"],
        )
    )

    precursors_df["prec_bin"] = bins3

    # no fadi filter for precursors
    # after groupinbg the precursors, the groups are split on the "sample" ie the file,
    # the each split of the group is merged in the __def mergeListsMsms__ method that uses linear alignment
    # thats why... prec_ms2_peaks = ms2_peaks[(ms2_peaks.precursor_mz == t) & (ms2_peaks.stem == '190321_Serum_Lipidextract_368723_01')]
    return precursors_df


###############ms2 agg across spectra
# this one uses delta res for clustering
def bin_mkSurveyLinear_for_ms2(masses, options):  # copied from above
    # TODO assert masses are ordered
    minmass = masses.iloc[0]
    up_to = None
    for _, mass in masses.iteritems():
        if up_to is None:
            # up_to = mass + tolerance.getTinDA(mass) this is how its done in some places, but reuslt are not identical to below
            deltatol = (
                options["MSMSresolution"].tolerance
                + (mass - minmass) * options["MSMSresolutionDelta"]
            )
            up_to = mass + (mass / deltatol)
        if mass <= up_to:
            yield up_to
        else:
            deltatol = (
                options["MSMSresolution"].tolerance
                + (mass - minmass) * options["MSMSresolutionDelta"]
            )
            up_to = mass + (mass / deltatol)
            yield up_to


def ms2_peaks_group_generator(grouped_prec, options):
    for idx, prec_ms2_peaks in grouped_prec:
        # intensityWeightedAvg
        log.info(f"processing ms2 {idx}")
        prec_ms2_peaks.sort_values("mz", inplace=True)
        bins1 = list(bin_mkSurveyLinear_for_ms2(prec_ms2_peaks.mz, options))
        bins1_weighted_average = (prec_ms2_peaks.mz * prec_ms2_peaks.inty).groupby(
            bins1
        ).transform("sum") / prec_ms2_peaks.inty.groupby(bins1).transform("sum")
        bins2 = list(bin_mkSurveyLinear_for_ms2(bins1_weighted_average, options))
        bins2_weighted_average = (prec_ms2_peaks.mz * prec_ms2_peaks.inty).groupby(
            bins2
        ).transform("sum") / prec_ms2_peaks.inty.groupby(bins2).transform("sum")
        bins3 = list(bin_mkSurveyLinear_for_ms2(bins2_weighted_average, options))
        weighted_mass = (prec_ms2_peaks.mz * prec_ms2_peaks.inty).groupby(
            bins3
        ).transform("sum") / prec_ms2_peaks.inty.groupby(bins3).transform("sum")

        prec_ms2_peaks["bins"] = bins3
        prec_ms2_peaks["weighted_mass"] = weighted_mass

        fadi_denominator = prec_ms2_peaks.scan_id.unique().shape[0]
        ff_mask = (
            prec_ms2_peaks.groupby("bins")["bins"].transform("count") / fadi_denominator
            >= options["MSMSfilter"]
        )
        mof_mask = (
            prec_ms2_peaks.groupby("bins")["bins"].transform("count") / fadi_denominator
            >= options["MSMSminOccupation"]
        )

        tf_mask = prec_ms2_peaks.inty > options["MSMSthreshold"]

        # it uses merge sum intensity for getting the averrage intensity...
        agg_prec_ms2_peaks = (
            prec_ms2_peaks[ff_mask & tf_mask & mof_mask]
            .groupby("bins")
            .agg({"weighted_mass": ["mean", "count"], "inty": "mean"})
        )
        agg_prec_ms2_peaks["precursor_mz"] = prec_ms2_peaks.precursor_mz.mean().round(6)
        # there is minor differrence in mean between different files, and the same precursor bin, to avoid it we round

        agg_prec_ms2_peaks["stem"] = idx[0]

        agg_prec_ms2_peaks.columns = [
            "_".join(col).strip() for col in agg_prec_ms2_peaks.columns.values
        ]
        names = {
            "weighted_mass_mean": "mz",
            "weighted_mass_count": "count",
            "inty_mean": "inty",
            "precursor_mz_": "precursor_mz",
            "stem_": "stem",
        }
        agg_prec_ms2_peaks.rename(columns=names, inplace=True)

        yield agg_prec_ms2_peaks


# #recalibrate
# def recalibrate_mzs(mzs, cals):
#     # from lx2_masterscan
#     # lx1 takes all that are within tolerance and then uses highest intensity
#     if not cals or mzs.empty:
#         return mzs
#     cal_matchs = [mzs.loc[mzs.sub(cal).abs().idxmin()] for cal in cals]

#     cal_vals = [cal - cal_match for cal, cal_match in zip(cals, cal_matchs)]
#     # prefilter
#     if not any((v < 0.1 for v in cal_vals)):
#         return mzs
#     # find near tolerance
#     cutoff = mzs.diff(-1).quantile(0.1)
#     is_near = [v < cutoff for v in cal_vals]
#     if not any(is_near):
#         log.info("no valid calibration masses found")
#         return mzs

#     cal_matchs = [e for e, v in zip(cal_matchs, is_near) if v]
#     cal_vals = [e for e, v in zip(cal_vals, is_near) if v]
#     log.debug("recalibration info: {'\n'.join(zip(cal_matchs,cal_vals ))}")

#     return mzs + np.interp(mzs, cal_matchs, cal_vals)


###################### build masterscan
def mass_inty_generator_ms1_agg(ms1_agg_peaks, polarity):
    for mass, gdf in ms1_agg_peaks.groupby("mass"):
        dictIntensity = gdf.set_index("stem")["lx1_bad_inty"].to_dict()
        dictIntensity_lx2 = gdf.set_index("stem")["inty"].to_dict()
        dictIntensity.update({f"{k}_lx2": v for k, v in dictIntensity_lx2.items()})
        yield (mass, dictIntensity, polarity)


def MSMSEntry_list_generator(gdf, samples, polarity):
    for mz, precur_df in gdf.groupby("mz"):
        dictIntensity = precur_df.set_index("stem")["inty"].to_dict()
        dictIntensity.update(
            {f"{k}_lx2": v for k, v in dictIntensity.items()}
        )  # TODO actually get other values
        # TODO samples should be dictIntensity.keys()?
        yield (mz, dictIntensity, samples, polarity)


def MS2_dict_generator(ms2_agg_peaks, samples, polarity):
    for precursor_mz, gdf in ms2_agg_peaks.groupby("precursor_mz"):
        log.info(f"collecting ms2 {precursor_mz}")
        MSMSEntry_list = [
            ms2entry_factory(*args)
            for args in MSMSEntry_list_generator(gdf, samples, polarity)
        ]
        yield (precursor_mz, MSMSEntry_list)


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

