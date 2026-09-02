import sys
import os
import webbrowser
import wx
import wx.stc as stc
import wx.lib.buttons as buttons
import wx.lib.fancytext as fancytext
import wx.grid
import wx.html
import wx.adv
import csv
import re
import configparser
import threading
import traceback
import subprocess, json
import multiprocessing as mp

from wx.lib.newevent import NewEvent
import queue
import pickle
import io
from pathlib import Path

sysPath = '..' + os.sep + 'lib'
sys.path.append(sysPath)

from lx.lxMain import startMFQL

# the MFQL editor
from lx.gui.editor import PythonSTC

# those are for the MS-Tools. TODO: out source
from lx.mfql.chemParser import parseElemSeq
from lx.mfql.chemsc import calcSFbyMass
from lx.mfql.isotope import isotopicValuesInter, isotopicValues
from lx.mfql.runtimeStatic import TypeTolerance

# the lipid identification routines
from lx.lipidIdentification import syntaxCheck
from lx.spectraImport import getInputFiles, doImport

# the (one and only) exception
from lx.exceptions import LipidXException, SyntaxErrorException,\
		LogicErrorException, ImportException

#from lpdxSCTools import *
from lx.gui.sampleGrouping import ChooseGroupsFrame
from lx.project import Project, GUIProject
from lx.tools import staticTypeDict, odict, strToBool

from lx.debugger import Debug, DebugSet, DebugUnset

from lx.batch_processor import run_batch





balloontip = True
try:
    from agw import balloontip as BT
except ImportError: # if it's not there locally, try the wxPython lib.
	try:
		import wx.lib.agw.balloontip as BT
	except ImportError:
		balloontip = False


def resource_path(*parts):
    if hasattr(sys, "_MEIPASS"):          # PyInstaller
        base = Path(sys._MEIPASS)
    else:
        # this file is in .../lx/gui/, so go up two levels to project root
        base = Path(__file__).resolve().parents[2]
    return str(base.joinpath(*parts))


#import lpdxSCC
import platform
pf = platform.system()
# Bound unconditionally: none of the platform checks below currently enable
# sound, so this was always going to end up False for every recognized
# platform anyway. Previously it was only set inside the LINUX/CYGWIN_NT/
# WINDOWS branches, so platform.system() == 'Darwin' (macOS) fell through
# with playSound never bound at all, raising NameError at every one of the
# 9 call sites the first time a button handler read it.
playSound = False
if re.match('.*LINUX.*', pf, re.IGNORECASE):
	playSound = False
if re.match('.*CYGWIN_NT.*', pf, re.IGNORECASE):
	playSound = False
if re.match('.*WINDOWS.*', pf, re.IGNORECASE):
	playSound = False

# for exception forwarding
def formatExceptionInfo(maxTBlevel=None):
    cla, exc, trbk = sys.exc_info()
    excName = cla.__name__
    try:
        #excArgs = exc.__dict__["args"]
        excArgs = exc.args
    except KeyError:
        excArgs = "<no args>"
    excTb = traceback.format_tb(trbk, maxTBlevel)
    return (excName, excArgs, excTb, exc)

# Define File Drop Target class
class FileDropTarget(wx.FileDropTarget):
	""" This object implements Drop Target functionality for Files """
	def __init__(self, obj, callback, fileExt):
		""" Initialize the Drop Target, passing in the Object Reference to
			indicate what should receive the dropped files """
		# Initialize the wsFileDropTarget Object
		wx.FileDropTarget.__init__(self)
		# Store the Object Reference for dropped files
		self.obj = obj
		self.fileExt = fileExt

		self._callback = callback

	def OnDropFiles(self, x, y, filenames):
		""" Implement File Drop """
		# append a list of the file names dropped
		if len(filenames) > 1:
			raise LipidXException("Only a single file is dropable here.")

		if re.match(r'(.*\.%s$)' % (self.fileExt), filenames[0]):
			self._callback(filenames[0])

# Define File Drop Target class
class DrawerDropTarget(wx.FileDropTarget):
	""" This object implements Drop Target functionality for folders """
	def __init__(self, obj, callback):
		""" Initialize the Drop Target, passing in the Object Reference to
			indicate what should receive the dropped files """
		# Initialize the wsFileDropTarget Object
		wx.FileDropTarget.__init__(self)
		# Store the Object Reference for dropped files
		self.obj = obj

		self._callback = callback

	def OnDropFiles(self, x, y, filenames):
		""" Implement File Drop """
		# append a list of the file names dropped
		if len(filenames) > 1:
			raise LipidXException("Only a single file is dropable here.")

		if not os.path.isdir(filenames[0]):
			raise LipidXException("Only folders are dropable here.")

		self.obj.WriteText(filenames[0])

		self._callback(filenames[0])

###########################################
### Define MasterScan Drop Target class ###

class FileDrawerDropTarget(wx.FileDropTarget):
	""" This object implements Drop Target functionality for Files and Directories """
	def __init__(self, obj, callback, fileExt):

		# Initialize the wx.FileDropTarget Object
		wx.FileDropTarget.__init__(self)
		# Store the Object Reference for dropped files
		self.obj = obj
		self.fileExt = fileExt

		self._callback = callback

	def OnDropFiles(self, x, y, filenames):
		""" Implement File Drop """
		# append a list of the file names dropped

		if len(filenames) > 1:
			raise LipidXException("Only a single file is dropable here.")

		else:
			p = filenames[0]
			if os.path.isdir(p):
				for root, dirs, files in os.walk(p):
					for f in files:
						if re.match(r'(.*\.%s$)' % (self.fileExt), f):
							n = os.path.join(root, f)
							self.obj.WriteText(n)
							self._callback(n)
			else:
				self.obj.WriteText(p)
				self._callback(p)

class GeneralFileDrawerDropTarget(FileDrawerDropTarget):
	""" This object implements Drop Target functionality for Files and Directories """
	def __init__(self, obj, callback, fileExt):

		# Initialize the wx.FileDropTarget Object
		wx.FileDropTarget.__init__(self)
		# Store the Object Reference for dropped files
		self.obj = obj
		self.fileExt = fileExt

		self._callback = callback

	def OnDropFiles(self, x, y, filenames):
		""" Implement File Drop """
		# append a list of the file names dropped

		if len(filenames) > 1:
			raise LipidXException("Only a single file is dropable here.")

		else:
			p = filenames[0]
			if os.path.isdir(p):
				for root, dirs, files in os.walk(p):
					for f in files:
						if re.match(r'(.*\.%s$)' % (self.fileExt), f):
							n = os.path.join(root, f)
							self._callback(n)
			else:
				self._callback(p)

### Define MasterScan Drop Target class ###
###########################################


# Define Text Drop Target class
class MFQLDropTarget(wx.FileDropTarget):
	""" This object implements Drop Target functionality for Text """
	def __init__(self, obj, parent):

		# Initialize the wx.FileDropTarget Object
		wx.FileDropTarget.__init__(self)
		# Store the Object Reference for dropped files
		self.obj = obj

		self.parent = parent

	def OnDropFiles(self, x, y, filenames):
		""" Implement File Drop """
		# append a list of the file names dropped
		for p in filenames:

			if os.path.isdir(p):
				for root, dirs, files in os.walk(p):
					for f in files:
						if re.match(r'(.*\.mfql$)', f):
							n = os.path.join(root, f)
							self.parent.filePath_AddMFQL.append(n)
							l = n.split(os.sep)
							self.parent.dictMFQLScripts[l[-1]] = n
			else:
				self.parent.filePath_AddMFQL.append(p)
				l = p.split(os.sep)
				self.parent.dictMFQLScripts[l[-1]] = p

		#self.parent.list_box_1.Set(sorted(self.parent.dictMFQLScripts.keys()))
		self.parent.list_box_1.Set(list(self.parent.dictMFQLScripts.keys()))


USE_GENERIC = 1
if USE_GENERIC:
	from wx.lib.stattext import GenStaticText as StaticText
else:
	StaticText = wx.StaticText

# begin wxGlade: extracode
# end wxGlade

def relativePath(fullpath):

	loc = os.getcwd()
	listLoc = loc.split(os.sep)
	listFullPath = fullpath.split(os.sep)

	index = 0
	while index < max(len(listFullPath), len(listLoc)):
		if listLoc != []:
			if listFullPath[index] == listLoc[index]:
				del listFullPath[index]
				del listLoc[index]
			else:
				for index in range(len(listLoc)):
					listLoc[index] = '..'
				listLoc += listFullPath

				strRTR = '%s' % listLoc[0]
				for i in listLoc[1:]:
					strRTR += os.sep + i
				return strRTR

		elif listFullPath:
			strRTR = '%s' % listFullPath[0]
			for i in listFullPath[1:]:
				strRTR += os.sep + i
			return strRTR
		else:
			return '.'

	if not listFullPath:
		return '.'

def opj(path):
	"""Convert paths to the platform-specific separator"""


	st = os.path.join(*tuple(path.split('/')))
	# HACK: on Linux, a leading / gets lost...
	if path.startswith('/'):
	    st = '/' + st
	return st

ID_BEGIN=100
wxStdOut, EVT_STDOUT= NewEvent()
wxWriteDebug, EVT_WRITE_DEBUG = NewEvent()
wxWorkerDone, EVT_WORKER_DONE = NewEvent()

wxProgressDLG_Update, EVT_PROGRESSDLG_UPDATE = NewEvent()

class Worker(threading.Thread):

	requestID = 0
	def __init__(self, parent, requestQ, resultQ, **kwds):
		threading.Thread.__init__(self, **kwds)
		#self.setDaemon(True)
		self.setDaemon(False)
		self.requestQ = queue.Queue()#requestQ
		self.resultQ = queue.Queue()#resultQ
		self.parent = wx.GetApp()
		self.start()

	def beginThread(self, callable, *args, **kwds):
		Worker.requestID +=1
		self.requestQ.put((Worker.requestID, callable, args, kwds))
		return Worker.requestID

	def run(self):

		sys.stdout = SysOutListener()
		print("\n***Debugging Mode!***")
		sys.stderr = SysOutListener()
		while True:
			dlg = None
			requestID, callable, args, kwds = self.requestQ.get()
			try:
				if not wx.GetApp().frame.debugOpen:
					wx.GetApp().frame.OnMenuDebugWin(None)
				self.resultQ.put((requestID, callable(*args, **kwds)))

				result = self.resultQ.get()[1]

				if result == self.parent.frame.CONST_THREAD_SUCCESSFUL:
					dlg = wx.MessageDialog(wx.GetApp().frame, "Task completed.", "Ready", wx.OK|wx.ICON_INFORMATION)

				elif result == self.parent.frame.CONST_THREAD_USER_ABORT:
					dlg = wx.MessageDialog(wx.GetApp().frame, "User aborted.", "Ready", wx.OK|wx.ICON_EXCLAMATION)

				if dlg is not None:
					if dlg.ShowModal() == wx.ID_OK:
						dlg.Destroy()

			except SyntaxErrorException:
				evt = wxStdOut(text = '')#v.value)
				if not wx.GetApp().frame.debugOpen:
					wx.GetApp().frame.OnMenuDebugWin(None)
				wx.PostEvent(wx.GetApp().frame, evt)

				(excName, excArgs, excTb, exc) = formatExceptionInfo()
				dlg = wx.MessageDialog(wx.GetApp().frame,"%s" % (exc), "SYNTAX ERROR", wx.OK|wx.ICON_ERROR)
				if dlg.ShowModal() == wx.ID_OK:
					dlg.Destroy()

			except LogicErrorException:
				evt = wxStdOut(text = '')#v.value)
				if not wx.GetApp().frame.debugOpen:
					wx.GetApp().frame.OnMenuDebugWin(None)
				wx.PostEvent(wx.GetApp().frame, evt)

				(excName, excArgs, excTb, exc) = formatExceptionInfo()
				dlg = wx.MessageDialog(wx.GetApp().frame, "%s" % exc, "LOGICAL ERROR", wx.OK|wx.ICON_ERROR)
				if dlg.ShowModal() == wx.ID_OK:
					dlg.Destroy()

			except LipidXException:

				#wx.GetApp().frame.handleLipidXException()

				evt = wxStdOut(text = '')#v.value)
				if not wx.GetApp().frame.debugOpen:
					wx.GetApp().frame.OnMenuDebugWin(None)
				wx.PostEvent(wx.GetApp().frame, evt)

				(excName, excArgs, excTb, exc) = formatExceptionInfo()
				dlg = wx.MessageDialog(wx.GetApp().frame, "%s" % exc, "ERROR", wx.OK|wx.ICON_ERROR)
				if dlg.ShowModal() == wx.ID_OK:
					dlg.Destroy()

			except ImportException:
				evt = wxStdOut(text = '')#v.value)
				if not wx.GetApp().frame.debugOpen:
					wx.GetApp().frame.OnMenuDebugWin(None)
				wx.PostEvent(wx.GetApp().frame, evt)

				(excName, excArgs, excTb, exc) = formatExceptionInfo()
				dlg = wx.MessageDialog(wx.GetApp().frame, "%s" % exc, "IMPORT ERROR", wx.OK|wx.ICON_ERROR)
				if dlg.ShowModal() == wx.ID_OK:
					dlg.Destroy()


			except Exception:
				traceback.print_tb(sys.exc_info()[2])
				evt = wxStdOut(text = '')
				if not wx.GetApp().frame.debugOpen:
					wx.GetApp().frame.OnMenuDebugWin(None)
				wx.PostEvent(wx.GetApp().frame, evt)
				(excName, excArgs, excTb, exc) = formatExceptionInfo()
				print(excName, exc)

				text = "The following error occured:\n\n"
				text += "** %s : %s **\n\n\n" % (excName, exc)
				text += "If you think that this a bug in the software you can send\na bug report to the us.\n"
				text += "Do you want to generate the bug report?"
				dlg = wx.MessageDialog(wx.GetApp().frame, text, "ERROR", style=wx.YES_NO|wx.CANCEL|wx.NO_DEFAULT)
				#dlg = MyErrorDialog(wx.GetApp().frame, -1, "ERROR", 'bla')
				r = dlg.ShowModal()
				if r == wx.ID_YES:

					dlg = wx.MessageDialog(wx.GetApp().frame, "Please store the bugReport.html and send it to lifs-support@isas.de", \
							"ERROR", style=wx.OK)
					if dlg.ShowModal() == wx.ID_OK:
						dlg.Destroy()

					strBugReport = """
					<html><head></head><body>
					<h3>%s</h3>
					<h3>%s</h3>
					<h3>%s</h3>
					<p><tt>
					""" % (sys.version, excName, exc)
					for i in excTb:
						strBugReport += "%s<br>" % i
					strBugReport += "</tt></p><br>"
					strBugReport += "%s" % wx.GetApp().frame.genBugReportHTML()
					strBugReport += "</body></html>"

					dlg = wx.FileDialog(wx.GetApp().frame, "Specify the site for the bugReport.html",
						style=wx.DD_DEFAULT_STYLE|wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT,
						defaultFile = "bugReport.html")
					dlg.SetWildcard("*.html files|*.html")

					if dlg.ShowModal() == wx.ID_OK:
						d = dlg.GetPath()
						with open(d, 'w') as f:
							f.write(strBugReport)
						print(d)

				else:
					dlg.Destroy()

				#dlg = wx.MessageDialog(wx.GetApp().frame,"%s: %s" % (excName, exc), "Error.", wx.OK|wx.ICON_ERROR)
				#if dlg.ShowModal() == wx.ID_OK:
				#	dlg.Destroy()

			evt = wxWorkerDone(msg = callable.__name__)
			wx.PostEvent(wx.GetApp().frame, evt)


			#evt = wxWorkerDone()
			#wx.PostEvent(wx.GetApp().frame, evt)
				#self.resultQ.put((requestID, callable(*args, **kwds)))
				#evt = wxWorkerDone()
				#wx.PostEvent(wx.GetApp().frame, evt)
				#str = traceback.print_tb(sys.exc_info()[2]).join('/n')
				#evt = wxStdOut(text = traceback.print_tb(sys.exc_info()[2]))
				#evt = wxStdOut(text = str)
		#	print traceback.print_tb(sys.exc_info()[2])

class SysOutListener:
	def write(self, string):
		#sys.__stdout__.write(string)
		evt = wxStdOut(text=string)
		#wx.PostEvent(wx.GetApp().frame.output_window, evt)
		wx.PostEvent(wx.GetApp().frame, evt)

class MyErrorDialog(wx.Dialog):

	def __init__(self, parent, id, title, text):

		wx.Dialog.__init__(self, parent, id, title, size=(400, 230))

		self.sizer_v1 = wx.BoxSizer(wx.VERTICAL)
		self.sizer_b1 = wx.StdDialogButtonSizer()

		self.button_ok = wx.Button(self, wx.ID_OK)
		self.button_ok.SetDefault()
		self.sizer_b1.Add(self.button_ok)
		self.sizer_b1.Realize()

		self.txt_error = wx.html.HtmlWindow(self)
		self.txt_error.SetPage(text)
		self.txt_error.SetSize((380,150))

		self.sizer_v1.Add(self.txt_error, 0, wx.EXPAND|wx.ALL, 5)
		self.sizer_v1.Add(self.sizer_b1, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

		self.SetSizer(self.sizer_v1)
		#self.sizer_v1.Fit(self)

		self.Layout()

class MyHTMLDialog(wx.Dialog):

	def __init__(self, parent, id, title, text):
		wx.Dialog.__init__(self, parent, id, title, size=(400, 450))



class TextOutFrame(wx.Frame):

    def __init__(self, *args, **kwds):

        kwds["style"] = (
            wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.SYSTEM_MENU |
            wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN | wx.RESIZE_BORDER
        )

        super().__init__(*args, **kwds)

        self.parent = args[0]

        # for the progressDialog
        self.progressDialog = None

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.text_ctrl = stc.StyledTextCtrl(
            self,
            style=wx.SIMPLE_BORDER | wx.HSCROLL | wx.VSCROLL |
                  wx.ALWAYS_SHOW_SB | wx.TE_MULTILINE
        )
        self.text_ctrl.SetMarginType(0, stc.STC_MARGIN_NUMBER)
        self.text_ctrl.SetMarginWidth(0, 52)
        self.text_ctrl.StyleSetSpec(stc.STC_STYLE_DEFAULT, "size:10,face:NSimSun")
        self.text_ctrl.StyleSetSpec(stc.STC_STYLE_LINENUMBER, "size:9,face:Arial")
        self.text_ctrl.SetMinSize((self.GetSize()[0] - 40, self.GetSize()[1] - 150))
        self.text_ctrl.SetSize((self.GetSize()[0] - 40, self.GetSize()[1] - 150))
        self.text_ctrl.SetScrollWidth(3000)

        self.button_clear = wx.Button(self, -1, "Clear Buffer")
        self.button_clear.SetSize((20, 9))
        self.button_clear.SetMaxSize((120, 24))
        self.button_clear.SetMinSize((120, 24))

        self.sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_buttons.Add(self.button_clear, 0, wx.ADJUST_MINSIZE | wx.ALIGN_BOTTOM, 10)

        self.sizer.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        self.sizer.Add(self.sizer_buttons, 0, wx.ADJUST_MINSIZE | wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 10)

        self.SetSizer(self.sizer)

        self.SetMinSize((860, 400))
        self.SetSize((860, 400))
        self.Layout()

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.Bind(wx.EVT_BUTTON, self.OnClear, self.button_clear)

        self.listError = []

    def write(self, text):
        if re.match(r'.*lpdxUIExceptions.*', text):
            match = re.match(r'.*lpdxUIExceptions.*:(.*)', text)
            if match:
                error = match.group(1)
                self.listError.append(error)
        self.text_ctrl.AppendText(text)

    def OnClear(self, evt):
        self.text_ctrl.ClearAll()

    def OnStop(self, evt):
        self.parent.isRunning = False

    def OnCloseWindow(self, evt):
        self.Show(False)
        self.parent.debugOpen = False
        
    def AppendText(self, text):
        self.text_ctrl.AppendText(text)
        self.text_ctrl.ShowPosition(self.text_ctrl.GetLastPosition())
		
		



class SetDebugFrame(wx.Frame):

	def __init__(self, *args, **kwds):

		# begin wxGlade: LpdxFrame.__init__
		kwds["style"] = wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.SYSTEM_MENU | wx.CAPTION \
		| wx.CLOSE_BOX | wx.CLIP_CHILDREN | wx.RESIZE_BORDER

		wx.Frame.__init__(self, *args, **kwds)
		#panel = wx.Panel(self, -1)

		self.parent = args[0]

		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.checkBox_IsotopicCorrection_MSMS = wx.CheckBox(self, -1, "MS/MS Type II Isotopic Correction debug output")
		self.checkBox_IsotopicCorrection_MSMS.SetToolTip(wx.ToolTip(
			"outputs debug information for MS/MS isotopic correction"))
		if Debug("isotopicCorrection"):
			self.checkBox_IsotopicCorrection_MSMS.SetValue(True)
		else:
			self.checkBox_IsotopicCorrection_MSMS.SetValue(False)

		self.checkBox_removeIsotopes = wx.CheckBox(self, -1, "Do not remove the isotopes (from Type II correction) from the result")
		self.checkBox_removeIsotopes.SetToolTip(wx.ToolTip(
			"do not remove the isotopes from the result"))
		if Debug("removeIsotopes"):
			self.checkBox_removeIsotopes.SetValue(False)
		else:
			self.checkBox_removeIsotopes.SetValue(True)

		self.checkBox_isotopesInMasterscan = wx.CheckBox(self, -1, "Show isotopic correction in MasterScan dump")
		self.checkBox_isotopesInMasterscan.SetToolTip(wx.ToolTip(
			"Show isotopic correction in MasterScan dump"))
		if Debug("isotopesInMasterScan"):
			self.checkBox_isotopesInMasterscan.SetValue(True)
		else:
			self.checkBox_isotopesInMasterscan.SetValue(False)

		self.checkBox_monoisotopicCorrection = wx.CheckBox(self, -1, "Don't do Type I isotopic correction.")
		self.checkBox_monoisotopicCorrection.SetToolTip(wx.ToolTip(
			"Don't do Type I isotopic correction."))
		if Debug("noMonoisotopicCorrection"):
			self.checkBox_monoisotopicCorrection.SetValue(True)
		else:
			self.checkBox_monoisotopicCorrection.SetValue(False)

		self.checkBox_relativeIntensity = wx.CheckBox(self, -1, "Print relative intensities in dump.")
		self.checkBox_relativeIntensity.SetToolTip(wx.ToolTip(
			"Print relative intensities."))
		if Debug("relativeIntensity"):
			self.checkBox_relativeIntensity.SetValue(True)
		else:
			self.checkBox_relativeIntensity.SetValue(False)

		self.checkBox_MemoryLog = wx.CheckBox(self, -1, "Log memory usage")
		self.checkBox_MemoryLog.SetToolTip(wx.ToolTip(
			"outputs the memory usage from the Python Windows process and the object heap"))
		if Debug("logMemory"):
			self.checkBox_MemoryLog.SetValue(True)
		else:
			self.checkBox_MemoryLog.SetValue(False)

		self.sizer.Add(self.checkBox_IsotopicCorrection_MSMS, 0, wx.LEFT|wx.TOP, 20)
		self.sizer.Add(self.checkBox_removeIsotopes, 0, wx.LEFT|wx.TOP, 20)
		self.sizer.Add(self.checkBox_isotopesInMasterscan, 0, wx.LEFT|wx.TOP, 20)
		self.sizer.Add(self.checkBox_monoisotopicCorrection, 0, wx.LEFT|wx.TOP, 20)
		self.sizer.Add(self.checkBox_relativeIntensity, 0, wx.LEFT|wx.TOP, 20)
		self.sizer.Add(self.checkBox_MemoryLog, 0, wx.LEFT|wx.TOP, 20)
		self.SetSizer(self.sizer)

		self.SetMinSize((300,200))
		self.Layout()

		self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
		self.Bind(wx.EVT_CHECKBOX, self.OnCheckMemoryLog, self.checkBox_MemoryLog)
		self.Bind(wx.EVT_CHECKBOX, self.OnCheckIsotopicCorrection_MSMS, self.checkBox_IsotopicCorrection_MSMS)
		self.Bind(wx.EVT_CHECKBOX, self.OnCheckRemoveIsotopes, self.checkBox_removeIsotopes)
		self.Bind(wx.EVT_CHECKBOX, self.OnCheckIsotopesInMasterScan, self.checkBox_isotopesInMasterscan)
		self.Bind(wx.EVT_CHECKBOX, self.OnCheckMonoisotopicCorrection, self.checkBox_monoisotopicCorrection)
		self.Bind(wx.EVT_CHECKBOX, self.OnCheckRelativeIntensity, self.checkBox_relativeIntensity)

	def OnCheckMemoryLog(self, evt):

		if self.checkBox_MemoryLog.GetValue():
			DebugSet("logMemory")
		else:
			DebugUnset("logMemory")

	def OnCheckIsotopicCorrection_MSMS(self, evt):

		if self.checkBox_IsotopicCorrection_MSMS.GetValue():
			DebugSet("isotopicCorrection")
		else:
			DebugUnset("isotopicCorrection")

	def OnCheckRemoveIsotopes(self, evt):

		if self.checkBox_removeIsotopes.GetValue():
			DebugUnset("removeIsotopes")
		else:
			DebugSet("removeIsotopes")

	def OnCheckIsotopesInMasterScan(self, evt):

		if self.checkBox_isotopesInMasterscan.GetValue():
			DebugSet("isotopesInMasterScan")
		else:
			DebugUnset("isotopesInMasterScan")

	def OnCheckMonoisotopicCorrection(self, evt):

		if self.checkBox_monoisotopicCorrection.GetValue():
			DebugSet("noMonoisotopicCorrection")
		else:
			DebugUnset("noMonoisotopicCorrection")

	def OnCheckRelativeIntensity(self, evt):

		if self.checkBox_relativeIntensity.GetValue():
			DebugSet("relativeIntensity")
		else:
			DebugUnset("relativeIntensity")

	def OnCloseWindow(self, evt):
		self.Show(False)

class SetAlignmentFrame(wx.Frame):

	def __init__(self, *args, **kwds):

		# begin wxGlade: LpdxFrame.__init__
		kwds["style"] = wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.SYSTEM_MENU | wx.CAPTION \
		| wx.CLOSE_BOX | wx.CLIP_CHILDREN | wx.RESIZE_BORDER

		wx.Frame.__init__(self, *args, **kwds)
		#panel = wx.Panel(self, -1)

		self.parent = args[0]

		################################################
		### generate the window with the set options ###

		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.alignmentMethodsMS = ['linear (standard)', 'heuristic hierarchical (experimentell)']#, 'hierarchical (experimentell)']
		self.alignmentMethodsMSMS = ['linear (standard)', 'heuristic hierarchical (experimentell)']
		self.scanAveragingMethods = ['linear (standard)', 'heuristic hierarchical (experimentell)']

		self.alignmentMethodsMS_intern = ['linear', 'heuristic']#, 'hierarchical']
		self.alignmentMethodsMSMS_intern = ['linear', 'heuristic']
		self.scanAveragingMethods_intern = ['linear', 'heuristic']

		### radio box for ms alignment method ###
		self.radioBox_ms_alignment = wx.RadioBox(self, -1, "MS alignment method", wx.DefaultPosition, wx.DefaultSize,
				self.alignmentMethodsMS, 1, wx.RA_SPECIFY_COLS)
		self.radioBox_ms_alignment.SetToolTip(wx.ToolTip(
			"choose the preferred alignment method"))
		self.radioBox_ms_alignment.SetSelection(0)
		self.radioBox_ms_alignment.Hide()


		### radio box for ms/ms alignment method ###
		self.radioBox_msms_alignment = wx.RadioBox(self, -1, "MS/MS alignment method", wx.DefaultPosition, wx.DefaultSize,
				self.alignmentMethodsMSMS, 1, wx.RA_SPECIFY_COLS)
		self.radioBox_ms_alignment.SetToolTip(wx.ToolTip(
			"choose the preferred alignment method"))
		self.radioBox_msms_alignment.SetSelection(0)
		self.radioBox_msms_alignment.Hide()


		### radio box for scan averaging method ###
		self.radioBox_scanAveraging = wx.RadioBox(self, -1, "Scan averaging method", wx.DefaultPosition, wx.DefaultSize,
				self.scanAveragingMethods, 1, wx.RA_SPECIFY_COLS)
		self.radioBox_scanAveraging.SetToolTip(wx.ToolTip(
			"choose the preferred scan averaging method"))
		self.radioBox_scanAveraging.SetSelection(0)
		self.radioBox_scanAveraging.Hide()

		self.sizer_h = wx.BoxSizer(wx.HORIZONTAL)
		self.sizer_v = wx.BoxSizer(wx.VERTICAL)

		self.sizer_v.Add(self.radioBox_ms_alignment, 0, wx.LEFT|wx.TOP, 20)
		self.sizer_v.Add(self.radioBox_msms_alignment, 0, wx.LEFT|wx.TOP, 20)

		self.sizer_h.Add(self.radioBox_scanAveraging, 0, wx.LEFT|wx.TOP, 20)
		self.sizer_h.Add(self.sizer_v)
		self.sizer.Add(self.sizer_h)
		self.SetSizer(self.sizer)

		self.SetMinSize((485,230))
		self.SetSize((485,230))
		self.Layout()

		### generate the window with the set options ###
		################################################


		self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
		#self.Bind(wx.EVT_RADIOBOX, self.OnEvtRadioBoxMS, self.radioBox_ms_alignment)
		#self.Bind(wx.EVT_RADIOBOX, self.OnEvtRadioBoxMSMS, self.radioBox_msms_alignment)
		#self.Bind(wx.EVT_RADIOBOX, self.OnEvtRadioBoxScanAvg, self.radioBox_scanAveraging)

	#def OnEvtRadioBoxMS(self, evt):
	#	self.parent.lpdxOptions['alignmentMethodMS'] = self.alignmentMethodsMS_intern[evt.GetInt()]

	#def OnEvtRadioBoxMSMS(self, evt):
	#	self.parent.lpdxOptions['alignmentMethodMSMS'] = self.alignmentMethodsMSMS_intern[evt.GetInt()]

	#def OnEvtRadioBoxScanAvg(self, evt):
	#	self.parent.lpdxOptions['scanAveragingMethod'] = self.alignmentMethodsMSMS_intern[evt.GetInt()]

	def OnCloseWindow(self, evt):
		self.Show(False)

class SetOutputOptionFrame(wx.Frame):

	def __init__(self, *args, **kwds):

		# begin wxGlade: LpdxFrame.__init__
		kwds["style"] = wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.SYSTEM_MENU | wx.CAPTION \
		| wx.CLOSE_BOX | wx.CLIP_CHILDREN | wx.RESIZE_BORDER

		wx.Frame.__init__(self, *args, **kwds)
		#panel = wx.Panel(self, -1)

		self.parent = args[0]

		################################################
		### generate the window with the set options ###

		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.sizer_v_correctIntensities = wx.BoxSizer(wx.HORIZONTAL)

		### check box for correction of intensities ###
		self.checkBox_correctIntensities = wx.CheckBox(self, -1, "correct intensities: ")

		self.label_precursor = wx.StaticText(self, -1, "precursor prefix")
		self.text_ctrl_precursor = wx.TextCtrl(self, -1, "", style = wx.TE_PROCESS_ENTER)
		self.label_fragment = wx.StaticText(self, -1, "fragment prefix")
		self.text_ctrl_fragment = wx.TextCtrl(self, -1, "", style = wx.TE_PROCESS_ENTER)

		self.sizer_v_correctIntensities.Add(self.checkBox_correctIntensities, 0, wx.LEFT|wx.CENTER, 20)
		self.sizer_v_correctIntensities.Add(self.label_precursor, 0, wx.LEFT|wx.CENTER, 5)
		self.sizer_v_correctIntensities.Add(self.text_ctrl_precursor, 0, wx.LEFT|wx.CENTER, 5)
		self.sizer_v_correctIntensities.Add(self.label_fragment, 0, wx.LEFT|wx.CENTER, 5)
		self.sizer_v_correctIntensities.Add(self.text_ctrl_fragment, 0, wx.LEFT|wx.CENTER, 5)

		### check box for sql dump of the MasterScan ###
		self.sizer_v_masterScanInSQL = wx.BoxSizer(wx.HORIZONTAL)
		self.checkBox_masterScanInSQL = wx.CheckBox(self, -1, "Dump MasterScan in SQL compatible format")
		self.sizer_v_masterScanInSQL.Add(self.checkBox_masterScanInSQL, 0, wx.LEFT|wx.CENTER, 20)

		### check box for summing the fatty acids ###
		# !Note right now the column containing the lipid species is 'NAME' and the
		# fragment columns is "FRAGINTENS:*"
		self.sizer_v_sumFattyAcids = wx.BoxSizer(wx.HORIZONTAL)
		self.checkBox_sumFattyAcids = wx.CheckBox(self, -1, "Sum up fatty acids")
		self.checkBox_sumFattyAcids.SetToolTip(wx.ToolTip(
			"!Note right now the column containing the lipid species is 'NAME' and the fragment columns is 'FRAGINTENS:*'"))
		self.sizer_v_sumFattyAcids.Add(self.checkBox_sumFattyAcids, 0, wx.LEFT|wx.CENTER, 20)

		self.sizer_v_settingsPrefix = wx.BoxSizer(wx.HORIZONTAL)
		self.checkBox_settingsPrefix = wx.CheckBox(self, -1, "Attach the settings name on the MasterScan file name")
		self.checkBox_settingsPrefix.SetToolTip(wx.ToolTip(
			"Attache the name of the setting with which the MasterScan was build " +\
			"on the file name of the MasterScan."))
		self.sizer_v_settingsPrefix.Add(self.checkBox_settingsPrefix, 0, wx.LEFT|wx.CENTER, 20)

		self.sizer.Add((10,10))
		self.sizer.Add(self.sizer_v_correctIntensities)
		self.sizer.Add((10,10))
		self.sizer.Add(self.sizer_v_masterScanInSQL)
		self.sizer.Add((10,10))
		self.sizer.Add(self.sizer_v_sumFattyAcids)
		self.sizer.Add((10,10))
		self.sizer.Add(self.sizer_v_settingsPrefix)
		#self.sizer.Add(wx.StaticLine(self, -1))
		self.SetSizer(self.sizer)

		self.SetMinSize((565,160))
		self.SetSize((565,160))
		self.Layout()

		### generate the window with the set options ###
		################################################


		self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

	def OnCloseWindow(self, evt):
		self.Show(False)

class CSVViewer(wx.Frame):
	def __init__(self, parent, ID, title, file, size=(200,200)):
		wx.Frame.__init__(self, parent, ID, title,
						  (-1,-1),size)

		self.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		self.SetSize((600, 400))
		self.Center()
		self.filename = file
		self.file = None
		self.OnOpen(None)
		self.Show(True)
		return

	def OnOpen(self, event):
		#self.filename = parent.text_ctrl_OutputSection
		self.file = file(self.filename, 'r')
		csvfile = csv.reader(self.file)

		#grab a sample and see if there is a header
		sample=self.file.read(8192)
		self.file.seek(0)
		colnames=next(csvfile)

		self.box_sizer = wx.BoxSizer(wx.VERTICAL)

		self.button_SaveAs = buttons.GenButton(self, -1, "Save as ...")
		if getattr(self, 'grid', 0): self.grid.Destroy()
		self.grid=wx.grid.Grid(self, -1)
		self.box_sizer.Add(self.grid, 1, wx.ALL|wx.EXPAND, 10)
		self.box_sizer.Add(self.button_SaveAs, 0, wx.ALL|wx.EXPAND, 10)
		self.grid.CreateGrid(0, len(colnames) * 2)
		self.grid.SetColLabelAlignment(wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)

		self.Bind(wx.EVT_BUTTON, self.OnSaveAs, self.button_SaveAs)

		#fill in headings
		for i in range(len(colnames)):
			self.grid.SetColLabelValue(i, colnames[i])

		#fill in rows
		r=0
		for row in csvfile:
			self.grid.AppendRows(1)
			for i in range(len(row)):
				try:
					self.grid.SetCellValue(r, i, row[i])
					#self.grid.SetCellAlignment(r, i, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
				except:
					self.grid.AppendCols(1, True)
			r += 1
		self.file.close()
		self.grid.AutoSizeColumns(True)
		self.Refresh(True, self.grid.GetRect())
		self.SetSizer(self.box_sizer)
		self.Layout()

	def OnSaveAs(self, evt):
		dlg = wx.FileDialog(self, "Specify an output file",
			style=wx.DD_DEFAULT_STYLE|wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
		dlg.SetWildcard("*.csv files|*.csv")

		if dlg.ShowModal() == wx.ID_OK:
			p = dlg.GetFilename()
			d = dlg.GetPath()
			#p = dlg.GetPath().split(os.sep)[-1]
			if not re.match(r'.*\.csv', p, re.IGNORECASE):
				dlgError = wx.MessageDialog(self, "The filename must have '.csv' as ending",
					"Error", wx.OK)

			with open(self.filename) as fileIn:
				with open(d, 'w') as fileOut:
					fileOut.write(fileIn.read())

	def Exit(self, event):
		if getattr(self, 'file',0):
			self.file.close()
		self.Close(True)

from threading import Thread

class RunSubp(Thread):
	def __init__ (self, stdout, debug):
		Thread.__init__(self)
		self.stdout = stdout
		self.debug = debug
		self.status = -1

	def run(self):
		while True:
			line = self.stdout.readline()
			if line:
				self.debug.write(line)
			else:
				break

class RunOptions:

	lastSelected = None
	listChoices = ['tolerance', 'min occ.']
	listChoices_types = ['ppm', 'Da']

	def __init__(self, setting = None, value = None, type = None):
		if setting:
			self.value = {setting : value}
			self.type = {setting : type}
		else:
			self.value = {}
			self.type = {}

	def has_key(self, key):
		has_key = False
		if key in self.value: has_key = True
		if key in self.type: has_key = True
		return has_key











### Ballal #####


def get_resource_dir():
    return Path(__file__).resolve().parent

def get_runtime_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


######################


class LpdxFrame(wx.Frame):
    
	project_loaded_for_batch = False
    
	def __init__(self, *args, **kwds):

		### some constants ###

		self.CONST_THREAD_SUCCESSFUL = 0
		self.CONST_THREAD_USER_ABORT = 1
  
############# Ballal #############

		###########################################################
		### some user settings which are stored in lpdxopts.ini ###

		self.resource_dir = get_resource_dir()
		self.runtime_dir = get_runtime_dir()

		self.options_file = self.resource_dir / "lpdxopts.ini"
		self.default_import_file = self.resource_dir / "lpdxImportSettings_benchmark.ini"

		self.lpdxOptions = staticTypeDict()

		# set the default defaults. Those values are used if no lpdxopts.ini
		# was present
		self.lpdxOptions['defaultImportSettings'] = (str(self.default_import_file), type(''))

		self.confParseOpts = configparser.ConfigParser()
		self.confParseOpts.read(str(self.options_file))

		self.settingDefaults = "DEFAULTS"
		if not self.confParseOpts.has_section(self.settingDefaults):
			self.confParseOpts.add_section(self.settingDefaults)
			with open(str(self.options_file), 'w') as iniFile:
				self.confParseOpts.write(iniFile)

		for option in list(self.lpdxOptions.keys()):
			if self.confParseOpts.has_option(self.settingDefaults, option):
				o = self.confParseOpts.get(self.settingDefaults, option)
				if o not in ['True', 'False']:
					self.lpdxOptions[option] = o
				else:
					self.lpdxOptions[option] = (o == 'True')
			else:
				self.confParseOpts.set(self.settingDefaults, option, str(self.lpdxOptions[option]))

		# 'defaultImportSettings' is a file path persisted in lpdxopts.ini from a
		# PREVIOUS run. If that path no longer exists -- e.g. the project
		# directory was moved or renamed since it was last saved -- silently
		# trusting it leaves the settings dropdown empty with no explanation
		# (configparser.read() fails silently on a missing file). Fall back to
		# the freshly-computed, always-correct default in that case.
		if not Path(str(self.lpdxOptions['defaultImportSettings'])).exists():
			print("WARNING: persisted defaultImportSettings path not found on disk (%s); "
				"falling back to computed default (%s)" % (
					self.lpdxOptions['defaultImportSettings'], self.default_import_file))
			self.lpdxOptions['defaultImportSettings'] = str(self.default_import_file)

		with open(str(self.options_file), 'w') as iniFile:
			self.confParseOpts.write(iniFile)
   

		print("options_file:", self.options_file, self.options_file.exists())
		print("default_import_file:", self.default_import_file, self.default_import_file.exists())


		### some user settings which are stored in lpdxopts.ini ###
		###########################################################

		# version
		self.version = kwds['version']

		# lx or lo?
		self.lipidxplorer = kwds['lipidxplorer']

		# allow import of raw files?
		self.rawimport = kwds['rawimport']

		#self.supportedFileTypes = ['mzML', 'dta/csv', 'csv']
		self.supportedFileTypes = ['mzML', 'dta/csv']
		self.defaultFileType = 'mzML'
		self.rawToolTip = ""

		if "optimized" in kwds and kwds['optimized']:
			self.optimized = True
		else:
			self.optimized = False

		# remove this key, because otherwise Frame.__init__() gives TypeError
		try:
			del kwds['rawimport']
			del kwds['lipidxplorer']
			del kwds['version']
			del kwds['optimized']
		except KeyError:
			pass

		# the project file
		self.projectFile = ''

		###########################################
		### variables for the different modules ###

		# begin with some variables
		self.dictMFQLScripts = odict()
		self.filePath_AddMFQL = []
		self.importedFlag = False
		self.debugOpen = False
		self.isRunning = False

		# variables for the Import panel
		#self.settingSelectionIndex = None
		self.currentConfiguration = ""
		self.isChangedAndNotSavedCurrentConfiguration = False
		self.listConfigurations = []
		self.filePath_LoadIni = ""
		self.filePath_LoadIni_batch = ""
		self.filePath_ImportData = ""
		self.filePath_MasterScan = ""
		self.filePath_Wiff = ""
		self.filePath_Raw = ""

		# variables for the Run panel
		self.counterNotebookPages = 0
		self.dictNotebookPages = {}
		self.confParse = None
		self.filePath_ComplementSC = ""
		self.filePath_Dump = ""
		self.listChoices = RunOptions.listChoices#['tolerance', 'min occ.']
		self.listChoices_types = RunOptions.listChoices_types#['ppm', 'Da']

		# variables for the editor pane
		#self.list_index = 0
		self.dict_notebook_editor = {}
		self.dict_text_ctrl = {}
		self.dict_button_close = {}
		self.dict_button_save = {}
		self.dict_button_saveAs = {}
		self.dict_button_new = {}
		self.dict_box_sizer_vertical = {}
		self.dict_box_sizer_horizontal = {}
		self.dict_flex_sizer = {}
		self.dict_mfqlFile = {}
		self.dict_isChangedAndNotSavedMfqlFile = {}
  
  ######### ballal ###########
		self.disabled_pages = set()  # to store page names that are disabled
  ##########################

		### variables for the different modules ###
		###########################################


		############################
		### Initialize the Frame ###

		# begin wxGlade: LpdxFrame.__init__
		#kwds["style"] = wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.SYSTEM_MENU | wx.CAPTION \
		#| wx.CLOSE_BOX | wx.CLIP_CHILDREN | wx.RESIZE_BORDER
		kwds["style"] = wx.MINIMIZE_BOX | wx.SYSTEM_MENU | wx.CAPTION \
		| wx.CLOSE_BOX | wx.CLIP_CHILDREN | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX

		wx.Frame.__init__(self, *args, **kwds)

		
		# reduce flicker on Windows/X11
		self.SetDoubleBuffered(True)
# set some font things
		self.font = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)#, 0, 0, wx.FONTENCODING_SYSTEM))
		self.SetFont(self.font)

		
		# unified header font (subtle, not screaming colors)
		self.header_font = wx.Font(self.font.GetPointSize()+2, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
# font for the units
		self.font_units_size = 10

		# create the landing and content panels
		self.start_panel = wx.Panel(self, -1)
		self.placeholder_panel = wx.Panel(self, -1)

		# create the notebook panels
		self.notebook_1 = wx.Notebook(self, -1, style=0)
		self.notebook_1_pane_2 = wx.Panel(self.notebook_1, -1)
		self.notebook_1_pane_3 = wx.Panel(self.notebook_1, -1)
		self.notebook_1_pane_4 = wx.Panel(self.notebook_1, -1)
		self.notebook_1_pane_5 = wx.Panel(self.notebook_1, -1)

		self.button_open_next = wx.Button(self.start_panel, -1, "LipidXplorerNext")
		self.button_open_legacy = wx.Button(self.start_panel, -1, "LipidXplorer 1.5")
		self.button_back_from_placeholder = wx.Button(self.placeholder_panel, -1, "Back", size=(48, 20))
		self.button_back_to_start = wx.Button(self.notebook_1_pane_2, -1, "Back", size=(48, 20))

		try:
			logo_path = resource_path("lx", "stuff", "LipidXplorer-50.png")
			img = wx.Image(logo_path, wx.BITMAP_TYPE_PNG)
			w = img.GetWidth()
			h = img.GetHeight()
			scale_factor = 0.7 # 50% size
			img = img.Scale(int(w * scale_factor), int(h * scale_factor), wx.IMAGE_QUALITY_HIGH)
			self.bmp_LipidX_Logo = img.ConvertToBitmap()
			self.start_logo = wx.StaticBitmap(self.start_panel, -1, self.bmp_LipidX_Logo)
		except Exception as e:
			print("Logo load failed:", e)
			self.logo_bitmap = None
   
		
		self.label_placeholder_title = wx.StaticText(self.placeholder_panel, -1, "LipidXplorerNext")
		self.label_placeholder_message = wx.StaticText(self.placeholder_panel,-1,
		"LipidXplorerNext modernizes LipidXplorer with a new data architecture and design.\n"
		"Its central goal is to integrate and utilize multidimensional data — \n"
		"retention time, m/z and CCS/ion mobility — to better identify and quantify lipids.", style=wx.ALIGN_CENTER)
  
		self.label_placeholder_demo = wx.StaticText(
			self.placeholder_panel,
			-1,
			"")
		self.link_placeholder_demo = wx.adv.HyperlinkCtrl(
			self.placeholder_panel,
			-1,
			"LipidXplorerNext Wiki",
			"https://lifs-tools.org/wiki/index.php?title=LipidXplorerNext"
		)


		self.SetBackgroundColour(wx.Colour(245, 247, 250))
		self.start_panel.SetBackgroundColour(wx.Colour(245, 247, 250))
		self.placeholder_panel.SetBackgroundColour(wx.Colour(245, 247, 250))

		#self.notebook_1_pane_2.SetFont(self.font)
		#self.notebook_1_pane_3.SetFont(self.font)
		#self.notebook_1_pane_4.SetFont(self.font)
		#self.notebook_1_pane_5.SetFont(self.font)






		### Initialize the Frame ###
		############################


		################
		### Menu Bar ###

		self.menubar = wx.MenuBar()
  
		self.menu_project = wx.Menu()
		self.menu_project.Append(wx.MenuItem(self.menu_project, 1, "Load project"))
		self.menu_project.Append(wx.MenuItem(self.menu_project, 2, "Save project"))
		self.menu_project.Append(wx.MenuItem(self.menu_project, 3, "Save project as ..."))
  
		self.menu_debug = wx.Menu()
		self.menu_debug.Append(wx.MenuItem(self.menu_debug, 4, "Debug window"))
		self.menu_debug.Append(wx.MenuItem(self.menu_debug, 5, "Set debug levels"))
		self.menu_options = wx.Menu()
		# disabling alignment method dialog
		# self.menu_options.Append(wx.MenuItem(self.menu_options, 6, "Set alignment method"))
		self.menu_options.Append(wx.MenuItem(self.menu_options, 7, "Output options"))
		self.menu_help = wx.Menu()
		self.menu_help.Append(wx.MenuItem(self.menu_help, 8, "LipidXplorer Documentation"))
		self.menu_help.Append(wx.MenuItem(self.menu_help, 9, "MFQL tutorial"))
		self.menu_help.Append(wx.MenuItem(self.menu_help, 10, "MFQL reference"))
		self.menu_help.AppendSeparator()
		self.menu_help.Append(wx.MenuItem(self.menu_help, 11, "Help with 'Import Settings'"))
		self.menu_help.Append(wx.MenuItem(self.menu_help, 12, "Help with 'Run'"))
		self.menu_help.Append(wx.MenuItem(self.menu_help, 13, "Help with 'MS Tools'"))
		self.menu_help.AppendSeparator()
		self.menu_help.Append(wx.MenuItem(self.menu_help, 14, "About LipidXplorer"))
		self.menu_about = wx.Menu()
  
		self.menubar.Append(self.menu_project, "&Project")
		self.menubar.Append(self.menu_debug, "&Debug")
		self.menubar.Append(self.menu_options, "&Options")
		self.menubar.Append(self.menu_help, "&Help")
		self.SetMenuBar(self.menubar)

		### Menu Bar ###
		################

		if balloontip:
			tipballoon_color = None
			tipballoon_messagefonts = None
			tipballoon_windowsshape = BT.BT_ROUNDED
			tipballoon_tipstyle = BT.BT_BUTTON
			tipballoon_startDelay = 300
			tipballoon_endDelay = 1000

			tipballoon_args = {
					'topicon' : None,
					'toptitle' : None,
					'message' : None,
					'shape' : tipballoon_windowsshape,
					'tipstyle' : tipballoon_tipstyle}




		##############################
		### MS tools notebook pane ###

		# Mass vs. Sum Composition (header)
		self.label_mstools_InputSection = wx.StaticText(self.notebook_1_pane_4, -1, "Mass vs. Sum Composition")
		self.label_mstools_InputSection.SetFont(self.header_font) 
  		##wx.Font(self.font_units_size, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		self.label_mstools_InputSection_mz = wx.StaticText(self.notebook_1_pane_4, -1, "m/z value")
		self.label_mstools_InputSection_sumComposition = wx.StaticText(self.notebook_1_pane_4, -1, "sc-constraint or sum composition")
		self.label_mstools_InputSection_doubleBond_1 = wx.StaticText(self.notebook_1_pane_4, -1, "lDB")
		self.label_mstools_InputSection_doubleBond_2 = wx.StaticText(self.notebook_1_pane_4, -1, "hDB")
		self.label_mstools_InputSection_charge = wx.StaticText(self.notebook_1_pane_4, -1, "chg")
		self.label_mstools_InputSection_accuracy = wx.StaticText(self.notebook_1_pane_4, -1, "acc")
		self.label_mstools_InputSection_accuracy_blank = wx.StaticText(self.notebook_1_pane_4, -1, "  ")
		self.label_mstools_InputSection_accuracy_ppm = wx.StaticText(self.notebook_1_pane_4, -1, "ppm")
		self.text_ctrl_mstools_InputSection_mz = wx.TextCtrl(self.notebook_1_pane_4, -1, "", style = wx.TE_PROCESS_ENTER)
		self.text_ctrl_mstools_InputSection_mz.SetToolTip(wx.ToolTip(
			"Input a m/z value in Da."))
		self.text_ctrl_mstools_InputSection_sumComposition = wx.TextCtrl(self.notebook_1_pane_4, -1, "", style = wx.TE_PROCESS_ENTER)
		self.text_ctrl_mstools_InputSection_sumComposition.SetToolTip(wx.ToolTip(
			"A sum composition could be for example: C39 H78 N O8 P. An sc-constrain could be for example: C[20..50] " + \
				"H[40..100] O[0..8] N[1] P[1] chg(+1)"))
		self.text_ctrl_mstools_InputSection_doubleBond_1 = wx.TextCtrl(self.notebook_1_pane_4, -1, "", style = wx.TE_PROCESS_ENTER)
		self.text_ctrl_mstools_InputSection_doubleBond_1.SetToolTip(wx.ToolTip(
			"The lower border of double bond equivalent."))
		self.text_ctrl_mstools_InputSection_doubleBond_2 = wx.TextCtrl(self.notebook_1_pane_4, -1, "", style = wx.TE_PROCESS_ENTER)
		self.text_ctrl_mstools_InputSection_doubleBond_2.SetToolTip(wx.ToolTip(
			"The higher border of double bond equivalent."))
		self.text_ctrl_mstools_InputSection_charge = wx.TextCtrl(self.notebook_1_pane_4, -1, "", style = wx.TE_PROCESS_ENTER)
		self.text_ctrl_mstools_InputSection_charge.SetToolTip(wx.ToolTip(
			"The charge, if it is an ion. Charge will be 0 otherwise."))
		self.text_ctrl_mstools_InputSection_accuracy = wx.TextCtrl(self.notebook_1_pane_4, -1, "5", style = wx.TE_PROCESS_ENTER)
		self.text_ctrl_mstools_InputSection_accuracy.SetToolTip(wx.ToolTip(
			"The accuracy of the m/z-to-sum-composition function"))
		self.button_massToSumComposition = wx.Button(self.notebook_1_pane_4, -1, "Mass-to-sum-composition")
		self.button_massToSumComposition.SetToolTip(wx.ToolTip(
			"Calculate possible sum compositions for the given m/z with the given accuracy. Do not forget to give the charge"))
		self.button_sumCompositionToMass = wx.Button(self.notebook_1_pane_4, -1, "Sum-composition-to-m/z")
		self.button_sumCompositionToMass.SetToolTip(wx.ToolTip(
			"Calculate the m/z of the given sum composition. Do not forget to give the charge."))
		self.text_ctrl_mstools_OutputSection = wx.TextCtrl(self.notebook_1_pane_4, -1, "", style = wx.TE_MULTILINE|wx.TE_READONLY)

		# second half
		# Isotopes of molecules (header)
		self.label_mstools_Isotopes = wx.StaticText(self.notebook_1_pane_4, -1, "Isotopes of molecules")
		self.label_mstools_Isotopes.SetFont(self.header_font)
			##wx.Font(self.font_units_size, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		self.label_mstools_Isotopes_precursor = wx.StaticText(self.notebook_1_pane_4, -1, "Ion sum composition                  ")
		self.label_mstools_Isotopes_fragment = wx.StaticText(self.notebook_1_pane_4, -1, "Fragment sum composition                  ")
		self.text_ctrl_mstools_Isotopes_precursor = wx.TextCtrl(self.notebook_1_pane_4, -1, "", style = wx.TE_PROCESS_ENTER)
		self.text_ctrl_mstools_Isotopes_precursor.SetToolTip(wx.ToolTip(
			"input sum composition of precursor ion"))
		self.text_ctrl_mstools_Isotopes_fragment= wx.TextCtrl(self.notebook_1_pane_4, -1, "", style = wx.TE_PROCESS_ENTER)
		self.text_ctrl_mstools_Isotopes_fragment.SetToolTip(wx.ToolTip(
			"input sum composition of fragment ion"))
		self.button_Isotopes = wx.Button(self.notebook_1_pane_4, -1, "Get Isotopic distribution")
		self.button_massToSumComposition.SetToolTip(wx.ToolTip(
			"Calculate the Isotopic distribution of the given sum composition"))
		self.checkBox_mstools_Isotopes_nl = wx.CheckBox(self.notebook_1_pane_4, -1, "Neutral Loss")
		self.label_mstools_Isotopes_blank = wx.StaticText(self.notebook_1_pane_4, -1, "            ")
		self.text_ctrl_mstools_Isotopes_output = wx.TextCtrl(self.notebook_1_pane_4, -1, "", style = wx.TE_MULTILINE|wx.TE_READONLY)

		### MS tools notebook pane ###
		##############################








		############################
		### IMPORT notebook pane ###
###################### Ballal ######################


		# --- Folder with data files ---
		# Select the folder containing the mass spectra (header)
		self.label_ImportDataSection = wx.StaticText(self.notebook_1_pane_2, -1, "Select the folder containing the mass spectra")
		self.label_ImportDataSection.SetFont(self.header_font)

		self.text_ctrl_ImportDataSection = wx.TextCtrl(self.notebook_1_pane_2, -1, "", style=wx.TE_PROCESS_ENTER)
		self.text_ctrl_ImportDataSection.SetToolTip(wx.ToolTip(
			"Select a folder with mass spec data of the type which can be selected on the right. After input"
			" all other text fields will be filled automatically. \n  The data will be imported into LipidXplorer's own"
			" database called MasterScan."))

		self.button_Browse_ImportDataSection = wx.Button(self.notebook_1_pane_2, -1, "Browse")
		self.button_Browse_ImportDataSection.SetToolTip(wx.ToolTip(
			"Opens a dialog for selection the import data folder. All following text fields will be filled automatically."))

		self.combo_ctrl_ImportDataSection = wx.ComboBox(
			self.notebook_1_pane_2, -1,
			self.defaultFileType,
			(100, 100),
			(90, -1),
			self.supportedFileTypes,
			wx.CB_DROPDOWN
		)

		self.combo_ctrl_ImportDataSection.SetToolTip(wx.ToolTip(
		"""Choose the type of the mass spec data:
		mzML - XML file format
		dta/csv - text file format
		csv - single CSV with MS1/MS2 separated by QuadMass
		%s
		""" % self.rawToolTip))


		# --- Output MasterScan file ---
		self.label_OutputMasterScanSection = wx.StaticText(self.notebook_1_pane_2, -1, "Specify output MasterScan file")
		self.text_ctrl_OutputMasterScanSection = wx.TextCtrl(self.notebook_1_pane_2, -1, "")
		self.text_ctrl_OutputMasterScanSection.SetToolTip(wx.ToolTip(
			"Specify the path and the name of the MasterScan database for the mass spec data selected above."))
		self.button_Browse_OutputMasterScanSection = wx.Button(self.notebook_1_pane_2, -1, "Browse")
		self.button_Browse_OutputMasterScanSection.SetToolTip(wx.ToolTip(
			"Opens a dialog box for selection of the MasterScan database."))

		# --- Batch Mode Checkbox ---

		# Label
		self.label_occupational_threshold = wx.StaticText(
			self.notebook_1_pane_2,
			-1,
			"Occurrence Threshold:"
		)

		# Editable numeric control (0.00 – 1.00)
		self.spin_occupational_threshold = wx.SpinCtrlDouble(
			self.notebook_1_pane_2,
			-1,
			min=0.0,
			max=1.0,
			initial=0.25,
			inc=0.05
		)

		self.spin_occupational_threshold.SetDigits(2)  # show 2 decimal places

		# Tooltip
		self.spin_occupational_threshold.SetToolTip(
			"Minimum fraction of samples that must have Intensity > 0\n"
			"for a lipid to be retained.\n"
			"Example: 0.25 = at least 25% of samples."
		)
  
		self.label_occupational_threshold.Hide()  # hide the label for occupational threshold
		self.spin_occupational_threshold.Hide()  # hide the spin control for occupational threshold
		self.checkBox_BatchMode = wx.CheckBox(self.notebook_1_pane_2, -1, "Batch Mode")

		# --- Batch Panel (initially hidden) ---
		self.batchPanel = wx.Panel(self.notebook_1_pane_2)
		self.batchPanel.Hide()
  
  
		# --- Batch Panel controls ---
		self.label_cfg = wx.StaticText(self.batchPanel, -1, "Select a Configuration")
		self.label_cfg.SetFont(self.header_font)

		try:
			listConfigurations_batch = sorted(self.confParse.sections())
		except Exception:
			listConfigurations_batch = []

		self.choice_SelectSettingSection_batch = wx.Choice(
			self.batchPanel,
			-1,
			choices=listConfigurations_batch
		)

		self.label_mfql = wx.StaticText(self.batchPanel, -1, "MFQL directories (multiple allowed)")
		# self.listbox_MFQL_batch = wx.TextCtrl(self.batchPanel,style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP,
		# size=(-1, 120) )  # ← height in pixels)
		# self.button_Browse_MFQL = wx.Button(self.batchPanel, -1, "Browse")
		self.listbox_MFQL_batch = wx.ListBox(self.batchPanel, style=wx.LB_EXTENDED)  # multi-select
		self.button_Browse_MFQL_batch = wx.Button(self.batchPanel, -1, "Browse")
		self.button_Delete_MFQL_batch = wx.Button(self.batchPanel, -1, "Delete")
		self.button_Browse_MFQL_batch.SetToolTip(wx.ToolTip(
			"Opens a dialog box for selection of the folders containing the MFQL scripts."))

		# --- RUN button and checkbox side-by-side ---
		hbox_run = wx.BoxSizer(wx.HORIZONTAL)

		cpu_total = mp.cpu_count()
		max_workers = max(1, cpu_total)  

		self.label_cores = wx.StaticText(
			self.batchPanel,
			-1,
			"Number of CPU cores to use:"
		)

		self.spin_cores = wx.SpinCtrl(
			self.batchPanel,
			-1,
			min=1,
			max=max_workers,
			initial= cpu_total // 2
		)

		self.spin_cores.SetToolTip(
			wx.ToolTip(f"Detected cores: {cpu_total}")
		)
		
  
		# RUN button
		self.button_RUN_batch = wx.Button(self.batchPanel, -1, "RUN")

		# Checkbox: "Save per sample result"
		self.checkbox_save_per_sample = wx.CheckBox(self.batchPanel, -1, "Save per sample result")
		self.checkbox_save_per_sample.SetToolTip(
			wx.ToolTip(
				"If enabled, a separate result CSV file will be saved\n"
				"for each individual sample in addition to the merged batch file."
			)
		)
		
		self.checkbox_save_per_sample.SetValue(False)  # unchecked by default

		# Checkbox: "Verbose worker log"
		self.checkbox_verbose_log = wx.CheckBox(self.batchPanel, -1, "Verbose worker log")
		self.checkbox_verbose_log.SetToolTip(
			wx.ToolTip(
				"If enabled, batch_log.txt also records everything the import\n"
				"and MFQL code prints, not just each worker's progress and\n"
				"errors. Useful for diagnosis, but it is roughly 100x more\n"
				"output and noticeably slows a run down."
			)
		)
		self.checkbox_verbose_log.SetValue(False)  # unchecked by default




		# --- Checkbox toggle logic ---
		def on_checkbox_toggle(event):
      
			is_batch_checked = self.checkBox_BatchMode.IsChecked()
			self.notebook_1_pane_2.Freeze()
			if is_batch_checked:
				self.batchPanel.Show()
				self.label_occupational_threshold.Show()
				self.spin_occupational_threshold.Show()
				self.text_ctrl_ImportDataSection.Clear()
				self.label_OutputMasterScanSection.SetLabel("Select *.ini settings file")
				self.text_ctrl_OutputMasterScanSection.Clear()
				self.text_ctrl_OutputMasterScanSection.SetToolTip(wx.ToolTip(
				"Specify the path of *.ini settings file"))
				self.button_Browse_OutputMasterScanSection.SetToolTip(wx.ToolTip(
							"Opens a dialog box for selection of the Import Settings."))
				self.choice_SelectSettingSection_batch.Clear()
				self.listbox_MFQL_batch.Clear()
				self.disabled_pages.update({"Import Settings", "Run"})
				print("Import Settings and Run pages disabled.")
				
			else:
				self.batchPanel.Hide()
				self.label_occupational_threshold.Hide()
				self.spin_occupational_threshold.Hide()
				self.text_ctrl_ImportDataSection.Clear()
				self.label_OutputMasterScanSection.SetLabel("Specify output MasterScan file")
				self.text_ctrl_OutputMasterScanSection.Clear()
				self.text_ctrl_OutputMasterScanSection.SetToolTip(wx.ToolTip(
				"Specify the path and the name of the MasterScan database for the mass spec data selected above."))
				self.button_Browse_OutputMasterScanSection.SetToolTip(wx.ToolTip(
							"Opens a dialog box for selection of the MasterScan database."))
				self.choice_SelectSettingSection_batch.Clear()
				self.disabled_pages.clear()
				print("Import Settings and Run pages enabled.")

			self.notebook_1_pane_2.Layout()
			self.notebook_1_pane_2.SendSizeEvent()
			self.notebook_1_pane_2.Thaw()


		self.checkBox_BatchMode.Bind(wx.EVT_CHECKBOX, on_checkbox_toggle)
		self.choice_SelectSettingSection_batch.Bind(
			wx.EVT_CHOICE,
			self.OnConfigurationChoice_batch
		)
		self.notebook_1.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGING, self.on_notebook_page_changing)



		# --- Logo ---
		try:
			logo_path = resource_path("lx", "stuff", "LipidXplorer-50.png")
			img = wx.Image(logo_path, wx.BITMAP_TYPE_PNG)
			w = img.GetWidth()
			h = img.GetHeight()
			scale_factor = 0.5 
			img = img.Scale(int(w * scale_factor), int(h * scale_factor), wx.IMAGE_QUALITY_HIGH)
			self.bmp_LipidX_Logo = img.ConvertToBitmap()
			self.logo_bitmap = wx.StaticBitmap(self.notebook_1_pane_2, -1, self.bmp_LipidX_Logo)
		except Exception as e:
			print("Logo load failed:", e)
			self.logo_bitmap = None

		# =========================================================
		#  SIZER-BASED LAYOUT
		# =========================================================
		main_vbox = wx.BoxSizer(wx.VERTICAL)
		main_vbox.AddSpacer(50)

# === Top Row: Spacer + Batch Mode checkbox aligned right
		top_row = wx.BoxSizer(wx.HORIZONTAL)
		top_row.AddSpacer(80) # left spacer to simulate margin
		top_row.AddStretchSpacer(1)
		# Add to row
		top_row.Add(self.label_occupational_threshold, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
		top_row.Add(self.spin_occupational_threshold, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 20)
		top_row.Add(self.checkBox_BatchMode, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

		main_vbox.Add(top_row, 0, wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, 5)



		# === Label: Select folder
		main_vbox.Add(self.label_ImportDataSection, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

		# === Row: [ TextCtrl ][ Browse ][ ComboBox ]
		folder_row = wx.BoxSizer(wx.HORIZONTAL)
		folder_row.Add(self.text_ctrl_ImportDataSection, 1, wx.EXPAND | wx.RIGHT, 5)
		folder_row.Add(self.button_Browse_ImportDataSection, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
		folder_row.Add(self.combo_ctrl_ImportDataSection, 0, wx.ALIGN_CENTER_VERTICAL)
		main_vbox.Add(folder_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

		# === Label: Output
		main_vbox.Add(self.label_OutputMasterScanSection, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

		# === Row: [ Output TextCtrl ][ Browse ]
		output_row = wx.BoxSizer(wx.HORIZONTAL)
		output_row.Add(self.text_ctrl_OutputMasterScanSection, 1, wx.EXPAND | wx.RIGHT, 5)
		output_row.Add(self.button_Browse_OutputMasterScanSection, 0, wx.ALIGN_CENTER_VERTICAL)
		main_vbox.Add(output_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)

		# === Batch Panel Section ===
		# Create clean layout using same spacing and alignment

		batch_vbox = wx.BoxSizer(wx.VERTICAL)

		# Config Label + Dropdown
		batch_vbox.Add(self.label_cfg, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
		batch_vbox.Add(self.choice_SelectSettingSection_batch, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

		# MFQL Label
		batch_vbox.Add(self.label_mfql, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

		# MFQL Row: [ TextCtrl ][ Browse ]
		mfql_row = wx.BoxSizer(wx.HORIZONTAL)
		mfql_row.Add(self.listbox_MFQL_batch , 1, wx.EXPAND | wx.RIGHT, 5)
		#mfql_row.Add(self.button_Browse_MFQL, 0, wx.ALIGN_CENTER_VERTICAL)
  
		btn_col = wx.BoxSizer(wx.VERTICAL)
		btn_col.Add(self.button_Browse_MFQL_batch, 0, wx.EXPAND | wx.BOTTOM, 5)
		btn_col.Add(self.button_Delete_MFQL_batch, 0, wx.EXPAND)
		mfql_row.Add(btn_col, 0, wx.ALIGN_TOP)

		batch_vbox.Add(mfql_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)
		#set initial/min height
		self.listbox_MFQL_batch.SetMinSize((-1, 120))

		# Add button and checkbox to the horizontal sizer
		# CPU cores (left side)
		# Left side controls
		hbox_run.Add(self.label_cores, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
		hbox_run.Add(self.spin_cores, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 25)

		hbox_run.AddSpacer(40)  # small push to the right

		# RUN button (center anchor)
		hbox_run.Add(self.button_RUN_batch, 0)

		# Stretch spacer after RUN
		hbox_run.AddSpacer(40)  # small push to the right

		# Right side checkbox
		hbox_run.Add(self.checkbox_save_per_sample, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 20)
		hbox_run.Add(self.checkbox_verbose_log, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 20)

		# IMPORTANT: let row expand horizontally
		batch_vbox.Add(hbox_run, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 10)
  

		self.batchPanel.SetSizer(batch_vbox)
		main_vbox.Add(self.batchPanel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)



		# Push logo to bottom
		main_vbox.AddStretchSpacer(1)

		# Logo centered
		if self.logo_bitmap:
			main_vbox.Add(self.logo_bitmap, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 20)

		import_bottom_row = wx.BoxSizer(wx.HORIZONTAL)
		import_bottom_row.Add(self.button_back_to_start, 0, wx.LEFT | wx.TOP, 0)
		import_bottom_row.AddStretchSpacer(1)
		#main_vbox.Add(import_bottom_row, 0, wx.EXPAND | wx.BOTTOM, 0)

		# Set a fixed content width
		main_vbox.SetMinSize((700, -1))  # <-- pick  width here

		center_wrap = wx.BoxSizer(wx.HORIZONTAL)
		center_wrap.AddStretchSpacer(1)
		center_wrap.Add(main_vbox, 0, wx.EXPAND)
		center_wrap.AddStretchSpacer(1)

		import_bottom_row = wx.BoxSizer(wx.HORIZONTAL)
		import_bottom_row.Add(self.button_back_to_start, 0, wx.LEFT | wx.TOP, 8)
		import_bottom_row.AddStretchSpacer(1)

		outer = wx.BoxSizer(wx.VERTICAL)
		outer.Add(center_wrap, 1, wx.EXPAND)
		outer.Add(import_bottom_row, 0, wx.EXPAND | wx.BOTTOM, 0)

		self.notebook_1_pane_2.SetSizer(outer)
		self.notebook_1_pane_2.Layout()

########################



		# set settings

		# start Import button
		self.button_StartImport = wx.Button(self.notebook_1_pane_5, -1, "Start import")
		self.button_StartImport.SetToolTip(wx.ToolTip(
			"Starts the import procedure with the selected settings."))
		#self.button_StartImport.SetBackgroundColour(wx.Colour(140, 250, 140))
### IMPORT notebook pane ###
		############################


		#####################################
		### IMPORT SETTINGS notebook pane ###

		button1_w = 180
		button1_h = 28
		button1_small_w = button1_w / 2 - 5
		button1_small_h = 28


		# ini file
		self.label_LoadIniSection = wx.StaticText(self.notebook_1_pane_5, -1, "Select *.ini settings file")
		self.text_ctrl_LoadIniSection = wx.TextCtrl(self.notebook_1_pane_5, -1, "")
		self.text_ctrl_LoadIniSection.SetToolTip(wx.ToolTip(
			"The import settings are stored in a special file which can be changed to your own file here."))

		self.text_ctrl_LoadIniSection.SetValue(self.lpdxOptions['defaultImportSettings'])

		# line separating settings load and change settings
		self.static_line_LoadIniSection = wx.StaticLine(self.notebook_1_pane_5, -1, (-1, -1), (650, 4), wx.LI_HORIZONTAL, "")

		# set initially *.ini file
		self.filePath_LoadIni = self.text_ctrl_LoadIniSection.GetValue()
		self.text_ctrl_LoadIniSection.SetValue(self.filePath_LoadIni)
		self.confParse = configparser.ConfigParser()
		_iniReadResult = self.confParse.read(self.text_ctrl_LoadIniSection.GetLineText(0))

		# configparser.read() fails SILENTLY (no exception, just an empty
		# result) if the file doesn't exist or can't be parsed -- warn
		# explicitly instead of leaving the configuration dropdown empty
		# with no indication of why
		if not _iniReadResult:
			wx.MessageBox(
				"Could not load the default import settings file:\n\n%s\n\n"
				"The file was not found, or could not be read. The "
				"'Select a Configuration' list will be empty until a "
				"valid *.ini file is selected via Browse." % self.text_ctrl_LoadIniSection.GetLineText(0),
				"Import Settings Not Loaded",
				wx.OK | wx.ICON_WARNING,
			)

		self.button_Browse_LoadIniSection = wx.Button(self.notebook_1_pane_5, -1, "Browse")
		self.button_Browse_LoadIniSection.SetToolTip(wx.ToolTip(
			"Opens a dialog for selection an import settings file (*.ini)."))

		# select setting
		#self.label_SelectSettingSection = wx.StaticText(self.notebook_1_self.notebook_1_pane_5, -1, "Select setting")
		#strFancy = '<font color="$8CFA8C" size="12">Select setting</font>'
		# Select a Configuration (header)
		self.label_SelectSettingSection = wx.StaticText(self.notebook_1_pane_5, -1, "Select a Configuration")
		self.label_SelectSettingSection.SetFont(self.header_font)
			##wx.Font(self.font_units_size, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		self.label_SelectSettingSection.SetToolTip(wx.ToolTip(
			"A section with import settings must be selected for the data import."))

		self.listConfigurations = sorted(self.confParse.sections())
		self.choice_SelectSettingSection = wx.Choice(self.notebook_1_pane_5, -1, size = (500, 30), choices = self.listConfigurations)

		button1_w = 140
		button1_h = 24
		button1_small_w = button1_w / 2 - 5
		button1_small_h = 24

		sizeBorder = 5

		self.button_Delete_LoadIniSection = wx.Button(self.notebook_1_pane_5, -1, "Delete")
		self.button_Delete_LoadIniSection.SetToolTip(wx.ToolTip(
			"deletes the selected settings section from the *.ini file."))
		self.button_Save_LoadIniSection = wx.Button(self.notebook_1_pane_5, -1, "Save ...")
		self.button_Save_LoadIniSection.SetToolTip(wx.ToolTip(
			"Saves the current settings to the selected section."))
		self.button_SaveAs_LoadIniSection = wx.Button(self.notebook_1_pane_5, -1, "Save As ...")
		self.button_SaveAs_LoadIniSection.SetToolTip(wx.ToolTip(
			"Saves the current settings to a new section."))

		
		# neither textCtrl nor label stuff
		self.choice_SettingsSection_tolerance_ms = wx.Choice(self.notebook_1_pane_5, -1, choices = ["ppm", "Da"])
		self.choice_SettingsSection_tolerance_ms.SetStringSelection("ppm")
		self.store_SettingsSection_tolerance_ms = "ppm"
		self.choice_SettingsSection_tolerance_msms = wx.Choice(self.notebook_1_pane_5, -1, choices = ["ppm", "Da"])
		self.choice_SettingsSection_tolerance_msms.SetStringSelection("ppm")
		self.store_SettingsSection_tolerance_msms = None

		self.choice_SettingsSection_threshold_ms = wx.Choice(self.notebook_1_pane_5, -1, choices = ["absolute", "relative"])
		self.choice_SettingsSection_threshold_ms.SetStringSelection("absolute")
		self.store_SettingsSection_threshold_ms = "absolute"
		self.choice_SettingsSection_threshold_ms.SetToolTip(wx.ToolTip("Relative intensity in '%'"))
		self.choice_SettingsSection_threshold_msms = wx.Choice(self.notebook_1_pane_5, -1, choices = ["absolute", "relative"])
		self.choice_SettingsSection_threshold_msms.SetStringSelection("absolute")
		self.store_SettingsSection_threshold_msms = "absolute"
		self.choice_SettingsSection_threshold_msms.SetToolTip(wx.ToolTip("Relative intensity in '%'"))

		# the following line seemingly "resets" the font for the next control... this might be a bug in wxPython
		self.choice_SettingsSection_threshold_msms.SetFont(
			wx.Font(self.font_units_size, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

		# Adjust alignment for settings section
		self.label_SettingsSection_precursorMassShift = wx.StaticText(self.notebook_1_pane_5, -1, "MS1 offset", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_precursorMassShift.SetToolTip(wx.ToolTip(
			"MS1 m/z offset correction. All MS1 m/z values will be shifted by this value in Da.")
		)
		self.label_SettingsSection_precursorMassShift_unit = wx.StaticText(self.notebook_1_pane_5, -1, "Da", style=wx.ALIGN_LEFT)

		self.label_SettingsSection_precursorMassShiftOrbi = wx.StaticText(self.notebook_1_pane_5, -1, "PMO", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_precursorMassShiftOrbi.SetToolTip(wx.ToolTip(
			 "Precursor offset correction (PMO). Specifies a shift for the precursor masses of the MS/MS spectra. " +
			 "A negative value shifts the precursor m/z value to the left and a positive value to the right. " +
			 "This function is a workaround for precursor offset shifts which can occur on LTQ Orbitrap machines.")
		)
		self.label_SettingsSection_precursorMassShiftOrbi_unit = wx.StaticText(self.notebook_1_pane_5, -1, "Da", style=wx.ALIGN_LEFT)

		self.label_SettingsSection_selectionWindow = wx.StaticText(self.notebook_1_pane_5, -1, "Selection window", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_selectionWindow.SetToolTip(wx.ToolTip("Specify the half-width of the precursor isolation window."))
		self.label_SettingsSection_selectionWindow_unit = wx.StaticText(self.notebook_1_pane_5, -1, "Da", style=wx.ALIGN_LEFT)

		self.label_SettingsSection_timerange = wx.StaticText(self.notebook_1_pane_5, -1, "Timerange", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_timerange.SetToolTip(wx.ToolTip("Select a timerange from within the spectra should be imported"))
		self.label_SettingsSection_timerange_unit = wx.StaticText(self.notebook_1_pane_5, -1, "sec.", style=wx.ALIGN_LEFT)

		self.label_SettingsSection_massrange = wx.StaticText(self.notebook_1_pane_5, -1, "m/z range", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_massrange.SetToolTip(wx.ToolTip("Select a m/z range from within the spectra should be imported"))
		self.label_SettingsSection_massrange_ms = wx.StaticText(self.notebook_1_pane_5, -1, "MS", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_massrange_ms_unit = wx.StaticText(self.notebook_1_pane_5, -1, "m/z,m/z", style=wx.ALIGN_LEFT)
		self.label_SettingsSection_massrange_msms = wx.StaticText(self.notebook_1_pane_5, -1, "MS/MS", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_massrange_msms_unit = wx.StaticText(self.notebook_1_pane_5, -1, "m/z,m/z", style=wx.ALIGN_LEFT)

		self.label_SettingsSection_resolution = wx.StaticText(self.notebook_1_pane_5, -1, "Resolution", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_resolution_ms = wx.StaticText(self.notebook_1_pane_5, -1, "MS", style=wx.ALIGN_RIGHT)
		strTT = """Set the resolution of the acquired spectra according to mass spec settings.
\nNOTE that this resolution referes to the smalles mass in the spectra. The change of resolution for greater masses is handled with the 'resolution gradien' below."""
		self.label_SettingsSection_resolution.SetToolTip(wx.ToolTip(strTT))
		self.label_SettingsSection_resolution_ms_unit = wx.StaticText(self.notebook_1_pane_5, -1, "FWHM", style=wx.ALIGN_LEFT)
		self.label_SettingsSection_resolution_msms = wx.StaticText(self.notebook_1_pane_5, -1, "MS/MS", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_resolution_msms_unit = wx.StaticText(self.notebook_1_pane_5, -1, "FWHM", style=wx.ALIGN_LEFT)

		self.label_SettingsSection_tolerance = wx.StaticText(self.notebook_1_pane_5, -1, "Tolerance", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_tolerance.SetToolTip(wx.ToolTip("Set the accuracy of the acquired masses according to mass spec settings"))
		self.label_SettingsSection_tolerance_ms = wx.StaticText(self.notebook_1_pane_5, -1, "MS", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_tolerance_msms = wx.StaticText(self.notebook_1_pane_5, -1, "MS/MS", style=wx.ALIGN_RIGHT)

		self.label_SettingsSection_threshold = wx.StaticText(self.notebook_1_pane_5, -1, "Threshold", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_threshold.SetToolTip(wx.ToolTip("Set a threshold to import only masses above a certain intensity"))
		self.label_SettingsSection_threshold_ms = wx.StaticText(self.notebook_1_pane_5, -1, "MS", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_threshold_msms = wx.StaticText(self.notebook_1_pane_5, -1, "MS/MS", style=wx.ALIGN_RIGHT)

		self.label_SettingsSection_occupationThr = wx.StaticText(self.notebook_1_pane_5, -1, "Min occupation", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_occupationThr.SetToolTip(wx.ToolTip("Select a minimum percentage with which a peak should be appear in all samples, the value should be between 0 and 1"))
		self.label_SettingsSection_occupationThr_ms = wx.StaticText(self.notebook_1_pane_5, -1, "MS", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_occupationThr_ms_unit = wx.StaticText(self.notebook_1_pane_5, -1, "[0..1]", style=wx.ALIGN_LEFT)
		self.label_SettingsSection_occupationThr_msms = wx.StaticText(self.notebook_1_pane_5, -1, "MS/MS", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_occupationThr_msms_unit = wx.StaticText(self.notebook_1_pane_5, -1, "[0..1]", style=wx.ALIGN_LEFT)
  
		self.label_SettingsSection_resDelta = wx.StaticText(self.notebook_1_pane_5, -1, "Resolution gradient", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_resDelta.SetToolTip(wx.ToolTip("Give a gradient of how the resolution changes the greater the m/z value is"))
  
		self.label_SettingsSection_resDelta_ms = wx.StaticText(self.notebook_1_pane_5, -1, "MS", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_resDelta_ms_unit = wx.StaticText(self.notebook_1_pane_5, -1, "res/(m/z)", style=wx.ALIGN_LEFT)
		self.label_SettingsSection_resDelta_msms = wx.StaticText(self.notebook_1_pane_5, -1, "MS/MS", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_resDelta_msms_unit = wx.StaticText(self.notebook_1_pane_5, -1, "res/(m/z)", style=wx.ALIGN_LEFT)

		self.label_SettingsSection_calibration = wx.StaticText(self.notebook_1_pane_5, -1, "Calibration masses", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_calibration.SetToolTip(wx.ToolTip("Given m/z values are used for linear recalibration of the spectra"))
		#self.label_SettingsSection_calibration_unit = wx.StaticText(pane, -1, "m/z, m/z, ...")
		self.label_SettingsSection_calibration_ms = wx.StaticText(self.notebook_1_pane_5, -1, "MS", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_calibration_msms = wx.StaticText(self.notebook_1_pane_5, -1, "MS/MS", style=wx.ALIGN_RIGHT)

		self.label_SettingsSection_filter_ms = wx.StaticText(self.notebook_1_pane_5, -1, "MS", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_filter_ms_unit = wx.StaticText(self.notebook_1_pane_5, -1, "[0..1]", style=wx.ALIGN_LEFT)
		self.label_SettingsSection_filter_ms.SetToolTip(wx.ToolTip("A minimum frequency for a peak appearing in all associated scans, the value should be between 0 and 1"))
		self.label_SettingsSection_filter_msms = wx.StaticText(self.notebook_1_pane_5, -1, "Frequency filter", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_filter_ms_ms = wx.StaticText(self.notebook_1_pane_5, -1, "MS/MS", style=wx.ALIGN_RIGHT)
		self.label_SettingsSection_filter_msms_unit = wx.StaticText(self.notebook_1_pane_5, -1, "[0..1]", style=wx.ALIGN_LEFT)

		self.label_SettingsSection_filter_msms.SetToolTip(wx.ToolTip("A minimum frequency for a peak appearing in all associated scans, the value is between 0 and 1 "))
		self.text_ctrl_SettingsSection_precursorMassShift = wx.TextCtrl(self.notebook_1_pane_5, -1, '')
		self.text_ctrl_SettingsSection_precursorMassShiftOrbi = wx.TextCtrl(self.notebook_1_pane_5, -1, '')
		self.text_ctrl_SettingsSection_selectionWindow = wx.TextCtrl(self.notebook_1_pane_5, -1, '')
		self.text_ctrl_SettingsSection_timerange1 = wx.TextCtrl(self.notebook_1_pane_5, -1, '')
		self.text_ctrl_SettingsSection_timerange2 = wx.TextCtrl(self.notebook_1_pane_5, -1, '')
		self.text_ctrl_SettingsSection_massrange_ms1 = wx.TextCtrl(self.notebook_1_pane_5, -1, '')
		self.text_ctrl_SettingsSection_massrange_ms2 = wx.TextCtrl(self.notebook_1_pane_5, -1, '')
		self.text_ctrl_SettingsSection_massrange_msms1 = wx.TextCtrl(self.notebook_1_pane_5, -1, '')
		self.text_ctrl_SettingsSection_massrange_msms2 = wx.TextCtrl(self.notebook_1_pane_5, -1, '')
		self.text_ctrl_SettingsSection_resolution_ms = wx.TextCtrl(self.notebook_1_pane_5, -1, '')
		self.text_ctrl_SettingsSection_resolution_msms = wx.TextCtrl(self.notebook_1_pane_5, -1, '')
		self.text_ctrl_SettingsSection_tolerance_ms = wx.TextCtrl(self.notebook_1_pane_5, -1, '')
		self.text_ctrl_SettingsSection_tolerance_msms = wx.TextCtrl(self.notebook_1_pane_5, -1, '')
		self.text_ctrl_SettingsSection_threshold_ms = wx.TextCtrl(self.notebook_1_pane_5, -1, '')
		self.text_ctrl_SettingsSection_threshold_msms = wx.TextCtrl(self.notebook_1_pane_5, -1, '')
		self.text_ctrl_SettingsSection_occupationThr_ms = wx.TextCtrl(self.notebook_1_pane_5, -1, '')
		self.text_ctrl_SettingsSection_occupationThr_msms = wx.TextCtrl(self.notebook_1_pane_5, -1, '')
		self.text_ctrl_SettingsSection_resDelta_ms = wx.TextCtrl(self.notebook_1_pane_5, -1, '')
		self.text_ctrl_SettingsSection_resDelta_msms = wx.TextCtrl(self.notebook_1_pane_5, -1, '')
		self.text_ctrl_SettingsSection_calibration_ms = wx.TextCtrl(self.notebook_1_pane_5, -1, '')
		self.text_ctrl_SettingsSection_calibration_msms = wx.TextCtrl(self.notebook_1_pane_5, -1, '')
		self.text_ctrl_SettingsSection_filter_ms = wx.TextCtrl(self.notebook_1_pane_5, -1, '0')
		self.text_ctrl_SettingsSection_filter_msms = wx.TextCtrl(self.notebook_1_pane_5, -1, '0')

		### end *.ini ###
  
  
  
  
		#########################
		### RUN notebook pane ###

		# mfql Queries
		# Select/Add MFQL files (header)
		self.label_mfqlQueriesSection = wx.StaticText(self.notebook_1_pane_3, -1, "Select/Add MFQL files")
		self.label_mfqlQueriesSection.SetFont(self.header_font)
			##wx.Font(self.font_units_size, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		self.label_mfqlQueriesSection.SetToolTip(wx.ToolTip(
			"MFQL scripts have to be selected for LipidXplorer to query the data."))
		self.list_box_1 = wx.ListBox(self.notebook_1_pane_3, -1, pos=(10,10), choices=[], name="", style = wx.LB_EXTENDED)
		self.list_box_1.SetToolTip(wx.ToolTip(
			"All queries occuring in this list will be runned on the selected MasterScan file after pressing 'Lipidx Run'."))
		self.button_AddMFQL = wx.Button(self.notebook_1_pane_3, -1, "Add MFQL file", style=wx.BU_TOP|wx.BU_BOTTOM)
		self.button_AddMFQL.SetToolTip(wx.ToolTip(
			"Opens a dialog for selecting a MFQL file."))
		self.button_AddDir = wx.Button(self.notebook_1_pane_3, -1, "Add MFQL directory")
		self.button_AddDir.SetToolTip(wx.ToolTip(
			"Opens a dialog for selecting a directory of MFQL files. It will load all its content to the list."))
		self.button_NewFile = wx.Button(self.notebook_1_pane_3, -1, "New MFQL Entry")
		self.button_NewFile.SetToolTip(wx.ToolTip(
			"Opens a dialog for specifying a new MFQL file. The file will be opened for editing in a new panel."))
		self.button_OpenFile = wx.Button(self.notebook_1_pane_3, -1, "Edit MFQL Entry")
		self.button_OpenFile.SetToolTip(wx.ToolTip(
			"Opens an list entry for editing and viewing in a new panel."))
		self.button_RemoveEntry = wx.Button(self.notebook_1_pane_3, -1, "Remove MFQL Entry")
		self.button_RemoveEntry.SetToolTip(wx.ToolTip(
			"Removes the selected entry from the list."))

		# masterScan file
		self.label_MasterScanSection = wx.StaticText(self.notebook_1_pane_3, -1, "Select Master Scan File")
		self.text_ctrl_MasterScanSection = wx.TextCtrl(self.notebook_1_pane_3, -1, "", style=wx.TE_PROCESS_ENTER)
		self.text_ctrl_MasterScanSection.SetToolTip(wx.ToolTip(
			"Specify the MasterScan file which should be queried."))

		self.button_Browse_MasterScan = wx.Button(self.notebook_1_pane_3, -1, "Browse")
		self.button_Browse_MasterScan.SetToolTip(wx.ToolTip(
			"Opens a dialog for MasterScan specification."))
		self.button_Browse_MasterScan.SetToolTip(wx.ToolTip(
			"Open a directory with your MasterScan files. All other text fields will be filled automatically."))

		# output file
		self.label_OutputSection = wx.StaticText(self.notebook_1_pane_3, -1, "Specify output file")
		self.text_ctrl_OutputSection = wx.TextCtrl(self.notebook_1_pane_3, -1, "")
		self.text_ctrl_OutputSection.SetToolTip(wx.ToolTip(
			"The ouput is a comma seperated file (*.csv)."))
		self.button_Browse_OutputSection = wx.Button(self.notebook_1_pane_3, -1, "Browse")
		self.button_Browse_OutputSection.SetToolTip(wx.ToolTip(
			"Specify the output (*.csv) file."))
		self.button_Open_OutputSection = wx.Button(self.notebook_1_pane_3, -1, "View")
		self.button_Open_OutputSection.SetToolTip(wx.ToolTip(
			"Opens the generated output to take a look inside."))

		# options
		self.label_RunOptions = wx.StaticText(self.notebook_1_pane_3, -1, "Optional settings for this run")
		self.label_RunOptions_tolerance = wx.StaticText(self.notebook_1_pane_3, -1, "Tolerance	")
		self.label_RunOptions_tolerance.SetToolTip(
		wx.ToolTip(
			"Run-time mass tolerance override used during MFQL identification. "
			"If left empty, the default tolerances from the import settings are used."
		))
		self.label_RunOptions_MS = wx.StaticText(self.notebook_1_pane_3, -1, "MS	")
		self.text_ctrl_RunOptions_MS = wx.TextCtrl(self.notebook_1_pane_3, -1, "")
		self.choice_RunOptions_MS_type = wx.Choice(self.notebook_1_pane_3, -1, choices = self.listChoices_types)
		self.label_RunOptions_MSMS = wx.StaticText(self.notebook_1_pane_3, -1, "MS/MS	")
		self.text_ctrl_RunOptions_MSMS = wx.TextCtrl(self.notebook_1_pane_3, -1, "")
		self.choice_RunOptions_MSMS_type = wx.Choice(self.notebook_1_pane_3, -1, choices = self.listChoices_types)

		#self.label_RunOptions_minocc = wx.StaticText(self.notebook_1_pane_3, -1, "Min Occ")
		#self.label_RunOptions_MS_minocc = wx.StaticText(self.notebook_1_pane_3, -1, "MS")
		#self.text_ctrl_RunOptions_MS_minocc = wx.TextCtrl(self.notebook_1_pane_3, -1, "")
		#self.label_RunOptions_MSMS_minocc = wx.StaticText(self.notebook_1_pane_3, -1, "MS/MS")
		#self.text_ctrl_RunOptions_MSMS_minocc = wx.TextCtrl(self.notebook_1_pane_3, -1, "")

		self.checkBox_OptionsSection_isocorrect_ms = wx.CheckBox(self.notebook_1_pane_3, -1, "Isotopic Correction MS")
		self.checkBox_OptionsSection_isocorrect_ms.SetValue(True)

		self.checkBox_OptionsSection_isocorrect_ms.SetToolTip(wx.ToolTip(
			"Isotopic correction of quantitative information in MS spectra"))
		self.checkBox_OptionsSection_isocorrect_msms = wx.CheckBox(self.notebook_1_pane_3, -1, "Isotopic Correction MS/MS")
		self.checkBox_OptionsSection_isocorrect_msms.SetValue(True)
		self.checkBox_OptionsSection_isocorrect_msms.SetToolTip(wx.ToolTip(
			"Isotopic correction of quantitative information in MS/MS spectra"))
		self.checkBox_OptionsSection_complement_sc = wx.CheckBox(self.notebook_1_pane_3, -1, "Generate Complement MasterScan")
		self.checkBox_OptionsSection_complement_sc.SetToolTip(wx.ToolTip(
			"Generate the complement MasterScan and saved it as <name>-complement.sc in the origin directory."))
		self.checkBox_OptionsSection_dumpMasterScan = wx.CheckBox(self.notebook_1_pane_3, -1, "Dump MasterScan")
		self.checkBox_OptionsSection_dumpMasterScan.SetToolTip(wx.ToolTip(
			"Generate a dump of the MasterScan to view its content."))
		self.checkBox_OptionsSection_tabLimited = wx.CheckBox(self.notebook_1_pane_3, -1, "Tab delimited")
		self.checkBox_OptionsSection_tabLimited.SetToolTip(wx.ToolTip(
			"Use tabs as delimiter instead as commas."))
		self.checkBox_OptionsSection_compress = wx.CheckBox(self.notebook_1_pane_3, -1, "Compress")
		self.checkBox_OptionsSection_compress.SetToolTip(wx.ToolTip(
			"No output of query names."))
		self.checkBox_OptionsSection_nohead = wx.CheckBox(self.notebook_1_pane_3, -1, "No head")
		self.checkBox_OptionsSection_nohead.SetToolTip(wx.ToolTip(
			"No output of *.csv file's head with the names of the columns."))
		self.checkBox_generateStatistics = wx.CheckBox(self.notebook_1_pane_3, -1, "Statistics")
		self.checkBox_generateStatistics.SetToolTip(wx.ToolTip(
			"Some statistic values are added to the output:\n" +\
				"\t1) the intensity relative to total ion count of one lipid class \n" +\
				"\t2) the intensity average \n" +\
				"\t3) the standard deviation"))
		self.checkBox_noPermutations = wx.CheckBox(self.notebook_1_pane_3, -1, "No permutations")
		self.checkBox_noPermutations.SetValue(True)
		self.checkBox_noPermutations.SetToolTip(wx.ToolTip(
"""Without permutations the positions of fatty acids are random
and cannot be determined. But the query runs faster and uses less
memory. Otherwise some constraints in the
SUCHTHAT section could generate positions of fatty acids according
to particular attributes of the peaks. Like for example the
intensity."""))

		# dump file
		#self.label_DumpSection = wx.StaticText(self.notebook_1_pane_3, -1, "Specify optional dump file")
		#	"The dump file contains the content of the MasterScan plus the marked ions and fragment ions." +\
		#	"Leave this field empty, if you do not want to output the MasterScan content."))
		#self.button_Browse_DumpSection = wx.Button(self.notebook_1_pane_3, -1, "Save dump file as ...")
		#self.button_Browse_DumpSection.SetToolTip(wx.ToolTip(
		#	"Opens a dialog for specification of the dump output file."))
		self.button_Open_DumpSection = wx.Button(self.notebook_1_pane_3, -1, "View dump file")
		self.button_Open_DumpSection.SetToolTip(wx.ToolTip(
			"Opens the dump file to take a look inside."))

		# run
		self.button_RunLipidX = wx.Button(self.notebook_1_pane_3, -1, "Run LipidXplorer")
		self.button_RunLipidX.SetToolTip(wx.ToolTip(
			"Starts LipidXplorer with the choosen MFQL files on the MasterScan file."))
### RUN notebook pane ###
		#########################





		self.debug = TextOutFrame(self, -1, "Debugging")
		self.debug.text_ctrl.AppendText("LipidXplorer version: %s\n" % self.version)
		self.debug.text_ctrl.AppendText("Python version: " + sys.version + \
				"(%s.%s.%s)" % sys.version_info[0:3] + platform.machine() + '\n\n')

		self.debugSetting = SetDebugFrame(self, -1, "Set debugging options")
		self.alignmentSetting = SetAlignmentFrame(self, -1, "Choose the preferred alignment method")
		self.outputOptionSetting = SetOutputOptionFrame(self, -1, "Set your output options")

		self.__set_properties()
		self.__do_layout()
  
		self.__bind_events()
		self.Layout()
		self.Center()
  





		# end wxGlade
  




############################

	def __bind_events(self):

		self.button_open_next.Bind(wx.EVT_BUTTON, self.on_open_next_view)
		self.button_open_legacy.Bind(wx.EVT_BUTTON, self.on_open_legacy_view)
		self.button_back_from_placeholder.Bind(wx.EVT_BUTTON, self.on_back_to_landing)
		self.button_back_to_start.Bind(wx.EVT_BUTTON, self.on_back_to_landing)

		# for Key events
		#self.Bind(wx.EVT_KEY_DOWN, self.OnKeyPressed)

		# for the menu
		self.Bind(wx.EVT_MENU, self.OnMenuProjectLoad, id = 1)
		self.Bind(wx.EVT_MENU, self.OnMenuProjectSave, id = 2)
		self.Bind(wx.EVT_MENU, self.OnMenuProjectSaveAs, id = 3)
		self.Bind(wx.EVT_MENU, self.OnMenuDebugWin, id = 4)
		self.Bind(wx.EVT_MENU, self.OnMenuDebugSet, id = 5)
		# disable the alignment settings menu
		#self.Bind(wx.EVT_MENU, self.OnMenuAlignmentSet, id = 6)
		self.Bind(wx.EVT_MENU, self.OnMenuOutputOptions, id = 7)
		self.Bind(wx.EVT_MENU, self.OnMenuLipidXDocumentation, id = 8)
		self.Bind(wx.EVT_MENU, self.OnMenuMFQLTutorial, id = 9)
		self.Bind(wx.EVT_MENU, self.OnMenuMFQLReference, id = 10)
		self.Bind(wx.EVT_MENU, self.OnMenuHelpImportSettings, id = 11)
		self.Bind(wx.EVT_MENU, self.OnMenuHelpRun, id = 12)
		self.Bind(wx.EVT_MENU, self.OnMenuHelpMSTools, id = 13)
		self.Bind(wx.EVT_MENU, self.OnMenuAbout, id = 14)

		# for the editor
		self.Bind(wx.EVT_TEXT_ENTER, self.OnTextEnter)
		self.Bind(wx.EVT_TEXT, self.OnText)

		# mstools panel buttons
		self.Bind(wx.EVT_BUTTON, self.OnMassToSumComposition, self.button_massToSumComposition)
		self.Bind(wx.EVT_BUTTON, self.OnSumCompositionToMass, self.button_sumCompositionToMass)
		self.Bind(wx.EVT_BUTTON, self.OnCalcIsotopes, self.button_Isotopes)

		# import source panel
		self.Bind(wx.EVT_BUTTON, self.OnBrowse_ImportData, self.button_Browse_ImportDataSection)
		self.Bind(wx.EVT_BUTTON, self.OnBrowse_OutputMasterScan, self.button_Browse_OutputMasterScanSection)
  
  
  ################ Ballal ############
		self.Bind(wx.EVT_BUTTON, self.OnBrowse_MFQL_batch, self.button_Browse_MFQL_batch)
		self.Bind(wx.EVT_BUTTON, self.OnDelete_MFQL_batch, self.button_Delete_MFQL_batch)
		self.Bind(wx.EVT_BUTTON, self.On_button_RUN_batch, self.button_RUN_batch)
  
  
  
		self.Bind(wx.EVT_BUTTON, self.OnBrowse_LoadIni, self.button_Browse_LoadIniSection)
		# self.Bind(wx.EVT_BUTTON, self.OnGroupSamples, self.label_SettingsSection_occupationThr_groups)
		self.Bind(wx.EVT_BUTTON, self.OnStartImport, self.button_StartImport)
		self.Bind(wx.EVT_CHOICE, self.OnConfigurationChoice, self.choice_SelectSettingSection)
		# self.Bind(wx.EVT_CHECKBOX, self.OnImportMSMS, self.checkBox_importMSMS)


		# import settings panel
		self.Bind(wx.EVT_BUTTON, self.OnSave_LoadIni, self.button_Save_LoadIniSection)
		self.Bind(wx.EVT_BUTTON, self.OnDelete_LoadIni, self.button_Delete_LoadIniSection)
		self.Bind(wx.EVT_BUTTON, self.OnSaveAs_LoadIni, self.button_SaveAs_LoadIniSection)
		self.Bind(wx.EVT_CHOICE, self.OnChoice_Tolerance_MS, self.choice_SettingsSection_tolerance_ms)
		self.Bind(wx.EVT_CHOICE, self.OnChoice_Tolerance_MSMS, self.choice_SettingsSection_tolerance_msms)
		self.Bind(wx.EVT_CHOICE, self.OnChoice_Threshold_MS, self.choice_SettingsSection_threshold_ms)
		self.Bind(wx.EVT_CHOICE, self.OnChoice_Threshold_MSMS, self.choice_SettingsSection_threshold_msms)

		# run panel buttons
		self.Bind(wx.EVT_LISTBOX_DCLICK, self.OnOpenFile, self.list_box_1)
		self.Bind(wx.EVT_BUTTON, self.OnAddMFQL, self.button_AddMFQL)
		self.Bind(wx.EVT_BUTTON, self.OnRemoveEntry, self.button_RemoveEntry)
		self.Bind(wx.EVT_BUTTON, self.OnOpenFile, self.button_OpenFile)
		self.Bind(wx.EVT_BUTTON, self.OnNewFile, self.button_NewFile)
		self.Bind(wx.EVT_BUTTON, self.OnAddDir, self.button_AddDir)
		self.Bind(wx.EVT_BUTTON, self.OnBrowse_Output, self.button_Browse_OutputSection)
		self.Bind(wx.EVT_BUTTON, self.OnOpen_Output, self.button_Open_OutputSection)
		self.Bind(wx.EVT_BUTTON, self.OnOpen_Dump, self.button_Open_DumpSection)
		self.Bind(wx.EVT_BUTTON, self.OnBrowse_MasterScan, self.button_Browse_MasterScan)
		self.Bind(wx.EVT_BUTTON, self.OnRunLipidX, self.button_RunLipidX)

		# close application
		self.Bind(wx.EVT_CLOSE, self.OnCloseApp, self)

		# stc bindings
		#self.Bind(stc.EVT_STC_CHANGE, self.OnStcChange)

		# set up drag'n drop
		dropTargetMFQLFiles = MFQLDropTarget(self.list_box_1, self)
		self.list_box_1.SetDropTarget(dropTargetMFQLFiles)
  
  
		is_batch_checked = self.checkBox_BatchMode.IsChecked()

		if is_batch_checked:
			dropTargetMasterScanFile = FileDrawerDropTarget(self.text_ctrl_MasterScanSection, self.OnBrowse_MasterScan_Body, "ini")
			self.text_ctrl_MasterScanSection.SetDropTarget(dropTargetMasterScanFile)	
				
		else:
			dropTargetMasterScanFile = FileDrawerDropTarget(self.text_ctrl_MasterScanSection, self.OnBrowse_MasterScan_Body, "sc")
			self.text_ctrl_MasterScanSection.SetDropTarget(dropTargetMasterScanFile)	
    


		dropTargetImportFolder = DrawerDropTarget(self.text_ctrl_ImportDataSection, self.OnBrowse_ImportData_Body)
		self.text_ctrl_ImportDataSection.SetDropTarget(dropTargetImportFolder)

		dropTargetSettingsFile = FileDrawerDropTarget(self.text_ctrl_LoadIniSection, self.OnBrowse_LoadIni_Body, "ini")
		self.text_ctrl_LoadIniSection.SetDropTarget(dropTargetSettingsFile)


		### initialization for threading ###

		# bind events for stdout capture
		self.Bind(EVT_STDOUT, self.OnUpdateOutputWindow)
		#self.Bind(wx.EVT_TIMER, self.OnProcessPendingOutputWindowEvents)
		self.Bind(EVT_WORKER_DONE, self.OnWorkerDone)
		self.Bind(EVT_WRITE_DEBUG, self.OnUpdateOutputWindowEvent)

		# bind events for progressDialog
		self.Bind(EVT_PROGRESSDLG_UPDATE, self.OnUpdateProgressDialog)
  
		
  

   
	def OnUpdateOutputWindow(self, evt):
		self.debug.text_ctrl.AppendText(evt.text)
		self.debug.text_ctrl.ScrollToLine(self.debug.text_ctrl.GetLineCount())
		pass

	def OnUpdateOutputWindowEvent(self, evt):
		self.debug.text_ctrl.AppendText(evt.text)
		self.debug.text_ctrl.ScrollToLine(self.debug.text_ctrl.GetLineCount())
		#self.debug.text_ctrl.ScrollLines(1)
		#self.debug.text_ctrl.SetInsertionPoint(self.debug.text_ctrl.GetLastPosition() + 1)
		pass

	def OnWorkerDone(self, evt):
		if evt.msg == "startFromGUI":
			self.button_RunLipidX.Enable()
		if evt.msg == "doImport":
			self.button_StartImport.Enable()
		if evt.msg == "doImport_new":
			self.button_StartImport.Enable()
		if evt.msg == "doImport_alt":
			self.button_StartImport.Enable()
		if evt.msg == "startMFQL":
			self.button_RunLipidX.Enable()
		if evt.msg == "startImport":
			self.button_StartImport.Enable()
			self.button_RunLipidX.Enable()

		if self.debug.progressDialog:
			self.debug.progressDialog.Destroy()

	def OnUpdateProgressDialog(self, evt):
		self.debug.progressDialog.Update(evt.value)

	def OnKeyPressed(self, evt):

		key = evt.GetKeyCode()







	def OnMenuProjectSaveAs(self, evt):

		project = self.readOptions()
		print("OnMenuProjectSaveAs    project options:", project.options)
		# initialize config parser and fill it with the options
		sectionP = "project"
		sectionQ = "mfql"
		configParser = configparser.ConfigParser()
		configParser.add_section(sectionP)
		configParser.add_section(sectionQ)
		for opt in list(project.options.keys()):
			#print("OnMenuProjectSaveAs    option:", opt, "value:", project.options[opt])
			configParser.set(sectionP, opt, str(project.options[opt])) # in python3 configparser only accepts strings
		for query in list(project.mfql.keys()):
			configParser.set(sectionQ, query + "-name", query)
			configParser.set(sectionQ, query, project.mfql[query])

		# offer a filename for the project
		if not project.options['importDir'] is None:
			defaultFileName = "%s-project.lxp" % project.options['importDir'].split(os.sep)[-1]
		else:
			defaultFileName = ".lxp"

		dlg = wx.FileDialog(wx.GetApp().frame, "Specify the project file",
				style = wx.DD_DEFAULT_STYLE|wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT, defaultFile = defaultFileName)

		if not project.options['importDir'] is None:
			dlg.SetDirectory(project.options['importDir'])
		dlg.SetWildcard("*.lxp files|*.lxp")

		if dlg.ShowModal() == wx.ID_OK:
			projectFilePath = dlg.GetPath()
			if not re.match(r'.*\.lxp', projectFilePath):
				s = projectFilePath.split('.')
				if len(s) == 1:
					projectFilePath += '.sc'
				else:
					projectFilePath = ''
				for i in s[:-1]:
					projectFilePath += '%s.' % i
				projectFilePath += 'lxp'

			with open(projectFilePath, 'w') as f:
				configParser.write(f)

			self.projectFile = projectFilePath

		dlg.Destroy()

	def OnMenuProjectSave(self, evt):

		if self.projectFile == '':
			self.OnMenuProjectSaveAs(None)
			return None

		project = self.readOptions()

		# initialize config parser and fill it with the options
		sectionP = "project"
		sectionQ = "mfql"
		configParser = configparser.ConfigParser()
		configParser.add_section(sectionP)
		configParser.add_section(sectionQ)
		for opt in list(project.options.keys()):
			print("OnMenuProjectSave    option:", opt, "value:", project.options[opt])
			configParser.set(sectionP, opt, str(project.options[opt])) # in python3 configparser only accepts strings
		for query in list(project.mfql.keys()):
			configParser.set(sectionQ, query + "-name", query)
			configParser.set(sectionQ, query, project.mfql[query])

		# offer a filename for the project
		if not project.options['importDir'] is None:
			defaultFileName = "%s-project.lxp" % project.options['importDir'].split(os.sep)[-1]
		else:
			defaultFileName = ".lxp"

		with open(self.projectFile, 'w') as f:
			configParser.write(f)
    ############## ballal##########
	def normalize(self, value):
		value = value.strip() if isinstance(value, str) else value
		return value if value not in (None, '', []) else None
	#####################################

	def readOptions(self):

		print("readOptions----------------GUI-------###############################",self.currentConfiguration)
		project = Project()

		project.options['importDir'] = self.text_ctrl_ImportDataSection.GetValue()
		project.options['masterScanImport'] = self.text_ctrl_OutputMasterScanSection.GetValue() # in expectation of a project file
		project.options['masterScanRun'] = self.text_ctrl_MasterScanSection.GetValue() # in expectation of a project file
		project.options['importMSMS'] ="True" ########## Ballal 
		project.options['pisSpectra'] = "False" ########## Ballal
		project.options['dataType'] = self.combo_ctrl_ImportDataSection.GetValue()
		project.options['ini'] = self.text_ctrl_LoadIniSection.GetValue()
		project.options['setting'] = self.currentConfiguration       ## self.choice_SelectSettingSection.GetSelection()
		project.options['selectionWindow'] = self.text_ctrl_SettingsSection_selectionWindow.GetValue()
		project.options['timerange'] = "(%s,%s)" % (self.text_ctrl_SettingsSection_timerange1.GetValue(), self.text_ctrl_SettingsSection_timerange2.GetValue())
		project.options['MScalibration'] = self.text_ctrl_SettingsSection_calibration_ms.GetValue()
		project.options['MSMScalibration'] = self.text_ctrl_SettingsSection_calibration_msms.GetValue()
		project.options['MSfilter'] = self.text_ctrl_SettingsSection_filter_ms.GetValue()
		project.options['MSMSfilter'] = self.text_ctrl_SettingsSection_filter_msms.GetValue()
		project.options['MSmassrange'] = "(%s,%s)" % (self.text_ctrl_SettingsSection_massrange_ms1.GetValue(), self.text_ctrl_SettingsSection_massrange_ms2.GetValue())
		project.options['MSMSmassrange'] = "(%s,%s)" % (self.text_ctrl_SettingsSection_massrange_msms1.GetValue(), self.text_ctrl_SettingsSection_massrange_msms2.GetValue())
		project.options['MStolerance'] = self.text_ctrl_SettingsSection_tolerance_ms.GetValue()
		project.options['MSMStolerance'] = self.text_ctrl_SettingsSection_tolerance_msms.GetValue()
		project.options['MStoleranceType'] = self.choice_SettingsSection_tolerance_ms.GetString(self.choice_SettingsSection_tolerance_ms.GetSelection())
		project.options['MSMStoleranceType'] = self.choice_SettingsSection_tolerance_msms.GetString(self.choice_SettingsSection_tolerance_msms.GetSelection())
		project.options['MSresolution'] = self.text_ctrl_SettingsSection_resolution_ms.GetValue()
		project.options['MSMSresolution'] = self.text_ctrl_SettingsSection_resolution_msms.GetValue()
		############## balla test #########
		# value = self.text_ctrl_SettingsSection_resDelta_ms.GetValue()
		# print("MSresolutionDelta---------------------------------------------: =", value)
		#########################
  
		project.options['MSresolutionDelta'] = self.text_ctrl_SettingsSection_resDelta_ms.GetValue()
  
  
		project.options['MSMSresolutionDelta'] = self.text_ctrl_SettingsSection_resDelta_msms.GetValue()
		project.options['MSthreshold'] = self.text_ctrl_SettingsSection_threshold_ms.GetValue()
		project.options['MSMSthreshold'] = self.text_ctrl_SettingsSection_threshold_msms.GetValue()
		project.options['MSthresholdType'] = self.choice_SettingsSection_threshold_ms.GetString(self.choice_SettingsSection_threshold_ms.GetSelection())
		project.options['MSMSthresholdType'] = self.choice_SettingsSection_threshold_msms.GetString(self.choice_SettingsSection_threshold_msms.GetSelection())
		project.options['MSminOccupation'] = self.text_ctrl_SettingsSection_occupationThr_ms.GetValue()
		project.options['MSMSminOccupation'] = self.text_ctrl_SettingsSection_occupationThr_msms.GetValue()
		project.options['precursorMassShift'] = self.text_ctrl_SettingsSection_precursorMassShift.GetValue()
		project.options['precursorMassShiftOrbi'] = self.text_ctrl_SettingsSection_precursorMassShiftOrbi.GetValue()
		project.options['alignmentMethodMS'] = self.alignmentSetting.alignmentMethodsMS_intern[self.alignmentSetting.radioBox_ms_alignment.GetSelection()]
		project.options['alignmentMethodMSMS'] = self.alignmentSetting.alignmentMethodsMSMS_intern[self.alignmentSetting.radioBox_msms_alignment.GetSelection()]
		project.options['scanAveragingMethod'] = self.alignmentSetting.scanAveragingMethods_intern[self.alignmentSetting.radioBox_scanAveraging.GetSelection()]
		project.options['isotopicCorrection_MSMS'] =  self.debugSetting.checkBox_IsotopicCorrection_MSMS.GetValue() # here starts the Set debugging Options from the Debug menu
		project.options['removeIsotopes'] = self.debugSetting.checkBox_removeIsotopes.GetValue()
		project.options['isotopesInMasterScan'] = self.debugSetting.checkBox_isotopesInMasterscan.GetValue()
		project.options['monoisotopicCorrection'] = self.debugSetting.checkBox_monoisotopicCorrection.GetValue()
		project.options['relativeIntensity'] = self.debugSetting.checkBox_relativeIntensity.GetValue()
		project.options['logMemory'] =  self.debugSetting.checkBox_MemoryLog.GetValue() # here starts the Set debugging Options from the Debug menu
		project.options['intensityCorrection'] = self.outputOptionSetting.checkBox_correctIntensities.GetValue() # here starts the output options menu
		project.options['intensityCorrectionPrecursor'] = self.outputOptionSetting.text_ctrl_precursor.GetValue()
		project.options['intensityCorrectionFragment'] = self.outputOptionSetting.text_ctrl_fragment.GetValue()
		project.options['masterScanInSQL'] = self.outputOptionSetting.checkBox_masterScanInSQL.GetValue()
		project.options['sumFattyAcids'] = self.outputOptionSetting.checkBox_sumFattyAcids.GetValue()
		project.options['settingsPrefix'] = self.outputOptionSetting.checkBox_settingsPrefix.GetValue()
		project.options['resultFile'] = self.text_ctrl_OutputSection.GetValue() # here starts the RUN panel
		########### ballal##############
		project.options['optionalMStolerance'] = self.normalize(self.text_ctrl_RunOptions_MS.GetValue())
		project.options['optionalMSMStolerance'] = self.normalize(self.text_ctrl_RunOptions_MSMS.GetValue())
		idx = self.choice_RunOptions_MS_type.GetSelection()
		if idx == wx.NOT_FOUND:
			project.options['optionalMStoleranceType'] = None
		else:
			project.options['optionalMStoleranceType'] = self.normalize(self.choice_RunOptions_MS_type.GetString(idx))
		idx = self.choice_RunOptions_MSMS_type.GetSelection()
		if idx == wx.NOT_FOUND:
			project.options['optionalMSMStoleranceType'] = None
		else:
			project.options['optionalMSMStoleranceType'] = self.normalize(
				self.choice_RunOptions_MS_type.GetString(idx))
		########################
		project.options['isotopicCorrectionMS'] = self.checkBox_OptionsSection_isocorrect_ms.GetValue()
		project.options['isotopicCorrectionMSMS'] = self.checkBox_OptionsSection_isocorrect_msms.GetValue()
		project.options['complementMasterScan'] = self.checkBox_OptionsSection_complement_sc.GetValue()
		project.options['noHead'] = self.checkBox_OptionsSection_nohead.GetValue()
		project.options['compress'] = self.checkBox_OptionsSection_compress.GetValue()
		project.options['tabLimited'] = self.checkBox_OptionsSection_tabLimited.GetValue()
		project.options['dumpMasterScan'] = self.checkBox_OptionsSection_dumpMasterScan.GetValue()
		project.options['statistics'] = self.checkBox_generateStatistics.GetValue()
		project.options['noPermutations'] = self.checkBox_noPermutations.GetValue()
		project.options['mzXML'] = None # option key used in lpdxImport.py, substituted by 'dataType'
		# option key used in lpdxImport.py, substituted by 'dataType'
		project.options['spectraFormat'] = self.combo_ctrl_ImportDataSection.GetValue()

		for query in list(self.dictMFQLScripts.keys()):
			project.mfql[query] = self.dictMFQLScripts[query]

		return project

	def readOptionsRun(self):

		project = Project()

		project.options['masterScanImport'] = self.text_ctrl_OutputMasterScanSection.GetValue() # in expectation of a project file
		project.options['masterScanRun'] = self.text_ctrl_MasterScanSection.GetValue() # in expectation of a project file
		project.options['precursorMassShift'] = self.text_ctrl_SettingsSection_precursorMassShift.GetValue()
		project.options['precursorMassShiftOrbi'] = self.text_ctrl_SettingsSection_precursorMassShiftOrbi.GetValue()
		project.options['alignmentMethodMS'] = self.alignmentSetting.alignmentMethodsMS_intern[self.alignmentSetting.radioBox_ms_alignment.GetSelection()]
		project.options['alignmentMethodMSMS'] = self.alignmentSetting.alignmentMethodsMSMS_intern[self.alignmentSetting.radioBox_msms_alignment.GetSelection()]
		project.options['scanAveragingMethod'] = self.alignmentSetting.scanAveragingMethods_intern[self.alignmentSetting.radioBox_scanAveraging.GetSelection()]
		project.options['isotopicCorrection_MSMS'] =  self.debugSetting.checkBox_IsotopicCorrection_MSMS.GetValue() # here starts the Set debugging Options from the Debug menu
		project.options['removeIsotopes'] = self.debugSetting.checkBox_removeIsotopes.GetValue()
		project.options['isotopesInMasterScan'] = self.debugSetting.checkBox_isotopesInMasterscan.GetValue()
		project.options['monoisotopicCorrection'] = self.debugSetting.checkBox_monoisotopicCorrection.GetValue()
		project.options['relativeIntensity'] = self.debugSetting.checkBox_relativeIntensity.GetValue()
		project.options['logMemory'] =  self.debugSetting.checkBox_MemoryLog.GetValue() # here starts the Set debugging Options from the Debug menu
		project.options['intensityCorrection'] = self.outputOptionSetting.checkBox_correctIntensities.GetValue() # here starts the output options menu
		project.options['intensityCorrectionPrecursor'] = self.outputOptionSetting.text_ctrl_precursor.GetValue()
		project.options['intensityCorrectionFragment'] = self.outputOptionSetting.text_ctrl_fragment.GetValue()
		project.options['masterScanInSQL'] = self.outputOptionSetting.checkBox_masterScanInSQL.GetValue()
		project.options['sumFattyAcids'] = self.outputOptionSetting.checkBox_sumFattyAcids.GetValue()
		project.options['settingsPrefix'] = self.outputOptionSetting.checkBox_settingsPrefix.GetValue()
		project.options['resultFile'] = self.text_ctrl_OutputSection.GetValue() # here starts the RUN panel
		project.options['optionalMStolerance'] = self.text_ctrl_RunOptions_MS.GetValue()
		project.options['optionalMSMStolerance'] = self.text_ctrl_RunOptions_MSMS.GetValue()
		project.options['optionalMStoleranceType'] = self.choice_RunOptions_MS_type.GetString(self.choice_RunOptions_MS_type.GetSelection())
		project.options['optionalMSMStoleranceType'] = self.choice_RunOptions_MSMS_type.GetString(self.choice_RunOptions_MSMS_type.GetSelection())
		project.options['isotopicCorrectionMS'] = self.checkBox_OptionsSection_isocorrect_ms.GetValue()
		project.options['isotopicCorrectionMSMS'] = self.checkBox_OptionsSection_isocorrect_msms.GetValue()
		project.options['complementMasterScan'] = self.checkBox_OptionsSection_complement_sc.GetValue()
		project.options['noHead'] = self.checkBox_OptionsSection_nohead.GetValue()
		project.options['compress'] = self.checkBox_OptionsSection_compress.GetValue()
		project.options['tabLimited'] = self.checkBox_OptionsSection_tabLimited.GetValue()
		project.options['dumpMasterScan'] = self.checkBox_OptionsSection_dumpMasterScan.GetValue()
		project.options['statistics'] = self.checkBox_generateStatistics.GetValue()
		project.options['noPermutations'] = self.checkBox_noPermutations.GetValue()
		project.options['mzXML'] = None # option key used in lpdxImport.py, substituted by 'dataType'
		# option key used in lpdxImport.py, substituted by 'dataType'
		project.options['spectraFormat'] = self.combo_ctrl_ImportDataSection.GetValue()

		for query in list(self.dictMFQLScripts.keys()):
			project.mfql[query] = self.dictMFQLScripts[query]

		return project

	def loadProject(self, filename):
		self.OnMenuProjectLoad(None, pFile = filename)


	def OnMenuProjectLoad(self, evt, pFile=''):

		project = GUIProject()

		# load the project file
		if pFile == '':
			dlg = wx.FileDialog(
				wx.GetApp().frame,
				"Load the project file",
				style=wx.DD_DEFAULT_STYLE | wx.FD_OPEN,
				defaultFile=''
			)
			dlg.SetWildcard("*.lxp files|*.lxp")

			if dlg.ShowModal() == wx.ID_OK:
				self.projectFile = dlg.GetPath()
			else:
				return None
		else:
			self.projectFile = pFile

		# initialize the project options
		project.load(self.projectFile)

		# project options (already parsed/typed)
		options = project.getOptions().getOrdinary()

		try:
			is_batch_checked = self.checkBox_BatchMode.IsChecked()

			# -----------------------------
			# BATCH MODE
			# -----------------------------
			if is_batch_checked:
				print("Loading project in BATCH MODE----------------GUI-------###############################")

				self.project_loaded_for_batch = True

				# open and load ini first (populates choice with INI SECTION NAMES)
				if options.get('ini'):
					self.text_ctrl_OutputMasterScanSection.SetValue(options['ini'])
					self.filePath_LoadIni_batch = options['ini']
					self.OnBrowse_LoadIni_Body(self.filePath_LoadIni_batch)

					# "setting" is stored as SECTION NAME from now on.
					# For legacy projects where setting is numeric, try mapping id->name if available.
					loaded = options.get('setting', '')
					s = '' if loaded is None else str(loaded).strip()

					if s.isdigit():
						# OLD PROJECT: treat as index
						idx = int(s)
						if 0 <= idx < self.choice_SelectSettingSection_batch.GetCount():
							self.choice_SelectSettingSection_batch.SetSelection(idx)
							self.currentConfiguration = self.choice_SelectSettingSection_batch.GetString(idx)
							self.collectSettings(self.currentConfiguration)  # important for batch
						else:
							print("WARNING: legacy batch setting index out of range:", idx)
					else:
						# NEW PROJECT: treat as section name
						idx = self.choice_SelectSettingSection_batch.FindString(s)
						if idx != wx.NOT_FOUND:
							self.choice_SelectSettingSection_batch.SetSelection(idx)
							self.currentConfiguration = s
							self.collectSettings(s)
						else:
							print("WARNING: batch setting name not found:", s)


				# other batch UI fields
				self.text_ctrl_ImportDataSection.SetValue(options.get('importDir', ''))
				self.combo_ctrl_ImportDataSection.SetValue(options.get('dataType', ''))

				# MFQL dirs in listbox (from project mfql paths)
				self.dictMFQLScripts = project.mfql
				unique_dirs = sorted({os.path.dirname(path) for path in self.dictMFQLScripts.values()})

				self.listbox_MFQL_batch.Clear()
				self.listbox_MFQL_batch.InsertItems(unique_dirs, 0)

			# -----------------------------
			# NORMAL MODE
			# -----------------------------
			else:
				self.project_loaded_for_batch = False
				print(options)
				# open and load ini first (populates choice with INI SECTION NAMES)
				if options.get('ini'):
					self.text_ctrl_LoadIniSection.SetValue(options['ini'])
					self.filePath_LoadIni = options['ini']
					self.OnBrowse_LoadIni_Body(self.filePath_LoadIni)

					# "setting" is stored as SECTION NAME from now on.
					# For legacy projects where setting is numeric, try mapping id->name if available.
					loaded = options.get('setting', '')
					s = '' if loaded is None else str(loaded).strip()

					if s.isdigit():
						# OLD PROJECT: treat as index
						idx = int(s)
						if 0 <= idx < self.choice_SelectSettingSection.GetCount():
							self.choice_SelectSettingSection.SetSelection(idx)
							self.currentConfiguration = self.choice_SelectSettingSection.GetString(idx)
							self.fillConfiguration(self.currentConfiguration)
						else:
							print("WARNING: legacy setting index out of range:", idx)
					else:
						# NEW PROJECT: treat as section name
						idx = self.choice_SelectSettingSection.FindString(s)
						if idx != wx.NOT_FOUND:
							self.choice_SelectSettingSection.SetSelection(idx)
							self.currentConfiguration = s
							self.fillConfiguration(s)
						else:
							print("WARNING: setting name not found:", s)


				# keep the rest of your UI population as-is
				self.text_ctrl_ImportDataSection.SetValue(options['importDir'])
				self.text_ctrl_OutputMasterScanSection.SetValue(options['masterScanImport'])
				self.text_ctrl_MasterScanSection.SetValue(options['masterScanRun'])

				self.combo_ctrl_ImportDataSection.SetValue(options['dataType'])
				self.text_ctrl_SettingsSection_selectionWindow.SetValue(options['selectionWindow'])
				self.text_ctrl_SettingsSection_timerange1.SetValue(options['timerange'][0])
				self.text_ctrl_SettingsSection_timerange2.SetValue(options['timerange'][1])
				self.text_ctrl_SettingsSection_calibration_ms.SetValue(','.join(options['MScalibration']))
				self.text_ctrl_SettingsSection_calibration_msms.SetValue(','.join(options['MSMScalibration']))
				self.text_ctrl_SettingsSection_filter_ms.SetValue(options['MSfilter'])
				self.text_ctrl_SettingsSection_filter_msms.SetValue(options['MSMSfilter'])
				self.text_ctrl_SettingsSection_massrange_ms1.SetValue(options['MSmassrange'][0])
				self.text_ctrl_SettingsSection_massrange_ms2.SetValue(options['MSmassrange'][1])
				self.text_ctrl_SettingsSection_massrange_msms1.SetValue(options['MSMSmassrange'][0])
				self.text_ctrl_SettingsSection_massrange_msms2.SetValue(options['MSMSmassrange'][1])
				self.text_ctrl_SettingsSection_tolerance_ms.SetValue((options['MStolerance']))
				self.text_ctrl_SettingsSection_tolerance_msms.SetValue((options['MSMStolerance']))
				self.choice_SettingsSection_tolerance_ms.SetStringSelection((options['MStoleranceType']))
				self.choice_SettingsSection_tolerance_msms.SetStringSelection((options['MSMStoleranceType']))
				self.text_ctrl_SettingsSection_resolution_ms.SetValue((options['MSresolution']))
				self.text_ctrl_SettingsSection_resolution_msms.SetValue((options['MSMSresolution']))
				self.text_ctrl_SettingsSection_resDelta_ms.SetValue((options['MSresolutionDelta']))
				self.text_ctrl_SettingsSection_resDelta_msms.SetValue((options['MSMSresolutionDelta']))
				self.text_ctrl_SettingsSection_threshold_ms.SetValue((options['MSthreshold']))
				self.text_ctrl_SettingsSection_threshold_msms.SetValue((options['MSMSthreshold']))
				self.choice_SettingsSection_threshold_ms.SetStringSelection(options['MSthresholdType'])
				self.choice_SettingsSection_threshold_msms.SetStringSelection(options['MSMSthresholdType'])
				self.text_ctrl_SettingsSection_occupationThr_ms.SetValue((options['MSminOccupation']))
				self.text_ctrl_SettingsSection_occupationThr_msms.SetValue((options['MSMSminOccupation']))
				self.text_ctrl_SettingsSection_precursorMassShift.SetValue((options['precursorMassShift']))
				self.text_ctrl_SettingsSection_precursorMassShiftOrbi.SetValue((options['precursorMassShiftOrbi']))
				self.alignmentSetting.radioBox_ms_alignment.SetSelection(
					self.alignmentSetting.alignmentMethodsMS_intern.index(options['alignmentMethodMS'])
				)
				self.alignmentSetting.radioBox_msms_alignment.SetSelection(
					self.alignmentSetting.alignmentMethodsMSMS_intern.index(options['alignmentMethodMSMS'])
				)
				self.alignmentSetting.radioBox_scanAveraging.SetSelection(
					self.alignmentSetting.scanAveragingMethods_intern.index(options['scanAveragingMethod'])
				)

				# Debug menu options
				self.debugSetting.checkBox_IsotopicCorrection_MSMS.SetValue(strToBool(options['isotopicCorrection_MSMS']))
				self.debugSetting.OnCheckIsotopicCorrection_MSMS(None)
				self.debugSetting.checkBox_removeIsotopes.SetValue(strToBool(options['removeIsotopes']))
				self.debugSetting.OnCheckRemoveIsotopes(None)
				self.debugSetting.checkBox_isotopesInMasterscan.SetValue(strToBool(options['isotopesInMasterScan']))
				self.debugSetting.OnCheckIsotopesInMasterScan(None)
				self.debugSetting.checkBox_monoisotopicCorrection.SetValue(strToBool(options['monoisotopicCorrection']))
				self.debugSetting.OnCheckMonoisotopicCorrection(None)
				self.debugSetting.checkBox_relativeIntensity.SetValue(strToBool(options['relativeIntensity']))
				self.debugSetting.OnCheckRelativeIntensity(None)
				self.debugSetting.checkBox_MemoryLog.SetValue(strToBool(options['logMemory']))

				# Output options
				self.outputOptionSetting.checkBox_correctIntensities.SetValue(strToBool(options['intensityCorrection']))
				self.outputOptionSetting.text_ctrl_precursor.SetValue(options['intensityCorrectionPrecursor'])
				self.outputOptionSetting.text_ctrl_fragment.SetValue(options['intensityCorrectionFragment'])
				self.outputOptionSetting.checkBox_masterScanInSQL.SetValue(strToBool(options['masterScanInSQL']))
				self.outputOptionSetting.checkBox_sumFattyAcids.SetValue(strToBool(options['sumFattyAcids']))
				self.outputOptionSetting.checkBox_settingsPrefix.SetValue(strToBool(options['settingsPrefix']))

				# RUN panel
				self.text_ctrl_OutputSection.SetValue(options['resultFile'])
				self.text_ctrl_RunOptions_MS.SetValue(options['optionalMStolerance'])
				self.text_ctrl_RunOptions_MSMS.SetValue(options['optionalMSMStolerance'])
				self.choice_RunOptions_MS_type.GetString(
					self.choice_RunOptions_MS_type.SetStringSelection(options['optionalMStoleranceType'])
				)
				self.choice_RunOptions_MSMS_type.GetString(
					self.choice_RunOptions_MSMS_type.SetStringSelection(options['optionalMSMStoleranceType'])
				)
				self.checkBox_OptionsSection_isocorrect_ms.SetValue(strToBool(options['isotopicCorrectionMS']))
				self.checkBox_OptionsSection_isocorrect_msms.SetValue(strToBool(options['isotopicCorrectionMSMS']))
				self.checkBox_OptionsSection_complement_sc.SetValue(strToBool(options['complementMasterScan']))
				self.checkBox_OptionsSection_nohead.SetValue(strToBool(options['noHead']))
				self.checkBox_OptionsSection_compress.SetValue(strToBool(options['compress']))
				self.checkBox_OptionsSection_tabLimited.SetValue(strToBool(options['tabLimited']))
				self.checkBox_OptionsSection_dumpMasterScan.SetValue(strToBool(options['dumpMasterScan']))
				self.checkBox_generateStatistics.SetValue(strToBool(options['statistics']))
				self.checkBox_noPermutations.SetValue(strToBool(options['noPermutations']))

		except (TypeError, AttributeError):
			pass

		# set local variables
		self.dictMFQLScripts = project.mfql
		self.list_box_1.Set(list(self.dictMFQLScripts.keys()))
		self.filePath_Dump = options.get('dumpMasterScanFile')

		# if a setting was given we make it our current config (NORMAL MODE)
		if hasattr(self, "listConfigurations") and len(self.listConfigurations) > 0:
			sel = self.choice_SelectSettingSection.GetSelection()
			if sel != wx.NOT_FOUND:
				self.currentConfiguration = self.listConfigurations[sel]

		if self.currentConfiguration != "":
			self.OnSettingsSaved()

		return None


	def OnMenuDebugWin(self, evt):

		if not self.debugOpen:
			#self.debug.Center()
			self.debug.Show(True)
			self.debugOpen = True
		else:
			self.debug.Show(False)
			self.debugOpen = False

	def OnMenuDebugSet(self, evt):

		self.debugSetting.Show(True)

	# def OnMenuAlignmentSet(self, evt):
	#
	# 	self.alignmentSetting.Show(True)

	def OnMenuOutputOptions(self, evt):

		self.outputOptionSetting.Show(True)

	def OnMenuLipidXDocumentation(self, evt):

		webbrowser.open('https://lifs-tools.org/wiki/index.php?title=Main_Page')

	def OnMenuMFQLTutorial(self, evt):

		webbrowser.open('https://lifs-tools.org/wiki/index.php/LipidXplorer_MFQL#A_short_tutorial')

	def OnMenuMFQLReference(self, evt):

		webbrowser.open('https://lifs-tools.org/wiki/index.php/Main_Page#Citing_LipidXplorer')

	def OnMenuHelpImportSettings(self, evt):

		webbrowser.open('https://lifs-tools.org/wiki/index.php?title=LipidXplorer_Reference#Importing_mass_spectra_into_LipidXplorer')

	def OnMenuHelpRun(self, evt):

		webbrowser.open('https://lifs-tools.org/wiki/index.php?title=LipidXplorer_Reference#Run_queries_on_the_MasterScan')

	def OnMenuHelpMSTools(self, evt):

		webbrowser.open('https://lifs-tools.org/wiki/index.php?title=LipidXplorer_Reference#The_MS-Tools_panel')

	def OnMenuAbout(self, evt):

		webbrowser.open('https://lifs-tools.org/lipidxplorer.html')

	def OnTextEnter(self, evt):

		if evt.GetId() == self.text_ctrl_ImportDataSection.GetId():
			self.OnBrowse_ImportData_Body(self.text_ctrl_ImportDataSection.GetValue())
		if evt.GetId() == self.text_ctrl_MasterScanSection.GetId():
			self.OnBrowse_MasterScan_Body(self.text_ctrl_MasterScanSection.GetValue())
		if evt.GetId() == self.text_ctrl_OutputMasterScanSection.GetId():
			self.text_ctrl_MasterScanSection.SetValue(self.text_ctrl_OutputMasterScanSection.GetValue())

	def OnText(self, evt):

		if not self.isChangedAndNotSavedCurrentConfiguration:
			if evt.GetId() == self.text_ctrl_SettingsSection_timerange1.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_occupationThr_ms.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_occupationThr_msms.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_threshold_ms.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_threshold_msms.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_timerange1.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_timerange2.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_massrange_ms1.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_massrange_ms2.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_massrange_msms1.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_massrange_msms2.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_resolution_ms.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_resolution_msms.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_resDelta_ms.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_resDelta_msms.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_calibration_ms.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_calibration_msms.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_filter_ms.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_filter_msms.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_tolerance_ms.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_tolerance_msms.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_selectionWindow.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_precursorMassShift.GetId() or\
				evt.GetId() == self.text_ctrl_SettingsSection_precursorMassShiftOrbi.GetId():
				#print("resDelta_ms changed to:", self.text_ctrl_SettingsSection_resDelta_ms.GetValue()) #### ballal
				self.OnSettingsChange()

	def OnStcChange(self, evt):

		for key in list(self.dict_text_ctrl.keys()):
			if evt.GetId() == self.dict_text_ctrl[key].GetId():

				# find right page
				for i in range(self.notebook_1.GetPageCount()):
					if self.notebook_1.GetPage(i) == self.dict_text_ctrl[key].GetParent():
						self.dict_isChangedAndNotSavedMfqlFile[key] = True
						if key in self.dict_button_save:
							# this is normal gray: (230, 224, 218, 255)
							if not self.dict_button_save[key].GetBackgroundColour() == (250, 80, 80, 215):
								self.dict_button_save[key].SetBackgroundColour((250, 80, 80, 215))

	def OnCloseApp(self, evt):

		dialog = wx.MessageDialog(self, message="Are you sure you want to quit?", caption="Quit LipidXplorer", style=wx.YES_NO,
								  pos=wx.DefaultPosition)
		response = dialog.ShowModal()

		if response != wx.ID_YES:
			evt.StopPropagation()
			return

		for key in list(self.dict_text_ctrl.keys()):
			if self.dict_isChangedAndNotSavedMfqlFile[key]:
				dlg = wx.MessageDialog(self, "Modified query '%s' is not saved. Save it?" % key, "Ups..",
					wx.YES|wx.NO|wx.ICON_HAND)
				if dlg.ShowModal() == wx.ID_YES:
					with open(self.dictMFQLScripts[key], 'w') as mfqlFile:
						self.dict_mfqlFile[key] = mfqlFile
						mfqlFile.write(self.dict_text_ctrl[key].GetText())

		if wx.GetApp().frame.debugOpen:
			wx.GetApp().frame.OnMenuDebugWin(None)

		for tlw in wx.GetTopLevelWindows():
			tlw.Destroy()

		self.Destroy()

		if playSound:
			wx.Sound.Stop()
			wx.Sound('../pics/CloseApp.wav').Play()

	def handleSyntaxErrorException(self):

		evt = wxStdOut(text = '')#v.value)
		if not wx.GetApp().frame.debugOpen:
			wx.GetApp().frame.OnMenuDebugWin(None)
		wx.PostEvent(wx.GetApp().frame, evt)

		(excName, excArgs, excTb, exc) = formatExceptionInfo()

		if exc.p_value:
			htmlText = '''
			<html><head></head><body>
			<font color="#800000"><h3>Syntax Error</h3></font>
			'%s'
			<p>
			<table>
				<tr><td>file name:</td><td>%s</td></tr>
				<tr><td>line number:</td><td>%s</td></tr>
			</table>
			</p>
			</body></html>
			''' % (exc.p_value, exc.fileName, exc.lineno)
		else:
			htmlText = '''
			<html><head></head><body>
			<font color="#800000"><h3>Syntax Error</h3></font>
			<p>
			<table>
				<tr><td>file name:</td><td>%s</td></tr>
				<tr><td>line number:</td><td>%s</td></tr>
			</table>
			</p>
			</body></html>
			''' % (exc.fileName, exc.lineno)

		dlg = MyErrorDialog(wx.GetApp().frame, -1, "Syntax Error", htmlText)
		if dlg.ShowModal() == wx.ID_OK:
			dlg.Destroy()

	def handleLogicErrorExcept(self):

		evt = wxStdOut(text = '')#v.value)
		if not wx.GetApp().frame.debugOpen:
			wx.GetApp().frame.OnMenuDebugWin(None)
		wx.PostEvent(wx.GetApp().frame, evt)

		(excName, excArgs, excTb, exc) = formatExceptionInfo()
		dlg = wx.MessageDialog(wx.GetApp().frame, "%s" % exc, "LOGICAL ERROR", wx.OK|wx.ICON_ERROR)
		if dlg.ShowModal() == wx.ID_OK:
			dlg.Destroy()

	def handleLipidXException(self):

		evt = wxStdOut(text = '')#v.value)
		if not wx.GetApp().frame.debugOpen:
			wx.GetApp().frame.OnMenuDebugWin(None)
		wx.PostEvent(wx.GetApp().frame, evt)

		(excName, excArgs, excTb, exc) = formatExceptionInfo()

		htmlText = '''
		<html><head></head><body>
		<font color="#800000"><h3>Error</h3></font>
		'%s'
		<p>
		'%s'
		</p>
		</body></html>
		''' % (exc.head, exc.body)

		dlg = MyErrorDialog(wx.GetApp().frame, -1, "Syntax Error", htmlText)
		if dlg.ShowModal() == wx.ID_OK:
			dlg.Destroy()

		# old
		#evt = wxStdOut(text = '')#v.value)
		#if not wx.GetApp().frame.debugOpen:
		#	wx.GetApp().frame.OnMenuDebugWin(None)
		#wx.PostEvent(wx.GetApp().frame, evt)

		#(excName, excArgs, excTb, exc) = formatExceptionInfo()
		#dlg = wx.MessageDialog(wx.GetApp().frame, "%s" % exc, "ERROR", wx.OK|wx.ICON_ERROR)
		#if dlg.ShowModal() == wx.ID_OK:
		#	dlg.Destroy()

	def handleImportException(self):

		evt = wxStdOut(text = '')#v.value)
		if not wx.GetApp().frame.debugOpen:
			wx.GetApp().frame.OnMenuDebugWin(None)
		wx.PostEvent(wx.GetApp().frame, evt)

		(excName, excArgs, excTb, exc) = formatExceptionInfo()
		dlg = wx.MessageDialog(wx.GetApp().frame, "%s" % exc, "IMPORT ERROR", wx.OK|wx.ICON_ERROR)
		if dlg.ShowModal() == wx.ID_OK:
			dlg.Destroy()

	def handleException(self):

		traceback.print_tb(sys.exc_info()[2])
		evt = wxStdOut(text = '')
		if not wx.GetApp().frame.debugOpen:
			wx.GetApp().frame.OnMenuDebugWin(None)
		wx.PostEvent(wx.GetApp().frame, evt)
		(excName, excArgs, excTb, exc) = formatExceptionInfo()
		print(excName, exc)

		text = "The following error occured:\n\n"
		text += "** %s : %s **\n\n\n" % (excName, exc)
		text += "If you think that this a bug in the software you can send\na bug report to the us.\n"
		text += "Do you want to generate the bug report?"
		dlg = wx.MessageDialog(wx.GetApp().frame, text, "ERROR", style=wx.YES_NO|wx.CANCEL|wx.NO_DEFAULT)
		r = dlg.ShowModal()
		if r == wx.ID_YES:

			dlg = wx.MessageDialog(wx.GetApp().frame, "Please store the bugReport.html and send it to lifs-support@isas.de", \
					"ERROR", style=wx.OK)
			if dlg.ShowModal() == wx.ID_OK:
				dlg.Destroy()

			strBugReport = """
			<html><head></head><body>
			<h3>%s</h3>
			<h3>%s</h3>
			<h3>%s</h3>
			<p><tt>
			""" % (sys.version, excName, exc)
			for i in excTb:
				strBugReport += "%s<br>" % i
			strBugReport += "</tt></p><br>"
			strBugReport += "%s" % wx.GetApp().frame.genBugReportHTML()
			strBugReport += "</body></html>"

			dlg = wx.FileDialog(wx.GetApp().frame, "Specify the site for the bugReport.html",
				style=wx.DD_DEFAULT_STYLE|wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT,
				defaultFile = "bugReport.html")
			dlg.SetWildcard("*.html files|*.html")

			if dlg.ShowModal() == wx.ID_OK:
				d = dlg.GetPath()
				with open(d, 'w') as f:
					f.write(strBugReport)
				print(d)

		else:
			dlg.Destroy()

			#dlg = wx.MessageDialog(wx.GetApp().frame,"%s: %s" % (excName, exc), "Error.", wx.OK|wx.ICON_ERROR)
			#if dlg.ShowModal() == wx.ID_OK:
			#	dlg.Destroy()

		evt = wxWorkerDone(msg = callable.__name__)
		wx.PostEvent(wx.GetApp().frame, evt)

	def startConvertWiff(self):

		if playSound:
			wx.Sound('../pics/PressButton.wav').Play()

		wiffIn = wiffOut = self.filePath_WiffIn

		if os.path.exists(wiffIn):
			if os.path.exists(wiffOut):

				# initialize to fail
				exitCode = -1

				max = 0
				count = 0
				for root, dir, files in os.walk(wiffIn):
					max = len(files)

				thinking = wx.ProgressDialog("Thinking ...", "Thinking ...", max, self, wx.PD_AUTO_HIDE|wx.ICON_EXCLAMATION|wx.PD_SMOOTH)

				for root, dir, files in os.walk(wiffIn):
					for f in files:
						if re.match(r'.*\.wiff', f, re.IGNORECASE):

							# select msconvert (MC) or ReAdW
							if self.flagMC: # msconvert
								if self.flagCentroid:
									strStartWiff = 'msconvert-with-centroization.bat "%s" "%s"' % (os.path.join(root, f), wiffOut)
								else:
									strStartWiff = 'msconvert-without-centroization.bat "%s" "%s"' % (os.path.join(root, f), wiffOut)
							else: # readw
								if self.flagCentroid:
									strCentroid = '-c -c1'
								else:
									strCentroid = ''
								strStartWiff = 'mzWiff -FPC1 %s --mzXML "%s"' % (strCentroid, os.path.join(root, f))#s, wiffOut)

							print(strStartWiff)
							exitCode = os.system(strStartWiff)
						count += 1
						thinking.Update(count)

				thinking.Destroy()
				#info = wx.ScrolledMessageDialog(self, msg, caption, pos, size, style)

				if exitCode == 0:
					#dlg = wx.MessageDialog(self, "Wiff files successfully converted!", "Success", wx.OK|wx.ICON_INFORMATION)
					#if dlg.ShowModal() == wx.ID_OK:
					#	dlg.Destroy()
					return "WIFF" #True
				else:
					dlg = wx.MessageDialog(self, "Problems with Wiff file conversion!", "Failed", wx.OK|wx.ICON_INFORMATION)
					if dlg.ShowModal() == wx.ID_OK:
						dlg.Destroy()
						return False
			else:
				dlg = wx.MessageDialog(self, "The path '%s' does not exist!" % wiffOut, "Error", wx.OK|wx.ICON_HAND)
				if dlg.ShowModal() == wx.ID_OK:
					dlg.Destroy()
					return False
		else:
			dlg = wx.MessageDialog(self, "The path '%s' does not exist!" % wiffIn, "Error", wx.OK|wx.ICON_HAND)
			if dlg.ShowModal() == wx.ID_OK:
				dlg.Destroy()
				return False

	def startConvertRaw(self):

		if playSound:
			wx.Sound('../pics/PressButton.wav').Play()

		rawIn = rawOut = self.filePath_RawIn

		if os.path.exists(rawIn):
			if os.path.exists(rawOut):

				max = 0
				count = 0
				for root, dir, files in os.walk(rawIn):
					max = len(files)

				thinking = wx.ProgressDialog("Thinking ...", "Converting *.raw to *.mzXML", max, self, wx.PD_AUTO_HIDE|wx.PD_SMOOTH)

				for root, dir, files in os.walk(rawIn):
					for f in files:
						if re.match(r'.*\.raw', f, re.IGNORECASE):
							fout = f.split('.')[0] + '.mzXML'
							fout = rawOut + os.sep + fout

							# select msconvert (MC) or ReAdW
							if self.flagMC: # msconvert
								if self.flagCentroid:
									strStartRaw = 'msconvert-with-centroization.bat "%s" "%s"' % (os.path.join(root, f), rawOut)
								else:
									strStartRaw = 'msconvert-without-centroization.bat "%s" "%s"' % (os.path.join(root, f), rawOut)
							else: # readw
								if self.flagCentroid:
									strCentroid = '-c' # for ReAdW.exe
								else:
									strCentroid = ''
								strStartRaw = 'readw --precursorFromFilterLine --mzXML %s "%s" "%s"' % (strCentroid, os.path.join(root, f), fout)

							print(strStartRaw)
							exitCode = os.system(strStartRaw)
						count += 1
						thinking.Update(count)

				thinking.Destroy()

				if exitCode == 0:
					#dlg = wx.MessageDialog(self, "Raw files successfully converted!", "Success", wx.OK|wx.ICON_INFORMATION)
					#if dlg.ShowModal() == wx.ID_OK:
					#	dlg.Destroy()
					return "RAW" #True
				else:
					dlg = wx.MessageDialog(self, "Problems with Raw file conversion!", "Failed", wx.OK|wx.ICON_INFORMATION)
					if dlg.ShowModal() == wx.ID_OK:
						dlg.Destroy()
						return None
			else:
				dlg = wx.MessageDialog(self, "The path '%s' does not exist!" % rawOut, "Error", wx.OK|wx.ICON_HAND)
				if dlg.ShowModal() == wx.ID_OK:
					dlg.Destroy()
					return None
		else:
			dlg = wx.MessageDialog(self, "The path '%s' does not exist!" % rawIn, "Error", wx.OK|wx.ICON_HAND)
			if dlg.ShowModal() == wx.ID_OK:
				dlg.Destroy()
				return None

	def OnBrowse_ImportData(self, evt):

		# open directory with *.dta/*mzXML content
		dlg = wx.DirDialog(self, "Choose a directory", style=wx.DD_DEFAULT_STYLE|wx.DD_DIR_MUST_EXIST)
		#dlg.SetPath(os.getcwd())

		if dlg.ShowModal() == wx.ID_OK:
			#self.filePath_ImportData = relativePath(dlg.GetPath())
			self.filePath_ImportData = dlg.GetPath()
			if not os.path.exists(self.filePath_ImportData):
				raise LipidXException

		self.OnBrowse_ImportData_Body(self.filePath_ImportData)

	def OnBrowse_ImportData_Body(self, filePath):

		if not os.path.exists(filePath):
			dlg = wx.MessageDialog(self, "The path '%s' does not exist!" % filePath, "Error", wx.OK|wx.ICON_HAND)
			if dlg.ShowModal() == wx.ID_OK:
				dlg.Destroy()
				return None

###################### Ballal ##########################

		is_batch_checked = self.checkBox_BatchMode.IsChecked()

		if is_batch_checked:
			self.text_ctrl_ImportDataSection.SetValue(filePath)
		else:
			strMasterScan = filePath + os.sep + filePath.split(os.sep)[-1] + '.sc'
			strOutputFile = filePath + os.sep + filePath.split(os.sep)[-1] + '-out.csv'
			self.filePath_Dump = filePath + os.sep + filePath.split(os.sep)[-1] + '-dump.csv'
	
			self.text_ctrl_MasterScanSection.SetValue(strMasterScan)
			self.text_ctrl_OutputMasterScanSection.SetValue(strMasterScan)
			self.text_ctrl_OutputSection.SetValue(strOutputFile)
			self.text_ctrl_ImportDataSection.SetValue(filePath)
   ##########################################

	def OnBrowse_OutputMasterScan(self, evt):


################ Ballal ####################
		is_batch_checked = self.checkBox_BatchMode.IsChecked()

		if is_batch_checked:
					# open directory with *.dta/*mzXML content
			dlg = wx.FileDialog(self, "Choose a *.ini file with settings", style=wx.DD_DEFAULT_STYLE|wx.FD_OPEN)
			dlg.SetWildcard("*.ini files|*.ini")

			if dlg.ShowModal() == wx.ID_OK:
				#self.filePath_LoadIni = relativePath(dlg.GetPath())
				self.filePath_LoadIni = dlg.GetPath()

			self.OnBrowse_LoadIni_Body(self.filePath_LoadIni)

			dlg.Destroy()
			self.text_ctrl_OutputMasterScanSection.SetValue(self.filePath_LoadIni)	
		else:
			# open directory with *.dta/*mzXML content
			dlg = wx.FileDialog(self, "Choose a MasterScan *.sc file", style=wx.DD_DEFAULT_STYLE|wx.FD_SAVE)
			dlg.SetWildcard("*.sc files|*.sc")

			if dlg.ShowModal() == wx.ID_OK:
				self.filePath_MasterScan = dlg.GetPath()
				if not re.match(r'.*\.sc', self.filePath_MasterScan):
					s = self.filePath_MasterScan.split('.')
					if len(s) == 1:
						self.filePath_MasterScan += '.sc'
					else:
						self.filePath_MasterScan = ''
					for i in s[:-1]:
						self.filePath_MasterScan += '%s.' % i
					self.filePath_MasterScan += 'sc'

			dlg.Destroy()
			self.text_ctrl_OutputMasterScanSection.SetValue(self.filePath_MasterScan)
   
   ##################### Ballal ##########################
   
	def on_notebook_page_changing(self, event):
		"""
		Prevent navigation to disabled pages, but still allow leaving them.
		Works reliably on all platforms by determining the target tab manually.
		"""
		notebook = self.notebook_1

		# Determine target page using mouse position (reliable even on Windows)
		x, y = wx.GetMousePosition()
		x, y = notebook.ScreenToClient((x, y))
		tab_index, flags = notebook.HitTest((x, y))

		if tab_index == wx.NOT_FOUND:
			# Fallback: try normal method
			tab_index = event.GetSelection()

		# If still invalid, do nothing
		if tab_index == wx.NOT_FOUND:
			event.Skip()
			return

		page_name = notebook.GetPageText(tab_index)
		#print(f"Attempting to switch to page: {page_name}")

		# Block switching to disabled pages
		if page_name in self.disabled_pages:
			wx.Bell()
			wx.MessageBox(
				f"The '{page_name}' page is disabled when batch mode is active.",
				"Page Disabled",
				wx.OK | wx.ICON_INFORMATION,
			)
			event.Veto()
		else:
			event.Skip()


   
   
   
	def OnBrowse_MFQL_batch(self, evt):
		dlg = wx.DirDialog(
			self,
			"Choose a directory with MFQL files",
			style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST
		)
		#dlg.SetPath(os.getcwd())

		try:
			if dlg.ShowModal() != wx.ID_OK:
				return

			selected_dir = dlg.GetPath()

			# Check if folder contains at least one .mfql file
			has_mfql = any(
				f.lower().endswith(".mfql")
				for f in os.listdir(selected_dir)
			)

			if not has_mfql:
				wx.MessageBox("No .mfql files found in this directory.", "Info",
							wx.OK | wx.ICON_INFORMATION)
				return

			# Add if not already present
			existing = set(self.listbox_MFQL_batch.GetItems())
			if selected_dir not in existing:
				self.listbox_MFQL_batch.Append(selected_dir)

		finally:
			dlg.Destroy()

	def OnDelete_MFQL_batch(self, evt):
		selections = list(self.listbox_MFQL_batch.GetSelections())  # indices
		if not selections:
			wx.MessageBox("Select one or more directories to delete.", "Info",
						wx.OK | wx.ICON_INFORMATION)
			return

		# Delete from bottom to top to avoid index shifting
		for idx in reversed(selections):
			self.listbox_MFQL_batch.Delete(idx)



	def OnConfigurationChoice_batch(self, evt):

		self.currentConfiguration = evt.GetString()
		self.collectSettings(self.currentConfiguration)# self.optsImport is filled there
		print(f"Configuration '{self.currentConfiguration}' selected. Options loaded into self.optsImport: {self.optsImport}")
  


	def readOptions_batch(self):
		"""
		Build a Project object using options loaded from a configuration (self.optsImport)
		instead of reading from GUI controls.
		"""
		project = Project()

		# ---- Load values from imported configuration ----
		opts = self.optsImport
		print("-------------------------------------------------------------------------",opts)
		# Defensive: make sure it's a dict
		if not isinstance(opts, dict):
			print("self.optsImport is not a dictionary.")
			return None

		# Example: directly assign each key to project.options
		# (you can choose which to include or override defaults)
		for key, value in opts.items():
			project.options[key] = value

		# ---- Fill any defaults or GUI-linked options not in optsImport ----
		project.options['importDir'] = self.text_ctrl_ImportDataSection.GetValue()
		project.options['dataType'] = self.combo_ctrl_ImportDataSection.GetValue()
		project.options['ini'] = self.text_ctrl_OutputMasterScanSection.GetValue()
		project.options['setting'] = self.currentConfiguration
  
		#project.options.setdefault('resultFile', self.text_ctrl_OutputSection.GetValue())

		# You can also set placeholders for fields that don’t exist in optsImport:
		# for key in ['alignmentMethodMS', 'alignmentMethodMSMS', 'scanAveragingMethod']:
		# 	project.options.setdefault(key, None)

		print("Batch project options loaded successfully from self.optsImport.", project.options)
		return project

	def options_to_readoptions_shape(self):
		"""
		Convert the currently loaded, fully typed self.project.options
		into the same mix of types that readOptions() produces.
		Operates in place on the lx.tools.odict.
		"""
		o = self.project.options

		def to_text(v):
			if v is None:
				return ''
			if isinstance(v, tuple):
				return f"({','.join(str(x) for x in v)})"
			return str(v)

		# ---- 1Booleans ----
		bool_keys = {
			'importMSMS','pisSpectra',
			'isotopicCorrection_MSMS','removeIsotopes','isotopesInMasterScan',
			'monoisotopicCorrection','relativeIntensity','logMemory',
			'intensityCorrection','masterScanInSQL','sumFattyAcids',
			'isotopicCorrectionMS','isotopicCorrectionMSMS','complementMasterScan',
			'noHead','compress','tabLimited','dumpMasterScan','statistics',
			'noPermutations','settingsPrefix','batch_mode'
		}

		# ---- Integers ----
		int_keys = {'loopNr'}

		# ---- Fields that should be None if empty ----
		none_if_empty = {
			'optionalMSthreshold','optionalMSMSthreshold',
			'optionalMSthresholdType','optionalMSMSthresholdType',
			'complementMasterScanFile','mzXML','dumpMasterScanFile'
		}

		# ---- Empty-string fields (GUI text boxes) ----
		empty_if_none = {'MSMScalibration','intensityCorrectionPrecursor','intensityCorrectionFragment'}

		# ---- Pass 1: fix types by category ----
		for k, v in list(o.items()):
			# booleans
			if k in bool_keys:
				if isinstance(v, str):
					lv = v.strip().lower()
					if lv in ('true', '1', 'yes', 'on'):
						o[k] = True
					elif lv in ('false', '0', 'no', 'off', ''):
						o[k] = False
					else:
						o[k] = False
				else:
					o[k] = bool(v)
				continue

			# integers
			if k in int_keys:
				try:
					o[k] = int(v)
				except Exception:
					pass
				continue

			# None-handling fields
			if k in none_if_empty:
				if v in (None, '', 'None', 'none'):
					o[k] = None
				continue

			# Empty-string fields
			if k in empty_if_none:
				if v is None:
					o[k] = ''
				else:
					o[k] = str(v)
				continue

			# tuples as text
			if isinstance(v, tuple):
				o[k] = f"({','.join(str(x) for x in v)})"
				continue

			# everything else as str (text controls)
			if not isinstance(v, (bool, int)):
				o[k] = to_text(v)
        
        
        
	def _start_batch_log_tail(self):
		"""Begin pumping the batch log file into the debug window.

		Batch output arrives from two places the GUI cannot be written to
		from: the background batch thread, and the spawned worker processes.
		Both append to the log file instead, and this timer -- which fires on
		the main thread -- is the only thing that touches the text control.
		"""
		if getattr(self, "_batch_log_timer", None) is None:
			self._batch_log_timer = wx.Timer(self)
			self.Bind(wx.EVT_TIMER, self._on_batch_log_tick, self._batch_log_timer)
		self._batch_log_timer.Start(300)

	def _on_batch_log_tick(self, evt=None):
		"""Append everything written to the batch log since the last tick."""
		path = getattr(self, "_batch_log_path", None)
		if not path:
			return

		try:
			with open(path, "r", encoding="utf-8", errors="replace") as handle:
				handle.seek(self._batch_log_pos)
				chunk = handle.read()
				self._batch_log_pos = handle.tell()
		except OSError:
			# The log may not exist yet on the first tick.
			return

		if not chunk:
			return

		try:
			self.debug.text_ctrl.AppendText(chunk)
			# Follow the tail, as a console would.
			self.debug.text_ctrl.GotoPos(self.debug.text_ctrl.GetLength())
		except (AttributeError, RuntimeError):
			# The debug window was closed while the batch was still running.
			# Stop the timer here rather than via _stop_batch_log_tail, which
			# would tick again and land straight back in this handler.
			timer = getattr(self, "_batch_log_timer", None)
			if timer is not None and timer.IsRunning():
				timer.Stop()

	def _stop_batch_log_tail(self):
		"""Drain the log one last time, then stop the timer."""
		timer = getattr(self, "_batch_log_timer", None)
		if timer is not None and timer.IsRunning():
			timer.Stop()
		self._on_batch_log_tick()

	def _finish_batch_logging(self):
		"""Wind the run down: hand back print() and the streams, then drain.

		Order matters. restore_streams() flushes a trailing partial line into
		the log, so it has to happen before the final drain -- otherwise that
		last line sits in the file and never reaches the window.
		"""
		logger = getattr(self, "logger", None)
		if logger is not None:
			logger.restore_streams()
			logger.restore_print()
		self._stop_batch_log_tail()

	def On_button_RUN_batch(self, evt):
		"""
		Launch batch processing in a background thread.

		- Collects options + MFQL queries from the GUI/project
		- Calls lx.batch_processor.run_batch() in a background thread
		- run_batch() internally uses multiprocessing.Pool (spawn) → safe for Windows + PyInstaller
		- GUI stays responsive and displays output in real time
		"""

		import pickle, platform, sys, os, wx
		from pathlib import Path
		from lx.logger import TeeLogger

		self.button_RUN_batch.Disable()
		self.isRunning = True

		# -----------------------------
		# Build payload (options + queries)
		# -----------------------------
		if self.project_loaded_for_batch:
			if not self.validate_before_batch():
				self.button_RUN_batch.Enable()
				return

			project = Project()
			project.load(self.projectFile)
			self.project = project  # (options_to_readoptions_shape relies on self.project)

			#print("Initial project options loaded from file:", type(project.options),type(self.project.options))
			# Apply ini + setting so preset-dependent parameters get populated/updated

			for k, v in self.optsImport.items():
				self.project.options[k] = v

			# Overlay GUI values (these MUST win)
			# IMPORTANT: build_batch_options_from_ui should include ini/setting/importDir/dataType/batch_mode/savePerSample
			self.project.options.update(self.build_batch_options_from_ui())

			# Convert types into the shape expected downstream
			self.options_to_readoptions_shape()

			# Recompute / validate / format and get final options
			self.project.testOptions()
			self.project.formatOptions()
			options = self.project.getOptions()
			#print("Initial project options loaded from file:????????", type(project.options),type(self.project.options), type(options))
			# Refresh MFQL scripts from GUI listbox (same as your else branch)
			self.dictMFQLScripts = {}
			self.dictMFQLScripts = self.collect_mfql_from_listbox()

			print("Running in batch mode: MasterScan will not be saved.")

			queries_payload = [
				{"name": k, "path": str(Path(v).resolve())}
				for k, v in self.dictMFQLScripts.items()
			]		
		
		else:
			print("No project loaded for batch processing.")
			if not self.validate_before_batch():
				wx.MessageBox(
					"Missing information for batch processing.",
					"Error", wx.OK | wx.ICON_ERROR
				)
				self.button_RUN_batch.Enable()
				return

			project = self.readOptions_batch()

			self.dictMFQLScripts = {}
			self.dictMFQLScripts = self.collect_mfql_from_listbox()


			options = project.options
			options["batch_mode"] = True
			options["importMSMS"] = True
			options["spectraFormat"] = self.combo_ctrl_ImportDataSection.GetValue()
			options["masterScanImport"] = self.text_ctrl_ImportDataSection.GetValue()
			options["resultFile"] = self.text_ctrl_ImportDataSection.GetValue()
			options["savePerSample"] = bool(self.checkbox_save_per_sample.IsChecked())
			options["verboseWorkerLog"] = bool(self.checkbox_verbose_log.IsChecked())

			project.testOptions()
			project.formatOptions()
			options = project.getOptions()

			queries_payload = [
				{"name": k, "path": str(Path(v).resolve())}
				for k, v in self.dictMFQLScripts.items()
			]

		# -----------------------------
		# Create GUI debug window
		# -----------------------------
		try:
			if hasattr(self, "debug") and self.debug:
				self.debug.Destroy()
				self.debug = None
		except Exception:
			pass

		import_dir = Path(options.get("importDir", "")).resolve()

		self.debug = TextOutFrame(self, -1, "Batch Debug")
		self.debugOpen = True
		self.debug.Show(True)

		# -----------------------------
		# Unified logger (GUI + file)
		# -----------------------------
		log_path = os.path.join(import_dir, "batch_log.txt")

		# The log file is the single source of text for the debug window: this
		# process writes to it through TeeLogger, the spawned workers append to
		# it themselves, and a timer on the main thread pumps whatever is new
		# into the control. That is why gui_writer is None here -- writing to
		# the control from TeeLogger as well would double every line, and would
		# do it from the batch thread, which is not allowed to touch wx.
		# Remember where the file ends before anything is written so a second
		# run does not replay the first one (TeeLogger appends).
		try:
			self._batch_log_pos = os.path.getsize(log_path)
		except OSError:
			self._batch_log_pos = 0
		self._batch_log_path = log_path

		self.logger = TeeLogger(
			gui_writer=None,
			file_path=log_path,
			also_stdout=False,
			# Matches the "[W3 <sample>]" the workers stamp on their lines, so
			# every line in the log says which process it came from.
			context="[MAIN]"
		)
		self.logger.log("Starting batch process...")
		print("Starting batch process...##",options)
		#redirect all print() in this process to this logger
		self.logger.install_as_print()
		# ...and sys.stdout/sys.stderr with it, so warnings raised during the
		# merge (a mis-detected CSV delimiter, say) are not lost.
		self.logger.install_as_streams()
		self._start_batch_log_tail()
		# -----------------------------
		# Payload passed to thread (not subprocess)
		# -----------------------------
		payload = {
			"options": options,
			"queries": queries_payload,
			"log_file": log_path
		}
  
		#print(f"Batch payload prepared: {payload}")
		#self.button_RUN_batch.Enable()##remove this line after testing
  
		# -----------------------------
		# Run batch in background thread (NOT subprocess)
		# -----------------------------
		def run_in_thread():
			from lx.batch_processor import run_batch
		# Reinstall print redirection inside this thread
			self.logger.install_as_print()
			n_cores = int(self.spin_cores.GetValue())
			occupation_threshold = float(self.spin_occupational_threshold.GetValue())

			print(f"Batch thread started. Using {n_cores} cores for processing.")
			try:
				# run_batch logs its own summary line through print(), which
				# now reaches the window via the log file.
				run_batch(
					payload["options"],
					payload["queries"],
					log_file=payload["log_file"],
					occurrence_threshold=occupation_threshold,
    				n_cores=n_cores	
				)

				print("Batch processing completed.")

			except Exception:
				# A bare str(e) hid where the batch actually broke; the log file
				# is the only record once the run is over, so put the traceback
				# in it rather than a one-line summary.
				print("Batch failed:\n" + traceback.format_exc())

			finally:
				wx.CallAfter(self._finish_batch_logging)
				wx.CallAfter(self.button_RUN_batch.Enable)
				wx.CallAfter(setattr, self, "isRunning", False)



		# Start background thread
		import threading
		threading.Thread(target=run_in_thread, daemon=True).start()



	def validate_before_batch(self):

		if self.combo_ctrl_ImportDataSection.GetValue().strip().lower() == "dta/csv":
			wx.MessageBox("Batch mode supports mzML only. dta/csv is not allowed.", "Warning")
			return False

		#Check TextCtrl
		if not self.text_ctrl_ImportDataSection.GetValue().strip():
			wx.MessageBox("Import data section is empty.", "Warning")
			return False

		#Check Configuration list
		self.listConfigurations_batch = sorted(self.confParse.sections())
		if not self.listConfigurations_batch:
			wx.MessageBox("No configuration sections found.", "Error")
			return False

		# Check current selection (if applicable)
		if not self.currentConfiguration.strip():
			wx.MessageBox("No configuration selected.", "Warning")
			return False
		
			# Check MFQL batch entries 
		lines = [s.strip() for s in self.listbox_MFQL_batch.GetItems() if s.strip()]
		if not lines:
			wx.MessageBox("MFQL batch list is empty.", "Warning")
			return False
		else:
			print(f"MFQL batch list has {len(lines)} entr(y/ies): {lines}")



		
		# All checks passed
		return True



	def build_batch_options_from_ui(self):
		"""
		Build raw (string/bool/int) options from the current GUI state.
		These are the values that should win over whatever the project file stored.
		"""
		opts = {}

		#print("Building batch options from UI...", self.listConfigurations_batch, self.choice_SelectSettingSection_batch.GetStringSelection(),self.currentConfiguration)
		opts["importDir"] = self.text_ctrl_ImportDataSection.GetValue()
		opts["dataType"] = self.combo_ctrl_ImportDataSection.GetValue()
		opts["ini"] = self.text_ctrl_OutputMasterScanSection.GetValue()
		opts["setting"] = self.choice_SelectSettingSection_batch.GetStringSelection()

		opts["batch_mode"] = True
		opts["savePerSample"] = bool(self.checkbox_save_per_sample.IsChecked())
		opts["verboseWorkerLog"] = bool(self.checkbox_verbose_log.IsChecked())

		return opts

	def collect_mfql_from_listbox(self):
		"""
		Rebuild self.dictMFQLScripts from directories listed in self.listbox_MFQL_batch.
		Returns a dict {filename: full_path}.
		"""
		mfql = {}
		lines = [s.strip() for s in self.listbox_MFQL_batch.GetItems() if s.strip()]

		for dir_path in lines:
			if not os.path.isdir(dir_path):
				print(f"Skipping invalid directory: {dir_path}")
				continue

			for root, _, files in os.walk(dir_path):
				for filename in files:
					if filename.lower().endswith(".mfql"):
						full_path = os.path.join(root, filename)
						mfql[filename] = full_path

		return mfql


    #############################################################
    
    
    
    
	def OnPaneChanged(self, evt=None):

		# redo the layout
		self.Layout()
		self.Fit()

		# and also change the labels
		if self.collapsable_pane.IsExpanded():
			self.collapsable_pane.SetLabel(self.label2)
		else:
			self.collapsable_pane.SetLabel(self.label1)

	def OnBrowse_LoadIni(self, evt):

		# open directory with *.dta/*mzXML content
		dlg = wx.FileDialog(self, "Choose a *.ini file with settings", style=wx.DD_DEFAULT_STYLE|wx.FD_OPEN)
		dlg.SetWildcard("*.ini files|*.ini")

		if dlg.ShowModal() == wx.ID_OK:
			#self.filePath_LoadIni = relativePath(dlg.GetPath())
			self.filePath_LoadIni = dlg.GetPath()

		self.OnBrowse_LoadIni_Body(self.filePath_LoadIni)

		dlg.Destroy()

	def OnBrowse_LoadIni_Body(self, filePath_LoadIni):


		is_batch_checked = self.checkBox_BatchMode.IsChecked()

		if is_batch_checked:
      
			self.text_ctrl_MasterScanSection.SetValue(filePath_LoadIni)
			self.filePath_MasterScan = filePath_LoadIni

			self.confParse = configparser.ConfigParser()
			self.confParse.read(self.text_ctrl_MasterScanSection.GetLineText(0))

			self.listConfigurations_batch = sorted(self.confParse.sections())
			print("Batch configurations loaded:", self.listConfigurations_batch)

			self.currentConfiguration = ''

			self.choice_SelectSettingSection_batch.Clear()
			self.choice_SelectSettingSection_batch.Append(self.listConfigurations_batch)
   
			if self.choice_SelectSettingSection_batch.GetCount() > 0:
				# if nothing selected yet, select first
				if self.choice_SelectSettingSection_batch.GetSelection() == wx.NOT_FOUND:
					self.choice_SelectSettingSection_batch.SetSelection(0)

				self.currentConfiguration = self.choice_SelectSettingSection_batch.GetStringSelection()
				self.collectSettings(self.currentConfiguration)

				
		else:
			self.text_ctrl_LoadIniSection.SetValue(filePath_LoadIni)
			self.filePath_LoadIni = filePath_LoadIni

			self.confParse = configparser.ConfigParser()
			self.confParse.read(self.text_ctrl_LoadIniSection.GetLineText(0))

			self.listConfigurations = sorted(self.confParse.sections())

			self.currentConfiguration = ''
			print("Configurations loaded:", self.listConfigurations)
			self.choice_SelectSettingSection.Clear()
			self.choice_SelectSettingSection.Append(self.listConfigurations)
			self.clearConfiguration()

	def OnSave_LoadIni(self, evt):

		if self.currentConfiguration != '':
			section = self.currentConfiguration

			self.confParse.set(section, 'precursorMassShift', self.text_ctrl_SettingsSection_precursorMassShift.GetValue())
			self.confParse.set(section, 'precursorMassShiftOrbi', self.text_ctrl_SettingsSection_precursorMassShiftOrbi.GetValue())
			strTimerange = '(%s,%s)' % (self.text_ctrl_SettingsSection_timerange1.GetValue(), self.text_ctrl_SettingsSection_timerange2.GetValue())
			self.confParse.set(section, 'timerange', strTimerange)
			self.confParse.set(section, 'selectionWindow', self.text_ctrl_SettingsSection_selectionWindow.GetValue())
			self.confParse.set(section, 'MSresolution', self.text_ctrl_SettingsSection_resolution_ms.GetValue())
			self.confParse.set(section, 'MSMSresolution', self.text_ctrl_SettingsSection_resolution_msms.GetValue())
			self.confParse.set(section, 'MStolerance', '%s %s' % (self.text_ctrl_SettingsSection_tolerance_ms.GetValue(),\
					self.choice_SettingsSection_tolerance_ms.GetString(self.choice_SettingsSection_tolerance_ms.GetSelection())))
			self.confParse.set(section, 'MSMStolerance',  '%s %s' % (self.text_ctrl_SettingsSection_tolerance_msms.GetValue(),\
					self.choice_SettingsSection_tolerance_msms.GetString(self.choice_SettingsSection_tolerance_msms.GetSelection())))
			strMassrange = '(%s,%s)' % (self.text_ctrl_SettingsSection_massrange_ms1.GetValue(), self.text_ctrl_SettingsSection_massrange_ms2.GetValue())
			self.confParse.set(section, 'MSmassrange', strMassrange)
			strMassrange = '(%s,%s)' % (self.text_ctrl_SettingsSection_massrange_msms1.GetValue(), self.text_ctrl_SettingsSection_massrange_msms2.GetValue())
			self.confParse.set(section, 'MSMSmassrange', strMassrange)
			self.confParse.set(section, 'MSthreshold', self.text_ctrl_SettingsSection_threshold_ms.GetValue())
			self.confParse.set(section, 'MSMSthreshold', self.text_ctrl_SettingsSection_threshold_msms.GetValue())
			#self.confParse.set(section, 'MSthresholdType', '%s' % self.choice_SettingsSection_threshold_ms.GetSelection())
			#self.confParse.set(section, 'MSMSthresholdType', '%s' % self.choice_SettingsSection_threshold_msms.GetSelection())
			self.confParse.set(section, 'MSthresholdType', '%s' % self.store_SettingsSection_threshold_ms)
			self.confParse.set(section, 'MSMSthresholdType', '%s' % self.store_SettingsSection_threshold_msms)
			self.confParse.set(section, 'MSminOccupation', self.text_ctrl_SettingsSection_occupationThr_ms.GetValue())
			self.confParse.set(section, 'MSMSminOccupation', self.text_ctrl_SettingsSection_occupationThr_msms.GetValue())
			self.confParse.set(section, 'MSresolutionDelta', self.text_ctrl_SettingsSection_resDelta_ms.GetValue())
			self.confParse.set(section, 'MSMSresolutionDelta', self.text_ctrl_SettingsSection_resDelta_msms.GetValue())
			self.confParse.set(section, 'MScalibration', self.text_ctrl_SettingsSection_calibration_ms.GetValue())
			self.confParse.set(section, 'MSMScalibration', self.text_ctrl_SettingsSection_calibration_msms.GetValue())
			self.confParse.set(section, 'MSfilter', self.text_ctrl_SettingsSection_filter_ms.GetValue())
			self.confParse.set(section, 'MSMSfilter', self.text_ctrl_SettingsSection_filter_msms.GetValue())

			with open(self.filePath_LoadIni, 'w+') as fIni:
				self.confParse.write(fIni)

			self.fillConfiguration(section)
			self.OnSettingsSaved()

		else:
			self.OnSaveAs_LoadIni(evt)

	def OnDelete_LoadIni(self, evt):

		self.confParse.remove_section(self.currentConfiguration)
		for index in range(len(self.listConfigurations)):
			if self.listConfigurations[index] == self.currentConfiguration:
				del self.listConfigurations[index]
				break

		self.currentConfiguration = ''

		self.choice_SelectSettingSection.Clear()
		self.choice_SelectSettingSection.Append(self.listConfigurations)
		self.clearConfiguration()

		with open(self.filePath_LoadIni, 'w+') as fIni:
			self.confParse.write(fIni)

	def OnSaveAs_LoadIni(self, evt):

		dlg = wx.TextEntryDialog(self, "Choose a name for the section")
		if dlg.ShowModal() == wx.ID_OK:
			newSection = dlg.GetValue()
			dlg.Destroy()
		else:
			dlg.Destroy()
			self.OnSettingsSaved()
			return None

		# now *.ini load since now
		if not self.confParse:

			self.confParse = configparser.ConfigParser()

			msgDlg = wx.MessageDialog(self, "You have to load an existing *.ini file first. Do you want to create one?",
			'Caption', wx.YES|wx.NO|wx.CANCEL|wx.ICON_INFORMATION)

			# create a new *.ini file
			if msgDlg.ShowModal() == wx.ID_YES:
				createNew = True
			msgDlg.Destroy()

			if createNew:
				dlgFile = wx.FileDialog(self, "Choose a *.ini file with settings", style=wx.DD_DEFAULT_STYLE|wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
				if dlgFile.ShowModal() == wx.ID_OK:
					#self.filePath_LoadIni = relativePath(dlgFile.GetPath())
					self.filePath_LoadIni = dlgFile.GetPath()
				dlgFile.Destroy()

				# add a new section
				dlg2 = wx.TextEntryDialog(self, "Choose a section name")
				if dlg2.ShowModal() == wx.ID_OK:
					newSection = dlg2.GetValue()
				dlg2.Destroy()

		self.confParse.add_section(newSection)

		self.confParse.set(newSection, 'precursorMassShift', self.text_ctrl_SettingsSection_precursorMassShift.GetValue())
		self.confParse.set(newSection, 'precursorMassShiftOrbi', self.text_ctrl_SettingsSection_precursorMassShiftOrbi.GetValue())
		strTimerange = '(%s,%s)' % (self.text_ctrl_SettingsSection_timerange1.GetValue(), self.text_ctrl_SettingsSection_timerange2.GetValue())
		self.confParse.set(newSection, 'timerange', strTimerange)
		self.confParse.set(newSection, 'selectionWindow', self.text_ctrl_SettingsSection_selectionWindow.GetValue())
		self.confParse.set(newSection, 'MSresolution', self.text_ctrl_SettingsSection_resolution_ms.GetValue())
		self.confParse.set(newSection, 'MSMSresolution', self.text_ctrl_SettingsSection_resolution_msms.GetValue())
		self.confParse.set(newSection, 'MStolerance', self.text_ctrl_SettingsSection_tolerance_ms.GetValue())
		self.confParse.set(newSection, 'MSMStolerance', self.text_ctrl_SettingsSection_tolerance_msms.GetValue())
		strMassrange = '(%s,%s)' % (self.text_ctrl_SettingsSection_massrange_ms1.GetValue(), self.text_ctrl_SettingsSection_massrange_ms2.GetValue())
		self.confParse.set(newSection, 'MSmassrange', strMassrange)
		strMassrange = '(%s,%s)' % (self.text_ctrl_SettingsSection_massrange_msms1.GetValue(), self.text_ctrl_SettingsSection_massrange_msms2.GetValue())
		self.confParse.set(newSection, 'MSMSmassrange', strMassrange)
		self.confParse.set(newSection, 'MSthreshold', self.text_ctrl_SettingsSection_threshold_ms.GetValue())
		self.confParse.set(newSection, 'MSMSthreshold', self.text_ctrl_SettingsSection_threshold_msms.GetValue())
		self.confParse.set(newSection, 'MSthresholdType', '%s' % self.store_SettingsSection_threshold_ms)
		self.confParse.set(newSection, 'MSMSthresholdType', '%s' % self.store_SettingsSection_threshold_msms)
		self.confParse.set(newSection, 'MSminOccupation', self.text_ctrl_SettingsSection_occupationThr_ms.GetValue())
		self.confParse.set(newSection, 'MSMSminOccupation', self.text_ctrl_SettingsSection_occupationThr_msms.GetValue())
		self.confParse.set(newSection, 'MSresolutionDelta', self.text_ctrl_SettingsSection_resDelta_ms.GetValue())
		self.confParse.set(newSection, 'MSMSresolutionDelta', self.text_ctrl_SettingsSection_resDelta_msms.GetValue())
		self.confParse.set(newSection, 'MScalibration', self.text_ctrl_SettingsSection_calibration_ms.GetValue())
		self.confParse.set(newSection, 'MSMScalibration', self.text_ctrl_SettingsSection_calibration_msms.GetValue())
		self.confParse.set(newSection, 'MSfilter', self.text_ctrl_SettingsSection_filter_ms.GetValue())
		self.confParse.set(newSection, 'MSMSfilter', self.text_ctrl_SettingsSection_filter_msms.GetValue())

		self.listConfigurations.append(newSection)
		self.listConfigurations.sort()

		#self.choice_SelectSettingSection.Set(sorted(self.confParse.sections()))
		self.choice_SelectSettingSection.Clear()
		self.choice_SelectSettingSection.Append(self.listConfigurations)

		with open(self.filePath_LoadIni, 'w+') as fIni:
			self.confParse.write(fIni)

		self.fillConfiguration(newSection)

		indexSection = None
		self.listConfigurations = sorted(self.confParse.sections())
		for i in range(len(self.listConfigurations)):
			if self.listConfigurations[i] == newSection:
				indexSection = i

		if indexSection:
			self.choice_SelectSettingSection.SetSelection(indexSection)
		self.currentConfiguration = newSection

		self.OnSettingsSaved()

	def OnChoice_Tolerance_MS(self, evt):
		if evt.GetString() == 'ppm':
			self.store_SettingsSection_tolerance_ms = 'ppm'
		elif evt.GetString() == 'Da':
			self.store_SettingsSection_tolerance_ms = 'Da'

	def OnChoice_Tolerance_MSMS(self, evt):
		if evt.GetString() == 'ppm':
			self.store_SettingsSection_tolerance_msms = 'ppm'
		elif evt.GetString() == 'Da':
			self.store_SettingsSection_tolerance_msms = 'Da'

	def OnChoice_Threshold_MS(self, evt):
		if evt.GetString() == 'relative':
			self.store_SettingsSection_threshold_ms = 'relative'
		elif evt.GetString() == 'absolute':
			self.store_SettingsSection_threshold_ms = 'absolute'
		self.OnSettingsChange()

	def OnChoice_Threshold_MSMS(self, evt):
		if evt.GetString() == 'relative':
			self.store_SettingsSection_threshold_msms = 'relative'
		elif evt.GetString() == 'absolute':
			self.store_SettingsSection_threshold_msms = 'absolute'
		self.OnSettingsChange()


	def OnOpen_Output(self, evt):

		if playSound:
			wx.Sound('../pics/OpenFile.wav').Play()

		curScript = self.text_ctrl_OutputSection.GetValue().split(os.sep)[-1]
		fileName = self.text_ctrl_OutputSection.GetValue()

		if not os.path.exists(fileName):
			dlg = wx.MessageDialog(self, "The path '%s' does not exist!" % fileName, "Error", wx.OK|wx.ICON_HAND)
			if dlg.ShowModal() == wx.ID_OK:
				dlg.Destroy()
				return None

		win = CSVViewer(self, -1, "Ouput as *.csv file", file = fileName)
		win.Show(True)
		pass

	def OnBrowse_Output(self, evt):

		# specify output file
		dlg = wx.FileDialog(self, "Specify a file for the output", style=wx.DD_DEFAULT_STYLE|wx.FD_SAVE)
		dlg.SetWildcard("*.csv|*.csv")

		if dlg.ShowModal() == wx.ID_OK:
			self.filePath_Output = dlg.GetPath()

			if not re.match(r'.*\.csv', self.filePath_Output):
				s = self.filePath_Output.split('.')
				if len(s) == 1:
					self.filePath_Output += '.csv'
				else:
					self.filePath_Output = ''
				for i in s[:-1]:
					self.filePath_Output += '%s.' % i
				self.filePath_Output += 'csv'

		dlg.Destroy()
		try:
			self.text_ctrl_OutputSection.SetValue(self.filePath_Output)
		except AttributeError:
			print("No output file specified!")

	def OnBrowse_MasterScan(self, evt):

		# open MasterScanFile
		dlg = wx.FileDialog(self, "Choose a masterScan file", style=wx.DD_DEFAULT_STYLE|wx.FD_OPEN)
		dlg.SetWildcard("*.sc files|*.sc")

		if dlg.ShowModal() == wx.ID_OK:
			self.filePath_MasterScan = dlg.GetPath()

		dlg.Destroy()

		self.OnBrowse_MasterScan_Body(self.filePath_MasterScan)

	def OnBrowse_MasterScan_Body(self, filePath):

		if not re.match(r'.*\.sc$', filePath):
			dlg = wx.MessageDialog(self, "The filename '%s' has no '.sc' at its end!" % filePath, "Error", wx.OK|wx.ICON_HAND)
			if dlg.ShowModal() == wx.ID_OK:
				dlg.Destroy()
				return None

		# generate output file
		file = filePath.split(os.sep)[-1]
		fileOut = file.split('.')[0] + '-out.csv'
		fileDump = file.split('.')[0] + '-dump.csv'
		fileComplementSC = file.split('.')[0] + '-complement.sc'
		path = filePath.split(os.sep)[:-1]
		strPath = ''
		for i in path:
			strPath += i + os.sep

		if strPath != '':
			if strPath[-1] == os.sep:
				strOutputFile = strPath + fileOut
				strDump = strPath + fileDump
				strComplementSC = strPath + fileComplementSC
			else:
				strOutputFile = strPath + os.sep + fileOut
				strDump = strPath + os.sep + fileDump
				strComplementSC = strPath + os.sep + fileComplementSC
		else:
			strOutputFile = fileOut
			strDump = fileDump
			strComplementSC = fileComplementSC

		self.text_ctrl_OutputSection.SetValue(strOutputFile)
		self.text_ctrl_MasterScanSection.SetValue(filePath)

		self.filePath_Dump = strDump
		self.filePath_ComplementSC = strComplementSC

	def OnBrowse_Dump(self, evt):

		# specify a dump file
		dlg = wx.FileDialog(self, "Specify a dump file", style=wx.DD_DEFAULT_STYLE|wx.FD_SAVE)
		if self.filePath_Dump:
			dlg.SetPath(self.filePath_Dump)

		if dlg.ShowModal() == wx.ID_OK:
			self.filePath_Dump = dlg.GetPath()

		dlg.Destroy()
		#self.filePath_Dump = self.filePath_MasterScan + os.sep + self.filePath_MasterScan.split(os.sep)[-1] + '-dump.csv'

	def OnOpen_Dump(self, evt):

		if playSound:
			wx.Sound('../pics/OpenFile.wav').Play()

		curScript = self.filePath_Dump.split(os.sep)[-1]
		fileName = self.filePath_Dump

		if not os.path.exists(fileName):
			dlg = wx.MessageDialog(self, "The dump of your MasterScan does not exist. It will be generated if you check 'dump MasterScan' and hit the 'Run LipidXplorer' button.",
					"Attention!", wx.OK|wx.ICON_HAND)
			if dlg.ShowModal() == wx.ID_OK:
				dlg.Destroy()
				return None

		win = CSVViewer(self, -1, "Dump file output", file = fileName)
		win.Show(True)

		return None

	def OnSettingsChange(self):

		#if not self.button_Save_LoadIniSection.GetBackgroundColour() == (250, 80, 80, 215):
		self.button_Save_LoadIniSection.SetBackgroundColour((250, 80, 80, 215))
		self.isChangedAndNotSavedCurrentConfiguration = True
		self.Refresh()

	def OnSettingsSaved(self):

		#if not self.button_Save_LoadIniSection.GetBackgroundColour() == (230, 224, 218, 255):
		self.button_Save_LoadIniSection.SetBackgroundColour((240, 240, 240, 94))
		self.isChangedAndNotSavedCurrentConfiguration = False
		self.Refresh()


		

	def OnConfigurationChoice(self, evt):

		if self.isChangedAndNotSavedCurrentConfiguration:
			dlg = wx.MessageDialog(self, "Modified configuration '%s' is not saved. Save it?" % \
					self.currentConfiguration, "Ups..", wx.YES|wx.NO|wx.ICON_HAND)
			if dlg.ShowModal() == wx.ID_YES:
				self.OnSave_LoadIni()
				return None

		self.currentConfiguration = evt.GetString()
		self.fillConfiguration(self.currentConfiguration)
		self.OnSettingsSaved()

	#def OnImportMSMS(self, evt):

	#	if self.checkBox_importMSMS.GetValue():
	#		self.lpdxOptions['importMSMS'] = False
	#	else:
	#		self.lpdxOptions['importMSMS'] = True

	def OnConfigurationEdit(self, evt):
		pass

	def OnConfigurationNew(self, evt):
		pass

	def OnConfigurationRemove(self, evt):
		pass

	def fillConfiguration(self, setting):
		'''Fill values in the configuration panel from the *.ini file.'''

		# some options
		self.opts = {}
		if self.confParse.has_option(setting, "MSminOccupation"):
			self.text_ctrl_SettingsSection_occupationThr_ms.ChangeValue(self.confParse.get(setting, "MSminOccupation"))
		else:
			self.text_ctrl_SettingsSection_occupationThr_ms.ChangeValue('')

		if self.confParse.has_option(setting, "MSMSminOccupation"):
			self.text_ctrl_SettingsSection_occupationThr_msms.ChangeValue(self.confParse.get(setting, "MSMSminOccupation"))
		else:
			self.text_ctrl_SettingsSection_occupationThr_msms.ChangeValue('')

		if self.confParse.has_option(setting, "MSthreshold"):
			self.text_ctrl_SettingsSection_threshold_ms.ChangeValue(self.confParse.get(setting, "MSthreshold"))
		else:
			self.text_ctrl_SettingsSection_threshold_ms.ChangeValue('')

		if self.confParse.has_option(setting, "MSMSthreshold"):
			self.text_ctrl_SettingsSection_threshold_msms.ChangeValue(self.confParse.get(setting, "MSMSthreshold"))
		else:
			self.text_ctrl_SettingsSection_threshold_msms.ChangeValue('')

		if self.confParse.has_option(setting, "MSthresholdType"):
			self.choice_SettingsSection_threshold_ms.SetStringSelection(self.confParse.get(setting, "MSthresholdType"))
			self.store_SettingsSection_threshold_ms = self.confParse.get(setting, "MSthresholdType")
		else:
			self.choice_SettingsSection_threshold_ms.SetStringSelection("absolute")
			self.store_SettingsSection_threshold_ms = "absolute"

		if self.confParse.has_option(setting, "MSMSthresholdType"):
			self.choice_SettingsSection_threshold_msms.SetStringSelection(self.confParse.get(setting, "MSMSthresholdType"))
			self.store_SettingsSection_threshold_msms = self.confParse.get(setting, "MSMSthresholdType")
		else:
			self.choice_SettingsSection_threshold_msms.SetStringSelection("absolute")
			self.store_SettingsSection_threshold_msms = "absolute"

		if self.confParse.has_option(setting, "timerange"):
			strTimerange = self.confParse.get(setting, "timerange")
			m = re.match(r'\(\s*(\d+)\s*,\s*(\d+)\s*\)', strTimerange)
			if m:
				self.text_ctrl_SettingsSection_timerange1.ChangeValue(m.group(1))
				self.text_ctrl_SettingsSection_timerange2.ChangeValue(m.group(2))
			else:
				self.text_ctrl_SettingsSection_timerange1.ChangeValue('')
				self.text_ctrl_SettingsSection_timerange2.ChangeValue('')
		else:
			self.text_ctrl_SettingsSection_timerange1.ChangeValue('')
			self.text_ctrl_SettingsSection_timerange2.ChangeValue('')

		if self.confParse.has_option(setting, "MSmassrange"):
			strMassrange = self.confParse.get(setting, "MSmassrange")
			m = re.match(r'\(\s*(\d+)\s*,\s*(\d+)\s*\)', strMassrange)
			if m:
				self.text_ctrl_SettingsSection_massrange_ms1.ChangeValue(m.group(1))
				self.text_ctrl_SettingsSection_massrange_ms2.ChangeValue(m.group(2))
			else:
				self.text_ctrl_SettingsSection_massrange_ms1.ChangeValue('')
				self.text_ctrl_SettingsSection_massrange_ms2.ChangeValue('')
		else:
			self.text_ctrl_SettingsSection_massrange_ms1.ChangeValue('')
			self.text_ctrl_SettingsSection_massrange_ms2.ChangeValue('')

		if self.confParse.has_option(setting, "MSMSmassrange"):
			strMassrange = self.confParse.get(setting, "MSMSmassrange")
			m = re.match(r'\(\s*(\d+)\s*,\s*(\d+)\s*\)', strMassrange)
			if m:
				self.text_ctrl_SettingsSection_massrange_msms1.ChangeValue(m.group(1))
				self.text_ctrl_SettingsSection_massrange_msms2.ChangeValue(m.group(2))
			else:
				self.text_ctrl_SettingsSection_massrange_msms1.ChangeValue('')
				self.text_ctrl_SettingsSection_massrange_msms2.ChangeValue('')
		else:
			self.text_ctrl_SettingsSection_massrange_msms1.ChangeValue('')
			self.text_ctrl_SettingsSection_massrange_msms2.ChangeValue('')

		if self.confParse.has_option(setting, "MSresolution"):
			self.text_ctrl_SettingsSection_resolution_ms.ChangeValue(self.confParse.get(setting, "MSresolution"))
		else:
			self.text_ctrl_SettingsSection_resolution_ms.ChangeValue('')

		if self.confParse.has_option(setting, "MSMSresolution"):
			self.text_ctrl_SettingsSection_resolution_msms.ChangeValue(self.confParse.get(setting, "MSMSresolution"))
		else:
			self.text_ctrl_SettingsSection_resolution_msms.ChangeValue("")

		if self.confParse.has_option(setting, "MSresolutionDelta"):
			self.text_ctrl_SettingsSection_resDelta_ms.ChangeValue(self.confParse.get(setting, "MSresolutionDelta"))
		else:
			self.text_ctrl_SettingsSection_resDelta_ms.ChangeValue('')

		if self.confParse.has_option(setting, "MSMSresolutionDelta"):
			self.text_ctrl_SettingsSection_resDelta_msms.ChangeValue(self.confParse.get(setting, "MSMSresolutionDelta"))
		else:
			self.text_ctrl_SettingsSection_resDelta_msms.ChangeValue('')

		if self.confParse.has_option(setting, "MScalibration"):
			self.text_ctrl_SettingsSection_calibration_ms.ChangeValue(self.confParse.get(setting, "MScalibration"))
		else:
			self.text_ctrl_SettingsSection_calibration_ms.ChangeValue('')

		if self.confParse.has_option(setting, "MSMScalibration"):
			self.text_ctrl_SettingsSection_calibration_msms.ChangeValue(self.confParse.get(setting, "MSMScalibration"))
		else:
			self.text_ctrl_SettingsSection_calibration_msms.ChangeValue('')

		if self.confParse.has_option(setting, "MSfilter"):
			self.text_ctrl_SettingsSection_filter_ms.ChangeValue(self.confParse.get(setting, "MSfilter"))
		else:
			self.text_ctrl_SettingsSection_filter_ms.ChangeValue('')

		if self.confParse.has_option(setting, "MSMSfilter"):
			self.text_ctrl_SettingsSection_filter_msms.ChangeValue(self.confParse.get(setting, "MSMSfilter"))
		else:
			self.text_ctrl_SettingsSection_filter_msms.ChangeValue('')

		if self.confParse.has_option(setting, "MStolerance"):
			str = self.confParse.get(setting, "MStolerance")
			#if re.match('(.*)!(\s(ppm|Da))', str):
			if re.match(r'(\d+|\d+\.\d+)$', str):
				m = re.match(r'(\d+|\d+\.\d+)', str)
				self.text_ctrl_SettingsSection_tolerance_ms.ChangeValue(m.group(1))
				self.choice_SettingsSection_tolerance_ms.SetStringSelection('ppm')
			elif re.match(r'(\d+|\d+\.\d+)(\s)*(ppm|Da)', str):
				m = re.match(r'(\d+|\d+\.\d+)(\s)*(ppm|Da)', str)
				self.text_ctrl_SettingsSection_tolerance_ms.ChangeValue(m.group(1))
				self.choice_SettingsSection_tolerance_ms.SetStringSelection(m.group(3))
			else:
				dlgError = wx.MessageDialog(self, "Cannot read MS Tolerance Value. Setting it to zero.",
					"Error", wx.OK)
				self.text_ctrl_SettingsSection_tolerance_ms.ChangeValue('')
		else:
			self.text_ctrl_SettingsSection_tolerance_ms.ChangeValue('')

		if self.confParse.has_option(setting, "MSMStolerance"):
			str = self.confParse.get(setting, "MSMStolerance")
			#if re.match('(.*)!(\s(ppm|Da))', str):
			if re.match(r'(\d+|\d+\.\d+)$', str):
				m = re.match(r'(\d+|\d+\.\d+)', str)
				self.text_ctrl_SettingsSection_tolerance_msms.ChangeValue(m.group(1))
				self.choice_SettingsSection_tolerance_msms.SetStringSelection('ppm')
			elif re.match(r'(\d+|\d+\.\d+)(\s)*(ppm|Da)', str):
				m = re.match(r'(\d+|\d+\.\d+)(\s)*(ppm|Da)', str)
				self.text_ctrl_SettingsSection_tolerance_msms.ChangeValue(m.group(1))
				self.choice_SettingsSection_tolerance_msms.SetStringSelection(m.group(3))
			else:
				dlgError = wx.MessageDialog(self, "Cannot read MS/MS Tolerance Value. Setting it to zero.",
					"Error", wx.OK)
				self.text_ctrl_SettingsSection_tolerance_msms.ChangeValue('')
		else:
			self.text_ctrl_SettingsSection_tolerance_msms.ChangeValue('')

		if self.confParse.has_option(setting, "selectionWindow"):
			self.text_ctrl_SettingsSection_selectionWindow.ChangeValue(self.confParse.get(setting, "selectionWindow"))
		else:
			self.text_ctrl_SettingsSection_selectionWindow.ChangeValue('')

		if self.confParse.has_option(setting, "precursorMassShift"):
			self.text_ctrl_SettingsSection_precursorMassShift.ChangeValue(self.confParse.get(setting, "precursorMassShift"))
		else:
			self.text_ctrl_SettingsSection_precursorMassShift.ChangeValue('')

		if self.confParse.has_option(setting, "precursorMassShiftOrbi"):
			self.text_ctrl_SettingsSection_precursorMassShiftOrbi.ChangeValue(self.confParse.get(setting, "precursorMassShiftOrbi"))
		else:
			self.text_ctrl_SettingsSection_precursorMassShiftOrbi.ChangeValue('')

	def clearConfiguration(self):

		# some options
		self.text_ctrl_SettingsSection_occupationThr_ms.ChangeValue('')
		self.text_ctrl_SettingsSection_occupationThr_msms.ChangeValue('')
		self.text_ctrl_SettingsSection_threshold_ms.ChangeValue('')
		self.text_ctrl_SettingsSection_threshold_msms.ChangeValue('')
		self.text_ctrl_SettingsSection_timerange1.ChangeValue('')
		self.text_ctrl_SettingsSection_timerange2.ChangeValue('')
		self.text_ctrl_SettingsSection_massrange_ms1.ChangeValue('')
		self.text_ctrl_SettingsSection_massrange_ms2.ChangeValue('')
		self.text_ctrl_SettingsSection_massrange_msms1.ChangeValue('')
		self.text_ctrl_SettingsSection_massrange_msms2.ChangeValue('')
		self.text_ctrl_SettingsSection_resolution_ms.ChangeValue('')
		self.text_ctrl_SettingsSection_resolution_msms.ChangeValue('')
		self.text_ctrl_SettingsSection_resDelta_ms.ChangeValue('')
		self.text_ctrl_SettingsSection_resDelta_msms.ChangeValue('')
		self.text_ctrl_SettingsSection_calibration_ms.ChangeValue('')
		self.text_ctrl_SettingsSection_calibration_msms.ChangeValue('')
		self.text_ctrl_SettingsSection_filter_ms.ChangeValue('')
		self.text_ctrl_SettingsSection_filter_msms.ChangeValue('')
		self.text_ctrl_SettingsSection_tolerance_ms.ChangeValue('')
		self.text_ctrl_SettingsSection_tolerance_msms.ChangeValue('')
		self.text_ctrl_SettingsSection_selectionWindow.ChangeValue('')
		self.text_ctrl_SettingsSection_precursorMassShift.ChangeValue('')
		self.text_ctrl_SettingsSection_precursorMassShiftOrbi.ChangeValue('')

	def OnStartImport(self, evt):

		if self.lipidxplorer:
			from lx.lxMain import startImport
		else:
			from lipoxplorer.lxMain import runLipoX

		# get the options from GUI settings
		project = self.readOptions()
		#print("project = self.readOptions()",type(project.options), project.options) # (<class 'lx.tools.odict'>)
		#exit()
		# test if all options are correct
		project.testOptions()

		# change them into the right format
		project.formatOptions()
		#print("project.formatOptions()", type(project.options), project.options)


		# get options

		options = project.getOptions()
		#print("options = project.getOptions()", type(options),options) ##<class 'lx.options.optionsDict'>


		self.button_StartImport.Disable()
		self.isRunning = True

		# start import
		#startImportGUI(self, options)

		try: # generate a new MasterScan and set the import settings


			if self.lipidxplorer:

				if not wx.GetApp().frame.debugOpen:
					wx.GetApp().frame.OnMenuDebugWin(None)

				# give queues to the Worker class for threadsave data handling
				requestQ = queue.Queue()
				resultQ = queue.Queue()
				worker = Worker(self, requestQ, resultQ)
				options["batch_mode"] = False
				startImport(options = options,
						queries = project.mfql,
						parent = self,
						worker = worker,
						lipidxplorer = self.lipidxplorer,
						optimization = self.optimized)

			else:
				runLipoX(options = options, queries = project.mfql, parent = self)

		except LipidXException:

			#frame.handleLipidXException()

			evt = wxStdOut(text = '')#v.value)
			if not wx.GetApp().frame.debugOpen:
				wx.GetApp().frame.OnMenuDebugWin(None)
			wx.PostEvent(wx.GetApp().frame, evt)

			(excName, excArgs, excTb, exc) = formatExceptionInfo()
			dlg = wx.MessageDialog(wx.GetApp().frame,"%s" % (exc), "ERROR", wx.OK|wx.ICON_ERROR)
			if dlg.ShowModal() == wx.ID_OK:
				dlg.Destroy()

			self.button_StartImport.Enable()
			self.isRunning = False
			return None

		except ImportException:

			evt = wxStdOut(text = '')#v.value)
			if not wx.GetApp().frame.debugOpen:
				wx.GetApp().frame.OnMenuDebugWin(None)
			wx.PostEvent(wx.GetApp().frame, evt)

			(excName, excArgs, excTb, exc) = formatExceptionInfo()
			dlg = wx.MessageDialog(wx.GetApp().frame,"%s" % (exc), "ERROR", wx.OK|wx.ICON_ERROR)
			if dlg.ShowModal() == wx.ID_OK:
				dlg.Destroy()

			self.button_StartImport.Enable()
			self.isRunning = False
			return None

		except Exception:

			# hijack the exception
			traceback.print_tb(sys.exc_info()[2])
			evt = wxStdOut(text = '')
			if not wx.GetApp().frame.debugOpen:
				wx.GetApp().frame.OnMenuDebugWin(None)
			wx.PostEvent(wx.GetApp().frame, evt)
			(excName, excArgs, excTb, exc) = formatExceptionInfo()
			print(excName, exc)

			text = "The following error occured:\n\n"
			text += "** %s : %s **\n\n\n" % (excName, exc)
			text += "If you think that this a bug in the software you can send\na bug report to the us.\n"
			text += "Do you want to generate the bug report?"
			dlg = wx.MessageDialog(wx.GetApp().frame, text, "ERROR", style=wx.YES_NO|wx.CANCEL|wx.NO_DEFAULT)
			#dlg = MyErrorDialog(wx.GetApp().frame, -1, "ERROR", 'bla')
			r = dlg.ShowModal()
			if r == wx.ID_YES:

				dlg = wx.MessageDialog(wx.GetApp().frame, "Please store the bugReport.html and send it to lifs-support@isas.de", \
						"ERROR", style=wx.OK)
				if dlg.ShowModal() == wx.ID_OK:
					dlg.Destroy()

				strBugReport = """
				<html><head></head><body>
				<h3>%s</h3>
				<h3>%s</h3>
				<h3>%s</h3>
				<p><tt>
				""" % (sys.version, excName, exc)
				for i in excTb:
					strBugReport += "%s<br>" % i
				strBugReport += "</tt></p><br>"
				strBugReport += "%s" % wx.GetApp().frame.genBugReportHTML()
				strBugReport += "</body></html>"

				dlg = wx.FileDialog(wx.GetApp().frame, "Specify the site for the bugReport.html",
					style=wx.DD_DEFAULT_STYLE|wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT,
					defaultFile = "bugReport.html")
				dlg.SetWildcard("*.html files|*.html")

				if dlg.ShowModal() == wx.ID_OK:
					d = dlg.GetPath()
					with open(d, 'w') as f:
						f.write(strBugReport)
					print(d)

			else:
				dlg.Destroy()

			self.button_StartImport.Enable()
			self.isRunning = False
			return None


	def OnAddMFQL(self, evt):

		# open directory with *.dta/*mzXML content
		dlg = wx.FileDialog(self, "Choose a MFQL file", style=wx.DD_DEFAULT_STYLE|wx.FD_OPEN|wx.FD_MULTIPLE)
		dlg.SetWildcard("*.mfql files|*.mfql")

		if dlg.ShowModal() == wx.ID_OK:
			self.filePath_AddMFQL = dlg.GetPaths()

			for p in self.filePath_AddMFQL:
				l = p.split(os.sep)
				self.dictMFQLScripts[l[-1]] = p

			#self.list_box_1.Set(sorted(self.dictMFQLScripts.keys()))
			self.list_box_1.Set(list(self.dictMFQLScripts.keys()))

		dlg.Destroy()

	def OnAddDir(self, evt):

		# open directory with *.dta/*mzXML content
		dlg = wx.DirDialog(self, "Choose a directory with MFQL files", style=wx.DD_DEFAULT_STYLE|wx.DD_DIR_MUST_EXIST)
		#dlg.SetPath(os.getcwd())

		if dlg.ShowModal() == wx.ID_OK:
			self.filePath_MFQLDir = dlg.GetPath()

			for i in os.listdir(self.filePath_MFQLDir):
				if re.match(r'.*\.mfql', i):
					self.dictMFQLScripts[i] = self.filePath_MFQLDir + os.sep + i
			self.list_box_1.Set(list(self.dictMFQLScripts.keys()))

		dlg.Destroy()

	def OnSavePanel(self, evt):

		for key in list(self.dict_button_save.keys()):
			if evt.GetId() == self.dict_button_save[key].GetId():

				# find right page
				for i in range(self.notebook_1.GetPageCount()):
					if self.notebook_1.GetPage(i) == self.dict_button_save[key].GetParent():
						with open(self.dictMFQLScripts[key], 'w') as mfqlFile:
							self.dict_mfqlFile[key] = mfqlFile
							mfqlFile.write(self.dict_text_ctrl[key].GetText())
							self.dict_isChangedAndNotSavedMfqlFile[key] = False
						if key in self.dict_button_save:
							self.dict_button_save[key].SetBackgroundColour((230, 224, 218, 255))

	def OnNewPanel(self, evt):

		self.OnNewFile(evt)
		return None

	def OnSaveAsPanel(self, evt):

		# open directory with *.dta/*mzXML content
		dlg = wx.FileDialog(self, "Specify a filename for the MFQL file", style=wx.DD_DEFAULT_STYLE|wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
		dlg.SetWildcard("*.mfql files|*.mfql")
		#dlg.SetPath(os.getcwd())

		if dlg.ShowModal() == wx.ID_OK:
			p = dlg.GetFilename()
			if not re.match(r'.*\.mfql', p, re.IGNORECASE):
				s = p.split('.')
				if len(s) == 1:
					p += '.mfql'
				else:
					p = ''
					for i in s[:-1]:
						p = '%s.' % i
					p += 'mfql'


			if p not in self.dictMFQLScripts:

				self.dictMFQLScripts[p] = ''
				for i in dlg.GetPath().split(os.sep)[:-1]:
					self.dictMFQLScripts[p] += i + os.sep
				self.dictMFQLScripts[p] += p

				for key in list(self.dict_button_saveAs.keys()):
					if evt.GetId() == self.dict_button_saveAs[key].GetId():

						oldText = key

						# find right page
						for i in range(self.notebook_1.GetPageCount()):
							if self.notebook_1.GetPage(i) == self.dict_button_saveAs[key].GetParent():

								with open(self.dictMFQLScripts[p], 'w') as f:
									f.write(self.dict_text_ctrl[key].GetText())
								self.dict_isChangedAndNotSavedMfqlFile[p] = False
								if key in self.dict_button_save:
									self.dict_button_save[key].SetBackgroundColour((230, 224, 218, 255))



				### remove entry
				#sortedKeys = self.dictMFQLScripts.keys()

				#for index in self.list_box_1.GetSelections():
				#	del self.dictMFQLScripts[key]
				#	self.OnClosePanel(evt, key, secureCheck = False)

				# update list_box in Run panel
				self.list_box_1.Set(list(self.dictMFQLScripts.keys()))
				self.list_box_1.SetSelection(list(self.dictMFQLScripts.keys()).index(p))
				### end remove entry

				# fill the changed text with the original one
				with open(self.dictMFQLScripts[oldText], 'r') as o:
					self.dict_text_ctrl[oldText].SetText(o.read())
				self.dict_isChangedAndNotSavedMfqlFile[oldText] = False
				self.dict_button_save[oldText].SetBackgroundColour((230, 224, 218, 255))

				#self.OnOpenFile(newFile = sorted(self.dictMFQLScripts.keys()).index(p))
				self.OnOpenFile(newFile = -1)

				self.notebook_1.ChangeSelection(self.notebook_1.GetPageCount() - 1)


			else:
				with open(self.dictMFQLScripts[p], 'w') as mfqlFile:
					self.dict_mfqlFile[p] = mfqlFile
					mfqlFile.write(self.dict_text_ctrl[p].GetText())
				self.dict_isChangedAndNotSavedMfqlFile[p] = False
				if p in self.dict_button_save:
					self.dict_button_save[p].SetBackgroundColour((230, 224, 218, 255))

	#self.key_button[i].GetParent().GetParent().RemovePage(n)
	#self.notebook_1.RemovePage(i)

		return None
		#self.list_notebook_editor


####################################### Ballal changed it #############################################

	def OnClosePanel(self, evt, key=None, secureCheck=True):

		if (key or key == 0) and key in self.dict_button_close:
			for i in range(self.notebook_1.GetPageCount()):
				if self.notebook_1.GetPage(i) == self.dict_button_close[key].GetParent():

					if self.dict_isChangedAndNotSavedMfqlFile[key] and secureCheck:
						dlg = wx.MessageDialog(
							self,
							"Modified Query '%s' is not saved! Save it?" % key,
							"Ups...",
							wx.NO | wx.YES | wx.ICON_HAND
						)

						if dlg.ShowModal() == wx.ID_YES:
							with open(self.dictMFQLScripts[key], 'w', encoding='utf-8') as mfqlFile:
								mfqlFile.write(self.dict_text_ctrl[key].GetText())

							self.dict_isChangedAndNotSavedMfqlFile[key] = False
							if key in self.dict_button_save:
								self.dict_button_save[key].SetBackgroundColour((230, 224, 218, 255))

						dlg.Destroy()

					self.notebook_1.RemovePage(i)
					# Ballal - navigate to Run tab after closing an MFQL editor script,
					# instead of falling back to wx's default post-removal selection
					# find the "Run" tab by its actual current page text rather than trusting
					# self.dictNotebookPages, which is off by one from real tab indices (a
					# pre-existing setup bug: counterNotebookPages is incremented BEFORE being
					# stored, so every entry points one tab too far) and was otherwise unused
					# anywhere else in the codebase
					_runTabIndex = None
					for _i in range(self.notebook_1.GetPageCount()):
						if self.notebook_1.GetPageText(_i) == "Run":
							_runTabIndex = _i
							break
					if _runTabIndex is not None:
						wx.CallAfter(self.notebook_1.ChangeSelection, _runTabIndex)
					self.dict_button_close[key].Destroy()
					del self.dict_button_close[key]
					self.dict_button_save[key].Destroy()
					del self.dict_button_save[key]
					self.dict_button_saveAs[key].Destroy()
					del self.dict_button_saveAs[key]
					self.dict_button_new[key].Destroy()
					del self.dict_button_new[key]
					self.dict_text_ctrl[key].Destroy()
					del self.dict_text_ctrl[key]
					self.dict_notebook_editor[key].Destroy()
					del self.dict_notebook_editor[key]

					self.dict_mfqlFile.pop(key, None)

					for k in self.dict_notebook_editor:
						self.dict_notebook_editor[k].Layout()

					return None

		else:
			for key in list(self.dict_button_close.keys()):
				if evt.GetId() == self.dict_button_close[key].GetId():
					for i in range(self.notebook_1.GetPageCount()):
						if self.notebook_1.GetPage(i) == self.dict_button_close[key].GetParent():

							if self.dict_isChangedAndNotSavedMfqlFile[key]:
								dlg = wx.MessageDialog(
									self,
									"Modified Query '%s' is not saved! Save it?" % key,
									"Ups...",
									wx.NO | wx.YES | wx.ICON_HAND
								)

								if dlg.ShowModal() == wx.ID_YES:
									with open(self.dictMFQLScripts[key], 'w', encoding='utf-8') as mfqlFile:
										mfqlFile.write(self.dict_text_ctrl[key].GetText())

									self.dict_isChangedAndNotSavedMfqlFile[key] = False
									if key in self.dict_button_save:
										self.dict_button_save[key].SetBackgroundColour((230, 224, 218, 255))

								dlg.Destroy()

							self.notebook_1.RemovePage(i)
							# navigate to Run tab after closing an MFQL editor script,
							# instead of falling back to wx's default post-removal selection
							# find the "Run" tab by its actual current page text rather than trusting
							# self.dictNotebookPages, which is off by one from real tab indices (a
							# pre-existing setup bug: counterNotebookPages is incremented BEFORE being
							# stored, so every entry points one tab too far) and was otherwise unused
							# anywhere else in the codebase
							_runTabIndex = None
							for _i in range(self.notebook_1.GetPageCount()):
								if self.notebook_1.GetPageText(_i) == "Run":
									_runTabIndex = _i
									break
							if _runTabIndex is not None:
								wx.CallAfter(self.notebook_1.ChangeSelection, _runTabIndex)
							self.dict_button_close[key].Destroy()
							del self.dict_button_close[key]
							self.dict_button_save[key].Destroy()
							del self.dict_button_save[key]
							self.dict_button_saveAs[key].Destroy()
							del self.dict_button_saveAs[key]
							self.dict_button_new[key].Destroy()
							del self.dict_button_new[key]
							self.dict_text_ctrl[key].Destroy()
							del self.dict_text_ctrl[key]
							self.dict_notebook_editor[key].Destroy()
							del self.dict_notebook_editor[key]

							self.dict_mfqlFile.pop(key, None)

							for k in self.dict_notebook_editor:
								self.dict_notebook_editor[k].Layout()

							return None

		return None


	def OnOpenFile(self, evt=None, newFile=None):
		if playSound:
			wx.Sound('../pics/OpenFile.wav').Play()

		sortedKeys = list(self.dictMFQLScripts.keys())

		if newFile is None:
			indices = self.list_box_1.GetSelections()
		else:
			indices = [newFile]

		for index in indices:
			curScript = sortedKeys[index]

			if curScript in self.dict_notebook_editor:
				continue

			panel = wx.Panel(self.notebook_1, -1)
			self.dict_notebook_editor[curScript] = panel

			textctrl = PythonSTC(
				panel, -1,
				style=wx.SIMPLE_BORDER | wx.HSCROLL | wx.ALWAYS_SHOW_SB | wx.TE_MULTILINE | wx.TE_RICH
			)
			self.dict_text_ctrl[curScript] = textctrl

			textctrl.Bind(stc.EVT_STC_CHANGE, self.OnStcChange)
			textctrl.SetZoom(2)
			textctrl.SetMarginType(0, stc.STC_MARGIN_NUMBER)
			textctrl.SetMarginWidth(0, 22)
			textctrl.StyleSetSpec(stc.STC_STYLE_LINENUMBER, "size:9,face:Arial")
			textctrl.SetEOLMode(stc.STC_EOL_LF)

			with open(self.dictMFQLScripts[curScript], "r", encoding="utf-8") as f:
				textctrl.SetText(f.read())

			self.dict_isChangedAndNotSavedMfqlFile[curScript] = False

			btn_new = wx.Button(panel, -1, "New")
			btn_save = wx.Button(panel, -1, "Save")
			btn_save_as = wx.Button(panel, -1, "SaveAs")
			btn_close = wx.Button(panel, -1, "Close")

			self.dict_button_new[curScript] = btn_new
			self.dict_button_save[curScript] = btn_save
			self.dict_button_saveAs[curScript] = btn_save_as
			self.dict_button_close[curScript] = btn_close

			btn_new.Bind(wx.EVT_BUTTON, self.OnNewPanel)
			btn_save.Bind(wx.EVT_BUTTON, self.OnSavePanel)
			btn_save_as.Bind(wx.EVT_BUTTON, self.OnSaveAsPanel)
			btn_close.Bind(wx.EVT_BUTTON, self.OnClosePanel)

			hbox = wx.BoxSizer(wx.HORIZONTAL)
			hbox.Add(btn_new, 0, wx.ALL, 5)
			hbox.Add(btn_save, 0, wx.ALL, 5)
			hbox.Add(btn_save_as, 0, wx.ALL, 5)
			hbox.Add(btn_close, 0, wx.ALL, 5)

			vbox = wx.BoxSizer(wx.VERTICAL)
			vbox.Add(textctrl, 1, wx.ALL | wx.EXPAND, 10)
			vbox.Add(hbox, 0, wx.ALIGN_CENTER)

			panel.SetSizer(vbox)
			panel.Layout()

			self.notebook_1.AddPage(panel, curScript, select=True)

		self.notebook_1.Layout()
#################################################################################################

	# def OnOpenFile(self, evt = None, newFile = None):

	# 	if playSound:
	# 		wx.Sound('../pics/OpenFile.wav').Play()
	# 	sortedKeys = list(self.dictMFQLScripts.keys())

	# 	if not newFile:
	# 		for index in self.list_box_1.GetSelections():

	# 			curScript = [sortedKeys[index]][0]

	# 			# add a page to the notebook
	# 			if self.dict_notebook_editor == {}:
	# 				self.dict_notebook_editor = {curScript : wx.Panel(self.notebook_1, -1)}
	# 			elif curScript not in self.dict_notebook_editor:
	# 				self.dict_notebook_editor[curScript] = wx.Panel(self.notebook_1, -1)
	# 			else:
	# 				return None

	# 			self.notebook_1.AddPage(self.dict_notebook_editor[curScript], curScript)

	# 			# generate textCtrl window
	# 			#self.dict_text_ctrl[curScript] = stc.StyledTextCtrl(self.dict_notebook_editor[curScript], -1, "",
	# 			#	style = wx.SIMPLE_BORDER|wx.HSCROLL|wx.ALWAYS_SHOW_SB|wx.TE_MULTILINE|wx.TE_RICH)#, size = wx.Point(835, 700))
	# 			#self.dict_text_ctrl[curScript] = stc.StyledTextCtrl(self.dict_notebook_editor[curScript],
	# 			#	style = wx.SIMPLE_BORDER|wx.HSCROLL|wx.ALWAYS_SHOW_SB|wx.TE_MULTILINE|wx.TE_RICH)#, size = wx.Point(835, 700))
	# 			self.dict_text_ctrl[curScript] = PythonSTC(self.dict_notebook_editor[curScript], -1,
	# 				style = wx.SIMPLE_BORDER|wx.HSCROLL|wx.ALWAYS_SHOW_SB|wx.TE_MULTILINE|wx.TE_RICH)#, size = wx.Point(835, 700))
	# 	   				# line numbers in the margin

	# 			# stc bindings
	# 			self.dict_text_ctrl[curScript].Bind(stc.EVT_STC_CHANGE, self.OnStcChange)

	# 			self.dict_text_ctrl[curScript].SetZoom(2)
	# 			self.dict_text_ctrl[curScript].SetMarginType(0, stc.STC_MARGIN_NUMBER)
	# 			self.dict_text_ctrl[curScript].SetMarginWidth(0, 22)
	# 			self.dict_text_ctrl[curScript].StyleSetSpec(stc.STC_STYLE_LINENUMBER, "size:9,face:Arial")
	# 			self.dict_text_ctrl[curScript].Colourise(0, -1)

	# 			#self.dict_text_ctrl[curScript].SetSize((835,700))
	# 			#self.dict_text_ctrl[curScript].SetMinSize((800,700))
	# 			self.dict_text_ctrl[curScript].SetMinSize((self.GetSize()[0] - 40, self.GetSize()[1] - 150))

	# 			# open MFQL file
	# 			with open(self.dictMFQLScripts[curScript], 'r') as mfqlFile:
	# 				self.dict_mfqlFile[curScript] = mfqlFile
	# 				for line in self.dict_mfqlFile[curScript].readlines():
	# 					self.dict_text_ctrl[curScript].AppendText(line)
	# 			self.dict_isChangedAndNotSavedMfqlFile[curScript] = False

	# 			# add the close button
	# 			self.dict_button_close[curScript] = wx.Button(self.dict_notebook_editor[curScript], -1, "Close")
	# 			self.dict_button_close[curScript].SetMinSize((140, 34))
	# 			self.Bind(wx.EVT_BUTTON, self.OnClosePanel, self.dict_button_close[curScript])

	# 			# add the save button
	# 			self.dict_button_save[curScript] = wx.Button(self.dict_notebook_editor[curScript], -1, "Save")
	# 			self.dict_button_save[curScript].SetMinSize((140, 34))
	# 			self.Bind(wx.EVT_BUTTON, self.OnSavePanel, self.dict_button_save[curScript])

	# 			# add the saveAs button
	# 			self.dict_button_saveAs[curScript] = wx.Button(self.dict_notebook_editor[curScript], -1, "SaveAs")
	# 			self.dict_button_saveAs[curScript].SetMinSize((140, 34))
	# 			self.Bind(wx.EVT_BUTTON, self.OnSaveAsPanel, self.dict_button_saveAs[curScript])

	# 			# add the new button
	# 			self.dict_button_new[curScript] = wx.Button(self.dict_notebook_editor[curScript], -1, "New")
	# 			self.dict_button_new[curScript].SetMinSize((140, 34))
	# 			self.Bind(wx.EVT_BUTTON, self.OnNewPanel, self.dict_button_new[curScript])

	# 			# put all together with a box sizer
	# 			#self.dict_flex_sizer[curScript] = wx.FlexGridSizer(2,1,3,3)
	# 			self.dict_box_sizer_horizontal[curScript] = wx.BoxSizer(wx.HORIZONTAL)
	# 			self.dict_box_sizer_vertical[curScript] = wx.BoxSizer(wx.VERTICAL)
	# 			self.dict_box_sizer_horizontal[curScript].Add(self.dict_button_new[curScript], 0, wx.ALL|wx.EXPAND, 5)
	# 			self.dict_box_sizer_horizontal[curScript].Add(self.dict_button_save[curScript], 0, wx.ALL|wx.EXPAND, 5)
	# 			self.dict_box_sizer_horizontal[curScript].Add(self.dict_button_saveAs[curScript], 0, wx.ALL|wx.EXPAND, 5)
	# 			self.dict_box_sizer_horizontal[curScript].Add(self.dict_button_close[curScript], 0, wx.ALL|wx.EXPAND, 5)
	# 			self.dict_box_sizer_horizontal[curScript].Fit(self.dict_notebook_editor[curScript])
	# 			#self.dict_flex_sizer[curScript].Add(self.dict_text_ctrl[curScript], 1, wx.ALL|wx.EXPAND|wx.GROW, 10)
	# 			#self.dict_flex_sizer[curScript].Add(self.dict_box_sizer_horizontal[curScript], 0,
	# 			#	wx.ALIGN_CENTER, 0)
	# 			self.dict_box_sizer_vertical[curScript].Add(self.dict_text_ctrl[curScript], 1, wx.ALL|wx.EXPAND|wx.ADJUST_MINSIZE, 10)

	# 			self.dict_box_sizer_vertical[curScript].Add(self.dict_box_sizer_horizontal[curScript], 0,
	# 				wx.ALIGN_CENTER|wx.ADJUST_MINSIZE, 0)

	# 			self.dict_notebook_editor[curScript].SetSizerAndFit(self.dict_box_sizer_vertical[curScript])
	# 			#self.dict_notebook_editor[curScript].SetSizer(self.dict_flex_sizer[curScript])

	# 			#self.dict_notebook_editor[curScript].Fit()
	# 			self.dict_notebook_editor[curScript].Layout()

	# 			#self.Layout()
	# 			#self.SetSize(self.GetSize())

	# 	#	self.SetClientSize(p.GetSize())
	# 		return None

	# 	elif False:

	# 		for index in self.list_box_1.GetSelections():

	# 			curScript = [sortedKeys[index]][0]

	# 			# add a page to the notebook
	# 			if self.dict_notebook_editor == {}:
	# 				self.dict_notebook_editor = {curScript : wx.Panel(self.notebook_1, -1)}
	# 			elif curScript not in self.dict_notebook_editor:
	# 				self.dict_notebook_editor[curScript] = wx.Panel(self.notebook_1, -1)
	# 			else:
	# 				return None

	# 			self.notebook_1.AddPage(self.dict_notebook_editor[curScript], curScript, True)

	# 			# generate textCtrl window
	# 			#self.dict_text_ctrl[curScript] = stc.StyledTextCtrl(self.dict_notebook_editor[curScript], -1, "",
	# 			#	style = wx.SIMPLE_BORDER|wx.HSCROLL|wx.ALWAYS_SHOW_SB|wx.TE_MULTILINE|wx.TE_RICH)#, size = wx.Point(835, 700))
	# 			#self.dict_text_ctrl[curScript] = stc.StyledTextCtrl(self.dict_notebook_editor[curScript],
	# 			#	style = wx.SIMPLE_BORDER|wx.HSCROLL|wx.ALWAYS_SHOW_SB|wx.TE_MULTILINE|wx.TE_RICH)#, size = wx.Point(835, 700))
	# 			self.dict_text_ctrl[curScript] = PythonSTC(self.dict_notebook_editor[curScript], -1,
	# 				style = wx.SIMPLE_BORDER|wx.HSCROLL|wx.ALWAYS_SHOW_SB|wx.TE_MULTILINE|wx.TE_RICH)#, size = wx.Point(835, 700))
	# 	   				# line numbers in the margin

	# 			self.dict_text_ctrl[curScript].Bind(stc.EVT_STC_CHANGE, self.OnStcChange)
	# 			self.dict_text_ctrl[curScript].SetEOLMode(stc.STC_EOL_CR)
	# 			self.dict_text_ctrl[curScript].SetZoom(2)
	# 			self.dict_text_ctrl[curScript].SetMarginType(0, stc.STC_MARGIN_NUMBER)
	# 			self.dict_text_ctrl[curScript].SetMarginWidth(0, 22)
	# 			self.dict_text_ctrl[curScript].StyleSetSpec(stc.STC_STYLE_LINENUMBER, "size:9,face:Arial")

	# 			#self.dict_text_ctrl[curScript].SetSize((835,700))
	# 			#self.dict_text_ctrl[curScript].SetMinSize((800,700))
	# 			self.dict_text_ctrl[curScript].SetMinSize((self.GetSize()[0] - 40, self.GetSize()[1] - 150))

	# 			# open MFQL file
	# 			with open(self.dictMFQLScripts[curScript], 'r') as mfqlFile:
	# 				self.dict_mfqlFile[curScript] = mfqlFile
	# 				for line in self.dict_mfqlFile[curScript].readlines():
	# 					self.dict_text_ctrl[curScript].AppendText(line)
	# 			self.dict_isChangedAndNotSavedMfqlFile[curScript] = False

	# 			# add the close button
	# 			self.dict_button_close[curScript] = wx.Button(self.dict_notebook_editor[curScript], -1, "Close")
	# 			self.dict_button_close[curScript].SetMinSize((140, 34))
	# 			self.Bind(wx.EVT_BUTTON, self.OnClosePanel, self.dict_button_close[curScript])

	# 			# add the save button
	# 			self.dict_button_save[curScript] = wx.Button(self.dict_notebook_editor[curScript], -1, "Save")
	# 			self.dict_button_save[curScript].SetMinSize((140, 34))
	# 			self.Bind(wx.EVT_BUTTON, self.OnSavePanel, self.dict_button_save[curScript])

	# 			# add the saveAs button
	# 			self.dict_button_saveAs[curScript] = wx.Button(self.dict_notebook_editor[curScript], -1, "SaveAs")
	# 			self.dict_button_saveAs[curScript].SetMinSize((140, 34))
	# 			self.Bind(wx.EVT_BUTTON, self.OnSaveAsPanel, self.dict_button_saveAs[curScript])

	# 			# add the new button
	# 			self.dict_button_new[curScript] = wx.Button(self.dict_notebook_editor[curScript], -1, "New")
	# 			self.dict_button_new[curScript].SetMinSize((140, 34))
	# 			self.Bind(wx.EVT_BUTTON, self.OnNewPanel, self.dict_button_new[curScript])

	# 			# put all together with a box sizer
	# 			#self.dict_flex_sizer[curScript] = wx.FlexGridSizer(2,1,3,3)
	# 			self.dict_box_sizer_horizontal[curScript] = wx.BoxSizer(wx.HORIZONTAL)
	# 			self.dict_box_sizer_vertical[curScript] = wx.BoxSizer(wx.VERTICAL)
	# 			self.dict_box_sizer_horizontal[curScript].Add(self.dict_button_new[curScript], 0, wx.ALL|wx.EXPAND, 5)
	# 			self.dict_box_sizer_horizontal[curScript].Add(self.dict_button_save[curScript], 0, wx.ALL|wx.EXPAND, 5)
	# 			self.dict_box_sizer_horizontal[curScript].Add(self.dict_button_saveAs[curScript], 0, wx.ALL|wx.EXPAND, 5)
	# 			self.dict_box_sizer_horizontal[curScript].Add(self.dict_button_close[curScript], 0, wx.ALL|wx.EXPAND, 5)
	# 			self.dict_box_sizer_horizontal[curScript].Fit(self.dict_notebook_editor[curScript])
	# 			#self.dict_flex_sizer[curScript].Add(self.dict_text_ctrl[curScript], 1, wx.ALL|wx.EXPAND|wx.GROW, 10)
	# 			#self.dict_flex_sizer[curScript].Add(self.dict_box_sizer_horizontal[curScript], 0,
	# 			#	wx.ALIGN_CENTER, 0)
	# 			self.dict_box_sizer_vertical[curScript].Add(self.dict_text_ctrl[curScript], 1, wx.ALL|wx.EXPAND|wx.ADJUST_MINSIZE, 10)

	# 			self.dict_box_sizer_vertical[curScript].Add(self.dict_box_sizer_horizontal[curScript], 0,
	# 				wx.ALIGN_CENTER|wx.ADJUST_MINSIZE, 0)

	# 			self.dict_notebook_editor[curScript].SetSizerAndFit(self.dict_box_sizer_vertical[curScript])
	# 			#self.dict_notebook_editor[curScript].SetSizer(self.dict_flex_sizer[curScript])

	# 			#self.dict_notebook_editor[curScript].Fit()
	# 			self.dict_notebook_editor[curScript].Layout()

	# 			#self.Layout()
	# 			#self.SetSize(self.GetSize())

	# 	else:

	# 		curScript = [sortedKeys[newFile]][0]

	# 		# add a page to the notebook
	# 		if self.dict_notebook_editor == {}:
	# 			self.dict_notebook_editor = {curScript : wx.Panel(self.notebook_1, -1)}
	# 		elif curScript not in self.dict_notebook_editor:
	# 			self.dict_notebook_editor[curScript] = wx.Panel(self.notebook_1, -1)
	# 		else:
	# 			return None

	# 		# add the page
	# 		self.notebook_1.AddPage(self.dict_notebook_editor[curScript], curScript, True)

	# 		### generate the layout ###
	# 		# generate textCtrl window
	# 		#self.dict_text_ctrl[curScript] = stc.StyledTextCtrl(self.dict_notebook_editor[curScript], -1, "",
	# 		#	style = wx.SIMPLE_BORDER|wx.HSCROLL|wx.ALWAYS_SHOW_SB|wx.TE_MULTILINE|wx.TE_RICH)#, size = wx.Point(835, 700))
	# 		#self.dict_text_ctrl[curScript] = stc.StyledTextCtrl(self.dict_notebook_editor[curScript],
	# 		#	style = wx.SIMPLE_BORDER|wx.HSCROLL|wx.ALWAYS_SHOW_SB|wx.TE_MULTILINE|wx.TE_RICH)#, size = wx.Point(835, 700))
	# 		self.dict_text_ctrl[curScript] = PythonSTC(self.dict_notebook_editor[curScript], -1,
	# 			style = wx.SIMPLE_BORDER|wx.HSCROLL|wx.ALWAYS_SHOW_SB|wx.TE_MULTILINE|wx.TE_RICH)#, size = wx.Point(835, 700))
	# 	   			# line numbers in the margin

	# 		self.dict_text_ctrl[curScript].Bind(stc.EVT_STC_CHANGE, self.OnStcChange)
	# 		self.dict_text_ctrl[curScript].SetEOLMode(stc.STC_EOL_CR)
	# 		self.dict_text_ctrl[curScript].SetZoom(2)
	# 		self.dict_text_ctrl[curScript].SetMarginType(0, stc.STC_MARGIN_NUMBER)
	# 		self.dict_text_ctrl[curScript].SetMarginWidth(0, 22)
	# 		self.dict_text_ctrl[curScript].StyleSetSpec(stc.STC_STYLE_LINENUMBER, "size:9,face:Arial")

	# 		#self.dict_text_ctrl[curScript].SetSize((835,700))
	# 		#self.dict_text_ctrl[curScript].SetMinSize((800,700))
	# 		self.dict_text_ctrl[curScript].SetMinSize((self.GetSize()[0] - 40, self.GetSize()[1] - 150))

	# 		# open MFQL file
	# 		self.dict_mfqlFile[curScript] = open(self.dictMFQLScripts[curScript], 'r')
	# 		for line in self.dict_mfqlFile[curScript].readlines():
	# 			self.dict_text_ctrl[curScript].AppendText(line)
	# 		self.dict_mfqlFile[curScript].close()
	# 		self.dict_isChangedAndNotSavedMfqlFile[curScript] = False

	# 		# add the close button
	# 		self.dict_button_close[curScript] = wx.Button(self.dict_notebook_editor[curScript], -1, "Close")
	# 		self.dict_button_close[curScript].SetMinSize((140, 34))
	# 		self.Bind(wx.EVT_BUTTON, self.OnClosePanel, self.dict_button_close[curScript])

	# 		# add the save button
	# 		self.dict_button_save[curScript] = wx.Button(self.dict_notebook_editor[curScript], -1, "Save")
	# 		self.dict_button_save[curScript].SetMinSize((140, 34))
	# 		self.Bind(wx.EVT_BUTTON, self.OnSavePanel, self.dict_button_save[curScript])

	# 		# add the saveAs button
	# 		self.dict_button_saveAs[curScript] = wx.Button(self.dict_notebook_editor[curScript], -1, "SaveAs")
	# 		self.dict_button_saveAs[curScript].SetMinSize((140, 34))
	# 		self.Bind(wx.EVT_BUTTON, self.OnSaveAsPanel, self.dict_button_saveAs[curScript])

	# 		# add the new button
	# 		self.dict_button_new[curScript] = wx.Button(self.dict_notebook_editor[curScript], -1, "New")
	# 		self.dict_button_new[curScript].SetMinSize((140, 34))
	# 		self.Bind(wx.EVT_BUTTON, self.OnNewPanel, self.dict_button_new[curScript])

	# 		# put all together with a box sizer
	# 		#self.dict_flex_sizer[curScript] = wx.FlexGridSizer(2,1,3,3)
	# 		self.dict_box_sizer_horizontal[curScript] = wx.BoxSizer(wx.HORIZONTAL)
	# 		self.dict_box_sizer_vertical[curScript] = wx.BoxSizer(wx.VERTICAL)
	# 		self.dict_box_sizer_horizontal[curScript].Add(self.dict_button_new[curScript], 0, wx.ALL|wx.EXPAND, 5)
	# 		self.dict_box_sizer_horizontal[curScript].Add(self.dict_button_save[curScript], 0, wx.ALL|wx.EXPAND, 5)
	# 		self.dict_box_sizer_horizontal[curScript].Add(self.dict_button_saveAs[curScript], 0, wx.ALL|wx.EXPAND, 5)
	# 		self.dict_box_sizer_horizontal[curScript].Add(self.dict_button_close[curScript], 0, wx.ALL|wx.EXPAND, 5)
	# 		self.dict_box_sizer_horizontal[curScript].Fit(self.dict_notebook_editor[curScript])
	# 		#self.dict_flex_sizer[curScript].Add(self.dict_text_ctrl[curScript], 1, wx.ALL|wx.EXPAND|wx.GROW, 10)
	# 		#self.dict_flex_sizer[curScript].Add(self.dict_box_sizer_horizontal[curScript], 0,
	# 		#	wx.ALIGN_CENTER, 0)
	# 		self.dict_box_sizer_vertical[curScript].Add(self.dict_text_ctrl[curScript], 1, wx.ALL|wx.EXPAND|wx.ADJUST_MINSIZE, 10)

	# 		self.dict_box_sizer_vertical[curScript].Add(self.dict_box_sizer_horizontal[curScript], 0,
	# 			wx.ALIGN_CENTER|wx.ADJUST_MINSIZE, 0)

	# 		self.dict_notebook_editor[curScript].SetSizerAndFit(self.dict_box_sizer_vertical[curScript])
	# 		#self.dict_notebook_editor[curScript].SetSizer(self.dict_flex_sizer[curScript])

	# 		#self.dict_notebook_editor[curScript].Fit()
	# 		self.dict_notebook_editor[curScript].Layout()

	# 		#self.Layout()
	# 		#self.SetSize(self.GetSize())
	# 	#	self.SetClientSize(p.GetSize())
	# 		return None

	def OnNewFile(self, evt):

		# open directory with *.dta/*mzXML content
		dlg = wx.FileDialog(self, "Specify a MFQL file",
			style=wx.DD_DEFAULT_STYLE|wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
		dlg.SetWildcard("*.mfql files|*.mfql")

		if dlg.ShowModal() == wx.ID_OK:
			p = dlg.GetFilename()
			#p = dlg.GetPath().split(os.sep)[-1]
			if not re.match(r'.*\.mfql', p, re.IGNORECASE):
				s = p.split('.')
				if len(s) == 1:
					p += '.mfql'
				else:
					p = ''
					for i in s[:-1]:
						p = '%s.' % i
					p += 'mfql'

			self.dictMFQLScripts[p] = ''
			for i in dlg.GetPath().split(os.sep)[:-1]:
				self.dictMFQLScripts[p] += i + os.sep
			self.dictMFQLScripts[p] += p

			self.list_box_1.Set(list(self.dictMFQLScripts.keys()))
			self.list_box_1.SetSelection(list(self.dictMFQLScripts.keys()).index(p), select = True)

			f = open(self.dictMFQLScripts[p], 'w')
			f.write('')
			f.close()
			self.dict_isChangedAndNotSavedMfqlFile[p] = False
			if p in self.dict_button_save:
				self.dict_button_save[p].SetBackgroundColour((230, 224, 218, 255))

			self.OnOpenFile(None)

		pass

	def OnRemoveEntry(self, evt):

		sortedKeys = list(self.dictMFQLScripts.keys())

		for index in self.list_box_1.GetSelections():
			del self.dictMFQLScripts[sortedKeys[index]]
			self.OnClosePanel(evt, sortedKeys[index])

		#self.list_box_1.Set(sorted(self.dictMFQLScripts.keys()))
		self.list_box_1.Set(list(self.dictMFQLScripts.keys()))

	def OnRunLipidX(self, evt):

		if not self.lipidxplorer:
			self.OnStartImport(evt)
			return None

		progressMax = 1

		if not self.text_ctrl_MasterScanSection.IsEmpty():
			# = 1
			progressMax += 1


		# generate one big *mfql script, since windows has a restriction on length of command line
		if len(list(self.dictMFQLScripts.keys())) > 0:
			for k in list(self.dictMFQLScripts.keys()):
				progressMax += 1

		# do a syntax check. The purpose is actually to count the queries. This is nessecary if there
		# should be more than one query per file.
#		try:
#			numQueries = syntaxCheck(self.dictMFQLScripts, masterScan)
#		except SyntaxErrorException:
#			self.handleSyntaxErrorException()
#			return None
#		except Exception:
#			self.handleException()
#			return None

		if self.checkBox_OptionsSection_isocorrect_ms.IsChecked():
			progressMax += 1

		if self.checkBox_OptionsSection_isocorrect_msms.IsChecked():
			progressMax += 1

		if self.checkBox_OptionsSection_complement_sc.IsChecked():
			progressMax += 1

		self.button_RunLipidX.Disable()
		self.isRunning = True

		if not self.debugOpen:
			self.OnMenuDebugWin(None)

		self.debug.progressDialog = wx.ProgressDialog("Processing spectra", "Finished, if the bar is filled completely.",
				progressMax, style = wx.PD_CAN_ABORT)

		
  		
    	# get the options from GUI settings
		project = self.readOptions()
		#project = Options()

		try:

			## test if all options are correct
			project.testOptionsRun()

			# change them into the right format
			project.formatOptions()

			# get options
			options = project.getOptions()
   
			options["batch_mode"] = False

			# put the dump file for dumping without importing
			self.filePath_Dump = options['dumpMasterScanFile']

			# give queues to the Worker class for threadsave data handling
			requestQ = queue.Queue()
			resultQ = queue.Queue()

			# thread
			worker = Worker(self, requestQ, resultQ)

			### start identification ###
			worker.beginThread(startMFQL, queries = self.dictMFQLScripts, parent = self, options = options)

		except LipidXException:

			#frame.handleLipidXException()
			try:
				self.debug.progressDialog.Destroy()
			except:
				pass

			evt = wxStdOut(text = '')#v.value)
			if not wx.GetApp().frame.debugOpen:
				wx.GetApp().frame.OnMenuDebugWin(None)
			wx.PostEvent(wx.GetApp().frame, evt)

			(excName, excArgs, excTb, exc) = formatExceptionInfo()
			dlg = wx.MessageDialog(wx.GetApp().frame,"%s" % (exc), "ERROR", wx.OK|wx.ICON_ERROR)
			if dlg.ShowModal() == wx.ID_OK:
				dlg.Destroy()

			self.button_StartImport.Enable()
			self.button_RunLipidX.Enable()
			self.isRunning = False
			return None

		except ImportException:

			evt = wxStdOut(text = '')#v.value)
			if not wx.GetApp().frame.debugOpen:
				wx.GetApp().frame.OnMenuDebugWin(None)
			wx.PostEvent(wx.GetApp().frame, evt)

			(excName, excArgs, excTb, exc) = formatExceptionInfo()
			dlg = wx.MessageDialog(wx.GetApp().frame,"%s" % (exc), "ERROR", wx.OK|wx.ICON_ERROR)
			if dlg.ShowModal() == wx.ID_OK:
				dlg.Destroy()

			self.button_StartImport.Enable()
			self.isRunning = False
			return None

		except Exception:

			try:
				self.debug.progressDialog.Destroy()
			except:
				pass

			# hijack the exception
			traceback.print_tb(sys.exc_info()[2])
			evt = wxStdOut(text = '')
			if not wx.GetApp().frame.debugOpen:
				wx.GetApp().frame.OnMenuDebugWin(None)
			wx.PostEvent(wx.GetApp().frame, evt)
			(excName, excArgs, excTb, exc) = formatExceptionInfo()
			print(excName, exc)

			text = "The following error occured:\n\n"
			text += "** %s : %s **\n\n\n" % (excName, exc)
			text += "If you think that this a bug in the software you can send\na bug report to the us.\n"
			text += "Do you want to generate the bug report?"
			dlg = wx.MessageDialog(wx.GetApp().frame, text, "ERROR", style=wx.YES_NO|wx.CANCEL|wx.NO_DEFAULT)
			#dlg = MyErrorDialog(wx.GetApp().frame, -1, "ERROR", 'bla')
			r = dlg.ShowModal()
			if r == wx.ID_YES:

				dlg = wx.MessageDialog(wx.GetApp().frame, "Please store the bugReport.html and send it to lifs-support@isas.de", \
						"ERROR", style=wx.OK)
				if dlg.ShowModal() == wx.ID_OK:
					dlg.Destroy()

				strBugReport = """
				<html><head></head><body>
				<h3>%s</h3>
				<h3>%s</h3>
				<h3>%s</h3>
				<p><tt>
				""" % (sys.version, excName, exc)
				for i in excTb:
					strBugReport += "%s<br>" % i
				strBugReport += "</tt></p><br>"
				strBugReport += "%s" % wx.GetApp().frame.genBugReportHTML()
				strBugReport += "</body></html>"

				dlg = wx.FileDialog(wx.GetApp().frame, "Specify the site for the bugReport.html",
					style=wx.DD_DEFAULT_STYLE|wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT,
					defaultFile = "bugReport.html")
				dlg.SetWildcard("*.html files|*.html")

				if dlg.ShowModal() == wx.ID_OK:
					d = dlg.GetPath()
					f = open(d, 'w')
					f.write(strBugReport)
					f.close()
					print(d)

			else:
				dlg.Destroy()

			self.button_RunLipidX.Enable()
			self.button_StartImport.Enable()
			self.isRunning = False
			return None

	def OnMassToSumComposition(self, evt):

		if self.text_ctrl_mstools_InputSection_mz.IsEmpty():
			dlg = wx.MessageDialog(self, "You have to give a m/z value!", "Attention", wx.OK|wx.ICON_HAND)
			if dlg.ShowModal() == wx.ID_OK:
				dlg.Destroy()
				return None
		else:
			mass = self.text_ctrl_mstools_InputSection_mz.GetValue()

		if self.text_ctrl_mstools_InputSection_sumComposition.IsEmpty():
			dlg = wx.MessageDialog(self, "You have to give a sf-constraint!", "Attention", wx.OK|wx.ICON_HAND)
			if dlg.ShowModal() == wx.ID_OK:
				dlg.Destroy()
				return None
		else:
			sf_constraint = self.text_ctrl_mstools_InputSection_sumComposition.GetValue()

		if self.text_ctrl_mstools_InputSection_doubleBond_1.IsEmpty():
			dlg = wx.MessageDialog(self, "You have to give a lower double bond border!", "Attention", wx.OK|wx.ICON_HAND)
			if dlg.ShowModal() == wx.ID_OK:
				dlg.Destroy()
				return None
		else:
			lowerDB = self.text_ctrl_mstools_InputSection_doubleBond_1.GetValue()

		if self.text_ctrl_mstools_InputSection_doubleBond_2.IsEmpty():
			dlg = wx.MessageDialog(self, "You have to give a higher double bond border!", "Attention", wx.OK|wx.ICON_HAND)
			if dlg.ShowModal() == wx.ID_OK:
				dlg.Destroy()
				return None
		else:
			higherDB = self.text_ctrl_mstools_InputSection_doubleBond_2.GetValue()

		if self.text_ctrl_mstools_InputSection_charge.IsEmpty():
			charge = ' chg(0)'
		else:
			charge = ' chg(%s)' % self.text_ctrl_mstools_InputSection_charge.GetValue()

		if self.text_ctrl_mstools_InputSection_accuracy.IsEmpty():
			accuracy = '5'
		else:
			accuracy = self.text_ctrl_mstools_InputSection_accuracy.GetValue()

		strDB = ' db(%.1f,%.1f)' % (float(lowerDB), float(higherDB))

		t = float(mass) / ((float(mass) / 1000000) * float(accuracy))## 21.02.25: Ballal chacged the value to 1000000. Before it was 100000

		elscp = parseElemSeq(sf_constraint + strDB + charge)
		rslt = calcSFbyMass(float(mass), elscp, t, False)

		if rslt == []:
			outtext = "No sum composition found for %s with m/z %.4f" % (elscp, float(mass))

		for i in rslt:
			outtext = "m/z: %.4f sc: %s error: %.4f Da" % ( ## 21.02.25: Ballal chacged the error in Da. Before it was ppm
					i.getWeight(),
					i,
					(float(mass) - i.getWeight()))


		self.text_ctrl_mstools_OutputSection.SetValue(outtext)


	def OnSumCompositionToMass(self, evt):

		if playSound:
			wx.Sound('../pics/PressButton.wav').Play(flags = wx.SOUND_ASYNC)

		strAccuracy = ''

		if self.text_ctrl_mstools_InputSection_sumComposition.IsEmpty():
			dlg = wx.MessageDialog(self, "You have to give a sum composition!", "Attention", wx.OK|wx.ICON_HAND)
			if dlg.ShowModal() == wx.ID_OK:
				dlg.Destroy()
				return None
		else:
			sf_constraint = self.text_ctrl_mstools_InputSection_sumComposition.GetValue()

		if self.text_ctrl_mstools_InputSection_charge.IsEmpty():
			charge = ' chg(0)'
		else:
			charge = ' chg(%s)' % self.text_ctrl_mstools_InputSection_charge.GetValue()

		elemSeq = parseElemSeq(sf_constraint + charge)

		max = 1

		if playSound:
			sound = wx.Sound('../pics/Wait2.wav')
			sound.Play(flags = wx.SOUND_LOOP|wx.SOUND_ASYNC)

		outtext = "For %s:\nExact mass is %.6f; Double Bonds are: %.1f; charge is: %d" % (elemSeq, elemSeq.getWeight(), elemSeq.get_DB(), elemSeq.charge)
		self.text_ctrl_mstools_OutputSection.SetValue(outtext)

		if playSound:
			sound.Stop()
		pass

	def OnCalcIsotopes(self, evt):


		if self.text_ctrl_mstools_Isotopes_precursor.IsEmpty():
			dlg = wx.MessageDialog(self, "You have to give a sum composition!", "Attention", wx.OK|wx.ICON_HAND)
			if dlg.ShowModal() == wx.ID_OK:
				dlg.Destroy()
				return None
		else:
			sumComp = parseElemSeq(self.text_ctrl_mstools_Isotopes_precursor.GetValue())

		if self.text_ctrl_mstools_Isotopes_fragment.IsEmpty():
			sumCompFrg = None
		else:
			sumCompFrg = parseElemSeq(self.text_ctrl_mstools_Isotopes_fragment.GetValue())

		if sumCompFrg:
			# is a neutral loss
			if self.checkBox_mstools_Isotopes_nl.GetValue():
				monoisotopic = 1.0
				sumCompNL = sumComp - sumCompFrg
				(Mtx, monoistopic) = isotopicValuesInter(sumCompNL['C'], sumCompNL['H'], sumCompNL['O'], \
						sumCompNL['N'], sumCompNL['P'], sumCompNL['P'], sumCompFrg['C'], sumCompFrg['H'], \
						sumCompNL['O'], sumCompFrg['N'], sumCompFrg['S'], sumCompFrg['P'])
				str = "F:%s; N:%s\n ------------- \n" % (repr(sumCompNL), repr(sumCompFrg))
				str += "     F0N0: %.4f\n" % Mtx[0][0]
				str += "     F0N1: %.4f, F1N0: %.4f\n" % (Mtx[0][1], Mtx[1][0])
				str += "     F0N2: %.4f, F1N1: %.4f, F2N0: %.4f\n" % (Mtx[0][2], Mtx[1][1], Mtx[2][0])
				str += "     F0N3: %.4f, F1N2: %.4f, F2N1: %.4f, F3N0: %.4f\n" % (Mtx[0][3], Mtx[1][2], Mtx[2][1], Mtx[3][0])
				str += "     F0N4: %.4f, F1N3: %.4f, F2N2: %.4f, F3N1: %.4f, F4N0: %.4f\n" % (Mtx[0][4], Mtx[1][3], Mtx[2][2], Mtx[3][1], Mtx[4][0])

				self.text_ctrl_mstools_Isotopes_output.SetValue(str)
				pass
			# is a fragment
			else:
				monoisotopic = 1.0
				sumCompNL = sumComp - sumCompFrg
				(Mtx, monoisotopic) = isotopicValuesInter(sumCompFrg['C'], sumCompFrg['H'], sumCompFrg['O'], \
						sumCompFrg['N'], sumCompFrg['S'], sumCompFrg['P'], sumCompNL['C'], sumCompNL['H'], \
						sumCompNL['O'], sumCompNL['N'], sumCompNL['S'], sumCompNL['P'])

				str = "F:%s; N:%s\n ------------- \n" % (repr(sumCompFrg), repr(sumCompNL))
				str += "     F0N0: %.4f\n" % Mtx[0][0]
				str += "     F0N1: %.4f, F1N0: %.4f\n" % (Mtx[0][1], Mtx[1][0])
				str += "     F0N2: %.4f, F1N1: %.4f, F2N0: %.4f\n" % (Mtx[0][2], Mtx[1][1], Mtx[2][0])
				str += "     F0N3: %.4f, F1N2: %.4f, F2N1: %.4f, F3N0: %.4f\n" % (Mtx[0][3], Mtx[1][2], Mtx[2][1], Mtx[3][0])
				str += "     F0N4: %.4f, F1N3: %.4f, F2N2: %.4f, F3N1: %.4f, F4N0: %.4f\n" % (Mtx[0][4], Mtx[1][3], Mtx[2][2], Mtx[3][1], Mtx[4][0])

				self.text_ctrl_mstools_Isotopes_output.SetValue(str)
				pass
		else:

			(mz, intens, monoisotopic) = isotopicValues(sumComp['C'], sumComp['H'], sumComp['O'], \
						sumComp['N'], sumComp['S'], sumComp['P'])

			str = '\nMonoisotopic m/z: %.4f \n' % intens[0] * monoisotopic
			str += '    m/z    abundance  \n'
			for index in range(len(mz)):
				#str += "%.4f %.4f\n" % (mz[index], intens[index])
				str += "%.4f   %.4f\n" % (sumComp.getWeight() + 1.00055 * index, intens[index] * monoisotopic)
			self.text_ctrl_mstools_Isotopes_output.SetValue(str)

		pass
################## ballal edited it ##################
	def collectSettings(self, setting):
		import re
		import configparser

		self.opts = {}
		self.optsImport = {}
		self.optsRun = {}

		try:
			# Helper to get config value safely
			def get_opt(name, default=None):
				return self.confParse.get(setting, name) if self.confParse.has_option(setting, name) else default

			# Numeric ranges ---------------------------------------------------------
			def parse_range(opt_name):
				val = get_opt(opt_name)
				if val:
					m = re.match(r'\(\s*(\d+)\s*,\s*(\d+)\s*\)', val)
					if m:
						return f"({m.group(1)},{m.group(2)})"
				return None

			# Assign ranges
			self.optsImport['timerange'] = parse_range('timerange')
			self.optsImport['MSmassrange'] = parse_range('MSmassrange')
			self.optsImport['MSMSmassrange'] = parse_range('MSMSmassrange')

			# Thresholds ------------------------------------------------------------
			self.optsImport['MSminOccupation'] = get_opt('MSminOccupation', '')
			self.optsImport['MSMSminOccupation'] = get_opt('MSMSminOccupation', '')
			self.optsImport['MSthreshold'] = get_opt('MSthreshold', '')
			self.optsImport['MSMSthreshold'] = get_opt('MSMSthreshold', '')
			self.optsImport['MSthresholdType'] = get_opt('MSthresholdType', 'absolute')
			self.optsImport['MSMSthresholdType'] = get_opt('MSMSthresholdType', 'absolute')

			# Resolution ------------------------------------------------------------
			self.optsImport['MSresolution'] = get_opt('MSresolution', '')
			self.optsImport['MSMSresolution'] = get_opt('MSMSresolution', '')
			self.optsImport['MSresolutionDelta'] = get_opt('MSresolutionDelta', '')
			self.optsImport['MSMSresolutionDelta'] = get_opt('MSMSresolutionDelta', '')

			# Calibration / filters -------------------------------------------------
			self.optsImport['MScalibration'] = get_opt('MScalibration', '')
			self.optsImport['MSMScalibration'] = get_opt('MSMScalibration', '')
			self.optsImport['MSfilter'] = get_opt('MSfilter', '')
			self.optsImport['MSMSfilter'] = get_opt('MSMSfilter', '')

			# Tolerances ------------------------------------------------------------
			def parse_tolerance(opt_name, default_val='0', default_unit='ppm'):
				val = get_opt(opt_name)
				if not val:
					return default_val, default_unit
				if re.match(r'(\d+(\.\d+)?)$', val):
					return val, default_unit
				m = re.match(r'(\d+(\.\d+)?)(\s)*(ppm|Da)', val)
				if m:
					return m.group(1), m.group(4)
				return default_val, default_unit

			self.optsImport['MStolerance'], self.optsImport['MStoleranceType'] = parse_tolerance('MStolerance')
			self.optsImport['MSMStolerance'], self.optsImport['MSMStoleranceType'] = parse_tolerance('MSMStolerance')

			# Optional tolerances (defaults)
			self.optsImport['optionalMStolerance'] = ''
			self.optsImport['optionalMSMStolerance'] = ''
			self.optsImport['optionalMStoleranceType'] = 'ppm'
			self.optsImport['optionalMSMStoleranceType'] = 'ppm'
			self.optsImport['optionalMSthreshold'] = None
			self.optsImport['optionalMSMSthreshold'] = None
			self.optsImport['optionalMSthresholdType'] = None
			self.optsImport['optionalMSMSthresholdType'] = None

			# Other parameters ------------------------------------------------------
			self.optsImport['selectionWindow'] = get_opt('selectionWindow', '')
			self.optsImport['precursorMassShift'] = get_opt('precursorMassShift', '')
			self.optsImport['precursorMassShiftOrbi'] = get_opt('precursorMassShiftOrbi', '')

			# Default alignment and averaging methods
			self.optsImport['alignmentMethodMS'] = get_opt('alignmentMethodMS', 'linear')
			self.optsImport['alignmentMethodMSMS'] = get_opt('alignmentMethodMSMS', 'linear')
			self.optsImport['scanAveragingMethod'] = get_opt('scanAveragingMethod', 'linear')

			# Boolean options with clean conversion ---------------------------------
			def get_bool_opt(name, default=False):
				val = get_opt(name)
				if val is None:
					return default
				if isinstance(val, str):
					return val.strip().lower() in ['1', 'true', 'yes', 'on']
				return bool(val)

			bool_fields = {
				'isotopicCorrection_MSMS': False,
				'removeIsotopes': False,
				'isotopesInMasterScan': False,
				'monoisotopicCorrection': False,
				'relativeIntensity': False,
				'logMemory': False,
				'intensityCorrection': False,
				'masterScanInSQL': False,
				'sumFattyAcids': False,
				'isotopicCorrectionMS': True,
				'isotopicCorrectionMSMS': True,
				'complementMasterScan': False,
				'noHead': False,
				'compress': False,
				'tabLimited': False,
				'dumpMasterScan': False,
				'statistics': False,
				'noPermutations': True,
				'settingsPrefix': False,
			}

			for k, default in bool_fields.items():
				self.optsImport[k] = get_bool_opt(k, default)

			# Fill placeholders / unused options ------------------------------------
			self.optsImport['intensityCorrectionPrecursor'] = ''
			self.optsImport['intensityCorrectionFragment'] = ''
			self.optsImport['complementMasterScanFile'] = None
			self.optsImport['dumpMasterScanFile'] = None
			self.optsImport['mzXML'] = None
			self.optsImport['loopNr'] = 3

			# Copy import → run
			self.optsRun.update(self.optsImport)

		except configparser.NoSectionError:
			pass
#######################################################

	def getMasterScanInfo(self):

		# Run Panel
		masterScan = self.text_ctrl_MasterScanSection.GetValue()

		if masterScan != '':
			try:
				masterscan = loadSC(masterScan)
			except:
				return " ... error loading the MasterScan file ..."
		else:
			return ""

		MSthresholdType = ""
		MSMSthresholdType = ""
		if masterscan.options['MSthresholdType'] == 'relative': MSthresholdType = "%"
		if masterscan.options['MSMSthresholdType'] == 'relative': MSMSthresholdType = "%"

		strOut = ""
		#strOut += "\nMasterScan: ," + self.name
		strOut += "\n<h4>Loaded MasterScan</h4>\n"
		strOut += "<table>"
		strOut += "<tr><td>time range:</td><td>(%s, %s)</td></tr>\n" % (repr(masterscan.options['timerange'][0]), repr(masterscan.options['timerange'][1]))
		strOut += "<tr><td>MS m/z range:</td><td>(%s, %s)</td></tr>\n" % (repr(masterscan.options['MSmassrange'][0]), repr(masterscan.options['MSmassrange'][1]))
		strOut += "<tr><td>MS/MS m/z range:</td><td>(%s, %s)</td></tr>\n" % (repr(masterscan.options['MSMSmassrange'][0]), repr(masterscan.options['MSMSmassrange'][1]))
		strOut += "<tr><td>MS tolerance:</td><td>+/- %s</td></tr>\n" % (repr(masterscan.options['MStolerance']))
		strOut += "<tr><td>MS/MS tolerance:</td><td>+/- %s</td></tr>\n" % (repr(masterscan.options['MSMStolerance']))
		strOut += "<tr><td>MS resolution:</td><td>%s</td></tr>\n" % (repr(masterscan.options['MSresolution']))
		strOut += "<tr><td>MS/MS resolution:</td><td>%s</td></tr>\n" % (repr(masterscan.options['MSMSresolution']))
		strOut += "<tr><td>MS resolution gradient:</td><td>%s</td></tr>\n" % (repr(masterscan.options['MSminOccupation']))
		strOut += "<tr><td>MS/MS resolution gradient:</td><td>%s</td></tr>\n" % (repr(masterscan.options['MSMSminOccupation']))
		strOut += "<tr><td>MS threshold:</td><td>%s%s</td></tr>\n" % (repr(masterscan.options['MSthreshold']), MSthresholdType)
		strOut += "<tr><td>MS/MS threshold:</td><td>%s%s</td></tr>\n" % (repr(masterscan.options['MSMSthreshold']), MSMSthresholdType)
		strOut += "<tr><td>MS minimum occupation:</td><td>+/- %s</td></tr>\n" % (repr(masterscan.options['MSminOccupation']))
		strOut += "<tr><td>MS/MS minimum occupation:</td><td>+/- %s</td></tr>\n" % (repr(masterscan.options['MSMSminOccupation']))
		strOut += "<tr><td>MS frequency filter:</td><td>+/- %s</td></tr>\n" % (repr(masterscan.options['MSfilter']))
		strOut += "<tr><td>MS/MS frequency filter:</td><td>+/- %s</td></tr>\n" % (repr(masterscan.options['MSMSfilter']))
		strOut += "</table>\n\n"

		return strOut

	def genBugReportHTML(self, options = {}):

		if options == {}:
			self.collectSettings(self.currentConfiguration)
			#options = self.optsRun + self.optsImport
			options = self.optsRun

		#strMasterScan = self.getMasterScanInfo()
		#self.optsRun['mfqlFiles'] = self.dictMFQLScripts

		strBugReport = "<h3>Options</h3>\n"

		strBugReport += "<table>\n"
		for k in list(options.keys()):
			strBugReport += "<tr><td>%s:</td><td>%s</td></tr>\n" % (k, options[k])
		strBugReport += "</table><br>\n"

		#strBugReport += "<h3>MFQL Panel</h3>\n"

		#strBugReport += strMasterScan
		#strBugReport += "<br><h4>Panel Settings</h4>"

		#strBugReport += "<table>\n"
		#for k in self.optsRun.keys():
		#	if k != 'mfqlFiles':
		#		strBugReport += "<tr><td>%s:</td><td>%s</td></tr>\n" % (k, self.optsRun[k])
		#strBugReport += "</table>\n"

		strBugReport += "<h3>MFQL queries</h3><tt>\n"
		for i in self.dictMFQLScripts:
			txt = ''
			f = open(self.dictMFQLScripts[i], 'r')
			txt += " \n\n>> filename: %s >>\n\n" % i
			txt += f.read()
			strBugReport += txt.replace('\n', '<br>')
			f.close()
		strBugReport += "</tt>"

		#strBugReport += self.optsRun['mfqlFiles']

		return strBugReport

	def genBugReport(self):

		self.collectSettings(self.currentConfiguration)
		self.optsRun['mfqlFiles'] = self.dictMFQLScripts

		strBugReport = "\nImport Panel\n\n"

		for k in list(self.optsImport.keys()):
			strBugReport += "%s:\t\t%s\n" % (k, self.optsImport[k])

		strBugReport += "\n\nMFQL Panel\n\n"
		for k in list(self.optsRun.keys()):
			if k != 'mfqlFiles':
				strBugReport += "%s:\t\t%s\n" % (k, self.optsRun[k])

		strBugReport += "\n\nMFQL queries\n\n"
		for i in self.optsRun['mfqlFiles']:
			f = open(self.optsRun['mfqlFiles'][i], 'r')
			strBugReport += f.read()
			f.close()
		#strBugReport += self.optsRun['mfqlFiles']

		return strBugReport

	def __set_properties(self):

		button1_w = 140
		button1_h = 24
		button1_small_w = button1_w / 2 - 5
		button1_small_h = 24

		button2_w = 450
		button2_h = 34

		textCtrl_small_w = 90
		textCtrl_small_h = 22
		textCtrl_big_w = 440
		textCtrl_big_h = 22

		# begin wxGlade: LpdxFrame.__set_properties
		if self.lipidxplorer:
			self.SetTitle("LipidXplorer %s" % self.version)
		else:
			self.SetTitle("LipOXplorer %s" % self.version)

		self.SetMinSize((720, 660))
		self.SetSize((1000, 730))

		self.list_box_1.SetMinSize((textCtrl_big_w, 211))

		self.text_ctrl_mstools_InputSection_mz.SetMinSize((textCtrl_small_w - 20, textCtrl_small_h))
		self.text_ctrl_mstools_InputSection_sumComposition.SetMinSize((textCtrl_big_w - 120, textCtrl_small_h))
		self.text_ctrl_mstools_InputSection_doubleBond_1.SetMinSize((textCtrl_small_w - 60, textCtrl_small_h))
		self.text_ctrl_mstools_InputSection_doubleBond_2.SetMinSize((textCtrl_small_w - 60, textCtrl_small_h))
		self.text_ctrl_mstools_InputSection_charge.SetMinSize((textCtrl_small_w - 60, textCtrl_small_h))
		self.text_ctrl_mstools_InputSection_accuracy.SetMinSize((textCtrl_small_w - 60, textCtrl_small_h))
		self.text_ctrl_mstools_OutputSection.SetMinSize((660, textCtrl_small_h * 6))

		self.text_ctrl_mstools_InputSection_mz.SetMaxSize((textCtrl_small_w - 20, textCtrl_small_h))
		self.text_ctrl_mstools_InputSection_sumComposition.SetMaxSize((textCtrl_big_w - 120, textCtrl_small_h))
		self.text_ctrl_mstools_InputSection_doubleBond_1.SetMaxSize((textCtrl_small_w - 60, textCtrl_small_h))
		self.text_ctrl_mstools_InputSection_doubleBond_2.SetMaxSize((textCtrl_small_w - 60, textCtrl_small_h))
		self.text_ctrl_mstools_InputSection_charge.SetMaxSize((textCtrl_small_w - 60, textCtrl_small_h))
		self.text_ctrl_mstools_InputSection_accuracy.SetMaxSize((textCtrl_small_w - 60, textCtrl_small_h))
		self.text_ctrl_mstools_OutputSection.SetMaxSize((660, textCtrl_small_h * 6))

		self.button_AddMFQL.SetMinSize((button1_w, button1_h))
		self.button_RemoveEntry.SetMinSize((button1_w, button1_h))
		self.button_OpenFile.SetMinSize((button1_w, button1_h))
		self.button_NewFile.SetMinSize((button1_w, button1_h))
		self.button_AddDir.SetMinSize((button1_w, button1_h))

		self.button_Browse_MasterScan.SetMinSize((button1_w, button1_h))
		self.button_Browse_OutputSection.SetMinSize((button1_small_w, button1_h))
		self.button_Open_OutputSection.SetMinSize((button1_small_w, button1_h))
		#self.button_Browse_DumpSection.SetMinSize((button1_w, button1_h))
		self.button_Open_DumpSection.SetMinSize((button1_w, button1_h))
		self.button_RunLipidX.SetMinSize((button2_w, button2_h))
		self.button_StartImport.SetMinSize((button2_w, button2_h))
		self.button_Browse_ImportDataSection.SetMinSize((button1_small_w, button1_h))
		self.button_Browse_OutputMasterScanSection.SetMinSize((button1_w, button1_h))
		self.button_Browse_LoadIniSection.SetMinSize((button1_w, button1_h))
		
		#self.button_SelectSettingSection_edit.SetMinSize((button1_w, button1_h))
		#self.button_SelectSettingSection_new.SetMinSize((button1_w, button1_h))
		#self.button_SelectSettingSection_remove.SetMinSize((button1_w, button1_h))

		self.text_ctrl_OutputSection.SetMinSize((textCtrl_big_w, textCtrl_big_h))
		self.text_ctrl_RunOptions_MS.SetMinSize((button1_small_w, button1_h))
		self.text_ctrl_RunOptions_MSMS.SetMinSize((button1_small_w, button1_h))
		self.text_ctrl_MasterScanSection.SetMinSize((textCtrl_big_w, textCtrl_big_h))
		self.text_ctrl_OutputMasterScanSection.SetMinSize((textCtrl_big_w, textCtrl_big_h))
		self.text_ctrl_ImportDataSection.SetMinSize((textCtrl_big_w / 2 + 200, textCtrl_big_h))
		self.text_ctrl_LoadIniSection.SetMinSize((textCtrl_big_w, textCtrl_big_h))

		self.text_ctrl_SettingsSection_precursorMassShift.SetMinSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_precursorMassShift.SetMaxSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_precursorMassShiftOrbi.SetMinSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_precursorMassShiftOrbi.SetMaxSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_selectionWindow.SetMinSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_selectionWindow.SetMaxSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_timerange1.SetMinSize((textCtrl_small_w / 2 - 5, textCtrl_small_h))
		self.text_ctrl_SettingsSection_timerange2.SetMinSize((textCtrl_small_w / 2 - 5, textCtrl_small_h))
		self.text_ctrl_SettingsSection_timerange1.SetMaxSize((textCtrl_small_w / 2 - 5, textCtrl_small_h))
		self.text_ctrl_SettingsSection_timerange2.SetMaxSize((textCtrl_small_w / 2 - 5, textCtrl_small_h))
		self.text_ctrl_SettingsSection_massrange_ms1.SetMinSize((textCtrl_small_w / 2 - 5, textCtrl_small_h))
		self.text_ctrl_SettingsSection_massrange_ms2.SetMinSize((textCtrl_small_w / 2 - 5, textCtrl_small_h))
		self.text_ctrl_SettingsSection_massrange_ms1.SetMaxSize((textCtrl_small_w / 2 - 5, textCtrl_small_h))
		self.text_ctrl_SettingsSection_massrange_ms2.SetMaxSize((textCtrl_small_w / 2 - 5, textCtrl_small_h))
		self.text_ctrl_SettingsSection_massrange_msms1.SetMinSize((textCtrl_small_w / 2 - 5, textCtrl_small_h))
		self.text_ctrl_SettingsSection_massrange_msms2.SetMinSize((textCtrl_small_w / 2 - 5, textCtrl_small_h))
		self.text_ctrl_SettingsSection_massrange_msms1.SetMaxSize((textCtrl_small_w / 2 - 5, textCtrl_small_h))
		self.text_ctrl_SettingsSection_massrange_msms2.SetMaxSize((textCtrl_small_w / 2 - 5, textCtrl_small_h))
		self.text_ctrl_SettingsSection_resolution_ms.SetMinSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_resolution_ms.SetMaxSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_resolution_msms.SetMinSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_resolution_msms.SetMaxSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_tolerance_ms.SetMinSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_tolerance_ms.SetMaxSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_tolerance_msms.SetMinSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_tolerance_msms.SetMaxSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_threshold_ms.SetMinSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_threshold_ms.SetMaxSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_threshold_msms.SetMinSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_threshold_msms.SetMaxSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_occupationThr_ms.SetMinSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_occupationThr_ms.SetMaxSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_occupationThr_msms.SetMinSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_occupationThr_msms.SetMaxSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_resDelta_ms.SetMinSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_resDelta_ms.SetMaxSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_resDelta_msms.SetMinSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_resDelta_msms.SetMaxSize((textCtrl_small_w, textCtrl_small_h))
		self.text_ctrl_SettingsSection_calibration_ms.SetMinSize((textCtrl_small_w * 2, textCtrl_small_h))
		self.text_ctrl_SettingsSection_calibration_ms.SetMaxSize((textCtrl_small_w * 2, textCtrl_small_h))
		self.text_ctrl_SettingsSection_calibration_msms.SetMinSize((textCtrl_small_w * 2, textCtrl_small_h))
		self.text_ctrl_SettingsSection_calibration_msms.SetMaxSize((textCtrl_small_w * 2, textCtrl_small_h))

		self.text_ctrl_SettingsSection_filter_ms.SetMinSize((textCtrl_small_w * 2, textCtrl_small_h))
		self.text_ctrl_SettingsSection_filter_ms.SetMaxSize((textCtrl_small_w * 2, textCtrl_small_h))
		self.text_ctrl_SettingsSection_filter_msms.SetMinSize((textCtrl_small_w * 2, textCtrl_small_h))
		self.text_ctrl_SettingsSection_filter_msms.SetMaxSize((textCtrl_small_w * 2, textCtrl_small_h))

		self.text_ctrl_mstools_OutputSection.SetMinSize((textCtrl_big_w, textCtrl_big_h * 3))
		self.text_ctrl_mstools_OutputSection.SetMaxSize((textCtrl_big_w * 2, textCtrl_big_h * 3))
		self.text_ctrl_mstools_Isotopes_output.SetMinSize((textCtrl_big_w, textCtrl_big_h * 6))
		self.text_ctrl_mstools_Isotopes_output.SetMaxSize((textCtrl_big_w * 2, textCtrl_big_h * 6))

		self.notebook_1_pane_5.SetMinSize((835, 800))
		self.notebook_1_pane_4.SetMinSize((835, 800))
		self.notebook_1_pane_3.SetMinSize((835, 800))
		self.notebook_1_pane_2.SetMinSize((835, 800))
		self.button_open_next.SetMinSize((260, 42))
		self.button_open_legacy.SetMinSize((260, 42))
		self.button_back_from_placeholder.SetMinSize((48, 20))
		self.button_back_to_start.SetMinSize((48, 20))
		self.label_placeholder_title.SetFont(self.header_font)
		self.label_placeholder_message.SetFont(self.font)
		self.label_placeholder_demo.SetFont(self.font)
		self.label_placeholder_demo.SetForegroundColour(wx.Colour(80, 80, 80))
		self.link_placeholder_demo.SetNormalColour(wx.Colour(0, 102, 204))
		self.link_placeholder_demo.SetVisitedColour(wx.Colour(85, 26, 139))
		self.link_placeholder_demo.SetHoverColour(wx.Colour(0, 102, 204))
		# end wxGlade

	def __do_layout(self):

		border_labels = 4

		# #### TOOL pane ###
		sizer_toolPane = wx.BoxSizer(wx.VERTICAL)
		sizer_toolPane.Add(self.label_mstools_InputSection, 0, wx.ALIGN_LEFT | wx.ALL, 10)
		# sizer_toolPane.Add((10,10)) # Commented out as it's a fixed spacer

		sizer_toolPane_3 = wx.BoxSizer(wx.VERTICAL)
		sizer_toolPane_3.Add(self.label_mstools_InputSection_mz, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, 5)
		sizer_toolPane_3.Add(self.text_ctrl_mstools_InputSection_mz, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, 5)

		sizer_toolPane_4 = wx.BoxSizer(wx.VERTICAL)
		sizer_toolPane_4.Add(self.label_mstools_InputSection_sumComposition, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, 5)
		sizer_toolPane_4.Add(self.text_ctrl_mstools_InputSection_sumComposition, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, 5)

		sizer_toolPane_8 = wx.BoxSizer(wx.VERTICAL)
		sizer_toolPane_8.Add(self.label_mstools_InputSection_doubleBond_1, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, 5)
		sizer_toolPane_8.Add(self.text_ctrl_mstools_InputSection_doubleBond_1, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, 5)

		sizer_toolPane_9 = wx.BoxSizer(wx.VERTICAL)
		sizer_toolPane_9.Add(self.label_mstools_InputSection_doubleBond_2, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, 5)
		sizer_toolPane_9.Add(self.text_ctrl_mstools_InputSection_doubleBond_2, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, 5)

		sizer_toolPane_6 = wx.BoxSizer(wx.VERTICAL)
		sizer_toolPane_6.Add(self.label_mstools_InputSection_charge, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, 5)
		sizer_toolPane_6.Add(self.text_ctrl_mstools_InputSection_charge, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, 5)

		sizer_toolPane_5 = wx.BoxSizer(wx.VERTICAL)
		sizer_toolPane_5.Add(self.label_mstools_InputSection_accuracy, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, 5)
		sizer_toolPane_5.Add(self.text_ctrl_mstools_InputSection_accuracy, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, 5)

		sizer_toolPane_7 = wx.BoxSizer(wx.VERTICAL)
		sizer_toolPane_7.Add(self.label_mstools_InputSection_accuracy_blank, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, 5)
		sizer_toolPane_7.Add(self.label_mstools_InputSection_accuracy_ppm, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, 5)

		sizer_toolPane_2 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_toolPane_2.Add(sizer_toolPane_3, 0, wx.EXPAND) # Removed default flags, EXPAND is usually enough for nested sizers
		sizer_toolPane_2.Add(sizer_toolPane_4, 0, wx.EXPAND)
		sizer_toolPane_2.Add(sizer_toolPane_8, 0, wx.EXPAND)
		sizer_toolPane_2.Add(sizer_toolPane_9, 0, wx.EXPAND)
		sizer_toolPane_2.Add(sizer_toolPane_6, 0, wx.EXPAND)
		sizer_toolPane_2.Add(sizer_toolPane_5, 0, wx.EXPAND)
		sizer_toolPane_2.Add(sizer_toolPane_7, 0, wx.EXPAND)
		sizer_toolPane.Add(sizer_toolPane_2, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10) # Removed ALIGN_CENTER_HORIZONTAL due to EXPAND

		sizer_toolPane_1 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_toolPane_1.Add(self.button_massToSumComposition, 0, wx.ALIGN_LEFT | wx.ALL, 10)
		sizer_toolPane_1.Add(self.button_sumCompositionToMass, 0, wx.ALIGN_LEFT | wx.ALL, 10)
		sizer_toolPane.Add(sizer_toolPane_1, 0, wx.ALIGN_LEFT, 10) # Removed redundant ALIGN_LEFT with no expand

		sizer_toolPane.Add(self.text_ctrl_mstools_OutputSection, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 20) # Removed ALIGN_CENTER_HORIZONTAL due to EXPAND

		# second half
		sizer_toolPane.Add(self.label_mstools_Isotopes, 0, wx.ALIGN_LEFT | wx.ALL, 10)
		sizer_toolPane_10 = wx.BoxSizer(wx.VERTICAL)
		sizer_toolPane_10.Add(self.label_mstools_Isotopes_precursor, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, 5)
		sizer_toolPane_10.Add(self.text_ctrl_mstools_Isotopes_precursor, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, 5)

		sizer_toolPane_11 = wx.BoxSizer(wx.VERTICAL)
		sizer_toolPane_11.Add(self.label_mstools_Isotopes_fragment, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, 5)
		sizer_toolPane_11.Add(self.text_ctrl_mstools_Isotopes_fragment, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, 5)

		sizer_toolPane_12 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_toolPane_12.Add(sizer_toolPane_10, 0, wx.EXPAND)
		sizer_toolPane_12.Add(sizer_toolPane_11, 0, wx.EXPAND)

		sizer_toolPane_14 = wx.BoxSizer(wx.VERTICAL)
		sizer_toolPane_14.Add(self.label_mstools_Isotopes_blank, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, 5)
		sizer_toolPane_14.Add(self.checkBox_mstools_Isotopes_nl, 0, wx.EXPAND | wx.ALL, 5)
		sizer_toolPane_12.Add(sizer_toolPane_14, 0, wx.EXPAND)

		sizer_toolPane.Add(sizer_toolPane_12, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10) # Removed ALIGN_CENTER_HORIZONTAL due to EXPAND

		sizer_toolPane_13 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_toolPane_13.Add(self.button_Isotopes, 0, wx.ALIGN_LEFT | wx.ALL, 10)
		sizer_toolPane.Add(sizer_toolPane_13, 0, wx.ALIGN_LEFT) # Removed default flags, ALIGN_LEFT is fine here

		sizer_toolPane.Add(self.text_ctrl_mstools_Isotopes_output, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 20) # Removed ALIGN_CENTER_HORIZONTAL due to EXPAND

		self.notebook_1_pane_4.SetSizer(sizer_toolPane)

		### RUN pane ###
		sizer_2 = wx.BoxSizer(wx.VERTICAL)
		grid_sizer_1_RunCard = wx.BoxSizer(wx.VERTICAL)
		grid_sizer_1_RunCard_0 = wx.BoxSizer(wx.VERTICAL)
		# For wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL in a vertical sizer,
		# only ALIGN_CENTER_HORIZONTAL is meaningful for the item's placement.
		# ALIGN_CENTER_VERTICAL is redundant if the sizer itself is vertical.
		grid_sizer_1_RunCard_0.Add(grid_sizer_1_RunCard, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)

		# mfql Queries
		grid_sizer_1_RunCard.Add((10, 10))
		grid_sizer_1_RunCard.Add(self.label_mfqlQueriesSection, 0, wx.LEFT | wx.EXPAND, border_labels)

		grid_sizer_5_listBox = wx.GridBagSizer(7, 1)
		grid_sizer_5_listBox.Add(self.list_box_1, (0, 0), (6, 1), wx.TOP | wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
		grid_sizer_5_listBox.Add((20, 55), (0, 1), wx.DefaultSpan, wx.ALL, 0)
		# grid_sizer_5_listBox.Add((80, 10), (1,1), wx.DefaultSpan, wx.ALL, 0) # Commented out
		# grid_sizer_5_listBox.Add((80, 10), (2,1), wx.DefaultSpan, wx.ALL, 0) # Commented out
		grid_sizer_5_listBox.Add(self.button_AddMFQL, (1, 1), wx.DefaultSpan, wx.ALL | wx.EXPAND, 2)
		grid_sizer_5_listBox.Add(self.button_AddDir, (2, 1), wx.DefaultSpan, wx.ALL | wx.EXPAND, 2)
		grid_sizer_5_listBox.Add(self.button_OpenFile, (3, 1), wx.DefaultSpan, wx.ALL | wx.EXPAND, 2)
		grid_sizer_5_listBox.Add(self.button_NewFile, (4, 1), wx.DefaultSpan, wx.ALL | wx.EXPAND, 2)
		grid_sizer_5_listBox.Add(self.button_RemoveEntry, (5, 1), wx.DefaultSpan, wx.ALL, 2)
		grid_sizer_5_listBox.AddGrowableCol(0)
		grid_sizer_5_listBox.AddGrowableRow(0)


  
		grid_sizer_1_RunCard.Add(grid_sizer_5_listBox, 1, wx.EXPAND, 0) # Added wx.EXPAND, as it's common for list boxes

		# masterScan
		grid_sizer_1_RunCard.Add((10, 10))
		grid_sizer_1_RunCard.Add(self.label_MasterScanSection, 0, wx.LEFT | wx.EXPAND, border_labels) # Added wx.EXPAND
		grid_sizer_7_textBrowse_V = wx.BoxSizer(wx.VERTICAL)
		grid_sizer_8_MasterScanSection = wx.BoxSizer(wx.HORIZONTAL)
		grid_sizer_8_MasterScanSection.Add(self.text_ctrl_MasterScanSection, 1, wx.ALL | wx.EXPAND, 10) # Added proportion=1 and EXPAND
		grid_sizer_8_MasterScanSection.Add(self.button_Browse_MasterScan, 0, wx.ALL, 5)
		grid_sizer_7_textBrowse_V.Add(grid_sizer_8_MasterScanSection, 1, wx.EXPAND, 0)
		grid_sizer_1_RunCard.Add(grid_sizer_7_textBrowse_V, 0, wx.EXPAND, 0) # Added wx.EXPAND

		# output
		grid_sizer_1_RunCard.Add(self.label_OutputSection, 0, wx.LEFT | wx.EXPAND, border_labels) # Added wx.EXPAND
		grid_sizer_9_OutputSection = wx.BoxSizer(wx.HORIZONTAL)
		grid_sizer_9_OutputSection.Add(self.text_ctrl_OutputSection, 1, wx.ALL | wx.EXPAND, 10) # Added proportion=1 and EXPAND
		grid_sizer_9_OutputSection.Add(self.button_Browse_OutputSection, 0, wx.ALL, 5)
		grid_sizer_9_OutputSection.Add(self.button_Open_OutputSection, 0, wx.ALL, 5)
		grid_sizer_10_textBrowse_V = wx.BoxSizer(wx.VERTICAL)
		grid_sizer_10_textBrowse_V.Add(grid_sizer_9_OutputSection, 1, wx.EXPAND, 0)
		grid_sizer_1_RunCard.Add(grid_sizer_10_textBrowse_V, 0, wx.EXPAND, 0) # Added wx.EXPAND

		# options
		grid_sizer_1_RunCard.Add(self.label_RunOptions, 0, wx.LEFT | wx.BOTTOM | wx.EXPAND, border_labels) # Added wx.EXPAND

		grid_sizer_29_OptionsSection = wx.GridBagSizer(1, 6) # GridBagSizer needs explicit row/col spanning
		grid_sizer_29_OptionsSection.Add(self.label_RunOptions_tolerance, (0, 0), (1, 1), wx.ALL | wx.EXPAND, 2) # Adjusted span
		grid_sizer_29_OptionsSection.Add(self.label_RunOptions_MS, (0, 1), (1, 1), wx.ALL | wx.EXPAND, 2)
		grid_sizer_29_OptionsSection.Add(self.text_ctrl_RunOptions_MS, (0, 2), (1, 1), wx.ALL | wx.EXPAND, 2)
		grid_sizer_29_OptionsSection.Add(self.choice_RunOptions_MS_type, (0, 3), (1, 1), wx.ALL | wx.EXPAND, 2)
		grid_sizer_29_OptionsSection.Add(self.label_RunOptions_MSMS, (0, 4), (1, 1), wx.ALL | wx.EXPAND, 2)
		grid_sizer_29_OptionsSection.Add(self.text_ctrl_RunOptions_MSMS, (0, 5), (1, 1), wx.ALL | wx.EXPAND, 2)
		grid_sizer_29_OptionsSection.Add(self.choice_RunOptions_MSMS_type, (0, 6), (1, 1), wx.ALL | wx.EXPAND, 2)

		# Commented out sections, assuming they are not currently used
		# grid_sizer_29_OptionsSection.Add(self.label_RunOptions_minocc, (1,0), wx.DefaultSpan, wx.ALL|wx.EXPAND, 2)
		# grid_sizer_29_OptionsSection.Add(self.label_RunOptions_MS_minocc, (1,1), wx.DefaultSpan, wx.ALL|wx.EXPAND, 2)
		# grid_sizer_29_OptionsSection.Add(self.text_ctrl_RunOptions_MS_minocc, (1,2), wx.DefaultSpan, wx.ALL|wx.EXPAND, 2)
		# grid_sizer_29_OptionsSection.Add(self.label_RunOptions_MSMS_minocc, (1,4), wx.DefaultSpan, wx.ALL|wx.EXPAND, 2)
		# grid_sizer_29_OptionsSection.Add(self.text_ctrl_RunOptions_MSMS_minocc, (1,5), wx.DefaultSpan, wx.ALL|wx.EXPAND, 2)

		grid_sizer_1_RunCard.Add(grid_sizer_29_OptionsSection, 0, wx.LEFT | wx.EXPAND, 10)
		grid_sizer_1_RunCard.Add((20, 20))

		grid_sizer_24_OptionsSection = wx.BoxSizer(wx.HORIZONTAL)
		grid_sizer_11_OptionsSection = wx.BoxSizer(wx.VERTICAL)
		grid_sizer_11_OptionsSection.Add(self.checkBox_OptionsSection_isocorrect_ms, 0, wx.LEFT | wx.EXPAND, 10)
		grid_sizer_11_OptionsSection.Add(self.checkBox_OptionsSection_isocorrect_msms, 0, wx.LEFT | wx.EXPAND, 10)
		grid_sizer_11_OptionsSection.Add(self.checkBox_OptionsSection_complement_sc, 0, wx.LEFT | wx.EXPAND, 10)

		grid_sizer_26_OptionsSection = wx.BoxSizer(wx.VERTICAL)
		grid_sizer_26_OptionsSection.Add(self.checkBox_OptionsSection_dumpMasterScan, 0, wx.LEFT | wx.EXPAND, 10)
		grid_sizer_13_DumpSection = wx.BoxSizer(wx.VERTICAL)
		grid_sizer_13_DumpSection.Add(self.button_Open_DumpSection, 0, wx.ALL | wx.EXPAND, 5)
		grid_sizer_26_OptionsSection.Add(grid_sizer_13_DumpSection, 0, wx.LEFT | wx.EXPAND, 10)

		grid_sizer_25_OptionsSection = wx.BoxSizer(wx.VERTICAL)
		grid_sizer_25_OptionsSection.Add(self.checkBox_OptionsSection_nohead, 0, wx.LEFT | wx.EXPAND, 10)
		grid_sizer_25_OptionsSection.Add(self.checkBox_OptionsSection_compress, 0, wx.LEFT | wx.EXPAND, 10)
		grid_sizer_25_OptionsSection.Add(self.checkBox_OptionsSection_tabLimited, 0, wx.LEFT | wx.EXPAND, 10)

		grid_sizer_31_OptionsSection = wx.BoxSizer(wx.VERTICAL)
		grid_sizer_31_OptionsSection.Add(self.checkBox_generateStatistics, 0, wx.LEFT | wx.EXPAND, 10)
		grid_sizer_31_OptionsSection.Add(self.checkBox_noPermutations, 0, wx.LEFT | wx.EXPAND, 10)

		grid_sizer_24_OptionsSection.Add(grid_sizer_11_OptionsSection, 0, wx.EXPAND, 0)
		grid_sizer_24_OptionsSection.Add(grid_sizer_25_OptionsSection, 0, wx.EXPAND, 0)
		grid_sizer_24_OptionsSection.Add(grid_sizer_31_OptionsSection, 0, wx.EXPAND, 0)
		grid_sizer_24_OptionsSection.Add(grid_sizer_26_OptionsSection, 0, wx.EXPAND, 0)
		grid_sizer_1_RunCard.Add(grid_sizer_24_OptionsSection, 0, wx.EXPAND, 0)

		# run
		grid_sizer_13_RunButton = wx.BoxSizer(wx.VERTICAL)
		# grid_sizer_13_RunButton.Add((10,380)) # Commented out
		grid_sizer_13_RunButton.Add((10, 10))
		grid_sizer_13_RunButton.Add(self.button_RunLipidX, 0, wx.ALL, 5)
		grid_sizer_1_RunCard.Add(grid_sizer_13_RunButton, 0, wx.ALIGN_CENTER_HORIZONTAL, 0) # Changed ALIGN_CENTER to ALIGN_CENTER_HORIZONTAL for vertical sizer

		self.notebook_1_pane_3.SetSizer(grid_sizer_1_RunCard_0)



		##############################
		### Import Settings ###

		sizeBorder = 5

		# ini file
		box_sizer_ImportSettings = wx.BoxSizer(wx.VERTICAL)
		box_sizer_ImportSettings.Add((10, 10))
		box_sizer_ImportSettings.Add(self.label_LoadIniSection, 0, wx.LEFT | wx.EXPAND, border_labels) # Added wx.EXPAND

		grid_sizer_16_textBrowse_V = wx.BoxSizer(wx.VERTICAL)
		grid_sizer_17_LoadIniSection = wx.BoxSizer(wx.HORIZONTAL)
		grid_sizer_17_LoadIniSection.Add(self.text_ctrl_LoadIniSection, 1, wx.ALL | wx.EXPAND, 10) # Added proportion=1 and EXPAND
		grid_sizer_17_LoadIniSection.Add(self.button_Browse_LoadIniSection, 0, wx.ALL, 5)
		grid_sizer_16_textBrowse_V.Add(grid_sizer_17_LoadIniSection, 1, wx.EXPAND, 0)

		#box_sizer_ImportSettings.Add(grid_sizer_16_textBrowse_V, 0, wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, 0) # Removed ALIGN_CENTER_HORIZONTAL if EXPAND is used. Kept EXPAND for consistent filling.
		box_sizer_ImportSettings.Add(grid_sizer_16_textBrowse_V, 0, wx.EXPAND, 0)		
		box_sizer_ImportSettings.Add((5, 5))
		#box_sizer_ImportSettings.Add(self.static_line_LoadIniSection, 0, wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, 20) # Kept ALIGN_CENTER_HORIZONTAL as it might be for the static line itself, but EXPAND is more common here.
		box_sizer_ImportSettings.Add(self.static_line_LoadIniSection, 0, wx.EXPAND, 20)
		box_sizer_ImportSettings.Add((10, 10))
  

		# set settings
		box_sizer_ImportSettings.Add(self.label_SelectSettingSection, 0, wx.LEFT | wx.EXPAND, border_labels) # Added wx.EXPAND
		box_sizer_ImportSettings.Add((10, 10))

		box_sizer_ImportSettings_SelectConfiguration = wx.BoxSizer(wx.VERTICAL)
		box_sizer_ImportSettings_SelectConfiguration.Add(self.choice_SelectSettingSection, 0, wx.LEFT | wx.EXPAND, 20) # Added wx.EXPAND
		#box_sizer_ImportSettings.Add(box_sizer_ImportSettings_SelectConfiguration, 0, wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, 20) # Removed ALIGN_CENTER_HORIZONTAL if EXPAND is used. Kept EXPAND for consistent filling.
		box_sizer_ImportSettings.Add(box_sizer_ImportSettings_SelectConfiguration, 0, wx.EXPAND, 20)		
		box_sizer_ImportSettings.Add((20, 20))

		### start settings ###
		grid_sizer_19_SettingsSection_gridBag = wx.GridBagSizer(10, 8)

		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_selectionWindow, (0, 1),
												wx.DefaultSpan, wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder)
		grid_sizer_19_SettingsSection_gridBag.Add(self.text_ctrl_SettingsSection_selectionWindow, (0, 4),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_selectionWindow_unit, (0, 5),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span

		box_sizer_SettingsSection_buttons = wx.BoxSizer(wx.HORIZONTAL)
		box_sizer_SettingsSection_buttons.Add(self.button_Save_LoadIniSection, 0, wx.EXPAND) # Added EXPAND
		box_sizer_SettingsSection_buttons.Add(self.button_SaveAs_LoadIniSection, 0, wx.EXPAND) # Added EXPAND
		box_sizer_SettingsSection_buttons.Add(self.button_Delete_LoadIniSection, 0, wx.EXPAND) # Added EXPAND
		grid_sizer_19_SettingsSection_gridBag.Add(box_sizer_SettingsSection_buttons, (0, 6), (2, 3), wx.EXPAND, 0) # Added EXPAND
		# grid_sizer_19_SettingsSection_gridBag.Add(self.button_SaveAs_LoadIniSection, (0,6), wx.DefaultSpan, 0, 0) # Commented out
		# grid_sizer_19_SettingsSection_gridBag.Add(self.button_Save_LoadIniSection, (0,7), wx.DefaultSpan, 0, 0) # Commented out
		# grid_sizer_19_SettingsSection_gridBag.Add(self.button_Delete_LoadIniSection, (1,6), wx.DefaultSpan, 0, 0) # Commented out

		box_sizer_timerange = wx.BoxSizer(wx.HORIZONTAL)
		box_sizer_timerange.Add(self.text_ctrl_SettingsSection_timerange1, 1, wx.EXPAND) # Added proportion=1 and EXPAND
		# box_sizer_timerange.Add(wx.StaticText(self, -1, " , ")) # Commented out
		box_sizer_timerange.Add(self.text_ctrl_SettingsSection_timerange2, 1, wx.EXPAND) # Added proportion=1 and EXPAND
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_timerange, (1, 1),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(box_sizer_timerange, (1, 4),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_timerange_unit, (1, 5),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span

		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_calibration, (2, 1),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_calibration_ms, (2, 3),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.text_ctrl_SettingsSection_calibration_ms, (2, 4),
												(1, 2), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder)
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_calibration_msms, (2, 6),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.text_ctrl_SettingsSection_calibration_msms, (2, 7),
												(1, 2), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder)

		box_sizer_massrange_ms = wx.BoxSizer(wx.HORIZONTAL)
		box_sizer_massrange_ms.Add(self.text_ctrl_SettingsSection_massrange_ms1, 1, wx.EXPAND) # Added proportion=1 and EXPAND
		# box_sizer_massrange_ms.Add(wx.StaticText(self, -1, " , ")) # Commented out
		box_sizer_massrange_ms.Add(self.text_ctrl_SettingsSection_massrange_ms2, 1, wx.EXPAND) # Added proportion=1 and EXPAND

		box_sizer_massrange_msms = wx.BoxSizer(wx.HORIZONTAL)
		box_sizer_massrange_msms.Add(self.text_ctrl_SettingsSection_massrange_msms1, 1, wx.EXPAND) # Added proportion=1 and EXPAND
		# box_sizer_massrange_msms.Add(wx.StaticText(self, -1, " , ")) # Commented out
		box_sizer_massrange_msms.Add(self.text_ctrl_SettingsSection_massrange_msms2, 1, wx.EXPAND) # Added proportion=1 and EXPAND

		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_massrange, (3, 1),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_massrange_ms, (3, 3),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(box_sizer_massrange_ms, (3, 4),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_massrange_ms_unit, (3, 5),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_massrange_msms, (3, 6),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(box_sizer_massrange_msms, (3, 7),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_massrange_msms_unit, (3, 8),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span

		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_resolution, (4, 1),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_resolution_ms, (4, 3),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.text_ctrl_SettingsSection_resolution_ms, (4, 4),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_resolution_ms_unit, (4, 5),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_resolution_msms, (4, 6),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.text_ctrl_SettingsSection_resolution_msms, (4, 7),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_resolution_msms_unit, (4, 8),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span

		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_tolerance, (5, 1),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_tolerance_ms, (5, 3),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.text_ctrl_SettingsSection_tolerance_ms, (5, 4),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.choice_SettingsSection_tolerance_ms, (5, 5),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		# grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_tolerance_ms_unit, (6,5), # Commented out
		#   wx.DefaultSpan, wx.LEFT|wx.TOP|wx.EXPAND, sizeBorder)
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_tolerance_msms, (5, 6),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.text_ctrl_SettingsSection_tolerance_msms, (5, 7),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.choice_SettingsSection_tolerance_msms, (5, 8),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		# grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_tolerance_msms_unit, (6,8), # Commented out
		#   wx.DefaultSpan, wx.LEFT|wx.TOP|wx.EXPAND, sizeBorder)

		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_threshold, (6, 1),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_threshold_ms, (6, 3),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.text_ctrl_SettingsSection_threshold_ms, (6, 4),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.choice_SettingsSection_threshold_ms, (6, 5),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_threshold_msms, (6, 6),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.text_ctrl_SettingsSection_threshold_msms, (6, 7),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.choice_SettingsSection_threshold_msms, (6, 8),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span

		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_resDelta, (7, 1),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
  
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_resDelta_ms, (7, 3),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span

		grid_sizer_19_SettingsSection_gridBag.Add(self.text_ctrl_SettingsSection_resDelta_ms, (7, 4),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_resDelta_ms_unit, (7, 5),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_resDelta_msms, (7, 6),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.text_ctrl_SettingsSection_resDelta_msms, (7, 7),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_resDelta_msms_unit, (7, 8),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span

		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_occupationThr, (8, 1),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_occupationThr_ms, (8, 3),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.text_ctrl_SettingsSection_occupationThr_ms, (8, 4),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_occupationThr_ms_unit, (8, 5),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_occupationThr_msms, (8, 6),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.text_ctrl_SettingsSection_occupationThr_msms, (8, 7),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_occupationThr_msms_unit, (8, 8),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		# grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_occupationThr_groups, (8,8), # Commented out
		#   wx.DefaultSpan, wx.LEFT|wx.TOP|wx.EXPAND, sizeBorder)

		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_precursorMassShift, (10, 1),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.text_ctrl_SettingsSection_precursorMassShift, (10, 4),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_precursorMassShift_unit, (10, 5),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span

		grid_sizer_19_SettingsSection_gridBag.Add(self.text_ctrl_SettingsSection_filter_ms, (9, 4),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_filter_ms, (9, 3),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_filter_ms_unit, (9, 5),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span

		grid_sizer_19_SettingsSection_gridBag.Add(self.text_ctrl_SettingsSection_filter_msms, (9, 7),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_filter_msms, (9, 1),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span

		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_filter_ms_ms, (9, 6),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_filter_msms_unit, (9, 8),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span

		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_precursorMassShiftOrbi, (10, 6),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.text_ctrl_SettingsSection_precursorMassShiftOrbi, (10, 7),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span
		grid_sizer_19_SettingsSection_gridBag.Add(self.label_SettingsSection_precursorMassShiftOrbi_unit, (10, 8),
												(1, 1), wx.LEFT | wx.TOP | wx.EXPAND, sizeBorder) # Adjusted span

		box_sizer_ImportSettings.Add(grid_sizer_19_SettingsSection_gridBag, 1, wx.EXPAND | wx.ALL, sizeBorder) # Added proportion=1 and EXPAND, and ALL border

		grid_sizer_20_RunButton = wx.BoxSizer(wx.VERTICAL)
		# grid_sizer_20_RunButton.Add((10,380)) # Commented out
		grid_sizer_20_RunButton.Add((10, 10))
		grid_sizer_20_RunButton.Add(self.button_StartImport, 0, wx.ALL, 5)
		box_sizer_ImportSettings.Add(grid_sizer_20_RunButton, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)


		self.notebook_1_pane_5.SetSizer(box_sizer_ImportSettings)

		### Import Settings ###
		##############################
		self.notebook_1.AddPage(self.notebook_1_pane_2, "Import Source")
		self.counterNotebookPages += 1
		self.dictNotebookPages["Import"] = self.counterNotebookPages

		dropTargetProject = GeneralFileDrawerDropTarget(self.notebook_1_pane_2, self.loadProject, 'lxp')
		self.notebook_1_pane_2.SetDropTarget(dropTargetProject)

		self.notebook_1.AddPage(self.notebook_1_pane_5, "Import Settings")
		self.counterNotebookPages += 1
		self.dictNotebookPages["ImportSettings"] = self.counterNotebookPages

		self.notebook_1.AddPage(self.notebook_1_pane_3, "Run")
		self.counterNotebookPages += 1
		self.dictNotebookPages["Run"] = self.counterNotebookPages

		self.notebook_1.AddPage(self.notebook_1_pane_4, "MS Tools")
		self.counterNotebookPages += 1
		self.dictNotebookPages["MSTools"] = self.counterNotebookPages

		start_sizer = wx.BoxSizer(wx.VERTICAL)
		start_sizer.AddStretchSpacer(1)
		start_title = wx.StaticText(self.start_panel, -1, "Choose a workspace")
		start_title.SetFont(self.header_font)
		start_subtitle = wx.StaticText(self.start_panel, -1, "Open LipidXplorerNext or the current LipidXplorer 1.5 interface.")
		start_button_row = wx.BoxSizer(wx.HORIZONTAL)
		start_button_row.Add(self.button_open_next, 0, wx.ALL, 8)
		start_button_row.Add(self.button_open_legacy, 0, wx.ALL, 8)
		start_sizer.Add(self.start_logo, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, 14)
		start_sizer.Add(start_title, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, 8)
		start_sizer.Add(start_subtitle, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, 18)
		start_sizer.Add(start_button_row, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
		start_sizer.AddStretchSpacer(1)
		self.start_panel.SetSizer(start_sizer)

		placeholder_sizer = wx.BoxSizer(wx.VERTICAL)
		placeholder_sizer.AddStretchSpacer(1)

		group_top = wx.BoxSizer(wx.VERTICAL)
		group_top.Add(self.label_placeholder_title, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, 8)
		group_top.Add(self.label_placeholder_message, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)

		group_bottom = wx.BoxSizer(wx.VERTICAL)
		group_bottom.Add(self.label_placeholder_demo, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, 8)
		group_bottom.Add(self.link_placeholder_demo, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)

		placeholder_sizer.Add(group_top, 0, wx.ALIGN_CENTER_HORIZONTAL)
		placeholder_sizer.AddSpacer(70)
		placeholder_sizer.Add(group_bottom, 0, wx.ALIGN_CENTER_HORIZONTAL)
		placeholder_sizer.AddStretchSpacer(1)

		placeholder_bottom = wx.BoxSizer(wx.HORIZONTAL)
		placeholder_bottom.Add(self.button_back_from_placeholder, 0, wx.LEFT, 12)
		placeholder_bottom.AddStretchSpacer(1)
		placeholder_sizer.Add(placeholder_bottom, 0, wx.EXPAND | wx.BOTTOM, 4)

		self.placeholder_panel.SetSizer(placeholder_sizer)


		sizer_2.Add(self.start_panel, 1, wx.EXPAND, 0)
		sizer_2.Add(self.placeholder_panel, 1, wx.EXPAND, 0)
		sizer_2.Add(self.notebook_1, 1, wx.EXPAND, 0)
		self.counterNotebookPages += 1
		self.dictNotebookPages["Import"] = self.counterNotebookPages
		self.SetAutoLayout(True)
		self.SetSizer(sizer_2)
		self._set_active_view("landing")
		self.Layout()

		# end wxGlade



	def _update_chrome_for_view(self, view_name):
		if view_name == "legacy":
			if self.GetMenuBar() is None:
				self.SetMenuBar(self.menubar)
		else:
			if self.GetMenuBar() is not None:
				self.SetMenuBar(None)

	def _set_active_view(self, view_name):
		show_start = view_name == "landing"
		show_placeholder = view_name == "next"
		show_legacy = view_name == "legacy"

		self.start_panel.Show(show_start)
		self.placeholder_panel.Show(show_placeholder)
		self.button_back_from_placeholder.Show(show_placeholder)
		self.notebook_1.Show(show_legacy)
		self._update_chrome_for_view(view_name)
		self.Layout()

	def on_open_next_view(self, event):
		self._set_active_view("next")

	def on_open_legacy_view(self, event):
		self._set_active_view("legacy")

	def on_back_to_landing(self, event):
		self._set_active_view("landing")
 

	def writeOutput(self, destination, content):

		tryAgain = True
		while tryAgain:
			try:
				f = open(destination, 'w')
				f.write(content)
				f.close()
				return True
			except IOError:
				dlgError = wx.MessageDialog(self, "The result cannot be saved. It is probably open by another program. Try again?",
					"File writing error", wx.YES_NO|wx.ICON_QUESTION)
				answer = dlgError.ShowModal()
				if answer == wx.ID_NO:
					tryAgain = False
				dlgError.Destroy()

		return False


    
# end of class LpdxFrame





class MyApp(wx.App):

	def OnInit(self):
		self.frame = LpdxFrame(None, -1, "")
		self.frame.Show(True)
		self.frame.Center()
		self.SetTopWindow(self.frame)
		return True

def main():

	app = MyApp(0)
	if playSound:
		wx.Sound('../pics/StartApp.wav').Play()
	app.MainLoop()
	## end of the software

if __name__ == "__main__":
	main()
