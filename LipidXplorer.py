import os
from pathlib import Path
from lx.gui import lpdxGUI
import wx
import sys

from lx.__version__ import __version__ as APP_VERSION


def resource_path(*parts):
    # PyInstaller extracts to sys._MEIPASS # for pyinstaller: https://stackoverflow.com/questions/22472124/what-is-sys-meipass-in-python
    base = getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)
    return str(Path(base, *parts))


class MyApp(wx.App):
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
        return True


def main():
    app = MyApp(0)
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
