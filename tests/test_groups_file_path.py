"""The groups.txt lookup must work on every platform.

The path was built as "%s\\\\groups.txt", so on Linux and macOS it never
matched. Occupation-threshold grouping silently did nothing there - no
error was raised and results were quietly different.
"""

import os

from lx.spectraImport import groups_file_path


def test_joins_with_the_platform_separator():
    assert groups_file_path(os.path.join("some", "import", "dir")) == os.path.join(
        "some", "import", "dir", "groups.txt"
    )


def test_finds_a_real_file(tmp_path):
    (tmp_path / "groups.txt").write_text("0.5, sample1, sample2\n", encoding="utf-8")
    assert os.path.exists(groups_file_path(str(tmp_path)))


def test_does_not_hardcode_a_backslash():
    assert "\\" not in groups_file_path("/tmp/import")
