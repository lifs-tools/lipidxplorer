import pytest
import pandas as pd
import warnings

from utils import read_options
from lx1_ref_masterscan import (
    spectra2df_settings, 
    spectra2df,
    add_lx1_bins,
    merge_peaks_from_scan,
    aggregate_groups,
    filter_repetition_rate,
    filter_intensity,
    find_reference_masses,
    recalibrate,
    align_spectra,
    collapsae_spectra_groups
)

ROOT_PATH = r'tests\resources\small_test'
OPTIONS_PATH = ROOT_PATH + r"\small_test-project.lxp"
SPECTRA_PATH = ROOT_PATH + r"\190321_Serum_Lipidextract_368723_01.mzML"
ms1_peaks_REF = ROOT_PATH + r"\test_get_ms1_peaks_ref.pkl"
group_ms1_peaks_REF = ROOT_PATH + r'\test_group_ms1_peaks_ref.pkl'
align_ms1_scans_ref_REF = ROOT_PATH + r'\test_align_ms1_scans_ref.pkl'

@pytest.fixture
def options():
    options = read_options(OPTIONS_PATH)
    return options

@pytest.fixture
def settings(options):
    
    return spectra2df_settings(options)


def test_spectra2df_settings(settings):
    expected_data = {
        "time_start": 33.0,
        "time_end": 1080.0,
        "ms1_start": 360.0,
        "ms1_end": 1000.0,
        "ms2_start": 150.0,
        "ms2_end": 1000.0,
    }
    actual_data = settings
    for key, value in expected_data.items():
        assert (
            key in actual_data
        ), f"Expected key '{key}' not found in the dictionary."
        assert (
            actual_data[key] == value
        ), f"Value for key '{key}' is not as expected."


def test_get_ms1_peaks(settings):
    settings['read_ms2_scans'] = False
    df = spectra2df(SPECTRA_PATH, **settings)
    assert df.shape == (65897, 8)
    assert df.scan_id.unique().shape[0] == 31
    assert df.filter_string.unique().shape[0] == 1
    df_ref = pd.read_pickle(ms1_peaks_REF)
    assert df_ref.equals(df)



def test_group_ms1_peaks(options):
    df = pd.read_pickle(ms1_peaks_REF)
    tolerance = options["MSresolution"].tolerance
    df = add_lx1_bins(df, tolerance)
    df = merge_peaks_from_scan(df)
    assert df.shape == (65897, 14)
    df, lx_data = aggregate_groups(df)
    assert df.shape == (6707, 6)
    mask = filter_repetition_rate(df, lx_data['scan_count'], options["MSfilter"])
    df = df[mask]
    assert df.shape == (1648, 6)
    mask = filter_intensity(df, options["MSthreshold"])
    df = df[mask]
    assert df.shape == (1648, 6)
    df_ref = pd.read_pickle(group_ms1_peaks_REF)
    assert df_ref.equals(df)


def test_recalibrate_ms1_peaks(options):
    df = pd.read_pickle(group_ms1_peaks_REF)
    tolerance = options["MSresolution"].tolerance
    calibration_masses = options["MScalibration"]
    matching_masses, reference_distance = find_reference_masses(df, tolerance, calibration_masses)
    df = recalibrate(df, matching_masses, reference_distance)
    assert df


def test_align_ms1_scans(options):
    df1 = pd.read_pickle(group_ms1_peaks_REF)
    # making a modified spectra
    df2 = pd.read_pickle(group_ms1_peaks_REF)
    df2 = df2.sample(frac=0.9, replace=True, random_state=1)
    df2 = recalibrate(df2, [500.0,800.0], [0.001,-0.002])
    df2['inty'] = df2['inty'] * 0.85

    df1["stem"] = 'filename1'
    df1["stem"] = df1["stem"].astype("category")

    df2["stem"] = 'filename2'
    df2["stem"] = df1["stem"].astype("category")

    df = pd.concat([df1,df2])

    tolerance = options["MSresolution"].tolerance
    resolutionDelta = options["MSresolutionDelta"]

    df = align_spectra(df, tolerance, resolutionDelta)
    assert not df1.equals(df2)
    df_ref = pd.read_pickle(align_ms1_scans_ref_REF)
    assert df_ref.equals(df)


def test_collapse_ms1_scans():
    df = pd.read_pickle(align_ms1_scans_ref_REF)
    df = collapsae_spectra_groups(df)
    assert False

def test_add_mass_window():
    df = pd.read_pickle(align_ms1_scans_ref_REF)
    df = add_massWindow(df)
    assert False

def test_filter_occupation():
    assert False

def test_alignment_mass():
    assert False


def test_tsim_detection():
    assert False

