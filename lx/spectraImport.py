#!/usr/bin/python
import csv
import os, sys, re
from optparse import OptionParser

import time

sysPath = '..' + os.sep + 'lib'
sys.path.append(sysPath)

from lx.tools import reportout, unique
from lx.mfql.runtimeStatic import TypeTolerance
from lx.exceptions import LipidXException
from lx.spectraContainer import MasterScan, SurveyEntry
from lx.spectraTools import recalibrateMS, recalibrateMSMS, saveSC
from lx.readSpectra import add_Sample, add_mzXMLSample, add_DTASample, add_CSVSample
from lx.alignment import mkSurveyLinear, \
		 mkMSMSEntriesLinear_new, \
		 specEntry, linearAlignment

from lx.debugger import Debug

# for debugging
#from guppy import hpy


def groups_file_path(import_dir):
	"""Return the path of the optional groups.txt inside an import directory.

	Kept as a named helper so the join can be unit tested: the caller is
	several hundred lines long and needs a fully populated options object.
	"""
	return os.path.join(import_dir, "groups.txt")


def lpdxImportDEF_new(parent, options=None):
	'''This version of importDEF does not process the options, since
	it assumes that they are already processed by lx.options.py'''

	# generate MasterScan object
	scan = MasterScan(options)

	scan.importSettingsFile = options['ini']
	#scan.setting = options['setting']
	if not parent is None:
		scan.setting = parent.currentConfiguration
	else:
		scan.setting = options['setting']
	scan.importDir = options['importDir']

	# check if last char is a '/':
	if scan.importDir[-1] == os.sep:
		scan.importDir = scan.importDir[:-1]


	# load occupation threshold settings
	if os.path.exists(groups_file_path(scan.importDir)):
		with open(groups_file_path(scan.importDir)) as f:
			s = f.readlines()
			if not s == []:
				for i in s:
					#scan.sampleOccThr['MS'].append((float(i.split(':')[0]), [x.strip() for x in i.split(':')[1].split(',')]))
					#scan.sampleOccThr['MSMS'].append((float(i.split(':')[0]), [x.strip() for x in i.split(':')[1].split(',')]))
					scan.sampleOccThr['MS'].append((options['MSminOccupation'], [x.strip() for x in i.split(',')]))
					scan.sampleOccThr['MSMS'].append((options['MSMSminOccupation'], [x.strip() for x in i.split(',')]))
			else:
				scan.sampleOccThr['MS'] = [(options['MSminOccupation'], [])]
				scan.sampleOccThr['MSMS'] = [(options['MSMSminOccupation'], [])]
	else:
		scan.sampleOccThr['MS'] = [(options['MSminOccupation'], [])]
		scan.sampleOccThr['MSMS'] = [(options['MSMSminOccupation'], [])]

	(listFiles, isTaken, isGroup) = getInputFiles(scan.importDir, options)

	scan.listFiles = listFiles
	print("options['masterScanImport'] in importDEF_new():", options['masterScanImport']) #lx.options.optionsDict
	return (options, scan, scan.importDir, options['masterScanImport'], parent, listFiles, isTaken, isGroup)


def getInputFiles(importDir, options):

	if not os.path.exists(importDir):
		raise LipidXException("Sample data '%s' folder not found." % importDir)

	if not os.path.isdir(importDir):
		raise LipidXException("Sample data '%s' is not a folder." % importDir)

	listFiles = []
	isGroup = False
	groupedSamples = False
	isTaken = False

	for root, dirs, files in os.walk(importDir):

		# import XML without having groups
		if not (re.match(r'(^\.\w+).*|.*\.svn.*', root)) and \
				options['spectraFormat'] in ['mzML', 'mzXML', 'raw', 'rawA', 'csv']:

			if options['spectraFormat'] == 'rawA':
				ext = 'raw'
			else:
				ext = options['spectraFormat']

			isTaken = True
			if not re.match(r'(^\.\w+).*|.*\.svn.*', root):
				for f in files:
					if re.match(r'(.*\.%s$)|(.*\.xml)' % ext, f,\
							re.IGNORECASE):
						listFiles.append([root + os.sep + f, root])

				# it is empty when folders for sample groups are given, because
				# this is the first point where os.walk() will be
				if listFiles == []:
					groupedSamples = True

				if groupedSamples and listFiles != []:
					samplegroupName = listFiles[0][1].split(os.sep)[-1]

		# import *.dta without having groups
		elif not (re.match(r'(^\.\w+).*|.*\.svn.*', root)) and options['spectraFormat'] == 'dta/csv':
			isTaken = True
			for i in dirs:
				if not re.match(r'(^\.\w+).*|.*\.svn.*', i):
					listFiles.append([root + os.sep + i, i])
     
		elif not (re.match(r'(^\.\w+).*|.*\.svn.*', root)) and options['spectraFormat'] == 'csv':
			isTaken = True
			for f in files:
				if re.match(r'.*\.csv$', f, re.IGNORECASE):
					listFiles.append([root + os.sep + f, root])
            

		elif re.match(r'(^\.\w+).*|.*\.svn.*', root):
			pass

		else:
			raise LipidXException("Problems with the data format %s in %s" % (options['spectraFormat'], root))


	if listFiles == []:
		raise LipidXException("No spectra files with the format *.%s found." % \
				options['spectraFormat'])

	return (listFiles, isTaken, isGroup)


def doImport(options, scan, importDir, output, parent, listFiles, isTaken, isGroup, alignmentMS, alignmentMSMS, scanAvg, importMSMS = True):

	### set standard values

	assert isinstance(importMSMS, type(True))

	if Debug("logMemory"):
		from guppy import hpy
		import memory_logging


	# some statistics
	nb_ms_scans = []
	nb_ms_peaks = []
	nb_msms_scans = []
	nb_msms_peaks = []

	# time
	starttime = time.perf_counter()

	# go recursively through the directory
	listPolarity = []
	dictBasePeakIntensity = {}
	progressCount = 0

	#print("options data type in doImport():", type(options)) #<class 'lx.options.optionsDict'>
 
	# the scan.dictSample variable is filled with
	# MSmass and MSMS classes. This means, the raw *.dta
	# and *.csv data is loaded into scan.dictSample.
	# After loading the cleaning algorithm is applied.
	if options['spectraFormat'] == 'dta/csv' and isTaken:
		if listFiles != []:
			listFiles.sort()

			for i in listFiles:
				ret = add_DTASample(scan, i[0], i[1],
					MSmassrange = scan.options['MSmassrange'],
					MSMSmassrange = scan.options['MSMSmassrange'],
					importMSMS = importMSMS,
					thresholdType = scan.options['MSthresholdType'])

				listPolarity.append(ret[0])
				dictBasePeakIntensity[ret[2]] = ret[1]
				nb_ms_peaks.append(ret[3])
		print("add_DTASample...............done")




	# the scan.dictSample variable is filled with
	# MSmass and MSMS classes taken from mzXML files.
	# After loading the cleaning algorithm is applied.
	elif listFiles != []:
		listFiles.sort()

		for i in listFiles:

			#		return parent.CONST_THREAD_USER_ABORT

			if options['spectraFormat'] == "mzXML": # old mzXML import. I don't wanna touch this
				ret = add_mzXMLSample(scan, i[0], i[1],
					timerange = scan.options['timerange'],
					MSmassrange = scan.options['MSmassrange'],
					MSMSmassrange = scan.options['MSMSmassrange'],
					scanAveraging = scanAvg,
					isGroup = isGroup,
					importMSMS = importMSMS,
					MSthresholdType = scan.options['MSthresholdType'],
					MSMSthresholdType = scan.options['MSMSthresholdType'])
    
			elif options['spectraFormat'] == "csv":
				ret = add_CSVSample(
					scan,
					i[0],
					i[1],
					options=scan.options,
					timerange=scan.options['timerange'],
					MSmassrange=scan.options['MSmassrange'],
					MSMSmassrange=scan.options['MSMSmassrange'],
					scanAveraging=scanAvg,
					isGroup=isGroup,
					importMSMS=importMSMS,
					MSthresholdType=scan.options['MSthresholdType'],
					MSMSthresholdType=scan.options['MSMSthresholdType']
				)

			elif options['spectraFormat'] == 'mzML': # the new import routine, :-)
				ret = add_Sample(scan, i[0], i[1],
					options = scan.options,
					timerange = scan.options['timerange'],
					MSmassrange = scan.options['MSmassrange'],
					MSMSmassrange = scan.options['MSMSmassrange'],
					scanAveraging = scanAvg,
					isGroup = isGroup,
					importMSMS = importMSMS,
					MSthresholdType = scan.options['MSthresholdType'],
					MSMSthresholdType = scan.options['MSMSthresholdType'],
					fileformat = "mzML")
			
				



			dictBasePeakIntensity[ret[0]] = ret[1]

			if len(ret) > 2:
				nb_ms_scans.append(ret[2])
				nb_ms_peaks.append(ret[3])
				nb_msms_scans.append(ret[4])
				nb_msms_peaks.append(ret[5])
			
			from time import sleep
			sleep(1) # dirty hack to reduce threading problem, give enough time for UI to update
			# os if you enable memory logging it crashes in the same way


		if not len(list(dictBasePeakIntensity.keys())) > 0:
			raise LipidXException("Something wrong with the calculation of the base peaks")



	else:
		raise LipidXException("No valid option given.")


	### print some information ###
	stats_file_entry = {}
	if not options['spectraFormat'] == 'dta/csv':
		#print("print some information for dta/csv--------------------------------------------------------------")
		if options['MSfilter'] and options['MSfilter'] > 0:
			reportout("> {0:.<30s}{1:>11.2f}".format('MS filter settings', options['MSfilter']))
		if options['MSMSfilter'] and options['MSMSfilter'] > 0:
			reportout("> {0:.<30s}{1:>11.2f}".format('MS/MS filter settings', options['MSMSfilter']))
		if len(nb_ms_scans) > 0:
			reportout("> {0:.<30s}{1:>11.2f}".format('Avg. Nb. of MS scans', sum(nb_ms_scans) / len(nb_ms_scans)))
			stats_file_entry["nb_ms_scans"] = sum(nb_ms_scans)
		if len(nb_ms_peaks) > 0:
			reportout("> {0:.<30s}{1:>11.2f}".format('Avg. Nb. of MS peaks', sum(nb_ms_peaks) / len(nb_ms_peaks)))
			stats_file_entry["nb_ms_peaks"] = sum(nb_ms_peaks)
		if len(nb_msms_scans) > 0:
			reportout("> {0:.<30s}{1:>11.2f}".format('Avg. Nb. of MS/MS scans', sum(nb_msms_scans) / len(nb_msms_scans)))
			stats_file_entry["nb_msms_scans"] = sum(nb_msms_scans)
		if len(nb_msms_peaks) > 0:
			reportout("> {0:.<30s}{1:>11.2f}".format('Avg. Nb. of MS/MS peaks', sum(nb_msms_peaks) / len(nb_msms_peaks)))
			stats_file_entry["nb_msms_peaks"] = sum(nb_msms_peaks)

	loadingtime = time.perf_counter() - starttime
	reportout("%.2f sec. for reading the spectra" % loadingtime)
	stats_file_entry["loading_time"] = loadingtime

	if Debug("logMemory"):
		print("ML> spectra loaded and averaged:", memory_logging.pythonMemory())
	#	print "MLh> spectra loaded and averaged: ", hpy().heap()

################### ballal changed it#######################
	# Precursor mass shift
	if (not scan.options.isEmpty('precursorMassShift')) and scan.options['precursorMassShift']:
		shift = float(scan.options['precursorMassShift'])
		if shift != 0:
			print("Applying precursor mass shift")
			scan.shiftPrecursors(shift)

	if (not scan.options.isEmpty('precursorMassShiftOrbi')) and scan.options['precursorMassShiftOrbi']:
		shift_orbi = float(scan.options['precursorMassShiftOrbi'])
		if shift_orbi != 0:
			print("Applying precursor mass shift for Scanline error on Orbitrap data.")
			scan.shiftPrecursorsInRawFilterLine(shift_orbi)




	scan.listSamples.sort()

	if listPolarity == []:
		listPolarity = [-1,1]
	else:
		listPolarity = unique(listPolarity)

	# recalibrate MS spectra
	if not scan.options.isEmpty('MScalibration'):
		recalibrateMS(scan, scan.options['MScalibration'])
	if not scan.options.isEmpty('MSMScalibration') and (scan.options['MSMScalibration']):
		recalibrateMSMS(scan, scan.options['MSMScalibration'])

	calibrationtime = time.perf_counter() - starttime - loadingtime
	reportout("%.2f sec. for calibrating the spectra" % calibrationtime)
	stats_file_entry["calibration_time"] = calibrationtime

	# align MS spectra
	print("Aligning MS spectra.........................", alignmentMS)

	if Debug("logMemory"):
		print("ML> before alignment (MS):", memory_logging.pythonMemory())


	### align the spectra for the MasterScan ###

	if alignmentMS == "linear":
		mkSurveyLinear(scan, [-1,1],
					numLoops = options['loopNr'],
					deltaRes = scan.options['MSresolutionDelta'],
					minocc = scan.options['MSminOccupation'])

	elif alignmentMS == "hierarchical":
		# experimental
		mkSurveyHierarchical(scan, '',
					numLoops = options['loopNr'],
					deltaRes = scan.options['MSresolutionDelta'],
					minocc = scan.options['MSminOccupation'])

	

	progressCount += 1



	### some infos ###

	reportout("> {0:.<30s}{1:>11d}\n".format('Nb. of MS peaks (after alg.)', len(scan.listSurveyEntry)))
	stats_file_entry["nb_ms_peaks_after_alg"] = len(scan.listSurveyEntry)

	if Debug("logMemory"):
		print("ML> after alignment (MS):", memory_logging.pythonMemory())
	#	print "MLh> after alignment (MS):", hpy().heap()

	#if not keepGoing:
	#	print "Stopped by user."
	#	parent.isRunning = False
	#	return None


	### aling the fragment spectra ###

	# Preparation of MSMS experiments is:
	# 1) clustering of the dta's precursor masses according
	#	 to MS accuracy -> every cluster contains all MSMS
	#    experiments for precursor mass m where thier dta-precursor
	#	 mass p is in [m - MSaccuracy, m + MSaccuracy]
	# 2) The MSMS experiments of one cluster c are then
	#	 merged with the known merging algorithm
	# 3) Every cluster c is associated to a precursor mass M
	#	 from the SurveyEntry list. This takes the
	#	 given selectionWindow into account.
	if importMSMS:
		reportout("Aligning MS/MS spectra in doImport() %s\n" % alignmentMSMS)
		if alignmentMSMS == "linear":
			mkMSMSEntriesLinear_new(scan, listPolarity,
								numLoops = options['loopNr'],
								isPIS = False)
		

	alignmenttime = time.perf_counter() - starttime - loadingtime - calibrationtime
	reportout("%.2f sec. for aligning the spectra\n" % alignmenttime)
	stats_file_entry["alignment_time"] = alignmenttime

	for sample in scan.listSamples:
		if sample in scan.dictSamples:
			del scan.dictSamples[sample]
	del scan.dictSamples

	if Debug("logMemory"):
		print("ML> after alignment of MS/MS:", memory_logging.pythonMemory())
	#	print "MLh> ", hpy().heap()

	progressCount += 1
	#if parent:
	#	(cont, skip) = parent.debug.progressDialog.Update(progressCount)
	#	if not cont:
	#		print "Stopped by user."
	#		parent.debug.progressDialog.Destroy()
	#		return parent.CONST_THREAD_USER_ABORT

	#if not keepGoing:
	#	print "Stopped by user."
	#	parent.isRunning = False
	#	return None

	scan.sortAndIndedice()
	for se in scan.listSurveyEntry:
		se.sortAndIndedice()

	if options['settingsPrefix']:
		splitext = os.path.splitext(output)
		output = splitext[0] + "-" + scan.setting + splitext[1]

	
	if options['batch_mode']:
		#print("don't save MasterScan")
		return scan
	else:
		print("Save output to %s." % output)
		saveSC(scan, output)

		total_runtime = time.perf_counter() - starttime
		reportout("%.2f sec. for the whole import process" % (total_runtime))
		reportout("\n")
		stats_file_entry["total_runtime"] = total_runtime

		stats_file_keys = ["nb_ms_scans", "nb_ms_peaks", "nb_msms_scans", "nb_msms_peaks", "nb_ms_peaks_after_alg", "loading_time", "calibration_time", "alignment_time", "total_runtime"]
		stats_file_data = [stats_file_entry]
		stats_file = os.path.splitext(output)[0] + "-stats.csv"
		try:
			with open(stats_file, 'w') as csvfile:
				writer = csv.DictWriter(csvfile, fieldnames=stats_file_keys)
				writer.writeheader()
				for data in stats_file_data:
					writer.writerow(data)
		except IOError:
			raise LipidXException("Writing of statistics to file '%s' failed." % stats_file)

	if parent:
		#parent.debug.progressDialog.Destroy()
		return parent.CONST_THREAD_SUCCESSFUL



if __name__ == "__main__":
	pass
	#(options, scan, importDir, output) = lpdxImportCLI()
