import pytest
from lx.tools import op
from utils import read_options
from LX1_masterscan import make_lx1_masterscan
import pickle


@pytest.fixture
def get_options():
    options = read_options(
        r"test_resources\t_sim\t_sim_project\tSIM_Stitched.lxp"
    )
    return options

@pytest.fixture
def get_no_res_options():
    options = read_options(
        r"test_resources\t_sim\t_sim_project\tSIM_Stitched.lxp"
    )
    options['MSresolution'] = ''
    options['MSMSresolution'] = ''
    options['MSresolutionDelta'] = ''
    options['MSMSresolutionDelta'] = ''

    return options

# def test_masterscan_by_lx1(get_options):
#     masterscan = make_masterscan(get_options)
#     assert False

def test_masterscan_manual(get_options):
    assert get_options['MSresolution']
    masterscan = make_lx1_masterscan(get_options)
    with open(r"test_resources\t_sim\reference_1.pkl", 'rb') as f: 
        reference = pickle.load(f)

    assert compareMasterScans(masterscan, reference)

def test_masterescan_automatic(get_no_res_options):
    assert not get_no_res_options['MSresolution']

    masterscan = make_lx1_masterscan(get_no_res_options)
    assert False

def test_mfql_manual():
    assert False

def test_mfql_automatic():
    assert False

def compareMasterScans(created, reference):
    c_ls = created.listSurveyEntry
    a_ls = reference.listSurveyEntry

    same = True
    for c, a in zip(c_ls, a_ls):
        if c != a:
            same = False
            break
    return same