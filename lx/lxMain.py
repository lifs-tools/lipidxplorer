# for import
from lx.lipidIdentification import writeReport
from lx.spectraImport import lpdxImportDEF_new

# for mfql spectra interpretation
from lx.exceptions import LipidXException
from lx.mfql.runtimeExecution import TypeMFQL
from lx.mfql.mfqlParser import startParsing
from lx.tools import odict
from lx.spectraTools import *
from lx.options import Options
from mztab.mztab_util import as_mztab

import time

# debugging
#from guppy import hpy
#import memory_logging
#import objgraph

def startImport(options, queries = None, parent = None, worker = None, lipidxplorer = False, optimization = False):

	######################################################
	###              start LipidXplorer                ###

	listIntermission = []

	listIntermission = lpdxImportDEF_new(
			options = options,
			parent = parent)

	if lipidxplorer:
		if not options['spectraFormat'] in ['dta/csv', 'mzXML', 'mzML']:
			raise LipidXException("The spectra format *.%s is not supported" % options['spectraFormat'])

	#if optimization:
	if False:
		from lx.spectraImportC import doImport_new as doImport
	else:
		from lx.spectraImport import doImport

	#if parent:
		#max = len(listIntermission[5]) + 3

		#if not parent is None:
		#	parent.debug.progressDialog = wx.ProgressDialog(
		#			"Importing spectra",
		#			"Finished, if the bar is filled completely.",
		#			max,
		#			style = wx.PD_CAN_ABORT)

	# listIntermission: (options, scan, importDir, output, parent, listFiles, isTaken, isGroup)
	if parent: # if started from GUI, put it in a thread
		worker.beginThread(doImport,
			listIntermission[0],
			listIntermission[1],
			listIntermission[2],
			listIntermission[3],
			listIntermission[4],
			listIntermission[5],
			listIntermission[6],
			listIntermission[7],
			options['alignmentMethodMS'],
			options['alignmentMethodMSMS'],
			options['scanAveragingMethod'],
			options['importMSMS'])

	else:

		doImport(
			listIntermission[0],
			listIntermission[1],
			listIntermission[2],
			listIntermission[3],
			listIntermission[4],
			listIntermission[5],
			listIntermission[6],
			listIntermission[7],
			options['alignmentMethodMS'],
			options['alignmentMethodMSMS'],
			options['scanAveragingMethod'],
			options['importMSMS'])


def startMFQL(options = {}, queries = {}, parent = None):

	# get the starting time for speed measure
	start = time.clock()

	progressCount = 0

	# collect all mfql scripts
	mfqlFiles = odict()
	if queries != {}:
		for arg in queries:
			if re.match('(.*\.mfql$)|(.*\.py$)', arg):
				#mfqlFiles[arg] = open(arg, 'r').read()
				with open(queries[arg], 'r') as mfqlFile:
					mfqlFiles[arg] = mfqlFile.read()

	print("\n****** Starting MFQL interpretation ******\n")

	# collect masterscan file
	if options['masterScanRun']:
		try:
			masterscan = loadSC(options['masterScanRun'])

		except IOError:
			raise LipidXException("The MasterScan does not exist. You need to generate it by importing " + \
					"your samples. Please have a look into the LipidXplorer tutorial to find out how to " + \
					"import spectra and generate a MasterScan.")
		#progressCount += 1
		#if parent:
		#	(cont, skip) = parent.debug.progressDialog.Update(progressCount)
		#	if not cont:
		#		parent.debug.progressDialog.Destroy()
		#		return parent.CONST_THREAD_USER_ABORT

	else:
		raise ValueError("MasterScan file has to be specificated with -s")

	mfqlObj = TypeMFQL(masterScan = masterscan)

	# give the options from the settings
	mfqlObj.options = options

	# give the options from the loaded MasterScan
	for i in list(mfqlObj.sc.options.keys()):
		if i in Options.importOptions and (not mfqlObj.sc.options.isEmpty(i)):
			mfqlObj.options[i] = mfqlObj.sc.options[i]

	# set the seperator
	if options['tabLimited']:
		mfqlObj.outputSeperator = '\t'
	else:
		mfqlObj.outputSeperator = ','

	# parse input file k and save the result in mfqlObj.result
	(progressCount, returnValue) = startParsing(mfqlFiles,
				mfqlObj,
				masterscan,
				isotopicCorrectionMS = options['isotopicCorrectionMS'],
				isotopicCorrectionMSMS = options['isotopicCorrectionMSMS'],
				complementSC = options['complementMasterScan'],
				parent = parent,
				progressCount = progressCount,
				generateStatistics = options['statistics'],
				)

	if parent:
		if returnValue == parent.CONST_THREAD_USER_ABORT:
			return parent.CONST_THREAD_USER_ABORT

	# process the result
	result = mfqlObj.result
	if result.mfqlOutput:
		txt = as_mztab(result)

	if result.mfqlOutput:
		strHead = ''
		if not options['noHead']:
			for key in result.listHead:
				if key != result.listHead[-1]:
					strHead += key + '%s' % mfqlObj.outputSeperator
				else:
					strHead += key

			# generate whole string
			strResult = "%s\n" % strHead
		else:
			strResult = ''

		for k in list(result.dictQuery.values()):
			if not options['compress']:
				strResult += "\n###,%s\n" % k.name
			strResult += k.strOutput
			if not options['compress']:
				strResult += '\n'

		# free 'k' because otherwise Python keeps all
		# the SurveyEntries. Don't ask me why...
		del k

		# put out
		if not options['resultFile']:
			print(strResult)
		else:
			if parent:
				parent.writeOutput(options['resultFile'], strResult)
			else:
				with open(options['resultFile'], 'w') as f:
					f.write(strResult)
	else:
		print("\n <Query returned no result.>\n")

	# maybe dump the complementary MasterScan
	if options['complementMasterScan']:
		saveSC(mfqlObj.complementSC, options['complementMasterScanFile'])
		#progressCount += 1
		#if parent:
		#	(cont, skip) = parent.debug.progressDialog.Update(progressCount)
		#	if not cont:
		#		parent.debug.progressDialog.Destroy()
		#		return parent.CONST_THREAD_USER_ABORT

	# may dump the masterscan
	if options['dumpMasterScan']:

		if not options['masterScanInSQL']:
			masterscan.dump(options['dumpMasterScanFile'])
		else:
			masterscan.dumpInSQL(options['dumpMasterScanFile'])

	writeReport(options['masterScanFileRun'], options, queries)

	del result.dictQuery
	del result
	del masterscan
	del mfqlObj

	print("\nOverall time needed for identification: %d:%d" % ((time.clock() - start) / 60, (time.clock() - start) % 60))

	# return successfull
	if parent:
		#parent.debug.progressDialog.Destroy()
		return parent.CONST_THREAD_SUCCESSFUL


