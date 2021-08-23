from x_masterscan import compareMasterScans
import pytest
from lx.spectraImport import doImport, lpdxImportDEF_new
from lx.spectraTools import loadSC
from utils import read_options, proy_path, expected_ms_path, make_masterscan
from lx.spectraTools import loadSC

def test_make_masterscan():
    options = read_options(proy_path)
    masterscan = make_masterscan(options)
    expected = loadSC(expected_ms_path)
    expected.listSurveyEntry =  expected.listSurveyEntry[:100]
    assert compareMasterScans(masterscan, expected)




