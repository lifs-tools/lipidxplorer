import os, re, numpy
from copy import deepcopy
from math import sqrt
from glob import glob
from lx.fileReader.mzAPI import mzFile
from lx.fileReader.mzxml import PrecursorSort, MzXMLFileReader
from lx.alignment import specEntry, linearAlignment, heuristicAlignment, mergeSumIntensity, doClusterSample, lpdxClusterMSMS
from lx.tools import reportout
from lx.spectraContainer import Sample, MSMass, MSMS
from lx.exceptions import LipidXException

from lx.debugger import Debug

# for debugging
# debugging
#from guppy import hpy
#import memory_logging
#import objgraph
#import pdb

# make a regular expression object for recognizing the entries
# of a .dta file
regDta = re.compile("(\d+\.?\d*)(\s|\t)+([-]?\d+\.?\d*)")

fadi_percentageMSMS = None # var used for filtering this is dirty code, TODO remove this global variable

def add_Sample(
		sc = None,
		specFile = None,
		specDir = None,
		options = {},
		**kwargs
		):

	#if Debug("logMemory"):
	#	from guppy import hpy
	#	import memory_logging

	# get comtypes for raw files
	if kwargs["fileformat"] == "raw":
		import comtypes
		comtypes.CoInitialize()

	# information of import
	nb_ms_scans = 0
	nb_ms_peaks = 0
	nb_msms_scans = 0
	nb_msms_peaks = 0

	# is the given file a hidden Directory?
	s = specFile.split(os.sep)
	for i in s:
		if re.match('(^\.\w+).*', i):
			raise LipidXException("The given path %s is not " +\
					"accepted by LipidXplorer." % specFile)

	specName = s[-1]

	# get the directory
	directory = os.sep.join(specFile.split(os.sep)[:-1])

	# start import
	reportout("Importing: %s" % specFile)

	# get time range and mass range
	if options['timerange']:
		t1 = options['timerange'][0] / 60
		t2 = options['timerange'][1] / 60

	if options['pisSpectra']:
		msm1 = options['MSMSmassrange'][0]
		msm2 = options['MSMSmassrange'][1]
	else:
		msm1 = options['MSmassrange'][0]
		msm2 = options['MSmassrange'][1]

	if options['MSMSmassrange']:
		msmsm1 = options['MSMSmassrange'][0]
		msmsm2 = options['MSMSmassrange'][1]

	global fadi_percentageMSMS
	fadi_percentageMSMS = options['MSMSfilter']

	# for MS/MS collection of spectra attributes
	polarity = ''
	count = 0

	# read the mz file
	mz_file = mzFile(specFile)

	#if Debug("logMemory"):
	#	print "ML> raw file loaded:", memory_logging.pythonMemory()
	#	print "MLh> ", hpy().heap()

	try:
		mz_file.time_range()
	except:
		raise LipidXException("Problems with the spectrum file %s." % specFile)

	# get MS1 scans
	get_ms1Scans = [(t, mz, sn, sm, pol, tic, np, bp) for t, mz, sn, st, sm, pol, tic, np, bp \
			in mz_file.scan_info(t1, t2, msm1, msm2) if st == 'MS1']

	ms1Scans = []
	for t, mz, sn, sm, pol, tic, np, bp in get_ms1Scans:

		# check for polarity switches which are not allowed right now
		if polarity != '':
			if pol != polarity:
				raise LipidXException(
					"It is not allowed to have both polarities within" \
						+ " one file")
		else:
			polarity = pol

		scan = mz_file.scan(scan_id=sn, time=t)

		# don't consider empty scans
		if len(scan) == 0:
			continue

		scan_processed = []

		# get relative intensity
		max_it = max([it_value for (mz_value, it_value, res, bl, ns, cg) in scan])
		if max_it <= 0:
			continue

		for mz1, it1, res, bl, ns, cg in scan:
			scan_processed.append((mz1, it1, it1 / max_it, res, bl, ns, cg))
			nb_ms_peaks += 1

		ms1Scans.append({
			'time' : t,
			'totIonCurrent' : tic,
			'polarity' : pol,
			'max_it' : max_it,
			'scan' : scan_processed})

		nb_ms_scans += 1

	#if Debug("logMemory"):
	#	print "ML> MS scans read from raw file:", memory_logging.pythonMemory()
	#	print "MLh> ", hpy().heap()

	# get MS2 scans
	get_ms2Scans = [(t, mz, sn, sm, pol, tic, np, bp) for t, mz, sn, st, sm, pol, tic, np, bp \
			in mz_file.scan_info(t1, t2, msm1, msm2) if st == 'MS2']

	ms2Scans = []
	for t, precursor, sn, sm, pol, tic, np, bp in get_ms2Scans:

		# check for polarity switches which are not allowed right now
		if polarity != '':
			if pol != polarity:
				raise LipidXException(
					"It is not allowed to have both polarities within" \
						+ " one file")
		else:
			polarity = pol

		scan = mz_file.scan(scan_id=sn, time=t)

		# don't consider empty scans
		if len(scan) == 0:
			continue

		nb_msms_scans += 1

		# filter for MS/MS mass range and relative intensity
		scan_processed = []
		max_it = max([mz_value for (mz_value, it_value, res, bl, ns, cg) in scan])
		for mz2, it2, res, bl, ns, cg in scan:
			if msmsm1 <= mz2 <= msmsm2:
				scan_processed.append((mz2, it2, it2 / max_it, res, bl, ns, cg))
				nb_msms_peaks += 1

		ms2Scans.append({
			'time' : t,
			'totIonCurrent' : tic,
			'polarity' : pol,
			'precursorMz' : precursor,
			'max_it' : max_it,
			'scan' : scan_processed})


	#if Debug("logMemory"):
	#	print "ML> MS/MS scans read from raw file:", memory_logging.pythonMemory()
	#	print "MLh> ", hpy().heap()

	avgBasePeakIntensity = 0

	# put the m/z values into specEntry data structure
	# for the alignment function
	if polarity == '-':
		p = -1
	elif polarity == '+':
		p = 1
	else:
		raise LipidXException("The polarity is given neither as '-' nor as '+'. "
				"It is %s" % polarity)

	# close the mz_file
	mz_file.close()

	# generate Sample
	lpdxSample = Sample(
				sampleName = specName,
				sourceDir = directory,
				sourceFile = specFile,
				polarity = p,
				options = options)
				#MSMSresolution = options['MSMSresolution'],
				#MSthreshold = options['MSthreshold'])

	# for getting only the stats, I set ms1scans and ms2scan to zero
	ms1Scans == []
	ms2Scans == []

	# get the total ion currents for statistics
	listTotIonCurrent = []
	numPeaks = -1 # init numPeaks to have it even if there are no ms1Scans

	# maybe there is only one polarity
	if len(ms1Scans) > 0:

		##################################
		### averaging of the MS1 scans ###

		# start averaging
		count = 0
		dictSpecEntry = {}
		for ms1scan_entry in ms1Scans:

			listTotIonCurrent.append(float(ms1scan_entry['totIonCurrent'])) # statistics

			dictSpecEntry[repr(count)] = []
			for mz, it, it_rel, res, bl, ns, cg in ms1scan_entry['scan']:
				if it > 0.0 and it_rel > 0.0:
					dictSpecEntry[repr(count)].append(specEntry(
						mass = mz,
						content = {'sample' : repr(count),
							'intensity' : it,
							'intensity_rel' : it_rel}))

			avgBasePeakIntensity += ms1scan_entry['max_it']
			count += 1

		# free unused stuff
		#if Debug("logMemory"):
		#	print "ML> generated specEntries for MS alignment", memory_logging.pythonMemory()
		#	print "MLh> ", hpy().heap()

		# as per fadi this is called on ms1
		fadi_denominator = count
		fadi_percentage = options['MSfilter']
		listClusters = linearAlignment(list(dictSpecEntry.keys()),
							dictSpecEntry,
							options['MSresolution'],
							merge = mergeSumIntensity,
							mergeTolerance = options['MSresolution'],
							mergeDeltaRes = options['MSresolutionDelta'], fadi_denominator= fadi_denominator, fadi_percentage = fadi_percentage)

		# free memory
		del dictSpecEntry

		#if Debug("logMemory"):
		#	print "ML> after MS averaging:", memory_logging.pythonMemory()
		#	print "MLh> after MS averaging:", hpy().heap()

		### averaging of the MS1 scans ###
		##################################


		###########################################
		### store the MS1 spectra in lpdxSample ###

		# get the threshold
		if options['MSthresholdType'] == 'absolute':
			thrshld_absolute = float(options['MSthreshold']) / sqrt(len(ms1Scans))
		else:
			thrshld_relative = float(options['MSthreshold']) / sqrt(len(ms1Scans))

		# get the keys for the individual scans
		keys = [repr(n) for n in range(count)]

		# get the average base peak intensity
		avgBasePeakIntensity = avgBasePeakIntensity / float(count)

		# for my interest
		numPeaks = 0

		# store the averaged spectrum
		for cl in listClusters:

			sumMass = 0
			sumMassIntensity = 0
			sumIntensity = 0
			sumIntensity_relative = 0

			# get the averaged intensity
			for sample in keys:#cl.keys():
				if sample in cl and cl[sample].content != {}:
					sumMass += cl[sample].mass
					sumMassIntensity += cl[sample].mass * cl[sample].content['intensity']
					sumIntensity += cl[sample].content['intensity']
					if 'intensity_rel' in cl[sample].content:
						sumIntensity_relative += cl[sample].content['intensity_rel']

			# empty intensity? make an empty entry
			if not sumIntensity > 0.0:
				out = specEntry(
					mass = sumMassIntensity,
					content = {'intensity' : 0.0,
						'intensity_rel' : 0.0}
					)
			else: # make new specEntry
				out = specEntry(
					mass = sumMassIntensity / sumIntensity,
					content = {})

				# write averaged intensity
				out.content['intensity'] = sumIntensity / len(keys) # divide by the total number of scan
				out.content['intensity_rel'] = sumIntensity_relative / len(keys)

			### store the averaged spectra in lpdxSample ###

			takeIt = False
			if options['MSthresholdType'] == 'absolute':
				if out.content['intensity'] >= thrshld_absolute:
					takeIt = True
			else:
				if out.content['intensity_rel'] >= thrshld_relative:
					takeIt = True

			if takeIt:
				numPeaks += 1
				lpdxSample.listPrecurmass.append(
					MSMass(
						precurmass = out.mass,
						intensity = out.content['intensity'],
						smpl = specName,
						polarity = p,
						charge = None,
						fileName = specFile,
						scanCount = count,
						basePeakIntensity = avgBasePeakIntensity))

		try:
			lpdxSample.base_peak_ms1 = max([x.intensity for x in lpdxSample.listPrecurmass])
		except ValueError:
			pass

		# free memory
		del listClusters

		### store the MS1 spectra in lpdxSample ###
		###########################################


	###########################################
	### store the MS2 spectra in lpdxSample ###

	# get the threshold
	if options['importMSMS']:
		if options['MSMSthresholdType'] == 'absolute':
			thrshld_absolute = float(options['MSMSthreshold'])
		else:
			thrshld_relative = float(options['MSMSthreshold'])

	# maybe there is no MS/MS?
	if len(ms2Scans) > 0:
		for ms2scan_entry in sorted(ms2Scans,
				cmp = lambda x,y : cmp(x['precursorMz'], y['precursorMz'])):
			if ms2scan_entry['scan'] != []:

				# add the fragment mass to the fragment spectrum
				lpdxSample.listMsms.append(MSMS(
					ms2scan_entry['precursorMz'],
					charge = None,
					polarity = p,
					fileName = specFile,
					scanNumber = None,
					retentionTime = ms2scan_entry['time'],
					peaksCount = None,
					totIonCurrent = ms2scan_entry['totIonCurrent'],
					basePeakMz = None,
					basePeakIntensity = ms2scan_entry['max_it'],
					threshold = options['MSMSthreshold']))

				#lpdxSample.listMsms[-1].entries = ms2scan_entry['scan']
				for mz, it, it_rel, res, bl, ns, cg in ms2scan_entry['scan']:
					if it > 0.0:
						lpdxSample.listMsms[-1].entries.append((mz, it, it_rel, res, bl, ns, cg))


	# if there was no MS/MS, take the survey m/z from the precursor masses
	if lpdxSample.listPrecurmass == []:
		set_PrecurmassFromMSMS(lpdxSample, chg = p)

	sc.dictSamples[specName] = lpdxSample
	sc.listSamples.append(specName)

	### calc the TIC scores ###
	listTotIonCurrent.sort()
	num = 0
	if len(listTotIonCurrent) < 5:
		pass
	elif len(listTotIonCurrent) < 20:
		del listTotIonCurrent[0]
		del listTotIonCurrent[-1]
	elif len(listTotIonCurrent) < 50:
		num = int((len(listTotIonCurrent) / 100) * 10)
		for i in range(num):
			del listTotIonCurrent[0]
			del listTotIonCurrent[-1]
	else:
		num = int((len(listTotIonCurrent) / 100) * 5)
		for i in range(num):
			del listTotIonCurrent[0]
			del listTotIonCurrent[-1]

	median = numpy.median(listTotIonCurrent)

	reportout("> {0:.<30s}{1:>11d}".format('Nb. of MS scans', nb_ms_scans))
	reportout("> {0:.<30s}{1:>11d}".format('Nb. of MS peaks', nb_ms_peaks))
	reportout("> {0:.<30s}{1:>11d}".format('Nb. of MS/MS scans', nb_msms_scans))
	reportout("> {0:.<30s}{1:>11d}".format('Nb. of MS/MS peaks', nb_msms_peaks))
	reportout("> {0:.<30s}{1:>11d}".format('Nb. of MS peaks (after avg.)', numPeaks))
	reportout("> Spray stability:")
	if listTotIonCurrent != []:
		reportout("> {0:.<30s}{1:>11.2f}% of median".format('  MaxTIC - MinTIC:', (100 * (float(max(listTotIonCurrent)) - float(min(listTotIonCurrent))) / float(median))))
	reportout("")

	# get comtypes for raw files
	if kwargs["fileformat"] == "raw":
		import comtypes
		comtypes.CoUninitialize()

	### End total ion count ###
	return (specName, lpdxSample.base_peak_ms1, nb_ms_scans, nb_ms_peaks, nb_msms_scans, nb_msms_peaks)


def add_Sample_AVG(
		sc = None,
		specFile = None,
		specDir = None,
		options = {},
		**kwargs
		):

	#if Debug("logMemory"):
	#	from guppy import hpy
	#	import memory_logging

	# information of import
	nb_ms_scans = 0
	nb_ms_peaks = 0
	nb_msms_scans = 0
	nb_msms_peaks = 0

	# is the given file a hidden Directory?
	s = specFile.split(os.sep)
	for i in s:
		if re.match('(^\.\w+).*', i):
			raise LipidXException("The given path %s is not " +\
					"accepted by LipidXplorer." % specFile)

	specName = s[-1]

	# get the directory
	directory = os.sep.join(specFile.split(os.sep)[:-1])

	# start import
	reportout("Importing: %s" % specFile)

	# get time range and mass range
	if options['timerange']:
		t1 = options['timerange'][0] / 60
		t2 = options['timerange'][1] / 60

	if options['pisSpectra']:
		msm1 = options['MSMSmassrange'][0]
		msm2 = options['MSMSmassrange'][1]
	else:
		msm1 = options['MSmassrange'][0]
		msm2 = options['MSmassrange'][1]

	if options['MSMSmassrange']:
		msmsm1 = options['MSMSmassrange'][0]
		msmsm2 = options['MSMSmassrange'][1]

	# for MS/MS collection of spectra attributes
	polarity = ''

	# read the mz file
	mz_file = mzFile(specFile)

	#if Debug("logMemory"):
	#	print "ML> raw file loaded:", memory_logging.pythonMemory()
	#	print "MLh> ", hpy().heap()

	try:
		mz_file.time_range()
	except:
		raise LipidXException("Problems with the spectrum file %s." % specFile)


	# get MS1 scans
	ms1_scan_nb = [sn for t, mz, sn, st, sm, pol, tic \
			in mz_file.scan_info(t1, t2, msm1, msm2) if st == 'MS1']

	# get averaged label data
	#spectrum = mz_file.ascan(ms1_scan_nb)
	spectrum = mz_file.ascan([12, 23])

	# get base peak intensity
	basePeakIntensity = 0
	for i in spectrum:
		print("%.4f,%.1f" % (i[0], i[1]))
		if i[1] > basePeakIntensity:
			basePeakIntensity = i[1]

	# get MS1 scans
	get_ms1Scans = [(t, mz, sn, sm, pol, tic) for t, mz, sn, st, sm, pol, tic \
			in mz_file.scan_info(t1, t2, msm1, msm2) if st == 'MS1']

	listTotIonCurrent = []
	ms1Scans = []
	for t, mz, sn, sm, pol, tic in get_ms1Scans:

		# check for polarity switches which are not allowed right now
		if polarity != '':
			if pol != polarity:
				raise LipidXException(
					"It is not allowed to have both polarities within" \
						+ " one file")
		else:
			polarity = pol

		ms1Scans.append({
			'time' : t,
			'totIonCurrent' : tic,
			'polarity' : pol,
			'max_it' : basePeakIntensity,
			'scan' : None})

		listTotIonCurrent.append(float(tic))

		nb_ms_scans += 1

	nb_ms_peaks = len(spectrum)

	#if Debug("logMemory"):
	#	print "ML> MS scans read from raw file:", memory_logging.pythonMemory()
	#	print "MLh> ", hpy().heap()

	# get MS2 scans
	get_ms2Scans = [(t, mz, sn, sm, pol, tic) for t, mz, sn, st, sm, pol, tic \
			in mz_file.scan_info(t1, t2, msm1, msm2) if st == 'MS2']

	ms2Scans = []
	for t, precursor, sn, sm, pol, tic in get_ms2Scans:

		# check for polarity switches which are not allowed right now
		if polarity != '':
			if pol != polarity:
				raise LipidXException(
					"It is not allowed to have both polarities within" \
						+ " one file")
		else:
			polarity = pol

		scan = mz_file.scan(scan_id=sn, time=t)

		# don't consider empty scans
		if len(scan) == 0:
			continue

		nb_msms_scans += 1

		# filter for MS/MS mass range and relative intensity
		scan_processed = []
		max_it = max([mz_value for (mz_value, it_value, res, bl, ns, cg) in scan])
		for mz2, it2, res, bl, ns, cg in scan:
			if msmsm1 <= mz2 <= msmsm2:
				scan_processed.append((mz2, it2, it2 / max_it, res, bl, ns, cg))
				nb_msms_peaks += 1

		ms2Scans.append({
			'time' : t,
			'totIonCurrent' : tic,
			'polarity' : pol,
			'precursorMz' : precursor,
			'max_it' : max_it,
			'scan' : scan_processed})


	#if Debug("logMemory"):
	#	print "ML> MS/MS scans read from raw file:", memory_logging.pythonMemory()
	#	print "MLh> ", hpy().heap()

	# put the m/z values into specEntry data structure
	# for the alignment function
	if polarity == '-':
		p = -1
	elif polarity == '+':
		p = 1
	else:
		raise LipidXException("Something is wrong with the polarity")

	# close the mz_file
	mz_file.close()

	# generate Sample
	lpdxSample = Sample(
				sampleName = specName,
				sourceDir = directory,
				sourceFile = specFile,
				polarity = p,
				options = options)
				#MSMSresolution = options['MSMSresolution'],
				#MSthreshold = options['MSthreshold'])

	# for getting only the stats, I set ms1scans and ms2scan to zero
	ms1Scans == []
	ms2Scans == []

	numPeaks = -1

	# maybe there is only one polarity
	if len(ms1Scans) > 0:

		###########################################
		### store the MS1 spectra in lpdxSample ###

		# get the threshold
		if options['MSthresholdType'] == 'absolute':
			thrshld_absolute = float(options['MSthreshold']) / sqrt(len(ms1Scans))
		else:
			thrshld_relative = float(options['MSthreshold']) / sqrt(len(ms1Scans))

		# for my interest
		numPeaks = 0

		# store the averaged spectrum
		for peak in spectrum:

			### store the averaged spectra in lpdxSample ###
			takeIt = False
			if options['MSthresholdType'] == 'absolute':
				if peak[1] >= thrshld_absolute:
					takeIt = True
			else:
				if peak[1] / basePeakIntensity >= thrshld_relative:
					takeIt = True

			if takeIt:
				numPeaks += 1
				lpdxSample.listPrecurmass.append(
					MSMass(
						precurmass = peak[0],
						intensity = peak[1],
						smpl = specName,
						polarity = p,
						charge = None,
						fileName = specFile,
						scanCount = len(ms1Scans),
						basePeakIntensity = basePeakIntensity))

		try:
			lpdxSample.base_peak_ms1 = max([x.intensity for x in lpdxSample.listPrecurmass])
		except ValueError:
			pass

		### store the MS1 spectra in lpdxSample ###
		###########################################


	###########################################
	### store the MS2 spectra in lpdxSample ###

	# get the threshold
	if options['MSMSthresholdType'] == 'absolute':
		thrshld_absolute = float(options['MSMSthreshold'])
	else:
		thrshld_relative = float(options['MSMSthreshold'])

	# maybe there is no MS/MS?
	if len(ms2Scans) > 0:
		for ms2scan_entry in sorted(ms2Scans,
				cmp = lambda x,y : cmp(x['precursorMz'], y['precursorMz'])):
			if ms2scan_entry['scan'] != []:

				# add the fragment mass to the fragment spectrum
				lpdxSample.listMsms.append(MSMS(
					ms2scan_entry['precursorMz'],
					charge = None,
					polarity = p,
					fileName = specFile,
					scanNumber = None,
					retentionTime = ms2scan_entry['time'],
					peaksCount = None,
					totIonCurrent = ms2scan_entry['totIonCurrent'],
					basePeakMz = None,
					basePeakIntensity = ms2scan_entry['max_it'],
					threshold = options['MSMSthreshold']))

				#lpdxSample.listMsms[-1].entries = ms2scan_entry['scan']
				for mz, it, it_rel, res, bl, ns, cg in ms2scan_entry['scan']:
					if it > 0.0:
						lpdxSample.listMsms[-1].entries.append((mz, it, it_rel, res, bl, ns, cg))

	# if there was no MS/MS, take the survey m/z from the precursor masses
	if lpdxSample.listPrecurmass == []:
		set_PrecurmassFromMSMS(lpdxSample, chg = p)

	sc.dictSamples[specName] = lpdxSample
	sc.listSamples.append(specName)

	### calc the TIC scores ###
	listTotIonCurrent.sort()
	num = 0
	if len(listTotIonCurrent) < 5:
		pass
	elif len(listTotIonCurrent) < 20:
		del listTotIonCurrent[0]
		del listTotIonCurrent[-1]
	elif len(listTotIonCurrent) < 50:
		num = int((len(listTotIonCurrent) / 100) * 10)
		for i in range(num):
			del listTotIonCurrent[0]
			del listTotIonCurrent[-1]
	else:
		num = int((len(listTotIonCurrent) / 100) * 5)
		for i in range(num):
			del listTotIonCurrent[0]
			del listTotIonCurrent[-1]

	median = numpy.median(listTotIonCurrent)

	reportout("> {0:.<30s}{1:>11d}".format('Nb. of MS scans', nb_ms_scans))
	reportout("> {0:.<30s}{1:>11d}".format('Nb. of MS peaks', nb_ms_peaks))
	reportout("> {0:.<30s}{1:>11d}".format('Nb. of MS/MS scans', nb_msms_scans))
	reportout("> {0:.<30s}{1:>11d}".format('Nb. of MS/MS peaks', nb_msms_peaks))
	reportout("> {0:.<30s}{1:>11d}".format('Nb. of MS peaks (after avg.)', numPeaks))
	reportout("> Spray stability:")
	if listTotIonCurrent != []:
		reportout("> {0:.<30s}{1:>11.2f}% of median".format('  MaxTIC - MinTIC:', (100 * (float(max(listTotIonCurrent)) - float(min(listTotIonCurrent))) / float(median))))
	reportout("")

	### End total ion count ###
	return (specName, lpdxSample.base_peak_ms1, nb_ms_scans, nb_ms_peaks, nb_msms_scans, nb_msms_peaks)

def add_mzXMLSample(sc, sample, strName, timerange = None, MSmassrange = None, MSMSmassrange = None, scanAveraging = None, isGroup = None, importMSMS = True, MSthresholdType = None, MSMSthresholdType = None):
	"""Adds a sample to the Survey Scan.
	IN: <the path of the sample
directory>, <the resolution of the mass spec machine>
	"""

	options = sc.options
	specFile = sample

	# is the given file a hidden Directory?
	s = specFile.split(os.sep)
	for i in s:
		if re.match('(^\.\w+).*', i):
			raise LipidXException("The given path %s is not " +\
					"accepted by LipidXplorer." % specFile)
	specName = s[-1]

	directory = os.sep.join(sample.split(os.sep)[:-1])

	if not isGroup:
		strName = s[-1]
	else:
		strName = s[-2] + '.' + s[-1]
	reportout("Importing: %s" % strName)

	numPeaks = -1  # init numPeaks to have it even if there are no ms1Scans

	if timerange:
		t1 = timerange[0]
		t2 = timerange[1]

	if MSmassrange:
		msm1 = MSmassrange[0]
		msm2 = MSmassrange[1]

	if MSMSmassrange:
		msmsm1 = MSMSmassrange[0]
		msmsm2 = MSMSmassrange[1]

	global fadi_percentageMSMS
	fadi_percentageMSMS = options['MSMSfilter']

	### let's start ###

	smpl = list(PrecursorSort(MzXMLFileReader(sample)))

	# for MS spectra collection and collection of spectra attributes
	unprocessed_info = []

	# for MS/MS collection of spectra attributes
	msms_info = []


	### for statistics ###

	nb_ms_scans = 0
	nb_ms_peaks = 0
	nb_msms_scans = 0
	nb_msms_peaks = 0


	### read the *.mzXML file and store the scans in ms[12]Scans ###

	ms1Scans = []
	ms2Scans = []
	polarity = ''

	count = 0
	countMSMS = 0
	listTotIonCurrent = []
	listRetTime = []
	for entry in smpl:

		if entry.get('centroided') == 0:
			raise LipidXException("Spectra in profile mode format. This is not allowed." +\
					" The spectra must be in centroided format.")

		# if spectrum is in time range
		if (not timerange) or (float(entry.get('retentionTime')) >= t1 and float(entry.get('retentionTime')) <= t2):

			peakList = []

			# if entry is a MS/MS spectrum
			if (entry.get('msLevel') == 2 and importMSMS) or (entry.get('msLevel') == 0 and options['pisSpectra']):

				# precursor mass is there
				if entry.get('precursorMz', None) and\
					entry.get('precursorMz') >= msm1 and\
					entry.get('precursorMz') <= msm2:

					precursor = entry.get('precursorMz')

					max_it = max(entry.it_)
					for (mz, it) in zip(entry.mz_, entry.it_):
						if mz >= msmsm1 and mz <= msmsm2:
							if it > 0.0:
								peakList.append((mz, it, it / max_it, 0, 0, 0, 0))


					if polarity != '':
						if polarity != entry.get('polarity', None):
							raise LipidXException("Having different polarities in one" +\
								" MasterScan is not allowed.")
					else:
						polarity = entry.get('polarity', None)

					t = entry.get('retentionTime', None)
					tic = entry.get('totIonCurrent', None)

					if len(peakList) > 0:
						ms2Scans.append({
							'time' : t,
							'totIonCurrent' : tic,
							'polarity' : polarity,
							'precursorMz' : precursor,
							'max_it' : max_it,
							'scan' : peakList})
						nb_msms_scans += 1
						countMSMS += 1

					# for the information output
					info = {}
					info['charge'] = entry.get('precursorCharge', None)
					info['scanNumber'] = entry.get('num', None)
					info['peaksCount'] = entry.get('peaksCount', None)
					info['retentionTime'] = entry.get('retentionTime', None)
					info['totIonCurrent'] = entry.get('totIonCurrent', None)
					info['basePeakMz'] = entry.get('basePeakMz', None)
					info['basePeakIntensity'] = entry.get('basePeakIntensity', None)

				# no precursor mass given
				elif not entry.get('precursorMz', None):
					raise LipidXException("The MS/MS spectra have no precursor mass")
					exit (-1)

			elif entry.get('msLevel') == 1:

				listTotIonCurrent.append(entry.get('totIonCurrent', None))
				listRetTime.append(entry.get('retentionTime'))

				info = {}
				info['scanNumber'] = entry.get('num', None)
				info['peaksCount'] = entry.get('peaksCount', None)
				info['retentionTime'] = entry.get('retentionTime', None)
				info['totIonCurrent'] = entry.get('totIonCurrent', None)
				info['basePeakMz'] = entry.get('basePeakMz', None)
				info['basePeakIntensity'] = entry.get('basePeakIntensity', None)

				unprocessed_info.append(info)

				max_it = max(entry.it_)
				for (mz, it) in zip(entry.mz_, entry.it_):
					# if mass is in mass range
					if mz >= msm1 and mz <= msm2 and it > 0:
						peakList.append((mz, it, it / max_it, 0, 0, 0, 0))

				if polarity != '':
					if polarity != entry.get('polarity', None):
						raise LipidXException("Having different polarities in one" +\
							" MasterScan is not allowed.")
				else:
					polarity = entry.get('polarity', None)

				if len(peakList) > 0:
					ms1Scans.append({
						'time' : entry.get('retentionTime'),
						'totIonCurrent' : entry.get('totIonCurrent'),
						'polarity' : entry.get('polarity'),
						'max_it' : max_it,
						'scan' : peakList})
					nb_ms_scans += 1
					count += 1
					## for Kai: read out single scan masses and TIC
					#tolerance = 0.25
					#for mass in [806.55, 774.56, 761.43, 622.26]:
					#
					#	if mz <= mass + tolerance and mz >= mass - tolerance:
					#		f = open("%s\mass-%.2f-%s.txt" % (directory, mass, strName.split('.')[0]), "a")
					#		str = "%d, %.4f, %.4f, %d\n" % (scanNumber, mz, it, totIonCurrent)
					#		f.write(str)
					#		f.close()
					#		#print "%s\mass-%.2f-%s.txt" % (sample[:-1], mass, strName)

				## read out TIC
				#f = open("%s\\tic-%s.txt" % (directory, strName.split('.')[0]), "a")
				#str = "%d, %d\n" % (scanNumber, totIonCurrent)
				#f.write(str)
				#f.close()




	del smpl

	# put the m/z values into specEntry data structure
	# for the alignment function

	if polarity == '-':
		p = -1
	else:
		p = 1


	### mk an emtpy Sample ###

	lpdxSample = Sample(
				sampleName = specName,
				sourceDir = directory,
				sourceFile = specFile,
				polarity = p,
				options = sc.options)
				#MSMSresolution = sc.options['MSMSresolution'],
				#MSthreshold = sc.options['MSthreshold'])


	### store the MS2 spectra in lpdxSample ###

	# get the threshold
	if options['MSMSthresholdType'] == 'absolute':
		thrshld_absolute = float(options['MSMSthreshold'])
	else:
		thrshld_relative = float(options['MSMSthreshold'])

	# maybe there is no MS/MS?
	if len(ms2Scans) > 0:
		for ms2scan_entry in sorted(ms2Scans,
				cmp = lambda x,y : cmp(x['precursorMz'], y['precursorMz'])):
			if ms2scan_entry['scan'] != []:

				# add the fragment mass to the fragment spectrum
				lpdxSample.listMsms.append(MSMS(
					ms2scan_entry['precursorMz'],
					charge = None,
					polarity = p,
					fileName = specFile,
					scanNumber = None,
					retentionTime = ms2scan_entry['time'],
					peaksCount = None,
					totIonCurrent = ms2scan_entry['totIonCurrent'],
					basePeakMz = None,
					basePeakIntensity = ms2scan_entry['max_it'],
					threshold = options['MSMSthreshold']))

				lpdxSample.listMsms[-1].entries = ms2scan_entry['scan']
				nb_msms_peaks += len(ms2scan_entry['scan'])
				#for mz, it, it_rel, res, bl, ns, cg in ms2scan_entry['scan']:
				#	lpdxSample.listMsms[-1].entries.append((mz, it, it_rel, res, bl, ns, cg))


	### averaging of the MS1 scans ###

	if len(ms1Scans) > 0:

		nb_ms_peaks = 0
		avgBasePeakIntensity = 0
		count = 0
		dictSpecEntry = {}
		for ms1scan_entry in ms1Scans:

			dictSpecEntry[repr(count)] = []
			for mz, it, it_rel, res, bl, ns, cg in ms1scan_entry['scan']:
				if it > 0.0 and it_rel > 0.0:
					dictSpecEntry[repr(count)].append(specEntry(
						mass = mz,
						content = {'sample' : repr(count),
							'intensity' : it,
							'intensity_rel' : it_rel}))
					nb_ms_peaks += 1
			avgBasePeakIntensity += ms1scan_entry['max_it']
			count += 1

		if scanAveraging == 'linear':
			fadi_denominator = count
			fadi_percentage = options['MSfilter']
			listClusters = linearAlignment(list(dictSpecEntry.keys()),
								dictSpecEntry,
								options['MSresolution'],
								merge = mergeSumIntensity,
								mergeTolerance = options['MSresolution'],
								mergeDeltaRes = options['MSresolutionDelta'],
								fadi_denominator = fadi_denominator, fadi_percentage=fadi_percentage)

		elif scanAveraging == 'heuristic':
			listClusters = heuristicAlignment(list(dictSpecEntry.keys()),
								dictSpecEntry,
								options['MSresolution'],
								merge = mergeSumIntensity,
								mergeTolerance = options['MSresolution'],
								mergeDeltaRes = options['MSresolutionDelta'])

		if (Debug("scanclusters")):
			# for debugging
			strings = []
			for cl in listClusters:
				str = ''
				for sample in list(dictSpecEntry.keys()):#cl.keys():
					if sample in cl:
						if cl[sample].content:
							str +=  "  {0:>9.4f} - {1:>12.1f}  ".format(cl[sample].mass, cl[sample].content['intensity'])
							#str +=  "  %.4f  " % cl[sample].content['intensity']
						else:
							try:
								str +=  " /{0:>9.4f} - {1:>12}/ ".format(cl[sample].mass, '')
							except TypeError:
								print("TypeError:", cl[sample].mass)
							except :
								import sys
								print((sys.exc_info()[0]))
					else:
						str +=  " /{0:>9} - {1:>12}/ ".format('empty', '')
				strings.append(str)

			print(('\n'.join(strings)))


		### averaging of the MS1 scans ###
		##################################


		###########################################
		### store the MS1 spectra in lpdxSample ###

		# get the threshold
		if len(ms1Scans) > 0:
			if options['MSthresholdType'] == 'absolute':
				thrshld_absolute = float(options['MSthreshold']) / sqrt(len(ms1Scans))
			else:
				thrshld_relative = float(options['MSthreshold']) / sqrt(len(ms1Scans))
		else:
			thrshld_absolute = float(options['MSthreshold'])
			thrshld_relative = float(options['MSthreshold'])

		# get the keys for the individual scans
		keys = [repr(n) for n in range(count)]

		# get the average base peak intensity
		avgBasePeakIntensity = avgBasePeakIntensity / float(count)
		numPeaks = 0
		# store the averaged spectrum
		for cl in listClusters:

			sumMass = 0
			sumMassIntensity = 0
			sumIntensity = 0
			sumIntensity_relative = 0

			for sample in list(dictSpecEntry.keys()):
				if sample in cl and cl[sample].content != {}:
					sumMass += cl[sample].mass
					sumMassIntensity += cl[sample].mass * cl[sample].content['intensity']
					sumIntensity += cl[sample].content['intensity']
					if 'intensity_rel' in cl[sample].content:
						sumIntensity_relative += cl[sample].content['intensity_rel']

			out = specEntry(
				mass = sumMassIntensity / sumIntensity,
				content = {})

			out.content['intensity'] = sumIntensity / len(keys) # divide by the total number of scan
			out.content['intensity_rel'] = sumIntensity_relative / len(keys)


			### store the averaged spectra in lpdxSample ###

			takeIt = False
			if options['MSthresholdType'] == 'absolute':
				if out.content['intensity'] >= thrshld_absolute:
					takeIt = True
			else:
				if out.content['intensity_rel'] >= thrshld_relative:
					takeIt = True

			if takeIt:
				numPeaks += 1
				lpdxSample.listPrecurmass.append(
					MSMass(
						precurmass = out.mass,
						intensity = out.content['intensity'],
						smpl = specName,
						polarity = p,
						charge = None,
						fileName = specFile,
						scanCount = count,
						basePeakIntensity = avgBasePeakIntensity))

		try:
			lpdxSample.base_peak_ms1 = max([x.intensity for x in lpdxSample.listPrecurmass])
		except ValueError:
			pass

		### store the MS1 spectra in lpdxSample ###
		###########################################


	### calc the TIC scores ###

	listTotIonCurrent.sort()
	num = 0
	if len(listTotIonCurrent) < 5:
		pass
	elif len(listTotIonCurrent) < 20:
		del listTotIonCurrent[0]
		del listTotIonCurrent[-1]
	elif len(listTotIonCurrent) < 50:
		num = int((len(listTotIonCurrent) / 100) * 10)
		for i in range(num):
			del listTotIonCurrent[0]
			del listTotIonCurrent[-1]
	else:
		num = int((len(listTotIonCurrent) / 100) * 5)
		for i in range(num):
			del listTotIonCurrent[0]
			del listTotIonCurrent[-1]

	median = numpy.median(listTotIonCurrent)

	### End total ion count ###


	### make average of info values ###

	if len(unprocessed_info) > 1:

		# MS
		sumPeaksCount = 0
		sumTotIonCurrent = 0
		sumBasePeakIntensity = 0
		for index in range(len(unprocessed_info)):
			sumPeaksCount += unprocessed_info[index]['peaksCount']
			sumTotIonCurrent += unprocessed_info[index]['totIonCurrent']
			sumBasePeakIntensity += unprocessed_info[index]['basePeakIntensity']

		avgPeaksCount = sumPeaksCount / len(unprocessed_info)
		avgTotIonCurrent = sumTotIonCurrent / len(unprocessed_info)
		avgBasePeakIntensity = sumBasePeakIntensity / len(unprocessed_info)

	else:
		avgBasePeakIntensity = 0

	# MS/MS
	if len(msms_info) > 0:
		sumBasePeakIntensity_MSMS = 0
		for index in range(len(msms_info)):
			sumBasePeakIntensity_MSMS += msms_info[index]['basePeakIntensity']

		avgBasePeakIntensity_MSMS = sumBasePeakIntensity_MSMS / len(msms_info)

	else:
		avgBasePeakIntensity_MSMS = 0

	# no spectra given
	if len(unprocessed_info) < 1 and lpdxSample.listMsms == []:
		raise LipidXException("Could not find any MS spectrum with the given settings."\
				+ " In particular, check the time range setting.")

	# prepare threshold value
	if sc.options['MSthresholdType'] == 'relative':
		thrshld = ((float(sc.options['MSthreshold'] / 100)) * avgBasePeakIntensity)
		#MSthresholdValues[strName] = ((float(sc.options['MSthreshold'] / 100)) * avgBasePeakIntensity) / sqrt(count)

	else:
		# be aware that there could be no MS1 spectra
		if len(ms1Scans) > 0:
			thrshld = float(sc.options['MSthreshold']) / sqrt(count)
		else:
			thrshld = float(sc.options['MSthreshold'])

	####################################
	### start averaging of the scans ###
	####################################

	lpdxSample.polarity = p

	# print the spectra attributes
	# count = nb_ms_scans
	reportout("> {0:.<30s}{1:>11d}".format('Nb. of MS scans', nb_ms_scans))
	reportout("> {0:.<30s}{1:>11d}".format('Nb. of MS peaks', nb_ms_peaks))
	# countMSMS = nb_msms_scans
	reportout("> {0:.<30s}{1:>11d}".format('Nb. of MS/MS scans', nb_msms_scans))
	reportout("> {0:.<30s}{1:>11d}".format('Nb. of MS/MS peaks', nb_msms_peaks))
	reportout("> {0:.<30s}{1:>11d}".format('Nb. of MS peaks (after avg.)', numPeaks))
	reportout("Spray stability:")
	if listTotIonCurrent != []:
		reportout("{0:.<30s}{1:>11.2f}% of median\n".format('  MaxTIC - MinTIC:', (100 * (float(max(listTotIonCurrent)) - float(min(listTotIonCurrent))) / float(median))))


	# get MS masses from MS/MS spectra, if no MS spectrum was present
	if len(ms1Scans) == 0:
		r = set_PrecurmassFromMSMS(lpdxSample)
		if r != 0:
			raise LipidXException(
					"Empty file '%s'. No MS or MS/MS spectra present in the file or the time range settings are wrong!" % strName)

	sc.dictSamples[strName] = lpdxSample
	sc.listSamples.append(strName)

	# to save memory... actually it does nothing because of Python GC
	del lpdxSample

	return (strName, avgBasePeakIntensity, count, nb_ms_peaks, countMSMS, nb_msms_peaks)

def add_DTASample(sc, sampleDir, sampleName, MSmassrange = None, MSMSmassrange = None, importMSMS = True, thresholdType = None):
	"""Add a sample to the Sample class. It reads the scans from the given *.mzXML files,
	does the averaging and stores it in the Sample class.
	"""

	# sample: path to dest directory (<bla>/destDir)
	# strName: name of the dest directory (destDir)

	if sampleDir != "":
		if re.compile('.*\%sneg_.*$' % (os.sep)).match(sampleDir): polarity = -1
		else: polarity = 1
	else:
		polarity = None

	reportout("Importing %s" % sampleName)

	reportout("Polarity or sample %s: %s" % (sampleDir, polarity))

	strName = sampleName
	strSampleDir = sampleDir

	# merge all precurmasses
	lpdxSample = Sample(
			sampleName = strName,
			sourceDir = strSampleDir,
			sourceFile = strSampleDir,
			polarity = polarity,
			options = sc.options)
			#MSMSresolution = sc.options['MSMSresolution'],
			#MSthreshold = sc.options['MSthreshold'])

	csv = ""
	dta = False

	mdta = re.compile(".*\.dta")
	mcsv = re.compile(".*\.csv")

	if MSmassrange:
		#msm1 = float(re.match("\(\s*(\d+\.?\d+)\s*,\s*(\d+\.?\d+)\s*\)", MSmassrange).group(1))
		#msm2 = float(re.match("\(\s*(\d+\.?\d+)\s*,\s*(\d+\.?\d+)\s*\)", MSmassrange).group(2))
		msm1 = MSmassrange[0]
		msm2 = MSmassrange[1]

	if MSMSmassrange:
		#msmsm1 = float(re.match("\(\s*(\d+\.?\d+)\s*,\s*(\d+\.?\d+)\s*\)", MSMSmassrange).group(1))
		#msmsm2 = float(re.match("\(\s*(\d+\.?\d+)\s*,\s*(\d+\.?\d+)\s*\)", MSMSmassrange).group(2))
		msms1 = MSMSmassrange[0]
		msms2 = MSMSmassrange[1]

	for root, dirs, files in os.walk(sampleDir):
		if root == sampleDir:
			if files == []:
				LipidXException("The directory \"" + root + "\" is empty")

			for namef in files:

				# sort out hidden files
				if not (re.match('(^\.\w+).*|.*(\\\.)|(\/\.).*', namef)) and \
						(len(namef.split(os.sep)) <= 1):

					if mdta.match(namef):
						dta = True
					if mcsv.match(namef):
						csv = root + os.sep + namef


#					lpdxTools.log("loading %s from %s" % (name, root))

#			if csv != "" and dta:
#				sampleDir = (csv, root)
#			elif dta:
#				sampleDir = ("", root)
#			elif csv != "":
#				sampleDir = (csv, "")

#			csv = ""
#			dta = False

			# unpack experiment
			dirmsms = sampleDir

			basePeakIntensity = None

			# TODO : insert Massranges ###
			# if only a container with .dta files is given
			if dirmsms != "" and csv == "" and dta and importMSMS:
				loadMSMS(lpdxSample, dirmsms, sc.options['MSMSresolution'], sc.options)
				set_PrecurmassFromMSMS(lpdxSample)

			# if both - .dta and .csv - are given
			elif dirmsms != "" and csv != "" and dta and importMSMS:
				loadMSMS(lpdxSample, dirmsms, sc.options['MSMSresolution'], sc.options)
				basePeakIntensity = lpdxSample.fillTable(lpdxSample.openAndRead(csv), sampleName, sampleDir, sc.options['MSthreshold'], thresholdType)

			# if both - .dta and .csv - are given, but importMSMS ('MS only') is False
			elif dirmsms != "" and csv != "" and dta and not importMSMS:
				basePeakIntensity = lpdxSample.fillTable(lpdxSample.openAndRead(csv), sampleName, sampleDir, sc.options['MSthreshold'], thresholdType)

			# if only *.csv is given
			elif csv != "" and not dta:
				basePeakIntensity = lpdxSample.fillTable(lpdxSample.openAndRead(csv), sampleName, sampleDir, sc.options['MSthreshold'], thresholdType)

			else:
				raise LipidXException("There are problems with your spectra files. Please check if they" +\
						"follow the right format as specified in the LipidXplorer documentation under" +\
						"'LipidXplorer import'")

	sc.dictSamples[sampleName] = deepcopy(doClusterSample(sc.options['MSresolution'], (doClusterSample(sc.options['MSresolution'], lpdxSample))))
	sc.listSamples.append(sampleName)

	num_peaks = len(sc.dictSamples[sampleName].listPrecurmass)

	del lpdxSample
	return (polarity, basePeakIntensity, sampleName, num_peaks)


# dta specific functions
def loadMSMS(sample, dirmsms, resolution, options):
	"""Loads all .dta files as MSMS's. Be careful: the path variable is case sensitive!
	and of the form name.csv. Input is the filename (with or without .csv) and output
	is filled in sample.listMsms and sample.msmsMasses."""

	import os
	dtalist = []

	# get list of all .dta files
	fn1 = dirmsms.split('.')
	if fn1[0].split(os.sep)[-1] == '':

		# set name of the sample directory
		sample.sampleName = fn1[0].split(os.sep)[-2]

		fn2 = fn1[0].split(os.sep)[-2]
		fnp = ""
		for i in fn1[0].split(os.sep)[:-2]:
			fnp = fnp + i + os.sep
	else:

		# set name of the sample directory
		sample.sampleName = fn1[0].split(os.sep)[-1]

		fn2 = fn1[0].split(os.sep)[-1]
		fnp = ""
		for i in fn1[0].split(os.sep)[:-1]:
			fnp = fnp + i + os.sep

	# load all .dta files
	files = glob(fnp + "%s/*.dta" % fn2)
	if files == []:
		raise "No .dta files in directory ", i

	dtalist = dtalist + files

	count = 0
	for i in dtalist:
		# open file, read
		with open(i, "r") as f:
			l = f.readlines()

		count += 1

		# generate MSMS and append it to sample.listMsms
		#n1, n2 = l[0].split(' |\t')
		n1, xxx, n2 = regDta.match(l[0]).groups()

		# beware of the charge which is given in the dta
		# if option 'fixedcharge' is set the recalculate every entry

		if int(n2) > 0:
			polarity = 1
		else:
			polarity = -1

		### 'forcesinglecharge' is depricated
		#if options.has_key('forcesinglecharge') and options['forcesinglecharge'] != 0 and int(n2) > 1:
		#	n1 = (float(n1) + ((int(n2) - 1) * 1.0078)) / abs(int(n2))

		#elif options.has_key('forcesinglecharge')  and options['forcesinglecharge'] != 0 and int(n2) < -1:
		#	n1 = (float(n1) - (abs(int(n2)) - 1) * 1.0078) / abs(int(n2))

		for j in l[1:]:
			if not re.match('^#.*', j):
				if float(j[1]) < float(options['MSMSthreshold']):
					del j

		sample.listMsms.append(MSMS(
					mass = n1,
					retentionTime = None,
					charge = int(n2),
					polarity = polarity,
					table = l[1:],
					fileName = i,
					MSMSthreshold = options['MSMSthreshold']))

	print("Number of *.dta files:", count)

	sample.listMsms.sort()

	lpdxClusterMSMS(sample, resolution)

def set_PrecurmassFromMSMS(sample, chg = None):
	"""Get list of precurmasses from msms .dta files, the sample.msms must
	be given."""
	if sample.listMsms != []:
		for i in sample.listMsms:

			if chg and i.precurmass:
				isIn = False
				for p in sample.listPrecurmass:
					if i.precurmass == p.precurmass:
						isIn = True

				if not isIn:
					sample.listPrecurmass.append(MSMass(
						precurmass = i.precurmass,
						intensity = 1,
						polarity = chg,
						charge = i.charge,
						smpl = sample.sampleName,
						fileName = i.fileName,
						scanCount = i.scanCount,
						basePeakIntensity = None))

			elif hasattr(i, 'charge'):

				if i.charge > 0: p = 1
				else: p = -1

				sample.listPrecurmass.append(MSMass(
					precurmass = i.precurmass,
					intensity = 1,
					polarity = p,
					charge = i.charge,
					smpl = sample.sampleName,
					fileName = i.fileName,
					scanCount = i.scanCount,
					basePeakIntensity = None))

			else:

				if i.polarity == '+': c = 1
				else: c = -1

				sample.listPrecurmass.append(MSMass(
					precurmass = i.precurmass,
					intensity = 1,
					polarity = i.polarity,
					charge = c,
					smpl = sample.sampleName,
					fileName = i.fileName,
					scanCount = i.scanCount,
					basePeakIntensity = None))

		# everything is ok
		return 0

	else:
		# error: no MS/MS experiments present
		return -1
