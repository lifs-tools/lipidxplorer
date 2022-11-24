import pytest
from pathlib import Path
from utils import (
    masterscan_2_df,
    read_options,
    make_MFQL_result,
    makeResultsString,
    compareMasterScans,
    compareResults,
)
from LX1_masterscan import make_lx1_masterscan
import pickle


@pytest.fixture
def get_options():
    options = read_options(r"test_resources\t_sim\project_data\tSIM_Stitched.lxp")
    return options


@pytest.fixture
def get_no_res_options():
    options = read_options(r"test_resources\t_sim\project_data\tSIM_Stitched.lxp")
    options["MSresolution"] = ""
    options["MSMSresolution"] = ""
    options["MSresolutionDelta"] = ""
    options["MSMSresolutionDelta"] = ""
    return options


@pytest.fixture
def get_masterscan(get_options):
    return make_lx1_masterscan(get_options)


@pytest.fixture
def get_no_res_masterscan(get_no_res_options):
    return make_lx1_masterscan(get_no_res_options)


@pytest.fixture
def getMfqlFiles():
    p = Path(r"test_resources\t_sim\mfqls")
    mfqls = p.glob("*.mfql")
    return {mfql.name: mfql.read_text() for mfql in mfqls}




def test_masterscan_2_df():
    with open(r"test_resources\t_sim\reference\masterscan_1.pkl", "rb") as f:
        reference1 = pickle.load(f)
    df1 = masterscan_2_df(reference1)

    with open(r"test_resources\t_sim\reference\masterscan_2.pkl", "rb") as f:
        reference2 = pickle.load(f)
    df2 = masterscan_2_df(reference2)

    assert len(reference1.listSurveyEntry) == df1.shape[0]
    assert len(reference2.listSurveyEntry) == df2.shape[0]
    assert (
        df2.shape[0] < 1.2 * df1.shape[0]
    )  # if they are roughly the same shape it indicates lx1 comparable clustering
    # pd.merge_asof(df1,df2.assign(precurmass_2=lambda x:x.precurmass), on='precurmass', direction='nearest', tolerance=0.05).to_clipboard()


def test_masterscan_manual(get_options, get_masterscan):
    assert get_options["MSresolution"]
    masterscan = get_masterscan
    with open(r"test_resources\t_sim\reference\masterscan_1.pkl", "rb") as f:
        reference = pickle.load(f)
    assert compareMasterScans(masterscan, reference)


def test_masterescan_automatic(get_no_res_options, get_no_res_masterscan):
    assert not get_no_res_options._data["MSresolution"]
    masterscan = get_no_res_masterscan
    with open(r"test_resources\t_sim\reference\masterscan_2.pkl", "rb") as f:
        reference = pickle.load(f)
    assert compareMasterScans(masterscan, reference)


def test_mfql_manual(get_masterscan, get_options, getMfqlFiles):
    with open(r"test_resources\t_sim\reference\result_1.pkl", "rb") as f:
        reference = pickle.load(f)
    result = make_MFQL_result(get_masterscan, getMfqlFiles, get_options, log_steps=True)
    assert compareResults(result, reference)

def test_mfql_stages( get_options, getMfqlFiles):
    with open(r"test_resources\t_sim\reference\masterscan_1.pkl", "rb") as f:
        masterscan = pickle.load(f)
    
    #after identification
    #after isotopic correction_ms
    #after merge_ids
    #after monoisotopic correction
    #after suchthat
    #after remove permutations

    # make it a callback

    result,  = make_MFQL_result(masterscan, getMfqlFiles, get_options, log_steps=True)


    assert False



def test_mfql_automatic(get_no_res_masterscan, get_no_res_options, getMfqlFiles):
    with open(r"test_resources\t_sim\reference\result_2.pkl", "rb") as f:
        reference = pickle.load(f)
    result = make_MFQL_result(
        get_no_res_masterscan, getMfqlFiles, get_no_res_options, log_steps=True
    )
    # to see results print(makeResultsString(result, get_options))
    assert compareResults(result, reference)


def test_multi_id_isotopic_correction(getMfqlFiles, get_options):
    with open(r"test_resources\t_sim\reference\masterscan_1.pkl", "rb") as f:
        scan = pickle.load(f)
    scan.listSurveyEntry = [e for e in scan.listSurveyEntry if 760 < e.precurmass < 860]

    problem_mz = [798.5179466, 826.5485398, 854.5812816]
    problem_mz = [round(mz, 2) for mz in problem_mz]

    # problem_se = [se for se in scan.listSurveyEntry if round(se.precurmass,3) in problem_mz]
    # above values modified by runing the query

    mfql_keys = ["QS_MS1_PId5 (M-H)-.mfql", "QS_MS1_PSd5 (M-H)-.mfql"]
    mfqlFiles = {k: getMfqlFiles[k] for k in mfql_keys}
    result = make_MFQL_result(scan, mfqlFiles, get_options, log_steps=True)
    result.resultSC.listSurveyEntry = [
        se for se in result.resultSC.listSurveyEntry if len(se.listPrecurmassSF) > 1
    ]
    # to see results print(makeResultsString(result, get_options))
    problem_res = [
        se
        for se in result.resultSC.listSurveyEntry
        if round(se.precurmass, 2) in problem_mz
    ]
    is_ok = True
    for se in problem_res:
        for k, v in se.dictIntensity.items():
            if v == 0:
                continue
            ratio = se.dictBeforeIsocoIntensity[k] / v
            ratio = round(ratio, 1)
            if ratio != round(se.monoisotopicRatio, 1):
                is_ok = False
                break

    assert is_ok

