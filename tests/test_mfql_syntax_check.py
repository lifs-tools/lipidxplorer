"""The MFQL editor's syntax check (lx/mfql/mfqlSyntaxCheck.py)."""

import pytest

from lx.mfql.mfqlSyntaxCheck import check

GOOD = """QUERYNAME = PCpos;
DEFINE pr = 'C[30..50] H[30..200] N[1] O[8] P[1]' WITH DBR = (1.5,8.5), CHG = 1;
DEFINE h1 = 'C5 H15 O4 P1 N1' WITH CHG = 1;
# comment with umlaut: Fettsäure
IDENTIFY
	pr IN MS1+ AND
	h1 IN MS2+
SUCHTHAT
	isOdd(pr.chemsc[H])
REPORT
	MASS = pr.mass;
	NAME = "PC %d:%d" % "((pr.chemsc)[C] - 8, (pr.chemsc)[db] - 1.5)";
	;
"""


def errors(text):
    return [p for p in check(text) if p.severity == "error"]


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_valid_query_has_no_problems(newline):
    assert check(GOOD.replace("\n", newline)) == []


def test_empty_or_comment_only_file_is_not_an_error():
    assert check("") == []
    assert check("# new query\n\n") == []


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_missing_semicolon_points_at_next_line(newline):
    text = GOOD.replace("MASS = pr.mass;", "MASS = pr.mass").replace("\n", newline)
    (p,) = errors(text)
    assert (p.line, p.column) == (12, 2)
    assert p.message.startswith("Syntax error at 'NAME'.")
    assert "';' missing" in p.message


def test_missing_final_semicolon():
    (p,) = errors(GOOD.rstrip().rstrip(";"))
    assert "Unexpected end" in p.message


@pytest.mark.parametrize("old, new, expected_line, expected_text", [
    ("h1 IN MS2+", "h2 IN MS2+", 7, 'Variable "h2" in query "PCpos" does not exist.'),
    ("\th1 IN MS2+", "\tpr IN MS2+", 3, "The variable 'h1' in query 'PCpos' has to be used in IDENTIFY"),
    ("CHG = 1;\nDEFINE h1", "CHG = 1, TOLERANCE = 0 ppm;\nDEFINE h1", 2, "can not be smaller or equal zero"),
    ("'C5 H15 O4 P1 N1'", "'C5 H15 O4 P1 N1 Xx'", 3, "Invalid sum composition"),
    ("IDENTIFY\n", "IDENTIFY PC WHERE\n", 5, "Please remove the query name after 'IDENTIFY'"),
    ("QUERYNAME = PCpos;", "QUERYNAME = PC_pos;", 1, "No underscore allowed."),
])
def test_errors_the_run_would_report(old, new, expected_line, expected_text):
    assert old in GOOD
    (p,) = errors(GOOD.replace(old, new, 1))
    assert p.line == expected_line
    assert expected_text in p.message


def test_only_one_query_per_file():
    (p,) = errors(GOOD + GOOD)
    assert p.message == "There is only one query per *.mfql file allowed!"


def test_illegal_character_is_a_warning_only():
    problems = check(GOOD.replace("CHG = 1;\nDEFINE h1", "CHG = 1; @\nDEFINE h1"))
    assert [p.severity for p in problems] == ["warning"]
