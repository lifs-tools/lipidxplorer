###########################################################################
## Class MyFrame1
###########################################################################
import wx


class MyFrame1(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(
            self,
            parent,
            id=wx.ID_ANY,
            title=wx.EmptyString,
            pos=wx.DefaultPosition,
            size=wx.Size(500, 300),
            style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL,
        )

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        bSizer1 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText1 = wx.StaticText(
            self,
            wx.ID_ANY,
            "enter number",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText1.Wrap(-1)

        bSizer1.Add(self.m_staticText1, 0, wx.ALL | wx.EXPAND, 5)

        self.m_textCtrl1 = wx.TextCtrl(
            self,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        bSizer1.Add(self.m_textCtrl1, 0, wx.ALL | wx.EXPAND, 5)

        self.m_button1 = wx.Button(
            self, wx.ID_ANY, "MyButton", wx.DefaultPosition, wx.DefaultSize, 0
        )
        bSizer1.Add(self.m_button1, 0, wx.ALL | wx.EXPAND, 5)

        self.m_textCtrl2 = wx.TextCtrl(
            self,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        bSizer1.Add(self.m_textCtrl2, 0, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(bSizer1)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.m_button1.Bind(wx.EVT_BUTTON, self.findSquare)

    def __del__(self):
        pass

    # Virtual event handlers, override them in your derived class
    def findSquare(self, event):
        num = int(self.m_textCtrl1.GetValue())
        self.m_textCtrl2.SetValue(str(num * num))


app = wx.App(False)
frame = MyFrame1(None)
frame.Show(True)
# start the applications
app.MainLoop()
