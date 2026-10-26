"""The "file is open, try again?" loop around MasterScan saving.

startMFQL() runs on the GUI's Worker thread, so the question must be shown
on the GUI thread, and the worker must wait for the answer.
"""

import threading

import wx

from lx.gui import saveRetry
from lx.gui.saveRetry import ask_yes_no, save_with_retry


class _Save:
    """A save() that fails with OSError the first `failures` times."""

    def __init__(self, failures):
        self.failures = failures
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self.calls <= self.failures:
            raise PermissionError("file is open in another program")


def _answers(*replies):
    replies = list(replies)
    asked = []

    def ask(parent, message, caption):
        asked.append(message)
        return replies.pop(0)

    return ask, asked


def test_saves_without_asking_when_the_file_is_writable():
    save, (ask, asked) = _Save(0), _answers()
    assert save_with_retry(save, object(), "MasterScan", ask=ask) is True
    assert save.calls == 1 and asked == []


def test_retries_while_the_user_says_yes():
    save, (ask, asked) = _Save(2), _answers(wx.ID_YES, wx.ID_YES)
    assert save_with_retry(save, object(), "MasterScan", ask=ask) is True
    assert save.calls == 3
    assert "MasterScan cannot be saved" in asked[0]


def test_gives_up_when_the_user_says_no():
    save, (ask, _) = _Save(5), _answers(wx.ID_NO)
    assert save_with_retry(save, object(), "MasterScan", ask=ask) is False
    assert save.calls == 1


def test_without_gui_reports_once_and_does_not_ask(capsys):
    save, (ask, asked) = _Save(5), _answers()
    assert save_with_retry(save, None, "MasterScan", ask=ask) is False
    assert asked == [] and save.calls == 1
    assert "could not save MasterScan" in capsys.readouterr().out


def test_question_from_a_worker_thread_is_shown_on_the_gui_thread(monkeypatch):
    """The dialog is created by the CallAfter target, never by the worker."""
    gui_thread_calls = []
    dialog_threads = []

    class FakeDialog:
        def __init__(self, *args, **kwargs):
            dialog_threads.append(threading.current_thread())

        def ShowModal(self):
            return wx.ID_YES

        def Destroy(self):
            pass

    def fake_call_after(fn):
        # stands in for the GUI thread processing the CallAfter event
        t = threading.Thread(target=fn, name="gui")
        gui_thread_calls.append(t)
        t.start()

    monkeypatch.setattr(saveRetry.wx, "IsMainThread", lambda: False)
    monkeypatch.setattr(saveRetry.wx, "CallAfter", fake_call_after)
    monkeypatch.setattr(saveRetry.wx, "MessageDialog", FakeDialog)

    assert ask_yes_no(None, "Try again?", "File writing error") == wx.ID_YES
    assert [t.name for t in dialog_threads] == ["gui"]
    assert threading.current_thread() not in dialog_threads
