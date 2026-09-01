"""`LipidXplorer.py --version` is the only headless check the app offers.

It must print the version and exit before any wx.App is constructed, so CI
can verify a frozen bundle actually starts on a runner with no display.
"""

import pathlib
import subprocess
import sys

from lx.__version__ import __version__

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _run_version_flag():
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "LipidXplorer.py"), "--version"],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(REPO_ROOT),
    )


def test_prints_the_version_and_exits_zero():
    result = _run_version_flag()
    assert result.returncode == 0, result.stderr
    assert __version__ in result.stdout


def test_matches_the_single_source_of_truth():
    assert _run_version_flag().stdout.strip().endswith(__version__)
