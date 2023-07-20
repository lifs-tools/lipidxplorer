from pathlib import Path
import pandas as pd
import numpy as np
from ms_deisotope import MSFileLoader
import logging, sys, warnings

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="[%(asctime)s] {%(name)s:%(lineno)d} %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(Path(__file__).stem)

def spectra2df_settings(options):
    res = {}
    time_range = options["timerange"]
    res['time_start'] = 0 if not time_range else time_range[0]
    res['time_end'] = float("inf") if not time_range else time_range[1]
    ms1_mass_range = options["MSmassrange"]
    res['ms1_start'] = 0 if not ms1_mass_range else ms1_mass_range[0]
    res['ms1_end'] = float("inf") if not ms1_mass_range else ms1_mass_range[1]
    ms2_mass_range = options["MSMSmassrange"]
    res['ms2_start'] = 0 if not ms2_mass_range else ms2_mass_range[0]
    res['ms2_end'] = float("inf") if not ms2_mass_range else ms2_mass_range[1]
    return  res

def spectra2df(
    path,
    read_ms1_scans = True,
    read_ms2_scans = True,
    time_start=0,
    time_end=float("inf"),
    ms1_start=0,
    ms1_end=float("inf"),
    ms2_start=0,
    ms2_end=float("inf"),
    polarity=None,
):
    assert read_ms1_scans or read_ms2_scans, ' must read ms1 or ms2 scans'
    path = Path(path)
    dfs = []
    with MSFileLoader(str(path)) as r:
        r.get_scan_by_time(time_start / 60)
        r.start_from_scan(r.get_scan_by_time(time_start / 60).id)
        _categorical_cols = ["stem","scan_id","filter_string", "precursor_id", "precursor_mz", "polarity"]
        for b in r:
            if not (time_start / 60 < b.precursor.scan_time < time_end / 60):
                continue
            if polarity and b.precursor.polarity != polarity:
                continue
            
            if read_ms1_scans:
                a = b.precursor.arrays
                df = pd.DataFrame(
                    {
                        "mz": a.mz.astype("float32"),
                        "inty": a.intensity.astype("float32"),
                        "stem": path.stem,
                        "scan_id": b.precursor.scan_id,
                        "filter_string": b.precursor.annotations["filter string"]
                        if b.precursor.annotations
                        else b.precursor._data["filterLine"],
                        "precursor_id": np.NaN,
                        "precursor_mz": 0,
                        "polarity": b.precursor.polarity,
                    }
                )
                df = df[df.mz.between(ms1_start, ms1_end) & df.inty > 0]
                for col in _categorical_cols:
                    df[col] = df[col].astype("category")
                dfs.append(df)
            
            # read the ms2 scans
            if not read_ms2_scans: continue
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
                for col in _categorical_cols:
                    df[col] = df[col].astype("category")
                dfs.append(df)
    df = pd.concat(dfs)
    log.info(f"spectra {path.stem}, size: {df.shape}")
    return df

############## LX1 style grouping of ms1 scans

def add_lx1_bins(df, tolerance, resolutionDelta = 0):
    '''returns the reordered dataframe withadded group column'''
    df.sort_values("mz", inplace=True)
    # binning is done 3 times in lx1, between each fadi filter is performed, we do it at the end intead
    bins1 = bin_linear_alignment(df['mz'], tolerance, resolutionDelta)
    bins2 = bin_linear_alignment(df.groupby(bins1)["mz"].transform("mean"), tolerance, resolutionDelta)
    bins3 = bin_linear_alignment(df.groupby(bins2)["mz"].transform("mean"), tolerance, resolutionDelta)

    df['_group'] = bins3
    return df 

def bin_linear_alignment(masses, tolerance, resolutionDelta = 0):
    '''groups the masses like in lx1'''
    assert masses.is_monotonic_increasing, "The 'masses' Series must be sorted in ascending order."
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
    '''when a single scan has more than one peak in a group
    use the average value, of the peaks'''
    assert '_group' in df, "The DataFrame or Series must contain a column named 'group'."

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
    log.info('columns starting with _ "underscore" are pof processing and can be discarded')
    return df

def aggregate_groups(df):
    '''get the averege value for each group'''

    # aggregate results
    agg_df = (
        df.loc[
            df["_group_enumerate"] == 0
        ]  # use only the first of merged masses
        .assign(
            _mass_intensity=lambda x: x['mz'] * x['_merged_inty']
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
    log.info('aggregated dataframe contains metadata in "lx_data" atribute... eg df.lx_data')
    lx_data = {}
    scan_count = df['scan_id'].unique().shape[0]
    lx_data['scan_count'] = scan_count
    #NOTE lx1 intensity is wrong because it uses the total number of scans, instead of the numebr of scans with a peak
    warnings.warn('incorrect calculation of intensity')
    return agg_df, lx_data

##### filter the data
def filter_repetition_rate(df, scan_count = None, MSfilter = 0):
    '''returns a boolean list as in df'''
    if scan_count is None: # use default
        scan_count = df['_merged_mass_count'].max()
        log.warning('scan_count was not provided , using the maximum or _merged_mass_count instead , this may not be correct')

    # apply fadi filters, in lx1 its done between each bin  process
    fadi_denominator = scan_count
    mask_repetition_rate_filter = (
        df['_merged_mass_count'] / fadi_denominator >= MSfilter
    )
    return mask_repetition_rate_filter
    
def filter_intensity(df, MSthreshold = 0):
    # NOTE intensity threshold is done in add_Sample... but lets do it here
    mask_inty = df['inty'] > MSthreshold
    return mask_inty

###### recalibrate 

def find_reference_masses(df, tolerance, recalibration_masses):
    recalibration_masses = pd.Series(recalibration_masses)
    recalibration_masses.sort_values(inplace=True)
    # Find the indices of the closest float values in the right DataFrame for each value in the left DataFrame
    df_indices = np.searchsorted(df['mz'], recalibration_masses, side='left')
    matching_masses = df['mz'].iloc[df_indices].values
    differences = matching_masses - recalibration_masses.values
    mask = differences < (matching_masses / tolerance)
    return matching_masses[mask], differences[mask]

def recalibrate(df, matching_masses, reference_distance):
    df['mz'] = df['mz'] - np.interp(df['mz'], matching_masses, reference_distance)
    return df

###### spectra alignment

def align_spectra(df, tolerance, resolutionDelta):
    assert "stem" in df, "The DataFramemust contain a column named 'stem'."
    df.sort_values("mz", inplace=True)
    df = add_lx1_bins(df, tolerance, resolutionDelta=resolutionDelta)
    return df

def collapsable_adjacent_groups(df, headers_column ,group_column, close_enogh_da=0.001):
    '''tries to merge adjacent groups that might have been splip by the low tolerance, its a work arownd for bad results'''
    #TODO make this more elegant if needed
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

def collapsae_spectra_groups(df):
    collapsable_map = collapsable_adjacent_groups(df, 'stem' ,'_group')
    df["_group"].replace(collapsable_map, inplace=True)
    return df

def add_massWindow(df):
    '''masswindow is actually the tolerance by resolution delta, see :bin_linear_alignment,
    it is not used but required to make the surveryentries in the masterscan 
    '''
    masses = df['mz']
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








