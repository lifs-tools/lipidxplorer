from pathlib import Path
import pandas as pd
import numpy as np
import logging, sys
from collections import OrderedDict

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
    options["lx2_polarity"] = None  # to select scans by polaority
    options[
        "lx2_drop_fuzzy"
    ] = None  # to drop the first few MS1 scans that dont have at least 10% of the average intensity
    options["lx2_include_text"] = None  # all scans should include this text
    options["lx2_exclude_text"] = None  # all scans should exlude this text

    spectra_dfs = spectra_2_df(options)  # already teim range and mass range filtered
    polarity = spectra_dfs[0].polarity.iat[0]

    # suggested_selection_window = suggest_selection_window(spectra_dfs[0])

    # agg ms1 per spectra
    use_lx2 = options._data.get("MSresolution") is None
    ms1_dfs = {}
    for df in spectra_dfs:  # first file, already teim range and mass range filtered
        ms1_peaks = df.loc[df.precursor_id.isna()]
        agg_df = (
            ms1_peaks_agg(ms1_peaks, options)
            if not use_lx2
            else ms1_peaks_agg_lx2(ms1_peaks, options)
        )
        agg_df["stem"] = df.stem.iloc[0]
        ms1_dfs[df.stem.iloc[0]] = agg_df

    if options._data.get("MScalibration"):
        for ms1_df in ms1_dfs.values():
            cal_matchs, cal_vals = recalibration_values(ms1_df, options)
            if cal_matchs and cal_vals:
                ms1_df.mz = ms1_df.mz + np.interp(ms1_df.mz, cal_matchs, cal_vals)

    ms1_agg_peaks = pd.concat(ms1_dfs.values())
    # agg ms1 acrosss spectra
    ms1_agg_peaks = (
        ms1_scans_agg(ms1_agg_peaks, options)
        if not use_lx2
        else ms1_scans_agg_lx2(ms1_agg_peaks, options)
    )
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
        grouped_prec = ms2_peaks.groupby("prec_bin")
        ms2_agg_peaks = pd.concat(ms2_peaks_group_generator(grouped_prec, options))

        # TODO recalibrate
        # TODO # collape_join_adjecent_clusters_msms(cluster)

    # make listSurveyEntry

    samples = [k for k in ms1_dfs.keys()]
    # samples.extend([f"{k}_lx2" for k in samples])  # because we add both results
    samples = sorted(samples)
    polarity = int(spectra_dfs[0].polarity.iat[0])
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
    bins3 = make_lx1_bins(ms1_peaks, options)

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
    # agg_df["lx1_bad_inty"] = agg_df.merged_inty_sum / fadi_denominator

    agg_df.rename(
        columns={"weigted_mass": "mz", "merged_inty_mean": "inty"}, inplace=True
    )
    return agg_df


def make_lx1_bins(ms1_peaks, options):
    ms1_peaks.sort_values("mz", inplace=True)

    # binning is done 3 times in lx1, between each fadi filter is performed, we do it at the end intead
    bins1 = list(bin_linear_alignment(ms1_peaks.mz, options))
    bins2 = list(
        bin_linear_alignment(ms1_peaks.groupby(bins1)["mz"].transform("mean"), options)
    )
    bins3 = list(
        bin_linear_alignment(ms1_peaks.groupby(bins2)["mz"].transform("mean"), options)
    )

    return bins3


def get_collapsable_bins(
    df, accross_column="scan_id", cluster_column="bin_mass", close_enogh=0.001
):
    df["accross_column_f"] = df[accross_column].factorize()[0]
    grouped = df.groupby(cluster_column)
    grouped_stats = grouped.agg({"mz": ["max", "min", "std"]})
    close_mz = grouped_stats[("mz", "min")] - grouped_stats[("mz", "max")].shift(
        -1
    ) < grouped_stats[("mz", "std")] + grouped_stats[("mz", "std")].shift(-1)
    close_enough_mz = (
        grouped_stats[("mz", "min")] - grouped_stats[("mz", "max")].shift(-1)
        < close_enogh
    )

    close_mz = close_mz | close_enough_mz

    close_mz_groups = close_mz[close_mz | close_mz.shift(1)].index.to_numpy()
    close_sets = (
        df.loc[df[cluster_column].isin(close_mz_groups)]
        .groupby(cluster_column)["accross_column_f"]
        .apply(lambda s: set(s))
    )

    collapsable_map = {}
    prev_set = set()
    prev_idx = 0
    merging = False
    for idx, curr_set in close_sets.iteritems():
        if (
            close_mz[prev_idx]
            and (idx - prev_idx <= 1 or merging)
            and not curr_set.intersection(prev_set)
        ):
            collapsable_map[idx] = prev_idx
            prev_set.update(curr_set)
            merging = True
            continue
        prev_idx = idx
        prev_set = curr_set
        merging = False

    return collapsable_map


def diff_bin(df):

    cur_bin = 0
    curr_long = 0.01

    for tup in df.itertuples():
        if tup.mz_diff > curr_long:
            cur_bin += 1

        if tup.mz_diff_long < curr_long:
            curr_long = tup.mz_diff_long

        yield cur_bin


def ms1_peaks_agg_lx2(ms1_peaks, options):
    ms1_peaks.sort_values("mz", ascending=False, inplace=True)
    # repetition_rate = 0.7
    scan_count = ms1_peaks.scan_id.unique().size
    if scan_count < 2:
        log.info("no averaging, not enough scans")
        return ms1_peaks
    ms1_peaks["mz_diff"] = ms1_peaks.mz.diff(-1).shift()
    ms1_peaks["mz_diff_long"] = (
        ms1_peaks["mz_diff"]
        .where(ms1_peaks["mz_diff"] > 0.0001, np.nan)
        .rolling(scan_count, min_periods=2)
        .mean()
    )  # neg because of sorting order

    # below for reference in as a reminders
    # df['scan_id_f'] = df['scan_id'].factorize()[0]
    # df['scan_cnt'] = df.scan_id_f.rolling(scan_count).apply(lambda s: len(set(s)))
    # df['mean_mz_diff']  = df.mz_diff.rolling(window = 31, center=True, win_type ='cosine' ).mean() # note win_type =should be tukey

    ms1_peaks["bin_mass"] = list(diff_bin(ms1_peaks))

    ######collapse adjacent
    collapsable_map = get_collapsable_bins(ms1_peaks)

    ms1_peaks["bin_mass"].replace(collapsable_map, inplace=True)

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
        .agg({"merged_mass": ["mean", "count"], "merged_inty": "mean",})
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
    # agg_df["weigted_mass"] = agg_df.mass_intensity_sum / agg_df.merged_inty_sum
    # lx1 intensity is wrong because it uses the total number of scans, instead of the numebr of scans with a peak
    # agg_df["lx1_bad_inty"] = agg_df.merged_inty_sum / fadi_denominator

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


def ms1_scans_agg_lx2(ms1_agg_peaks, options):
    ms1_agg_peaks.sort_values("mz", ascending=False, inplace=True)
    sample_count = ms1_agg_peaks.stem.unique().size
    if sample_count < 2:
        log.info("no averaging, not enough samples")
        ms1_agg_peaks["mass"] = ms1_agg_peaks["mz"]
        return ms1_agg_peaks

    ms1_agg_peaks["mz_diff"] = ms1_agg_peaks.mz.diff(-1).shift()

    ms1_agg_peaks["mz_diff_long"] = (
        ms1_agg_peaks["mz_diff"]
        .where(ms1_agg_peaks["mz_diff"] > 0.0001, np.nan)
        .rolling(sample_count, min_periods=2)
        .mean()
    )  # neg because of sorting order
    # .replace(0,np.nan).fillna(method = 'bfill').fillna(method = 'ffill')

    ms1_agg_peaks["bins"] = list(diff_bin(ms1_agg_peaks))
    collapsable_map = get_collapsable_bins(
        ms1_agg_peaks, accross_column="stem", cluster_column="bins"
    )
    ms1_agg_peaks["bins"].replace(collapsable_map, inplace=True)

    # -----------------------

    # check occupation spectracontainer.py masterscan.chekoccupation
    # occupation is the % of peak intensities abvove "thrsld: "
    threshold_denominator = sample_count
    threshold = options["MSminOccupation"]
    bin_peak_count = ms1_agg_peaks.groupby("bins")["inty"].transform("count")
    tf_mask = (bin_peak_count / threshold_denominator) >= threshold
    ms1_agg_peaks["above_threshold"] = tf_mask

    ms1_agg_peaks["mass"] = ms1_agg_peaks.groupby("bins")["mz"].transform("mean")
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

        tf_mask = prec_ms2_peaks.inty > options["MSMSthreshold"]

        # it uses merge sum intensity for getting the averrage intensity...
        agg_prec_ms2_peaks = (
            prec_ms2_peaks[tf_mask]
            .groupby(
                ["weighted_mass", "stem"]
            )  # weighted_mass is as indicateive as the bin
            .agg({"inty": "mean", "mz": "count"})
        )
        agg_prec_ms2_peaks.rename(columns={"mz": "count"}, inplace=True)
        agg_prec_ms2_peaks.reset_index(inplace=True)
        agg_prec_ms2_peaks.rename(columns={"weighted_mass": "mz"}, inplace=True)

        fadi_denominators = (
            prec_ms2_peaks.groupby("stem")["scan_id"].nunique().to_dict()
        )

        ff_mask = (
            agg_prec_ms2_peaks["count"] / agg_prec_ms2_peaks.stem.map(fadi_denominators)
            >= options["MSMSfilter"]
        )
        mof_mask = (
            agg_prec_ms2_peaks["count"] / agg_prec_ms2_peaks.stem.map(fadi_denominators)
            >= options["MSMSminOccupation"]
        )

        agg_prec_ms2_peaks["precursor_mz"] = prec_ms2_peaks.precursor_mz.mean()
        agg_prec_ms2_peaks = agg_prec_ms2_peaks[ff_mask & mof_mask]

        # agg_prec_ms2_peaks.columns = [
        #     "_".join(col).strip() for col in agg_prec_ms2_peaks.columns.values
        # ]
        # names = {
        #     "weighted_mass_mean": "mz",
        #     "weighted_mass_count": "count",
        #     "inty_mean": "inty",
        #     "precursor_mz_": "precursor_mz",
        #     "stem_": "stem",
        # }
        # agg_prec_ms2_peaks.rename(columns=names, inplace=True)

        yield agg_prec_ms2_peaks


# #recalibrate
def recalibration_values(ms1_df, options):
    res = []
    for cal_mass in options["MScalibration"]:
        tol = cal_mass / options["MSresolution"].tolerance
        # find close enough most intense

        reference_mass = (
            ms1_df[ms1_df.mz.between(cal_mass - tol, cal_mass + tol)]
            .sort_values("inty", ascending=False)
            .mz
        )
        if not reference_mass.any():
            return None, None
        reference_mass = reference_mass.iat[0]
        change_val = cal_mass - reference_mass
        res.append((reference_mass, change_val))

    cal_matchs, cal_vals = zip(*res)
    # note is used like this
    # ms1_df.mz = (ms1_df.mz + np.interp(ms1_df.mz, cal_matchs, cal_vals))
    return (cal_matchs, cal_vals)


###################### build masterscan
def mass_inty_generator_ms1_agg(ms1_agg_peaks, polarity):
    for mass, gdf in ms1_agg_peaks.groupby("mass"):
        # dictIntensity = gdf.set_index("stem")["lx1_bad_inty"].to_dict()
        dictIntensity = gdf.set_index("stem")["inty"].to_dict()
        # dictIntensity.update({f"{k}_lx2": v for k, v in dictIntensity_lx2.items()})
        dictIntensity = OrderedDict(sorted(dictIntensity.items()))
        yield (mass, dictIntensity, polarity)


def MSMSEntry_list_generator(gdf, samples, polarity):
    for mz, precur_df in gdf.groupby("mz"):
        dictIntensity = precur_df.set_index("stem")["inty"].to_dict()
        # dictIntensity.update(
        #     {f"{k}_lx2": v for k, v in dictIntensity.items()}
        # )  # TODO actually get other values
        # TODO samples should be dictIntensity.keys()?
        dictIntensity = OrderedDict(sorted(dictIntensity.items()))
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


#######LX2 functionsloity
def suggest_selection_window(spectra_df):
    precursor_mzs = spectra_df.loc[
        ~spectra_df.precursor_id.isna()
    ].precursor_mz.drop_duplicates()
    precursor_mzs.sort_values(inplace=True)
    agg_data = precursor_mzs.diff().agg(["mean", "std"])

    mean_less_std = agg_data.at["mean"] - agg_data.at["std"]
    if mean_less_std > 0:
        res = mean_less_std / 2
    else:
        res = agg_data.at["mean"] / 2

    return res


def suggest_resolution_gradient_and_tolerance(spectra_df):
    df = spectra_df.loc[spectra_df.precursor_id.isna()]
    # use only thge last few scans
    scan_count = df.scan_id.unique().size

    df["scan_id_f"] = df["scan_id"].factorize()[0]
    df.sort_values(["mz", "scan_id_f"], ascending=False, inplace=True)
    df["nunique_scans"] = df.rolling(60)["scan_id_f"].apply(lambda s: len(set(s)))
    # try https://stackoverflow.com/questions/46470743/how-to-efficiently-compute-a-rolling-unique-count-in-a-pandas-time-series
    max_unique_scans = df["nunique_scans"].max()
    df["mean_diff"] = df["mz"].diff(-1).rolling(max_unique_scans).mean()
    df["mz_r"] = (df.mz / 10).round() * 10

    valids = df.loc[df["nunique_scans"] >= max_unique_scans * 0.9]
    valids.sort_values("mz", inplace=True)
    valids["max_diff"] = valids["mean_diff"].cummax()
    selected = valids.groupby("mz_r")["resolution"].min().to_frame().reset_index()
    # selected.plot(x='mz_r', y="resolution")
    res_at_loest_mass = selected["resolution"].iat[0]
    gradient = (
        selected["resolution"].iat[-1]
        - selected["resolution"].iat[0] / selected["mz_r"].iat[-1]
        - selected["mz_r"].iat[0]
    )

    return res_at_loest_mass, gradient


if __name__ == "__main__":
    import pickle

    with open("optoins.pkl", "rb") as f:
        options = pickle.load(f)

    masterscan = make_lx1_masterscan(options)
    with open("tmp_lx1_and_lx2.sc", "wb") as f:
        pickle.dump(masterscan, f)

