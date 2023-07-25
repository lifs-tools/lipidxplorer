import pytest
import pandas as pd

from lx1_refactored import spectra2df, parse_filter_string, trim_and_join_scans



SIM_PATH = r"tests\resources\t_sim\sim_sample.mzML"
ref_SIM_SPECTRA = r"tests\resources\t_sim\ref_SIM_SPECTRA.pkl"


def test_read_sim_spectra():
    settings = {
        "read_sim_scans": True,
        "read_ms1_scans": False,
        "read_ms2_scans": False,
        "polarity": -1,
        "time_start": 33.0,
        "time_end": 1080.0,
        "ms1_start": 360.0,
        "ms1_end": 1000.0,
        "ms2_start": 150.0,
        "ms2_end": 1000.0,
    }
    df = spectra2df(SIM_PATH, **settings)
    assert df.shape == (12399, 8)
    df_ref = pd.read_pickle(ref_SIM_SPECTRA)
    assert df_ref.equals(df)


def test_parse_filter_string():
    df = pd.read_pickle(ref_SIM_SPECTRA)
    filter_string_df = parse_filter_string(df)
    assert filter_string_df.shape == (33, 5)

def test_trim_and_join_spectra():
    df = pd.read_pickle(ref_SIM_SPECTRA)
    filter_string_df = parse_filter_string(df)
    fixed = 11.0
    filter_string_df["_trim_overlap"] = fixed
    assert filter_string_df.shape == (33, 7)

def test_trim_sims():
    df = pd.read_pickle(ref_SIM_SPECTRA)
    ref = df["filter_string"].unique().shape
    ref_shape = df.shape
    filter_string_df = parse_filter_string(df, trim_overlap=18.0)
    df = trim_and_join_scans(df, filter_string_df, replace_filter_string = True)
    assert df.shape != ref_shape and ref != df["filter_string"].unique().shape


def test_recalibrate_with_ms1():
    assert False


def test_output_mzml():
    # see https://git.mpi-cbg.de/labShevchenko/simtrim/-/blob/master/simtrim/simtrim.py

    assert False


