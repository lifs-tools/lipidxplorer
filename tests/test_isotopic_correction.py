import pytest
import pickle

from lx.mfql.runtimeExecution import TypeResult, TypeMFQL


def test_isotopic_correction():
    with open(r"test_resources\t_sim\reference\type_result_1.pkl", "rb") as f:
        reference = pickle.load(f)

    result = reference
    result.isotopicCorrectionMS()
    # in reference.mfqlObj.sc.listSurveyEntry  the intensities changed
    

    assert False
