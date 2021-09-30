import pytest
from lx.spectraImport import doImport, lpdxImportDEF_new
from lx.spectraTools import loadSC
from x_masterscan import compareMasterScans

from utils import expected_ms_path, make_masterscan, proy_path, read_options


def test_make_masterscan():
    options = read_options(proy_path)
    masterscan = make_masterscan(options)
    expected = loadSC(expected_ms_path)
    expected.listSurveyEntry = expected.listSurveyEntry[:100]
    assert compareMasterScans(masterscan, expected)
