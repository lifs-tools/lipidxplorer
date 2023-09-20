"""Averaging multiple ms1 scans into a single scan per spectra
then aligninig multiple spectra/scans,

for one spectra, similar scans are grouped (eg.ms1 scans)
    for a group of scans peaks are clustered (eg. target mass +- reolution 456.89 +- 0.055)
    peaks are grouped by mass to average the intensity, (eg avereage mass, average intensity)
    a weighted average can be used where more intensse peaks influence the average mass more
    for each spectra masses can be "recalibrated" based on expected mass (see np.interp)

    multiple spectra are "aligned" by grouping similar scans
    and clustering peaks from the different scans
    per scan intensity is keept as that is the information used in the output

    the colection of grouped / averaged and aligned spectra is stored  in a masterscan file
    that contains the averaged mass of the aligned spectra and the intensity for each spectra

    for ms2 there is a similar operation, of grouping, averaging and aligning and recalibration



"""
import logging
import sys
import warnings

from pathlib import Path
from enum import Flag, auto

import numpy as np
import pandas as pd
from ms_deisotope import MSFileLoader
from pyteomics.xml import unitfloat
from ms_deisotope.data_source.memory import make_scan
from ms_deisotope.data_source.metadata import file_information
from ms_deisotope.data_source.metadata.scan_traits import (
    ScanAcquisitionInformation,
    ScanEventInformation,
)
import pickle
from ms_deisotope.data_source.scan.base import RawDataArrays
from ms_deisotope.output.mzml import MzMLSerializer

from .lx1_ref_masterscan import (
    build_masterscan,
    df2listSurveyEntry,
    make_masterscan,
    make_masterscan,
)
from .lx1_ref_read_write_spectra import get_settings, spectra_as_df

from .lx1_ref_sim_tools import (
    parse_filter_string,
    stitch_sim_scans,
    filter_string_replacements,
)

from .lx1_ref_change_peaks import (
    filter_repetition_rate,
    filter_intensity,
    find_reference_masses,
    recalibrate,
    filter_occupation,
    add_massWindow,
)

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="[%(asctime)s] {%(name)s:%(lineno)d} %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(Path(__file__).stem)


############## LX1 style grouping of ms1 scans


def add_lx1_bins(df, tolerance, resolutionDelta=0):
    """returns the reordered dataframe with added _group column"""
    df.sort_values("mz", inplace=True)
    # binning is done 3 times in lx1, between each fadi filter is performed, we do it at the end intead
    bins1 = bin_linear_alignment(df["mz"], tolerance, resolutionDelta)
    bins2 = bin_linear_alignment(
        df.groupby(bins1)["mz"].transform("mean"), tolerance, resolutionDelta
    )
    bins3 = bin_linear_alignment(
        df.groupby(bins2)["mz"].transform("mean"), tolerance, resolutionDelta
    )

    df["_group"] = bins3
    return df


def bin_linear_alignment(masses, tolerance, resolutionDelta=0):
    """groups the masses like in lx1"""
    assert (
        masses.is_monotonic_increasing
    ), "The 'masses' Series must be sorted in ascending order."
    minmass = masses.min()

    up_to = None
    result = np.empty(len(masses), dtype=float)

    for i, mass in enumerate(masses):
        delta = (mass - minmass) * resolutionDelta
        if up_to is None:
            # NOTE up_to = mass + tolerance.getTinDA(mass) this is how its done in some places, but reuslt are not identical to below
            up_to = mass + mass / (tolerance + delta)
        if mass <= up_to:
            result[i] = up_to
        else:
            up_to = mass + mass / (tolerance + delta)
            result[i] = up_to

    return result


def merge_peaks_from_scan(df):
    """when a single scan has more than one peak in a group
    use the average value, of the peaks"""
    assert (
        "_group" in df
    ), "The DataFrame or Series must contain a column named 'group'."

    # reset the index
    df = df.reset_index()

    # use weighted mass
    df["_inty_x_mass"] = df["mz"] * df["inty"]

    # merge mutiple peaks from single scan
    g = df.groupby(["_group", "scan_id"])
    df["_group_enumerate"] = g.cumcount()
    df["_merged_mass"] = g["mz"].transform("mean")
    df["_merged_inty"] = g["inty"].transform("mean")
    df["_weigted_mass"] = g["_inty_x_mass"].transform("sum") / g[
        "inty"
    ].transform("sum")

    # TODO make a weighted intensity based on standard deviation... but not now
    # NOTE lx1 adds the intesities of close peaks... see alignmebt.py mk survey linear:643
    # NOTE LX! does a bad averagin if peaks see readspectra:add_sample:401
    log.info(
        'columns starting with _ "underscore" are for processing and can be discarded'
    )
    return df


def aggregate_groups(df):
    """get the averege value for each group"""

    # aggregate results
    agg_df = (
        df.loc[
            df["_group_enumerate"] == 0
        ]  # use only the first of merged masses
        .assign(
            _mass_intensity=lambda x: x["mz"] * x["_merged_inty"]
        )  # for the weighted average intensity
        .groupby("_group")
        .agg(
            {
                "_merged_mass": ["mean", "count"],
                "_merged_inty": ["mean", "sum"],
                "_mass_intensity": "sum",
                "_weigted_mass": "mean",
            }
        )
        .dropna()
    )
    agg_df.columns = ["_".join(col).strip() for col in agg_df.columns.values]
    agg_df.rename(
        columns={"_weigted_mass_mean": "mz", "_merged_inty_mean": "inty"},
        inplace=True,
    )
    agg_df.reset_index(inplace=True)
    log.info(
        'aggregated dataframe contains metadata in "lx_data" atribute... eg df.lx_data'
    )
    lx_data = {}
    scan_count = df["scan_id"].unique().shape[0]
    lx_data["scan_count"] = scan_count
    # NOTE lx1 intensity is wrong because it uses the total number of scans, instead of the numebr of scans with a peak
    warnings.warn("incorrect calculation of intensity")
    return agg_df, lx_data


###### spectra alignment


def align_spectra(df, tolerance, resolutionDelta):
    assert "stem" in df, "The DataFrame must contain a column named 'stem'."
    df.sort_values("mz", inplace=True)
    df = add_lx1_bins(df, tolerance, resolutionDelta=resolutionDelta)
    return df


def _collapsable_adjacent_groups(
    df, headers_column, group_column, close_enogh_da=0.001
):
    """tries to merge adjacent groups that might have been splip by the low tolerance,
    its a work arownd for bad results"""
    # TODO make this more elegant if needed
    cluster_column = group_column
    accross_column = headers_column
    df.sort_values("mz", ascending=False, inplace=True)
    df[cluster_column] = df[cluster_column].factorize()[0]
    df["_accross_column_f"] = df[accross_column].factorize()[0]
    grouped = df.groupby(cluster_column)
    grouped_stats = grouped.agg({"mz": ["max", "min", "std"]})
    close_mz = grouped_stats[("mz", "min")] - grouped_stats[
        ("mz", "max")
    ].shift(-1) < grouped_stats[("mz", "std")] + grouped_stats[
        ("mz", "std")
    ].shift(
        -1
    )
    close_enough_mz = (
        grouped_stats[("mz", "min")] - grouped_stats[("mz", "max")].shift(-1)
        < close_enogh_da
    )

    close_mz = close_mz | close_enough_mz
    if not close_mz.any():
        return None

    close_mz_groups = close_mz[close_mz | close_mz.shift(1)].index.to_numpy()
    close_sets = (
        df.loc[df[cluster_column].isin(close_mz_groups)]
        .groupby(cluster_column)["_accross_column_f"]
        .apply(lambda s: set(s))
    )

    collapsable_map = {}
    prev_set = set()
    prev_idx = close_mz[close_mz].index[0]
    base_idx = prev_idx
    for idx, curr_set in close_sets.iteritems():
        if (
            close_mz[prev_idx]
            and idx - prev_idx <= 1
            and not curr_set.intersection(prev_set)
        ):
            collapsable_map[idx] = base_idx
            prev_set.update(curr_set)
        else:
            prev_set = curr_set
            base_idx = idx
        prev_idx = idx
    return collapsable_map


def collapse_spectra_groups(df):
    """join consecutive groups where non-empy values are complementary,
    huristic to fix too high reolution setting in the clustering
     eg
                stem_1  stem_2  stem_3
    mz 450.1    100     0       0
    mz 450.2      0     200     0

    converts to
    mz 450.15      100     200     0


    Args:
        df (dataframe): the averaged and grouped data

    Returns:
        dataframe: with same columns but potentially modified grouping
    """
    collapsable_map = _collapsable_adjacent_groups(df, "stem", "_group")
    df["_group"].replace(collapsable_map, inplace=True)
    return df


def add_aggregated_mass(df):
    # NOTE not sure why this is done here, maybe its the way its done in lx1
    df["mass"] = df.groupby("_group")["mz"].transform("mean")
    return df


def spectra_2_DF_lx1(spectra_path, options, add_stem=True):
    """convert a spectra mzml, with multiple scans, into a dataframe an average ms1 dataframe"""
    settings = get_settings(options)
    settings["ms_level"] = settings.get("ms_level", "1")
    settings["polarity"] = settings.get("polarity", 1)
    df = spectra_as_df(spectra_path, **settings)

    tolerance = options["MSresolution"].tolerance
    df = add_lx1_bins(df, tolerance)
    df = merge_peaks_from_scan(df)

    df, lx_data = aggregate_groups(df)
    # TODO extend df with lx_data, https://pandas.pydata.org/pandas-docs/stable/development/extending.html
    # see https://git.mpi-cbg.de/mirandaa/lipidxplorer2.0/-/blob/master/lx2_tools/scansDecorator.py
    lx_data["stem"] = Path(spectra_path).stem
    lx_data["ms_level"] = settings["ms_level"]
    lx_data["polarity"] = settings["polarity"]

    if add_stem:
        df["stem"] = lx_data["stem"]
        df["stem"] = df["stem"].astype("category")

    mask = filter_repetition_rate(
        df, lx_data["scan_count"], options["MSfilter"]
    )
    df = df[mask]
    mask = filter_intensity(df, options["MSthreshold"])
    df = df[mask]

    calibration_masses = options["MScalibration"]
    matching_masses, reference_distance = find_reference_masses(
        df, tolerance, calibration_masses
    )
    # TODO: @Jacobo matching_masses can be empty
    df = recalibrate(df, matching_masses, reference_distance)
    lx_data["recalibration"] = (matching_masses, reference_distance)
    return df, lx_data


def align_ms1_dfs(dfs, options):
    """aling multiple dataframes, from multiple spectra, into single dataframe"""
    df = pd.concat(dfs)
    tolerance = options["MSresolution"].tolerance
    resolutionDelta = options["MSresolutionDelta"]

    df = align_spectra(df, tolerance, resolutionDelta)
    return df


def get_mz_ml_paths(options):
    p = Path(options["importDir"])
    mzmls = list(p.glob("*.[mM][zZ][mM][lL]"))
    if not mzmls:
        log.warning("no mzml files found in {}".format(p))
        log.warning("using all mzXML files in {}".format(p))
        mzmls = list(p.glob("*.[mM][zZ][xX][mM][lL]"))

    return mzmls


def aligned_spectra_df_lx1(options):
    """create a dataframe with the average ms1 information for all the spectra indicated in the options

    Args:
        options (_type_): as in lx1

    Returns:
        tuple : dataframe and list with information about the processing of the spectra
    """
    mzmls = get_mz_ml_paths(options)
    dfs_and_info = [
        spectra_2_DF_lx1(spectra_path, options) for spectra_path in mzmls
    ]
    dfs, df_infos = zip(*dfs_and_info)
    # NOTE assert all dfs have same polarity? YAGNI
    df = align_ms1_dfs(dfs, options)
    return df, df_infos


def make_masterscan_lx1(options):
    """make the masterscan based on the optoins inftomation

    Args:
        options (_type_): as in lx1

    Returns:
        masterscan: with the averaged spectra information
    """
    df, df_infos = aligned_spectra_df_lx1(options)
    return make_masterscan(options, df, df_infos)
