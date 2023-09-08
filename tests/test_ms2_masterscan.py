import pytest

from utils import read_options


OPTIONS_PATH = r"tests/resources/small_test/small_test-project.lxp"


@pytest.fixture
def get_options():
    options = read_options(OPTIONS_PATH)
    return options


def test_options(get_options):
    assert get_options["importDir"] == "tests/resources/small_test"


@pytest.mark.skip(reason="Make it work later")  # TODO: Jacobo for the future
def test_get_ms1_peaks():
    assert False


@pytest.mark.skip(reason="Make it work later")  # TODO: Jacobo for the future
def test_drop_fuzzy():
    assert False


@pytest.mark.skip(reason="Make it work later")  # TODO: Jacobo for the future
def test_include_text():
    assert False


@pytest.mark.skip(reason="Make it work later")  # TODO: Jacobo for the future
def test_exclude_text():
    assert False