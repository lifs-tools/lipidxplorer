# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version Oct 26 2018)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class SimStitcherFrame
###########################################################################


class SimStitcherFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(
            self,
            parent,
            id=wx.ID_ANY,
            title=wx.EmptyString,
            pos=wx.DefaultPosition,
            size=wx.Size(600, 480),
            style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL,
        )

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetBackgroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_MENU)
        )

        bSizer2 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText1 = wx.StaticText(
            self,
            wx.ID_ANY,
            "Sim Stitcher",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText1.Wrap(-1)

        self.m_staticText1.SetFont(
            wx.Font(
                14,
                wx.FONTFAMILY_SWISS,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                False,
                "Arial",
            )
        )

        bSizer2.Add(self.m_staticText1, 0, wx.ALL, 5)

        self.m_staticline1 = wx.StaticLine(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.LI_HORIZONTAL,
        )
        bSizer2.Add(self.m_staticline1, 0, wx.EXPAND | wx.ALL, 5)

        self.m_staticText2 = wx.StaticText(
            self,
            wx.ID_ANY,
            "Select mzML/mzXML file to Sim Stitch:",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText2.Wrap(-1)

        bSizer2.Add(self.m_staticText2, 0, wx.ALL, 5)

        bSizer3 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_textCtrl1 = wx.TextCtrl(
            self,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        bSizer3.Add(self.m_textCtrl1, 1, wx.ALL, 5)

        self.BrowseBtn = wx.Button(
            self, wx.ID_ANY, "Browse", wx.DefaultPosition, wx.DefaultSize, 0
        )
        bSizer3.Add(self.BrowseBtn, 0, wx.ALL, 5)

        self.m_button2 = wx.Button(
            self, wx.ID_ANY, "Start", wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.m_button2.Enable(False)

        bSizer3.Add(self.m_button2, 0, wx.ALL, 5)

        bSizer2.Add(bSizer3, 1, wx.EXPAND, 5)

        bSizer61 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_checkBox11 = wx.CheckBox(
            self,
            wx.ID_ANY,
            "Cut SIM edges",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_checkBox11.SetValue(True)
        self.m_checkBox11.SetToolTip(
            "Remove peaks that overlap AND peaks close to the edge"
        )

        bSizer61.Add(self.m_checkBox11, 0, wx.ALL | wx.ALIGN_BOTTOM, 5)

        self.m_textCtrl4 = wx.TextCtrl(
            self, wx.ID_ANY, "5.0", wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.m_textCtrl4.Enable(False)
        self.m_textCtrl4.SetToolTip("Daltons to from the edge")

        bSizer61.Add(self.m_textCtrl4, 0, wx.ALL | wx.ALIGN_BOTTOM, 5)

        self.m_staticText8 = wx.StaticText(
            self, wx.ID_ANY, "Da.", wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.m_staticText8.Wrap(-1)

        bSizer61.Add(self.m_staticText8, 0, wx.ALL | wx.ALIGN_BOTTOM, 5)

        bSizer61.Add((0, 0), 1, wx.EXPAND, 5)

        self.m_radioBtn31 = wx.RadioButton(
            self, wx.ID_ANY, "Default", wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.m_radioBtn31.SetValue(True)
        bSizer61.Add(self.m_radioBtn31, 0, wx.ALL | wx.ALIGN_BOTTOM, 5)

        self.m_radioBtn41 = wx.RadioButton(
            self, wx.ID_ANY, "Custom", wx.DefaultPosition, wx.DefaultSize, 0
        )
        bSizer61.Add(self.m_radioBtn41, 0, wx.ALL | wx.ALIGN_BOTTOM, 5)

        bSizer2.Add(bSizer61, 1, wx.EXPAND, 5)

        bSizer6 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_checkBox1 = wx.CheckBox(
            self,
            wx.ID_ANY,
            "Scale SIM to FT center mass",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_checkBox1.SetToolTip(
            "Scale the intensity such that the center SIM mass is the same as the corresponding FT mass"
        )

        bSizer6.Add(self.m_checkBox1, 0, wx.ALL | wx.ALIGN_BOTTOM, 5)

        bSizer6.Add((0, 0), 1, wx.EXPAND, 5)

        bSizer2.Add(bSizer6, 1, wx.EXPAND, 5)

        bSizer62 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_checkBox12 = wx.CheckBox(
            self,
            wx.ID_ANY,
            "Adapt SIM to matching FT peaks",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_checkBox12.SetToolTip(
            "Change the intensity of the SIM peaks based on trend of matchin FT peaks"
        )

        bSizer62.Add(self.m_checkBox12, 0, wx.ALL | wx.ALIGN_BOTTOM, 5)

        bSizer62.Add((0, 0), 1, wx.EXPAND, 5)

        bSizer2.Add(bSizer62, 1, wx.EXPAND, 5)

        bSizer5 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_staticText51 = wx.StaticText(
            self, wx.ID_ANY, "Log Level", wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.m_staticText51.Wrap(-1)

        bSizer5.Add(self.m_staticText51, 0, wx.ALL | wx.ALIGN_BOTTOM, 5)

        self.m_staticText6 = wx.StaticText(
            self, wx.ID_ANY, "low", wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.m_staticText6.Wrap(-1)

        bSizer5.Add(
            self.m_staticText6,
            0,
            wx.TOP | wx.BOTTOM | wx.LEFT | wx.ALIGN_BOTTOM,
            5,
        )

        self.m_slider1 = wx.Slider(
            self,
            wx.ID_ANY,
            0,
            0,
            3,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.SL_HORIZONTAL,
        )
        bSizer5.Add(self.m_slider1, 0, wx.ALL | wx.ALIGN_BOTTOM, 5)

        self.m_staticText7 = wx.StaticText(
            self, wx.ID_ANY, "high", wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.m_staticText7.Wrap(-1)

        bSizer5.Add(
            self.m_staticText7,
            0,
            wx.TOP | wx.BOTTOM | wx.RIGHT | wx.ALIGN_BOTTOM,
            5,
        )

        bSizer2.Add(bSizer5, 1, wx.EXPAND, 5)

        self.m_gauge1 = wx.Gauge(
            self,
            wx.ID_ANY,
            100,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.GA_HORIZONTAL,
        )
        self.m_gauge1.SetValue(0)
        bSizer2.Add(self.m_gauge1, 0, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(bSizer2)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.BrowseBtn.Bind(wx.EVT_BUTTON, self.browseClicked)
        self.m_button2.Bind(wx.EVT_BUTTON, self.clickStart)
        self.m_checkBox11.Bind(wx.EVT_CHECKBOX, self.checkCut)
        self.m_radioBtn31.Bind(wx.EVT_RADIOBUTTON, self.radioDefault)
        self.m_radioBtn41.Bind(wx.EVT_RADIOBUTTON, self.RadioCustom)
        self.m_checkBox1.Bind(wx.EVT_CHECKBOX, self.checkScale)
        self.m_checkBox12.Bind(wx.EVT_CHECKBOX, self.checkAdapt)

    def __del__(self):
        pass

    # Virtual event handlers, overide them in your derived class
    def browseClicked(self, event):
        event.Skip()

    def clickStart(self, event):
        event.Skip()

    def checkCut(self, event):
        event.Skip()

    def radioDefault(self, event):
        event.Skip()

    def RadioCustom(self, event):
        event.Skip()

    def checkScale(self, event):
        event.Skip()

    def checkAdapt(self, event):
        event.Skip()
