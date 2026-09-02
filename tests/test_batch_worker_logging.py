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
import pathlib
import subprocess
import sys
import textwrap

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
    """Stamping every fragment would fill the log with bare timestamps."""
    log = tmp_path / "batch_log.txt"
    sink = _WorkerLog(str(log))

    sink.write("\n   \n\n")

    # Nothing was worth writing, so the file is never even created.
    assert not log.exists()

    # ...and the blank input is not replayed once there is something to write.
    sink.write("a real line\n")
    assert log.read_text(encoding="utf-8").count("\n") == 1


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


def test_streams_capture_warnings(tmp_path):
    """warnings.warn bypasses print(), so stream capture has to catch it.

    A mis-detected CSV delimiter is reported this way during the merge.
    Without stream capture it goes to the null sink a windowed build gives a
    GUI process, and the merged table is silently parsed the wrong way.

    This runs in a subprocess on purpose: pytest swaps out
    warnings._showwarnmsg_impl for its own recorder, so a warning raised
    inside the test process never reaches sys.stderr and the capture could
    not be observed at all.
    """
    log = tmp_path / "batch_log.txt"
    script = textwrap.dedent(
        f"""
        import warnings
        from lx.logger import TeeLogger

        logger = TeeLogger(file_path={str(log)!r})
        logger.install_as_streams()
        warnings.warn("Could not detect delimiter. Falling back to comma.",
                      UserWarning)
        logger.restore_streams()
        """
    )

    subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(pathlib.Path(__file__).resolve().parents[1]),
        check=True,
    )

    assert "Could not detect delimiter" in log.read_text(encoding="utf-8")


def test_streams_capture_tracebacks(tmp_path, restore_streams):
    """traceback.print_exc() writes to sys.stderr, not through print()."""
    import traceback

    from lx.logger import TeeLogger

    log = tmp_path / "batch_log.txt"
    logger = TeeLogger(file_path=str(log))
    logger.install_as_streams()
    try:
        raise RuntimeError("merge blew up")
    except RuntimeError:
        traceback.print_exc()
    finally:
        logger.restore_streams()

    body = log.read_text(encoding="utf-8")
    assert "Traceback (most recent call last)" in body
    assert "RuntimeError: merge blew up" in body


def test_restore_streams_puts_the_originals_back(tmp_path, restore_streams):
    from lx.logger import TeeLogger

    before = (sys.stdout, sys.stderr)
    logger = TeeLogger(file_path=str(tmp_path / "batch_log.txt"))

    logger.install_as_streams()
    assert (sys.stdout, sys.stderr) != before

    logger.restore_streams()
    assert (sys.stdout, sys.stderr) == before


def test_multi_line_traceback_is_not_stamped_mid_line(tmp_path, restore_streams):
    """Each stamped line must be a whole line, not a stream fragment."""
    from lx.logger import TeeLogger

    log = tmp_path / "batch_log.txt"
    logger = TeeLogger(file_path=str(log))
    logger.install_as_streams()
    try:
        sys.stderr.write("Traceback (most recent call last):\n")
        sys.stderr.write('  File "x.py", ')      # fragment, no newline yet
        sys.stderr.write("line 1, in <module>\n")
    finally:
        logger.restore_streams()

    lines = log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert lines[1].endswith('File "x.py", line 1, in <module>')


def test_restore_streams_flushes_a_partial_line(tmp_path, restore_streams):
    from lx.logger import TeeLogger

    log = tmp_path / "batch_log.txt"
    logger = TeeLogger(file_path=str(log))
    logger.install_as_streams()
    sys.stdout.write("no trailing newline")
    logger.restore_streams()

    assert "no trailing newline" in log.read_text(encoding="utf-8")


def test_context_is_stamped_on_every_line(tmp_path):
    """Deep code (doImport, the MFQL interpreter) knows nothing about batches.

    It just calls print(), so the context has to be applied by the sink for
    those lines to be attributable at all.
    """
    log = tmp_path / "batch_log.txt"
    sink = _WorkerLog(str(log), context="[W3 sampleA]")

    sink.write("Building MasterScan\n")
    sink.write("some line from deep in readSpectra\n")

    lines = log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert all("[W3 sampleA]" in line for line in lines)
    assert lines[1].endswith("[W3 sampleA] some line from deep in readSpectra")


def test_context_is_optional(tmp_path):
    """Without a context the line keeps its plain timestamp, with no gap."""
    log = tmp_path / "batch_log.txt"
    sink = _WorkerLog(str(log))

    sink.write("no context here\n")

    line = log.read_text(encoding="utf-8").rstrip()
    assert line.endswith("] no context here")


def test_worker_context_shortens_the_pool_worker_name(monkeypatch):
    import multiprocessing as mp

    from lx import batch_processor

    class _Proc:
        name = "SpawnPoolWorker-7"

    monkeypatch.setattr(mp, "current_process", lambda: _Proc())
    assert batch_processor._worker_context("240506_QC_a") == "[W7 240506_QC_a]"


def test_worker_context_falls_back_to_the_raw_name(monkeypatch):
    """Outside a pool the process is 'MainProcess', which has no number."""
    import multiprocessing as mp

    from lx import batch_processor

    class _Proc:
        name = "MainProcess"

    monkeypatch.setattr(mp, "current_process", lambda: _Proc())
    assert batch_processor._worker_context("s1") == "[MainProcess s1]"


def test_teelogger_context_matches_the_worker_format(tmp_path):
    """The controller's lines are labelled the same way the workers' are."""
    from lx.logger import TeeLogger

    log = tmp_path / "batch_log.txt"
    logger = TeeLogger(file_path=str(log), context="[MAIN]")

    logger.log("Found 12 input sample(s)")

    line = log.read_text(encoding="utf-8").rstrip()
    assert line.endswith("[MAIN] Found 12 input sample(s)")


def test_teelogger_context_applies_to_captured_streams(tmp_path, restore_streams):
    """Warnings raised during the merge are labelled too, not just log() calls."""
    from lx.logger import TeeLogger

    log = tmp_path / "batch_log.txt"
    logger = TeeLogger(file_path=str(log), context="[MAIN]")
    logger.install_as_streams()
    try:
        sys.stderr.write("something from deep in the merge\n")
    finally:
        logger.restore_streams()

    assert log.read_text(encoding="utf-8").rstrip().endswith(
        "[MAIN] something from deep in the merge"
    )


def test_teelogger_without_context_is_unchanged(tmp_path):
    """Other callers of TeeLogger must not gain a stray separator."""
    from lx.logger import TeeLogger

    log = tmp_path / "plain.txt"
    TeeLogger(file_path=str(log)).log("no context")

    assert log.read_text(encoding="utf-8").rstrip().endswith("] no context")
