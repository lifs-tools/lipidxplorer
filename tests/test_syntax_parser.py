"""lx/mfql/syntaxParser.py: the MFQL syntax check used by the editor.

The first tests make sure its grammar is the same as the real parser's
(lx/mfql/mfqlParser.py). If they fail after a change of the MFQL language,
make the same change in syntaxParser.py.
"""

import re

import pytest

from lx.mfql import mfqlParser, syntaxParser
from lx.mfql.syntaxParser import checkText, startSyntaxCheck
from lx.exceptions import SyntaxErrorException


def _productions(module):
    prods = set()
    for name in dir(module):
        f = getattr(module, name)
        if name.startswith("p_") and name != "p_error" and callable(f) and f.__doc__:
            lhs = None
            for line in f.__doc__.strip().splitlines():
                line = line.strip()
                if not line:
                    continue
                if ":" in line and not line.startswith("|"):
                    lhs, rhs = line.split(":", 1)
                    lhs = lhs.strip()
                else:
                    rhs = line.lstrip("|")
                prods.add("%s : %s" % (lhs, " ".join(rhs.split())))
    return prods


def _token_regexes(module):
    return {name: getattr(module, name) for name in dir(module)
            if name.startswith("t_") and isinstance(getattr(module, name), str)}


def test_grammar_rules_are_the_same_as_mfqlParser():
    real, check = _productions(mfqlParser), _productions(syntaxParser)
    assert sorted(real - check) == [], "rules missing in syntaxParser"
    assert sorted(check - real) == [], "rules only in syntaxParser"


def test_tokens_keywords_precedence_are_the_same_as_mfqlParser():
    assert set(syntaxParser.keywords) == set(mfqlParser.keywords)
    assert set(syntaxParser.tokens) == set(mfqlParser.tokens)
    assert syntaxParser.precedence == mfqlParser.precedence
    assert _token_regexes(syntaxParser) == _token_regexes(mfqlParser)


GOOD = """QUERYNAME = PCpos;
DEFINE Precursor = 'C[30..50] H[30..200] N[1] O[8] P[1]' WITH DBR = (1.5,8.5), CHG = 1;
DEFINE h1 = 'C5 H15 O4 P1 N1' WITH CHG = 1;
# comment with umlaut: Fettsäure
IDENTIFY
	Precursor IN MS1+ AND
	h1 IN MS2+
SUCHTHAT
	isOdd(Precursor.chemsc[H]) AND Precursor.chemsc <~ h1.chemsc
REPORT
	MASS = Precursor.mass;
	NAME = "PC %d:%d" % (Precursor.chemsc[C] - 8, Precursor.chemsc[db] - 1.5);
	;
"""


def errors(text):
    return [p for p in checkText(text) if p.severity == "error"]


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_valid_query_has_no_problems(newline):
    # 'Precursor', '<~' and REPORT "..." % (args) were rejected by the old version
    assert checkText(GOOD.replace("\n", newline)) == []


def test_empty_or_comment_only_file_is_not_an_error():
    assert checkText("") == []
    assert checkText("# new query\n\n") == []


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_missing_semicolon_points_at_next_line(newline):
    text = GOOD.replace("MASS = Precursor.mass;", "MASS = Precursor.mass").replace("\n", newline)
    (p,) = errors(text)
    assert (p.lineno, p.column) == (12, 2)
    assert p.message.startswith("Syntax error at 'NAME'.")
    assert "';' missing" in p.message


def test_missing_final_semicolon():
    (p,) = errors(GOOD.rstrip().rstrip(";"))
    assert "Unexpected end" in p.message


@pytest.mark.parametrize("old, new, expected_line, expected_text", [
    ("h1 IN MS2+", "h2 IN MS2+", 7, 'Variable "h2" in query "PCpos" does not exist.'),
    ("\th1 IN MS2+", "\tPrecursor IN MS2+", 3, "The variable 'h1' in query 'PCpos' has to be used in IDENTIFY"),
    ("CHG = 1;\nDEFINE h1", "CHG = 1, TOLERANCE = 0 ppm;\nDEFINE h1", 2, "can not be smaller or equal zero"),
    ("'C5 H15 O4 P1 N1'", "'C5 H15 O4 P1 N1 Xx'", 3, "Invalid sum composition"),
    ("IDENTIFY\n", "IDENTIFY PC WHERE\n", 5, "Please remove the query name after 'IDENTIFY'"),
    ("QUERYNAME = PCpos;", "QUERYNAME = PC_pos;", 1, "No underscore allowed."),
    ("REPORT", "INTERPRETATION Precursor.mass > 1\nREPORT", 10, "Syntax error at 'INTERPRETATION'"),
])
def test_errors_the_run_would_report(old, new, expected_line, expected_text):
    assert old in GOOD
    (p,) = errors(GOOD.replace(old, new, 1))
    assert p.lineno == expected_line
    assert expected_text in p.message


def test_only_one_query_per_file():
    (p,) = errors(GOOD + GOOD)
    assert p.message == "There is only one query per *.mfql file allowed!"


def test_illegal_character_is_a_warning_only():
    problems = checkText(GOOD.replace("CHG = 1;\nDEFINE h1", "CHG = 1; @\nDEFINE h1"))
    assert [p.severity for p in problems] == ["warning"]


def test_startSyntaxCheck_counts_and_raises_with_file_and_line():
    assert startSyntaxCheck({"a.mfql": GOOD, "b.mfql": GOOD}) == 2
    with pytest.raises(SyntaxErrorException) as info:
        startSyntaxCheck({"a.mfql": GOOD, "b.mfql": GOOD.replace("h1 IN", "h2 IN")})
    e = info.value
    assert (e.fileName, e.lineno) == ("b.mfql", 7)
    assert "h2" in e.p_value
