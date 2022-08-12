import wx
from lx2_gui import Lx2_gui


class lx2_gui_controler(Lx2_gui):
    def __init__(self, parent):
        Lx2_gui.__init__(self, parent)

    def gen_masterscan_clicked(self, event):
        num = int(self.ms1_tolerance_txt.GetValue())
        self.ms2_tol_text.SetValue(str(num))


def main():
    app = wx.App()
    frame = lx2_gui_controler(None)
    frame.Show(True)
    # start the applications
    app.MainLoop()


if __name__ == "__main__":
    main()
