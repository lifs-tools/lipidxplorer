"""Every module under `lx/` must actually import.

This is the smoke test named in the migration design doc (section 5): it
walks every module under `lx/` with `importlib` and imports it for real,
so a numpy/pandas pin regression -- or any other broken dependency --
fails here instead of only surfacing when a user opens the matching
feature. `tests/test_internal_imports.py` checks a narrower, static thing
(that `import lx.*` statements name a path that exists on disk); it does
not execute any import and so cannot catch this class of failure. The two
tests are complementary, not redundant.

Run empirically against this branch: 44 modules under `lx/`, 43 import
cleanly, and 1 fails --
`lx.fileReader.mzAPI.mzWiff: ModuleNotFoundError: No module named
'wiffbridge'`. `wiffbridge` is a SCIEX .wiff bridge module that is not
part of this repository (see CHANGELOG and tests/test_internal_imports.py
for the related, but distinct, doubled-import-path fix). That single
known failure is recorded below as an xfail; if this list and the real
import results ever diverge, this test is the one that is wrong.
"""

import importlib
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# module dotted name -> reason, naming the missing dependency.
KNOWN_IMPORT_FAILURES = {
    "lx.fileReader.mzAPI.mzWiff": "missing dependency: wiffbridge (not part of this repository)",
}


def _module_names():
    names = []
    for path in sorted((REPO_ROOT / "lx").rglob("*.py")):
        rel = path.relative_to(REPO_ROOT)
        parts = list(rel.parts)
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1][:-3]
        names.append(".".join(parts))
    return names


def test_module_collector_found_a_sensible_number():
    # Same defensive floor as test_internal_imports.py: a parametrized test
    # over an empty list reports "skipped", not "failed", so if a refactor
    # of _module_names() ever made it return nothing, test_module_imports
    # below would silently stop testing anything while still looking green.
    names = _module_names()
    assert len(names) > 20, (
        f"expected substantially more than 20 modules under lx/, found {len(names)}"
    )


@pytest.mark.parametrize("module", _module_names())
def test_module_imports(module):
    if module in KNOWN_IMPORT_FAILURES:
        pytest.xfail(KNOWN_IMPORT_FAILURES[module])
    importlib.import_module(module)
