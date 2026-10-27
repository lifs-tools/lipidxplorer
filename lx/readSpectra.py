import os, re, numpy
from copy import deepcopy
from math import sqrt
from glob import glob
import csv
from lx.fileReader.mzAPI import mzFile
from lx.alignment import specEntry, linearAlignment, mergeSumIntensity, doClusterSample, lpdxClusterMSMS
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
regDta = re.compile(r"(\d+\.?\d*)(\s|\t)+([-]?\d+\.?\d*)")

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
		if re.match(r'(^\.\w+).*', i):
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
		reportout("Limiting timerange from %f to %f (sec), %f to %f (min)" % (options['timerange'][0], options['timerange'][1], t1, t2))

	# if options['pisSpectra']:
	# 	msm1 = options['MSMSmassrange'][0]
	# 	msm2 = options['MSMSmassrange'][1]
	# else:
	# 	msm1 = options['MSmassrange'][0]
	# 	msm2 = options['MSmassrange'][1]
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
		
		#print("MSthreshold", options['MSthreshold'], "thrshld_relative", thrshld_relative)

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

			#print("Take it?", takeIt, thrshld_relative, out.content['intensity_rel'], out.content['intensity'])
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

		print("DEBUG kept averaged MS1 peaks:", numPeaks, "for", specFile)
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
		for ms2scan_entry in sorted(ms2Scans, key=lambda x: x['precursorMz']):
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



def add_CSVSample(
		sc=None,
		csvFile=None,
		specDir=None,
		options=None,
		**kwargs
	):
	"""
	Import new single CSV format.

	Expected columns:
		Function
		index
		m_z
		m_zNoCal
		rt
		Mobility [ms]
		Polarity
		QuadMass
		inten

	Rule:
		QuadMass == 0  -> MS1 peak
		QuadMass > 0   -> MS/MS fragment peak, QuadMass is precursor mass

	Mobility/RT are stored permanently in:
		sc.raw_peak_lookup[specName]

	Return shape matches add_Sample():
		(specName, base_peak_ms1, nb_ms_scans, nb_ms_peaks,
		nb_msms_scans, nb_msms_peaks)
	"""

	import csv as csvlib
	from collections import defaultdict

	def _to_float(value, default=None):
		try:
			if value is None:
				return default
			value = str(value).strip()
			if value == "":
				return default
			return float(value)
		except:
			return default

	def _to_int(value, default=None):
		try:
			if value is None:
				return default
			value = str(value).strip()
			if value == "":
				return default
			return int(float(value))
		except:
			return default

	def _polarity_to_int(value):
		if value is None:
			return None

		value = str(value).strip().lower()

		if value in ["pos", "positive", "+", "1", "esi+", "p"]:
			return 1

		if value in ["neg", "negative", "-", "-1", "esi-", "n"]:
			return -1

		return None

	if options is None:
		options = sc.options

	if csvFile is None or not os.path.isfile(csvFile):
		raise LipidXException("CSV file does not exist: %s" % csvFile)

	# Match normal importer style: sample name is filename.
	# If you want no extension in output, change this one line only.
	specName = os.path.basename(csvFile)

	if specDir is None:
		specDir = os.path.dirname(csvFile)

	reportout("Importing %s" % specName)

	# lxNext fix: optionsDict.get() RAISES LipidXException for a missing key instead of
	# returning the default, and Python evaluates a default ARGUMENT eagerly -- so the
	#     kwargs.get("importMSMS", options.get("importMSMS", True))
	# that used to stand here blew up whenever the options object lacked the key, even
	# when kwargs supplied it. That made this importer impossible to call.
	def _opt(name, default=None):
		if name in kwargs:
			return kwargs[name]
		try:
			return options[name]
		except Exception:
			return default

	MSmassrange = _opt("MSmassrange")
	MSMSmassrange = _opt("MSMSmassrange")
	importMSMS = _opt("importMSMS", True)
	MSthresholdType = _opt("MSthresholdType")
	MSMSthresholdType = _opt("MSMSthresholdType")

	global fadi_percentageMSMS
	fadi_percentageMSMS = options["MSMSfilter"]

	rows = []

	with open(csvFile, "r", newline="") as f:
		reader = csvlib.DictReader(f)

		required_columns = [
			"Function",
			"m_z",
			"rt",
			"Mobility [ms]",
			"Polarity",
			"QuadMass",
		]

		# lxNext fix: real exports spell the intensity column "Intensity"; only "inten"
		# used to be accepted, so those files were rejected outright.
		intensity_column = None
		for candidate in ("inten", "Intensity", "intensity"):
			if candidate in (reader.fieldnames or []):
				intensity_column = candidate
				break
		if intensity_column is None:
			raise LipidXException(
				"CSV file %s has no intensity column (inten / Intensity)" % csvFile
			)

		for col in required_columns:
			if col not in reader.fieldnames:
				raise LipidXException(
					"CSV file %s is missing required column: %s" % (csvFile, col)
				)

		for row in reader:
			# lxNext fix: keep only peaks the detector assigned an index to. Rows with
			# index = -1 are unassigned detections -- in a real export they are half the
			# file, disjoint from the assigned peaks and systematically weaker.
			try:
				if float(row.get("index", -1)) <= 0:
					continue
			except (TypeError, ValueError):
				continue
			rows.append(row)

	if rows == []:
		raise LipidXException("CSV file is empty: %s" % csvFile)

	if not hasattr(sc, "raw_peak_lookup"):
		sc.raw_peak_lookup = {}

	nb_ms_scans = 0
	nb_ms_peaks = 0
	nb_msms_scans = 0
	nb_msms_peaks = 0

	polarity = None
	for row in rows:
		polarity = _polarity_to_int(row.get("Polarity"))
		if polarity is not None:
			break

	if polarity is None:
		raise LipidXException("Could not determine polarity from CSV file: %s" % csvFile)

	lpdxSample = Sample(
		sampleName=specName,
		sourceDir=specDir,
		sourceFile=csvFile,
		polarity=polarity,
		options=options
	)

	lpdxSample.raw_peak_lookup = []

	# -----------------------------
	# Determine MS1 base peak
	# -----------------------------
	ms1_intensities = []

	for row in rows:
		quadmass = _to_float(row.get("QuadMass"), 0.0)
		intensity = _to_float(row.get(intensity_column), 0.0)

		if quadmass == 0.0 and intensity is not None:
			ms1_intensities.append(intensity)

	if ms1_intensities:
		basePeakIntensity = max(ms1_intensities)
		nb_ms_scans = 1
	else:
		basePeakIntensity = 0.0
		nb_ms_scans = 0

	# lxNext fix: this used to divide by 100, so the SAME MSthreshold meant a hundred
	# times smaller cut here than in the mzML importer (add_Sample, which compares
	# MSthreshold against the relative intensity directly). One settings file must not
	# mean two different things depending on the input format.
	if MSthresholdType == "relative":
		ms_threshold = float(options["MSthreshold"]) * basePeakIntensity
	else:
		ms_threshold = float(options["MSthreshold"])

	# Store MS2 rows by precursor mass.
	msms_rows = defaultdict(list)
	msms_meta = {}

	# -----------------------------
	# Read MS1 and MS2 rows
	# -----------------------------
	for row in rows:
		function_id = _to_int(row.get("Function"), None)
		index = _to_int(row.get("index"), None)

		mz = _to_float(row.get("m_z"), None)
		mz_no_cal = _to_float(row.get("m_zNoCal"), None)
		rt = _to_float(row.get("rt"), None)
		mobility = _to_float(row.get("Mobility [ms]"), None)
		pol = _polarity_to_int(row.get("Polarity"))
		quadmass = _to_float(row.get("QuadMass"), 0.0)
		intensity = _to_float(row.get(intensity_column), 0.0)

		if mz is None:
			continue

		if pol is None:
			pol = polarity

		if pol != polarity:
			raise LipidXException(
				"Mixed polarity inside one CSV file is not supported: %s" % csvFile
			)

		ms_level = "MS1" if quadmass == 0.0 else "MS2"

		lpdxSample.raw_peak_lookup.append({
			"sample": specName,
			"source_file": csvFile,
			"ms_level": ms_level,
			"function": function_id,
			"index": index,
			"mz": mz,
			"mz_no_cal": mz_no_cal,
			"rt": rt,
			"mobility": mobility,
			"polarity": pol,
			"quadmass": quadmass,
			"intensity": intensity
		})

		# -----------------------------
		# MS1
		# -----------------------------
		if quadmass == 0.0:

			if MSmassrange:
				if mz < MSmassrange[0] or mz > MSmassrange[1]:
					continue

			nb_ms_peaks += 1

			if intensity < ms_threshold:
				continue

			intensity_relative = 0.0
			if basePeakIntensity > 0:
				intensity_relative = intensity / basePeakIntensity

			lpdxSample.listPrecurmass.append(MSMass(
				precurmass=mz,
				intensity=intensity,
				smpl=specName,
				polarity=pol,
				charge=None,
				fileName=csvFile,
				scanCount=1,
				basePeakIntensity=basePeakIntensity,
				intensity_relative=intensity_relative
			))

		# -----------------------------
		# MS/MS
		# -----------------------------
		else:
			if not importMSMS:
				continue

			if MSMSmassrange:
				if mz < MSMSmassrange[0] or mz > MSMSmassrange[1]:
					continue

			if intensity <= 0.0:
				continue

			nb_msms_peaks += 1

			msms_rows[quadmass].append({
				"mz": mz,
				"intensity": intensity,
				"rt": rt,
				"polarity": pol,
				"function": function_id
			})

			if quadmass not in msms_meta:
				msms_meta[quadmass] = {
					"rt": rt,
					"polarity": pol,
					"function": function_id
				}

	# -----------------------------
	# Create MSMS objects manually
	# Do not use table=..., because MSMS.fillTable()
	# filters fragments immediately and behaves differently.
	# -----------------------------
	if importMSMS:
		for quadmass in sorted(msms_rows.keys()):

			fragment_rows = msms_rows[quadmass]
			if fragment_rows == []:
				continue

			max_frag_intensity = max([x["intensity"] for x in fragment_rows])
			meta = msms_meta.get(quadmass, {})

			msms = MSMS(
				quadmass,
				charge=None,
				polarity=meta.get("polarity", polarity),
				fileName=csvFile,
				scanNumber=None,
				retentionTime=meta.get("rt", None),
				peaksCount=len(fragment_rows),
				totIonCurrent=sum([x["intensity"] for x in fragment_rows]),
				basePeakMz=None,
				basePeakIntensity=max_frag_intensity,
				threshold=options["MSMSthreshold"]
			)

			for frag in fragment_rows:
				intensity_relative = 0.0
				if max_frag_intensity > 0:
					intensity_relative = frag["intensity"] / max_frag_intensity

				msms.entries.append([
					frag["mz"],
					frag["intensity"],
					intensity_relative,
					None,
					None,
					None,
					None
				])

			lpdxSample.listMsms.append(msms)

		nb_msms_scans = len(lpdxSample.listMsms)

		lpdxSample.listMsms.sort()

		if lpdxSample.listMsms != []:
			lpdxClusterMSMS(lpdxSample, options["MSMSresolution"])

	# If no MS1 exists, use MS2 precursor masses.
	if lpdxSample.listPrecurmass == []:
		r = set_PrecurmassFromMSMS(lpdxSample, chg=polarity)
		if r != 0:
			raise LipidXException(
				"Empty file '%s'. No MS or MS/MS spectra present." % specName
			)

	# Required by mkSurveyLinear/checkOccupation.
	if lpdxSample.listPrecurmass:
		lpdxSample.base_peak_ms1 = max([x.intensity for x in lpdxSample.listPrecurmass])
	else:
		lpdxSample.base_peak_ms1 = basePeakIntensity

	# Match add_DTASample behavior for CSV-like import:
	# cluster sample before adding to scan.
	sc.dictSamples[specName] = deepcopy(
		doClusterSample(
			options["MSresolution"],
			doClusterSample(options["MSresolution"], lpdxSample)
		)
	)

	sc.dictSamples[specName].base_peak_ms1 = lpdxSample.base_peak_ms1

	# Temporary copy, useful during import debugging.
	sc.dictSamples[specName].raw_peak_lookup = lpdxSample.raw_peak_lookup

	# Permanent copy; survives after scan.dictSamples is deleted in doImport().
	sc.raw_peak_lookup[specName] = lpdxSample.raw_peak_lookup

	sc.listSamples.append(specName)

	numPeaksAfterAvg = len(sc.dictSamples[specName].listPrecurmass)

	reportout("> {0:.<30s}{1:>11d}".format("Nb. of MS scans", nb_ms_scans))
	reportout("> {0:.<30s}{1:>11d}".format("Nb. of MS peaks", nb_ms_peaks))
	reportout("> {0:.<30s}{1:>11d}".format("Nb. of MS/MS scans", nb_msms_scans))
	reportout("> {0:.<30s}{1:>11d}".format("Nb. of MS/MS peaks", nb_msms_peaks))
	reportout("> {0:.<30s}{1:>11d}".format("Nb. of MS peaks (after avg.)", numPeaksAfterAvg))
	reportout("")

	del lpdxSample

	return (
		specName,
		sc.dictSamples[specName].base_peak_ms1,
		nb_ms_scans,
		nb_ms_peaks,
		nb_msms_scans,
		nb_msms_peaks
	)
	
	
	
	
	
	



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
		if re.match(r'(^\.\w+).*', i):
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
		reportout("Limiting timerange from %f to %f (sec), %f to %f (min)" % (options['timerange'][0], options['timerange'][1], t1, t2))

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
		for ms2scan_entry in sorted(ms2Scans, key=lambda x: x['precursorMz']):
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

def add_DTASample(sc, sampleDir, sampleName, MSmassrange = None, MSMSmassrange = None, importMSMS = True, thresholdType = None):
	"""Add a sample to the Sample class. It reads the scans from the given *.mzXML files,
	does the averaging and stores it in the Sample class.
	"""

	# sample: path to dest directory (<bla>/destDir)
	# strName: name of the dest directory (destDir)

	if sampleDir != "":
		if re.compile(r'.*\%sneg_.*$' % (os.sep)).match(sampleDir): polarity = -1
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

	mdta = re.compile(r".*\.dta")
	mcsv = re.compile(r".*\.csv")

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
				if not (re.match(r'(^\.\w+).*|.*(\\\.)|(\/\.).*', namef)) and \
						(len(namef.split(os.sep)) <= 1):

					if mdta.match(namef):
						dta = True
					if mcsv.match(namef):
						csv = root + os.sep + namef

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
		############## test ballal #############
				print("MSfilter in add_DTA ####################################:", sc.options['MSfilter'])
				print("MSMSfilter in add_DTA ####################################:", sc.options['MSMSfilter'])
	#############################
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
		raise Exception("No .dta files in directory ", i)

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
