import pytest
from lx.spectraImport import doImport, lpdxImportDEF_new
from lx.spectraTools import loadSC
from x_masterscan import compareMasterScans

from utils import (
    expected_ms_path,
    expected_lx2ms_path,
    make_masterscan,
    proy_path,
    read_options,
)
from LX2_masterscan import make_lx2_masterscan

# from memory_profiler import profile


def test_make_masterscan():
    options = read_options(proy_path)
    masterscan = make_masterscan(options)
    expected = loadSC(expected_ms_path)
    expected.listSurveyEntry = expected.listSurveyEntry[:100]
    masterscan.listSurveyEntry = masterscan.listSurveyEntry[:100]
    assert compareMasterScans(masterscan, expected)


def test_make_lx2_masterscan():
    options = read_options(proy_path)
    masterscan = make_lx2_masterscan(options)
    expected = loadSC(expected_lx2ms_path)
    expected.listSurveyEntry = expected.listSurveyEntry[:100]
    masterscan.listSurveyEntry = masterscan.listSurveyEntry[:100]
    assert compareMasterScans(masterscan, expected)

