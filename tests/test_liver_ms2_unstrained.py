import pytest
from pathlib import Path
from utils import (
    read_options,
    make_MFQL_result,
    makeResultsString,
    compareResults,
    compareMasterScans,
)
from LX1_masterscan import make_lx1_masterscan
import pickle


@pytest.fixture
def get_options():
    options = read_options(
        r"tests/resources/liver_ms2_unstrained/project_data/PRM_import.lxp"
    )
    return options


@pytest.fixture
def get_no_res_options():
    options = read_options(
        r"tests/resources/liver_ms2_unstrained/project_data/PRM_import.lxp"
    )
    options["MSresolution"] = ""
    options["MSMSresolution"] = ""
    options["MSresolutionDelta"] = ""
    options["MSMSresolutionDelta"] = ""
    options["lx2_MSresolution"] = True
    return options


@pytest.fixture
def get_masterscan(get_options):
    return make_lx1_masterscan(get_options)


@pytest.fixture
def get_no_res_masterscan(get_no_res_options):
    return make_lx1_masterscan(get_no_res_options)


@pytest.fixture
def getMfqlFiles():
    p = Path(r"tests/resources/liver_ms2_unstrained/mfqls")
    mfqls = p.glob("*.mfql")
    return {mfql.name: mfql.read_text() for mfql in mfqls}


def test_masterscan_manual(get_options, get_masterscan):
    assert get_options["MSresolution"]
    masterscan = get_masterscan
    with open(
        r"tests/resources/liver_ms2_unstrained/reference/masterscan_1.pkl",
        "rb",
    ) as f:
        reference = pickle.load(f)
    assert compareMasterScans(masterscan, reference)


def test_masterescan_automatic(get_no_res_options, get_no_res_masterscan):
    assert not get_no_res_options._data["MSresolution"]
    masterscan = get_no_res_masterscan
    with open(
        r"tests/resources/liver_ms2_unstrained/reference/masterscan_2.pkl",
        "rb",
    ) as f:
        reference = pickle.load(f)
    assert compareMasterScans(masterscan, reference)


def test_mfql_manual(get_masterscan, get_options, getMfqlFiles):
    with open(
        r"tests/resources/liver_ms2_unstrained/reference/result_1.pkl", "rb"
    ) as f:
        reference = pickle.load(f)
    result = make_MFQL_result(
        get_masterscan, getMfqlFiles, get_options, log_steps=True
    )
    assert compareResults(result, reference)


def test_mfql_automatic(
    get_no_res_masterscan, get_no_res_options, getMfqlFiles
):
    with open(
        r"tests/resources/liver_ms2_unstrained/reference/result_2.pkl", "rb"
    ) as f:
        reference = pickle.load(f)
    result = make_MFQL_result(
        get_no_res_masterscan, getMfqlFiles, get_no_res_options, log_steps=True
    )
    # to see results print(makeResultsString(result, get_options))
    assert compareResults(result, reference)
