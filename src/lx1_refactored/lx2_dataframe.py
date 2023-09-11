import logging
import sys
import numpy as np
import pandas as pd
from pathlib import Path
import warnings

from .lx1_ref_dataframe import (
    get_settings,
    spectra_as_df,
    merge_peaks_from_scan,
    aggregate_groups,
    filter_repetition_rate,
    filter_intensity,
    recalibrate,
    get_mz_ml_paths,
)
from .lx1_ref_dataframe import make_masterscan as make_masterscan_from_lx1

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="[%(asctime)s] {%(name)s:%(lineno)d} %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(Path(__file__).stem)


# see compare_grouping from LX1 masterscan
def add_bins(df, expected_group_count=None):
    """groups the masses like in lx1"""
    if expected_group_count is None:
        if df["stem"].unique().shape[0] == 1:
            expected_group_count = df["scan_id"].unique().shape[0]
        else:
            expected_group_count = df["stem"].unique().shape[0]
    eg_count = expected_group_count

    assert (
        "filter_string" not in df or df["filter_string"].unique().shape[0] == 1
    ), "only one filterstring to bin over"
    df = df.sort_values("mz")
    groups, bins_info = get_bins(df["mz"], expected_group_count)

    df["_group"] = groups.values
    # TODO merge peaks from single scan
    # df['scan_peak_count'] = df.groupby(["_group", 'scan_id']).cumcount()
    # df["weights"] = df.groupby("_group")["mz"].apply(get_weighted_masses)

    return df


def get_bins(masses, eg_count, sigma=2):
    """returns the group for the masses,
    based on MS clusterting, and the mean and std for each group"""
    assert (
        masses.is_monotonic_increasing
    ), "The 'masses' Series must be sorted in ascending order."

    masses.reset_index(drop=True, inplace=True)
    mz_r_mean = masses.rolling(eg_count, center=True).mean()
    mz_r_std = masses.rolling(eg_count, center=True).apply(np.std)
    mz_r_std_min = mz_r_std.rolling(eg_count, center=True).min()
    is_std_min = mz_r_std == mz_r_std_min
    # TODO add kurtosis and skew to check?
    mean_mz = mz_r_mean.loc[is_std_min]
    std_mz = mz_r_std[is_std_min]
    upper_mz = mean_mz + (sigma * std_mz)
    lower_mz = mean_mz - (sigma * std_mz)

    bins = mean_mz.to_frame()
    bins["group_no"] = bins.index
    bins["lower_mz"] = lower_mz
    bins["upper_mz"] = upper_mz
    bins["is_overlap"] = bins["upper_mz"] > bins["lower_mz"].shift(-1)

    bins["overlap_group"] = (
        bins["lower_mz"] > bins["upper_mz"].shift()
    ).cumsum()
    bins["width_mz"] = bins["upper_mz"] - bins["lower_mz"]

    # NOTE about overlaps
    # split with prioroty to smallest width
    current_wider_than_next = bins["width_mz"] > bins["width_mz"].shift(-1)
    replace_upper = (bins["is_overlap"]) & (current_wider_than_next)
    bins.loc[replace_upper, "upper_mz"] = bins.assign(
        next_lower=bins["lower_mz"].shift(-1)
    ).loc[replace_upper, "next_lower"]

    replace_lower = (bins["is_overlap"].shift()) & (
        current_wider_than_next.shift() == False
    )
    bins.loc[replace_lower, "lower_mz"] = bins.assign(
        prev_upper=bins["upper_mz"].shift()
    ).loc[replace_lower, "prev_upper"]

    cuts = pd.concat([bins["lower_mz"], bins["upper_mz"]]).sort_values()
    cuts = cuts.drop_duplicates()

    # NOTE prefer to sort ino small bins instead of large ones
    # bins.sort_values('width_mz', inplace =True) # to takes smallest first

    # NOTE cut out large bins, large can be defined as elbow in width_mz
    # delta = np.gradient(bins['width_mz'])
    # delta = abs(bins['width_mz'].shift(-1) + bins['width_mz'].shift() - 2*bins['width_mz'])
    # elbow = np.argmax(delta)

    ########## approach 3 make index interval and
    # and siort poeaks into first fall
    # bins_intervals = pd.IntervalIndex.from_arrays(bins['lower_mz'], bins['upper_mz'], closed='both')

    # def get_group(mz):
    #     df = bins[bins_intervals.contains(mz)]
    #     if df.empty:
    #         return -1
    #     else:
    #         return df.iloc[0].at['group_no']

    # groups_df = masses.to_frame()
    # groups_df['group'] = masses.apply(lambda mz: get_group(mz) )

    ################## Approach 1 what the logic should do, but is slow
    # def wrapper(mass):
    #     for _, row in bins.iterrows():
    #         if row['lower_mz'] <= mass < row['upper_mz']:
    #             return row['group_no']
    # groups_df = masses.to_frame()
    # groups_df['group'] =  masses.apply(wrapper)

    return pd.cut(masses, cuts, labels=False), bins


def get_weighted_masses(gdf_mz):
    # https://stackoverflow.com/questions/64368050/gaussian-rolling-weights-pandas
    # https://www.youtube.com/watch?v=QIi2eWmdPM8&ab_channel=learndataa
    # https://dsp.stackexchange.com/questions/84471/rolling-average-in-pandas-using-a-gaussian-window\

    x = gdf_mz
    mu = gdf_mz.mean()
    sigma = 2
    weights = np.exp(-((x - mu) ** 2) / 2 * sigma**2) / np.sqrt(
        2 * np.pi * sigma**2
    )
    return weights * x


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


def align_spectra(df):
    """returns the reordered dataframe with added _group column"""
    df.sort_values("mz", inplace=True)
    expected_group_count = df["stem"].unique().shape[0]
    df = add_bins(df, expected_group_count)
    return df


def spectra_2_DF(spectra_path, options, add_stem=True):
    """convert a spectra mzml, with multiple scans, into a dataframe an average ms1 dataframe"""
    settings = get_settings(options)
    settings["ms_level"] = settings.get("ms_level", 'ms1')
    settings["polarity"] = settings.get("polarity", 1)
    df = spectra_as_df(spectra_path, **settings)

    df = add_bins(df)
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
        df, calibration_masses
    )
    df = recalibrate(df, matching_masses, reference_distance)
    lx_data["recalibration"] = (matching_masses, reference_distance)

    return df, lx_data


def aligned_spectra_df(options):
    """create a dataframe with the average ms1 information for all the spectra indicated in the options

    Args:
        options (_type_): as in lx1

    Returns:
        tuple : dataframe and list with information about the processing of the spectra
    """
    mzmls = get_mz_ml_paths(options)
    dfs_and_info = [
        spectra_2_DF(spectra_path, options) for spectra_path in mzmls
    ]
    dfs, df_infos = zip(*dfs_and_info)
    # NOTE assert all dfs have same polarity? YAGNI
    df = pd.concat(dfs)
    df = align_spectra(df)
    return df, df_infos


def make_masterscan(options, **kwargs):
    df, df_infos = aligned_spectra_df(options)
    return make_masterscan_from_lx1(options, df, df_infos, lx2=True)
