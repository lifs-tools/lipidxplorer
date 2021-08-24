import pytest

from utils import expected_options_str, proy_path, read_options


def test_read_project():
    options = read_options(proy_path)

    assert expected_options_str == str(options)
