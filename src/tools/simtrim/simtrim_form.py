# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.10.1-0-g8feb16b3)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class simtrim_Frame
###########################################################################


class simtrim_Frame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(
            self,
            parent,
            id=wx.ID_ANY,
            title="Simtrim",
            pos=wx.DefaultPosition,
            size=wx.Size(500, 239),
            style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL,
        )

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
        )
        self.SetBackgroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
        )

        bSizer15 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText26 = wx.StaticText(
            self,
            wx.ID_ANY,
            "trim the sims from a spectra\n",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText26.Wrap(-1)

        self.m_staticText26.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
        )

        bSizer15.Add(self.m_staticText26, 0, wx.ALL, 5)

        fgSizer5 = wx.FlexGridSizer(4, 2, 0, 0)
        fgSizer5.SetFlexibleDirection(wx.BOTH)
        fgSizer5.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        self.m_staticText18 = wx.StaticText(
            self,
            wx.ID_ANY,
            "Spectra File with sims",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText18.Wrap(-1)

        self.m_staticText18.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
        )

        fgSizer5.Add(self.m_staticText18, 0, wx.ALL, 5)

        bSizer35 = wx.BoxSizer(wx.VERTICAL)

        self.m_filePicker10 = wx.FilePickerCtrl(
            self,
            wx.ID_ANY,
            wx.EmptyString,
            "Select a files",
            "*.*",
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.FLP_DEFAULT_STYLE | wx.FLP_FILE_MUST_EXIST | wx.FLP_OPEN,
        )
        bSizer35.Add(self.m_filePicker10, 1, wx.ALL | wx.EXPAND, 5)

        fgSizer5.Add(bSizer35, 1, wx.EXPAND, 5)

        self.m_staticText20 = wx.StaticText(
            self,
            wx.ID_ANY,
            "custom dalton size to trim",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText20.Wrap(-1)

        self.m_staticText20.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
        )

        fgSizer5.Add(self.m_staticText20, 0, wx.ALL, 5)

        bSizer36 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_textCtrl3 = wx.TextCtrl(
            self, wx.ID_ANY, "0", wx.DefaultPosition, wx.DefaultSize, 0
        )
        bSizer36.Add(self.m_textCtrl3, 0, wx.ALL, 5)

        self.m_staticText30 = wx.StaticText(
            self,
            wx.ID_ANY,
            "0 for automatic",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText30.Wrap(-1)

        self.m_staticText30.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
        )

        bSizer36.Add(self.m_staticText30, 0, wx.ALL, 5)

        fgSizer5.Add(bSizer36, 1, wx.EXPAND, 5)

        self.m_staticText22 = wx.StaticText(
            self,
            wx.ID_ANY,
            "Retention Time",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText22.Wrap(-1)

        self.m_staticText22.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
        )

        fgSizer5.Add(self.m_staticText22, 0, wx.ALL, 5)

        bSizer37 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_staticText23 = wx.StaticText(
            self, wx.ID_ANY, "Start", wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.m_staticText23.Wrap(-1)

        self.m_staticText23.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
        )

        bSizer37.Add(self.m_staticText23, 0, wx.ALL, 5)

        self.m_textCtrl4 = wx.TextCtrl(
            self,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        bSizer37.Add(self.m_textCtrl4, 0, wx.ALL, 5)

        self.m_staticText231 = wx.StaticText(
            self, wx.ID_ANY, "end", wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.m_staticText231.Wrap(-1)

        self.m_staticText231.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
        )

        bSizer37.Add(self.m_staticText231, 0, wx.ALL, 5)

        self.m_textCtrl41 = wx.TextCtrl(
            self,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        bSizer37.Add(self.m_textCtrl41, 0, wx.ALL, 5)

        fgSizer5.Add(bSizer37, 1, wx.EXPAND, 5)

        bSizer15.Add(fgSizer5, 1, wx.EXPAND, 5)

        bSizer40 = wx.BoxSizer(wx.VERTICAL)

        self.run = wx.Button(
            self, wx.ID_ANY, "run", wx.DefaultPosition, wx.Size(-1, -1), 0
        )
        bSizer40.Add(self.run, 0, wx.ALL | wx.ALIGN_RIGHT, 5)

        bSizer15.Add(bSizer40, 1, wx.EXPAND, 5)

        self.SetSizer(bSizer15)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.run.Bind(wx.EVT_BUTTON, self.run_clicked)

    def __del__(self):
        pass

    # Virtual event handlers, override them in your derived class
    def run_clicked(self, event):
        event.Skip()
