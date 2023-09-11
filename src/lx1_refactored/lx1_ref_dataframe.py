"""averaging multiple scans into a single scan


"""
import logging
import sys
import warnings
from datetime import datetime
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

from .lx1_ref_masterscan import build_masterscan, df2listSurveyEntry
from .lx1_ref_read_spectra import get_settings, spectra_as_df

from .lx1_ref_sim_tools import (
    parse_filter_string,
    stitch_sim_scans,
    filter_string_replacements,
)


logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="[%(asctime)s] {%(name)s:%(lineno)d} %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(Path(__file__).stem)


def recalibrate_with_ms1(df):
    # https://git.mpi-cbg.de/labShevchenko/PeakStrainer/-/blob/master/lib/simStitching/simStitcher.py#L198
    raise NotImplementedError()


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


##### filter the data
def filter_repetition_rate(df, scan_count=None, MSfilter=0.0):
    """returns a boolean list as in df"""
    if scan_count is None:  # use default
        scan_count = df["_merged_mass_count"].max()
        log.warning(
            "scan_count was not provided , using the maximum or _merged_mass_count instead , this may not be correct"
        )

    # apply fadi filters, in lx1 its done between each bin  process
    fadi_denominator = scan_count
    mask_repetition_rate_filter = (
        df["_merged_mass_count"] / fadi_denominator >= MSfilter
    )
    return mask_repetition_rate_filter


def filter_intensity(df, MSthreshold=0.0):
    # NOTE intensity threshold is done in add_Sample... but lets do it here
    mask_inty = df["inty"] > MSthreshold
    return mask_inty


###### recalibrate


def find_reference_masses(df, tolerance, recalibration_masses):
    recalibration_masses = pd.Series(recalibration_masses)
    recalibration_masses.sort_values(inplace=True)
    # Find the indices of the closest float values in the right DataFrame for each value in the left DataFrame
    df_indices = np.searchsorted(df["mz"], recalibration_masses, side="left")
    matching_masses = df["mz"].iloc[df_indices].values
    differences = matching_masses - recalibration_masses.values
    mask = differences < (matching_masses / tolerance)
    return matching_masses[mask], differences[mask]


def recalibrate(df, matching_masses, reference_distance):
    if not matching_masses or not reference_distance:
        log.warn("no calibration masses found, spectra is not recalibrated")
        return df
    df["mz"] = df["mz"] - np.interp(
        df["mz"], matching_masses, reference_distance
    )
    return df


###### spectra alignment


def align_spectra(df, tolerance, resolutionDelta):
    assert "stem" in df, "The DataFrame must contain a column named 'stem'."
    df.sort_values("mz", inplace=True)
    df = add_lx1_bins(df, tolerance, resolutionDelta=resolutionDelta)
    return df


def collapsable_adjacent_groups(
    df, headers_column, group_column, close_enogh_da=0.001
):
    """tries to merge adjacent groups that might have been splip by the low tolerance, its a work arownd for bad results"""
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
    collapsable_map = collapsable_adjacent_groups(df, "stem", "_group")
    df["_group"].replace(collapsable_map, inplace=True)
    return df


def add_massWindow(df, tolerance, resolutionDelta):
    """masswindow is actually the tolerance by resolution delta, see :bin_linear_alignment,
    it is not used but required to make the surveryentries in the masterscan
    """
    masses = df["mz"]
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

    df["masswindow"] = result
    return df


def filter_occupation(df, minOccupation):
    # check occupation spectracontainer.py masterscan.chekoccupation
    # occupation is the % of peak intensities abvove "thrsld: "
    threshold_denominator = df["stem"].unique().shape[0]  # same as len(res)
    threshold = minOccupation
    bin_peak_count = df.groupby("_group")["inty"].transform("count")
    tf_mask = (bin_peak_count / threshold_denominator) >= threshold
    return tf_mask


def add_aggregated_mass(df):
    # NOTE not sure why this is done here, maybe its the way its done in lx1
    df["mass"] = df.groupby("_group")["mz"].transform("mean")
    return df


def dataframe2mzml(df, source, destination=None):
    """write a dataframe into a mzml file

    Args:
        df (dataframe): contains masses and intensities and scans (mz,inty, filter_string)
        source (str: filepath): the basis for this file, some metadata is copied
        destination (str: filepath, optional): name of the file that shouild be generated or defaults to adding the date to the source file name. Defaults to None.

    Returns:
        str: the name of the file that was destination
    """
    # NOTE https://github.com/mobiusklein/ms_deisotope/blob/master/src/ms_deisotope/data_source/text.py
    # https://github.com/mobiusklein/ms_deisotope/blob/master/examples/csv_to_mzml.py
    # see https://git.mpi-cbg.de/labShevchenko/simtrim/-/blob/master/simtrim/simtrim.py#L35
    # or https://mobiusklein.github.io/ms_deisotope/docs/_build/html/output/mzml.html
    source_reader = MSFileLoader(source)
    scan1 = next(source_reader)
    scan1 = scan1.precursor
    scan1.pick_peaks()
    source = Path(source)

    if destination is None:
        # Get the current date and time
        current_datetime = datetime.now()

        # Format the date and time as a string in a tight format
        tight_datetime_string = current_datetime.strftime("%Y%m%d%H%M%S")
        destination = Path(
            str(source.with_suffix("")) + tight_datetime_string + ".mzml"
        )

    with MzMLSerializer(
        open(destination, "wb"),
        1,
        deconvoluted=False,
        sample_name=destination.stem,
        build_extra_index=False,
    ) as writer:
        # writer.copy_metadata_from(source) #NOTE not sure if is needed
        writer.add_file_contents(file_information.MS_MSn_Spectrum.name)
        writer.add_data_processing(writer.build_processing_method())

        writer.save(scan1)
        index = 0
        for filter_string, gdf in df.groupby("filter_string"):
            signal = RawDataArrays(gdf["mz"].values, gdf["inty"].values)
            scanEventInformation = ScanEventInformation(
                unitfloat(0, "minute"),
                [],
                traits={"filter string": filter_string},
            )
            acquisition_information = ScanAcquisitionInformation(
                "no combination", [scanEventInformation,],
            )
            # Create a new spectrum
            index += 1
            scan = make_scan(
                signal,
                1,
                f"index={index}",
                0,
                0,
                is_profile=False,
                polarity=gdf.iloc[0].at["polarity"],
                acquisition_information=acquisition_information,
                precursor_information=None,
            )
            scan.pick_peaks()

            # Write the spectrum to the MzML file
            writer.save(scan)

    return destination


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


def make_masterscan(
    options, aligned_spectra_df, aligned_spectra_infos, lx2=False
):
    """make the masterscan based on the optoins inftomation

    Args:
        options (_type_): as in lx1

    Returns:
        masterscan: with the averaged spectra information
    """
    df = aligned_spectra_df
    df_infos = aligned_spectra_infos
    df["masswindow"] = -1  # # NOTE use :add_massWindow instead
    polarity = df_infos[0]["polarity"]
    samples = df["stem"].unique().tolist()
    listSurveyEntry = df2listSurveyEntry(df, polarity, samples)
    scan = build_masterscan(options, listSurveyEntry, samples)

    idp = Path(options["importDir"])

    if lx2:
        filename = str(idp / Path("".join([idp.stem, "-lx2.sc"])))
    else:
        filename = str(idp / Path("".join([idp.stem, "-lx1-ref.sc"])))

    # filename = options["masterScanRun"]
    log.info(f"saving file to: {filename}")
    with open(filename, "wb") as scFile:
        pickle.dump(scan, scFile, pickle.HIGHEST_PROTOCOL)

    return scan
