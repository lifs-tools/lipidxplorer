import pickle
import pytest
from LX2_masterscan import make_lx2_masterscan

from utils import (
    getMfqlFiles,
    make_MFQL_result,
    makeResultsString,
    proy_path,
    read_options,
)


# TODO: @Jacobo
@pytest.mark.skip(reason="out_reference is not defined!")
def test_run_mfql():
    options = read_options(proy_path)

    with open(options["masterScanFileRun"], "rb") as handle:
        masterscan = pickle.load(handle)
    masterscan.listSurveyEntry = [
        se for se in masterscan.listSurveyEntry if 600 < se.peakMean < 750
    ]
    for se in masterscan.listSurveyEntry:
        se.listMSMS = [msms for msms in se.listMSMS if 360 < msms.mass < 380]

    mfqlFiles = getMfqlFiles(r"test_resources/small_test")

    result = make_MFQL_result(masterscan, mfqlFiles, options, log_steps=True)
    resultStr = makeResultsString(result, options)

    assert resultStr.strip() == out_reference.strip()


# TODO: @Jacobo
@pytest.mark.skip(reason="out_reference is not defined!")
def test_lx2_sc_on_run_mfql():
    options = read_options(proy_path)

    with open(r"tests/resources/small_test/small_test.sc", "rb") as fh:
        scan = pickle.load(fh)  # make_lx2_masterscan(options)

    scan.listSurveyEntry = [
        se for se in scan.listSurveyEntry if 600 < se.peakMean < 750
    ]
    for se in scan.listSurveyEntry:
        se.listMSMS = [msms for msms in se.listMSMS if 360 < msms.mass < 380]

    mfqlFiles = getMfqlFiles(r"test_resources/small_test")

    result_lx2 = make_MFQL_result(scan, mfqlFiles, options)
    resultStr_lx2 = makeResultsString(result_lx2, options)

    assert resultStr_lx2.strip() == out_reference.strip()
