import wx
from lx2_gui import Lx2_gui


class lx2_gui_controler(Lx2_gui):
    def __init__(self, parent):
        Lx2_gui.__init__(self, parent)

    def rep_rate_texted(self, event):
        num = int(self.rep_rate_txt.GetValue())
        self.rep_rate_slider.SetValue(num)

    def rep_rate_slider_scroll(self, event):
        num = self.rep_rate_slider.GetValue()
        self.rep_rate_txt.SetValue(str(num))


def main():
    app = wx.App()
    frame = lx2_gui_controler(None)
    frame.Show(True)
    # start the applications
    app.MainLoop()


if __name__ == "__main__":
    main()
