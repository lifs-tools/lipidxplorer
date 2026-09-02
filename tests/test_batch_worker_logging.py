"""Worker processes must be able to report progress and failures.

Batch workers are started with the 'spawn' method, so they get a fresh
interpreter: they do not inherit the TeeLogger the GUI installs over
builtins.print, and in a windowed PyInstaller bundle their stdout and stderr
go nowhere. Everything a worker printed used to be discarded, which left the
GUI silent from "Using N worker process(es)" until the first sample finished
and made a crashed sample indistinguishable from one with no hits.

These tests exercise the sink directly; they need no spectra and no display.
"""

import builtins
import sys

import pytest

from lx.batch_processor import _WorkerLog, _install_worker_logging


@pytest.fixture
def restore_streams():
    """_install_worker_logging rebinds process-global state; put it back."""
    saved = (sys.stdout, sys.stderr, builtins.print)
    yield
    sys.stdout, sys.stderr, builtins.print = saved


def test_writes_whole_lines_to_the_log(tmp_path):
    log = tmp_path / "batch_log.txt"
    sink = _WorkerLog(str(log))

    sink.write("first line\n")
    sink.write("second line\n")

    lines = log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert lines[0].endswith("first line")
    assert lines[1].endswith("second line")


def test_buffers_fragments_until_a_newline_arrives(tmp_path):
    """print() and traceback both emit a line in several write() calls."""
    log = tmp_path / "batch_log.txt"
    sink = _WorkerLog(str(log))

    sink.write("[PID 1] ")
    sink.write("START sample=")
    assert not log.exists() or log.read_text(encoding="utf-8") == ""

    sink.write("'a'\n")
    assert log.read_text(encoding="utf-8").rstrip().endswith("[PID 1] START sample='a'")


def test_flush_emits_a_trailing_partial_line(tmp_path):
    log = tmp_path / "batch_log.txt"
    sink = _WorkerLog(str(log))

    sink.write("no trailing newline")
    sink.flush()

    assert log.read_text(encoding="utf-8").rstrip().endswith("no trailing newline")


def test_blank_lines_are_not_timestamped(tmp_path):
    log = tmp_path / "batch_log.txt"
    sink = _WorkerLog(str(log))

    sink.write("\n   \n\n")

    assert log.read_text(encoding="utf-8") == "" if log.exists() else True


def test_a_vanished_log_does_not_kill_the_worker(tmp_path):
    """A worker must finish its sample even if the log is gone."""
    sink = _WorkerLog(str(tmp_path / "missing-dir" / "batch_log.txt"))

    sink.write("this cannot be written anywhere\n")  # must not raise


def test_install_redirects_print_and_stderr(tmp_path, restore_streams):
    log = tmp_path / "batch_log.txt"

    sink = _install_worker_logging(str(log))
    assert sink is not None

    print("progress from the worker")
    print("to stderr", file=sys.stderr)
    sys.stderr.write("raw stderr write\n")

    body = log.read_text(encoding="utf-8")
    assert "progress from the worker" in body
    # print(file=...) is ignored on purpose: everything a worker emits belongs
    # in the one log the GUI is tailing.
    assert "to stderr" in body
    # traceback.print_exc() writes to sys.stderr, so it has to be captured too.
    assert "raw stderr write" in body


def test_install_is_a_no_op_without_a_log_file(restore_streams):
    """run_batch can be driven from a script with no log file configured."""
    before = builtins.print
    assert _install_worker_logging(None) is None
    assert builtins.print is before


def test_restore_print_puts_the_original_back(tmp_path, restore_streams):
    """A finished run must stop capturing everything the session prints."""
    from lx.logger import TeeLogger

    original = builtins.print
    logger = TeeLogger(file_path=str(tmp_path / "batch_log.txt"))

    logger.install_as_print()
    assert builtins.print is not original

    logger.restore_print()
    assert builtins.print is original
