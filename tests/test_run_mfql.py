import pytest
from pathlib import Path
import pickle

from utils import read_options, proy_path, getMfqlFiles, make_MFQL_result, makeResultsString

def test_run_mfql():
    options = read_options(proy_path)
    # masterscan = make_masterscan(options)
    with open(options['masterScanFileRun'],'rb') as handle:
        masterscan = pickle.load(handle)
    mfqlFiles = getMfqlFiles(r'test_resources\small_test')
    result = make_MFQL_result(masterscan, mfqlFiles, options)
    resultStr = makeResultsString(result, options)
    reference = Path(r'..\test_resources\small_test\small_test-out.csv').read_text()
    print(f'are same {resultStr == reference}')

    assert resultStr == reference