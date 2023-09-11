import pytest
import pandas as pd
from pathlib import Path

from lx1_refactored import (
    spectra_as_df,
    parse_filter_string,
    stitch_sim_scans,
    recalibrate_with_ms1,
    dataframe2mzml,
    sim_trim,
    write2templateMzXML,
)

SIM_PATH = r"tests/resources/t_sim/spectra/sim_sample.mzML"
ref_SIM_SPECTRA = r"tests/resources/t_sim/reference/ref_SIM_SPECTRA.pkl"


def test_read_sim_spectra():
    settings = {
        "ms_level": 'sim',
        "polarity": -1,
        "time_start": 33.0,
        "time_end": 1080.0,
        "ms1_start": 360.0,
        "ms1_end": 1000.0,
        "ms2_start": 150.0,
        "ms2_end": 1000.0,
    }
    df = spectra_as_df(SIM_PATH, **settings)
    assert df.shape == (12399, 8)
    df_ref = pd.read_pickle(ref_SIM_SPECTRA)
    assert df_ref.equals(df)


def test_parse_filter_string():
    df = pd.read_pickle(ref_SIM_SPECTRA)
    filter_string_df = parse_filter_string(df)
    assert filter_string_df.shape == (33, 7)


def test_trim_and_join_spectra():
    df = pd.read_pickle(ref_SIM_SPECTRA)
    filter_string_df = parse_filter_string(df)
    fixed = 11.0
    filter_string_df["_trim_overlap"] = fixed
    assert filter_string_df.shape == (33, 7)


def test_sim_stitcher():
    df = pd.read_pickle(ref_SIM_SPECTRA)
    ref = df["filter_string"].unique().shape
    ref_shape = df.shape
    filter_string_df = parse_filter_string(df, trim_overlap=18.0)
    df = stitch_sim_scans(df, filter_string_df, replace_filter_string=True)
    assert df.shape != ref_shape and ref != df["filter_string"].unique().shape


def test_sim_trim():
    simrtim = sim_trim(SIM_PATH, 18)
    dest = Path(simrtim)
    assert dest.is_file()
    dest.unlink()
    Path(simrtim + "-idx.json").unlink()


@pytest.mark.skip(
    reason="YAGNI, not tested and never used in original codebase"
)
def test_recalibrate_with_ms1():
    recalibrate_with_ms1(None)
    assert False


def test_output_mzml():
    df = pd.read_pickle(ref_SIM_SPECTRA)
    filter_string_df = parse_filter_string(df, trim_overlap=15.0)
    df = stitch_sim_scans(df, filter_string_df, replace_filter_string=True)
    destination = dataframe2mzml(df, SIM_PATH)
    dest = Path(destination)
    assert dest.is_file()
    dest.unlink()


def test_output_mzxml():
    df = pd.read_pickle(ref_SIM_SPECTRA)
    res = write2templateMzXML(SIM_PATH + ".mzxml", df)
    dest = Path(SIM_PATH + ".mzxml")
    assert dest.is_file()
    dest.unlink()
