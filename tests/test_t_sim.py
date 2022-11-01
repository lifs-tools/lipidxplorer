import pytest
from pathlib import Path
from utils import read_options, make_MFQL_result, makeResultsString
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


def test_mfql_automatic(get_no_res_masterscan, get_no_res_options, getMfqlFiles):
    with open(r"test_resources\t_sim\reference\result_2.pkl", "rb") as f:
        reference = pickle.load(f)
    result = make_MFQL_result(
        get_no_res_masterscan, getMfqlFiles, get_no_res_options, log_steps=True
    )
    #to see results print(makeResultsString(result, get_options))
    assert compareResults(result, reference)

def test_multi_id_isotopic_correction(getMfqlFiles, get_options):
    with open(r"test_resources\t_sim\reference\masterscan_1.pkl", "rb") as f:
        scan = pickle.load(f)
    scan.listSurveyEntry = [e for e in scan.listSurveyEntry if 760 < e.precurmass < 860]
    
    problem_mz = [798.5179466, 826.5485398, 854.5812816]
    problem_mz = [round(mz,2) for mz in problem_mz]

    #problem_se = [se for se in scan.listSurveyEntry if round(se.precurmass,3) in problem_mz]
    #above values modified by runing the query

    mfql_keys = ['QS_MS1_PId5 (M-H)-.mfql','QS_MS1_PSd5 (M-H)-.mfql']
    mfqlFiles = {k:getMfqlFiles[k] for k in mfql_keys}
    result = make_MFQL_result(scan, mfqlFiles, get_options, log_steps=True)
    result.resultSC.listSurveyEntry = [se for se in result.resultSC.listSurveyEntry if len(se.listPrecurmassSF)>1]
    #to see results print(makeResultsString(result, get_options))
    problem_res = [se for se in result.resultSC.listSurveyEntry if round(se.precurmass,2) in problem_mz]
    is_ok = True
    for se in problem_res:
        for k,v in se.dictIntensity.items():
            if v == 0: continue
            ratio = se.dictBeforeIsocoIntensity[k] / v
            ratio = round(ratio,1)
            if ratio != round(se.monoisotopicRatio,1) :
                is_ok = False
                break

    assert is_ok


def compareMasterScans(created, reference):
    c_ls = created.listSurveyEntry
    a_ls = reference.listSurveyEntry

    same = True
    for c, a in zip(c_ls, a_ls):
        if c != a:
            same = False
            break
            # TODO does this work and check the listMSMS ?

    return same

def compareResults(created, reference):
    # col_headers = reference.listHead
    same = True
    for k in reference.dictQuery:
        created_q = created.dictQuery[k]
        reference_q = reference.dictQuery[k]

        for col_header in reference_q.dataMatrix:
            for idx,val in enumerate(reference_q.dataMatrix[col_header]):
                if created_q.dataMatrix[col_header][idx] != val:
                    same =False
                    break
    return same



