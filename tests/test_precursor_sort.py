"""Result candidates are ordered by the |errppm| of their precursor.

A precursor marked by an sc-constraint without a sum composition has
errppm None; ordering must not raise TypeError on it.
"""

from types import SimpleNamespace

from lx.mfql.runtimeExecution import _precursorAbsErrppm


def _mark(scope, errppm):
    return SimpleNamespace(scope=scope, errppm=errppm)


def test_uses_the_absolute_errppm_of_the_precursor():
    candidate = {"PR": _mark("MS1-", -2.5), "FA": _mark("MS2-", 0.1)}
    assert _precursorAbsErrppm(candidate) == 2.5


def test_lowest_absolute_errppm_sorts_first():
    candidates = [
        {"PR": _mark("MS1+", -3.0)},
        {"PR": _mark("MS1+", 1.0)},
        {"PR": _mark("MS1+", -0.5)},
    ]
    ordered = sorted(candidates, key=_precursorAbsErrppm)
    assert [c["PR"].errppm for c in ordered] == [-0.5, 1.0, -3.0]


def test_precursor_without_errppm_sorts_last_instead_of_raising():
    candidates = [
        {"PR": _mark("MS1+", None)},
        {"PR": _mark("MS1+", 2.0)},
    ]
    ordered = sorted(candidates, key=_precursorAbsErrppm)
    assert [c["PR"].errppm for c in ordered] == [2.0, None]
