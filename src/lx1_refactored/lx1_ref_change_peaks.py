"""functions that change the values in the peaks that will be use in the output,
like:
    recalibrating the masses
    intensity weighing functions
    filtering functions
"""

import logging
import pickle
import sys
from collections import OrderedDict
from pathlib import Path

import numpy as np
import pandas as pd
from lx.spectraContainer import MasterScan, MSMSEntry, SurveyEntry
import warnings

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="[%(asctime)s] {%(name)s:%(lineno)d} %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(Path(__file__).stem)

###### recalibrate not with tolerance like lx2


def find_closest():
    raise NotImplementedError("This function is not yet implemented.")
    # ser1 = pd.Series(list(MS2_dict.keys()), name="ser1")
    # ser1.sort_values(inplace=True)
    # tol = 0.001

    # precur_map_df = pd.merge_asof(
    #     ser1,
    #     ser2,
    #     left_on="ser1",
    #     right_on="ser2",
    #     direction="nearest",
    #     tolerance=tol,
    # )

    ######### vs
    # df_indices = np.searchsorted(df['mz'], recalibration_masses, side='left')
    # matching_masses = df['mz'].iloc[df_indices].values
    return None


def tukey_upper(differences, k=1.5):
    q1 = np.percentile(differences, 25)
    q3 = np.percentile(differences, 75)
    iqr = q3 - q1
    upper_bound = q3 + k * iqr
    return upper_bound


def find_reference_masses(df, recalibration_masses, max_tolearance=0.1):
    # TODO make find_closest function... see above
    recalibration_masses = pd.Series(recalibration_masses)
    recalibration_masses.sort_values(inplace=True)
    # Find the indices of the closest float values in the right DataFrame for each value in the left DataFrame
    df_indices = np.searchsorted(df["mz"], recalibration_masses, side="left")
    matching_masses = df["mz"].iloc[df_indices].values
    differences = matching_masses - recalibration_masses.values

    tolerance = tukey_upper(differences)
    if tolerance > max_tolearance:
        tolerance = max_tolearance
        message = f"reference mass tolerance is exxceded with replace with max tolerance: {max_tolearance}"
        warnings.warn(message)
        log.warning(message)

    mask = differences <= (matching_masses / tolerance)
    return matching_masses[mask], differences[mask]


###### recalibrate with tolerance like lx1
def find_reference_masses_w_tol(df, tolerance, recalibration_masses):
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


def recalibrate_with_ms1(df):
    # https://git.mpi-cbg.de/labShevchenko/PeakStrainer/-/blob/master/lib/simStitching/simStitcher.py#L198
    raise NotImplementedError()


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


def filter_occupation(df, minOccupation):
    # check occupation spectracontainer.py masterscan.chekoccupation
    # occupation is the % of peak intensities abvove "thrsld: "
    threshold_denominator = df["stem"].unique().shape[0]  # same as len(res)
    threshold = minOccupation
    bin_peak_count = df.groupby("_group")["inty"].transform("count")
    tf_mask = (bin_peak_count / threshold_denominator) >= threshold
    return tf_mask


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
