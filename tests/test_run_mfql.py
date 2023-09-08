import pickle
import pytest
from pathlib import Path

from utils import (
    getMfqlFiles,
    make_MFQL_result,
    makeResultsString,
    proy_path,
    read_options,
)

ROOT_SMALL_TEST = r"tests/resources/small_test/"
EXPECTED_OUTPUT_PATH = r"tests/resources/small_test/small_test-out.csv"


@pytest.fixture
def out_reference():
    return Path(EXPECTED_OUTPUT_PATH).read_text()


def test_run_mfql(out_reference):
    options = read_options(proy_path)

    with open(options["masterScanFileRun"], "rb") as handle:
        masterscan = pickle.load(handle)
    masterscan.listSurveyEntry = [
        se for se in masterscan.listSurveyEntry if 600 < se.peakMean < 750
    ]
    for se in masterscan.listSurveyEntry:
        se.listMSMS = [msms for msms in se.listMSMS if 360 < msms.mass < 380]

    mfqlFiles = getMfqlFiles(ROOT_SMALL_TEST)

    result = make_MFQL_result(masterscan, mfqlFiles, options, log_steps=True)
    resultStr = makeResultsString(result, options)

    assert resultStr.strip() == out_reference.strip()
