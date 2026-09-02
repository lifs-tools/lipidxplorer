"""The merge step must not mis-read its own per-sample CSVs.

merge_lipid_results sniffs each per-sample CSV for its delimiter from a
fixed 4096-byte read. Result rows here run to several hundred characters, so
that read almost always stops mid-line, and the short line it leaves behind
has a different field count from the rest -- exactly what csv.Sniffer's
consistency check rejects. Detection failed for all twelve files of a real
benchmark run, and the silent fallback to comma was only correct by luck.
"""

import csv
import warnings

import pytest

from lx.batch_processor import merge_lipid_results


def _sniff_like_merge(text):
    """The delimiter detection as merge_lipid_results performs it."""
    lines = text.splitlines(keepends=True)
    if len(lines) > 1 and not lines[-1].endswith("\n"):
        text = "".join(lines[:-1])
    return csv.Sniffer().sniff(text, delimiters=",;\t|").delimiter


def _wide_csv(delimiter=","):
    """A file shaped like a real result: long header, long rows."""
    header = delimiter.join(f"Column{i}" for i in range(40))
    row = delimiter.join(f"value{i}" for i in range(40))
    return header + "\n" + "".join(row + "\n" for _ in range(12))


def _truncated_window(body):
    """A fixed-size read that stops in the middle of a line, as the real one does."""
    lines = body.splitlines(keepends=True)
    return "".join(lines[:6]) + lines[6][: len(lines[6]) // 2]


@pytest.mark.parametrize("delimiter", [",", ";", "\t", "|"])
def test_detects_delimiter_despite_a_truncated_read(delimiter):
    window = _truncated_window(_wide_csv(delimiter))
    assert not window.endswith("\n"), "test needs a genuinely truncated window"

    assert _sniff_like_merge(window) == delimiter


def test_a_truncated_line_is_what_used_to_break_it():
    """Guards the reason for the fix, not just the fix."""
    window = _truncated_window(_wide_csv(","))

    with pytest.raises(csv.Error):
        csv.Sniffer().sniff(window, delimiters=",;\t|")

    assert _sniff_like_merge(window) == ","


def test_a_complete_short_file_keeps_its_last_line():
    """Dropping the tail unconditionally would discard real data."""
    assert _sniff_like_merge("a,b,c\n1,2,3\n") == ","


def test_merge_reads_a_real_per_sample_csv(tmp_path):
    """End to end: a wide comma file merges without a delimiter warning."""
    path = tmp_path / "sample_a.csv"
    header = "LipidSpecies,LipidClass,Mass,ScanPolarity,Intensity"
    rows = "\n".join(
        f"PC 34:{i},PC,{760.0 + i},negative,{1000 * i}" for i in range(1, 25)
    )
    path.write_text(header + "\n" + rows + "\n", encoding="utf-8")

    with warnings.catch_warnings():
        warnings.simplefilter("error")  # a delimiter warning would fail here
        df, polarity = merge_lipid_results([str(path)])

    assert polarity == ["negative"]
    assert "LipidSpecies" in df.columns
    # merge_lipid_results appends one blank separator row per lipid class.
    assert int(df["LipidSpecies"].notna().sum()) == 24
