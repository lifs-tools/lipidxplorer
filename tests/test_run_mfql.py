import pickle
from pathlib import Path

import pytest

from utils import (
    getMfqlFiles,
    make_MFQL_result,
    makeResultsString,
    out_reference,
    proy_path,
    read_options,
)


def test_run_mfql():
    options = read_options(proy_path)
    with open(options["masterScanFileRun"], "rb") as handle:
        masterscan = pickle.load(handle)
    masterscan.listSurveyEntry = [
        se for se in masterscan.listSurveyEntry if 600 < se.peakMean < 750
    ]
    for se in masterscan.listSurveyEntry:
        se.listMSMS = [msms for msms in se.listMSMS if 360 < msms.mass < 380]
    mfqlFiles = getMfqlFiles(r"test_resources\small_test")
    result = make_MFQL_result(masterscan, mfqlFiles, options)
    resultStr = makeResultsString(result, options)

    assert resultStr.strip() == out_reference.strip()
