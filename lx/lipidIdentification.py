#!/usr/bin/python

import re

#sysPath = '..' + os.sep + 'lib'
#sys.path.append(sysPath)

from lx.mfql.runtimeExecution import TypeMFQL
from lx.mfql.mfqlParser import startParsing
from lx.exceptions import LipidXException
from lx.tools import odict
from lx.spectraTools import *
from lx.options import Options

def syntaxCheck(
					queries = None,
					masterscan = None,
					parent = None):

	opts = {}
	opts['queries'] = queries

	# collect all mfql scripts
	mfqlFiles = odict()
	if opts['queries'] != [None]:
		for arg in opts['queries']:
			if re.match('(.*\.mfql$)|(.*\.py$)', arg):
				with open(opts['queries'][arg], 'r') as mfqlFile:
					mfqlFiles[arg] = mfqlFile.read()

	print "\n****** Starting Syntax Check ******\n"

	return 1

def startFromGUI(
					parent = None,
					queries = None,
					options = {}):

	progressCount = 0

	# collect all mfql scripts
	mfqlFiles = odict()
	if queries != [None]:
		for arg in queries:
			if re.match('(.*\.mfql$)|(.*\.py$)', arg):
				#mfqlFiles[arg] = open(arg, 'r').read()
				with open(queries[arg], 'r') as mfqlFile:
					mfqlFiles[arg] = mfqlFile.read()

	print "\n****** Starting MFQL interpretation ******\n"

	# collect masterscan file
	if options['masterScan']:
		try:
			masterscan = loadSC(options['masterScan'])
		except IOError:
			raise LipidXException("The MasterScan does not exist. You need to generate it by importing " + \
					"your samples. Please have a look into the LipidXplorer tutorial to find out how to " + \
					"import spectra and generate a MasterScan.")
		progressCount += 1
		if parent:
			(cont, skip) = parent.debug.progressDialog.Update(progressCount)
			if not cont:
				parent.debug.progressDialog.Destroy()
				return parent.CONST_THREAD_USER_ABORT

	else:
		raise ValueError("MasterScan file has to be specificated with -s")

	# execute lipidX

	mfqlObj = TypeMFQL(masterScan = masterscan)

	# give the options from the settings
	mfqlObj.options = options

	# give the options from the loaded MasterScan
	for i in mfqlObj.sc.options.keys():
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

		for k in result.dictQuery.values():
			if not options['compress']:
				strResult += "\n###,%s\n" % k.name
			strResult += k.strOutput
			if not options['compress']:
				strResult += '\n'

		# put out
		if not options['resultFile']:
			print strResult
		else:
			if parent:
				parent.writeOutput(options['resultFile'], strResult)
			else:
				writeOutput(options['resultFile'], strResult)

	else:
		print "\n <Query returned no result.>\n"

	# maybe dump the complementary MasterScan
	if options['complementMasterScan']:
		saveSC(mfqlObj.complementSC, options['complementMasterScanFile'])
		progressCount += 1
		if parent:
			(cont, skip) = parent.debug.progressDialog.Update(progressCount)
			if not cont:
				parent.debug.progressDialog.Destroy()
				return parent.CONST_THREAD_USER_ABORT

	# may dump the masterscan
	if options['dumpMasterScan']:

		if not options['masterScanInSQL']:
			masterscan.dump(options['dumpMasterScanFile'])
		else:
			masterscan.dumpInSQL(options['dumpMasterScanFile'])

	writeReport(options['masterScanFile'], options, queries)

	# return successfull for GUI
	if parent:
		parent.debug.progressDialog.Destroy()
		return parent.CONST_THREAD_SUCCESSFUL

def writeReport(file = "", options = {}, queries = {}):
	print "Writing HTML report from lipidIdentification.py"
	strReport = "<html><head></head><body>"
	strReport += "<br>"
	strReport += "%s" % genReportHTML(options, queries)
	strReport += "</body></html>"
	reportBaseFile = os.path.splitext(file)[0]
	print "Saving report to file " + reportBaseFile + "-report.html"
	with open(reportBaseFile + "-report.html", "w") as f:
		f.write(strReport)

def genReportHTML(options = {}, queries = {}):

	strBugReport = "<h3>Options</h3>\n"

	strBugReport += "<table>\n"
	for k in sorted(options.keys()):
		if not options.isEmpty(k):
			strBugReport += "<tr><td>%s:</td><td>%s</td></tr>\n" % (k, options[k])
	strBugReport += "</table><br>\n"

	strBugReport += "<h3>MFQL queries</h3><tt>\n"
	for i in queries:
		txt = ''
		if i != "":
			with open(queries[i], 'r') as f:
				txt += " \n\n>> filename: %s >>\n\n" % i
				txt += f.read()
				strBugReport += txt.replace('\n', '<br>')
	strBugReport += "</tt>"

	return strBugReport

if __name__ == "__main__":
	startFromCLI()
