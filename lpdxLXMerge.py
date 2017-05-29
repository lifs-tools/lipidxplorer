import csv
import os
import sys
import re
import wx
import wx.stc as stc
import wx.lib.buttons as buttons
import wx.lib.fancytext as fancytext
import wx.grid
from wx.lib.newevent import NewEvent
import traceback
from lx.tools import odict
from cStringIO import StringIO

DRAG_SOURCE = wx.NewId()
wxStdOut, EVT_STDOUT= NewEvent()
wxWriteDebug, EVT_WRITE_DEBUG = NewEvent()

class SysOutListener:
	def write(self, string):
		#sys.__stdout__.write(string)
		evt = wxStdOut(text=string)
		#wx.PostEvent(wx.GetApp().frame.output_window, evt)
		wx.PostEvent(wx.GetApp().frame, evt)

# for exception forwarding
def formatExceptionInfo(maxTBlevel=8):
    cla, exc, trbk = sys.exc_info()
    excName = cla.__name_
    try:
        #excArgs = exc.__dict__["args"]
        excArgs = exc.args
    except KeyError:
        excArgs = "<no args>"
    excTb = traceback.format_tb(trbk, maxTBlevel)
    return (excName, excArgs, excTb, exc)

def excepthook(type, value, tb):

	frame = wx.GetApp().frame
	m = ''.join(traceback.format_exception(type, value, tb))
	#m = type, value

	dlg = wx.MessageDialog(frame, m, "Exception!", wx.ICON_ERROR)

	if dlg.ShowModal() == wx.ID_OK:
		dlg.Destroy()

class TextOutFrame(wx.Frame):

	def __init__(self, *args, **kwds):

		# begin wxGlade: LpdxFrame.__init__
		kwds["style"] = wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.SYSTEM_MENU | wx.CAPTION \
		| wx.CLOSE_BOX | wx.CLIP_CHILDREN | wx.RESIZE_BORDER

		wx.Frame.__init__(self, *args, **kwds)
		#panel = wx.Panel(self, -1)

		self.parent = args[0]

		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.text_ctrl = stc.StyledTextCtrl(self,
			style = wx.SIMPLE_BORDER|wx.HSCROLL|wx.VSCROLL|wx.TE_AUTO_SCROLL|wx.ALWAYS_SHOW_SB|wx.TE_MULTILINE)#, size = wx.Point(835, 700))
		self.text_ctrl.SetMarginType(0, stc.STC_MARGIN_NUMBER)
		self.text_ctrl.SetMarginWidth(0, 22)
		self.text_ctrl.StyleSetSpec(stc.STC_STYLE_DEFAULT, "size:10,face:NSimSun")
		self.text_ctrl.StyleSetSpec(stc.STC_STYLE_LINENUMBER, "size:9,face:Arial")
		self.text_ctrl.SetMinSize((self.GetSize()[0] - 40, self.GetSize()[1] - 150))
		self.text_ctrl.SetSize((self.GetSize()[0] - 40, self.GetSize()[1] - 150))
		self.text_ctrl.SetScrollWidth(3000)

		self.button_clear = wx.Button(self, -1, "Clear Buffer")
		self.button_clear.SetSize((20, 9))
		self.button_clear.SetMaxSize((120, 24))
		self.button_clear.SetMinSize((120, 24))

		self.button_stop = wx.Button(self, -1, "Stop")
		self.button_stop.SetSize((20, 9))
		self.button_stop.SetMaxSize((120, 24))
		self.button_stop.SetMinSize((120, 24))

		self.sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
		self.sizer_buttons.Add(self.button_clear, 0, wx.ADJUST_MINSIZE|wx.ALIGN_BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 10)
		self.sizer_buttons.Add(self.button_stop, 0, wx.ADJUST_MINSIZE|wx.ALIGN_BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 10)
		self.sizer.Add(self.text_ctrl, 1, wx.EXPAND|wx.ALL, 10)
		self.sizer.Add(self.sizer_buttons, 0, wx.ADJUST_MINSIZE|wx.ALIGN_BOTTOM|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 10)
		self.SetSizer(self.sizer)

		self.SetMinSize((700,400))
		self.SetSize((700,400))
		self.Layout()

		self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
		self.Bind(wx.EVT_BUTTON, self.OnClear, self.button_clear)
		self.Bind(wx.EVT_BUTTON, self.OnStop, self.button_stop)

		self.listError = []

	def write(self, text):

		if re.match('.*lpdxUIExceptions.*', text):
			error = re.match('.*lpdxUIExceptions.*:(.*)', text).group(1)
			self.listError.append()

		self.text_ctrl.AppendText(text)

	def OnClear(self, evt):
		self.text_ctrl.ClearAll()

	def OnStop(self, evt):
		self.parent.isRunning = False

	def OnCloseWindow(self, evt):
		self.Show(False)
		self.parent.debugOpen = False

	def OnUpdate(self, evt):
		self.text_ctrl.AppendText(evt.text)
		self.text_ctrl.ScrollToLine(self.text_ctrl.GetLineCount())

class InputFileDropTarget(wx.FileDropTarget):
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
						if re.match('(.*\.mfql$)|(.*\.py$)', f):
							n = os.path.join(root, f)
							self.parent.filePath_AddInputFile.append(n)
							l = n.split(os.sep)
							self.parent.dictInputFiles[l[-1]] = n
			else:
				self.parent.filePath_AddInputFile.append(p)
				l = p.split(os.sep)
				self.parent.dictInputFiles[l[-1]] = p

		#self.parent.list_box_1.Set(sorted(self.parent.dictMFQLScripts.keys()))
		self.parent.listBox_inputFiles.Set(self.parent.dictInputFiles.keys())

class ChooseColFrame(wx.Frame):

	def __init__(self, *args, **kwds):

		# begin wxGlade: LpdxFrame.__init__
		kwds["style"] = wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.SYSTEM_MENU | wx.CAPTION \
		| wx.CLOSE_BOX | wx.CLIP_CHILDREN | wx.RESIZE_BORDER

		wx.Frame.__init__(self, *args, **kwds)
		#panel = wx.Panel(self, -1)

		self.parent = args[0]
		self.columnsToChoose = []
		self.columnsChoosen = []

		self.sizer_v = wx.BoxSizer(wx.VERTICAL)
		self.sizer_h = wx.BoxSizer(wx.HORIZONTAL)

		self.label_left = wx.StaticText(self, -1, "All columns of the result files")
		self.listBox_left = wx.ListBox(self, -1, choices = self.columnsToChoose, name = "",
				style = wx.LB_EXTENDED|wx.EXPAND, size = (200, 210))
		self.button_toTheRight = wx.Button(self, -1, "->")
		self.button_toTheLeft = wx.Button(self, -1, "<-")
		self.label_right = wx.StaticText(self, -1, "Columns to be in the merging result")
		self.listBox_right = wx.ListBox(self, -1, choices = [], name = "",
				style = wx.LB_EXTENDED, size = (200, 210))
		self.button_ready = wx.Button(self, -1, "      Merge Results     ")

		self.sizer_buttons = wx.BoxSizer(wx.VERTICAL)
		self.sizer_buttons.Add(self.button_toTheRight, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		self.sizer_buttons.Add(self.button_toTheLeft, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.sizer_leftPart = wx.BoxSizer(wx.VERTICAL)
		self.sizer_leftPart.Add(self.label_left, 0, wx.ALIGN_LEFT|wx.ALL, 4)
		self.sizer_leftPart.Add(self.listBox_left, 0, wx.ALIGN_LEFT|wx.ALL, 4)

		self.sizer_rightPart = wx.BoxSizer(wx.VERTICAL)
		self.sizer_rightPart.Add(self.label_right, 0, wx.ALIGN_LEFT|wx.ALL, 4)
		self.sizer_rightPart.Add(self.listBox_right, 0, wx.ALIGN_LEFT|wx.ALL, 4)

		self.sizer_h.Add(self.sizer_leftPart, 0, wx.ALIGN_CENTER|wx.ALL, 10)
		self.sizer_h.Add(self.sizer_buttons, 0, wx.ALIGN_CENTER_VERTICAL)
		self.sizer_h.Add(self.sizer_rightPart, 0, wx.ALIGN_CENTER|wx.ALL, 10)

		self.sizer_v.Add(self.sizer_h)
		self.sizer_v.Add(self.button_ready, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.SetSizer(self.sizer_v)

		#self.SetMinSize((350,500))
		self.SetSize((560,330))
		self.CentreOnParent(wx.BOTH)
		self.Layout()

		self.Bind(wx.EVT_SIZE, self.OnSize)
		self.Bind(wx.EVT_BUTTON, self.OnButtonToTheRight, self.button_toTheRight)
		self.Bind(wx.EVT_BUTTON, self.OnButtonToTheLeft, self.button_toTheLeft)
		self.Bind(wx.EVT_BUTTON, self.OnButtonReady, self.button_ready)
		#self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

	def OnSize(self, evt):
		self.Refresh()

	def fillRightWindow(self, choices):
		self.columnsToChoose = choices
		self.listBox_left.Set(self.columnsToChoose)

	def OnButtonToTheRight(self, evt):
		for index in self.listBox_left.GetSelections():
			self.columnsChoosen.append(self.columnsToChoose[index])

		### remove selected items ###
		# first mark them
		for index in self.listBox_left.GetSelections():
			self.columnsToChoose[index] = 0

		# second, remove them
		index = 0
		while index < len(self.columnsToChoose):
			if self.columnsToChoose[index] == 0:
				del self.columnsToChoose[index]
			else:
				index += 1

		self.listBox_left.Set(self.columnsToChoose)
		self.listBox_right.Set(self.columnsChoosen)

	def OnButtonToTheLeft(self, evt):
		for index in self.listBox_right.GetSelections():
			self.columnsToChoose.append(self.columnsChoosen[index])

		### remove selected items ###
		# first mark them
		for index in self.listBox_right.GetSelections():
			self.columnsChoosen[index] = 0

		# second, remove them
		index = 0
		while index < len(self.columnsChoosen):
			if self.columnsChoosen[index] == 0:
				del self.columnsChoosen[index]
			else:
				index += 1

		self.listBox_left.Set(self.columnsToChoose)
		self.listBox_right.Set(self.columnsChoosen)

	def OnButtonReady(self, evt):
		self.parent.StartAlignment()
		self.Show(False)

	def OnCloseWindow(self, evt):
		self.Show(False)


# Define File Drop Target class
class FileDropTarget(wx.FileDropTarget):
	""" This object implements Drop Target functionality for Files """
	def __init__(self, obj):
		""" Initialize the Drop Target, passing in the Object Reference to
			indicate what should receive the dropped files """
		# Initialize the wsFileDropTarget Object
		wx.FileDropTarget.__init__(self)
		# Store the Object Reference for dropped files
		self.obj = obj

	def OnDropFiles(self, x, y, filenames):
		""" Implement File Drop """
		# append a list of the file names dropped
		if len(filenames) > 1:
			raise AttributeError

		self.obj.Clear()
		self.obj.WriteText(filenames[0])


#############################################################################
###                            GUI part                                   ###
#############################################################################


class MyFrame(wx.Frame):
	def __init__(self, *args, **kwds):

		################################################################################
		# standard routines                                                            #
		################################################################################

		# redirect output
		#sys.stdout = SysOutListener()

		# redirect exceptions
		sys.excepthook = excepthook

		# begin wxGlade: LpdxFrame.__init__
		kwds["style"] = wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.SYSTEM_MENU | wx.CAPTION \
		| wx.CLOSE_BOX | wx.CLIP_CHILDREN | wx.RESIZE_BORDER

		wx.Frame.__init__(self, *args, **kwds)

		# set up the menu
		self.menubar = wx.MenuBar()
		self.menu_options = wx.Menu()
		self.menu_options.AppendItem(wx.MenuItem(self.menu_options, 1, "Output window"))
		self.menubar.Append(self.menu_options, "&Options")
		self.SetMenuBar(self.menubar)

		self.Bind(wx.EVT_MENU, self.OnMenuOutputWin, id = 1)

		# set up output window
		self.winOpen = False
		self.output = TextOutFrame(self, -1, "Output")
		self.output.text_ctrl.AppendText(sys.version + '\n\n')
		#self.output.Show(True)
		self.dictOutput = odict()

		# standard bind for the ouput
		#self.Bind(EVT_STDOUT, self.output.OnUpdate)


		################################################################################
		# start working routines                                                       #
		################################################################################

		self.filePath_AddInputFile = []
		self.dictInputFiles = odict()
		self.onlyFullOccupation = False

		# set window size
		self.SetSize((420, 380))

		# create Sizers
		self.sizer_main_v = wx.BoxSizer(wx.VERTICAL)
		self.sizer3_v = wx.BoxSizer(wx.VERTICAL)
		#self.sizer_main_v.Add(self.sizer2_h)
		#self.sizer_main_v.Add(self.sizer4_h)

		#s1 = "C:\\Users\\earl\\lipidx\\trunk\\scripts\\benchmark\\algorithms\\validation_of_merging_Xcalibur_vs_LipidX\\071121_uniklinik_LipidX"
		#s2 = "C:\\Users\\earl\\lipidx\\trunk\\scripts\\benchmark\\algorithms\\validation_of_merging_Xcalibur_vs_LipidX\\071011_uniklinik_Xcalibur"

		# create buttons and textctrls
		self.label_inputFiles = wx.StaticText(self, -1, "Insert files to merge")
		self.listBox_inputFiles = wx.ListBox(self, -1, pos=(30,10), choices=[], name="", style = wx.LB_EXTENDED, size = (300, 100))
		self.button_inputFiles_browse = buttons.GenButton(self, -1, "Browse")
		self.sizer_inputFile1_h = wx.BoxSizer(wx.HORIZONTAL)

		self.label_outputFile = wx.StaticText(self, -1, "Output file")
		self.text_ctrl_inputFile2 = wx.TextCtrl(self, -1, "result.csv",
				style = wx.TE_PROCESS_ENTER, size = (300, 25))
		self.button_inputFile2_browse = buttons.GenButton(self, -1, "Browse")
		self.sizer_inputFile2_h = wx.BoxSizer(wx.HORIZONTAL)

		self.label_colsToAlign = wx.StaticText(self, -1, "Cols to align")
		self.text_ctrl_colsToAlign = wx.TextCtrl(self, -1, "SPECIE, CHEMSC",
				style = wx.TE_PROCESS_ENTER, size = (300, 25))

		self.checkBox_onlyFullOcc = wx.CheckBox(self, -1, "Output only fully occupied rows")

		#self.button_inputFile_browse.SetBackgroundColour(wx.Colour(140, 250, 140))
		self.button_start = buttons.GenButton(self, -1, "Start", size = (200, 25))
		self.button_start.SetBackgroundColour(wx.Colour(140, 250, 140))

		self.SetBackgroundColour(wx.Colour(210, 210, 210))

		# add stuff to the sizers
		self.sizer_inputFile1_h.Add(self.listBox_inputFiles, 0, wx.RIGHT, 5)
		self.sizer_inputFile1_h.Add(self.button_inputFiles_browse, 0, wx.LEFT, 5)
		self.sizer_inputFile2_h.Add(self.text_ctrl_inputFile2, 0, wx.RIGHT, 5)
		self.sizer_inputFile2_h.Add(self.button_inputFile2_browse, 0, wx.LEFT, 5)
		self.sizer3_v.Add(self.label_inputFiles, 0, wx.ALL, 5)
		self.sizer3_v.Add(self.sizer_inputFile1_h, 0, wx.ALL, 5)
		self.sizer3_v.Add(self.label_colsToAlign, 0, wx.ALL, 5)
		self.sizer3_v.Add(self.text_ctrl_colsToAlign, 0, wx.ALL, 5)
		self.sizer3_v.Add(self.label_outputFile, 0, wx.ALL, 5)
		self.sizer3_v.Add(self.sizer_inputFile2_h, 0, wx.ALL, 5)
		self.sizer3_v.Add(self.checkBox_onlyFullOcc, 0, wx.ALL, 5)
		self.sizer_main_v.Add(self.sizer3_v, 0, wx.ALL, 5)
		self.sizer_main_v.Add(self.button_start, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5)

		# set the sizer
		self.SetSizer(self.sizer_main_v)

		# set up drag'n drop
		dropTarget2 = FileDropTarget(self.text_ctrl_inputFile2)
		self.text_ctrl_inputFile2.SetDropTarget(dropTarget2)
		dropTarget1 = InputFileDropTarget(self.listBox_inputFiles, self)
		self.listBox_inputFiles.SetDropTarget(dropTarget1)

		# bind buttons

		self.listBox_inputFiles.Bind(wx.EVT_KEY_DOWN, self.OnListEvtKeyDown)#, self.listBox_inputFiles)
		self.Bind(wx.EVT_KEY_DOWN, self.OnListEvtKeyDown)#, self.listBox_inputFiles)

		self.Bind(wx.EVT_BUTTON, self.OnBrowse, self.button_inputFiles_browse)
		self.Bind(wx.EVT_BUTTON, self.OnBrowse2, self.button_inputFile2_browse)
		self.Bind(wx.EVT_CHECKBOX, self.OnCheckOnlyFullOcc, self.checkBox_onlyFullOcc)
		self.Bind(wx.EVT_BUTTON, self.OnStart, self.button_start)

		# initialize used variables
		self.inputFilePath = None

	def OnMenuOutputWin(self, evt):

		if not self.winOpen:
			#self.debug.Center()
			self.output.Show(True)
			self.winOpen = True
		else:
			self.output.Show(False)
			self.winOpen = False

	def OnListEvtKeyDown(self, evt):

		keycode = evt.GetKeyCode()

		if keycode == wx.WXK_DELETE:
			entries = []
			for index in self.listBox_inputFiles.GetSelections():
				entries.append(self.listBox_inputFiles.GetString(index))

			for entry in entries:
				del self.dictInputFiles[entry]

			self.listBox_inputFiles.Set(self.dictInputFiles.keys())

	def OnBrowse1(self, evt):
		dlg = wx.FileDialog(self, "Xcalibur spectra directory", style=wx.DD_DEFAULT_STYLE|wx.FD_SAVE)

		if dlg.ShowModal() == wx.ID_OK:
			inputFilePath = dlg.GetPath()

		dlg.Destroy()
		self.text_ctrl_inputFile1.SetValue(inputFilePath)

	def OnBrowse(self, evt):
		dlg = wx.FileDialog(self, "Select LipidXplorer result files for alignment.", style=wx.DD_DEFAULT_STYLE|wx.FD_MULTIPLE)

		if dlg.ShowModal() == wx.ID_OK:
			inputFilePath = dlg.GetPaths()

		dlg.Destroy()

		for p in inputFilePath:

			if os.path.isdir(p):
				for root, dirs, files in os.walk(p):
					for f in files:
						if re.match('(.*\.csv$)', f):
							n = os.path.join(root, f)
							l = n.split(os.sep)
							self.parent.dictInputFiles[l[-1]] = n
			else:
				l = p.split(os.sep)
				self.dictInputFiles[l[-1]] = p

		self.listBox_inputFiles.Set(self.dictInputFiles.keys())

	def OnBrowse2(self, evt):
		dlg = wx.FileDialog(self, "LipidX aligned spectra (from the MasterScan)", style=wx.DD_DEFAULT_STYLE|wx.FD_SAVE)

		if dlg.ShowModal() == wx.ID_OK:
			inputFilePath = dlg.GetPath()

		dlg.Destroy()
		self.text_ctrl_inputFile2.SetValue(inputFilePath)

	def OnCheckOnlyFullOcc(self, evt):

		if self.checkBox_onlyFullOcc.GetValue():
			self.onlyFullOccupation = True
		else:
			self.onlyFullOccupation = False

	def OnStart(self, evt):

		# initialize some variables
		self.dictOutput = odict()

		# get the columns which are to be aligned
		self.colsToAlign = self.text_ctrl_colsToAlign.GetValue().replace(' ', '').split(',')
		colsToAlign_index = odict()
		for col in self.colsToAlign:
			colsToAlign_index[col] = []
		csvInputFiles = odict()

		allKeys = []
		intensityKeys = []
		nonIntensityKeys = []

		if self.dictInputFiles == {}:
			dlg = wx.MessageDialog(self, "There are no input files", "Error", wx.ICON_ERROR)
			if dlg.ShowModal() == wx.ID_OK:
				dlg.Destroy()
				return None

		for file in self.dictInputFiles.keys():

			csvInputFiles[file] = csv.DictReader(open(self.dictInputFiles[file], 'rb'), delimiter=",")

			# get the index of the colsToAlign (to generate a primary key)
			for index in range(len(csvInputFiles[file].fieldnames)):
				for col in self.colsToAlign:
					if col == csvInputFiles[file].fieldnames[index]:
						colsToAlign_index[col].append(index)

			# get the horizontal entry of the thing to be aligned
			for row in csvInputFiles[file]:

				# sort the rows
				row_sorted = odict()
				for key in sorted(row.keys()):
					row_sorted[key] = row[key]

				# get the values of the columns to align for the current row
				values = []
				for col in self.colsToAlign:
					try:
						values.append(row_sorted[col])
					except KeyError:
						print "KeyError in %s with %s" % (file,col)

				# format the values to a dictionary entry, which will form the output
				for index in range(len(values)):
					if not isinstance(values[index], str):
						values[index] = "%s" % values[index]
				strValues = ','.join(values)

				# the strValues are the content of the primary key

				# add the entries to the ouput
				if not self.dictOutput.has_key(strValues):
					self.dictOutput[strValues] = odict()
					self.dictOutput[strValues][file] = row_sorted
				else:
					self.dictOutput[strValues][file] = row_sorted

				for key in row_sorted.keys():
					if key:
						if not key in allKeys:
							allKeys.append(key)
						if re.match('.*:.*', key):
							if not key in intensityKeys:
								intensityKeys.append(key)
						else:
							if not key in nonIntensityKeys and not key in self.colsToAlign:
								nonIntensityKeys.append(key)
					else:
						del row_sorted[key]

		intensityKeysAbbr = []
		for sample in intensityKeys:
			m = re.match('(.*):(.*)', sample)
			if m:
				if not "%s:" % m.group(1) in intensityKeysAbbr:
					intensityKeysAbbr.append("%s:" % m.group(1))


		################################################
		### open the window for choosing the columns ###
		nonIntensityKeys.sort()
		intensityKeysAbbr.sort()
		self.win_chooseCols = ChooseColFrame(self, -1, "Choose the colums you like to have in the output")
		self.win_chooseCols.Show(True)
		self.win_chooseCols.fillRightWindow(nonIntensityKeys + intensityKeysAbbr)

	def StartAlignment(self):

		col_m = re.compile('.*:')

		print " *** Preparing the output format *** "

		# collect the filenames of the files to merge
		filenames = []
		for i in self.dictOutput.keys():
			for file in self.dictOutput[i].keys():
				if not file in filenames:
					filenames.append(file)

		# generate dummy entries for filename for empty files
		for i in self.dictOutput.keys():
			for file in filenames:
				if not file in self.dictOutput[i].keys():
					self.dictOutput[i][file] = odict()

		# sort out the intensity columns and the non intensity columns
		columnsChoosenNonIntensity = []
		columnsChoosenIntensity = []
		for col in self.win_chooseCols.columnsChoosen:
			if col_m.match(col):
				columnsChoosenIntensity.append(col)
			else:
				columnsChoosenNonIntensity.append(col)

		### make header for csv output ###
		colIntensitiesSamples = []
		fileSamples = odict()

		# collect all the intensity columns
		#count = 0
		#samples = []
		for entry in self.dictOutput.keys():

			for file in filenames:
				count = 0
				samples = []
				if self.dictOutput[entry][file] != {}:
					for col in columnsChoosenIntensity:
						for sample in self.dictOutput[entry][file].keys():
							if re.match('%s.*' % col, sample):
								if not sample in colIntensitiesSamples:
									colIntensitiesSamples.append(sample)
								samples.append(sample)
								count += 1

				# sort the samples according to thier origin
				if not file in fileSamples.keys() and count > 0:
					fileSamples[file] = odict()
					fileSamples[file]['samples'] = samples
					fileSamples[file]['count'] = count


		del samples
		del count

		# collect the intensity data into dictOutputSamples
		dictOutputSamples = odict()
		for entry in self.dictOutput.keys():
			# put all entries from different files into one dictionary
			dictOutputSamples[entry] = odict()
			for file in filenames:
				dictOutputSamples[entry][file] = odict()
				for sample in self.dictOutput[entry][file].keys():
					if not dictOutputSamples.has_key(sample):
						dictOutputSamples[entry][file][sample] = self.dictOutput[entry][file][sample]
					else:
						dictOutputSamples[entry][file]['%s-%s' % (sample, file)] = self.dictOutput[entry][file][sample]
						if '%s-%s' % (sample, file) not in colIntensitiesSamples:
							colIntensitiesSamples.append('%s-%s' % (sample, file))

		print " *** Start the alignment *** "

		#####################################
		### START writing the output file ###
		#####################################

		outputKeys = odict()
		outputCSV = StringIO()

		# format the output header
		for col in self.colsToAlign:
			outputCSV.write(",")

		# format the header with the input files
		for file in filenames:
			outputCSV.write("%s," % file)
			for i in range(len(columnsChoosenNonIntensity) - 1):
				outputCSV.write(",")
			if fileSamples.has_key(file):
				for i in range(fileSamples[file]['count']):
					outputCSV.write(",")
		outputCSV.write("\n")

		# write the header with the column names
		for col in self.colsToAlign:
			outputCSV.write("%s," % col)

		for file in filenames:
			outputKeys[file] = []
			for col in columnsChoosenNonIntensity:
				outputCSV.write("%s," % col)
				outputKeys[file].append(col)

			print ">>>", fileSamples
			if file in fileSamples.keys():
				for sample in colIntensitiesSamples:
					if sample in fileSamples[file]['samples']:
						outputCSV.write("%s," % sample)
						outputKeys[file].append(sample)
		outputCSV.write("\n")

		### go through the aligned entries ###
		countEntries = 0
		lengthEntries = len(self.dictOutput.keys())
		f_output = open(self.text_ctrl_inputFile2.GetValue(), 'w+')
		f_output.write(outputCSV.getvalue())

		for entry in sorted(self.dictOutput.keys()):

			### write the non intensity columns ###

			countEntries += 1
			csvOut = ""

			# count the occupied columns (for filtering the not fully occupied)
			if self.onlyFullOccupation:
				count = 0
				keys = 0
				for file in filenames:
					for col in outputKeys[file]:
						keys += 1
						if self.dictOutput[entry][file].has_key(col) or \
							dictOutputSamples[entry][file].has_key(col):
							count += 1

				# if the user checks the "only full occupied"
				cont = False
				if count == keys:
					cont = True
					for col in self.colsToAlign:
						if self.dictOutput[entry][file].has_key(col):
							if self.dictOutput[entry][file][col] == '':
								cont = False
			else:
				cont = True

			if cont:

				if countEntries % 10 == 0:
					print "\n%d done - %d to go" % (countEntries, lengthEntries - countEntries)
				else:
					print ".",

				# write the entries of the colums to align
				csvOut += '%s,' % entry

				for file in filenames:
					#if self.dictOutput[entry][file] != {}:

					for col in outputKeys[file]:
						if self.dictOutput[entry][file].has_key(col):
							#outputCSV.write('%s,' % self.dictOutput[entry][file][col])
							csvOut += '%s,' % self.dictOutput[entry][file][col]
						elif dictOutputSamples[entry][file].has_key(col):
							#outputCSV.write('%s,' % dictOutputSamples[entry][file][col])
							csvOut += '%s,' % dictOutputSamples[entry][file][col]
						else:
							#outputCSV.write(',')
							csvOut += '0,'

				f_output.write(csvOut + '\n')

		print ""
		print " *** Write the output file *** "

		### write the output to the given filename ###
		#f = open(self.text_ctrl_inputFile2.GetValue(), 'w')
		#f.write(outputCSV.getvalue())
		#f.close()
		f_output.close()

		print " *** Finished *** "

class MyApp(wx.App):

	def OnInit(self):
		self.frame = MyFrame(None, -1, 'LXMerge')
		self.frame.Show(True)
		self.frame.Center()
		return True

app = MyApp(0)
app.MainLoop()

