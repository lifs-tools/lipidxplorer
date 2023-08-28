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
## Class MyFrame2
###########################################################################


class MyFrame2(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(
            self,
            parent,
            id=wx.ID_ANY,
            title=wx.EmptyString,
            pos=wx.DefaultPosition,
            size=wx.Size(750, 600),
            style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL,
        )

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetBackgroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_MENU)
        )

        bSizer3 = wx.BoxSizer(wx.VERTICAL)

        self.m_panel1 = wx.Panel(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.TAB_TRAVERSAL,
        )
        bSizer2 = wx.BoxSizer(wx.VERTICAL)

        bSizer30 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText1 = wx.StaticText(
            self.m_panel1,
            wx.ID_ANY,
            "PeakStrainer Development",
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

        bSizer30.Add(self.m_staticText1, 0, wx.TOP | wx.RIGHT | wx.LEFT, 5)

        self.m_staticText27 = wx.StaticText(
            self.m_panel1,
            wx.ID_ANY,
            "Shotgun MS repetition rate filter",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText27.Wrap(-1)

        bSizer30.Add(self.m_staticText27, 0, wx.BOTTOM | wx.RIGHT | wx.LEFT, 5)

        bSizer2.Add(bSizer30, 1, wx.EXPAND, 5)

        self.m_staticline1 = wx.StaticLine(
            self.m_panel1,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.LI_HORIZONTAL,
        )
        bSizer2.Add(self.m_staticline1, 0, wx.EXPAND | wx.ALL, 5)

        self.m_panel1.SetSizer(bSizer2)
        self.m_panel1.Layout()
        bSizer2.Fit(self.m_panel1)
        bSizer3.Add(self.m_panel1, 1, wx.EXPAND, 5)

        self.m_notebook1 = wx.Notebook(
            self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.m_panel3 = wx.Panel(
            self.m_notebook1,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.TAB_TRAVERSAL,
        )
        self.m_panel3.Hide()

        bSizer5 = wx.BoxSizer(wx.VERTICAL)

        bSizer6 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_staticText3 = wx.StaticText(
            self.m_panel3,
            wx.ID_ANY,
            "Select Files:",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText3.Wrap(-1)

        bSizer6.Add(
            self.m_staticText3, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_textCtrl1 = wx.TextCtrl(
            self.m_panel3,
            wx.ID_ANY,
            "No files Selected...",
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.TE_READONLY,
        )
        self.m_textCtrl1.SetBackgroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
        )

        bSizer6.Add(self.m_textCtrl1, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.m_buttonBrowse = wx.Button(
            self.m_panel3,
            wx.ID_ANY,
            "Browse",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        bSizer6.Add(
            self.m_buttonBrowse, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        bSizer5.Add(bSizer6, 0, wx.EXPAND, 5)

        bSizer7 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_checkBox2 = wx.CheckBox(
            self.m_panel3,
            wx.ID_ANY,
            "Open with",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_checkBox2.SetValue(True)
        bSizer7.Add(
            self.m_checkBox2,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM | wx.LEFT,
            5,
        )

        self.m_button3 = wx.Button(
            self.m_panel3,
            wx.ID_ANY,
            "Spectra Reorder",
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.BORDER_NONE,
        )
        bSizer7.Add(self.m_button3, 0, wx.TOP | wx.BOTTOM | wx.RIGHT, 5)

        self.m_button4 = wx.Button(
            self.m_panel3,
            wx.ID_ANY,
            "simStitcher",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        bSizer7.Add(self.m_button4, 0, wx.ALL, 5)

        bSizer5.Add(bSizer7, 0, 0, 5)

        self.m_panel3.SetSizer(bSizer5)
        self.m_panel3.Layout()
        bSizer5.Fit(self.m_panel3)
        self.m_notebook1.AddPage(self.m_panel3, "General", True)
        self.m_panel4 = wx.Panel(
            self.m_notebook1,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.TAB_TRAVERSAL,
        )
        bSizer9 = wx.BoxSizer(wx.VERTICAL)

        bSizer10 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_checkBox8 = wx.CheckBox(
            self.m_panel4,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        bSizer10.Add(self.m_checkBox8, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.m_staticTexttocsv = wx.StaticText(
            self.m_panel4,
            wx.ID_ANY,
            "CSV output directory:",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticTexttocsv.Wrap(-1)

        bSizer10.Add(
            self.m_staticTexttocsv, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_dirPicker1 = wx.DirPickerCtrl(
            self.m_panel4,
            wx.ID_ANY,
            wx.EmptyString,
            "Select a folder",
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.DIRP_DEFAULT_STYLE,
        )
        self.m_dirPicker1.Enable(False)

        bSizer10.Add(self.m_dirPicker1, 1, wx.ALL, 5)

        bSizer9.Add(bSizer10, 0, wx.EXPAND, 5)

        self.m_staticline5 = wx.StaticLine(
            self.m_panel4,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.LI_HORIZONTAL,
        )
        bSizer9.Add(self.m_staticline5, 0, wx.EXPAND | wx.ALL, 5)

        bSizer11 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_checkBox9 = wx.CheckBox(
            self.m_panel4,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        bSizer11.Add(self.m_checkBox9, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.m_staticText4 = wx.StaticText(
            self.m_panel4,
            wx.ID_ANY,
            "Set log Level:",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText4.Wrap(-1)

        bSizer11.Add(
            self.m_staticText4, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_staticText16 = wx.StaticText(
            self.m_panel4,
            wx.ID_ANY,
            "low",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText16.Wrap(-1)

        bSizer11.Add(
            self.m_staticText16, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_slider1 = wx.Slider(
            self.m_panel4,
            wx.ID_ANY,
            1,
            1,
            5,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.SL_AUTOTICKS | wx.SL_HORIZONTAL,
        )
        self.m_slider1.Enable(False)

        bSizer11.Add(self.m_slider1, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.m_staticText17 = wx.StaticText(
            self.m_panel4,
            wx.ID_ANY,
            "high",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText17.Wrap(-1)

        bSizer11.Add(
            self.m_staticText17, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        bSizer9.Add(bSizer11, 0, wx.EXPAND, 5)

        self.m_staticline6 = wx.StaticLine(
            self.m_panel4,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.LI_HORIZONTAL,
        )
        bSizer9.Add(self.m_staticline6, 0, wx.EXPAND | wx.ALL, 5)

        bSizer12 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_checkBox10 = wx.CheckBox(
            self.m_panel4,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        bSizer12.Add(
            self.m_checkBox10, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_staticText5 = wx.StaticText(
            self.m_panel4,
            wx.ID_ANY,
            "Use Config file:",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText5.Wrap(-1)

        bSizer12.Add(
            self.m_staticText5, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_filePicker2 = wx.FilePickerCtrl(
            self.m_panel4,
            wx.ID_ANY,
            wx.EmptyString,
            "Select a config.ini",
            "*.ini",
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.FLP_DEFAULT_STYLE,
        )
        self.m_filePicker2.Enable(False)

        bSizer12.Add(self.m_filePicker2, 1, wx.ALL, 5)

        bSizer9.Add(bSizer12, 0, wx.EXPAND, 5)

        self.m_panel4.SetSizer(bSizer9)
        self.m_panel4.Layout()
        bSizer9.Fit(self.m_panel4)
        self.m_notebook1.AddPage(self.m_panel4, "Output", False)
        self.m_panel5 = wx.Panel(
            self.m_notebook1,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.TAB_TRAVERSAL,
        )
        bSizer19 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText7 = wx.StaticText(
            self.m_panel5,
            wx.ID_ANY,
            "Select Scans",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText7.Wrap(-1)

        self.m_staticText7.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_SWISS,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                False,
                "Arial",
            )
        )

        bSizer19.Add(self.m_staticText7, 0, wx.ALL, 5)

        self.m_staticline9 = wx.StaticLine(
            self.m_panel5,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.LI_HORIZONTAL,
        )
        bSizer19.Add(self.m_staticline9, 0, wx.EXPAND | wx.ALL, 5)

        bSizer21 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_checkBox5 = wx.CheckBox(
            self.m_panel5,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        bSizer21.Add(self.m_checkBox5, 0, wx.ALL, 5)

        self.m_staticText8 = wx.StaticText(
            self.m_panel5,
            wx.ID_ANY,
            "By Retention Time, from: ",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText8.Wrap(-1)

        bSizer21.Add(
            self.m_staticText8, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_textCtrl2 = wx.TextCtrl(
            self.m_panel5,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_textCtrl2.Enable(False)

        bSizer21.Add(self.m_textCtrl2, 0, wx.ALL, 5)

        self.m_staticText9 = wx.StaticText(
            self.m_panel5,
            wx.ID_ANY,
            "to",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText9.Wrap(-1)

        bSizer21.Add(
            self.m_staticText9, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_textCtrl3 = wx.TextCtrl(
            self.m_panel5,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_textCtrl3.Enable(False)

        bSizer21.Add(self.m_textCtrl3, 0, wx.ALL, 5)

        self.m_staticText10 = wx.StaticText(
            self.m_panel5,
            wx.ID_ANY,
            "in seconds",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText10.Wrap(-1)

        bSizer21.Add(
            self.m_staticText10, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        bSizer19.Add(bSizer21, 0, wx.EXPAND, 5)

        self.m_staticline11 = wx.StaticLine(
            self.m_panel5,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.LI_HORIZONTAL,
        )
        bSizer19.Add(self.m_staticline11, 0, wx.EXPAND | wx.ALL, 5)

        bSizer23 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_checkBox6 = wx.CheckBox(
            self.m_panel5,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        bSizer23.Add(self.m_checkBox6, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.m_staticText11 = wx.StaticText(
            self.m_panel5,
            wx.ID_ANY,
            "By Header (filterline) text:",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText11.Wrap(-1)

        bSizer23.Add(
            self.m_staticText11, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_textCtrl4 = wx.TextCtrl(
            self.m_panel5,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_textCtrl4.Enable(False)

        bSizer23.Add(self.m_textCtrl4, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        m_radioBox1Choices = ["including", "excluding"]
        self.m_radioBox1 = wx.RadioBox(
            self.m_panel5,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            m_radioBox1Choices,
            1,
            wx.RA_SPECIFY_ROWS,
        )
        self.m_radioBox1.SetSelection(0)
        self.m_radioBox1.Enable(False)

        bSizer23.Add(self.m_radioBox1, 0, wx.ALL, 5)

        bSizer19.Add(bSizer23, 0, wx.EXPAND, 5)

        self.m_staticline111 = wx.StaticLine(
            self.m_panel5,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.LI_HORIZONTAL,
        )
        bSizer19.Add(self.m_staticline111, 0, wx.EXPAND | wx.ALL, 5)

        bSizer231 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_checkBox61 = wx.CheckBox(
            self.m_panel5,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        bSizer231.Add(
            self.m_checkBox61, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_staticText111 = wx.StaticText(
            self.m_panel5,
            wx.ID_ANY,
            "Round Collision Energy Decimal places",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText111.Wrap(-1)

        bSizer231.Add(
            self.m_staticText111, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_spinCtrl11 = wx.SpinCtrl(
            self.m_panel5,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.SP_ARROW_KEYS,
            0,
            6,
            6,
        )
        self.m_spinCtrl11.Enable(False)

        bSizer231.Add(self.m_spinCtrl11, 0, wx.ALL, 5)

        bSizer19.Add(bSizer231, 0, wx.EXPAND, 5)

        self.m_staticline152 = wx.StaticLine(
            self.m_panel5,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.LI_HORIZONTAL,
        )
        bSizer19.Add(self.m_staticline152, 0, wx.EXPAND | wx.ALL, 5)

        bSizer231 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_checkBox61 = wx.CheckBox(
            self.m_panel5,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_checkBox61.SetValue(True)
        bSizer231.Add(
            self.m_checkBox61, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_staticText111 = wx.StaticText(
            self.m_panel5,
            wx.ID_ANY,
            "Remove 'lock ' from header text",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText111.Wrap(-1)

        self.m_staticText111.SetToolTip(
            "ms lock and ms non lock are considered the same"
        )

        bSizer231.Add(
            self.m_staticText111, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        bSizer19.Add(bSizer231, 0, wx.EXPAND, 5)

        self.m_staticline153 = wx.StaticLine(
            self.m_panel5,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.LI_HORIZONTAL,
        )
        bSizer19.Add(self.m_staticline153, 0, wx.EXPAND | wx.ALL, 5)

        bSizer2311 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_checkBox611 = wx.CheckBox(
            self.m_panel5,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_checkBox611.SetValue(True)
        bSizer2311.Add(
            self.m_checkBox611, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_staticText1111 = wx.StaticText(
            self.m_panel5,
            wx.ID_ANY,
            "Remove Scans with increased Ion Injection Time",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText1111.Wrap(-1)

        self.m_staticText1111.SetToolTip(
            "unusually increased Ion Injection Time indicates the scan is in transition and is invalid"
        )

        bSizer2311.Add(
            self.m_staticText1111, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        bSizer19.Add(bSizer2311, 0, wx.EXPAND, 5)

        self.m_panel5.SetSizer(bSizer19)
        self.m_panel5.Layout()
        bSizer19.Fit(self.m_panel5)
        self.m_notebook1.AddPage(self.m_panel5, "Scan Selection", False)
        self.m_panel6 = wx.Panel(
            self.m_notebook1,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.TAB_TRAVERSAL,
        )
        bSizer25 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticline15 = wx.StaticLine(
            self.m_panel6,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.LI_HORIZONTAL,
        )
        bSizer25.Add(self.m_staticline15, 0, wx.EXPAND | wx.ALL, 5)

        bSizer43 = wx.BoxSizer(wx.VERTICAL)

        self.m_radioBtn10 = wx.RadioButton(
            self.m_panel6,
            wx.ID_ANY,
            "Use Default",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_radioBtn10.SetValue(True)
        self.m_radioBtn10.SetFont(
            wx.Font(
                9,
                wx.FONTFAMILY_SWISS,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                False,
                "Arial",
            )
        )

        bSizer43.Add(self.m_radioBtn10, 0, wx.ALL, 5)

        bSizer25.Add(bSizer43, 0, wx.EXPAND, 5)

        self.m_staticline181 = wx.StaticLine(
            self.m_panel6,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.LI_HORIZONTAL,
        )
        bSizer25.Add(self.m_staticline181, 0, wx.EXPAND | wx.ALL, 5)

        bSizer26 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_radioBtn11 = wx.RadioButton(
            self.m_panel6,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        bSizer26.Add(self.m_radioBtn11, 0, wx.ALL, 5)

        self.m_staticText14 = wx.StaticText(
            self.m_panel6,
            wx.ID_ANY,
            "Group to decimal place",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText14.Wrap(-1)

        self.m_staticText14.SetFont(
            wx.Font(
                9,
                wx.FONTFAMILY_SWISS,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                False,
                "Arial",
            )
        )
        self.m_staticText14.Enable(False)

        bSizer26.Add(
            self.m_staticText14, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_spinCtrl2 = wx.SpinCtrl(
            self.m_panel6,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.SP_ARROW_KEYS,
            1,
            10,
            2,
        )
        self.m_spinCtrl2.Enable(False)

        bSizer26.Add(self.m_spinCtrl2, 0, wx.ALL, 5)

        self.m_staticText15 = wx.StaticText(
            self.m_panel6,
            wx.ID_ANY,
            "discard groups less than",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText15.Wrap(-1)

        self.m_staticText15.SetFont(
            wx.Font(
                9,
                wx.FONTFAMILY_SWISS,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                False,
                "Arial",
            )
        )
        self.m_staticText15.Enable(False)

        bSizer26.Add(
            self.m_staticText15, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_spinCtrl1 = wx.SpinCtrl(
            self.m_panel6,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.SP_ARROW_KEYS,
            0,
            10,
            2,
        )
        self.m_spinCtrl1.Enable(False)

        bSizer26.Add(self.m_spinCtrl1, 0, wx.ALL, 5)

        self.m_staticText22 = wx.StaticText(
            self.m_panel6,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText22.Wrap(-1)

        self.m_staticText22.SetFont(
            wx.Font(
                9,
                wx.FONTFAMILY_SWISS,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                False,
                "Arial",
            )
        )
        self.m_staticText22.Enable(False)

        bSizer26.Add(
            self.m_staticText22, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        bSizer25.Add(bSizer26, 0, wx.EXPAND, 5)

        self.m_panel6.SetSizer(bSizer25)
        self.m_panel6.Layout()
        bSizer25.Fit(self.m_panel6)
        self.m_notebook1.AddPage(self.m_panel6, "Prefilter Peaks", False)
        self.m_panel7 = wx.Panel(
            self.m_notebook1,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.TAB_TRAVERSAL,
        )
        bSizer34 = wx.BoxSizer(wx.VERTICAL)

        bSizer42 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_radioBtn9 = wx.RadioButton(
            self.m_panel7,
            wx.ID_ANY,
            "Use Default (a= 5408000.0, b=0.5)",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_radioBtn9.SetValue(True)
        self.m_radioBtn9.SetFont(
            wx.Font(
                9,
                wx.FONTFAMILY_SWISS,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                False,
                "Arial",
            )
        )

        bSizer42.Add(self.m_radioBtn9, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        bSizer34.Add(bSizer42, 0, wx.EXPAND, 5)

        bSizer31 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticline16 = wx.StaticLine(
            self.m_panel7,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.LI_HORIZONTAL,
        )
        bSizer31.Add(self.m_staticline16, 0, wx.EXPAND | wx.ALL, 5)

        bSizer32 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_radioBtn1 = wx.RadioButton(
            self.m_panel7,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        bSizer32.Add(self.m_radioBtn1, 0, wx.ALL, 5)

        self.m_staticText23 = wx.StaticText(
            self.m_panel7,
            wx.ID_ANY,
            "By Measured Resolution trend line",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText23.Wrap(-1)

        self.m_staticText23.SetFont(
            wx.Font(
                9,
                wx.FONTFAMILY_SWISS,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                False,
                "Arial",
            )
        )
        self.m_staticText23.Enable(False)

        bSizer32.Add(self.m_staticText23, 0, wx.ALL, 5)

        bSizer31.Add(bSizer32, 0, wx.EXPAND, 5)

        bSizer34.Add(bSizer31, 0, wx.EXPAND, 5)

        bSizer311 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticline161 = wx.StaticLine(
            self.m_panel7,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.LI_HORIZONTAL,
        )
        bSizer311.Add(self.m_staticline161, 0, wx.EXPAND | wx.ALL, 5)

        bSizer321 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_radioBtn4 = wx.RadioButton(
            self.m_panel7,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        bSizer321.Add(self.m_radioBtn4, 0, wx.ALL, 5)

        self.m_staticText231 = wx.StaticText(
            self.m_panel7,
            wx.ID_ANY,
            "By Resolution based on quadratic function r = a *m/z ^ -b, seperate MS1 and MS2",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText231.Wrap(-1)

        self.m_staticText231.SetFont(
            wx.Font(
                9,
                wx.FONTFAMILY_SWISS,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                False,
                "Arial",
            )
        )
        self.m_staticText231.Enable(False)

        bSizer321.Add(self.m_staticText231, 0, wx.ALL, 5)

        bSizer311.Add(bSizer321, 0, wx.EXPAND, 5)

        bSizer331 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_staticText241 = wx.StaticText(
            self.m_panel7,
            wx.ID_ANY,
            "where a =",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText241.Wrap(-1)

        self.m_staticText241.SetFont(
            wx.Font(
                9,
                wx.FONTFAMILY_SWISS,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                False,
                "Arial",
            )
        )
        self.m_staticText241.Enable(False)

        bSizer331.Add(
            self.m_staticText241, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_textCtrl61 = wx.TextCtrl(
            self.m_panel7,
            wx.ID_ANY,
            "5408000.0",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_textCtrl61.Enable(False)

        bSizer331.Add(self.m_textCtrl61, 0, wx.ALL, 5)

        self.m_staticText251 = wx.StaticText(
            self.m_panel7,
            wx.ID_ANY,
            "and b =",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText251.Wrap(-1)

        self.m_staticText251.SetFont(
            wx.Font(
                9,
                wx.FONTFAMILY_SWISS,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                False,
                "Arial",
            )
        )
        self.m_staticText251.Enable(False)

        bSizer331.Add(
            self.m_staticText251, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_textCtrl71 = wx.TextCtrl(
            self.m_panel7,
            wx.ID_ANY,
            "0.5",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_textCtrl71.Enable(False)

        bSizer331.Add(self.m_textCtrl71, 0, wx.ALL, 5)

        self.m_staticText38 = wx.StaticText(
            self.m_panel7,
            wx.ID_ANY,
            "for MS1",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText38.Wrap(-1)

        self.m_staticText38.Enable(False)

        bSizer331.Add(
            self.m_staticText38, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        bSizer311.Add(bSizer331, 0, wx.EXPAND, 5)

        bSizer3311 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_staticText2411 = wx.StaticText(
            self.m_panel7,
            wx.ID_ANY,
            "where a =",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText2411.Wrap(-1)

        self.m_staticText2411.SetFont(
            wx.Font(
                9,
                wx.FONTFAMILY_SWISS,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                False,
                "Arial",
            )
        )
        self.m_staticText2411.Enable(False)

        bSizer3311.Add(
            self.m_staticText2411, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_textCtrl611 = wx.TextCtrl(
            self.m_panel7,
            wx.ID_ANY,
            "5408000.0",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_textCtrl611.Enable(False)

        bSizer3311.Add(self.m_textCtrl611, 0, wx.ALL, 5)

        self.m_staticText2511 = wx.StaticText(
            self.m_panel7,
            wx.ID_ANY,
            "and b =",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText2511.Wrap(-1)

        self.m_staticText2511.SetFont(
            wx.Font(
                9,
                wx.FONTFAMILY_SWISS,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                False,
                "Arial",
            )
        )
        self.m_staticText2511.Enable(False)

        bSizer3311.Add(
            self.m_staticText2511, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_textCtrl711 = wx.TextCtrl(
            self.m_panel7,
            wx.ID_ANY,
            "0.5",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_textCtrl711.Enable(False)

        bSizer3311.Add(self.m_textCtrl711, 0, wx.ALL, 5)

        self.m_staticText381 = wx.StaticText(
            self.m_panel7,
            wx.ID_ANY,
            "for MS2",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText381.Wrap(-1)

        self.m_staticText381.Enable(False)

        bSizer3311.Add(
            self.m_staticText381, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_staticline162 = wx.StaticLine(
            self.m_panel7,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.LI_HORIZONTAL,
        )
        bSizer3311.Add(self.m_staticline162, 0, wx.EXPAND | wx.ALL, 5)

        bSizer311.Add(bSizer3311, 0, wx.EXPAND, 5)

        bSizer34.Add(bSizer311, 0, wx.EXPAND, 5)

        bSizer38 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_checkBox11 = wx.CheckBox(
            self.m_panel7,
            wx.ID_ANY,
            "Merge overlapping bins",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_checkBox11.SetValue(True)
        self.m_checkBox11.Enable(False)

        bSizer38.Add(self.m_checkBox11, 0, wx.ALL, 5)

        bSizer34.Add(bSizer38, 1, wx.EXPAND, 5)

        self.m_panel7.SetSizer(bSizer34)
        self.m_panel7.Layout()
        bSizer34.Fit(self.m_panel7)
        self.m_notebook1.AddPage(self.m_panel7, "Bin Type", False)
        self.m_panel8 = wx.Panel(
            self.m_notebook1,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.TAB_TRAVERSAL,
        )
        bSizer251 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticline151 = wx.StaticLine(
            self.m_panel8,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.LI_HORIZONTAL,
        )
        bSizer251.Add(self.m_staticline151, 0, wx.EXPAND | wx.ALL, 5)

        bSizer431 = wx.BoxSizer(wx.VERTICAL)

        self.m_radioBtn101 = wx.RadioButton(
            self.m_panel8,
            wx.ID_ANY,
            "Use Default",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_radioBtn101.SetValue(True)
        self.m_radioBtn101.SetFont(
            wx.Font(
                9,
                wx.FONTFAMILY_SWISS,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                False,
                "Arial",
            )
        )

        bSizer431.Add(self.m_radioBtn101, 0, wx.ALL, 5)

        bSizer251.Add(bSizer431, 0, wx.EXPAND, 5)

        self.m_staticline1811 = wx.StaticLine(
            self.m_panel8,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.LI_HORIZONTAL,
        )
        bSizer251.Add(self.m_staticline1811, 0, wx.EXPAND | wx.ALL, 5)

        bSizer261 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_radioBtn111 = wx.RadioButton(
            self.m_panel8,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        bSizer261.Add(self.m_radioBtn111, 0, wx.ALL, 5)

        self.m_staticline1812 = wx.StaticText(
            self.m_panel8,
            wx.ID_ANY,
            "Minimum Repetition Rate",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticline1812.Wrap(-1)

        self.m_staticline1812.SetFont(
            wx.Font(
                9,
                wx.FONTFAMILY_SWISS,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                False,
                "Arial",
            )
        )
        self.m_staticline1812.Enable(False)

        bSizer261.Add(
            self.m_staticline1812, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_spinCtrl21 = wx.SpinCtrl(
            self.m_panel8,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.SP_ARROW_KEYS,
            1,
            99,
            70,
        )
        self.m_spinCtrl21.Enable(False)

        bSizer261.Add(self.m_spinCtrl21, 0, wx.ALL, 5)

        self.m_staticText26 = wx.StaticText(
            self.m_panel8,
            wx.ID_ANY,
            "%",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText26.Wrap(-1)

        self.m_staticText26.Enable(False)

        bSizer261.Add(
            self.m_staticText26, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        bSizer251.Add(bSizer261, 0, wx.EXPAND, 5)

        bSizer2611 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_staticline18121 = wx.StaticText(
            self.m_panel8,
            wx.ID_ANY,
            "Minimum signal to noise ratio",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticline18121.Wrap(-1)

        self.m_staticline18121.SetFont(
            wx.Font(
                9,
                wx.FONTFAMILY_SWISS,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                False,
                "Arial",
            )
        )
        self.m_staticline18121.Enable(False)

        bSizer2611.Add(
            self.m_staticline18121, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5
        )

        self.m_textCtrl612 = wx.TextCtrl(
            self.m_panel8,
            wx.ID_ANY,
            "1.0",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_textCtrl612.Enable(False)

        bSizer2611.Add(self.m_textCtrl612, 0, wx.ALL, 5)

        bSizer251.Add(bSizer2611, 0, wx.EXPAND, 5)

        self.m_panel8.SetSizer(bSizer251)
        self.m_panel8.Layout()
        bSizer251.Fit(self.m_panel8)
        self.m_notebook1.AddPage(self.m_panel8, "Bin Filter", False)
        self.m_panel9 = wx.Panel(
            self.m_notebook1,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.TAB_TRAVERSAL,
        )
        bSizer39 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticline17 = wx.StaticLine(
            self.m_panel9,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.LI_HORIZONTAL,
        )
        bSizer39.Add(self.m_staticline17, 0, wx.EXPAND | wx.ALL, 5)

        self.m_staticText41 = wx.StaticText(
            self.m_panel9,
            wx.ID_ANY,
            "Status Log:",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText41.Wrap(-1)

        bSizer39.Add(self.m_staticText41, 0, wx.ALL, 5)

        self.m_statuslog = wx.TextCtrl(
            self.m_panel9,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.TE_MULTILINE | wx.TE_READONLY,
        )
        bSizer39.Add(self.m_statuslog, 1, wx.ALL | wx.EXPAND, 5)

        self.m_panel9.SetSizer(bSizer39)
        self.m_panel9.Layout()
        bSizer39.Fit(self.m_panel9)
        self.m_notebook1.AddPage(self.m_panel9, "Status", False)

        bSizer3.Add(self.m_notebook1, 9, wx.EXPAND | wx.ALL, 5)

        self.m_panel2 = wx.Panel(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.TAB_TRAVERSAL,
        )
        bSizer4 = wx.BoxSizer(wx.VERTICAL)

        self.m_buttonFinish = wx.Button(
            self.m_panel2,
            wx.ID_ANY,
            "Finish",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_buttonFinish.Enable(False)

        bSizer4.Add(self.m_buttonFinish, 0, wx.ALL | wx.ALIGN_RIGHT, 5)

        self.m_panel2.SetSizer(bSizer4)
        self.m_panel2.Layout()
        bSizer4.Fit(self.m_panel2)
        bSizer3.Add(self.m_panel2, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(bSizer3)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.m_buttonBrowse.Bind(wx.EVT_BUTTON, self.clickedBrowse)
        self.m_button3.Bind(wx.EVT_BUTTON, self.clickOpenSpecReord)
        self.m_button4.Bind(wx.EVT_BUTTON, self.clickedSimStitcher)
        self.m_checkBox8.Bind(wx.EVT_CHECKBOX, self.checkOutcsv)
        self.m_checkBox9.Bind(wx.EVT_CHECKBOX, self.checkoutLog)
        self.m_checkBox10.Bind(wx.EVT_CHECKBOX, self.checkOutConf)
        self.m_checkBox5.Bind(wx.EVT_CHECKBOX, self.checkScanRet)
        self.m_checkBox6.Bind(wx.EVT_CHECKBOX, self.checkScanHead)
        self.m_checkBox61.Bind(wx.EVT_CHECKBOX, self.checkRoundCollision)
        self.m_checkBox61.Bind(wx.EVT_CHECKBOX, self.checkScanHead)
        self.m_checkBox611.Bind(wx.EVT_CHECKBOX, self.checkScanHead)
        self.m_radioBtn10.Bind(wx.EVT_RADIOBUTTON, self.radioPre)
        self.m_radioBtn11.Bind(wx.EVT_RADIOBUTTON, self.radioPre)
        self.m_radioBtn9.Bind(wx.EVT_RADIOBUTTON, self.radioBin)
        self.m_radioBtn1.Bind(wx.EVT_RADIOBUTTON, self.radioBin)
        self.m_radioBtn4.Bind(wx.EVT_RADIOBUTTON, self.radioBin)
        self.m_radioBtn101.Bind(wx.EVT_RADIOBUTTON, self.radioFil)
        self.m_radioBtn111.Bind(wx.EVT_RADIOBUTTON, self.radioFil)
        self.m_buttonFinish.Bind(wx.EVT_BUTTON, self.clickedFinish)

    def __del__(self):
        pass

    # Virtual event handlers, overide them in your derived class
    def clickedBrowse(self, event):
        event.Skip()

    def clickOpenSpecReord(self, event):
        event.Skip()

    def clickedSimStitcher(self, event):
        event.Skip()

    def checkOutcsv(self, event):
        event.Skip()

    def checkoutLog(self, event):
        event.Skip()

    def checkOutConf(self, event):
        event.Skip()

    def checkScanRet(self, event):
        event.Skip()

    def checkScanHead(self, event):
        event.Skip()

    def checkRoundCollision(self, event):
        event.Skip()

    def radioPre(self, event):
        event.Skip()

    def radioBin(self, event):
        event.Skip()

    def radioFil(self, event):
        event.Skip()

    def clickedFinish(self, event):
        event.Skip()
