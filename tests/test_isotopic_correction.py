import pytest
import pickle
from utils import read_options
from lx.mfql.runtimeExecution import TypeResult, TypeMFQL

OPTIONS_PATH = r"tests/resources/t_sim/project_data/tSIM_Stitched.lxp"
RESULT_PICKLE = r"tests/resources/t_sim/reference/type_result_1.pkl"


def test_isotopic_correction():
    options = read_options(OPTIONS_PATH)
    with open(RESULT_PICKLE, "rb") as f:
        reference = pickle.load(f)

    reference.mfqlObj.options["MSresolution"] = options["MSresolution"]
    reference.isotopicCorrectionMS()
    # in reference.mfqlObj.sc.listSurveyEntry  the intensities changed
    changed = [
        se
        for se in reference.mfqlObj.sc.listSurveyEntry
        if se.dictBeforeIsocoIntensity
    ]

    assert 198 == len(changed)
