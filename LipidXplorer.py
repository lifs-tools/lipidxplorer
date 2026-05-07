import os
from pathlib import Path
from lx.gui import lpdxGUI
import wx
import sys

APP_VERSION = "1.5"


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
    main()
