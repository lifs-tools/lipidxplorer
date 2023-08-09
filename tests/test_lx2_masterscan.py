import pandas as pd
import pytest
from legacy.lx2_masterscan import lx2_spectra
from lx1_refactored import (add_bins, aggregate_groups, filter_intensity,
                            filter_repetition_rate, merge_peaks_from_scan,
                            spectra2df)

ROOT_PATH = r"tests\resources\small_test"
OPTIONS_PATH = ROOT_PATH + r"\small_test-project.lxp"
SPECTRA_PATH = ROOT_PATH + r"\190321_Serum_Lipidextract_368723_01.mzML"
ms1_peaks_REF = ROOT_PATH + r"\test_get_ms1_peaks_ref.pkl"
lx2_group_ms1_peaks_REF = ROOT_PATH + r"\test_get_lx2_ms1_peaks_ref.pkl"

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
    df = spectra2df(SPECTRA_PATH, **settings)
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
    df = spectra2df(SPECTRA_PATH, **settings)
    assert df.shape == (302188, 8)


def test_group_ms1_peaks():
    options = {"MSfilter":0.7, "MSthreshold":0.5}
    df = pd.read_pickle(ms1_peaks_REF)
    df = add_bins(df)
    df = merge_peaks_from_scan(df)
    assert df.shape == (65897, 14) # NOTE same for LX1 test
    df, lx_data = aggregate_groups(df)
    assert df.shape == (3046, 7)#(6707, 7)
    mask = filter_repetition_rate(
        df, lx_data["scan_count"], options["MSfilter"]
    )
    df = df[mask]
    assert df.shape == (1729, 7)
    mask = filter_intensity(df, options["MSthreshold"])
    df = df[mask]
    assert df.shape == (1729, 7)
    df_ref = pd.read_pickle(lx2_group_ms1_peaks_REF)
    assert df_ref.equals(df)

@pytest.mark.skip(
    reason="not important now"
)
def test_drop_fuzzy():
    # TODO look into lx1_ref_masterscab:make_lx_spectra
    assert False

@pytest.mark.skip(
    reason="not important now"
)
def test_include_text():
    assert False

@pytest.mark.skip(
    reason="not important now"
)
def test_exclude_text():
    assert False

@pytest.mark.skip(
    reason="YAGNI, not used, is legacy"
)
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
