import pandas as pd
import numpy as np
import pytest
from legacy.lx2_masterscan import lx2_spectra
from lx1_refactored import (
    add_bins,
    aggregate_groups,
    filter_intensity,
    filter_repetition_rate,
    merge_peaks_from_scan,
    spectra_as_df,
    recalibrate,
)
from lx1_refactored.lx2_dataframe import align_spectra, spectra_2_DF, aligned_spectra_df, make_masterscan
from utils import read_options

ROOT_PATH = r"tests/resources/small_test"
OPTIONS_PATH = ROOT_PATH + r"/small_test-project.lxp"
SPECTRA_PATH = ROOT_PATH + r"/190321_Serum_Lipidextract_368723_01.mzML"
ms1_peaks_REF = ROOT_PATH + r"/test_get_ms1_peaks_ref.pkl"
lx2_group_ms1_peaks_REF = ROOT_PATH + r"/test_get_lx2_ms1_peaks_ref.pkl"
lx2_align_ms1_scans_ref_REF = ROOT_PATH + r"/test_lx2_align_ms1_scans_ref.pkl"

@pytest.fixture
def options():
    options = read_options(OPTIONS_PATH)
    return options

def test_get_ms1_peaks():
    # options = read_options(OPTIONS_PATH) # Note only here as reference
    settings = {
        "read_sim_scans": False,
        "read_ms1_scans": True,
        "read_ms2_scans": False,
        "polarity": 1,
        "time_start": 33.0,
        "time_end": 1080.0,
        "ms1_start": 360.0,
        "ms1_end": 1000.0,
        "ms2_start": 150.0,
        "ms2_end": 1000.0,
    }
    df = spectra_as_df(SPECTRA_PATH, **settings)
    assert df.shape == (65897, 8)


def test_get_ms2_peaks():
    settings = {
        "read_sim_scans": False,
        "read_ms1_scans": False,
        "read_ms2_scans": True,
        "polarity": 1,
        "time_start": 33.0,
        "time_end": 1080.0,
        "ms1_start": 360.0,
        "ms1_end": 1000.0,
        "ms2_start": 150.0,
        "ms2_end": 1000.0,
    }
    df = spectra_as_df(SPECTRA_PATH, **settings)
    assert df.shape == (302188, 8)


@pytest.mark.skip(
    reason="There is an issue of ValueError: cannot reindex from a duplicate axis"
)  # TODO: Jacobo for the future
def test_group_ms1_peaks():
    options = {"MSfilter": 0.6, "MSthreshold": 0.6}
    df = pd.read_pickle(ms1_peaks_REF)
    df = add_bins(df)
    df = merge_peaks_from_scan(df)
    assert df.shape == (65897, 14)  # NOTE same for LX1 test
    df, lx_data = aggregate_groups(df)
    assert df.shape == (3046, 7)  # (6707, 7)
    mask = filter_repetition_rate(
        df, lx_data["scan_count"], options["MSfilter"]
    )
    df = df[mask]
    assert df.shape == (1729, 7)
    mask = filter_intensity(df, options["MSthreshold"])
    df = df[mask]
    assert df.shape == (1729, 7)
    df_ref = pd.read_pickle(lx2_group_ms1_peaks_REF) # TODO recheck because iupdated lx2_group_ms1_peaks_REF
    assert df_ref.equals(df)


@pytest.mark.skip(
    reason="Check the differences!"
)  # TODO: Jacobo for the future
def test_align_ms1_scans():
    df1 = pd.read_pickle(lx2_group_ms1_peaks_REF) # TODO recheck because iupdated lx2_group_ms1_peaks_REF
    # making a modified spectra
    df2 = pd.read_pickle(lx2_group_ms1_peaks_REF)
    df2 = df2.sample(frac=0.9, replace=True, random_state=1)
    df2 = recalibrate(df2, [500.0, 800.0], [0.001, -0.002])
    df2["inty"] = df2["inty"] * 0.85

    df1["stem"] = "filename1"
    df1["stem"] = df1["stem"].astype("category")

    df2["stem"] = "filename2"
    df2["stem"] = df2["stem"].astype("category")
    assert not df1.equals(df2)

    df = pd.concat([df1, df2])

    df = align_spectra(df)
    # print(df.dtypes)

    df_ref = pd.read_pickle(lx2_align_ms1_scans_ref_REF)
    # print(df_ref.dtypes)
    print(df.compare(df_ref))

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


@pytest.mark.skip(reason="not important now")
def test_drop_fuzzy():
    # TODO look into lx1_ref_masterscab:make_lx_spectra
    assert False


@pytest.mark.skip(reason="not important now")
def test_include_text():
    assert False


@pytest.mark.skip(reason="not important now")
def test_exclude_text():
    assert False


@pytest.mark.skip(reason="YAGNI, not used, is legacy")
def test_readfile():
    spectra_path = r"tests/resources/benchmark128/spectra/190321_Serum_Lipidextract_368723_01.mzML"
    options = {  # NOTE to initialize Masterscan(options) a dictionalry is not enough
        "timerange": (33.0, 1080.0),
        "MSmassrange": (360.0, 1000.0),
        "MSMSmassrange": (150.0, 1000.0),
        "MScalibration": [680.4802],
        "MSMScalibration": None,
    }
    scan = lx2_spectra(spectra_path, options)
    assert scan is not None

def test_spectra_2_DF(options):
    df, lx_data = spectra_2_DF(SPECTRA_PATH, options)
    df_ref = pd.read_pickle(lx2_group_ms1_peaks_REF)
    cols = ['mz','inty']
    assert (df[cols] - df_ref[cols]).describe().loc['mean'].abs().sum() < 0.01 # to have a little wiggle room, like no close
    assert (df[cols] - df_ref[cols]).describe().loc['std'].abs().sum() < 0.01

def test_aligned_spectra_df(options):
    df, df_infos = aligned_spectra_df(options)
    df_ref = pd.read_pickle(lx2_align_ms1_scans_ref_REF)
    cols = ['mz','inty']
    assert df.shape == (3940, 8)

def test_make_masterscan(options):
    scan = make_masterscan(options)
    assert len(scan.listSurveyEntry) == 2095
