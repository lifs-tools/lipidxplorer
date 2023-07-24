import pytest

from lx1_refactored import (
    spectra2df, 
)

SIM_PATH = r"tests\resources\t_sim\sim_sample.mzML"

def test_read_sim_spectra():
    settings =  {
        'read_sim_scans' : True,
        'read_ms1_scans' : False,
        'read_ms2_scans' : False,
        "time_start": 33.0,
        "time_end": 1080.0,
        "ms1_start": 360.0,
        "ms1_end": 1000.0,
        "ms2_start": 150.0,
        "ms2_end": 1000.0,
    }
    df = spectra2df(SIM_PATH, **settings)
    assert False

def test_parse_filter_line():
    assert False

def test_replace_lock_in_Filter_line():
    assert False

def test_find_overlap():
    assert False

def test_overlap_is_consistent():
    assert False

def test_trim_sims():
    assert False

def test_find_gaps():
    assert False

def test_join_sims():
    assert False

def test_recalibrate_with_ms1():
    assert False

def test_output_mzml():
    # see https://git.mpi-cbg.de/labShevchenko/simtrim/-/blob/master/simtrim/simtrim.py
   
    assert False


