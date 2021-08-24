import pytest
from pathlib import Path
import pickle

from utils import read_options, proy_path, getMfqlFiles, make_MFQL_result, makeResultsString, out_reference

def test_run_mfql():
    # proy = r'test_resources\small_test\small_test-project.lxp'
    options = read_options(proy_path)
    with open(options['masterScanFileRun'],'rb') as handle:
        masterscan = pickle.load(handle)
    masterscan.listSurveyEntry = [se for se in masterscan.listSurveyEntry if 600< se.peakMean <750]
    mfqlFiles = getMfqlFiles(r'test_resources\small_test')
    result = make_MFQL_result(masterscan, mfqlFiles, options)
    resultStr = makeResultsString(result, options)
    
    assert resultStr.strip() == out_reference.strip()