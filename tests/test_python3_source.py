"""Every Python file in the repository must parse under Python 3.

The 2to3 migration left two files behind that Python 3 cannot parse. This
test is what makes "the codebase is Python 3" a checkable statement rather
than an approximate one.

Parsing is deliberate: it needs no third-party packages and no imports, so
it covers files that are unreachable at runtime and would otherwise rot
unnoticed.
"""

import ast
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".venv", "build", "dist", "__pycache__"}


def _source_files():
    return sorted(
        path
        for path in REPO_ROOT.rglob("*.py")
        if not SKIP_DIRS & set(path.relative_to(REPO_ROOT).parts)
    )


@pytest.mark.parametrize(
    "path",
    _source_files(),
    ids=lambda path: str(path.relative_to(REPO_ROOT)),
)
def test_source_file_parses_under_python3(path):
    ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
