import pandas as pd
import numpy as np
import pytest
from lx1_refactored import (
    add_aggregated_mass,
    add_lx1_bins,
    add_massWindow,
    aggregate_groups,
    align_spectra,
    build_masterscan,
    collapse_spectra_groups,
    df2listSurveyEntry,
    filter_intensity,
    filter_occupation,
    filter_repetition_rate,
    find_reference_masses,
    merge_peaks_from_scan,
    recalibrate,
    spectra2df,
    spectra2df_settings,
)

from utils import read_options

ROOT_PATH = r"tests/resources/small_test"
OPTIONS_PATH = ROOT_PATH + r"/small_test-project.lxp"
SPECTRA_PATH = ROOT_PATH + r"/190321_Serum_Lipidextract_368723_01.mzML"
ms1_peaks_REF = ROOT_PATH + r"/test_get_ms1_peaks_ref.pkl"
group_ms1_peaks_REF = ROOT_PATH + r"/test_group_ms1_peaks_ref.pkl"
align_ms1_scans_ref_REF = ROOT_PATH + r"/test_align_ms1_scans_ref.pkl"


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
    settings["read_ms2_scans"] = False
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
    assert df.shape == (6707, 7)
    mask = filter_repetition_rate(
        df, lx_data["scan_count"], options["MSfilter"]
    )
    df = df[mask]
    assert df.shape == (1648, 7)
    mask = filter_intensity(df, options["MSthreshold"])
    df = df[mask]
    assert df.shape == (1648, 7)
    df_ref = pd.read_pickle(group_ms1_peaks_REF)
    assert df_ref.equals(df)


def test_recalibrate_ms1_peaks(options):
    df = pd.read_pickle(group_ms1_peaks_REF)
    ref = df["mz"].copy()
    tolerance = options["MSresolution"].tolerance
    calibration_masses = options["MScalibration"]
    matching_masses, reference_distance = find_reference_masses(
        df, tolerance, calibration_masses
    )
    df = recalibrate(df, matching_masses, reference_distance)
    assert (df["mz"] != ref).all()


def test_align_ms1_scans(options):
    df1 = pd.read_pickle(group_ms1_peaks_REF)
    # making a modified spectra
    df2 = pd.read_pickle(group_ms1_peaks_REF)
    df2 = df2.sample(frac=0.9, replace=True, random_state=1)
    df2 = recalibrate(df2, [500.0, 800.0], [0.001, -0.002])
    df2["inty"] = df2["inty"] * 0.85

    df1["stem"] = "filename1"
    df1["stem"] = df1["stem"].astype("category")

    df2["stem"] = "filename2"
    df2["stem"] = df2["stem"].astype("category")
    assert not df1.equals(df2)

    df = pd.concat([df1, df2])

    tolerance = options["MSresolution"].tolerance
    resolutionDelta = options["MSresolutionDelta"]

    df = align_spectra(df, tolerance, resolutionDelta)
    # print(df.dtypes)

    df_ref = pd.read_pickle(align_ms1_scans_ref_REF)
    assert np.all(np.isclose(df["_group"], df_ref["_group"]))
    assert np.all(
        np.isclose(df["_merged_mass_mean"], df_ref["_merged_mass_mean"])
    )
    assert np.all(
        np.isclose(df["_merged_mass_count"], df_ref["_merged_mass_count"])
    )
    assert np.all(np.isclose(df["inty"], df_ref["inty"]))
    assert np.all(
        np.isclose(df["_merged_inty_sum"], df_ref["_merged_inty_sum"])
    )
    assert np.all(
        np.isclose(df["_mass_intensity_sum"], df_ref["_mass_intensity_sum"])
    )
    assert np.all(np.isclose(df["mz"], df_ref["mz"]))


def test_collapse_ms1_scans():
    df = pd.read_pickle(align_ms1_scans_ref_REF)
    ref = df["_group"].unique().shape[0]
    df = collapse_spectra_groups(df)
    assert df["_group"].unique().shape[0] <= ref


def test_add_mass_window(options):
    df = pd.read_pickle(align_ms1_scans_ref_REF)
    tolerance = options["MSresolution"].tolerance
    resolutionDelta = options["MSresolutionDelta"]
    df = add_massWindow(df, tolerance, resolutionDelta)
    assert "masswindow" in df


def test_filter_occupation(options):
    minOccupation = options["MSminOccupation"]
    minOccupation = 0.7  # use another value to get more filtered out
    df = pd.read_pickle(align_ms1_scans_ref_REF)
    mask = filter_occupation(df, minOccupation)
    df = df[mask]
    assert df.shape == (2465, 8)


def test_aggregated_mass():
    df = pd.read_pickle(align_ms1_scans_ref_REF)
    df = add_aggregated_mass(df)
    assert (df["mass"] != df["mz"]).any()


def test_build_masterscan(options):
    df = pd.read_pickle(align_ms1_scans_ref_REF)
    df["masswindow"] = -1  # # NOTE use :add_massWindow instead
    polarity = 1
    samples = df["stem"].unique().tolist()
    listSurveyEntry = df2listSurveyEntry(df, polarity, samples)
    scan = build_masterscan(options, listSurveyEntry, samples)
    assert scan
