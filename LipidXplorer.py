import os
from pathlib import Path
from lx.gui import lpdxGUI
import wx
import sys

from lx.__version__ import __version__ as APP_VERSION
from lx.winOpenWith import register_open_with


def resource_path(*parts):
    # PyInstaller extracts to sys._MEIPASS # for pyinstaller: https://stackoverflow.com/questions/22472124/what-is-sys-meipass-in-python
    base = getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)
    return str(Path(base, *parts))


def mfql_paths_from_argv(args):
    """Return absolute paths of the .mfql arguments, in order, without duplicates.

    Windows passes the double-clicked file as "%1". Existence is not checked
    here: a missing file is reported by the frame in a dialog instead of
    being dropped silently. Other arguments are ignored.
    """
    paths = []
    for arg in args:
        if arg.lower().endswith(".mfql"):
            path = os.path.abspath(arg)
            if path not in paths:
                paths.append(path)
    return paths


class MyApp(wx.App):
    def __init__(self, *args, mfql_files=(), **kwargs):
        # Set before wx.App.__init__, which calls OnInit.
        self.mfql_files = list(mfql_files)
        super().__init__(*args, **kwargs)

    def OnInit(self):
        self.frame = lpdxGUI.LpdxFrame(
            None, -1, "",
            rawimport=False,
            lipidxplorer=True,
            version=APP_VERSION
        )

        icon_path = resource_path("lx", "stuff", "lipidx_ico2.ico")
        self.frame.SetIcon(wx.Icon(icon_path, wx.BITMAP_TYPE_ICO))

        self.frame.Show(True)
        self.frame.Center()
        self.SetTopWindow(self.frame)

        # Opened once the event loop runs, so the frame is fully laid out.
        for path in self.mfql_files:
            wx.CallAfter(self.frame.OpenMFQLFromPath, path)

        # Windows, packaged exe only: list LipidXplorer under
        # right-click > Open with for .mfql files (current user, no admin).
        wx.CallAfter(register_open_with)
        return True


def main():
    app = MyApp(0, mfql_files=mfql_paths_from_argv(sys.argv[1:]))
    app.MainLoop()
    wx.Exit()


if __name__ == "__main__":
    from multiprocessing import freeze_support

    freeze_support()  # <-- REQUIRED FOR PYINSTALLER WORKERS

    import multiprocessing

    # batch_processor assumes spawn (see lx/gui/lpdxGUI.py:3448). Linux would
    # otherwise default to fork and give batch mode different semantics.
    if multiprocessing.get_start_method(allow_none=True) is None:
        multiprocessing.set_start_method("spawn")

    # Answered before any wx.App exists, so CI can check a frozen bundle
    # starts on a runner with no display.
    if "--version" in sys.argv[1:]:
        print(f"LipidXplorer {APP_VERSION}")
        sys.exit(0)

    main()
