"""Every `import lx.*` statement must name a module that exists.

The 2to3 pass rewrote some absolute imports into paths that were never
valid. Because the broken ones sit in lazily-imported branches, nothing
raises until a user opens the matching file format.

Resolution is filesystem-based on purpose. Importing the packages for real
would execute their __init__ modules, which reach for optional Windows-only
dependencies, and the test would fail for reasons it is not testing.
"""

import ast
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Pre-existing dead branches, documented in the design doc. They name modules
# that have never existed in this repository. Repairing them needs knowledge
# this migration does not establish, so they are recorded rather than fixed.
#
# lx.fileReader.mzAPI.mzURL and lx.fileReader.mzAPI.raw were discovered while
# implementing this test: `git log --all --full-history` shows neither file
# ever existed in this repository, and the shipped 1.5.0 PyInstaller build
# log (build/LipidXplorer/warn-LipidXplorer.txt at eada6a3) independently
# lists both as "missing module ... (delayed, conditional)", the same class
# of pre-existing gap as the two entries below. Unlike the doubled
# `lx.fileReader.lx.fileReader.mzAPI.mzWiff` path this task fixes, there is
# no typo to correct here -- the intended targets (an HTTP mzURL reader and a
# Thermo .raw reader) were never shipped, so making these two resolve would
# mean writing new file-format readers, not fixing an import path.
KNOWN_MISSING = {
    "lx.spectraImportC",         # lx/lxMain.py:40
    "lx.fileReader.lxml",        # lx/fileReader/mzAPI/mzML.py:35, an ImportError fallback
    "lx.fileReader.mzAPI.mzURL",  # lx/fileReader/mzAPI/__init__.py:357, http:// dispatch
    "lx.fileReader.mzAPI.raw",    # lx/fileReader/mzAPI/__init__.py:365, .raw dispatch
}


def _module_exists(dotted_name):
    relative = pathlib.Path(*dotted_name.split("."))
    return (
        (REPO_ROOT / relative).with_suffix(".py").is_file()
        or (REPO_ROOT / relative / "__init__.py").is_file()
    )


def _internal_imports():
    found = []
    for path in sorted((REPO_ROOT / "lx").rglob("*.py")):
        tree = ast.parse(
            path.read_text(encoding="utf-8", errors="replace"), filename=str(path)
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] == "lx":
                        found.append((str(path.relative_to(REPO_ROOT)), node.lineno, alias.name))
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module and node.module.split(".")[0] == "lx":
                    found.append((str(path.relative_to(REPO_ROOT)), node.lineno, node.module))
    return found


def test_internal_imports_collector_found_a_sensible_number():
    # A parametrized test over an empty list reports "skipped", not "failed",
    # and pytest exits 0 either way. If a refactor of _internal_imports()
    # ever made it return nothing, test_internal_import_target_exists below
    # would silently stop testing anything while still looking green. This
    # guard pins a floor well under today's real count so that regression
    # is caught as a failure instead.
    imports = _internal_imports()
    assert len(imports) > 20, (
        f"expected substantially more than 20 internal lx.* imports, found {len(imports)}"
    )


@pytest.mark.parametrize(
    "source_file,lineno,module",
    _internal_imports(),
    ids=lambda value: str(value),
)
def test_internal_import_target_exists(source_file, lineno, module):
    if any(module == known or module.startswith(known + ".") for known in KNOWN_MISSING):
        pytest.xfail(f"known pre-existing dead branch: {module} ({source_file}:{lineno})")
    assert _module_exists(module), f"{source_file}:{lineno} imports missing module {module}"
