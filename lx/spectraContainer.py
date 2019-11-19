import re, os, sys
from glob import glob
from math import sqrt
#from lx.alignment import doClusterMSMS
from lx.tools import sortDictKeys, log, reportout, dbgout
from lx.mfql.runtimeStatic import TypeTolerance
from lx.debugger import Debug
from lx.exceptions import LipidXException

# write a re match obj for the input line which should be:
# \d+\.\d+.*,.*\d+\.?\d*

numstart = re.compile("^\d+\.\d+\s*,\s*\d+\.?\d*.*")

#class Intensity(DictMixin):
#
#	def __init__(self):
#		self._int = {}
#		self._int_rel = {}
#		self._base_peak = {}
#
#	def __setitem__(self, key, value):
#		if isinstance(value, type(())):
#			if len(value) >= 2:
#				self._int[key] = value[0]
#				self._int_rel[key] = value[1]
#			if len(value) == 3:
#				self._base_peak[key] = value[2]
#		else:
#			self._int[key] = value
#			try:
#				self._int_rel[key] = value / self._base_peak[key]
#			except KeyError, ZeroDivisionError:
#				self.int_rel[key] = 0.0
#
#	def __getitem__(self, key):
#		return (self._int[key], self._int_rel[key])
#
#	def __delitem__(self, key):
#		del self._int[key]
#		del self._int_rel[key]
#		del self._base_peak[key]

#	def __repr__(self):
#		result = []
#		for key in self.keys():
#			result.append('%s: %s' % (repr(key), repr(self._data[key])))
#		return ''.join(['{', ', '.join(result), '}'])

#	def keys(self):
#		return self._int.keys()
#
#	def copy(self):
#		copyDict = Intensity()
#		copyDict._int = self._int.copy()
#		copyDict._int_rel = self._int_rel.copy()
#		return copyDict

#	def sort(self, *args, **kwargs):
#		self._int.keys.sort(*args, **kwargs)

#	def mkRelative(self, basePeak = {}):
#		if basePaek != {}:
#			for key in self._int.keys():
#				self._int_rel[key] = self._int[key] / basePeak[key]
#		else:
#			for key in self._int.keys():
#				self._int_rel[key] = self._int[key] / self._base_peak[key]

class MSMSEntry:
	"""Class is like SurveyEntry and handls the *.dta MSMS data."""
	def __init__(self, mass, dictIntensity, peaks, polarity, charge, se, dictScanCount, **argv):
		#if se != []:
		if se and isinstance(se, list) and se != []:
			self.se = se
		else:
			self.se = []
		self.index = 0
		self.mass = mass
		self.polarity = polarity
		self.charge = charge
		self.listFragSF = []
		self.strFragName = ""
		self.dictIntensity = dictIntensity
		self.dictIsocoIntensity = {}
		self.dictBeforeIsocoIntensity = {}
		self.dictBasePeakIntensity = argv['dictBasePeakIntensity']
		self.isIsotope = False
		self.isCorrectedIsotopic = {}
		self.isTakenBySuchthat = False
		self.dictScanCount = dictScanCount
		self.monoisotopicRatio = 1.0
		self.monoisotopicCorrected = False

		# a dummy for old functions
		self.occupation = 0

		# peak quality
		self.peaks = peaks

		# content of peaks: [i.precurmass, {i.smpl : i.intensity}, i.charge]
		lIntens = []
		lMass = []
		if self.peaks != []:
			for p in self.peaks:
				lIntens.append(list(p[1].values())[0])
				lMass.append(p[0])

			self.massWindow = max(lMass) - min(lMass)
			self.intensityWindow = max(lIntens) - min(lIntens)

			self.peakMean = sum(lMass) / len(lMass)
			self.peakMedian = min(lMass) + self.massWindow / 2

			listOfSquaredDeviation = []
			for m in lMass:
				listOfSquaredDeviation.append((self.peakMean - m) ** 2)

			self.variance = sum(listOfSquaredDeviation) / len(lMass)
			self.standardDeviation = sqrt(self.variance)

		else:
			self.massWindow = -1
			self.intensityWindow = -1

			self.peakMean = -1
			self.peakMedian = -1

			listOfSquaredDeviation = []

			self.variance = -1
			self.standardDeviation = -1

		if self.se != []:
			for i in se[0].sc.listSamples:
				if i not in self.dictIntensity:
					self.dictIntensity[i] = 0.0

		if 'samples' in argv:
			for i in argv['samples']:
				if i not in self.dictIntensity:
					self.dictIntensity[i] = 0.0

		self.listMark = []

		# all the names of the overlapping isotopes. Is needed for interscan isotopic correction.
		self.listNames = []

	def __repr__(self):
		str = ("  > %.4f " % self.mass).rjust(9)
		for i in sortDictKeys(self.dictIntensity):
			str += (" %.1f " % self.dictIntensity[i]).rjust(13)
		str += " QP: %.2f Mean: %.2f Median: %.2f V(X): %.2f E(X): %.2f %s" % \
			(self.massWindow, self.peakMean, self.peakMedian, self.variance, self.standardDeviation, self.listMark)
		for i in self.listMark:
			str += " " + repr(i) + " "
		if self.listFragSF != []:
			str += repr(self.listFragSF)
		if self.strFragName != "":
			str += repr(self.listFragName)
		return str

	def reprCSV(self):
		str = (" , >, %.4f, " % self.mass).rjust(9)
		if self.isIsotope:
			isotope = '*'
		else:
			isotope = ' '
		str += "%s, " % isotope

		intensities = {}
		if not Debug("isotopesInMasterScan"):
			if self.dictBeforeIsocoIntensity != {}:
				intensities = self.dictBeforeIsocoIntensity
				#for i in sortDictKeys(self.dictBeforeIsocoIntensity):
				#	str += (" %.1f, " % self.dictBeforeIsocoIntensity[i]).rjust(13)
			else:
				intensities = self.dictIntensity
				#for i in sortDictKeys(self.dictIntensity):
				#	str += (" %.1f, " % self.dictIntensity[i]).rjust(13)
		else:
			intensities = self.dictIntensity
			#for i in sortDictKeys(self.dictIntensity):
			#	str += (" %.1f, " % self.dictIntensity[i]).rjust(13)

		if Debug("relativeIntensity"):
			for sample in list(intensities.keys()):
				if self.dictBasePeakIntensity[sample] != 0.0:
					intensities[sample] /= self.dictBasePeakIntensity[sample]

		for i in sorted(intensities):
			if Debug("relativeIntensity"):
				str += (" %.4f, " % self.dictIntensity[i]).rjust(13)
			else:
				str += (" %.1f, " % self.dictIntensity[i]).rjust(13)

		str += " %.4f, %.2f, %.2f, %.2f, %.2f," % \
			(self.massWindow, self.peakMean, self.peakMedian, self.variance, self.standardDeviation)

		for i in self.listMark:
			if i.chemsc:
				str += " " + repr(i) + ":" + repr(i.chemsc) + ","
			else:
				str += " " + repr(i) + ","
		return str

	def __cmp__(self, otherself):
		return cmp(self.mass, otherself.mass)
	def __lt__(self, otherself):
		return self.mass<otherself.mass

class MSMS:
	"""Class for a DTA File"""
	def __init__(self, mass, charge, polarity, fileName, retentionTime = None, scanNumber = None,
			peaksCount = None, totIonCurrent = None, MSMSthreshold = None, table = None, basePeakMz = None,
			basePeakIntensity = None, threshold = None):
		"""arguments is the head of .dta table and eventually
		a list of their entries"""
		#self.strPrecurmass = mass
		self.precurmass = float(mass)
		self.scanNumber = scanNumber
		self.retentionTime = retentionTime
		self.peaksCount = peaksCount
		self.totIonCurrent = totIonCurrent
		self.basePeakMz = basePeakMz
		self.basePeakIntensity = basePeakIntensity
		self.threshold = threshold

		if charge:
			self.charge = int(charge)
		else:
			self.charge = None
		if polarity:
			self.polarity = int(polarity)
		else:
			self.polarity = None
		self.fileName = fileName
		#self.msms = []
		#self.entries = [[] for i in range(0,2)]
		self.entries = []
		self.scanCount = 1
		if not table is None:
			self.fillTable(table, MSMSthreshold)

	#def __add__(self, other):
	def add(self, other):
		"""__add__() for putting together two MS/MS spectra, which
		are from exactly the same precurmass"""

		assert self.strPrecurmass == other.strPrecurmass
		assert self.precurmass == other.precurmass
		#assert self.retentionTime == other.retentionTime
		try:
			assert self.charge == other.charge
			assert self.polarity == other.polarity
			assert self.filename == other.filename
		except AttributeError:
			pass

		self.msms += other.msms
		self.entries += other.entries

		return self

	def __cmp__(self, otherself):
		return cmp(self.precurmass, otherself.precurmass)

	def __repr__(self):
		str = "Precursor Mass      charge\n"
		str = " %.4f            %d\n\n" % (self.precurmass, self.polarity)
		for i in self.entries:
			str = str + " %.4f          %.4f\n" % (i[0], i[1])
		return str

	def get_EntryByNum(self, n):
		return self.entries[n]

	def get_Entry(self, m, t):
		"""Get list of MSMS experiment by giving precursor mass"""
		l = []
		if self.entries == []: raise "Empty entries"
		for i in self.entries:
			if m <= i[0] + t and m >= i[0] - t:
				l.append(i)
		return l

	def get_listEntryByMark(self, mark):
		"""Get all MSMS Entries which fit the mark conditions.
		The conditions are chain of marks connected with a boolean
		operator: and, or, xor."""
		l = []
		if self.entries == []: raise "Empty entries"
		for i in self.entries:
			if len(i) > 2:
				for j in i[2:]:
					if mark == j:
						l.append(i)
		return l

	def fillTable(self, table, MSMSthreshold):
		"""In: <list of strings>
		The strings are the lines of a .dta file. fillTable()
		writes it into self.entries"""

		regDta = re.compile("(\d+\.?\d*)(\s|\t)+([-]?\d+\.?\d*)")

		# go through all strings
		for i in table:
			if i[0] != '#':
				n1, xxx, n2 = regDta.match(i).groups()
				if float(n2) >= MSMSthreshold:
					self.entries.append([float(n1), float(n2)])

class MSMass:
	"""Class for a precurmass containing the mass itself, the intensity and
	relIntensity. The msms is a flag stating if there is a msms experiment."""
	def __init__(self, precurmass, intensity, smpl, polarity, charge,
			fileName, scanCount, basePeakIntensity, intensity_relative = None):
		self.precurmass = precurmass
		self.intensity = intensity
		self.intensity_relative = intensity_relative
		self.polarity = polarity
		self.charge = charge
		self.fileName = fileName
		self.relativeIntensity = 0
		self.smpl = smpl
		self.scanCount = scanCount
		self.basePeakIntensity = basePeakIntensity

	def __cmp__(self, otherself):
		"""For a Sample Iterator... why not?!"""
		return cmp(self.precurmass, otherself.precurmass)

	def __repr__(self):
		return "%.4f %.4f \n\n" % (self.precurmass, self.intensity)

	def set_relativeIntensity(self, referenceIntensity):
		self.relativeIntensity = self.intensity / referenceIntensity


class UnSpec:

	def __init__(self, options, name, mzxml):

		self.listUnSmpl = []
		self.listMSMS = []
		self.name = name

		self.MSthreshold = options['MSthreshold']
		self.MSresolution = options['MSresolution']
		self.deltaRes = options['MSresolutionDelta']
		self.options = options

	def addUnSpec(self, listUnSmpl):
		self.listUnSmpl.append(listUnSmpl)

	def addMSMS(self, precursorMass, listMSMS):
		self.listMSMS.append([precursorMass, listMSMS])

	def mergeSpectraHeuristic(self, threshold = None, threshold_type = 'absolute'):

		nrOfSpectra = len(self.listUnSmpl)

		# get max number of peaks
		maxLength = 0
		for i in range(len(self.listUnSmpl)):
			if maxLength < len(self.listUnSmpl[i]): maxLength = len(self.listUnSmpl[i])

		print(("maxLength of all spectra is " + repr(maxLength)))

		#heuristicAlignment(listSamples, dictSamples, listPolarity, tolerance, sumContent,
		#	merging, numLoops = None, deltaRes = None, minMass = None, minocc = None, msThreshold = None):

		# merge spectra, such that they are somehow ordered in advance

		### for Kai ###
		#listMass = ['876.801', '758.569', '742.574']
		#dictF = {}
		#for keyMass in listMass:
		#	dictF[keyMass] = open("%s-%s-output.txt" % (self.name, keyMass), 'w')
		#dictKai = {}
		#for keyMass in listMass:
		#	dictKai[keyMass] = []
		### End for Kai ###

		# generate dictionary for heuristicAlignment() input
		dictSpecEntry = {}
		index = 0
		for l in self.listUnSmpl:

			sample = "%d" % index
			dictSpecEntry[sample] = []
			for i in l:
				dictSpecEntry[sample].append(specEntry(
					mass = i[0],
					content = i[1]))
			index += 1

		listClusters = heuristicAlignment(list(dictSpecEntry.keys()),
				dictSpecEntry,
				self.options['MSresolution'],
				deltaRes = self.options['MSresolutionDelta'])


		listPeaks = []
		for cl in listClusters:
			sumMassTimesInt = 0
			sumInt = 0
			avgMass = 0
			listIntensities = []
			for sample in list(dictSpecEntry.keys()):#cl.keys():

				takeIt = False
				if sample in cl:
					if cl[sample].content:
						sumMassTimesInt += cl[sample].mass * float(cl[sample].content)
						sumInt += float(cl[sample].content)
						listIntensities.append(cl[sample].content)
						if cl[sample].content >= threshold:#self.options['MSthreshold'] / sqrt(nrOfSpectra):
							takeIt = True
				else:
					dbgout("missing sample %s while averaging" % sample)

			if takeIt and sumInt > 0.0:

				avgMass = sumMassTimesInt / sumInt
				avgInt = sumInt / nrOfSpectra

				listPeaks.append([avgMass, avgInt, listIntensities])

		return listPeaks

		#for cl in listClusters:
		#	str = ''
		##	for sample in dictSpecEntry.keys():#cl.keys():
		#		if cl.has_key(sample):
		#			if cl[sample].content:
		#				str +=  "  %.4f  " % cl[sample].mass
		#			else:
		#				try:
		#					str +=  " /%.4f/ " % cl[sample].mass
		#				except TypeError:
		#					dbgout("TypeError: %4.4f" % cl[sample].mass)
		#		else:
		#			str += " / empty  / "
		#	dbgout(str)
		#exit(0)

	def mergeSpectra(self, threshold = None, threshold_type = 'absolute'):

		nrOfSpectra = len(self.listUnSmpl)

		# get max number of peaks
		maxLength = 0
		for i in range(len(self.listUnSmpl)):
			if maxLength < len(self.listUnSmpl[i]): maxLength = len(self.listUnSmpl[i])

		print(("maxLength of all spectra is " + repr(maxLength)))

		#heuristicAlignment(listSamples, dictSamples, listPolarity, tolerance, sumContent,
		#	merging, numLoops = None, deltaRes = None, minMass = None, minocc = None, msThreshold = None):

		# merge spectra, such that they are somehow ordered in advance

		### for Kai ###
		#listMass = ['885.549', '786.565', '766.539']
		#dictF = {}
		#for keyMass in listMass:
		#	dictF[keyMass] = open("%s-%s-output.txt" % (self.name, keyMass), 'w')
		#dictKai = {}
		#for keyMass in listMass:
		#	dictKai[keyMass] = []
		### End for Kai ###

		# merge all scans into one peak list
		numMerges = 3

		listPeaks = []
		for i in range(numMerges + 1):
			listPeaks.append([])

		str = ''
		for index in range(maxLength):
			str += '\n'

			numL = 0
			for l in self.listUnSmpl:
				if len(l) > index and l[index][1]:

					### routine for Kai (delete after usage) ###
					## calc mass window for cluster
					#if not self.deltaRes:
					#	res = self.MSresolution
					#else:
					#	res = self.MSresolution + (l[index][0] - l[0][0]) * self.deltaRes
					##partialRes = (l[index][0] / res)
					## 5ppm:
					#partialRes = (l[index][0] / 1000000) * 7.5

					#for keyMass in listMass:
					#	if float(keyMass) - partialRes < l[index][0] and\
					#		l[index][0] < float(keyMass) + partialRes:
					#		#dbgout("%f, %f, %d" % (l[index][0], l[index][1], numL))
					#		dictKai[keyMass].append([l[index][0], l[index][1], numL])

					### End of routine for Kai ###

					listPeaks[0].append([l[index][0], l[index][1], l[index][2], []])

				numL += 1

		### for Kai ###
		#for keyMass in listMass:
		#	dictKai[keyMass].sort(cmp = lambda x, y: cmp(x[2], y[2]))
		#	for i in dictKai[keyMass]:
		#		dictF[keyMass].write("%s, %.1f, %d\n" % (i[0], i[1], i[2]))
		#	dictF[keyMass].close()
		### end for Kai ###

		try:
			minMass = listPeaks[0][0][0]
		except IndexError:
			raise LipidXException("No peaks imported. Check the import settings," +\
					" particular time range and threshold.")

		log("aligned list length is " + repr(len(listPeaks[0])))

		width = 0
		for index in range(len(listPeaks[0]) - 1):
			width = listPeaks[0][index + 1][0] - listPeaks[0][index][0]

		for count in range(numMerges):

			#hpy().heap().dump("C:\Users\The Duke\My_Projects\LipidXplorer BUGS\Dominik - 14-07-2011\LipidXplorer-v1.1\log-1.2.hpy")

			current = 0
			lnext = []

			listPeaks[count].sort(cmp = lambda i,j : (i[0] < j[0]) and -1 or\
					(i[0] > j[0]) and 1 or 0)

			lastEntry = False

			while current < (len(listPeaks[count]) - 1):

				# routine for collecting all masses which are in partialRes
				index = 1
				svIndex = 0
				sv = False
				lrslt = [listPeaks[count][current]]
				listSmpl = []

				# get the window size
				if isinstance(self.MSresolution, lpdxUITypes.TypeTolerance):
					if self.MSresolution.kind == 'Da':
						partialRes = self.MSresolution.da
					else:
						if self.deltaRes:
							tmp = self.MSresolution.tolerance + (listPeaks[count][current][0] - minMass) * self.deltaRes
						else:
							tmp = self.MSresolution.tolerance
						partialRes = (listPeaks[count][current][0] / tmp)

				while listPeaks[count][current + index][0] - listPeaks[count][current][0] < partialRes:

#					listSmpl += listAlignmentSpec[current + index][1].keys()
					lrslt.append(listPeaks[count][current + index])

					if (current + index) < (len(listPeaks[count]) - 1):
						index += 1
					else:
						break

				current += index

				# calc average of masses cluster
				sumMassTimesInt = 0
				avgMass = 0
				for i in lrslt:
					sumMassTimesInt += i[0] * i[1]

				listIntensities = []
				listInt = []
				for i in lrslt:
					if i[2] != []:
						listInt += i[2]
					listIntensities.append(i[1])

				# calc sum of Intensities
				sumInt = 0
				for i in listIntensities:
					sumInt += i
				avgMass = sumMassTimesInt / sumInt
				avgInt = sumInt / nrOfSpectra
				listInt += listIntensities

				takeIt = False
				for i in listInt:
					if threshold_type == 'absolute':
						if i >= threshold:
							takeIt = True
							break

				if takeIt:
					listPeaks[count + 1].append([avgMass, avgInt, listInt])

				if listPeaks[count][current] == listPeaks[count][-1]:
					listPeaks[count + 1].append([listPeaks[count][-1][0], listPeaks[count][-1][1], listPeaks[count][-1][2]])

		if listPeaks[-1] != []:

			index = 0
			while True:
				if isinstance(listPeaks[-1][index][2], list):
					sumInt = 0
					avgInt = 0
					for i in listPeaks[-1][index][2]:
						# calc average of intensities in cluster
						sumInt += i
					avgInt = sumInt / nrOfSpectra

					listPeaks[-1][index][1] = avgInt

				index += 1
				try: listPeaks[-1][index]
				except: break

		return listPeaks[-1]


class Sample:
	""" Class Sample is holds the entrys of one or more .csv files. The
	cvs has 3 colums for precurmass, intensity and relIntensity. These are
	stored in the dictionary entry"""
	def __init__(self, sampleName, sourceDir, sourceFile, polarity, options):

		# name for the sample
		self.sampleName = sampleName

		# source of the csv file
		self.sourceFile = sourceFile

		# source of the sample folder as path
		self.sourceDir = sourceDir

		# mz range start
		self.mzRangeStart = None

		# mz range end
		self.mzRangeEnd = None

		# the polarity of the spectrum
		self.polarity = polarity

		# the base peak of the MS1 spectrum
		self.base_peak_ms1 = None

		self.listPrecurmass = [] # list will be filled with MSMass's
		self.listMsms = [] # list of MSMS experiments

		return None

	def __repr__(self):
		str = self.sampleName + "\n\n"
		for i in self.listPrecurmass:
			str = str + "%.4f %.4f %.4f\n" % (i.precurmass, i.intensity, i.relativeIntensity)
		return str

	def add_MSMass(self, msmass):
		self.listPrecurmass.append(msmass)

	def add_MSMS(self, msms):
		self.listMsms.append(msms)

	def openAndRead(self, fn):
		"""The name says it."""

		with open(fn, "r") as f:
			l = f.readlines()

		# may there be an empty file
		if l == []:
			raise "File " + fn + " is empty."

		return l

	def fillTable(self, f, smplName, smplDir, MSthreshold, thresholdType):
		"""The argument is of type ["precurmass, intensity, relIntensity"].
		It is the content of .csv file."""

		maximum = None

		# if thr type is relative, find base peak first
		if thresholdType == 'relative':
			maximum = 0
			for i in f:
				if numstart.match(i):
					n = i.split(',')
					if float(n[1]) >= maximum: maximum = float(n[1])

			threshold = (MSthreshold / 100) * maximum

		else:
			threshold = MSthreshold


		for i in f:
			if numstart.match(i):

				# split it to read it
				n = i.split(',')

				if float(n[1]) >= threshold:
					# append a new MSMass
					self.listPrecurmass.append(MSMass(
							precurmass = float(n[0]),
							intensity = float(n[1]),
							smpl = smplName,
							polarity = None,
							charge = None,
							fileName = smplDir,
							scanCount = 1,
							basePeakIntensity = maximum))

		# return the base peak intensity
		return maximum

	def get_PrecurmassByNumber(self, n):
		"""in: (<number of precursor mass in the surface scan>)
			out: Mass object"""
		if not self.listPrecurmass == []:
			return self.listPrecurmass[n]
		else:
			raise "No Precursormasses loaded in the Surface Scan"

	def get_Precurmass(self, mass):
		"""in: (<number of precursor mass in the surface scan>)
			out: Mass object"""
		for i in self.listPrecurmass:
			if i.precurmass == mass:
				return i
		return None

	def get_EntryList(self):
		return self.listPrecurmass

	def get_MSMS(self, n):
		m = []
		for i in self.listMsms:
			if n == i.precurmass:
				return i
		return None


	def get_PrecurmassByWindow(self, upperBorder, lowerBorder):
		list = []
		for i in self.listPrecurmass:
			if upperBorder < i.precurmass and i.precurmass < lowerBorder:
				list.append(i)
		return list


	def set_referenceIntensity(self, referenceIntensity):
		self.referenceIntensity = referenceIntensity

	def calcRelativeIntensity(self):
		if self.referenceIntensity:
			for i in self.listPrecurmass:
				i.set_relativeIntensity(self.referenceIntensity)
		else:
			raise "Cannot set relativeIntensity without referenceIntensity."

	def bestFitWindow(self, msms1, msms2, window):
		"""Give back all MSMass's in the overlapping window."""
		lowerBorder = msms1.precurmass + window
		upperBorder = msms2.precurmass - window
		return self.get_PrecurmassByWindow(upperBorder, lowerBorder)


class MasterScan:
	"""This class holds all Sample Instanstances for a complete view over all
	experiments

	example:
	# loads all files, including directories
	scan = MasterScan(argv)

	# get a Entry by index
	scan.listSurveyEntry[i]

	# get a Sample by index
	scan[i]

	# this can be easiely printed:
	#print scan[i] # output is a table with precurmass, intensity, relative intensity

	IN: name -> string - name for the MasterScan
		MStolerance -> float - accuracy in ppm; is automatically converted into resolution
		MSMStolerance -> float - accuracy in ppm; is automatically converted into resolution
		MSresolution -> int - resolution in resolution per peak
		MSMSresolution -> int - resolution in resolution per peak
		selectionWindow -> float - window size in "hardcoded" float
	"""

	def __init__(self, options = None):

		self.importSettingsFile = ""
		self.setting = ""
		self.importDir = ""
		self.listFiles = []

		self.dictSamples = {}
		self.listSamples = []
		self.listSurveyEntry = []

		# the dict of base peaks for the calculation of relative intensities
		self.dictBasePeakIntensity_MS = {}

		# is true, if the first Sample is saved as Survey Entry
		self.basicSurvey = False

		# set the options
		self.strEmpty = '0'
		self.options = {}
		if options:
			self.options = options

		# for backwards compatibality
		if 'MStolerance' not in self.options:
			self.options['MStolerance'] = options['MSaccuracy']
		if 'MSMStolerance' not in self.options:
			self.options['MSMStolerance'] = options['MSMSaccuracy']

		# init the occupation threshold variable
		self.sampleOccThr = {}
		self.sampleOccThr['MS'] = []
		self.sampleOccThr['MSMS'] = []

		# the charge for the whole MasterScan
		if "forcesinglecharge" in self.options:
			self.charge = self.options['forcesinglecharge']
			self.forcesinglecharge = self.options['forcesinglecharge']
		else:
			self.charge = None
			self.forcesinglecharge = 0

		# optional options for the Run
		self.optionalOptions = {}

		self.name = ""

	def __getitem__(self, smpl):
		if self.dictSamples[smpl]:
			return self.dictSamples[smpl]
		else:
			raise "No sample %s." % (smpl)

	def __repr__(self):

		noListMSMS = True
		noDictMSMS = False

		str = ""
		for i in self.listSurveyEntry:
			str += repr(i) + '\n'
			if i.listMSMS == []:
				noDictMSMS = True
				for j in self.listSamples:
					if j in i.dictMSMS:
						str = str + repr(i.dictMSMS[j]) + '\n'
						noDictMSMS = False
					else:
						break
			else:
				noListMSMS = False
				for j in i.listMSMS:
					str = str + repr(j)

		return str

	def getSEbyIndex(self, index):
		for se in self.listSurveyEntry:
			if se.index == index:
				return se

	def sortAndIndedice(self):

		self.listSurveyEntry.sort()

		# generate indices
		for index in range(len(self.listSurveyEntry)):
			self.listSurveyEntry[index].index = index

	def get_lastSurveyEntry(self, mass, polarity):
		"""Get the biggest entry as index from listSurveyEntry which is smaller than mass"""

		for i in range(len(self.listSurveyEntry)):
			if self.listSurveyEntry[i].precurmass >= mass and self.listSurveyEntry[i].polarity == polarity:
				return i - 1
		return len(self.listSurveyEntry) - 1

	def get_SurveyEntry(self, mass, polarity):
		"""Returns the searched SurveyEntry, if its precursor mass is
in <mass> +- machines resolution. Per options this can be changed with
MStolerance to an arbitrary value"""

		# list for output
		list = []

		for i in range(len(self.listSurveyEntry)):
			#if mass - tMS <= self.listSurveyEntry[i].precurmass \
			#	and mass + tMS >= self.listSurveyEntry[i].precurmass \
			#	and self.listSurveyEntry[i].polarity == polarity:
			if self.options['MSresolution'].fitIn(self.listSurveyEntry[i].precurmass, mass) and \
				self.listSurveyEntry[i].polarity == polarity:

				# "one-to-right" look ahead
				try: dummy = self.listSurveyEntry[i+1]
				except IndexError: return self.listSurveyEntry[i]

				#if mass - tMS <= self.listSurveyEntry[i+1].precurmass \
				#	and mass + tMS >= self.listSurveyEntry[i+1].precurmass \
				#	and self.listSurveyEntry[i+1].polarity == polarity\
					#and abs(self.listSurveyEntry[i].precurmass - mass) > abs(self.listSurveyEntry[i+1].precurmass - mass):
					#list.append(self.listSurveyEntry[i+1])
				if self.options['MSresolution'].fitIn(self.listSurveyEntry[i + 1].precurmass, mass) and \
					self.listSurveyEntry[i + 1].polarity == polarity and \
					abs(self.listSurveyEntry[i].precurmass - mass) > abs(self.listSurveyEntry[i+1].precurmass - mass):
					list.append(self.listSurveyEntry[i+1])
					return list
					#return self.listSurveyEntry[i+1]
				else:
					list.append(self.listSurveyEntry[i])
					#return self.listSurveyEntry[i]
		return list

	def get_SurveyEntriesByMassRange(self, lowerBound, upperBound):
		l = []
		for i in self.listSurveyEntry:
			tMS = i.precurmass / self.options['MStolerance']
			if lowerBound <= i.precurmass + tMS and upperBound >= i.precurmass - tMS:
				l.append(i)
		return l

	def get_SurveyEntryByMSMS(self, msms):
		for i in self.listSurveyEntry:
			for j in i.listMSMS:
				if j:
					if j == msms:
						return i

	def get_posSurveyEntry(self):
		l = []
		for i in self.listSurveyEntry:
			if i.polarity > 0 :
				l.append(i)
		return l

	def get_negSurveyEntry(self):
		l = []
		for i in self.listSurveyEntry:
			if i.polarity < 0:
				l.append(i)
		return l

	def set_charge(self, charge):
		self.charge = charge

	def shiftPrecursorsInRawFilterLine(self, shift):
		"""A hack for LTQ Orbitrap data where the filterLine entry
		of the mzXML's has a shifted Precursor mass. Correction
		by 'shift'."""

		s = float(shift)
		for keySample in list(self.dictSamples.keys()):
			for indexMsms in range(len(self.dictSamples[keySample].listMsms)):
				self.dictSamples[keySample].listMsms[indexMsms].precurmass += s

	def shiftPrecursors(self, shift):
		"""A precursor shift function which makes an offset correction
		of the value 'shift'. It just touches MS data."""

		s = float(shift)
		for keySample in list(self.dictSamples.keys()):
			for index in range(len(self.dictSamples[keySample].listPrecurmass)):
				self.dictSamples[keySample].listPrecurmass[index].precurmass += s

	def checkOccupation(self, dictIntensity, dictScans, occThr = None, threshold = None,
			mode = 'MS', dictBasePeakIntensity = {}, factor = 1, threshold_type = 'absolute'):
		'''Returns False if the occupation settings from MasterScan.sampleOccThr
		not fit to the SurveyEntry se. This function implements grouping of
		samples having different occupation threshold settings. If samples
		are missing they won't count for the occupation threshold.

		The factor attribute is used for testing if a theoretical isotopic
		correction would fit the threshold. The factor is the ratio of the
		particular isotope.'''

		# security check for dictScans and dictIntensity
		try:
			for k in self.listSamples:
				assert k in dictIntensity
				assert k in dictBasePeakIntensity
				assert k in dictScans
				assert dictScans[k] > 0
		except AssertionError:
			dbgout(">d> %d: %s" %(len(self.listSamples), repr(self.listSamples)))
			dbgout(">d> %d: %s" %(len(dictIntensity), repr(dictIntensity)))
			dbgout(">d> %d: %s" % (len(list(dictBasePeakIntensity.keys())), repr(dictBasePeakIntensity)))
			dbgout(">d> %d: %s" % (len(list(dictScans.keys())), repr(dictScans)))
			raise AssertionError

		if not occThr is None:

			# check every group, if only one group matches the occupation Threshold
			# return True (i.e. OR of all occupation tests)
			for occThrEntry in self.sampleOccThr[mode]:
				if occThrEntry[1] != []: # several groups given
					count = 0
					length = len(occThrEntry[1])
					t = {}
					for	sample in occThrEntry[1]:

						# if the threshold is given as a relative value make absolute value
						if threshold_type == 'relative':
							t[sample] = threshold * dictBasePeakIntensity[sample]
						else:
							t[sample] = threshold

						thrsld = t[sample] / sqrt(dictScans[sample])

						if float(dictIntensity[sample] * factor) > thrsld:
							count += 1

					if float(count) / length >= occThr:
						return True
				else:
					count = 0
					length = len(list(dictIntensity.keys()))

					t = {}
					for	sample in self.listSamples:

						# if the threshold is given as a relative value make absolute value
						if threshold_type == 'relative':
							t[sample] = threshold * dictBasePeakIntensity[sample]
						else:
							t[sample] = threshold

						thrsld = t[sample] / sqrt(dictScans[sample])

						if float(dictIntensity[sample] * factor) > thrsld:
							count += 1

					if float(count) / length >= occThr:
						return True


		else:
			count = 0
			length = len(list(dictIntensity.keys()))

			t = {}
			for	sample in self.listSamples:

				# if the threshold is given as a relative value make absolute value
				if threshold_type == 'relative':
					t[sample] = threshold * dictBasePeakIntensity[sample]
				else:
					t[sample] = threshold

				thrsld = t[sample] / sqrt(dictScans[sample])

				if float(dictIntensity[sample] * factor) > thrsld:
					count += 1

			if float(count) / length >= occThr:
				return True

		return False

	def getOccupation(self, dictIntensity, dictScans, occThr = None, threshold = None,
			mode = 'MS', dictBasePeakIntensity = {}, factor = 1, threshold_type = 'absolute'):

		nbScans = 1

		# security check for dictScans and dictIntensity
		try:
			for k in self.listSamples:
				assert k in dictIntensity
		except AssertionError:
			dbgout(">d> %d: %s" %(len(self.listSamples), repr(self.listSamples)))
			dbgout(">d> %d: %s" %(len(dictIntensity), repr(dictIntensity)))
			raise AssertionError

		count = 0
		length = len(list(dictIntensity.keys()))

		t = {}
		for	sample in self.listSamples:

			if dictScans != {}:
				nbScans = dictScans[sample]

			t[sample] = threshold
			thrsld = t[sample] / sqrt(nbScans)

			if float(dictIntensity[sample] * factor) > thrsld:
				count += 1

		return float(count) / length

	def checkThreshold(self, dictIntensity, dictScans, threshold, mode = 'MS', relative = None):
		'''Returns False if the threshold settings from MasterScan.options
		not fit to the SurveyEntry se.'''

		# security check for dictScans and dictIntensity
		try:
			for k in self.listSamples:
				assert k in dictIntensity
				assert k in dictScans
				assert dictScans[k] > 0
		except AssertionError:
			dbgout("sample %s" % k)
			dbgout("mode %s" % mode)
			dbgout(dictIntensity)
			dbgout(dictScans)
			raise AssertionError

		# if the threshold is given as a relative value make absolute value
		if not relative is None:
			threshold = (threshold / 100) * relative

		# check every group, if only one group matches the occupation Threshold
		# return True (i.e. OR of all occupation tests)
		for occThrEntry in self.sampleOccThr[mode]:
			if occThrEntry[1] != []: # several groups given
				count = 0
				length = len(occThrEntry[1])
				for	sample in occThrEntry[1]:
					if float(dictIntensity[sample]) > threshold / sqrt(dictScans[sample]):
						count += 1
				if float(count) / length >= occThrEntry[0]:
					return True
			else:
				count = 0
				length = len(list(dictIntensity.keys()))

				for	sample in self.listSamples:
					if float(dictIntensity[sample]) > threshold / sqrt(dictScans[sample]):
						count += 1

				if float(count) / length >= occThrEntry[0]:
					return True

		return False

	def dump(self, dump_file):

		reportout("Dumping Master Scan content")

		with open(dump_file, 'w') as f:

			strOut = "\n"
			strOut += "\nMasterScan: ," + self.name
			strOut += "\n"
			strOut += "data folder: , %s\n" % self.importDir
			strOut += "import configuration file: , %s\n" % self.importSettingsFile
			strOut += "import configuration: , %s\n" % self.setting
			strOut += "\n"
			if self.forcesinglecharge != 0:
				strOut += "forcesinglecharge: ," + repr(self.forcesinglecharge)
			strOut += "time range: , (%s, %s)\n" % (repr(self.options['timerange'][0]), repr(self.options['timerange'][1]))
			strOut += "MS mass range: , (%s, %s)\n" % (repr(self.options['MSmassrange'][0]), repr(self.options['MSmassrange'][1]))
			if 'MSMSmassrange' in self.options and not (self.options.isEmpty('MSMSmassrange')):
				strOut += "MS/MS mass range: , (%s, %s)\n" % (repr(self.options['MSMSmassrange'][0]), repr(self.options['MSMSmassrange'][1]))
			strOut += "MS tolerance: ,+/- %s\n" % (repr(self.options['MStolerance']))
			if 'MSMSfilter' in self.options and not (self.options.isEmpty('MSMSfilter')):
				strOut += "MS frequency filter: %s\n" % (repr(self.options['MSMSfilter']))
			if 'MSMStolerance' in self.options and not (self.options.isEmpty('MSMStolerance')):
				strOut += "MS/MS tolerance: ,+/- %s\n" % (repr(self.options['MSMStolerance']))
			strOut += "MS resolution: , %s\n" % (repr(self.options['MSresolution'].tolerance))
			if 'MSMSresolution' in self.options and not (self.options.isEmpty('MSMSresolution')):
				strOut += "MS/MS resolution: , %s\n" % (repr(self.options['MSMSresolution'].tolerance))
			else:
				strOut += "MS/MS resolution: , 0\n"
			strOut += "MS resolution gradient: , %s\n" % (repr(self.options['MSresolutionDelta']))
			if 'MSMSresolutionDelta' in self.options and not (self.options.isEmpty('MSMSresolutionDelta')):
				strOut += "MS/MS resolution gradient: , %s\n" % (repr(self.options['MSMSresolutionDelta']))
			strOut += "MS threshold: , %s\n" % (repr(self.options['MSthreshold']))
			if 'MSMSthreshold' in self.options and not (self.options.isEmpty('MSMSthreshold')):
				strOut += "MS/MS threshold: , %s\n" % (repr(self.options['MSMSthreshold']))
			strOut += "MS minimum occupation: ,+/- %s\n" % (repr(self.options['MSminOccupation']))
			if 'MSMSminOccupation' in self.options and not (self.options.isEmpty('MSMSminOccupation')):
				strOut += "MS/MS minimum occupation: ,+/- %s\n" % (repr(self.options['MSMSminOccupation']))
			if 'MSfilter' in self.options and not (self.options.isEmpty('MSfilter')):
				strOut += "MS/MS frequency filter: %s\n" % (repr(self.options['MSfilter']))


			strOut += "\n\n"

			strOut += ",,,,"
			for i in self.listSamples:
				strOut += i.rjust(13) + ","
			strOut += "Peak Quality, Mean, Median, Variance, standardDeviation\n"

			f.write(strOut)

			reportout("containing:\n%d MS entries and" % len(self.listSurveyEntry))
			countMSMS = 0
			for i in sorted(self.listSurveyEntry):
				# if options['massrange'] is given
				if ('massrange' not in self.options or (self.options['massrange'][0] <= i.precurmass \
					and i.precurmass <= self.options['massrange'][1])) and \
					('polarity' not in self.options or self.options['polarity'] == i.polarity) :

					#strOut += i.reprCSV() + "\n"
					f.write(i.reprCSV() + "\n")

					if i.listMSMS != []:
						for j in sorted(i.listMSMS):
							#strOut += j.reprCSV() + "\n"
							f.write(j.reprCSV() + "\n")
							countMSMS += 1
						#strOut += "\n"
						f.write("\n")

			reportout("%d MS/MS entries." % countMSMS)

		return True

	def dumpInSQL(self, dump_file):

		reportout("Dumping Master Scan content")

		with open(dump_file, 'w') as f:

			strSQL = ""
			strSQL += ",, Precursormass,"
			for i in self.listSamples:
				strSQL += i.rjust(13) + ","
			strSQL += "QueryName, Chemsc, error,"
			for i in self.listSamples:
				strSQL += i.rjust(13) + ","
			strSQL += "Mass, name, error, frsc, nlsc\n"
			#strSQL += "Peak Quality, Mean, Median, Variance, standardDeviation\n"

			f.write(strSQL)

			reportout("containing:\n%d MS entries and" % len(self.listSurveyEntry))
			countMSMS = 0
			for i in sorted(self.listSurveyEntry):
				# if options['massrange'] is given
				if ('massrange' not in self.options or (self.options['massrange'][0] <= i.precurmass \
					and i.precurmass <= self.options['massrange'][1])) and \
					('polarity' not in self.options or self.options['polarity'] == i.polarity) :

					#strSQL += i.reprCSV_SQL() + "\n"

					for line in i.reprCSV_SQL():
						f.write(line + "\n")
						#strSQL += line + "\n"

					#if i.listMSMS != []:
					#	for j in sorted(i.listMSMS):
					#		strSQL += j.reprCSV() + "\n"
					#		countMSMS += 1
					#	strSQL += "\n"

			reportout("%d MS/MS entries." % countMSMS)

		return True
		pass

class SurveyEntry:
	"""A class for a row of the MasterScan. To have a extra class here makes the
	handling easier without using more memory, since we deal always with references
	in python.
	"""

	def __init__(self, msmass, smpl, peaks, charge, polarity, dictScans, msms = None, **argv):

		self.index = 0

		if isinstance(msmass, MSMass):
			self.precurmass = msmass.precurmass
		else:
			self.precurmass = msmass

		if charge:
			assert isinstance(charge, int)
			self.charge = int(charge)
		else:
			self.charge = None

		self.polarity = polarity

		self.listPrecurmassSF = [] # contains sum compositions of the precursor mass
		self.sumComposition = [] # guess it is not used anymore
		self.listMark = [] # contains marks of the precursor mass
		self.dictScans = dictScans # needed for the intensity threshold (thrshl / sqrt(nb. of scans))
		self.isIsotope = False # isotopic marker for output if it was isotopic corrected
		self.isTakenBySuchthat = False # SUCHTHAT marker
		self.monoisotopicRatio = 1.0 # for type I isotopic correction
		self.listScanEntries = [] # used for storing the peakEntry structure in peak marking
		self.listVariables = [] # used when queries are parsed - the internal variable data structure

		self.dictIntensity = smpl # the intensities
		self.dictBeforeIsocoIntensity = {} # the intensities before isotopic correction
			# for outputting it in the MasterScan

		# for the relative intensities of the associated fragment
		# spectra, here are the MSMS base peaks
		self.dictBasePeakIntensity = argv['dictBasePeakIntensity']

		if not msms:
			self.dictMSMS = {}
			self.listMSMS = []
		else:
			self.add_MSMS(msms, smpl)

		# a dummy for old functions
		self.occupation = 0

		# peak quality
		self.peaks = peaks

		# peaks can be empty if it is a virtual SurveyEntry
		if self.peaks != []:

			# content of peaks: [i.precurmass, {i.smpl : i.intensity}, i.charge]
			lIntens = []
			lMass = []
			for p in self.peaks:
				lIntens.append(list(p[1].values())[0])
				lMass.append(p[0])

			self.massWindow = max(lMass) - min(lMass)
			self.intensityWindow = max(lIntens) - min(lIntens)

			self.peakMean = sum(lMass) / len(lMass)
			self.peakMedian = min(lMass) + self.massWindow / 2

			listOfSquaredDeviation = []
			for m in lMass:
				listOfSquaredDeviation.append((self.peakMean - m) ** 2)

			self.variance = sum(listOfSquaredDeviation) / len(lMass)
			self.standardDeviation = sqrt(self.variance)

		else:
			self.massWindow = -1
			self.intensityWindow = -1

			self.peakMean = -1
			self.peakMedian = -1

			listOfSquaredDeviation = []

			self.variance = -1
			self.standardDeviation = -1

		self.removedByIsotopicCorrection_MS = False
		self.removedByIsotopicCorrection_MSMS = False

	def __lt__(self, other):
		return self.precurmass < other.precurmass

	def __repr__(self):

		str = ("/%s/ . %.4f | " % (("%d" % self.polarity)[0], float(self.precurmass))).rjust(9)

		for i in sorted(self.dictIntensity.keys()):
			if i in self.dictMSMS and i in self.dictIntensity:
				str = str + (" [%d] " % (int(self.dictIntensity[i]))).rjust(13)
			else:
				if i not in self.dictIntensity:
					str = str + ("  %d  " % (int(0))).rjust(13)
				else:
					str = str + ("  %d  " % (int(self.dictIntensity[i]))).rjust(13)

		str += " QP: %.4f Mean: %.4f Median: %.4f V(X): %.4f E(X): %.4f %s" % \
			(self.massWindow, self.peakMean, self.peakMedian, self.variance, self.standardDeviation, self.listMark)

		return str

	def reprCSV(self, tab = False):

		if not tab:
			seperator = ','
		else:
			seperator = '\t'

		# calculate the error to sort the precursor masses
		listSF = []
		for sf in self.listPrecurmassSF:
			tmp = -((sf.getWeight() - self.precurmass) / self.precurmass) * 1000000
			listSF.append((sf, tmp))
		listSF.sort(key = lambda x : x[1])

		if not tab:

			if self.isIsotope:
				strIsotope = '*'
			else:
				strIsotope = ' '

			if listSF != []:
				str = ("%s,%s,%.4f,%s," % (("%d" % self.polarity)[0], strIsotope, float(self.precurmass), "(%s; %.4f)" % (listSF[0][0], listSF[0][1]))).rjust(9)
			else:
				str = ("%s,%s,%.4f,%%," % (("%d" % self.polarity)[0], strIsotope, float(self.precurmass))).rjust(9)

			intensities = {}
			if not Debug("isotopesInMasterScan"):

				if self.dictBeforeIsocoIntensity != {}:
					intensities = self.dictBeforeIsocoIntensity

					#for i in sorted(self.dictBeforeIsocoIntensity.keys()):
					#	if self.dictMSMS.has_key(i):
					#		str = str + (" [%.1f]," % (float(self.dictBeforeIsocoIntensity[i]))).rjust(13)
					#	else:
					#		if not self.dictBeforeIsocoIntensity.has_key(i):
					#			str = str + ("  %.1f, " % (float(0.0))).rjust(13)
					#		else:
					#			if self.dictBeforeIsocoIntensity[i] == '-1':
					#				str += "  -1, "
					#			else:
					#				str = str + ("  %.1f, " % (float(self.dictBeforeIsocoIntensity[i]))).rjust(13)

				else:
					for i in sorted(self.dictIntensity.keys()):
						intensities = self.dictIntensity

						#if self.dictMSMS.has_key(i) and self.dictIntensity.has_key(i):
						#	str = str + (" [%.1f]," % (float(self.dictIntensity[i]))).rjust(13)
						#else:
						#	if not self.dictIntensity.has_key(i):
						#		str = str + ("  %.1f, " % (float(0.0))).rjust(13)
						#	else:
						#		if self.dictIntensity[i] == '-1':
						#			str += "  -1, "
						#		else:
						#			str = str + ("  %.1f, " % (float(self.dictIntensity[i]))).rjust(13)
			else:
				intensities = self.dictIntensity

				#for i in sorted(self.dictIntensity.keys()):
				#	if self.dictMSMS.has_key(i) and self.dictIntensity.has_key(i):
				#		str = str + (" [%.1f]," % (float(self.dictIntensity[i]))).rjust(13)
				#	else:
				#		if not self.dictIntensity.has_key(i):
				#			str = str + ("  %.1f, " % (float(0.0))).rjust(13)
				#		else:
				#			if self.dictIntensity[i] == '-1':
				#				str += "  -1, "
				#			else:
				#				str = str + ("  %.1f, " % (float(repr(self.dictIntensity[i])))).rjust(13)

			if Debug("relativeIntensity"):
				for sample in list(intensities.keys()):
					intensities[sample] /= self.dictBasePeakIntensity[sample]

			if Debug("relativeIntensity"):
				for i in sorted(intensities.keys()):
					if i in self.dictMSMS and i in intensities:
						str = str + (" [%.4f]," % (float(intensities[i]))).rjust(13)
					else:
						if i not in intensities:
							str = str + ("  %.4f, " % (float(0.0))).rjust(13)
						else:
							if intensities[i] == '-1':
								str += "  -1, "
							else:
								str = str + ("  %.4f, " % (float(repr(intensities[i])))).rjust(13)
			else:
				for i in sorted(intensities.keys()):
					if i in self.dictMSMS and i in intensities:
						str = str + (" [%.1f]," % (float(intensities[i]))).rjust(13)
					else:
						if i not in intensities:
							str = str + ("  %.1f, " % (float(0.0))).rjust(13)
						else:
							if intensities[i] == '-1':
								str += "  -1, "
							else:
								str = str + ("  %.1f, " % (float(repr(intensities[i])))).rjust(13)

			str += " %.4f, %.4f, %.4f, %.4f, %.4f," % \
				(self.massWindow, self.peakMean, self.peakMedian, self.variance, self.standardDeviation)

			for i in self.listMark:
				if i.chemsc:
					str += "%s:%s," % (i, i.chemsc)
				else:
					str += "%s," % i

			if len(listSF) > 1:
				for sf in listSF[1:]:
					str += ("\n%s, , ,%s," % (("%d" % self.polarity)[0], "(%s; %.4f)" % (sf[0], sf[1]))).rjust(9)

		else:

			if listSF != []:
				str = ("%s\t%.4f\t%s\t" % (("%d" % self.polarity)[0], float(self.precurmass), "(%s; %.4f)" % (listSF[0][0], listSF[0][1]))).rjust(9)
			else:
				str = ("%s\t%.4f\t%%\t" % (("%d" % self.polarity)[0], float(self.precurmass))).rjust(9)

			if self.dictBeforeIsocoIntensity != {}:

				for i in sorted(self.dictBeforeIsocoIntensity.keys()):
					if i in self.dictMSMS and i in self.dictBeforeIsocoIntensity:
						str = str + (" [%.1f]," % (float(self.dictBeforeIsocoIntensity[i]))).rjust(13)
					else:
						if i not in self.dictBeforeIsocoIntensity:
							str = str + ("  %.1f, " % (float(0.0))).rjust(13)
						else:
							if self.dictBeforeIsocoIntensity[i] == '-1':
								str += "  -1, "
							else:
								str = str + ("  %.1f, " % (float(self.dictBeforeIsocoIntensity[i]))).rjust(13)
							#str = str + ("  %6.4f, " % (float(self.dictIntensity[i]))).rjust(13)
			else:

				for i in sorted(self.dictIntensity.keys()):
					if i in self.dictMSMS and i in self.dictIntensity:
						str = str + (" [%.1f]," % (float(self.dictIntensity[i]))).rjust(13)
					else:
						if i not in self.dictIntensity:
							str = str + ("  %.1f, " % (float(0.0))).rjust(13)
						else:
							if self.dictIntensity[i] == '-1':
								str += "  -1, "
							else:
								str = str + ("  %.1f, " % (float(repr(self.dictIntensity[i])))).rjust(13)
							#str = str + ("  %6.4f, " % (float(self.dictIntensity[i]))).rjust(13)

			#if self.listSumform != None:
			#	for i in self.listSumform:
			#		str += repr(i) + ", "

			str += " %.4f\t %.4f\t %.4f\t %.4f\t %.4f\t" % \
				(self.massWindow, self.peakMean, self.peakMedian, self.variance, self.standardDeviation)

			for i in self.listMark:
				str += "%s\t" % i

			if len(listSF) > 1:
				for sf in listSF[1:]:
					str += ("\n%s\t \t%s\t" % (("%d" % self.polarity)[0], "(%s; %.4f)" % (sf[0], sf[1]))).rjust(9)

		return str

	def reprCSV_SQL(self, tab = False):

		if not tab:
			seperator = ','
		else:
			seperator = '\t'

		# calculate the error to sort the precursor masses
		listSF = []
		for sf in self.listPrecurmassSF:
			tmp = -((sf.getWeight() - self.precurmass) / self.precurmass) * 1000000
			listSF.append((sf, tmp))
		listSF.sort(cmp = lambda x,y : cmp(x[1], y[1]))

		if self.isIsotope:
			strIsotope = '*'
		else:
			strIsotope = ' '

		allLines = []

		# for every precursor sum composition one line
		for markMS in self.listMark:

			for msmse in self.listMSMS:

				for markMSMS in msmse.listMark:

					if markMS.encodedName.split('_')[0] == markMSMS.encodedName.split('_')[0]:

						str = ("%s&%s&%.4f&" % (("%d" % self.polarity)[0], strIsotope, float(self.precurmass))).rjust(9)

						if not Debug("isotopesInMasterScan"):

							if self.dictBeforeIsocoIntensity != {}:
								for i in sorted(self.dictBeforeIsocoIntensity.keys()):
									if i in self.dictMSMS:
										str = str + (" %.1f& " % (float(self.dictBeforeIsocoIntensity[i]))).rjust(13)
									else:
										if i not in self.dictBeforeIsocoIntensity:
											str = str + ("  %.1f& " % (float(0.0))).rjust(13)
										else:
											if self.dictBeforeIsocoIntensity[i] == '-1':
												str += "  -1& "
											else:
												str = str + ("%.1f& " % (float(self.dictBeforeIsocoIntensity[i]))).rjust(13)

							else:
								for i in sorted(self.dictIntensity.keys()):
									if i in self.dictMSMS and i in self.dictIntensity:
										str = str + (" %.1f&" % (float(self.dictIntensity[i]))).rjust(13)
									else:
										if i not in self.dictIntensity:
											str = str + ("  %.1f& " % (float(0.0))).rjust(13)
										else:
											if self.dictIntensity[i] == '-1':
												str += "  -1& "
											else:
												str = str + ("  %.1f& " % (float(self.dictIntensity[i]))).rjust(13)
						else:
							for i in sorted(self.dictIntensity.keys()):
								if i in self.dictMSMS and i in self.dictIntensity:
									str = str + (" [%.1f]&" % (float(self.dictIntensity[i]))).rjust(13)
								else:
									if i not in self.dictIntensity:
										str = str + ("  %.1f& " % (float(0.0))).rjust(13)
									else:
										if self.dictIntensity[i] == '-1':
											str += "  -1& "
										else:
											str = str + ("  %.1f& " % (float(repr(self.dictIntensity[i])))).rjust(13)

						error = -((markMS.chemsc.getWeight() - self.precurmass) / self.precurmass) * 1000000

						if markMS.chemsc:
							str += "%s&%s&%.2f&" % (markMS.encodedName.split('_')[0], markMS.chemsc, error)
						else:
							str += "%s&" % markMS

						# MSMS
						if not Debug("isotopesInMasterScan"):
							if msmse.dictBeforeIsocoIntensity != {}:
								for i in sortDictKeys(msmse.dictBeforeIsocoIntensity):
									str += (" %.1f, " % msmse.dictBeforeIsocoIntensity[i]).rjust(13)
							else:
								for i in sortDictKeys(msmse.dictIntensity):
									str += (" %.1f, " % msmse.dictIntensity[i]).rjust(13)
						else:
							for i in sortDictKeys(msmse.dictIntensity):
								str += (" %.1f, " % msmse.dictIntensity[i]).rjust(13)

						### include it later,... maybe
						#str += " %.4f& %.4f& %.4f& %.4f& %.4f&" % \
						#	(self.massWindow, self.peakMean, self.peakMedian, self.variance, self.standardDeviation)

						error = -((markMSMS.chemsc.getWeight() - msmse.mass) / msmse.mass) * 1000000

						if markMSMS.chemsc:
							str += "%.4f&%s&%.2f&%s&%s&" % (msmse.mass, markMSMS.encodedName.split('_')[1].split(':')[0], error, markMSMS.frsc, markMSMS.nlsc)
						else:
							str += "%s&" % markMSMS

						allLines.append(str.replace("&", seperator))

		return allLines

	def __cmp__(self, otherself):
		return cmp(self.precurmass, otherself.precurmass)

	def __getitem__(self, smpl):
		return self.listMSMS[smpl]

	def sortAndIndedice(self):

		self.listMSMS.sort()

		# generate indices
		for index in range(len(self.listMSMS)):
			self.listMSMS[index].index = index

	def isInQueryMS(self, query, sep):
		found = False
		for mark in self.listMark:
			if mark.encodedName.split(':')[0].split(sep)[0] == query.split(sep)[0]:
				found = True
		return found

	def getMarksMS(self):
		listOut = []
		for mark in self.listMark:
			listOut.append(mark.encodedName)
		return listOut

	def get_listMSMSEntryByMark(self, mark):
		l = []
		# they can be empty, exactly then, when there is no MSMS experiment
		#if self.listMSMS == []: raise "Empty entries"
		for i in self.listMSMS:
			if i.listMark != []:
				for j in i.listMark:
					if j == mark:
						l.append(i)
		return l

	def get_listMSMSEntryIfMarked(self):
		l = []
		# they can be empty, exactly then, when there is no MSMS experiment
		#if self.listMSMS == []: raise "Empty entries"
		for i in self.listMSMS:
			if i.listMark != []:
				l.append(i)
		return l

	def get_listFragmentsIfMarked(self):
		l = []
		# they can be empty, exactly then, when there is no MSMS experiment
		#if self.listMSMS == []: raise "Empty entries"
		for i in self.listMSMS:
			if i.listMark != []:
				l.append(i.listMark)
		return l

	def get_listFragmentsByMark(self, mark):
		"""Returns all Fragments which have <mark> at position x in the
Fragment name 'x:<mass>'.
		"""
		l = []
		# they can be empty, exactly then, when there is no MSMS experiment
		#if self.listMSMS == []: raise "Empty entries"
		for i in self.listMSMS:
			if i.listMark != []:
				for j in i.listMark:
					if mark.split(':')[0] == j.name.split(':')[0]:
						l.append(j)
		return l

	def get_listFragments(self, listMarks):
		"""IN: list of fragment names
			OUT: marked fragments.
		"""
		l = []
		# they can be empty, exactly then, when there is no MSMS experiment
		#if self.listMSMS == []: raise "Empty entries"
		for mark in listMarks:
			for i in self.listMSMS:
				if i.listMark != []:
					for j in i.listMark:
						if mark.split(':')[0] == j.name.split(':')[0]:
							l.append(j)
		return l


	def del_Sample(self, smpl):
		"""IN: the specific sample.
		OUT: if the Survey Entry is empty return False, else return True."""

		# delete the particular entries
		#if self.dictMsmass.has_key(smpl): del self.dictMsmass[smpl]
		if smpl in self.dictIntensity: del self.dictIntensity[smpl]
		if smpl in self.dictMSMS: del self.dictMSMS[smpl]

		# remove sample key
		#del self.listSmplKeys[self.listSmplKeys.index(smpl)]

		# look if the precurmass has no entries any more
		flag = False
		for i in self.listSamples:
			#if self.dictMsmass.has_key(i): flag = True
			if i in self.dictIntensity: flag = True
			if i in self.dictMSMS: flag = True

		return flag

	def insert(self, msmass, smpl, avgPreMasses = 1):

		# check if charge is right
		#assert self.polarity == self.sc.dictSamples[smpl].polarity

		# inserts a new intensity or a new precursor mass from a new sample, respectively
		self.dictIntensity[smpl] = msmass.intensity

		# generate avg precursormass
		if avgPreMasses == 1:
			self.precurmass = (self.precurmass + msmass.precurmass) / 2

	def assignMSMS(self, msms, smpl):
		if smpl not in self.dictMSMS:
			self.dictMSMS[smpl] = None
		self.dictMSMS[smpl] = msms

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
