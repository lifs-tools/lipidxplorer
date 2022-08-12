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
## Class Lx2_gui
###########################################################################

class Lx2_gui ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"LX2_dev", pos = wx.DefaultPosition, size = wx.Size( 738,767 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_MENU ) )

		bSizer11 = wx.BoxSizer( wx.VERTICAL )

		self.m_notebook1 = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_panel5 = wx.Panel( self.m_notebook1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.m_panel5.SetToolTip( u"Blanks and Quality controls are not used to calculate signal stability" )

		bSizer12 = wx.BoxSizer( wx.VERTICAL )

		bSizer13 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText4 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Select Spectra Folder", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText4.Wrap( -1 )

		bSizer13.Add( self.m_staticText4, 0, wx.ALL, 5 )

		self.spectra_folder = wx.DirPickerCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, u"Select a folder", wx.DefaultPosition, wx.DefaultSize, wx.DIRP_DEFAULT_STYLE )
		bSizer13.Add( self.spectra_folder, 1, wx.ALL, 5 )


		bSizer12.Add( bSizer13, 0, wx.EXPAND, 5 )

		self.m_staticline1 = wx.StaticLine( self.m_panel5, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer12.Add( self.m_staticline1, 0, wx.EXPAND |wx.ALL, 5 )

		bSizer131 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText41 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Select Project or Settings file*", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText41.Wrap( -1 )

		bSizer131.Add( self.m_staticText41, 0, wx.ALL, 5 )

		self.ini_file = wx.FilePickerCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, u"Select a file", u"*.*", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		bSizer131.Add( self.ini_file, 1, wx.ALL|wx.EXPAND, 5 )


		bSizer12.Add( bSizer131, 0, wx.EXPAND, 5 )

		self.m_staticline2 = wx.StaticLine( self.m_panel5, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer12.Add( self.m_staticline2, 0, wx.EXPAND |wx.ALL, 5 )

		bSizer18 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText9 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Select Spectra by:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText9.Wrap( -1 )

		self.m_staticText9.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString ) )

		bSizer18.Add( self.m_staticText9, 0, wx.ALL|wx.EXPAND, 5 )

		bSizer20 = wx.BoxSizer( wx.VERTICAL )

		bSizer21 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText12 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Time range", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText12.Wrap( -1 )

		bSizer21.Add( self.m_staticText12, 0, wx.ALL, 5 )

		self.time_range1 = wx.TextCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer21.Add( self.time_range1, 0, wx.TOP|wx.BOTTOM, 5 )

		self.m_textCtrl10 = wx.TextCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer21.Add( self.m_textCtrl10, 0, wx.TOP|wx.BOTTOM, 5 )

		self.m_staticText13 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"s", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText13.Wrap( -1 )

		bSizer21.Add( self.m_staticText13, 0, wx.ALL, 5 )

		self.m_staticText22 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"|", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText22.Wrap( -1 )

		bSizer21.Add( self.m_staticText22, 0, wx.ALL, 5 )

		self.pos_mode_button = wx.Button( self.m_panel5, wx.ID_ANY, u"Positive mode", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer21.Add( self.pos_mode_button, 1, wx.ALL|wx.EXPAND, 5 )

		self.neg_mode_buttom = wx.Button( self.m_panel5, wx.ID_ANY, u"Negavite mode", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer21.Add( self.neg_mode_buttom, 1, wx.ALL|wx.EXPAND, 5 )

		self.drop_fuzzy_button = wx.Button( self.m_panel5, wx.ID_ANY, u"Drop Fuzzy", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.drop_fuzzy_button.SetToolTip( u"Initial scans oftenhave invalid data, discard these scans?" )

		bSizer21.Add( self.drop_fuzzy_button, 1, wx.ALL|wx.EXPAND, 5 )


		bSizer20.Add( bSizer21, 1, wx.EXPAND, 5 )

		bSizer211 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText121 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Mass Range", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText121.Wrap( -1 )

		bSizer211.Add( self.m_staticText121, 0, wx.ALL, 5 )

		self.mass_range_ms1_1 = wx.TextCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer211.Add( self.mass_range_ms1_1, 0, wx.TOP|wx.BOTTOM, 5 )

		self.mass_range_ms1_1 = wx.TextCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer211.Add( self.mass_range_ms1_1, 0, wx.TOP|wx.BOTTOM, 5 )

		self.m_staticText131 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"MS1", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText131.Wrap( -1 )

		bSizer211.Add( self.m_staticText131, 0, wx.ALL, 5 )

		self.m_staticText19 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"|", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText19.Wrap( -1 )

		bSizer211.Add( self.m_staticText19, 0, wx.ALL, 5 )

		self.m_staticText20 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Mass Range", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText20.Wrap( -1 )

		bSizer211.Add( self.m_staticText20, 0, wx.ALL, 5 )

		self.mass_range_ms2_1 = wx.TextCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer211.Add( self.mass_range_ms2_1, 0, wx.TOP|wx.BOTTOM, 5 )

		self.mass_range_ms2_2 = wx.TextCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer211.Add( self.mass_range_ms2_2, 0, wx.TOP|wx.BOTTOM, 5 )

		self.m_staticText21 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"MS2", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText21.Wrap( -1 )

		bSizer211.Add( self.m_staticText21, 0, wx.ALL, 5 )


		bSizer20.Add( bSizer211, 1, wx.EXPAND, 5 )

		bSizer25 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText24 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Including Text", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText24.Wrap( -1 )

		bSizer25.Add( self.m_staticText24, 0, wx.ALL, 5 )

		self.text_include = wx.TextCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer25.Add( self.text_include, 1, wx.TOP|wx.BOTTOM|wx.RIGHT|wx.EXPAND, 5 )

		self.m_staticText25 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"|", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText25.Wrap( -1 )

		bSizer25.Add( self.m_staticText25, 0, wx.ALL, 5 )

		self.m_staticText26 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Excluding text", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText26.Wrap( -1 )

		bSizer25.Add( self.m_staticText26, 0, wx.ALL|wx.EXPAND, 5 )

		self.text_eclude = wx.TextCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer25.Add( self.text_eclude, 1, wx.ALL|wx.EXPAND, 5 )


		bSizer20.Add( bSizer25, 0, wx.EXPAND, 5 )


		bSizer18.Add( bSizer20, 1, wx.EXPAND, 5 )


		bSizer12.Add( bSizer18, 0, wx.EXPAND, 5 )

		self.m_staticline3 = wx.StaticLine( self.m_panel5, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer12.Add( self.m_staticline3, 0, wx.EXPAND |wx.ALL, 5 )

		bSizer181 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText91 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Select Spectra by:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText91.Wrap( -1 )

		self.m_staticText91.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString ) )

		bSizer181.Add( self.m_staticText91, 0, wx.ALL|wx.EXPAND, 5 )

		bSizer201 = wx.BoxSizer( wx.VERTICAL )

		bSizer212 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText122 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Repetition Rate within Spectra", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText122.Wrap( -1 )

		bSizer212.Add( self.m_staticText122, 0, wx.ALL|wx.EXPAND, 5 )

		self.rep_rate_slider = wx.Slider( self.m_panel5, wx.ID_ANY, 70, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
		bSizer212.Add( self.rep_rate_slider, 0, wx.ALL, 5 )

		self.rep_rate_txt = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"70", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer212.Add( self.rep_rate_txt, 0, wx.ALL, 5 )

		self.m_staticText132 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"%", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText132.Wrap( -1 )

		bSizer212.Add( self.m_staticText132, 0, wx.ALL, 5 )

		self.m_staticText76 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"|", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText76.Wrap( -1 )

		bSizer212.Add( self.m_staticText76, 0, wx.ALL, 5 )

		self.select_blank_btn = wx.Button( self.m_panel5, wx.ID_ANY, u"Select Blank", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer212.Add( self.select_blank_btn, 0, wx.ALL, 5 )

		self.QC_spectra_button = wx.Button( self.m_panel5, wx.ID_ANY, u"QC Spectra", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer212.Add( self.QC_spectra_button, 0, wx.ALL, 5 )


		bSizer201.Add( bSizer212, 0, 0, 5 )

		bSizer2121 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText1221 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Found in % of spectra", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1221.Wrap( -1 )

		bSizer2121.Add( self.m_staticText1221, 0, wx.ALL, 5 )

		self.found_in_slider = wx.Slider( self.m_panel5, wx.ID_ANY, 0, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
		bSizer2121.Add( self.found_in_slider, 0, wx.ALL, 5 )

		self.found_int_txt = wx.TextCtrl( self.m_panel5, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer2121.Add( self.found_int_txt, 0, wx.ALL, 5 )

		self.m_staticText1321 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"%", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1321.Wrap( -1 )

		bSizer2121.Add( self.m_staticText1321, 0, wx.ALL, 5 )

		self.m_staticText74 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"|", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText74.Wrap( -1 )

		self.m_staticText74.SetToolTip( u"|" )

		bSizer2121.Add( self.m_staticText74, 0, wx.ALL, 5 )

		self.m_staticText75 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Number of Blanks and QC", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText75.Wrap( -1 )

		bSizer2121.Add( self.m_staticText75, 0, wx.ALL, 5 )

		self.qc_count_txt = wx.TextCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer2121.Add( self.qc_count_txt, 0, wx.ALL, 5 )


		bSizer201.Add( bSizer2121, 0, 0, 5 )

		bSizer2111 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText1211 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Signal Intensity", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1211.Wrap( -1 )

		bSizer2111.Add( self.m_staticText1211, 0, wx.ALL, 5 )

		self.signla_inty_ms1_txt = wx.TextCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer2111.Add( self.signla_inty_ms1_txt, 0, wx.TOP|wx.BOTTOM, 5 )

		ms1_sig_inty_typeChoices = [ u"Absolute", u"Relative" ]
		self.ms1_sig_inty_type = wx.Choice( self.m_panel5, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, ms1_sig_inty_typeChoices, 0 )
		self.ms1_sig_inty_type.SetSelection( 1 )
		bSizer2111.Add( self.ms1_sig_inty_type, 0, wx.ALL, 5 )

		self.m_staticText1311 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"MS1", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1311.Wrap( -1 )

		bSizer2111.Add( self.m_staticText1311, 0, wx.ALL, 5 )

		self.m_staticText191 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"|", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText191.Wrap( -1 )

		bSizer2111.Add( self.m_staticText191, 0, wx.ALL, 5 )

		self.m_staticText12111 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Signal Intensity", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText12111.Wrap( -1 )

		bSizer2111.Add( self.m_staticText12111, 0, wx.ALL, 5 )

		self.signla_inty_ms1_txt = wx.TextCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer2111.Add( self.signla_inty_ms1_txt, 0, wx.TOP|wx.BOTTOM, 5 )

		ms2_sig_inty_typeChoices = [ u"Absolute", u"Relative" ]
		self.ms2_sig_inty_type = wx.Choice( self.m_panel5, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, ms2_sig_inty_typeChoices, 0 )
		self.ms2_sig_inty_type.SetSelection( 0 )
		bSizer2111.Add( self.ms2_sig_inty_type, 0, wx.ALL, 5 )

		self.m_staticText211 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"MS2", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText211.Wrap( -1 )

		bSizer2111.Add( self.m_staticText211, 0, wx.ALL, 5 )


		bSizer201.Add( bSizer2111, 0, 0, 5 )


		bSizer181.Add( bSizer201, 0, wx.EXPAND, 5 )


		bSizer12.Add( bSizer181, 0, wx.EXPAND, 5 )

		self.m_staticline7 = wx.StaticLine( self.m_panel5, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer12.Add( self.m_staticline7, 0, wx.EXPAND |wx.ALL, 5 )

		bSizer56 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText100 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Selection Window and Calibration", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText100.Wrap( -1 )

		self.m_staticText100.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString ) )

		bSizer56.Add( self.m_staticText100, 0, wx.ALL, 5 )

		bSizer57 = wx.BoxSizer( wx.VERTICAL )

		bSizer58 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText102 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Precursor grouping tolerance", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText102.Wrap( -1 )

		bSizer58.Add( self.m_staticText102, 0, wx.ALL, 5 )

		self.prec_group_tol = wx.TextCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer58.Add( self.prec_group_tol, 0, wx.ALL, 5 )

		self.m_staticText103 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Da.", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText103.Wrap( -1 )

		bSizer58.Add( self.m_staticText103, 0, wx.ALL, 5 )

		self.m_button20 = wx.Button( self.m_panel5, wx.ID_ANY, u"Estimate grouping tolerance", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer58.Add( self.m_button20, 0, wx.ALL, 5 )


		bSizer57.Add( bSizer58, 0, wx.EXPAND, 5 )

		bSizer59 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText104 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Calibration masses", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText104.Wrap( -1 )

		bSizer59.Add( self.m_staticText104, 0, wx.ALL, 5 )

		self.cal_masses_ms1 = wx.TextCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.cal_masses_ms1.SetToolTip( u"comma seperated values" )

		bSizer59.Add( self.cal_masses_ms1, 0, wx.ALL, 5 )

		self.m_staticText105 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"MS1", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText105.Wrap( -1 )

		bSizer59.Add( self.m_staticText105, 0, wx.ALL, 5 )

		self.m_staticText106 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"|", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText106.Wrap( -1 )

		bSizer59.Add( self.m_staticText106, 0, wx.ALL, 5 )

		self.l_masses_ms2 = wx.TextCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.l_masses_ms2.SetToolTip( u"will use MS! calubration masses if none are provieded" )

		bSizer59.Add( self.l_masses_ms2, 0, wx.ALL, 5 )

		self.m_staticText107 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"MS2", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText107.Wrap( -1 )

		bSizer59.Add( self.m_staticText107, 0, wx.ALL, 5 )

		self.m_button21 = wx.Button( self.m_panel5, wx.ID_ANY, u"Suggest Calibration masses", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer59.Add( self.m_button21, 0, wx.ALL, 5 )


		bSizer57.Add( bSizer59, 1, wx.EXPAND, 5 )


		bSizer56.Add( bSizer57, 1, wx.EXPAND, 5 )


		bSizer12.Add( bSizer56, 0, wx.EXPAND, 5 )

		self.m_staticline8 = wx.StaticLine( self.m_panel5, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer12.Add( self.m_staticline8, 0, wx.EXPAND |wx.ALL, 5 )

		bSizer60 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText108 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Resolution and Tolerance:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText108.Wrap( -1 )

		self.m_staticText108.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString ) )

		bSizer60.Add( self.m_staticText108, 0, wx.ALL, 5 )

		bSizer61 = wx.BoxSizer( wx.VERTICAL )

		bSizer62 = wx.BoxSizer( wx.VERTICAL )

		bSizer591 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText1041 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Resolution of lowest mass", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1041.Wrap( -1 )

		bSizer591.Add( self.m_staticText1041, 0, wx.ALL, 5 )

		self.ms1_low_mass_res_txt = wx.TextCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer591.Add( self.ms1_low_mass_res_txt, 0, wx.ALL, 5 )

		self.m_staticText1051 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"MS1", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1051.Wrap( -1 )

		bSizer591.Add( self.m_staticText1051, 0, wx.ALL, 5 )

		self.m_staticText1061 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"|", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1061.Wrap( -1 )

		bSizer591.Add( self.m_staticText1061, 0, wx.ALL, 5 )

		self.ms2_low_mass_res_txt = wx.TextCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer591.Add( self.ms2_low_mass_res_txt, 0, wx.ALL, 5 )

		self.m_staticText1071 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"MS2", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1071.Wrap( -1 )

		bSizer591.Add( self.m_staticText1071, 0, wx.ALL, 5 )

		self.m_button211 = wx.Button( self.m_panel5, wx.ID_ANY, u"Suggest Resolution", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_button211.SetToolTip( u"NOTE: this is not the actual resolution; its the average distance between peaks acrosss scans" )

		bSizer591.Add( self.m_button211, 0, wx.ALL, 5 )

		self.m_staticText125 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"FWHM", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText125.Wrap( -1 )

		bSizer591.Add( self.m_staticText125, 0, wx.ALL, 5 )


		bSizer62.Add( bSizer591, 0, 0, 5 )

		bSizer5911 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText10411 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Resolution gradient", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText10411.Wrap( -1 )

		bSizer5911.Add( self.m_staticText10411, 0, wx.ALL, 5 )

		self.ms1_res_gradient_txt = wx.TextCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer5911.Add( self.ms1_res_gradient_txt, 0, wx.ALL, 5 )

		self.m_staticText10511 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"MS1", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText10511.Wrap( -1 )

		bSizer5911.Add( self.m_staticText10511, 0, wx.ALL, 5 )

		self.m_staticText10611 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"|", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText10611.Wrap( -1 )

		bSizer5911.Add( self.m_staticText10611, 0, wx.ALL, 5 )

		self.ms2_res_gradient_txt = wx.TextCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer5911.Add( self.ms2_res_gradient_txt, 0, wx.ALL, 5 )

		self.m_staticText10711 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"MS2", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText10711.Wrap( -1 )

		bSizer5911.Add( self.m_staticText10711, 0, wx.ALL, 5 )

		self.m_button2111 = wx.Button( self.m_panel5, wx.ID_ANY, u"Suggest Gradient", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer5911.Add( self.m_button2111, 0, wx.ALL, 5 )

		self.m_button31 = wx.Button( self.m_panel5, wx.ID_ANY, u"See estimated Resolution", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_button31.SetToolTip( u"NOTE: this is not the actual resolution; its the average distance between peaks within a scan" )

		bSizer5911.Add( self.m_button31, 0, wx.ALL, 5 )


		bSizer62.Add( bSizer5911, 0, 0, 5 )

		bSizer59111 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText104111 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Tolerance", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText104111.Wrap( -1 )

		bSizer59111.Add( self.m_staticText104111, 0, wx.ALL, 5 )

		self.ms1_tolerance_txt = wx.TextCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer59111.Add( self.ms1_tolerance_txt, 0, wx.ALL|wx.EXPAND, 5 )

		ms1_tolerance_type_choiseChoices = [ u"PPM", u"Da" ]
		self.ms1_tolerance_type_choise = wx.Choice( self.m_panel5, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, ms1_tolerance_type_choiseChoices, 0 )
		self.ms1_tolerance_type_choise.SetSelection( 1 )
		bSizer59111.Add( self.ms1_tolerance_type_choise, 0, wx.ALL, 5 )

		self.m_staticText105111 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"MS1", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText105111.Wrap( -1 )

		bSizer59111.Add( self.m_staticText105111, 0, wx.ALL, 5 )

		self.m_staticText106111 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"|", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText106111.Wrap( -1 )

		bSizer59111.Add( self.m_staticText106111, 0, wx.ALL, 5 )

		self.ms2_tol_text = wx.TextCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer59111.Add( self.ms2_tol_text, 0, wx.ALL, 5 )

		ms2_tol_type_choiseChoices = [ u"PPM", u"Da" ]
		self.ms2_tol_type_choise = wx.Choice( self.m_panel5, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, ms2_tol_type_choiseChoices, 0 )
		self.ms2_tol_type_choise.SetSelection( 1 )
		bSizer59111.Add( self.ms2_tol_type_choise, 0, wx.ALL, 5 )

		self.m_staticText107111 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"MS2", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText107111.Wrap( -1 )

		bSizer59111.Add( self.m_staticText107111, 0, wx.ALL, 5 )

		self.m_button21111 = wx.Button( self.m_panel5, wx.ID_ANY, u"Suggest Tolerance", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer59111.Add( self.m_button21111, 0, wx.ALL, 5 )


		bSizer62.Add( bSizer59111, 1, wx.EXPAND, 5 )


		bSizer61.Add( bSizer62, 1, wx.EXPAND, 5 )


		bSizer60.Add( bSizer61, 1, wx.EXPAND, 5 )


		bSizer12.Add( bSizer60, 0, 0, 5 )

		self.m_staticline9 = wx.StaticLine( self.m_panel5, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer12.Add( self.m_staticline9, 0, wx.EXPAND |wx.ALL, 5 )

		bSizer72 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_button32 = wx.Button( self.m_panel5, wx.ID_ANY, u"Save Settings", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer72.Add( self.m_button32, 0, wx.ALL, 5 )

		self.m_button33 = wx.Button( self.m_panel5, wx.ID_ANY, u"Save as...", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer72.Add( self.m_button33, 0, wx.ALL, 5 )

		self.m_button35 = wx.Button( self.m_panel5, wx.ID_ANY, u"log output", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer72.Add( self.m_button35, 0, wx.ALL, 5 )

		self.m_button34 = wx.Button( self.m_panel5, wx.ID_ANY, u"Generate MasterScan", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_button34.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString ) )

		bSizer72.Add( self.m_button34, 1, wx.ALL, 5 )


		bSizer12.Add( bSizer72, 1, wx.EXPAND, 5 )


		self.m_panel5.SetSizer( bSizer12 )
		self.m_panel5.Layout()
		bSizer12.Fit( self.m_panel5 )
		self.m_notebook1.AddPage( self.m_panel5, u"Import Settings", False )

		bSizer11.Add( self.m_notebook1, 1, wx.EXPAND |wx.ALL, 5 )


		self.SetSizer( bSizer11 )
		self.Layout()
		self.m_menubar1 = wx.MenuBar( 0 )
		self.SetMenuBar( self.m_menubar1 )

		self.m_statusBar1 = self.CreateStatusBar( 1, wx.STB_SIZEGRIP, wx.ID_ANY )

		self.Centre( wx.BOTH )

		# Connect Events
		self.spectra_folder.Bind( wx.EVT_DIRPICKER_CHANGED, self.spectra_dir_changed )
		self.ini_file.Bind( wx.EVT_FILEPICKER_CHANGED, self.ini_file_changed )
		self.pos_mode_button.Bind( wx.EVT_BUTTON, self.pos_mode_clicked )
		self.neg_mode_buttom.Bind( wx.EVT_BUTTON, self.neg_mode_clicked )
		self.drop_fuzzy_button.Bind( wx.EVT_BUTTON, self.drop_fuzzy_clicked )
		self.rep_rate_slider.Bind( wx.EVT_SCROLL, self.rep_rate_slider )
		self.rep_rate_txt.Bind( wx.EVT_TEXT_ENTER, self.rep_rate_texted )
		self.select_blank_btn.Bind( wx.EVT_BUTTON, self.slect_blanck clicked )
		self.QC_spectra_button.Bind( wx.EVT_BUTTON, self.qc_spectrza_clicked )
		self.found_in_slider.Bind( wx.EVT_SCROLL, self.found_in_slider )
		self.found_int_txt.Bind( wx.EVT_TEXT_ENTER, self.found_in_texted )
		self.qc_count_txt.Bind( wx.EVT_TEXT_ENTER, self.qc_count_texted )
		self.m_button20.Bind( wx.EVT_BUTTON, self.estimate_prec_group_clicked )
		self.m_button21.Bind( wx.EVT_BUTTON, self.suggest_cal_masses_clicked )
		self.m_button211.Bind( wx.EVT_BUTTON, self.suggest_res_clicked )
		self.m_button2111.Bind( wx.EVT_BUTTON, self.suggest_gradient_clicked )
		self.m_button31.Bind( wx.EVT_BUTTON, self.see_est_res_clicked )
		self.m_button21111.Bind( wx.EVT_BUTTON, self.suggest_tol_clicked )
		self.m_button32.Bind( wx.EVT_BUTTON, self.save_settings_clicked )
		self.m_button33.Bind( wx.EVT_BUTTON, self.save_as_clicked )
		self.m_button35.Bind( wx.EVT_BUTTON, self.log_out_clicked )
		self.m_button34.Bind( wx.EVT_BUTTON, self.gen_masterscan_clicked )

	def __del__( self ):
		pass


	# Virtual event handlers, override them in your derived class
	def spectra_dir_changed( self, event ):
		event.Skip()

	def ini_file_changed( self, event ):
		event.Skip()

	def pos_mode_clicked( self, event ):
		event.Skip()

	def neg_mode_clicked( self, event ):
		event.Skip()

	def drop_fuzzy_clicked( self, event ):
		event.Skip()

	def rep_rate_slider( self, event ):
		event.Skip()

	def rep_rate_texted( self, event ):
		event.Skip()

	def slect_blanck clicked( self, event ):
		event.Skip()

	def qc_spectrza_clicked( self, event ):
		event.Skip()

	def found_in_slider( self, event ):
		event.Skip()

	def found_in_texted( self, event ):
		event.Skip()

	def qc_count_texted( self, event ):
		event.Skip()

	def estimate_prec_group_clicked( self, event ):
		event.Skip()

	def suggest_cal_masses_clicked( self, event ):
		event.Skip()

	def suggest_res_clicked( self, event ):
		event.Skip()

	def suggest_gradient_clicked( self, event ):
		event.Skip()

	def see_est_res_clicked( self, event ):
		event.Skip()

	def suggest_tol_clicked( self, event ):
		event.Skip()

	def save_settings_clicked( self, event ):
		event.Skip()

	def save_as_clicked( self, event ):
		event.Skip()

	def log_out_clicked( self, event ):
		event.Skip()

	def gen_masterscan_clicked( self, event ):
		event.Skip()


