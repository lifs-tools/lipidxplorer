import wx
import wx.xrc
import os
from LipidXplorer import MyApp


class LandingFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        self.frame = wx.Frame.__init__(self, None, id=wx.ID_ANY, title=wx.EmptyString, pos=wx.DefaultPosition,
                                       size=wx.Size(420, 100),
                                       style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        b_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.m_lx2_button = wx.Button(self, wx.ID_ANY, u"LX2", wx.DefaultPosition, wx.DefaultSize, 0)
        b_sizer.Add(self.m_lx2_button, 0, wx.ALL, 5)

        self.m_lx1_buttonn = wx.Button(self, wx.ID_ANY, u"LX1", wx.DefaultPosition, wx.DefaultSize, 0)
        b_sizer.Add(self.m_lx1_buttonn, 0, wx.ALL, 5)

        self.m_lx1_refactor = wx.Button(self, wx.ID_ANY, u"LX1 (Refactored)", wx.DefaultPosition, wx.DefaultSize, 0)
        b_sizer.Add(self.m_lx1_refactor, 0, wx.ALL, 5)

        self.m_lx_tools = wx.Button(self, wx.ID_ANY, u"Tools", wx.DefaultPosition, wx.DefaultSize, 0)
        b_sizer.Add(self.m_lx_tools, 0, wx.ALL, 5)

        self.SetSizer(b_sizer)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.m_lx2_button.Bind(wx.EVT_BUTTON, self.m_lx2_buttonOnButtonClick)

    def m_lx2_buttonOnButtonClick(self, event):
        app = MyApp(self.frame)
        os.chdir(os.getcwd())
        app.MainLoop()
        app.Destroy()
        wx.Exit()

    def __del__(self):
        pass
