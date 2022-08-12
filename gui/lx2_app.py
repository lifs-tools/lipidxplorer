import wx
from lx2_gui import Lx2_gui


class lx2_gui_controler(Lx2_gui):
    def __init__(self, parent):
        Lx2_gui.__init__(self, parent)

    ################ bind controls
    def rep_rate_exited(self, event):
        try:
            num = int(self.rep_rate_txt.GetValue())
        except ValueError:
            wx.MessageBox(
                "Invalid repetition rate! \n must be between 0 - 100\n will reset to 70",
                "error",
                wx.OK | wx.ICON_ERROR,
            )
            num = 70

        if not 0 <= num <= 100:
            wx.MessageBox(
                "Invalid repetition rate! \n must be between 0 - 100\n will reset to 70",
                "error",
                wx.OK | wx.ICON_ERROR,
            )
            num = 70

        self.rep_rate_slider.SetValue(num)

    def rep_rate_txextenter(self, event):
        self.rep_rate_exited(event)  # delegate

    def rep_rate_slider_scroll(self, event):
        num = self.rep_rate_slider.GetValue()
        self.rep_rate_txt.SetValue(str(num))

    def found_in_exited(self, event):
        try:
            num = int(self.found_int_txt.GetValue())
        except ValueError:
            wx.MessageBox(
                "Invalid percentage rate! \n must be between 0 - 100\n will reset to 0",
                "error",
                wx.OK | wx.ICON_ERROR,
            )
            num = 0

        if not 0 <= num <= 100:
            wx.MessageBox(
                "Invalid percentage rate! \n must be between 0 - 100\n will reset to 0",
                "error",
                wx.OK | wx.ICON_ERROR,
            )
            num = 0

        self.found_in_slider.SetValue(num)

    def found_in_entered(self, event):
        self.found_in_exited(event)

    def found_in_slider_scrolled(self, event):
        num = self.found_in_slider.GetValue()
        self.found_int_txt.SetValue(str(num))


def main():
    app = wx.App()
    frame = lx2_gui_controler(None)
    frame.Show(True)
    # start the applications
    app.MainLoop()


if __name__ == "__main__":
    main()
