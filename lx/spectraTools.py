import re, os, sys
import numpy
from math import sqrt
import cPickle as pickle
from lx.mfql.chemParser import parseElemSeq
from tools import reportout

def getCalibrationPoints(lTable, lSpectrum, tolerance):

	lResultTable = []

	if lTable:
		for entry in sorted(lTable):
			lPeaks = []
			for m in range(len(lSpectrum) - 1):
				if tolerance.fitIn(lSpectrum[m].precurmass, entry):
					lPeaks.append(lSpectrum[m])

			# for making live more easy
			if lPeaks != []:
				tmp = lPeaks[0]
				for i in lPeaks:
					if tmp.intensity < i.intensity:
						tmp = i

				# the shift
				shift = tmp.precurmass - entry

				if lResultTable == [] and lPeaks != []:
					lResultTable.append([entry, shift])

				lResultTable.append([tmp.precurmass, shift])
			
		# makes live also more easy
		if lResultTable != [] and shift:
			lResultTable.append([lSpectrum[-1].precurmass, shift])

		return lResultTable
	
	else:
		return None

def getCalibrationPointsMSMS(lTable, lSpectrum, tolerance):

	lResultTable = []

	if not lTable is None:
		for entry in sorted(lTable):
			lPeaks = []
			for m in range(len(lSpectrum) - 1):
				if tolerance.fitIn(lSpectrum[m][0], entry):
					lPeaks.append(lSpectrum[m])

			# for making live more easy
			if lPeaks != []:
				tmp = lPeaks[0]
				for i in lPeaks:
					if tmp[1] < i[1]:
						tmp = i

				# the shift
				shift = tmp[0] - entry

				if lResultTable == [] and lPeaks != []:
					lResultTable.append([entry, shift])

				lResultTable.append([tmp[0], shift])
			
		# makes live also more easy
		if lResultTable != [] and shift:
			lResultTable.append([lSpectrum[-1][0], shift])

		return lResultTable
	
	else:
		return None

def frecal(x, listRecal, resolution):

	if listRecal:
		if len(listRecal) > 0:

			if x <= listRecal[0][0]:
				return listRecal[0][1]
			elif listRecal[-1][0] <= x:
				return listRecal[-1][1]
			else:
				for i in range(len(listRecal) - 1):
					if listRecal[i][0] <= x and x <= listRecal[i + 1][0]:
						return (listRecal[i + 1][1] - listRecal[i][1]) / (listRecal[i + 1][0] - listRecal[i][0]) * (x - listRecal[i][0]) + listRecal[i][1]

def recalibrateMS(sc, listRecalibration):

	# generate calibration
	lRecalTable = []

	if listRecalibration and len(listRecalibration) > 0:
		for key in sc.listSamples:
			lRecalTable = getCalibrationPoints(listRecalibration, sc.dictSamples[key].listPrecurmass, sc.options['MSresolution'])
			lRecalTable = getCalibrationPoints(listRecalibration, sc.dictSamples[key].listPrecurmass, sc.options['MStolerance'])

			if lRecalTable != []:
				for entry in sc.dictSamples[key].listPrecurmass:
					delta = frecal(entry.precurmass, lRecalTable, sc.options['MSresolution'])
					delta = frecal(entry.precurmass, lRecalTable, sc.options['MStolerance'])
					entry.precurmass = entry.precurmass - delta

		return lRecalTable

	else:
		return []

def recalibrateMSMS(sc,  listRecalibrationMSMS, listRecalibrationMS = None):

	# generate calibration table
	lRecalTableMS = []
	lRecalTableMSMS = []

	if listRecalibrationMSMS and len(listRecalibrationMSMS) > 0:
		for key in sc.listSamples:

			if listRecalibrationMS and len(listRecalibrationMS) > 0:
				lRecalTableMS = getCalibrationPoints(listRecalibrationMS, sc.dictSamples[key].listPrecurmass, sc.options['MSresolution'])
				lRecalTableMS = getCalibrationPoints(listRecalibrationMS, sc.dictSamples[key].listPrecurmass, sc.options['MStolerance'])

			for entry in sc.dictSamples[key].listMsms:

				lRecalTableMSMS = getCalibrationPointsMSMS(listRecalibrationMSMS, entry.entries, sc.options['MSMSresolution'])
				lRecalTableMSMS = getCalibrationPointsMSMS(listRecalibrationMSMS, entry.entries, sc.options['MSMStolerance'])
				if lRecalTableMSMS != []:
					for index in range(len(entry.entries)):
						delta = frecal(entry.entries[index][0], lRecalTableMSMS, sc.options['MSMSresolution'])
						delta = frecal(entry.entries[index][0], lRecalTableMSMS, sc.options['MSMStolerance'])
						entry.entries[index] = [entry.entries[index][0] - delta, entry.entries[index][1]]
				elif lRecalTableMS != []:
					for index in range(len(entry.entries)):
						delta = frecal(entry.entries[index].precurmass, lRecalTableMS, sc.options['MSresolution'])
						delta = frecal(entry.entries[index].precurmass, lRecalTableMS, sc.options['MStolerance'])
						entry.entries[index] = (entry.entries[index][0] - delta, entry.entries[index][1])


def del_Sample(sc, smpl):
	lenSurveyEntries = len(sc.listSurveyEntry)
	i = 0

	while i < lenSurveyEntries:
		flag = sc.listSurveyEntry[i].del_Sample(smpl)
		if not flag:
			del sc.listSurveyEntry[i]
			i = i - 1
			lenSurveyEntries = lenSurveyEntries - 1
		i = i + 1

	del sc.dictSamples[smpl]

def assignAllMSMS(sc):
	# assign MSMS experiments to survey entries
	for i in sc.listSamples:
		assignMSMS(sc, i)

def assignMSMS(sc, smpl):
	"""Go through msms experiments and assign every one to a precurmass
	
	in detail:
	let window(i) be the tolerance range [i-x...i+x] for i in precurmass and
		x in float
	for i in msms (in sample) do
		if window(i) overlaps with window(i+1) then
			sort precursor masses in overlapping window such that
			for every precursor mass j 	
				if j is nearer i assign it to i
				else assign it to i+1
		else assign ever precursor mass from the survey scan to i
			which is in window(i)
	"""

	reportout("Assigning MSMS experiment data for sample %s." % smpl)

	window = sc.selectionWindow / 2

	if sc.dictSamples[smpl].listMsms != []:

		# for all msms in sample smpl
		for i in range(len(sc.dictSamples[smpl].listMsms) - 1):
			# !!! check if also the last entry in listMsms is concidered !!!
			# set flag for last entry
			flag = False

			# does the next precursor mass overlap with the current?
			if sc.dictSamples[smpl].listMsms[i].precurmass + window > \
					sc.dictSamples[smpl].listMsms[i+1].precurmass - window:

				flat = True

				# test for the two precursor masses which one fits more to one of these windows
				precurmasses = sc.dictSamples[smpl].bestFitWindow(sc.dictSamples[smpl].listMsms[i], \
					sc.dictSamples[smpl].listMsms[i+1], window)

				for j in precurmasses:
					ni = j.precurmass - sc.dictSamples[smpl].listMsms[i].precurmass
					niplus1 = sc.dictSamples[smpl].listMsms[i+1].precurmass - j.precurmass
					if ni < niplus1:
						sc.get_SurveyEntry(j.precurmass, sc.dictSamples[smpl].polarity).assignMSMS(\
							sc.dictSamples[smpl].listMsms[i], smpl)
					#	self.dictSamples[smpl].get_Precurmass(j.precurmass).assignMSMS(\
					#		self.dictSamples[smpl].listMsms[i+1])
					else:
						sc.get_SurveyEntry(j.precurmass, sc.dictSamples[smpl].polarity).assignMSMS(\
							sc.dictSamples[smpl].listMsms[i+1], smpl)
					#	self.dictSamples[smpl].get_Precurmass(j.precurmass).assignMSMS(\
					#		self.dictSamples[smpl].listMsms[i])
			else:
				for j in sc.dictSamples[smpl].get_PrecurmassByWindow(sc.\
						dictSamples[smpl].listMsms[i].precurmass - window,\
						sc.dictSamples[smpl].listMsms[i].precurmass + window):
					sc.get_SurveyEntry(j.precurmass, sc.dictSamples[smpl].polarity).assignMSMS(sc.dictSamples\
						[smpl].listMsms[i], smpl)

		if not flag:
			l = len(sc.dictSamples[smpl].listMsms) - 1
			for j in sc.dictSamples[smpl].get_PrecurmassByWindow(sc.\
					dictSamples[smpl].listMsms[l].precurmass - window,\
					sc.dictSamples[smpl].listMsms[l].precurmass + window):
				sc.get_SurveyEntry(j.precurmass, sc.dictSamples[smpl].polarity).assignMSMS(sc.dictSamples\
					[smpl].listMsms[l], smpl)
#	else:
#		raise "list of MSMS experiments is empty"


def formatOutputSaira(list):

	str = ''
	for i in list:
		str += '%.4f ' % i[1]
	#str += '\n'
	return str
	

			
			
def calcSFbyMass(mass, sfconstraint, tolerance, nearest=False):
	"""IN: mass in m/z,
	sf-constraint,
	tolerance in resolution type,
	nearest in Boolean
OUT: list of SurveyEntry
"""	

	if not sfconstraint:
		raise "No SF given"

	if not isinstance(sfconstraint, ElementSequence):
		csf = parseElemSeq(sfconstraint)
	else:
		csf = sfconstraint

	# check for the right sample
	sf = csf.solveWithCalcSF(mass, tolerance)

	# with nearest=True the sum composition which nearest to
	# mass is returned
	if nearest and len(sf) > 1:
		error = 5 
		for i in sf:
			if abs(mass - i.getWeight()) < error:
				error = abs(mass - i.getWeight())
				out = i
		return [i]

	return sf
			
def calcSFbyMassSGR(mass, sfconstraint, tolerance, nearest=False):
	"""IN: mass in m/z,
	sf-constraint,
	tolerance in resolution type,
	nearest in Boolean
OUT: list of SurveyEntry
"""	

	if not sfconstraint:
		raise "No SF given"

	if not isinstance(sfconstraint, ElementSequence):
		csf = parseElemSeq(sfconstraint)
	else:
		csf = sfconstraint

	# check for the right sample
	sf = csf.solveWithSevenGoldenRules(mass, tolerance)

	# with nearest=True the sum composition which nearest to
	# mass is returned
	if nearest and len(sf) > 1:
		error = 5 
		for i in sf:
			if abs(mass - i.getWeight()) < error:
				error = abs(mass - i.getWeight())
				out = i
		return [i]

	return sf
			
def saveSC(sc, filename):
	pickle.dump(sc, open(filename, "wb"), pickle.HIGHEST_PROTOCOL)

def loadSC(filename):
	reportout("Loading SC %s ..." % filename)

	sc = pickle.load(open(filename, "rb"))

	# for backwards compatiblty
	if not sc.options.has_key('MStolerance'):
		sc.options['MStolerance'] = sc.options['MSaccuracy']
	if not sc.options.has_key('MSMStolerance'):
		sc.options['MSMStolerance'] = sc.options['MSMSaccuracy']

	return sc

def mergeSC(sc1, sc2):
	"""Maybe an idea. Let's see, if we need it some day."""
	pass

def selectSurveyEntries(sc, listArgs):
	
	if listArgs == []:
		raise "parameter list is empty"

	sc.didPreselection = True

	# number of samples (need for occupation calculation)
	samples = float(len(sc.listSamples))

	for i in listArgs:
		
		# overwrite standart tolerance
		if i.has_key('MStolerance'): MStolerance = 1000000 / i['MStolerance']
		else: MStolerance = sc.options['MStolerance']

		# mass range constraint
		if i.has_key('massrange'): massrange = i['massrange'] 
		else: massrange = (0, 30000)
		
		# set sample occupation threshold
		if i.has_key('occupationThreshold'): occThrld = i['occupationThreshold'] 
		else: occThrld = 0
	
		# set sample occupation threshold
		if i.has_key('minIntensityDelta'): minInsD = i['minIntensityDelta'] 
		else: minInsD = 0
	
		# set sample occupation threshold
		if i.has_key('maxIntensityDelta'): maxInsD = i['maxIntensityDelta'] 
		else: maxInsD = 2
	
		if i.has_key('sf-constraint'):
			for j in sc.listSurveyEntry:
				
				# test for mass range
				if massrange[0] <= j.precurmass and j.precurmass <= massrange[1]:

					# test for occupation threshold
					percsum = 0.0
					for k in sc.listSamples:
						if j.dictIntensity.has_key(k) and j.dictIntensity[k] != 0:
							percsum += 1                                        
					percsum = percsum / samples

					# test for min/max intensity delta
					breakBool = False
					if i.has_key('minIntensityDelta') or i.has_key('maxIntensityDelta'):
						dictRelIntensity = {}
						
						# find biggest intensity	
						maxInt = 0
						for k in sc.listSamples:
							if j.dictIntensity.has_key(k) and maxInt < j.dictIntensity[k]: maxInt = j.dictIntensity[k]

						# calc relative intensity
						for k in sc.listSamples:
							if j.dictIntensity.has_key(k): 
								dictRelIntensity[k] = j.dictIntensity[k] / maxInt
						
						# check for max/minIntensityDelta
						for k in sc.listSamples:
							for l in sc.listSamples:
								if dictRelIntensity.has_key(k) and dictRelIntensity.has_key(l):
									if abs(dictRelIntensity[k] - dictRelIntensity[l]) < minInsD: 
										boolBreak = True
										break
									if maxInsD and abs(dictRelIntensity[k] - dictRelIntensity[l]) > maxInsD:
										boolBreak = True
										break
				
					# test if it is under the threshold
					if percsum >= occThrld:
						newSF = calcSFbyMass(j.precurmass, i['sf-constraint'], MStolerance)

						# test if sum composition is already there
						if newSF != [] and intersect(newSF, j.listPrecurmassSF) == []:
							j.listPrecurmassSF += newSF
	
	return sc

# "selectSurveyEntriesWithSevenGoldenRules
def sSEwithSGR(sc, listArgs):
	
	if listArgs == []:
		raise "parameter list is empty"

	sc.didPreselection = True


	# number of samples (need for occupation calculation)
	samples = float(len(sc.listSamples))

	for i in listArgs:
		
		# overwrite standart tolerance
		if i.has_key('MStolerance'): MStolerance = 1000000 / i['MStolerance']
		else: MStolerance = sc.options['MStolerance']

		# mass range constraint
		if i.has_key('massrange'): massrange = i['massrange'] 
		else: massrange = (0, 30000)
		
		# set sample occupation threshold
		if i.has_key('occupationThreshold'): occThrld = i['occupationThreshold'] 
		else: occThrld = 0
	
		if i.has_key('sf-constraint'):
			for j in sc.listSurveyEntry:
				
				# test for mass range
				if massrange[0] <= j.precurmass and j.precurmass <= massrange[1]:

					# test for occupation threshold
					percsum = 0.0
					for k in sc.listSamples:
						if j.dictIntensity.has_key(k) and j.dictIntensity[k] != 0:
							percsum += 1                                        
					percsum = percsum / samples
				
					# test if it is under the threshold
					if percsum >= occThrld:
						newSF = calcSFbyMassSGR(j.precurmass, i['sf-constraint'], MStolerance)

						# test if sum composition is already there
						if newSF != [] and intersect(newSF, j.listPrecurmassSF) == []:
							j.listPrecurmassSF += newSF
	
	return sc

class linkedList:

	def __init__(self, first = None):
		if first:
			self.list = [first]
		else:
			self.list = []
		self.index = -1 
		self.length = len(self.list)

	def append(self, data):
		self.list.append(data)
		self.length += 1

	def next(self):
		self.index += 1
		return self.list[self.index]

	def prev(self):
		self.index -= 1
		return self.list[self.index]

	def reset(self):
		self.index = -1

def chargeEstimation(scan, adduct, options):
	"""The algorithm uses in particalur the idea of matched filter
approach, decribed in the phd thesis of Parminder Kaur 2007. It uses
the isotopic spacing of the ions. There
a theoretical spectrum for every charge per mass is convolved with
the (original) experimental spectrum. The charge is then estimated
by a maximum value. While this approach is based on continous spectra
we have to approximate it for discrete peak values. 

To compare TID (theoretical isotopic distribution spectrum) and
EID (experimantal ...) we use two scores: 
	1) how accurate an TID mass fits to the nearest EID mass (within
		MStolerance range). We weight this score with the relative
		intensity of the TID mass.
	2) intensity comparison: if the isotope intensity of a m/z of TID is
		greater than the m/z of the EID then this will get a low
		score. The m/z intensity of a EID peak can be smaller as 
		of the TID, since the EID peak can overlap with another
		ion. This could be different after isotopic correction.
	"""

	isotopeDiff = 1.0033

	# generate theoretical spectra for charges 1-5
	tid = []
	tid.append([1.003355, 2.00671, 3.010065])
	tid.append([1.003355/2, 2.00671/2, 3.010065/2])
	tid.append([1.003355/3, 2.00671/3, 3.010065/3])
#	tid.append([1.003355/4, 2.00671/4, 3.010065/4, 4.013420/4, 5.016775/4])
#	tid.append([1.003355/5, 2.00671/5, 3.010065/5, 4.013420/5, 5.016775/5])

	# prepare adduct variable
	if isinstance(adduct, float):
		mzDiff = adduct
	elif isinstance(adduct, lpdxChemsf.ElementSequence):
		mzDiff = adduct.getWeight()
	elif isinstance(adduct, string):
		mzDiff = lpdxParser.parseElemSeq(adduct).getWeight()
	else:
		return None

	# other initialization
	if options.has_key('MStolerance'):
		MStolerance = 1000000 / options['MStolerance']
	else:
		MStolerance = scan.options['MStolerance']

	# check every SurveyEntry for every possible charge
	for i in scan.listSurveyEntry:
		if i.charge > 0:
			err = []
			for chg in range(len(tid)):
				err.append([])
				for iso in tid[chg]:
					isoMass = scan.get_SurveyEntry(i.precurmass + iso, 1, {})
					if not isoMass:
						isoMass = scan.get_SurveyEntry(i.precurmass + iso, -1, {})
						if isoMass:
							err[chg].append(abs((i.precurmass + iso) - isoMass.precurmass))
						else:
							err[chg].append(-1.0)
					else:
						err[chg].append(abs((i.precurmass + iso) - isoMass.precurmass))

			for estCharge in range(len(err) - 1, -1, -1):
				if err[estCharge][0] != -1.0:
					i.charge = i.charge * (estCharge + 1)

def sequence(scan, sfconstraint, listDiffs, options, name):
	""" Identifies a sequence of fragments which differ sequentially
about the masses given in listDiffs. Options is again a dictionary
and name a string identifyer for the sequence. The return value is
a Sequence object. Possible options are:
	massrange, MStolerance, MSMStolerance"""

	if options.has_key('MStolerance'): MStolerance = 1000000 / options['MStolerance']
	else: MStolerance = scan.options['MStolerance']

	if options.has_key('MSMStolerance'): MSMStolerance = 1000000 / options['MSMStolerance']
	else: MSMStolerance = scan.options['MSMStolerance']

	selectSurveyEntries(scan, [{'sf-constraint' : sfconstraint, 'massrange' : options['massrange']}])

	# mark
	cipheredName = scan.mark_FragmentMass(chemPrecurFrag, name, {})

	# sort se list for preprocessing
	scan.listSurveyEntry.sort()

def selectConnectedSurveyEntries(scan, diff, options):
	"""
	"""

	if isinstance(diff, ElementSequence):
		diff = diff.getWeight()

	if not options.has_key('posToNeg'):	
		raise "Options has at least to contain 'posToNeg'"

	posList = scan.get_posSurveyEntry()
	negList = scan.get_negSurveyEntry()

	if options['posToNeg']:
		for i in posList:
			i.sibling = scan.get_SurveyEntry(i.precurmass + diff, '-1')

	if not options['posToNeg']:
		for i in negList:
			i.sibling = scan.get_SurveyEntry(i.precurmass + diff, '+1')

def checkWithSevenGoldenRules(scan, se, sfconstraint, tolerance):

	t = 1000000 / tolerance
	
	# this is the list of all precursors which are involved in the fragmentation
	listMSMSPeaks = []
	listEntrySE = []

	for entryse in se.listMSMS[0].se:
		listEntrySE.append(entryse)

	for entrymsms in se.listMSMS:
		# save fragment mass
		listPeaks = [entrymsms.mass]
		listSumCompositions = [calcSFbyMassSGR(entrymsms.mass, sfconstraint, t)]
		for entryse in listEntrySE:
			# calc neutral loss
			listPeaks.append(entryse.precurmass - entrymsms.mass)
			listSumCompositions.append(calcSFbyMassSGR(entryse.precurmass - entrymsms.mass, sfconstraint, t))
		listMSMSPeaks.append((listPeaks, listSumCompositions))

