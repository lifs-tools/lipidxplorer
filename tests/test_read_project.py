import pytest
import pickle
from utils import proy_path, read_options


def test_read_project():
    options = read_options(proy_path)
    with open(r'test_resources\small_test\expected_options.pkl','rb') as f: 
        expected_options = pickle.load(f)

    assert str(expected_options) == str(options)


def test_trigger_calcres():
    options = read_options(proy_path, make_msresolution_auto=True)
    # assert options["MSresolution"] == "auto"
    assert options["alignmentMethodMS"] == "calctol"
    assert options["alignmentMethodMSMS"] == "calctol"
    assert options["scanAveragingMethod"] == "calctol"
