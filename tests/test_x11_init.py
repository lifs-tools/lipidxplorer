"""X11 thread initialisation must never prevent lx.tools from importing.

wxWidgets needs XInitThreads() before any GUI thread starts, so the call
belongs at import time. But a frozen bundle runs on machines that have no
X11 development package, and previously an OSError there took the whole
application down before it drew a window.

lx.tools imports only the standard library at module level, so these tests
are cheap and need no display.
"""

import sys

import pytest

import lx.tools


def test_returns_false_off_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    assert lx.tools._init_x11_threads() is False


def test_returns_false_when_no_x11_library_can_be_loaded(monkeypatch):
    import ctypes

    monkeypatch.setattr(sys, "platform", "linux")

    attempted = []

    def refuse(name, *args, **kwargs):
        attempted.append(name)
        raise OSError(f"{name}: cannot open shared object file")

    monkeypatch.setattr(ctypes, "CDLL", refuse)

    assert lx.tools._init_x11_threads() is False
    assert attempted == ["libX11.so.6", "libX11.so"]


def test_prefers_the_versioned_soname(monkeypatch):
    import ctypes

    monkeypatch.setattr(sys, "platform", "linux")

    attempted = []

    class FakeLibrary:
        def XInitThreads(self):
            return 1

    def load(name, *args, **kwargs):
        attempted.append(name)
        return FakeLibrary()

    monkeypatch.setattr(ctypes, "CDLL", load)

    assert lx.tools._init_x11_threads() is True
    assert attempted == ["libX11.so.6"]
