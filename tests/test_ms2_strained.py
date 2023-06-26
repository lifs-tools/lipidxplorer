import pytest
from pathlib import Path
from utils import (
    read_options,
    make_MFQL_result,
    make_masterscan,
    compareResults,
    compareMasterScans,
)
from LX1_masterscan import make_lx_masterscan


@pytest.fixture
def get_options():
    options = read_options(
        r"tests/resources/ms2_strained/project_data/PRM_import.lxp"
    )
    return options


@pytest.fixture
def get_masterscan(get_options):
    # import pickle
    # with open(r"tests/resources/ms2_strained/reference/masterscan_1.pkl", "rb") as f:
    #     reference = pickle.load(f)
    return make_masterscan(get_options, lx_version=1)


@pytest.fixture
def get_lx1_refactored_masterscan(get_options):
    return make_lx_masterscan(get_options, lx_version=1)


@pytest.fixture
def get_lx2_masterscan(get_options):
    options = get_options  # just to validate that that info is not being used
    options["MSresolution"] = ""
    options["MSMSresolution"] = ""
    options["MSresolutionDelta"] = ""
    options["MSMSresolutionDelta"] = ""
    options["lx2_MSresolution"] = True
    return make_lx_masterscan(options, lx_version=2)


@pytest.fixture
def getMfqlFiles():
    p = Path(r"tests/resources/ms2_strained/mfqls")
    mfqls = p.glob("*.mfql")
    return {mfql.name: mfql.read_text() for mfql in mfqls}


# TODO: @Jacobo
@pytest.mark.skip(reason="not validated yet")
def test_masterscan_lx_vs_lx1(get_masterscan, get_lx1_refactored_masterscan):
    # with open(r"tests/resources/ms2_strained/reference/masterscan_1.pkl", "rb") as f:
    #     reference = pickle.load(f)
    assert compareMasterScans(get_masterscan, get_lx1_refactored_masterscan)


# TODO: @Jacobo
@pytest.mark.skip(reason="not validated yet")
def test_masterescan_lx_vs_lx2(
    get_masterscan, get_lx2_masterscan
):

    assert compareMasterScans(get_masterscan, get_lx2_masterscan)


# TODO: @Jacobo
@pytest.mark.skip(reason="not validated yet")
def test_mfql_lx_vs_lx1(get_masterscan, get_lx1_refactored_masterscan, get_options, getMfqlFiles):

    result1 = make_MFQL_result(
        get_masterscan, getMfqlFiles, get_options, log_steps=True
    )

    result2 = make_MFQL_result(
        get_lx1_refactored_masterscan,
        getMfqlFiles,
        get_options,
        log_steps=True,
    )

    assert compareResults(result1, result2)


# TODO: @Jacobo
@pytest.mark.skip(reason="not validated yet")
def test_mfql_lx_vs_lx2(get_masterscan,get_lx2_masterscan, get_options, getMfqlFiles):

    result1 = make_MFQL_result(
        get_masterscan, getMfqlFiles, get_options, log_steps=True
    )

    result2 = make_MFQL_result(
        get_lx2_masterscan, getMfqlFiles, get_options, log_steps=True
    )

    assert compareResults(result1, result2)
