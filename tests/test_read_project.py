import pytest
from utils import read_options, expected_options_str, proy_path

def test_read_project():
    options = read_options(proy_path)

    assert expected_options_str == str(options)