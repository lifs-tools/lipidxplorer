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
## Class MyFrame1
###########################################################################

class MyFrame1 ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 993,702 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_MENU ) )

		bSizer1 = wx.BoxSizer( wx.VERTICAL )

		bSizer8 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, "Reorder Scans", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1.Wrap( -1 )

		self.m_staticText1.SetFont( wx.Font( 14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial Black" ) )

		bSizer8.Add( self.m_staticText1, 0, wx.ALL, 5 )


		bSizer8.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_staticline1 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer8.Add( self.m_staticline1, 0, wx.EXPAND |wx.ALL, 5 )


		bSizer1.Add( bSizer8, 1, wx.EXPAND, 5 )

		bSizer9 = wx.BoxSizer( wx.VERTICAL )

		bSizer2 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText2 = wx.StaticText( self, wx.ID_ANY, "Select MZxml File:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText2.Wrap( -1 )

		bSizer2.Add( self.m_staticText2, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.m_filePicker1 = wx.FilePickerCtrl( self, wx.ID_ANY, wx.EmptyString, "Select a file", "*.*", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		bSizer2.Add( self.m_filePicker1, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


		bSizer9.Add( bSizer2, 1, wx.EXPAND, 5 )

		self.m_staticline5 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer9.Add( self.m_staticline5, 0, wx.EXPAND |wx.ALL, 5 )


		bSizer1.Add( bSizer9, 1, wx.EXPAND, 5 )

		bSizer3 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_searchCtrl2 = wx.SearchCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_searchCtrl2.ShowSearchButton( True )
		self.m_searchCtrl2.ShowCancelButton( False )
		bSizer3.Add( self.m_searchCtrl2, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.m_button_sub = wx.Button( self, wx.ID_ANY, "sub", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer3.Add( self.m_button_sub, 0, wx.ALL, 5 )

		self.m_button_clear = wx.Button( self, wx.ID_ANY, "clear", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer3.Add( self.m_button_clear, 0, wx.ALL, 5 )


		bSizer1.Add( bSizer3, 1, wx.EXPAND, 5 )

		bSizer4 = wx.BoxSizer( wx.HORIZONTAL )

		m_listBox1Choices = []
		self.m_listBox1 = wx.ListBox( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_listBox1Choices, 0 )
		bSizer4.Add( self.m_listBox1, 1, wx.ALL|wx.EXPAND, 5 )

		bSizer7 = wx.BoxSizer( wx.VERTICAL )

		bSizer5 = wx.BoxSizer( wx.VERTICAL )

		self.m_button1 = wx.Button( self, wx.ID_ANY, "add all", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer5.Add( self.m_button1, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

		self.m_button2 = wx.Button( self, wx.ID_ANY, "remove", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer5.Add( self.m_button2, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )


		bSizer7.Add( bSizer5, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5 )


		bSizer4.Add( bSizer7, 0, wx.ALIGN_CENTER_VERTICAL, 5 )

		m_listBox2Choices = []
		self.m_listBox2 = wx.ListBox( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_listBox2Choices, wx.LB_EXTENDED|wx.LB_NEEDED_SB )
		bSizer4.Add( self.m_listBox2, 1, wx.ALL|wx.EXPAND, 5 )


		bSizer1.Add( bSizer4, 12, wx.EXPAND, 5 )

		bSizer6 = wx.BoxSizer( wx.VERTICAL )

		bSizer10 = wx.BoxSizer( wx.HORIZONTAL )


		bSizer10.Add( ( 0, 0), 0, wx.EXPAND, 5 )

		self.m_textCtrl_1 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_READONLY )
		bSizer10.Add( self.m_textCtrl_1, 0, wx.ALL, 5 )


		bSizer10.Add( ( 0, 0), 2, wx.EXPAND, 5 )

		self.m_textCtrl_2 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_READONLY )
		bSizer10.Add( self.m_textCtrl_2, 0, wx.ALL, 5 )


		bSizer10.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_button3 = wx.Button( self, wx.ID_ANY, "Finish", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer10.Add( self.m_button3, 0, wx.ALL|wx.ALIGN_RIGHT, 5 )


		bSizer6.Add( bSizer10, 1, wx.EXPAND, 5 )


		bSizer1.Add( bSizer6, 1, wx.EXPAND, 5 )


		self.SetSizer( bSizer1 )
		self.Layout()

		self.Centre( wx.BOTH )

		# Connect Events
		self.m_filePicker1.Bind( wx.EVT_FILEPICKER_CHANGED, self.updateFile )
		self.m_searchCtrl2.Bind( wx.EVT_SEARCHCTRL_SEARCH_BTN, self.toggleSearch )
		self.m_searchCtrl2.Bind( wx.EVT_TEXT, self.updateSourceList )
		self.m_button_sub.Bind( wx.EVT_BUTTON, self.makeSublist )
		self.m_button_clear.Bind( wx.EVT_BUTTON, self.clear_subandsearch )
		self.m_button1.Bind( wx.EVT_BUTTON, self.addToTargetList )
		self.m_button2.Bind( wx.EVT_BUTTON, self.removeFromTargetList )
		self.m_button3.Bind( wx.EVT_BUTTON, self.finish )

	def __del__( self ):
		pass


	# Virtual event handlers, overide them in your derived class
	def updateFile( self, event ):
		event.Skip()

	def toggleSearch( self, event ):
		event.Skip()

	def updateSourceList( self, event ):
		event.Skip()

	def makeSublist( self, event ):
		event.Skip()

	def clear_subandsearch( self, event ):
		event.Skip()

	def addToTargetList( self, event ):
		event.Skip()

	def removeFromTargetList( self, event ):
		event.Skip()

	def finish( self, event ):
		event.Skip()


