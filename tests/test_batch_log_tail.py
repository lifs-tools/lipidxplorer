"""The debug window is fed by tailing the batch log, on the main thread.

Batch output originates in two places that must not touch wx: the background
batch thread, and the spawned worker processes. Both append to the log file
instead, and a wx.Timer on the main thread pumps what is new into the text
control -- so this incremental read is the only path into the GUI while a
batch runs.

Imports wx via lx.gui.lpdxGUI; like test_gui_module_constants, it needs a
display (CI runs it under xvfb-run).
"""

import lx.gui.lpdxGUI as lpdxGUI


class _StubCtrl:
    def __init__(self):
        self.text = ""

    def AppendText(self, chunk):
        self.text += chunk

    def GetLength(self):
        return len(self.text)

    def GotoPos(self, pos):
        pass


class _StubDebug:
    def __init__(self):
        self.text_ctrl = _StubCtrl()


class _Tailer:
    """Just the tail machinery, without building a real LpdxFrame."""

    _on_batch_log_tick = lpdxGUI.LpdxFrame._on_batch_log_tick

    def __init__(self, path, pos=0):
        self._batch_log_path = str(path)
        self._batch_log_pos = pos
        self.debug = _StubDebug()
        self._batch_log_timer = None


def test_appends_only_what_is_new(tmp_path):
    log = tmp_path / "batch_log.txt"
    log.write_text("first\n", encoding="utf-8")
    tailer = _Tailer(log)

    tailer._on_batch_log_tick()
    assert tailer.debug.text_ctrl.text == "first\n"

    # A worker appends while the timer is running.
    with open(log, "a", encoding="utf-8") as handle:
        handle.write("second\n")

    tailer._on_batch_log_tick()
    assert tailer.debug.text_ctrl.text == "first\nsecond\n"

    # Nothing new: the control must not grow.
    tailer._on_batch_log_tick()
    assert tailer.debug.text_ctrl.text == "first\nsecond\n"


def test_starts_from_the_recorded_offset(tmp_path):
    """A second run must not replay the first: TeeLogger appends."""
    log = tmp_path / "batch_log.txt"
    previous = "run one line\n"
    log.write_text(previous, encoding="utf-8")

    tailer = _Tailer(log, pos=len(previous.encode("utf-8")))
    with open(log, "a", encoding="utf-8") as handle:
        handle.write("run two line\n")

    tailer._on_batch_log_tick()
    assert tailer.debug.text_ctrl.text == "run two line\n"


def test_missing_log_is_tolerated(tmp_path):
    """The first tick can land before anything has created the file."""
    tailer = _Tailer(tmp_path / "not-created-yet.txt")

    tailer._on_batch_log_tick()  # must not raise

    assert tailer.debug.text_ctrl.text == ""


def test_undecodable_bytes_do_not_break_the_window(tmp_path):
    log = tmp_path / "batch_log.txt"
    log.write_bytes(b"before \xff\xfe after\n")
    tailer = _Tailer(log)

    tailer._on_batch_log_tick()

    assert "before" in tailer.debug.text_ctrl.text
    assert "after" in tailer.debug.text_ctrl.text
