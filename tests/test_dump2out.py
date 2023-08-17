import pandas as pd
from tools import replace_results_with_min_abs_error

OUT_FILE = r"tests/resources/dump2out/Trim-out-5 ppm.csv"
DUMP_FILE = r"tests/resources/dump2out/Trim-dump- 5 ppm.csv"
EXPECTED_FILE = r"tests/resources/dump2out/Trim-out-5 ppm_v2_ref.csv"


def test_check_and_relace_results():
    lines_out = replace_results_with_min_abs_error(
        OUT_FILE, DUMP_FILE, result_file=None
    )

    with open(EXPECTED_FILE, "r") as file:
        lines = file.readlines()

    assert lines_out == lines
