# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version Oct 26 2018)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc
import wx.adv
import wx.propgrid as pg

###########################################################################
## Class MyWizard1
###########################################################################


class MyWizard1(wx.adv.Wizard):
    def __init__(self, parent):
        wx.adv.Wizard.__init__(
            self,
            parent,
            id=wx.ID_ANY,
            title=wx.EmptyString,
            bitmap=wx.NullBitmap,
            pos=wx.DefaultPosition,
            style=wx.DEFAULT_DIALOG_STYLE,
        )

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.m_pages = []

        self.m_wizPage1 = wx.adv.WizardPageSimple(self)
        self.add_page(self.m_wizPage1)

        bSizer1 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText1 = wx.StaticText(
            self.m_wizPage1,
            wx.ID_ANY,
            "Folder with Input files",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText1.Wrap(-1)

        bSizer1.Add(self.m_staticText1, 0, wx.ALL, 5)

        self.m_dirPicker_input = wx.DirPickerCtrl(
            self.m_wizPage1,
            wx.ID_ANY,
            wx.EmptyString,
            "Select a folder",
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.DIRP_DEFAULT_STYLE,
        )
        bSizer1.Add(self.m_dirPicker_input, 0, wx.ALL | wx.EXPAND, 5)

        self.m_wizPage1.SetSizer(bSizer1)
        self.m_wizPage1.Layout()
        bSizer1.Fit(self.m_wizPage1)
        self.m_wizPage2 = wx.adv.WizardPageSimple(self)
        self.add_page(self.m_wizPage2)

        bSizer3 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText3 = wx.StaticText(
            self.m_wizPage2,
            wx.ID_ANY,
            "Input files",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText3.Wrap(-1)

        bSizer3.Add(self.m_staticText3, 0, wx.ALL, 5)

        m_checkList1_inputfilesChoices = []
        self.m_checkList1_inputfiles = wx.CheckListBox(
            self.m_wizPage2,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            m_checkList1_inputfilesChoices,
            0,
        )
        bSizer3.Add(self.m_checkList1_inputfiles, 1, wx.ALL | wx.EXPAND, 5)

        self.m_wizPage2.SetSizer(bSizer3)
        self.m_wizPage2.Layout()
        bSizer3.Fit(self.m_wizPage2)
        self.m_wizPage3 = wx.adv.WizardPageSimple(self)
        self.add_page(self.m_wizPage3)

        bSizer2 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText2 = wx.StaticText(
            self.m_wizPage3,
            wx.ID_ANY,
            "Root MFQL folder",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText2.Wrap(-1)

        bSizer2.Add(self.m_staticText2, 0, wx.ALL, 5)

        self.m_dirPicker_rootMFQLdir = wx.DirPickerCtrl(
            self.m_wizPage3,
            wx.ID_ANY,
            wx.EmptyString,
            "Select a folder",
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.DIRP_DEFAULT_STYLE,
        )
        bSizer2.Add(self.m_dirPicker_rootMFQLdir, 0, wx.ALL | wx.EXPAND, 5)

        self.m_wizPage3.SetSizer(bSizer2)
        self.m_wizPage3.Layout()
        bSizer2.Fit(self.m_wizPage3)
        self.m_wizPage4 = wx.adv.WizardPageSimple(self)
        self.add_page(self.m_wizPage4)

        bSizer4 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText4 = wx.StaticText(
            self.m_wizPage4,
            wx.ID_ANY,
            "MFQL files",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.m_staticText4.Wrap(-1)

        bSizer4.Add(self.m_staticText4, 0, wx.ALL, 5)

        m_checkList2_mfqlfilesChoices = []
        self.m_checkList2_mfqlfiles = wx.CheckListBox(
            self.m_wizPage4,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            m_checkList2_mfqlfilesChoices,
            0,
        )
        bSizer4.Add(self.m_checkList2_mfqlfiles, 1, wx.ALL | wx.EXPAND, 5)

        self.m_wizPage4.SetSizer(bSizer4)
        self.m_wizPage4.Layout()
        bSizer4.Fit(self.m_wizPage4)
        self.m_wizPage5 = wx.adv.WizardPageSimple(self)
        self.add_page(self.m_wizPage5)

        bSizer5 = wx.BoxSizer(wx.VERTICAL)

        self.Autofill_Parameters_label = wx.StaticText(
            self.m_wizPage5,
            wx.ID_ANY,
            "Autofill Parameters",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.Autofill_Parameters_label.Wrap(-1)

        bSizer5.Add(self.Autofill_Parameters_label, 0, wx.ALL, 5)

        self.m_propertyGridManager_props = pg.PropertyGridManager(
            self.m_wizPage5,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.propgrid.PGMAN_DEFAULT_STYLE,
        )
        self.m_propertyGridManager_props.SetExtraStyle(
            wx.propgrid.PG_EX_MODE_BUTTONS
        )
        bSizer5.Add(self.m_propertyGridManager_props, 1, wx.ALL | wx.EXPAND, 5)

        self.m_wizPage5.SetSizer(bSizer5)
        self.m_wizPage5.Layout()
        bSizer5.Fit(self.m_wizPage5)
        self.Centre(wx.BOTH)

        # Connect Events
        self.Bind(wx.adv.EVT_WIZARD_FINISHED, self.wiz_finished)
        self.Bind(wx.adv.EVT_WIZARD_PAGE_CHANGED, self.page_changed)

    def add_page(self, page):
        if self.m_pages:
            previous_page = self.m_pages[-1]
            page.SetPrev(previous_page)
            previous_page.SetNext(page)
        self.m_pages.append(page)

    def __del__(self):
        pass

    # Virtual event handlers, overide them in your derived class
    def wiz_finished(self, event):
        event.Skip()

    def page_changed(self, event):
        event.Skip()
