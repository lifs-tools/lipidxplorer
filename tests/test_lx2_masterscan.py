import pytest
from legacy.lx2_masterscan import lx2_spectra


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
