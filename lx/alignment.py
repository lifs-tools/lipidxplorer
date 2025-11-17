from copy import deepcopy
from lx.clustering import HierarchicalClustering
from lx.mfql.runtimeStatic import TypeTolerance
from lx.spectraContainer import SurveyEntry, MSMS, MSMSEntry, MSMass, set_PrecurmassFromMSMS
from lx.tools import sortDictKeys
from lx.exceptions import LipidXException
from math import sqrt

# peakCluster for merging peaks
class peakCluster:

	def __init__(self, mass = None, dictIntensity = None,
			polarity = None, charge = None, dictScans = None):

		self.mass = mass
		self.dictIntensity = dictIntensity
		self.charge = charge
		self.polarity = polarity
		self.peakList = []
		self.dictScans = dictScans

	def __repr__(self):
		return repr(self.mass) + ' \n -> ' + repr(self.peakList)

	def __cmp__(self, other):
		return cmp(self.mass, other.mass)


	#def findPeak(self, mass = None, key = None):
	def findPeak(self, key = None):
		""" Find and return a the peak with the given sample
		name (key) from the peakList."""

		if key:
			for i in self.peakList:
				for k in list(i[1].keys()):
					if k == key:
						return i
			return None

class specMSMSEntry:

	def __init__(self, precurmass, listMSMS, scanCount = 1):
		self.precurmass = precurmass
		self.listMSMS = listMSMS
		self.scanCount = scanCount

	def __repr__(self):
		return "%.4f -> %s" % (self.precurmass, repr(self.listMSMS))

	def __cmp__(self, other):
		return cmp(self.precurmass, other.precurmass)

class specMSEntry:

	def __init__(self, avgPrecurmass, sample, listMSMS):
		self.avgPrecurmass = avgPrecurmass
		#self.dictSample = {sample : listMSMS}
		self.listMasses = [[avgPrecurmass, {sample : listMSMS}]]

	def __cmp__(self, other):
		return cmp(self.avgPrecurmass, other.avgPrecurmass)

	def __repr__(self):
		str = "%.4f -> " % (self.avgPrecurmass)
		for i in self.listMasses:
			str += "%s, " % list(i[1].keys())
		return str + '\n'


def printClusters(keys, listClusters):
	"""This is for debugging the alignment functions. It
	just prints the resulting alignment."""

	for cl in listClusters:
		str = ''
		for sample in keys:
			if sample in cl:
				if cl[sample].content:
					str +=  "  {0:>9.4f} - {1:>12.1f}  ".format(cl[sample].mass, cl[sample].content['intensity'])
					#str +=  "  %.4f  " % cl[sample].content['intensity']
				else:
					try:
						str +=  " /{0:>9.4f} - {1:>12}/ ".format(cl[sample].mass, '')
					except TypeError:
						print("TypeError:", cl[sample].mass)
			else:
				str +=  " /{0:>9} - {1:>12}/ ".format('empty', '')
		print(str)

def avgPrecursor(content):

	precurmass = 0
	msms = []
	entries = []
	numEntries = 0
	for entry in content:
		precurmass += entry.precurmass
		msms += entry.msms
		entries += entry.entries
		numEntries += 1

	avgPrecurmass = precurmass / len(content)

	#def __init__(self, mass, retentionTime, charge, polarity, fileName, MSMSthreshold = None, table = None):
	output = MSMS(
		avgPrecurmass,
		0.0,
		None,
		content[0].polarity,
		content[0].fileName)

	return output

def avgMSMSFragment(content):

	intensity = 0
	for entry in content:
		intensity += entry['intensity']

	avgIntensity = intensity / len(content)

	output = {'intensity' : avgIntensity, 'polarity' : content[0]['polarity']}

	return output

class specEntry:

	def __init__(self, mass = None, content = {}, charge = None, sample = None):
		self.mass = mass
		self.content = content
		self.sample = sample
		self.charge = charge

	def __repr__(self):
		str = "{0:6}".format(self.mass)
		for k in list(self.content.keys()):
			str += " > {0:12}: {1:6}".format(k, self.content[k])
		return str

	def __cmp__(self, other):
		return cmp(self.mass, other.mass)


def mkSurveyLinear(sc, listPolarity, numLoops = None, deltaRes = 0, minocc = None, checkoccupation = True):
	""" Align the MS spectra."""

	# get the base peak dictionary
	dictBasePeakIntensity_MS = {}
	for sample in sc.listSamples:
		dictBasePeakIntensity_MS[sample] = sc.dictSamples[sample].base_peak_ms1
	sc.dictBasePeakIntensity_MS = dictBasePeakIntensity_MS


	# store smalles mass
	if sc.options['MSmassrange']:
		minMass = sc.options['MSmassrange'][0]
		maxMass = sc.options['MSmassrange'][1]
	else:
		minMass = 0
		maxMass = 100000


	for polarity in listPolarity:

		### generate list of all MSmasses ###

		# initialize listMSSpec
		listMSSpec = []
		for i in range(numLoops + 1):
			listMSSpec.append([])

		for key in sc.dictSamples:
			if sc.dictSamples[key].polarity == polarity:
				for i in sc.dictSamples[key].listPrecurmass:
					if i.precurmass >= minMass and i.precurmass <= maxMass:
						listMSSpec[0].append(peakCluster(
							mass = i.precurmass,
							dictIntensity = {i.smpl : i.intensity},
							charge = i.charge,
							polarity = polarity,
							dictScans = {i.smpl : i.scanCount}))
						listMSSpec[0][-1].peakList.append([i.precurmass, {i.smpl : i.intensity}])


		# if no mass found for a given charge, continues
		if listMSSpec[0] == []:
			continue

		if len(listMSSpec[0]) == 1:

			entry = listMSSpec[0][0]

			for k in sc.listSamples:
				if not k in entry.dictIntensity:
					entry.dictIntensity[k] = 0.0
				if not k in entry.dictScans:
					entry.dictScans[k] = 1

			if checkoccupation:
				checkOcc = sc.checkOccupation(
						entry.dictIntensity,
						entry.dictScans,
						occThr = sc.options['MSminOccupation'],
						mode = 'MS',
						dictBasePeakIntensity = sc.dictBasePeakIntensity_MS,
						threshold = sc.options['MSthreshold'],
						threshold_type = sc.options['MSthresholdType'])

				if checkOcc:
					sc.listSurveyEntry.append(SurveyEntry(
						msmass = entry.mass,
						smpl = entry.dictIntensity,
						peaks = entry.peakList,
						charge = None,
						polarity = polarity,
						dictScans = entry.dictScans,
						dictBasePeakIntensity = sc.dictBasePeakIntensity_MS))

			else:
				sc.listSurveyEntry.append(SurveyEntry(
					msmass = entry.mass,
					smpl = entry.dictIntensity,
					peaks = entry.peakList,
					charge = None,
					polarity = polarity,
					dictScans = entry.dictScans,
					dictBasePeakIntensity = sc.dictBasePeakIntensity_MS))

			return True

		#listMSSpec[0].sort()
		listMSSpec[0].sort(key=lambda pc: pc.mass) ## Ballal
  
		# sort precursor masses by intensity
		#listMSmassIntensity = sorted(listMSmass, cmp = sortPrecursorMasses)
		# TODO: do alignment according to sorted list by intensity

		for count in range(numLoops):

			current = 0
			lnext = []

			while current < (len(listMSSpec[count]) - 1):

				# calc mass window for cluster
				if sc.options['MSresolution'].kind != 'Da':
					res = sc.options['MSresolution'].tolerance + (listMSSpec[count][current].mass - minMass) * deltaRes
					#res = sc.options['MSresolution'].getTinDA(listMSSpec[count][current].mass
				else:
					raise LipidXException("Tolerance value for averaging MS has to be resolution")

				partialRes = (listMSSpec[count][current].mass / res)

				# routine for collecting all masses which are in partialRes
				#index = 1
				lrsltMSMS = [listMSSpec[count][current]]

				# instead of counting with 'current' we just delete the peak which is
				# in the bin from the spectra list. Thus we save some space.
				del listMSSpec[count][current]

				lastEntry = None
				while listMSSpec[count][current].mass - lrsltMSMS[0].mass < partialRes:
					lrsltMSMS.append(listMSSpec[count][current])
					del listMSSpec[count][current]

					if listMSSpec[count] == []:
						lastEntry = lrsltMSMS[-1]
						break


				# calc average of cluster
				sum = 0
				avg = 0
				length = 0
				for i in lrsltMSMS:
					for j in i.peakList:
						sum += j[0]
						length += 1
				avg = sum / length

				# calc average of count
				#sum = 0
				#for i in lrsltMSMS:
				#	sum += i.count
				#avgCount = sum / len(lrsltMSMS)

				# collect the cluster masses intensities
				dictIntensity = {}
				countIntensity = {}
				dictScans = {}
				for i in lrsltMSMS:
					for k in list(i.dictIntensity.keys()):

						if k not in countIntensity:
							countIntensity[k] = 1
						else:
							countIntensity[k] += 1

				### TODO: Attention, the method of just summing the
				### intensities for "too-close" peaks in on sample lead to
				### strong differences in the result (at least the unit test does
				### not accept the result). This has be checked and confirmed.
						if k not in dictIntensity:
							dictIntensity[k] = i.dictIntensity[k]
						else:
							dictIntensity[k] += i.dictIntensity[k]

						if k not in dictScans:
							dictScans[k] = i.dictScans[k]

					## take average intensity
					#for k in i.dictIntensity.keys():
					#	dictIntensity[k] = dictIntensity[k] / countIntensity[k]

				# is it not the last round?
				if count != numLoops - 1:

					# store list for a maybe second round
					#for intensKey in dictIntensity.keys():
					listMSSpec[count + 1].append(peakCluster(mass = avg, dictIntensity = dictIntensity,
						polarity = polarity, charge = None, dictScans = dictScans))
					for e in lrsltMSMS:
						for p in e.peakList:
							if len(list(p[1].keys())) < 2 and not listMSSpec[count + 1][-1].findPeak(key = list(p[1].keys())[0]):
								listMSSpec[count + 1][-1].peakList.append(p)

					#if current == len(listMSSpec[count]) - 1:
					#if listMSSpec[count] == []:
					if not lastEntry is None:
						# store last for a maybe second round
						#for intensKey in dictIntensity.keys():
						if not lastEntry in lrsltMSMS:
							listMSSpec[count + 1].append(peakCluster(
								mass = lastEntry.mass,
								dictIntensity = lastEntry.dictIntensity,
								charge = None,
								polarity = polarity,
								dictScans = lastEntry.dictScans))
							listMSSpec[count + 1][-1].peakList = lastEntry.peakList


					else:
						for e in lrsltMSMS:
							for p in e.peakList:
								if len(list(p[1].keys())) < 2 and not listMSSpec[count + 1][-1].findPeak(key = list(p[1].keys())[0]):
									listMSSpec[count + 1][-1].peakList.append(p)

				# it is the last round
				else:
					listMSSpec[count + 1].append(peakCluster(
						mass = avg,
						dictIntensity = dictIntensity,
						charge = None,
						polarity = polarity,
						dictScans = dictScans))

					for e in lrsltMSMS:
						for p in e.peakList:
							# only add peaks which are not aligned
							if len(list(p[1].keys())) < 2 and not listMSSpec[count + 1][-1].findPeak(key = list(p[1].keys())[0]):
								listMSSpec[count + 1][-1].peakList.append(p)

					if current == len(listMSSpec[count]) - 1:
						# store last for a maybe second round
						#for intensKey in dictIntensity.keys():
						if not listMSSpec[count][current] in lrsltMSMS:
							if listMSSpec[count + 1][-1].mass != listMSSpec[count][-1].mass:
								listMSSpec[count + 1].append(peakCluster(
									mass = listMSSpec[count][-1].mass,
									dictIntensity = listMSSpec[count][-1].dictIntensity,
									charge = None,
									polarity = polarity,
									dictScans = listMSSpec[count][-1].dictScans))
								listMSSpec[count + 1][-1].peakList = listMSSpec[count][-1].peakList

					else:
						for e in lrsltMSMS:
							for p in e.peakList:
								if len(list(p[1].keys())) < 2 and not listMSSpec[count + 1][-1].findPeak(key = list(p[1].keys())[0]):
									listMSSpec[count + 1][-1].peakList.append(p)

					# assert that every peak has the right distance to its predesessor
					#if len(listMSSpec[count + 1]) > 1:
					#	assert listMSSpec[count + 1][-1].mass - listMSSpec[count + 1][-2].mass >= partialRes


		### check if minimum occupation is fullfilled ###

		for entry in listMSSpec[-1]:

			for k in sc.listSamples:
				if not k in entry.dictIntensity:
					entry.dictIntensity[k] = 0.0
				if not k in entry.dictScans:
					entry.dictScans[k] = 1

			if checkoccupation:
				checkOcc = sc.checkOccupation(
						entry.dictIntensity,
						entry.dictScans,
						occThr = sc.options['MSminOccupation'],
						mode = 'MS',
						dictBasePeakIntensity = sc.dictBasePeakIntensity_MS,
						threshold = sc.options['MSthreshold'],
						threshold_type = sc.options['MSthresholdType'])

				if checkOcc:
					sc.listSurveyEntry.append(SurveyEntry(
						msmass = entry.mass,
						smpl = entry.dictIntensity,
						peaks = entry.peakList,
						charge = None,
						polarity = polarity,
						dictScans = entry.dictScans,
						dictBasePeakIntensity = sc.dictBasePeakIntensity_MS))

			else:
				sc.listSurveyEntry.append(SurveyEntry(
					msmass = entry.mass,
					smpl = entry.dictIntensity,
					peaks = entry.peakList,
					charge = None,
					polarity = polarity,
					dictScans = entry.dictScans,
					dictBasePeakIntensity = sc.dictBasePeakIntensity_MS))

		del listMSSpec



def mkMSMSEntriesLinear_new(scan, listPolarity, numLoops = None, isPIS = False, relative = None):

	################################################################
	###	merge MS/MS experiments if there are more than one for a ###
	### precursor mass                                           ###
	################################################################

	secondStep = True
	numLoops = 3

	msmsThreshold = scan.options['MSMSthreshold']
	if not isPIS:
		tolerance = TypeTolerance('Da', scan.options['selectionWindow'])
		#tolerance = scan.options['MSresolution']
		window = scan.options['selectionWindow'] / 2
		deltaRes = None
	else:
		tolerance = scan.options['MSMSresolution']
		deltaRes = scan.options['MSMSresolutionDelta']
		window = scan.options['MSMSresolution']

	listPolarity = []
	for k in scan.listSamples:
		if scan.dictSamples[k].polarity not in listPolarity:
			listPolarity.append(scan.dictSamples[k].polarity)

	# check if there are MS/MS spectra at all
	msmsThere = False
	for polarity in listPolarity:
		for sample in scan.listSamples:
			# TODO: This has to be tested ASAP
			if scan.dictSamples[sample].listMsms != []\
					and scan.dictSamples[sample].polarity == polarity:
				msmsThere = True

	# double check if the MSMSresolution was set
	if msmsThere:
		if not scan.options['MSMSresolution'] or scan.options['MSMSresolution'] == 0:
			raise LipidXException("no resolution setting given for MS/MS.")

		if not scan.options['selectionWindow'] or scan.options['selectionWindow'] == 0:
			raise LipidXException("no selection window given.")

	### go seperately for the polarity ###
	for polarity in listPolarity:


		############################################################
		### Cluster the precursor masses and average MS/MS scans ###

		dictMSMS = {}
		listAt = []

		dictSpecEntry = {}

		for sample in scan.listSamples:

			if msmsThere:

				# generate a list of specEntry elements
				dictSpecEntry[sample] = []
				scan.dictSamples[sample].listMsms.sort(key=lambda x: x.precurmass)
				for i in scan.dictSamples[sample].listMsms:
					dictSpecEntry[sample].append(specEntry(
						mass = i.precurmass,
						content = {'sample' : sample, 'MSMS' : i}))

		if msmsThere:

			listClusters = linearAlignment(list(dictSpecEntry.keys()),
								dictSpecEntry,
								tolerance,
								merge = mergeListMsms,
								mergeTolerance = scan.options['MSMSresolution'],
								mergeDeltaRes = scan.options['MSMSresolutionDelta'])

		else:
			listClusters = False

		### Cluster the precursor masses and average MS/MS scans ###
		############################################################

		if listClusters:

			##################################################################
			### align all the MS/MS masses for each precursor mass cluster ###

			alignedMSMS = []
			msmsLists = {}
			for cl in listClusters:
				sum = 0
				for sample in list(cl.keys()):
					sum += cl[sample].mass
				if cl != {}:
					avgPrecursorMass = sum / len(list(cl.keys()))

					# the standard data format for alignment functions
					dictSpecEntry = {}

					# collect the base peaks of the merged spectra
					dictBasePeakIntensity = {}

					for sample in list(cl.keys()):
						dictBasePeakIntensity[sample] = 0

						if cl[sample].content:
							dictSpecEntry[sample] = []

							p = cl[sample].content['MSMS'].polarity

							# find base peak
							for msmsEntry in cl[sample].content['MSMS'].entries:
								if msmsEntry[1] > dictBasePeakIntensity[sample]:
									dictBasePeakIntensity[sample] = msmsEntry[1]

							# collect MS/MS entries for specEntry
							for msmsEntry in cl[sample].content['MSMS'].entries:

								# check if the threshold setting fits encompassing the scanCount
								# this is the first check for the threshold. Later when the MS/MS
								# were aligned and should be put into MSMSEntries, we'll check
								# the threshold again combined with the occupation threshold
								aboveThreshold = False
								if scan.options['MSMSthresholdType'] == 'relative':
									if msmsEntry[1] >= (dictBasePeakIntensity[sample] * scan.options['MSMSthreshold'])\
											/ sqrt(cl[sample].content['MSMS'].scanCount):
										aboveThreshold = True
								else:
									if msmsEntry[1] >= scan.options['MSMSthreshold'] / sqrt(cl[sample].content['MSMS'].scanCount):
										aboveThreshold = True

								if aboveThreshold:
									# mk a specEntry for the alignment function
									dictSpecEntry[sample].append(specEntry(
										mass = msmsEntry[0],
										content = {'sample' : sample, 'intensity' : msmsEntry[1],
											'polarity': p,
											'scanCount' : cl[sample].content['MSMS'].scanCount,
											'peak_info' : msmsEntry[3:]}))

					# do the clustering for the alignment
					#print("do the clustering for the MSMS alignment - linearAlignment called")
					cluster = linearAlignment(list(dictSpecEntry.keys()),
												dictSpecEntry,
												scan.options['MSMSresolution'],
												deltaRes = scan.options['MSMSresolutionDelta'],
												minMass = scan.options['MSMSmassrange'][0]
												)


					# generate MSMSEntry with the dedicated intensities
					if cluster:
						for i in cluster:

							# check for the occupation of every fragment
							numSmpl = len(scan.listSamples)
							numOccSmpl = 0
							isEmpty = True
							dictIntensity = {}
							dictScanCount = {}
							peakList = []
							sum = 0

							for sample in scan.listSamples:
								try:
									if i[sample].content:
										numOccSmpl += 1
										dictIntensity[sample] = i[sample].content['intensity']
										dictScanCount[sample] = i[sample].content['scanCount']
										peakList.append([i[sample].mass, {sample : i[sample].content['intensity']}])
										isEmpty = False
										sum += i[sample].mass
									else:
										dictIntensity[sample] = 0.0
										dictScanCount[sample] = 1

								except KeyError:
									dictIntensity[sample] = 0.0
									dictScanCount[sample] = 1

							avgMass = sum / numOccSmpl

							if not isEmpty:
								if scan.checkOccupation(
										dictIntensity,
										dictScanCount,
										occThr = scan.options['MSMSminOccupation'],
										mode = 'MSMS',
										dictBasePeakIntensity = dictBasePeakIntensity,
										threshold = scan.options['MSMSthreshold'],
										threshold_type = scan.options['MSMSthresholdType']):

									if "%.6f" % avgPrecursorMass not in msmsLists:
										msmsLists["%.6f" % avgPrecursorMass] = []

									msmsLists["%.6f" % avgPrecursorMass].append(
										MSMSEntry(
											mass = avgMass,
											dictIntensity = dictIntensity,
											peaks = peakList,
											polarity = polarity,
											charge = None,
											se = None,
											samples = scan.listSamples,
											dictScanCount = dictScanCount,
											dictBasePeakIntensity = dictBasePeakIntensity))


			### align all the MS/MS masses for each precursor mass cluster ###
			##################################################################


			###################################
			### Start association algorithm ###

			if msmsLists != {}:

				print("Associate MSMSEntry objects to the according SurveyEntry objects (precursor masses)")

				# now listAvg is the basis for assigning the dta data to their
				# survey precurmass

				listSECharge = []
				for se in scan.listSurveyEntry:
					if se.polarity == polarity:
						listSECharge.append(se)

				if listSECharge != []:

					listSurveyEntry = listSECharge

					#iterEntry = sorted(listSECharge, lambda x,y: cmp(x.precurmass, y.precurmass)).__iter__()
					iterEntry = iter(sorted(listSECharge, key=lambda x: x.precurmass)) # Ballal


					iterListAvg = sortDictKeys(adict = msmsLists, compare = 'float').__iter__()

					listSEcurrentAvg = []
					listSEnextAvg = []
					onlyOneMSMS = False

					try:
						currentAvg = next(iterListAvg)
					except StopIteration:
						print("No MS/MS spectra after the averaging!")
						break

					try:
						nextAvg = next(iterListAvg)
					except StopIteration:
						onlyOneMSMS = True

					if not onlyOneMSMS:

						while iterListAvg:

							# calc window if a PIS is given
							if isPIS:
								window = tolerance.getTinDA(float(currentAvg))

							# is the following precursor mass overlapping with the current?
							if float(currentAvg) + window > float(nextAvg):# - window:
								listSE = []
								for se in listSurveyEntry:
									if float(currentAvg) - window < se.precurmass and se.precurmass < float(nextAvg) + window:
										listSE.append(se)

									# stop for loop, when masses get too big
									if float(nextAvg) + window < se.precurmass:
										break

								for j in range(len(listSE)):
									ni = abs(listSE[j].precurmass - float(currentAvg))
									niplus1 = abs(listSE[j].precurmass - float(nextAvg))
									if ni < niplus1:
										for se in scan.get_SurveyEntry(listSE[j].precurmass, listSE[j].polarity):
											se.listMSMS = msmsLists[currentAvg]
											for msmsentry in se.listMSMS:
												if isinstance(se, SurveyEntry):
													msmsentry.se.append(se)
												else:
													print("Error with SurveyEntry", se, " -> is no SurveyEntry")
													exit(0)
									else:
										for se in scan.get_SurveyEntry(listSE[j].precurmass, listSE[j].polarity):
											se.listMSMS = msmsLists[nextAvg]
											for msmsentry in se.listMSMS:
												if isinstance(se, SurveyEntry):
													msmsentry.se.append(se)
												else:
													print("Error with SurveyEntry", se, " -> is no SurveyEntry")
													exit(0)

							else:
								for se in listSurveyEntry:
									if float(currentAvg) - window < se.precurmass and se.precurmass < float(currentAvg) + window:
										se.listMSMS = msmsLists[currentAvg]
										for msmsentry in se.listMSMS:
											if isinstance(se, SurveyEntry):
												msmsentry.se.append(se)
											else:
												print("Error with SurveyEntry", se, " -> is no SurveyEntry")
												exit(0)

									# stop for loop, when masses get too big
									if float(nextAvg) + window < se.precurmass:
										break

							currentAvg = nextAvg
							try:
								nextAvg = next(iterListAvg)
							except StopIteration:
								for se in listSurveyEntry:
									if float(currentAvg) - window < se.precurmass and se.precurmass < float(currentAvg) + window:
										se.listMSMS = msmsLists[currentAvg]
										for msmsentry in se.listMSMS:
											msmsentry.se.append(se)

									# stop for loop, when masses get too big
									if float(nextAvg) + window < se.precurmass:
										break
								break

					else: # just one MS/MS spectrum present
						for se in listSurveyEntry:
							if float(currentAvg) - window < se.precurmass and se.precurmass < float(currentAvg) + window:
								se.listMSMS = msmsLists[currentAvg]
								for msmsentry in se.listMSMS:
									if isinstance(se, SurveyEntry):
										msmsentry.se.append(se)
									else:
										print("Error with SurveyEntry", se, " -> is no SurveyEntry")
										exit(0)

			else:
				print("No MS/MS spectra present")

				### End association algorithm ###
				###################################

	for i in scan.listSamples:
		if i in scan.dictSamples: # TODO: listSamples should actually be same as scan.dictSamples.keys()
			del scan.dictSamples[i]



############ ballal edited it ############

from collections import defaultdict

def linearAlignment(
    listSamples,
    dictSamples,
    tolerance,
    merge=None, mergeTolerance=None, mergeDeltaRes=None,
    charge=None, deltaRes=None, minocc=None, msThreshold=None,
    intensityWeightedAvg=False, minMass=None,
    fadi_denominator=None, fadi_percentage=0.0
):
    """
    #using fadi_denominator, fadi_percentage, becayse nbofscans and msthreshold variables are already in use !!!
	# these varuables are used to implement fadi filter
	
	This is the standard algorithm to align spectra. It is published
	in [...].

	It is optimized for the available data structures. Therefore the input
	is an own format (specEntry) provided as list in listSamples. Furthermore,
	dictSamples: is the list of all sample names (keys from dict)
	tolerance: is a TypeTolerance type with the
		tolerance as da, ppm or res.
	deltaRes: if the tolerance is given as resolution, the deltaRes
		states the resolution change over the masses.

	The output is a list of specEntry
	that can be "filtered" as per DS
    """

    # -----------------------------
    # 1) Compute max spectrum length
    # -----------------------------
    speclen = 0
    for k in listSamples:
        if speclen < len(dictSamples[k]):
            speclen = len(dictSamples[k])

    if speclen < 1:
        return None

    # -----------------------------
    # 2) Single-fragment shortcut
    # -----------------------------
    mass = None
    if speclen == 1:
        cluster = {}
        for sample in listSamples:
            try:
                mass = dictSamples[sample][0].mass
                cluster[sample] = specEntry(
                    mass=dictSamples[sample][0].mass,
                    content=dictSamples[sample][0].content,
                    charge=dictSamples[sample][0].charge
                )
            except IndexError:
                if mass:
                    cluster[sample] = specEntry(
                        mass=mass,
                        content=None,
                        charge=None
                    )
                else:
                    # search any other sample for a mass (Python 2 behavior)
                    for s in listSamples:
                        try:
                            mass = dictSamples[s][0].mass
                        except IndexError:
                            pass
                    if mass:
                        cluster[sample] = specEntry(
                            mass=mass,
                            content=None,
                            charge=None
                        )
                    else:
                        return None
        return [cluster]

# start the algorithm

    # -----------------------------
    # initialize merging algorithm
    # 3) Initialize merging structure
    # -----------------------------
    numLoops = 3
    listResult = [[] for _ in range(numLoops + 1)]

    # Join all peaks into listResult[0] as [mass, [specEntry]]
    for sample in listSamples:
        for idx in range(len(dictSamples[sample])):
            entry = dictSamples[sample][idx]
            listResult[0].append([entry.mass, [entry]])

    # Sort by mass (equivalent to the Python 2 implicit sort on first element)
    listResult[0].sort(key=lambda x: x[0])

    # -----------------------------
    # 4) Merging loops (binning)
    # -----------------------------
    for count in range(numLoops):
        current = 0

        # If there is nothing to merge, carry forward and stop (Python 2 logic)
        if not current < (len(listResult[count]) - 1):
            listResult[-1] = listResult[count]
            break

        # Iterate until the penultimate element (Python 2 loop bounds)
        while current < (len(listResult[count]) - 1):
            # Collect all masses within the window anchored at the FIRST item of the bin
            index = 1
            bin_list = [listResult[count][current]]

            # Window size calculation: Da vs "resolution-like" (Python 2 behavior)
            if isinstance(tolerance, TypeTolerance):
                if tolerance.kind == 'Da':
                    res = tolerance.da
                else:
                    if deltaRes:
                        tmp = tolerance.tolerance + (listResult[count][current][0] - minMass) * deltaRes
                    else:
                        tmp = tolerance.tolerance
                    # Python 2 guard for rare zero after drift
                    if tmp == 0.0:
                        tmp = tolerance.tolerance
                    # resolution-like: Δm ≈ m / R
                    res = (listResult[count][current][0] / tmp)
            else:
                raise LipidXException("The given tolerance is not of TypeTolerance()")

            # Grow bin while next_mass - FIRST_BIN_MASS < res  (Python 2 anchoring)
            while (listResult[count][current + index][0] - bin_list[0][0]) < res:
                bin_list.append(listResult[count][current + index])
                if (current + index) < (len(listResult[count]) - 1):
                    index += 1
                else:
                    break

            current += index
            
            # go for intensity weighted average and non-weighted avg
            # -----------------------------
            # 5) Average mass in the bin
            # -----------------------------
            if not intensityWeightedAvg:
                cnt = 0
                s = 0.0
                for pair in bin_list:
                    for specentry in pair[1]:
                        s += specentry.mass
                        cnt += 1
                avg = s / float(cnt)
            else:
                cnt = 0
                sumMass = 0.0
                sumIntensity = 0.0
                for pair in bin_list:
                    for specentry in pair[1]:
                        # Match Python 2: direct dict access; assumes key exists
                        sumMass += specentry.mass * specentry.content['intensity']
                        sumIntensity += specentry.content['intensity']
                        cnt += 1
                if sumIntensity == 0:
                    raise LipidXException(
                        "A peak intensity is zero. This should not be."
                        " Probably you imported profile spectra instead of centroided."
                    )
                avg = sumMass / float(sumIntensity)

            # Flatten entries in the bin
            resultingSpecEntries = []
            for pair in bin_list:
                resultingSpecEntries += pair[1]

            # -----------------------------
            # 6) FADI filtering 
            # ------------------------------
############################## Balla ##################################
            # Python 2 default is 0.0; if None is explicitly passed, normalize to 0.0, 
            if fadi_percentage is None:
                print("NOTE: fadi_percentage is None at entry; normalizing to 0.0")
                fadi_percentage = 0.0
#############################################################
            # Python 2 uses 'cnt' (entries counted during averaging), not len(flat)
            if fadi_denominator is not None and fadi_denominator > 0.0:
                fadi_ratio = cnt / float(fadi_denominator)
            else:
                fadi_ratio = 1.0

            if fadi_ratio >= fadi_percentage:
                listResult[count + 1].append([avg, resultingSpecEntries])

            # Tail carry-over (Python 2 behavior)
            if listResult[count][current] == listResult[count][-1]:
                if listResult[count][current] not in bin_list:
                    listResult[count + 1].append([
                        listResult[count][current][0],
                        listResult[count][current][1]
                    ])

    # -----------------------------
    # 7) Build listOutput (clusters)
    # -----------------------------
    listOutput = []
    for entry in listResult[-1]:
        cluster = {}
        clusterToMerge = {}
        mass = None

        # entry[1] contains merged specEntries
        for i in entry[1]:
            mass = i.mass  # store any mass to reuse below
            sample_name = i.content['sample']

            if sample_name not in cluster:
                cluster[sample_name] = i
                if merge:
                    clusterToMerge[sample_name] = [i]
            else:
                if merge:
                    clusterToMerge[sample_name].append(i)

        # Merge duplicates for a sample if requested
        if merge:
            for sample in listSamples:
                if sample in clusterToMerge:
                    if len(clusterToMerge[sample]) > 1:
                        cluster[sample] = merge(sample, clusterToMerge[sample],
                                                linearAlignment, mergeTolerance, mergeDeltaRes)
                    else:
                        cluster[sample] = clusterToMerge[sample][0]

        # Fill missing samples with the FIRST ENTRY'S MASS of this bin
        # (not the average) — this matches Python 2 behavior exactly.
        for sample in listSamples:
            if sample not in cluster:
                cluster[sample] = specEntry(
                    mass=entry[1][0].mass
                )

        listOutput.append(cluster)

    return listOutput


###########################


def mergeListMsms(sample, listSpecEntries, align, mergeTolerance, mergeDeltaRes):
	'''Merge several MS/MS scans. The specEntries have the precursor mass and
	the MS/MS lists in their .content attribute.

	This is the averaging algorithm for MS/MS spectra. The "mergeTolerance" is
	misleading, because this is actually the MSMSresolution.'''



	length = len(listSpecEntries)

	out = listSpecEntries[0]
	outMSMS = listSpecEntries[0].content['MSMS']
	#right = specEntryRight.content['MSMS']

	### first: put the MS/MS lists together in a new specEntry ###

	sumMass = 0
	sumPrecurmass = 0
	listScanNumber = []
	listRetentionTime = []
	listPeaksCount = []
	listTotIonCurrent = []
	listFileName = []
	sumEntries = []
	sumScanCount = 0
	for entry in listSpecEntries:
		sumMass += entry.mass

		e = entry.content['MSMS']
		sumPrecurmass += e.precurmass
		listScanNumber.append(e.scanNumber)
		listRetentionTime.append(e.retentionTime)
		listPeaksCount.append(e.peaksCount)
		listTotIonCurrent.append(e.totIonCurrent)
		listFileName.append(e.fileName)
		sumEntries += e.entries
		sumScanCount += e.scanCount

	out.mass = sumMass / length
	outMSMS.precurmass = sumPrecurmass / length
	outMSMS.scanNumber = listScanNumber
	outMSMS.retentionTime = listRetentionTime
	outMSMS.peaksCount = listPeaksCount
	outMSMS.totIonCurrent = listTotIonCurrent
	outMSMS.entries = sumEntries
	outMSMS.scanCount = sumScanCount

	# TODO: assert charge and polarity are the same
	#if not left.charge == right.charge:
	#	return None
	#if not left.polarity == right.polarity:
	#	return None
	#left.msms = []
	#left.entries = [[] for i in range(0,2)]

	####################################
	### averaging of the MS/MS scans ###

	# make a new specEntries dict for the averaging algorithm
	dictSpecEntries = {'one' : []}
	for entry in outMSMS.entries:
		dictSpecEntries['one'].append(specEntry(
			mass = entry[0],
			content = {'sample' : 'one', 'intensity' : entry[1],
				'peak_info' : entry[2:]}))

	# start the averaging algorithm
	from . import readSpectra
	fadi_percentageMSMS = readSpectra.fadi_percentageMSMS
	if dictSpecEntries['one'] != []:
		if align != linearAlignment:
			raise NotImplementedError('This filtering has only been implemented for linear alignment, for heuristic please contact FAM')

		listClusters = align(['one'], dictSpecEntries, mergeTolerance,
				intensityWeightedAvg = True, merge = mergeSumIntensity,
				deltaRes = mergeDeltaRes, minMass = sorted(dictSpecEntries['one'], key=lambda x: x.mass)[0].mass, fadi_denominator = length, fadi_percentage = fadi_percentageMSMS)

		#for cl in listClusters:
		#	str = ''
		#	for sample in dictSpecEntries.keys():#cl.keys():
		#		if cl.has_key(sample):
		#			if cl[sample].content:
		#				str +=  "  %.4f  " % cl[sample].mass
		#				#str +=  "  %.4f  " % cl[sample].content['intensity']
		#			else:
		#				try:
		#					str +=  " /%.4f/ " % cl[sample].mass
		#				except TypeError:
		#					print "TypeError:", cl[sample].mass
		#		else:
		#			str += " / empty  / "
		#	print str

		# put the resulting list to the output specEntry
		listEntries = []
		for cl in listClusters:
			entry = [[],[]]
			entry[0] = cl['one'].mass
			entry[1] = cl['one'].content['intensity']
			for e in cl['one'].content['peak_info']:
				entry.append(e)
			listEntries.append(entry)
		listSpecEntries[0].content['MSMS'].entries = listEntries

	else: # there were no entries summed in outMSMS.entries
		pass

	### averaging of the MS/MS scans ###
	####################################

	return listSpecEntries[0]

def mergeSumIntensity(sample, listSpecEntries, align, mergeTolerance, mergeDeltaRes):
	'''This function calculates the average intensity (average over the given
	peaks and not from all scans) and the average weighted m/z for the peak mass.'''

	out = listSpecEntries[0]

	sumMass = 0
	sumMassIntensity = 0
	sumIntensity = 0
	for entry in listSpecEntries:
		sumMass += entry.mass
		sumMassIntensity += entry.mass * entry.content['intensity']
		sumIntensity += entry.content['intensity']

	if not sumIntensity > 0.0:
		return out

	out.mass = sumMassIntensity / sumIntensity
	#out.content['intensity'] = sumIntensity
	out.content['intensity'] = sumIntensity / len(listSpecEntries)

	return out


def mkList(left, right):
	if isinstance(left, type([])) and isinstance(right, type([])):
		left = left + right
	if not isinstance(left, type([])) and isinstance(right, type([])):
		left = [left] + right
	if isinstance(left, type([])) and not isinstance(right, type([])):
		left = left + [right]
	if not isinstance(left, type([])) and not isinstance(right, type([])):
		left = [left, right]

def mergeListMsms_noContainer(sample, listSpecEntries, align, mergeTolerance, mergeDeltaRes):
	'''Merge several MS/MS scans. The specEntries have the precursor mass and
	the MS/MS lists in their .content attribute.'''

	length = len(listSpecEntries)

	out = listSpecEntries[0]
	outEntries = listSpecEntries[0].content['entries']
	#right = specEntryRight.content['MSMS']

	### first: put the MS/MS lists together in a new specEntry ###

	sumMass = 0
	sumEntries = []
	sumScanCount = 0
	for entry in listSpecEntries:

		sumMass += entry.mass

		e = entry.content['entries']
		sumEntries += e
		sumScanCount += entry.content['scanCount']

	out.mass = sumMass / length

	####################################
	### averaging of the MS/MS scans ###

	# make a new specEntries dict for the averaging algorithm
	dictSpecEntries = {'one' : []}
	for entry in outEntries:
		dictSpecEntries['one'].append(specEntry(
			mass = entry[0],
			content = {'sample' : 'one', 'intensity' : entry[1],
				'peak_info' : entry[2:]}))

	# start the averaging algorithm
	if dictSpecEntries['one'] != []:
		listClusters = align(['one'], dictSpecEntries, mergeTolerance,
				intensityWeightedAvg = True, merge = mergeSumIntensity,
				deltaRes = mergeDeltaRes, minMass = sorted(dictSpecEntries['one'])[0].mass)

		# put the resulting list to the output specEntry
		listEntries = []
		for cl in listClusters:
			entry = [[],[]]
			entry[0] = cl['one'].mass
			entry[1] = cl['one'].content['intensity']
			for e in cl['one'].content['peak_info']:
				entry.append(e)
			listEntries.append(entry)
		listSpecEntries[0].content['entries'] = listEntries
		listSpecEntries[0].content['scanCount'] = sumScanCount

	else: # there were no entries summed in outMSMS.entries
		pass

	### averaging of the MS/MS scans ###
	####################################

	return listSpecEntries[0]


def doClusterMSMS(res, msms):

	retMsms = MSMS(
		mass = msms.precurmass,
		retentionTime = None,
		charge = msms.charge,
		polarity = msms.polarity,
		fileName = msms.fileName)

	listEntries = msms.entries
	listEntries.sort()

	iterEntry = listEntries.__iter__()

	precurmasslist = []

	# get pivotmass
	try:
		pivot = next(iterEntry)
	except StopIteration:
		return msms

	while iterEntry:

		# set lookaheadFlag. It is important for the last entry
		lookaheadFlag = False

		# get first mass
		precurmasslist = []
		precurmasslist.append(deepcopy(pivot))

		# next mass
		try:
			lookahead = next(iterEntry)
		except StopIteration:
			break

		# hpb
		if isinstance(res, TypeTolerance):
			hpb = pivot[0] / res.tolerance
		else:
			hpb = pivot[0] / res

		# go through peaks
		while lookahead[0] <= pivot[0] + hpb:
			precurmasslist.append(deepcopy(lookahead))
			try:
				lookahead = next(iterEntry)
			except StopIteration:
				break
			lookaheadFlag = True

		pivot = deepcopy(lookahead)

		# calc average mass with the intensity as weight

		# get max intensity
		maxint = 0
		for i in precurmasslist:
			if i[1] > maxint:
				maxint = i[1]

		# get intensity weights and the sum of all precursmass's
		sumcount = 0
		sumprecurmass = 0
		for i in precurmasslist:
			if maxint != 0.0:
				i[0] = (i[1] / maxint) * i[0]
				sumprecurmass = sumprecurmass + i[0]
				sumcount = sumcount + (i[1] / maxint)
			else:
				sumprecurmass = sumprecurmass + i[0]
				sumcount = sumcount + (i[1])

		if sumprecurmass == 0:
			raise LipidXException("Zero sum in precursormass. This is nogood.")

		# get intensity average
		sumintensity = 0
		for i in precurmasslist:
			sumintensity = sumintensity + i[1]

		# problems with zero valued sumcount, but this should not be...
		if sumcount == 0.0:
			sumcount = 1

		avgprecurmass = sumprecurmass / sumcount
		avgintensity = sumintensity #/ len(precurmasslist)
		retMsms.entries.append([avgprecurmass, avgintensity])

	# just append the last entry, because otherwise it will be deleted.
	# This is ok, since if it would be in the lpdxCluster resolution range,
	# it would be deleted anyway.
	retMsms.entries.append([msms.entries[-1][0], msms.entries[-1][1]])
	return retMsms

def doClusterSample(res, sample):

	"""lpdxCluster algorithm
	see p.1.b
	Go through the masses, mass by mass, and look if there are masses in the
	sample.accuracy range just calculated. More precise:

	begin with the smallest mass in the ordered list of masses
	while there is next mass
		1) Get next mass and make it pivot
		2) look sample.accuracy to the right.
			If there is a mass take it and make mass new pivot
		3) look 2 * sample.accuracy to the right.
		If there is the first mass goto 2)
			else end algorithm
	"""

	sample.listPrecurmass.sort()

	itersampl = sample.listPrecurmass.__iter__()

	newsample = deepcopy(sample)
	newsample.listPrecurmass = []

	flag = False
	precurmasslist = []

	# get pivotmass
	try:
		pivot = next(itersampl)
	except StopIteration:
		return sample

	while itersampl:

		# get first mass
		precurmasslist = []
		precurmasslist.append(deepcopy(pivot))

		# next mass
		try:
			lookahead = next(itersampl)
		except StopIteration:
			break

		# set flag which is needed for the last entry
		flag = False

		# hpb
		if isinstance(res, TypeTolerance):
			hpb = pivot.precurmass / res.tolerance
		else:
			hpb = pivot.precurmass / res

		while lookahead.precurmass <= pivot.precurmass + hpb:
			flag = True
			precurmasslist.append(deepcopy(lookahead))
			#pivot = deepcopy(lookahead)
			try:
				lookahead = next(itersampl)
			except StopIteration:
				break

		pivot = deepcopy(lookahead)

		# calc average mass with the intensity as weight

		# get max intensity
		maxint = 0
		for i in precurmasslist:
			if i.intensity > maxint:
				maxint = i.intensity

		# get intensity weights and the sum of all precursmass's
		sumcount = 0
		sumprecurmass = 0
		if maxint != 0:
			for i in precurmasslist:
				i.precurmass = (i.intensity / maxint) * i.precurmass
				sumprecurmass = sumprecurmass + i.precurmass
				sumcount = sumcount + (i.intensity / maxint)
		else:
			# if an intensity is zero, just take the average of the precurmasses
			for i in precurmasslist:
				sumprecurmass += i.precurmass
				sumcount += 1

		# get intensity weights and the sum of all precursmass's
		sumcountScan = 0
		for i in precurmasslist:
			sumcountScan += i.scanCount
		countScan = sumcountScan / len(precurmasslist)

		# get sum intensity
		sumintensity = 0
		for i in precurmasslist:
			sumintensity = sumintensity + i.intensity

		avgprecurmass = sumprecurmass / sumcount

		newsample.add_MSMass(MSMass(
			precurmass = avgprecurmass,
			intensity = sumintensity,
			smpl = sample.sampleName,
			polarity = precurmasslist[0].polarity,
			charge = None,
			fileName = None,
			scanCount = 1,
			basePeakIntensity = pivot.basePeakIntensity))

	if not flag:
		newsample.listPrecurmass.append(sample.listPrecurmass[-1])

	return newsample

def lpdxClusterMSMS(sample, resolution):
	for i in range(len(sample.listMsms)):
		sample.listMsms[i] = doClusterMSMS(resolution, sample.listMsms[i])




    ############ test ballal ############
    # import inspect, itertools

    # def summarize(x):
    #     # Never call repr() on complex objects to avoid buggy __repr__
    #     try:
    #         if isinstance(x, (int, float, str, bool, type(None))):
    #             return f"{x!r}"
    #         if isinstance(x, (list, tuple, set)):
    #             return f"{type(x).__name__}(len={len(x)})"
    #         if isinstance(x, dict):
    #             sample_keys = list(itertools.islice(x.keys(), 5))
    #             return f"dict(len={len(x)}, sample_keys={sample_keys})"
    #         return f"<{type(x).__name__} at {hex(id(x))}>"
    #     except Exception as e:
    #         return f"<unprintable {type(x).__name__}: {e}>"

    # #print("MSfilter in linearAlignment ####################################:", sc.options['MSfilter'])
    # #print("MSMSfilter in linearAlignment ####################################:", sc.options['MSMSfilter'])
    # # Normalize in case None was passed (directly or via **kwargs)
    # if fadi_percentage is None:
    #     caller = inspect.stack()[1]
    #     print("\n--- linearAlignment called ---")
    #     print("from:", caller.filename, "line", caller.lineno)
    #     print("tolerance:", summarize(tolerance))
    #     print("deltaRes:", summarize(deltaRes))
    #     print("minMass:", summarize(minMass))
    #     print("fadi_denominator:", summarize(fadi_denominator))
    #     print("fadi_percentage:", summarize(fadi_percentage), "type:", type(fadi_percentage).__name__)
    #     print("listSamples:", f"list(len={len(listSamples)})")
    #     print("dictSamples:", summarize(dictSamples))
    #     print("-----------------------------\n")
        
    #     print("NOTE: fadi_percentage is None at entry; normalizing to 0.0")
    #     fadi_percentage = 0.0
        
    ############################################