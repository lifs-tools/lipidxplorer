import pytest

from utils import expected_options_str, proy_path, read_options


def test_read_project():
    options = read_options(proy_path)

    assert expected_options_str == str(options)


def test_trigger_calcres():
    options = read_options(proy_path, make_msresolution_auto=True)
    # assert options["MSresolution"] == "auto"
    assert options["alignmentMethodMS"] == "calctol"
    assert options["alignmentMethodMSMS"] == "calctol"
    assert options["scanAveragingMethod"] == "calctol"
