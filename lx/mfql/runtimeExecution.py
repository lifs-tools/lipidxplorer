import re
from lx.spectraContainer import MSMSEntry
from lx.tools import dbgout, odict, connectLists, combinations_with_replacement, permutations
from lx.mfql.runtimeStatic import *
from lx.mfql.isotope import isotopicValues, isotopicValuesInter
from lx.mfql.constants import *
from lx.mfql.peakMarking import TypeEmptyMark
from lx.debugger import Debug
from lx.exceptions import LipidXException, SyntaxErrorException
from copy import copy, deepcopy
import numpy as np

## CarthesianProduct
# Takes an array of arrays and generates the carthesian product of the given
# arrays. E.g. a = [[0], [1,2,3], [4,5]] -> [[0,1,4], [0,1,5], [0,2,4],
# [0,2,5], [0,3,4], [0,3,5]]
def CarthesianProduct(array):

	# init an array containing the lenghts of the arrays in "array"
	lengthVector = []
	for i in array:
		lengthVector.append(len(i))

	# indexVector contains the indices of the input arrays
	indexVector = [0] * len(lengthVector)

	combinations = []
	for step in range(reduce(lambda x,y: x*y, lengthVector)):
		c = []
		for index in range(len(indexVector)):
			c.append(array[index][indexVector[index]])
		combinations.append(c)
		
		# increment indexVector
		for i in reversed(range(len(indexVector))):
			if indexVector[i] < lengthVector[i] - 1:
				indexVector[i] += 1
				break
			else:
				indexVector[i] = 0
			if i == 0:
				break

	return combinations


class TypeMFQL:

	def __init__(self, masterScan):
		"""This is the MFQL object. All related information about the run of
		all given queries at run time is stored here.

		It contains the result, which is the resulting MasterScan object, which
		has individually associated queries."""

		self.sc = masterScan
		self.options = None
		self.scan = None
		self.queryName = ""
		self.currVars = {}
		self.currQuery = None
		self.currSC = None
		self.listQueryNames = []
		self.namespaceConnector = '!'

		# dictionary for the definition part
		self.dictDefinitionTable = odict()#{}

		# dictionary for the scan part
		self.dictScanTable = {}
		self.dictScanEntries = {}

		# dictionary for empty variables
		self.dictEmptyVariables = odict()

		# symbol table for all variable
		self.countSymbolTable = 0
		self.dictSymbolTable = {}

		# table for all data
		self.listDataTable = []

		# manage environments
		self.currentEnvironment = 'top'
		self.dictEnvironment = odict()#{}
		self.currentEnvEntry = []
		self.environmentCount = 0
		self.precursor = None

		# computationMode is either 'sc' or 'float'
		self.computationMode = 'sc'

		# count for dynamic variable allocation
		self.countAlloc = 1
		self.dictDynSymTable = {}

		# for the result
		self.listResult = []
		self.listReport = []

		self.resultSC = []
		self.complementSC = None
		self.result = TypeResult(mfqlObj = self)

		# postprocessing functions
		self.dictPostFuns = {}

		self.markIndex = 0

	def reset(self):

		self.scan = None

		# dictionary for the definition part
		#self.dictDefinitionTable[self.queryName] = odict()#{}

		# dictionary for the scan part
		self.dictScanTable = {}
		#self.listScanEntries = []

		# symbol table for all variable
		self.countSymbolTable = 0
		self.dictSymbolTable = {}

		# table for all data
		self.listDataTable = []

		# manage environments
		self.currentEnvironment = 'top'
		#self.dictEnvironment = {'parser' : {}}
		self.currentEnvEntry = []
		self.environmentCount = 0
		self.precursor = None

		# computationMode is either 'sc' or 'float'
		self.computationMode = 'sc'

		# count for dynamic variable allocation
		self.countAlloc = 1
		self.dictDynSymTable = {}

		# a temporary variable for all kinds of
		# pseudo global arrangements
		self.tmp = {}

		# for the result
		self.listReport = []
		self.listResult = []

	def addEmptyVariable(self, name, variable):
		'''Store "empty" variables in an extra dict which
		is read later by the SUCHTHAT routine.'''

		# options ....

		scconst = None
		chemsc = None
		isSFConstraint = None
		mass = None

		# the type of a variable can be
		# 	TypeSFConstraint, TypeElementSequence, TypeFloat or TypeList
		if variable.__class__.__name__ == "TypeSFConstraint":
			scconst = variable.elementSequence
			isSFConstraint = True

		if variable.__class__.__name__ == "TypeElementSequence":
			chemsc = variable.elementSequence
			isSFConstraint = False
			mass = variable.elementSequence.getWeight()

		if variable.__class__.__name__ == "TypeFloat":
			isSFConstraint = False
			mass = variable.float

		if variable.__class__.__name__ == "TypeList":
			raise LipidXException("Using a list without 'IDENTIFY' is not" +\
					" supported yet.")

		mark = TypeEmptyMark(name, chemsc, isSFConstraint, mass, scconst)

		if not self.dictEmptyVariables.has_key(self.queryName):
			self.dictEmptyVariables[self.queryName] = []
		self.dictEmptyVariables[self.queryName].append(mark)

	def genVariables_new(self, surveyEntry, plus_permutation = False, empty_vars = {}):
		'''This routine generates all combinations of fragments
		for a precursor plus MS/MS. The problem are ambiguous
		fragments. They exist if more than one variable of
		the DEFINE section has the same sc-constraint. For example:

		DEFINE FA1 ='C[12..22] H[20..50] O[2]' WITH DBR = (1.5,7.5), CHG = -1;
		DEFINE FA2 ='C[12..22] H[20..50] O[2]' WITH DBR = (1.5,7.5), CHG = -1;

		To have non-repeating results the chemical sum compositions are used as
		hashes for dictionary with the variable names as content. Such,
		we have an injective function masses: chemsc -> variable.
		The routine at the end choses "randomly" a variable when putting the
		result back together which then has only variables as output.'''

		### TODO: the empty variables have to be added somewhere here###

		loopResults = surveyEntry.listScanEntries
		surveyEntry.listScanEntries = []

		theResult = []
		for se in loopResults:

			# merge the marks and empty variables
			marks = se.dictMarks
			for key in empty_vars.keys():
				marks[key] = empty_vars[key]

			varsToBeCombined = odict()
			for variable in marks.keys():
				x = se.dictMarks[variable]
				for e in x:
					if not varsToBeCombined.has_key(variable):
						varsToBeCombined[variable] = [e]
					else:
						varsToBeCombined[variable].append(e)

			cp = CarthesianProduct(varsToBeCombined.values())

			for c in range(len(cp)):
				vars = {}
				for index in range(len(varsToBeCombined.keys())):
					vars[cp[c][index].name] = cp[c][index]
				theResult.append(vars)

		surveyEntry.listVariables += theResult


	def genVariables_old(self, surveyEntry, plus_permutation = False):
		'''This routine generates all combinations of fragments
		for a precursor plus MS/MS. The problem are ambiguous
		fragments. They exist if more than one variable of
		the DEFINE section has the same sc-constraint. For example:

		DEFINE FA1 ='C[12..22] H[20..50] O[2]' WITH DBR = (1.5,7.5), CHG = -1;
		DEFINE FA2 ='C[12..22] H[20..50] O[2]' WITH DBR = (1.5,7.5), CHG = -1;

		To have non-repeating results the chemical sum compositions are used as
		hashes for dictionary with the variable names as content. Such,
		we have an injective function masses: chemsc -> variable.
		The routine at the end choses "randomly" a variable when putting the
		result back together which then has only variables as output.'''

		# ??? Why did I take m/z instead of chemsc in the first place???

		loopResults = surveyEntry.listScanEntries

		vars = {}
		theResult = []

		tmp = []
		for se in loopResults:

			precursor = []
			noSFConstraint = []
			length = 0

			masses = {}
			#for x in se.dictMarks.values():
			for variable in se.dictMarks.keys():
				x = se.dictMarks[variable]
				if x[0].scope[2] != '1':
					for e in x:
						if e.isSFConstraint:
							if masses.has_key(repr(e.chemsc)):
								masses[repr(e.chemsc)].append(e)
							else:
								masses[repr(e.chemsc)] = [e]
						else:
							noSFConstraint.append(e)
				else:
					precursor += x

			# the number of variables to permut depends on the number of fragments
			length_fragments = len(se.dictMarks.values()) - 1 - len(noSFConstraint)
			result = combinations_with_replacement(masses.keys(),
					length_fragments)
			# subtract one for the precursor from the overal number of marks and
			# all marks which are no sc-constraint

			tmp = list(result)

			if not self.options['noPermutations']:#plus_permutation:
				tmp_2 = []
				for i in tmp:
					tmp_2 += permutations(i, len(i))
			else:
				tmp_2 = tmp

			#TODO multiple results for MS/MS !!!!!!!!!!!!!!!!!!!!!!!!#

			# the following code puts the
			r = []
			for entry in tmp_2:
				for p in precursor:
					t = [p]
					if noSFConstraint != []:
						for n in noSFConstraint:
							t.append(n)
							fragments = 0
							for i in entry:
								t.append(masses[i][fragments % len(masses[i])])
								fragments += 1
					else:
						fragments = 0
						for i in entry:
							t.append(masses[i][fragments % len(masses[i])])
							fragments += 1
					r.append(t)


			for i in r:
				print ">>>", i
				for e in i:
					vars[e.name] = e
				theResult.append(vars)
				vars = {}

		surveyEntry.listScanEntries = []
		surveyEntry.listVariables += theResult


		#self.dictEnvironment[self.queryName] = theResult

class TypeResult:

	def __init__(self, mfqlObj = None):

		self.mfqlObj = mfqlObj
		self.listQuery = []
		self.dictQuery = odict()#{}
		self.listHead = None

		self.resultSC = copy(self.mfqlObj.sc)

		self.mfqlOutput = False

		### flags for the operations ###

		# if the dictIntensity entry is called with a regular Expression
		self.flag_dI_regExp = False

	def __getitem__(self, item):
		return self.dictQuery[item]

	def generateResultSC(self):

		resultSC = self.mfqlObj.resultSC

		for se in self.mfqlObj.sc.listSurveyEntry:

			# take only se's which have a mark and a sum composition
			#if se.listMark != [] and \
			#		not se.removedByIsotopicCorrection_MS and\
			#		se.listPrecurmassSF != []:
			#	resultSC.append(se)

			# take only se's which have a sum composition
			if not se.removedByIsotopicCorrection_MS and\
					se.listPrecurmassSF != []:
				resultSC.append(se)

			else:
				mark = False
				for msmse in se.listMSMS:
					if msmse.listMark != []:
						mark = True
						break
				if mark and se.listPrecurmassSF != []:
					resultSC.append(se)


		resultSC.sort()


	def generateComplementSC(self):

		resultSC = []

		for query in self.dictQuery.values():

			# construct the artificial MasterScan
			for v in query.listVariables:
				for k in v.keys():
					isIn = False
					for se in v[k].se:
						if not isinstance(se, MSMSEntry):
							if not se in resultSC:
								resultSC.append(se)
						else:
							pass

		self.mfqlObj.complementSC = copy(self.mfqlObj.sc)
		self.mfqlObj.complementSC.listSurveyEntry = []
		sc = self.mfqlObj.complementSC

		with open('complementTest.csv', 'w') as f:
			listMSMS = []
			for entry in self.mfqlObj.sc.listSurveyEntry:

				if (not entry.isIsotope and not entry.isTakenBySuchthat):

					sc.listSurveyEntry.append(copy(entry))
					sc.listSurveyEntry[-1].listMark = []
					sc.listSurveyEntry[-1].listPrecurmassSF = []
					sc.listSurveyEntry[-1].sumComposition = []

					listMSMS = []
					isInResult = True
					index = 0
					while index < len(entry.listMSMS):
						if not entry.listMSMS[index].isTakenBySuchthat:
							listMSMS.append(entry.listMSMS[index])
							listMSMS[-1].listFragSF = []
						index += 1

					sc.listSurveyEntry[-1].listMSMS = listMSMS
				else:
					f.write('%.4f, %s, %s\n' % (entry.precurmass, entry.isIsotope, entry.isTakenBySuchthat))

				sc.listSurveyEntry.sort()

	def generateQueryResultSC(self):

		import re

		sc = self.mfqlObj.resultSC

		for query in self.dictQuery.values():

			query.sc = []

			# construct the artificial MasterScan
			for se in self.mfqlObj.resultSC:

				if se.isInQueryMS(query.name, self.mfqlObj.namespaceConnector):

					# I guess just doing a deepcopy cause a lot of trouble
					# newSE = deepcopy(se)
					newSE = copy(se)

					# add the variables to the variable list of the query
					# this is especially for queries with no SUCHTHAT, here they
					# are (again) checked if every entry of IDENTIFY was present
					# in the spectrum
					for vars in se.listVariables:

						# add the empty vars to the list of variables
						if self.mfqlObj.dictEmptyVariables.has_key(query.name):
							for emptyVar in self.mfqlObj.dictEmptyVariables[query.name]:
								vars[emptyVar.name] = emptyVar

						isIn = True
						for definition in self.mfqlObj.dictDefinitionTable[query.name].keys():
							if not vars.has_key(definition):# and not self.mfqlObj.currVars[defintion] is None:
								isIn = False

						if isIn:
							query.listVariables.append(vars)

					# this is an old entry and I am not sure if it is:
					# i)  newSE.name = query.name or
					# ii) newSE.charge = query.charge
					# But I guess the second... sure, a query has no charge! Arrrghhh...
					#newSE.charge = query.name
					newSE.name = query.name
					query.sc.append(newSE)

					for mark in se.listMark:
						mark.se = [newSE]
						#mark.msmse = newSE
						#if mark.scope == "MS1+" or mark.scope == "MS1-":
						if mark.type == 0:
							mark.intensity = mark.se[0].dictIntensity
							mark.float = mark.se[0].precurmass

						for msmse in newSE.listMSMS:
							for mark in msmse.listMark:
								#if mark.scope == "MS2+" or mark.scope == "MS2-":
								if mark.type == 1:
									mark.msmse.dictIntensity = copy(msmse.dictIntensity)
									mark.intensity = msmse.dictIntensity
									mark.float = msmse.mass

		#del self.mfqlObj.resultSC
		pass

	def deIsotopingMS_complement(self):

		import math
		scan = self.mfqlObj.sc
		listKeys = scan.listSamples
		listSE = self.mfqlObj.sc.listSurveyEntry

		for entry in range(len(listSE) - 1):

			if listSE[entry].isTakenBySuchthat:

				res = listSE[entry].precurmass / (((listSE[entry].precurmass - listSE[0].precurmass) * self.options['MSresolutionDelta']) + self.options['MSresolution'].tolerance)
				#res = listSE[entry].precurmass / scan.MSresolution

				if listSE[entry].listPrecurmassSF != []:

					actualKey = listSE[entry]
					keyIndex = entry + 1
					nextKey = listSE[keyIndex]

					M4found = []
					M3found = []
					M2found = []
					M1found = []

					while nextKey.precurmass - actualKey.precurmass - res <= 4.0132:

						# are there isotopes according to double bound difference?
						isThere = False

						if (4.0132 <= nextKey.precurmass - actualKey.precurmass + res and\
							4.0132 >= nextKey.precurmass - actualKey.precurmass - res) or\
							isThere:
							M4found.append(nextKey)

						if 3.0099 <= nextKey.precurmass - actualKey.precurmass + res and\
							3.0099 >= nextKey.precurmass - actualKey.precurmass - res:
							M3found.append(nextKey)

						# are there isotopes according to double bound difference?
						isThere = False

						if (2.0066 <= nextKey.precurmass - actualKey.precurmass + res and\
							2.0066 >= nextKey.precurmass - actualKey.precurmass - res) or\
							isThere:
							M2found.append(nextKey)

						if 1.0033 <= nextKey.precurmass - actualKey.precurmass + res and\
							1.0033 >= nextKey.precurmass - actualKey.precurmass - res:
							M1found.append(nextKey)

						keyIndex += 1
						if keyIndex < len(listSE):
							nextKey = listSE[keyIndex]
						else:
							break

					if (M4found != [] or M3found != [] or M2found != [] or M1found != []):

						# calculate ratios of isotopic occurance for M-2
						numC = 0
						for scomp in actualKey.listPrecurmassSF:
							numC += scomp['C']
						numC = numC / len(actualKey.listPrecurmassSF)
						gotOne = False

						neg = (1 - 0.01082)
						cWithoutIsotopes = neg**numC

						cfM = []
						cfM.append((numC * 0.01082 * neg**(numC - 1) / cWithoutIsotopes))
						cfM.append((0.5 * numC * (numC - 1) * 0.0001170724 * neg**(numC - 2)) / cWithoutIsotopes) # continue here!
						cfM.append(((1/6) * numC * (numC - 1) * (numC - 2) * 0.000001266723 * neg**(numC - 3)) / cWithoutIsotopes)
						cfM.append(((1/12) * numC * (numC - 1) * (numC - 2) * (numC - 3) * 0.000000014 * neg**(numC - 4)) / cWithoutIsotopes)

					if M1found != []:
						for M1f in M1found:
							# correct the found fragment intensity
							for k in listKeys:
								# change intensity of the fragment, if it is already changed
								difference = actualKey.dictIntensity[k] * cfM[0]
								M1f.dictIntensity[k] -= difference
								M1f.isIsotope = True
								self.mfqlObj.sc.getSEbyIndex(M1f.index).isIsotope = True

					if M2found != []:
						for M2f in M2found:
							# correct the found fragment intensity
							for k in listKeys:
								# change intensity of the fragment, if it is already changed
								difference = actualKey.dictIntensity[k] * cfM[1]
								M2f.dictIntensity[k] -= difference
								M2f.isIsotope = True
								self.mfqlObj.sc.getSEbyIndex(M2f.index).isIsotope = True

					if M3found != []:
						for M3f in M3found:
							# correct the found fragment intensity
							for k in listKeys:
								# change intensity of the fragment, if it is already changed
								difference = actualKey.dictIntensity[k] * cfM[2]
								M3f.dictIntensity[k] -= difference
								M3f.isIsotope = True
								self.mfqlObj.sc.getSEbyIndex(M3f.index).isIsotope = True

					if M4found:
						for M4f in M4found:
							# correct the found fragment intensity
							for k in listKeys:
								# change intensity of the fragment, if it is already changed
								difference = actualKey.dictIntensity[k] * cfM[3]
								M4f.dictIntensity[k] -= difference
								M4f.isIsotope = True
								self.mfqlObj.sc.getSEbyIndex(M4f.index).isIsotope = True


				zero = True
				for	k in listKeys:
					if listSE[entry].dictIntensity[k] < 0.0:
						listSE[entry].dictIntensity[k] = -1

					if listSE[entry].dictIntensity[k] != 0.0: zero = False


	def isotopicCorrectionMS_wholeSC(self):

		import math
		scan = self.mfqlObj.sc
		listKeys = scan.listSamples
		listSE = self.mfqlObj.sc.listSurveyEntry

		for entry in range(len(listSE) - 1):

			res = listSE[entry].precurmass / (((listSE[entry].precurmass - listSE[0].precurmass) * self.options['MSresolutionDelta']) + self.options['MSresolution'].tolerance)
			#res = listSE[entry].precurmass / scan.MSresolution

			if listSE[entry].listPrecurmassSF != []:

				actualKey = listSE[entry]
				keyIndex = entry + 1
				nextKey = listSE[keyIndex]

				M4found = []
				M3found = []
				M2found = []
				M1found = []

				while nextKey.precurmass - actualKey.precurmass - res <= 4.0132:

					# are there isotopes according to double bound difference?
					isThere = False

					if (4.0132 <= nextKey.precurmass - actualKey.precurmass + res and\
						4.0132 >= nextKey.precurmass - actualKey.precurmass - res) or\
						isThere:
						M4found.append(nextKey)

					if 3.0099 <= nextKey.precurmass - actualKey.precurmass + res and\
						3.0099 >= nextKey.precurmass - actualKey.precurmass - res:
						M3found.append(nextKey)

					# are there isotopes according to double bound difference?
					isThere = False

					if (2.0066 <= nextKey.precurmass - actualKey.precurmass + res and\
						2.0066 >= nextKey.precurmass - actualKey.precurmass - res) or\
						isThere:
						M2found.append(nextKey)

					if 1.0033 <= nextKey.precurmass - actualKey.precurmass + res and\
						1.0033 >= nextKey.precurmass - actualKey.precurmass - res:
						M1found.append(nextKey)

					keyIndex += 1
					if keyIndex < len(listSE):
						nextKey = listSE[keyIndex]
					else:
						break

				if (M4found != [] or M3found != [] or M2found != [] or M1found != []):

					# calculate ratios of isotopic occurance for M-2
					numC = 0
					for scomp in actualKey.listPrecurmassSF:
						numC += scomp['C']
					numC = numC / len(actualKey.listPrecurmassSF)
					gotOne = False

					neg = (1 - 0.01082)
					cWithoutIsotopes = neg**numC

					cfM = []
					cfM.append((numC * 0.01082 * neg**(numC - 1) / cWithoutIsotopes))
					cfM.append((0.5 * numC * (numC - 1) * 0.0001170724 * neg**(numC - 2)) / cWithoutIsotopes) # continue here!
					cfM.append(((1/6) * numC * (numC - 1) * (numC - 2) * 0.000001266723 * neg**(numC - 3)) / cWithoutIsotopes)
					cfM.append(((1/12) * numC * (numC - 1) * (numC - 2) * (numC - 3) * 0.000000014 * neg**(numC - 4)) / cWithoutIsotopes)

				if M1found:
					for M1f in M1found:
						# correct the found fragment intensity
						for k in listKeys:
							# change intensity of the fragment, if it is already changed
							difference = actualKey.dictIntensity[k] * cfM[0]
							M1f.dictIntensity[k] -= difference

				if M2found:
					for M2f in M2found:
						# correct the found fragment intensity
						for k in listKeys:
							# change intensity of the fragment, if it is already changed
							difference = actualKey.dictIntensity[k] * cfM[1]
							M2f.dictIntensity[k] -= difference

				if M3found:
					for M3f in M3found:
						# correct the found fragment intensity
						for k in listKeys:
							# change intensity of the fragment, if it is already changed
							difference = actualKey.dictIntensity[k] * cfM[2]
							M3f.dictIntensity[k] -= difference

				if M4found:
					for M4f in M4found:
						# correct the found fragment intensity
						for k in listKeys:
							# change intensity of the fragment, if it is already changed
							difference = actualKey.dictIntensity[k] * cfM[3]
							M4f.dictIntensity[k] -= difference


			zero = True
			for	k in listKeys:
				if listSE[entry].dictIntensity[k] < 0.0:
					listSE[entry].dictIntensity[k] = -1

				if listSE[entry].dictIntensity[k] != 0.0: zero = False

	def removeIsotopicCorrected(self):
		'''This routine checks all SurveyEntries (together with their MS/MS entries)
		if the occupation threshold still holds. Because some isotopic corrections
		may reduced the intensity to a level where the occupation threshold does not
		hold anymore.'''

		if self.mfqlObj.resultSC == []:
			return None

		scan = self.mfqlObj.sc
		listKeys = scan.listSamples
		listSE = self.mfqlObj.resultSC
		entry = 0
		numSamples = len(listSE[0].dictIntensity.keys())

		listSCMS = []
		listSCMSMS = []

		# check the occuaption threshold for MS1
		indexI = 0
		while indexI < len(listSE):

			entry = listSE[indexI]
			check = self.mfqlObj.sc.checkOccupation(
					#entry[keyVar].intensity,
					entry.dictIntensity,
					entry.dictScans,
					occThr = self.mfqlObj.options['MSminOccupation'],
					threshold = self.mfqlObj.options['MSthreshold'],
					threshold_type = self.mfqlObj.options['MSthresholdType'],
					dictBasePeakIntensity = entry.dictBasePeakIntensity)
			if not check:
				del listSE[indexI]
			else:
				indexI += 1

			# check the occupation threshold for MS2
			indexF = 0
			while indexF < len(entry.listMSMS):

				entryMSMS = entry.listMSMS[indexF]
				check = self.mfqlObj.sc.checkOccupation(
						entryMSMS.dictIntensity,
						entryMSMS.dictScanCount,
						occThr = self.mfqlObj.options['MSMSminOccupation'],
						threshold = self.mfqlObj.options['MSMSthreshold'],
						threshold_type = self.mfqlObj.options['MSMSthresholdType'],
						dictBasePeakIntensity = entry.listMSMS[indexF].dictBasePeakIntensity)
				if not check:
					del entry.listMSMS[indexF]
				else:
					indexF += 1

		self.mfqlObj.resultSC = listSE

	def isotopicCorrectionMS(self):

		import math
		scan = self.mfqlObj.sc
		listKeys = scan.listSamples
		listSE = self.mfqlObj.sc.listSurveyEntry

		if Debug("isotopicCorrection"):
			dbgstr  = "\n"
			dbgstr += "\n - - - - - - - - - - - - - - - - - - - - - - - - - - - - "
			dbgstr += "\n -        Isotopic correction on MS spectrum           - "
			dbgstr += "\n - - - - - - - - - - - - - - - - - - - - - - - - - - - - "
			dbgstr += "\n"
			dbgout(dbgstr)

		for entry in range(len(listSE)):

			actualKey = listSE[entry]

			### mark the isotopic corrected peaks ###
			numSamples = float(len(listKeys))
			countNonZeros = 0
			for	k in listKeys:
				if listSE[entry].dictIntensity[k] < 0.0:
					listSE[entry].dictIntensity[k] = -1

			### check the occupation threshold ###
			check = self.mfqlObj.sc.checkOccupation(
					listSE[entry].dictIntensity,
					listSE[entry].dictScans,
					occThr = self.mfqlObj.options['MSminOccupation'],
					threshold = self.mfqlObj.options['MSthreshold'],
					threshold_type = self.mfqlObj.options['MSthresholdType'],
					dictBasePeakIntensity = listSE[entry].dictBasePeakIntensity)


			# check if after the isotopic correction the occupation threshold is still hold
			#if not (float(countNonZeros) / numSamples) >= self.mfqlObj.sc.options['MSminOccupation']:
			if not check:
				actualKey.removedByIsotopicCorrection_MS = True

			if listSE[entry].listMark != []:

			#if scan.options.has_key('MSMSresolutionDelta') and scan.options['MSresolutionDelta']:
			#	res = listSE[entry].precurmass / (((listSE[entry].precurmass - listSE[0].precurmass) * scan.options['MSresolutionDelta']) + scan.options['MSresolution'].tolerance)
			#else:
			#	res = listSE[entry].precurmass / scan.options['MSresolution'].tolerance

				res = self.mfqlObj.options['MSresolution'].getTinDA(listSE[entry].precurmass)

				isotopicDistance = 1.0033
				chargePrecurmassSF = {}

				monoisotopic = 1.0

				# test if all listPrecurmassSF entries are of multiple charge
				multiCharge = True
				for scomp in listSE[entry].listPrecurmassSF:

					# sort precurmass sum compositions by charge
					if not chargePrecurmassSF.has_key("%d" % abs(scomp.charge)):
						chargePrecurmassSF["%d" % abs(scomp.charge)] = []

					chargePrecurmassSF["%d" % abs(scomp.charge)].append(scomp)

					#if abs(scomp.charge) < 2:
					#	multiCharge = False

				for charge in chargePrecurmassSF.keys():

					# calculate ratios of isotopic occurance for M-2
					numC = 0
					numH = 0
					numO = 0
					numN = 0
					numP = 0
					numS = 0
					for scomp in chargePrecurmassSF[charge]:
						numC += scomp['C']
						numH += scomp['H']
						numO += scomp['O']
						numN += scomp['N']
						numP += scomp['P']
						numS += scomp['S']
					numC = numC / len(chargePrecurmassSF[charge])
					numH = numH / len(chargePrecurmassSF[charge])
					numO = numO / len(chargePrecurmassSF[charge])
					numN = numN / len(chargePrecurmassSF[charge])
					numP = numP / len(chargePrecurmassSF[charge])
					numS = numS / len(chargePrecurmassSF[charge])
					gotOne = False

					(mz, intens, monoisotopic) = isotopicValues(numC, numH, numO, numN, numS, numP)

					cID = isotopicDistance / float(charge)

					#errorIntensityIsotope = 20.0 # the error of the isotopes intensity in percentage
					actualKey = listSE[entry]
					#keyIndex = entry + 1
					keyIndex = entry
					nextKey = listSE[keyIndex]
					#old:
					#delta = nextKey.precurmass - actualKey.precurmass
					#new:
					delta = nextKey.precurmass - actualKey.listPrecurmassSF[0].getWeight()

					M4found = []
					M3found = []
					M2found = []
					M1found = []

					M4foundUnmarked = []
					M3foundUnmarked = []
					M2foundUnmarked = []
					M1foundUnmarked = []

					listSE[entry].monoisotopicRatio = copy(monoisotopic)

					while delta <= 5 * cID:

						if (4 * cID <= delta + res and\
							4 * cID >= delta - res):
							if nextKey.listMark != []:
								M4found.append(nextKey)
							else:
								## check if the intensity of the found peak is close to the expected
								## intensity of the isotope
								#isIsotope = True
								#for sample in actualKey.dictIntensity.keys():
								#	isotopicRatio = actualKey.dictIntensity[sample] * intens[4]
								#	intensityError = (isotopicRatio / 100.0) * errorIntensityIsotope

								#	if not (nextKey.dictIntensity[sample] < isotopicRatio + intensityError and\
								#			nextKey.dictIntensity[sample] > isotopicRatio - intensityError):
								#		isIsotope = False
								#
								#if isIsotope:
								#	M4foundUnmarked.append(nextKey)
								M4foundUnmarked.append(nextKey)

						if 3 * cID <= delta + res and\
							3 * cID >= delta - res:
							if nextKey.listMark != []:
								M3found.append(nextKey)
							else:
								## check if the intensity of the found peak is close to the expected
								## intensity of the isotope
								#isIsotope = True
								#for sample in actualKey.dictIntensity.keys():
								#	isotopicRatio = actualKey.dictIntensity[sample] * intens[3]
								#	intensityError = (isotopicRatio / 100.0) * errorIntensityIsotope

								#	if not (nextKey.dictIntensity[sample] < isotopicRatio + intensityError and\
								#			nextKey.dictIntensity[sample] > isotopicRatio - intensityError):
								#		isIsotope = False
								#
								#if isIsotope:
								#	M3foundUnmarked.append(nextKey)
								M3foundUnmarked.append(nextKey)

						if (2 * cID <= delta + res and\
							2 * cID >= delta - res):

							if nextKey.listMark != []:
								M2found.append(nextKey)
							else:
								## check if the intensity of the found peak is close to the expected
								## intensity of the isotope
								#isIsotope = True
								#for sample in actualKey.dictIntensity.keys():
								#	isotopicRatio = actualKey.dictIntensity[sample] * intens[2]
								#	intensityError = (isotopicRatio / 100.0) * errorIntensityIsotope

								#	if not (nextKey.dictIntensity[sample] < isotopicRatio + intensityError and\
								#			nextKey.dictIntensity[sample] > isotopicRatio - intensityError):
								#		isIsotope = False

								#if isIsotope:
								#	M2foundUnmarked.append(nextKey)
								M2foundUnmarked.append(nextKey)

						if 1 * cID <= delta + res and\
							1 * cID >= delta - res:
							if nextKey.listMark != []:
								M1found.append(nextKey)
							else:
								## check if the intensity of the found peak is close to the expected
								## intensity of the isotope
								#isIsotope = True
								#for sample in actualKey.dictIntensity.keys():
								#	isotopicRatio = actualKey.dictIntensity[sample] * intens[1]
								#	intensityError = (isotopicRatio / 100.0) * errorIntensityIsotope

								#	if not (nextKey.dictIntensity[sample] < isotopicRatio + intensityError and\
								#			nextKey.dictIntensity[sample] > isotopicRatio - intensityError):
								#		isIsotope = False
								#
								#if isIsotope:
								#	M1foundUnmarked.append(nextKey)
								M1foundUnmarked.append(nextKey)

						keyIndex += 1
						if keyIndex < len(listSE):
							nextKey = listSE[keyIndex]
							delta = nextKey.precurmass - actualKey.precurmass
						else:
							break

					# removing the if clause will calc isotopic distribution of all precursors
					# but sure it will slow down the whole thing
					#if (M4found != [] or M3found != [] or M2found != [] or M1found != []):

					#######################################
					### check for the resolution defect ###

					# the defect comes from the lower resolution with higher masses
					# on high resolution acquired spectra. Sometimes the isotopic
					# peak is not present (as it should be, since it is high resolution),
					# but merged with the neighboring peak. But then, the neighbouring
					# peak does not shift towards the isotope and the isotope cannot
					# be found. The following routine does a workaround to this problem.

					# check if
					#if M1foundUnmarked == [] and M1found == [] or\
					#	M2foundUnmarked == [] and M2found == [] or\
					#	M3foundUnmarked == [] and M3found == [] or\
					#	M4foundUnmarked == [] and M4found == []:

					# check how many isotopes we should see depending on the given threshold settings
					matchM1 = False
					matchM2 = False
					matchM3 = False
					matchM4 = False

					singleScans = {}
					for sample in actualKey.dictScans.keys():
						singleScans[sample] = 1

					if scan.checkOccupation(
							actualKey.dictIntensity,
							singleScans,
							factor = intens[1],
							occThr = self.mfqlObj.options['MSminOccupation'],
							threshold = self.mfqlObj.options['MSthreshold'],
							threshold_type = self.mfqlObj.options['MSthresholdType'],
							dictBasePeakIntensity = actualKey.dictBasePeakIntensity):
						matchM1 = True
					if scan.checkOccupation(
							actualKey.dictIntensity,
							singleScans,
							factor = intens[2],
							occThr = self.mfqlObj.options['MSminOccupation'],
							threshold = self.mfqlObj.options['MSthreshold'],
							threshold_type = self.mfqlObj.options['MSthresholdType'],
							dictBasePeakIntensity = actualKey.dictBasePeakIntensity):
						matchM2 = True
					if scan.checkOccupation(
							actualKey.dictIntensity,
							singleScans,
							factor = intens[3],
							occThr = self.mfqlObj.options['MSminOccupation'],
							threshold = self.mfqlObj.options['MSthreshold'],
							threshold_type = self.mfqlObj.options['MSthresholdType'],
							dictBasePeakIntensity = actualKey.dictBasePeakIntensity):
						matchM3 = True
					if scan.checkOccupation(
							actualKey.dictIntensity,
							singleScans,
							factor = intens[4],
							occThr = self.mfqlObj.options['MSminOccupation'],
							threshold = self.mfqlObj.options['MSthreshold'],
							threshold_type = self.mfqlObj.options['MSthresholdType'],
							dictBasePeakIntensity = actualKey.dictBasePeakIntensity):
						matchM4 = True


					doCorrectionM1 = False
					doCorrectionM2 = False
					doCorrectionM3 = False
					doCorrectionM4 = False

					smthStrangeForM1 = False
					smthStrangeForM2 = False
					smthStrangeForM3 = False
					smthStrangeForM4 = False

					if not matchM2:
						if M1found != []:
							# do the isotopic correction
							doCorrectionM1 = True
						if M1found == [] and M1foundUnmarked == []:
							# something strange is going on
							smthStrangeForM1 = True
							pass

					elif not matchM3:
						if M1found != []:
							# do the isotopic correction
							doCorrectionM1 = True
							pass
						if M2found != []:
							# do the isotopic correction
							doCorrectionM2 = True
							pass
						if M1found == [] and M1foundUnmarked == []:
							# something strange is going on
							smthStrangeForM1 = True
							pass
						if M2found == [] and M2foundUnmarked == []:
							# something strange is going on
							smthStrangeForM2 = True
							pass

					elif not matchM4:
						if M1found != []:
							# do the isotopic correction
							doCorrectionM1 = True
							pass
						if M2found != []:
							# do the isotopic correction
							doCorrectionM2 = True
							pass
						if M3found != []:
							# do the isotopic correction
							doCorrectionM3 = True
							pass
						if M1found == [] and M1foundUnmarked == []:
							# something strange is going on
							smthStrangeForM1 = True
							pass
						if M2found == [] and M2foundUnmarked == []:
							# something strange is going on
							smthStrangeForM2 = True
							pass
						if M3found == [] and M3foundUnmarked == []:
							# something strange is going on
							smthStrangeForM3 = True
							pass

					else:
						if M1found != []:
							# do the isotopic correction
							doCorrectionM1 = True
							pass
						if M2found != []:
							# do the isotopic correction
							doCorrectionM2 = True
							pass
						if M3found != []:
							# do the isotopic correction
							doCorrectionM3 = True
							pass
						if M4found != []:
							# do the isotopic correction
							doCorrectionM4 = True
							pass
						if M1found == [] and M1foundUnmarked == []:
							# something strange is going on
							smthStrangeForM1 = True
							pass
						if M2found == [] and M2foundUnmarked == []:
							# something strange is going on
							smthStrangeForM2 = True
							pass
						if M3found == [] and M3foundUnmarked == []:
							# something strange is going on
							smthStrangeForM3 = True
							pass
						if M4found == [] and M4foundUnmarked == []:
							# something strange is going on
							smthStrangeForM4 = True
							pass

					if smthStrangeForM1:

						index = 1
						if entry + index < len(listSE):
							nextKey = listSE[entry + index]
							delta = nextKey.precurmass - actualKey.precurmass
						else:
							break

						delta = nextKey.precurmass - actualKey.precurmass

						while delta <= 1 * cID:

							if (1 * cID <= delta + 2 * res and\
								1 * cID >= delta - res):
								if nextKey.listMark != []:
									M1found.append(nextKey)
									doCorrectionM1 = True

							index += 1
							if entry + index < len(listSE):
								nextKey = listSE[entry + index]
								delta = nextKey.precurmass - actualKey.precurmass
							else:
								break

					if smthStrangeForM2:

						index = 1
						if entry + index < len(listSE):
							nextKey = listSE[entry + index]
							delta = nextKey.precurmass - actualKey.precurmass
						else:
							break
						delta = nextKey.precurmass - actualKey.precurmass

						while delta <= 3 * cID:

							if (delta >= 2 * cID - res and\
								delta <= 2 * cID + 3 * res):
								if nextKey.listMark != []:
									M2found.append(nextKey)
									doCorrectionM2 = True

							index += 1
							if entry + index < len(listSE):
								nextKey = listSE[entry + index]
								delta = nextKey.precurmass - actualKey.precurmass
							else:
								break

					if smthStrangeForM3:

						index = 1
						if entry + index < len(listSE):
							nextKey = listSE[entry + index]
							delta = nextKey.precurmass - actualKey.precurmass
						else:
							break
						delta = nextKey.precurmass - actualKey.precurmass

						while delta <= 4 * cID:

							if (3 * cID <= delta + 2 * res and\
								3 * cID >= delta - res):
								if nextKey.listMark != []:
									M3found.append(nextKey)
									doCorrectionM3 = True

							index += 1
							if entry + index < len(listSE):
								nextKey = listSE[entry + index]
								delta = nextKey.precurmass - actualKey.precurmass
							else:
								break

					if smthStrangeForM4:

						index = 1
						if entry + index < len(listSE):
							nextKey = listSE[entry + index]
							delta = nextKey.precurmass - actualKey.precurmass
						else:
							break
						delta = nextKey.precurmass - actualKey.precurmass

						while delta <= 5 * cID:

							if (4 * cID <= delta + 2 * res and\
								4 * cID >= delta - res):
								if nextKey.listMark != []:
									M4found.append(nextKey)
									doCorrectionM4 = True

							index += 1
							if entry + index < len(listSE):
								nextKey = listSE[entry + index]
								delta = nextKey.precurmass - actualKey.precurmass
							else:
								break

					if (M4found != [] or M3found != [] or M2found != [] or M1found != []):

						if Debug("isotopicCorrection"):
							dbgstr  = "\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"
							dbgstr += "\n MS sum compositions for %.4f:" % actualKey.precurmass
							str = '\n'
							for scomp in chargePrecurmassSF[charge]:
								str += " # %s" % repr(scomp)
							str += '\n'
							str += ' AVG: C%d H%d O%d N%d S%d P%d\n' % (numC, numH, numO, numN, numS, numP)
							for index in range(1, len(intens)):
								str += ' > I%d:%.5f' % (index, intens[index])
							str += '\n'
							dbgstr += str
							dbgout(dbgstr)

					# check if the lipid has isotopes (if not, it is possibly no lipid)
					if M1found == [] or M2found == [] or M3found == []:
						pass


					if M1found != [] and doCorrectionM1:
						for M1f in M1found:

							# mark it as isotop
							M1f.isIsotope

							# save old intensity for dump
							if M1f.dictBeforeIsocoIntensity == {}:
								M1f.dictBeforeIsocoIntensity = deepcopy(M1f.dictIntensity)

							# correct the found fragment intensity
							for k in listKeys:

								if M1f.dictIntensity[k] > 0:
									difference = actualKey.dictIntensity[k] * intens[1]
									M1f.dictIntensity[k] -= difference

									if Debug("isotopicCorrection"):
										dbgout(" > I1 %.4f corrected to: %.6f (-%.6f)" % (M1f.precurmass, M1f.dictIntensity[k], difference))

					if M2found != [] and doCorrectionM2:
						for M2f in M2found:

							# mark it as isotop
							M2f.isIsotope

							# save old intensity for dump
							if M2f.dictBeforeIsocoIntensity == {}:
								M2f.dictBeforeIsocoIntensity = deepcopy(M2f.dictIntensity)


							# correct the found fragment intensity
							for k in listKeys:

								if M2f.dictIntensity[k] > 0:
									difference = actualKey.dictIntensity[k] * intens[2]
									M2f.dictIntensity[k] -= difference

									if Debug("isotopicCorrection"):
										dbgout(" > I2 %.4f corrected to: %.6f (-%.6f)" % (M2f.precurmass, M2f.dictIntensity[k], difference))

					if M3found != [] and doCorrectionM3:
						for M3f in M3found:

							# mark it as isotop
							M3f.isIsotope

							# save old intensity for dump
							if M3f.dictBeforeIsocoIntensity == {}:
								M3f.dictBeforeIsocoIntensity = deepcopy(M3f.dictIntensity)

							# correct the found fragment intensity
							for k in listKeys:

								if M3f.dictIntensity[k] > 0:
									difference = actualKey.dictIntensity[k] * intens[3]
									M3f.dictIntensity[k] -= difference

									if Debug("isotopicCorrection"):
										dbgout(" > I3 %.4f corrected to: %.6f (-%.6f)" % (M3f.precurmass, M3f.dictIntensity[k], difference))

					if M4found != [] and doCorrectionM4:
						for M4f in M4found:

							# mark it as isotop
							M4f.isIsotope

							# save old intensity for dump
							if M4f.dictBeforeIsocoIntensity == {}:
								M4f.dictBeforeIsocoIntensity = deepcopy(M4f.dictIntensity)

							# correct the found fragment intensity
							for k in listKeys:

								if M4f.dictIntensity[k] > 0:
									difference = actualKey.dictIntensity[k] * intens[4]
									M4f.dictIntensity[k] -= difference

									if Debug("isotopicCorrection"):
										dbgout(" > I4 %.4f corrected to: %.6f (-%.6f)" % (M4f.precurmass, M4f.dictIntensity[k], difference))

					##################################
					#### correct monoisotopic peak ###
					##################################

					#for	k in listKeys:
					#	actualKey.dictIntensity[k] /= monoisotopic
					#actualKey.monoisotopicRatio = monoisotopic

					#### end monoisotopic correction ###


	def correctMonoisotopicPeaks(self):
		'''This function incorporates the ratio of the precursor
		monoisotopic peak into the fragments. If this would not
		be done, the fragment profile and precursor profile would not fit.'''
		import math
		scan = self.mfqlObj.sc
		listKeys = scan.listSamples
		listSE = self.mfqlObj.resultSC
		#listSE = self.resultSC # this is a MasterScan

		for entry in range(len(listSE)):

			# correct the monoisotopic peak
			for sample in listSE[entry].dictIntensity.keys():

				# store the original intensity for the dump
				if listSE[entry].dictBeforeIsocoIntensity == {}:
					listSE[entry].dictBeforeIsocoIntensity = deepcopy(listSE[entry].dictIntensity)

				listSE[entry].dictIntensity[sample] = listSE[entry].dictIntensity[sample] / listSE[entry].monoisotopicRatio

			for msmsEntry in listSE[entry].listMSMS:
				if msmsEntry.listMark != [] and not msmsEntry.monoisotopicCorrected:
					msmsEntry.monoisotopicCorrected = True

					# store the original intensity for the dump
					if msmsEntry.dictBeforeIsocoIntensity == {}:
						msmsEntry.dictBeforeIsocoIntensity = deepcopy(msmsEntry.dictIntensity)

					for sample in listSE[entry].dictIntensity.keys():
						msmsEntry.dictIntensity[sample] = msmsEntry.dictIntensity[sample] / listSE[entry].monoisotopicRatio
						pass


	def deIsotopingMSMS_complement(self, artPIS = None, scan = None):

		#sc = self.mfqlObj.resultSC
		sc = self.mfqlObj.sc.listSurveyEntry
		scan = self.mfqlObj.sc

		# generate a pseudo precursor ion scan
		# every particular PIS is stored in dictPIS and then come pairs of {precursormass : PIS-fragment} in a list
		dictPIS = {}
		for se in range(len(sc)):
			for i in sc[se]:
				if i.listMark != []:
					for m in i.listMark:
						pisName = repr(int(m.mass))
						if not pisName in dictPIS:
							dictPIS[pisName] = odict()

						precurmass = "%4.5f" % sc[se].precurmass
						if (not precurmass in dictPIS[pisName].keys()):
							dictPIS[pisName][precurmass] = m
						else:
							# neutral loss scan or precursor scan?
							if dictPIS[pisName][precurmass].isnl:
								if not dictPIS[pisName][precurmass].frsc:
									dictPIS[pisName][precurmass] = m
							else:
								if not dictPIS[pisName][precurmass].nlsc:
									dictPIS[pisName][precurmass] = m

		# generate a float list where every entry represents a key of the dictPISFrags
		# for working with

		# python tweak -> generate a list of sorted (key, value)
		for pis in dictPIS:

			# sort the precursor masses for PIS 'pis'
			listKeys = []
			for i in dictPIS[pis].keys():
				listKeys.append(float(i))
			listKeys.sort()

			for key, value in [(k,dictPIS[pis][k]) for k in dictPIS[pis]]:

				# index marks for isotope overlapped fragments
				M3found = []
				M2found = []
				M1found = []

				actualKey = precurKey = float(key)
				keyIndex = listKeys.index(precurKey)
				selectWin = self.mfqlObj.options['selectionWindow']
				while actualKey - precurKey - selectWin / 2 < 4.1:

					keyIndex += 1
					if keyIndex < len(listKeys):
						actualKey = listKeys[keyIndex]
					else:
						break

					if 3.0099 <= actualKey - precurKey + selectWin / 2 and\
						3.0099 >= actualKey - precurKey - selectWin / 2:
						M3found.append(actualKey)

					if 2.0066 <= actualKey - precurKey + selectWin / 2 and\
						2.0066 >= actualKey - precurKey - selectWin / 2:
						M2found.append(actualKey)

					if 1.0033 <= actualKey - precurKey + selectWin / 2 and\
						1.0033 >= actualKey - precurKey - selectWin / 2:
						M1found.append(actualKey)

				# takes the values for the isotopes from the neutral loss of M, where (M->I1->I2->...)
				if (M3found != [] or M2found != [] or M1found != []) and dictPIS[pis][key].chemsc:

					# calculate ratios of isotopic occurance for M-2
					gotOne = False

					try:
						if dictPIS[pis][key].isnl:
							numC = dictPIS[pis][key].frsc['C']
						else:
							numC = dictPIS[pis][key].nlsc['C']

					except TypeError:
						#dumpObj(dictPIS[pis][key])
						#exit(0)
						numC = 0

					neg = (1 - 0.01082)
					cWithoutIsotopes = neg**numC

					cfM = []
					cfM.append((numC * 0.01082 * neg**(numC - 1) / cWithoutIsotopes))
					cfM.append((0.5 * numC * (numC - 1) * 0.0001170724 * neg**(numC - 2)) / cWithoutIsotopes) # continue here!
					cfM.append(((1/6) * numC * (numC - 1) * (numC - 2) * 0.000001266723 * neg**(numC - 3)) / cWithoutIsotopes)
					cfM.append(((1/12) * numC * (numC - 1) * (numC - 2) * (numC - 3) * 0.000000014 * neg**(numC - 4)) / cWithoutIsotopes)

				if dictPIS[pis][key].chemsc:
					if M1found != []:
						for M1f in M1found:

							# correct the found fragment intensity
							for k in dictPIS[pis][key].msmse.dictIntensity.keys():

								# change intensity of the fragment, if it is already changed
								l = dictPIS[pis]["%4.5f" % M1f]
								l.msmse.isIsotope = True

								# change intensity of the fragment, if it is was not changed
								if l.msmse.dictIntensity[k] != 0.0:
									l.msmse.dictIntensity[k] = l.msmse.dictIntensity[k] - dictPIS[pis][key].msmse.dictIntensity[k] * cfM[0]

					if M2found != []:
						for M2f in M2found:

							# correct the found fragment intensity
							for k in dictPIS[pis][key].msmse.dictIntensity.keys():

								# change intensity of the fragment, if it is already changed
								l = dictPIS[pis]["%4.5f" % M2f]
								l.msmse.isIsotope = True

								# change intensity of the fragment, if it is was not changed
								if l.msmse.dictIntensity[k] != 0.0:
									l.msmse.dictIntensity[k] = l.msmse.dictIntensity[k] - dictPIS[pis][key].msmse.dictIntensity[k] * cfM[1]

					if M3found != []:
						for M3f in M3found:
					#
							# correct the found fragment intensity
							for k in dictPIS[pis][key].msmse.dictIntensity.keys():

								# change intensity of the fragment, if it is already changed
								l = dictPIS[pis]["%4.5f" % M3f]
								l.msmse.isIsotope = True

								# change intensity of the fragment, if it is was not changed
								if l.msmse.dictIntensity[k] != 0.0:
									l.msmse.dictIntensity[k] = l.msmse.dictIntensity[k] - dictPIS[pis][key].msmse.dictIntensity[k] * cfM[2]

	def isotopicCorrectionMSMS_wholeSC(self, artPIS = None, scan = None):

		#sc = self.mfqlObj.resultSC
		sc = self.mfqlObj.sc.listSurveyEntry
		scan = self.mfqlObj.sc

		# generate a pseudo precursor ion scan
		# every particular PIS is stored in dictPIS and then come pairs of {precursormass : PIS-fragment} in a list
		dictPIS = {}
		for se in range(len(sc)):
			for i in sc[se]:
				if i.listMark != []:
					for m in i.listMark:
						pisName = repr(int(m.mass))
						if not pisName in dictPIS:
							dictPIS[pisName] = odict()

						precurmass = "%4.5f" % sc[se].precurmass
						if (not precurmass in dictPIS[pisName].keys()):
							dictPIS[pisName][precurmass] = m
						else:
							# neutral loss scan or precursor scan?
							if dictPIS[pisName][precurmass].isnl:
								if not dictPIS[pisName][precurmass].frsc:
									dictPIS[pisName][precurmass] = m
							else:
								if not dictPIS[pisName][precurmass].nlsc:
									dictPIS[pisName][precurmass] = m

	#for debugging
	#	for k in dictPIS.keys():
	#		dbgout(k)
	#		for se in dictPIS[k].keys():
	#			if dictPIS[k][se].isnl:
	#				dbgout("\t", se, dictPIS[k][se].frmass)
	#			else:
	#				dbgout("\t", se, dictPIS[k][se].frmass)

	#	for pis in dictPISFrags.keys():
		# generate a float list where every entry represents a key of the dictPISFrags
		# for working with

		# python tweak -> generate a list of sorted (key, value)
		for pis in dictPIS:

			# sort the precursor masses for PIS 'pis'
			listKeys = []
			for i in dictPIS[pis].keys():
				listKeys.append(float(i))
			listKeys.sort()

			for key, value in [(k,dictPIS[pis][k]) for k in dictPIS[pis]]:

				# index marks for isotope overlapped fragments
				M3found = []
				M2found = []
				M1found = []

				actualKey = precurKey = float(key)
				keyIndex = listKeys.index(precurKey)
				selectWin = self.mfqlObj.options['selectionWindow']
				while actualKey - precurKey - selectWin / 2 < 3.0099:

					keyIndex += 1
					if keyIndex < len(listKeys):
						actualKey = listKeys[keyIndex]
					else:
						break

					if 3.0099 <= actualKey - precurKey + selectWin / 2 and\
						3.0099 >= actualKey - precurKey - selectWin / 2:
						M3found.append(actualKey)

					if 2.0066 <= actualKey - precurKey + selectWin / 2 and\
						2.0066 >= actualKey - precurKey - selectWin / 2:
						M2found.append(actualKey)

					if 1.0033 <= actualKey - precurKey + selectWin / 2 and\
						1.0033 >= actualKey - precurKey - selectWin / 2:
						M1found.append(actualKey)

				# takes the values for the isotopes from the neutral loss of M, where (M->I1->I2->...)
				if (M3found != [] or M2found != [] or M1found != []) and dictPIS[pis][key].chemsc:

					# calculate ratios of isotopic occurance for M-2
					gotOne = False

					try:
						if dictPIS[pis][key].isnl:
							numC = dictPIS[pis][key].frsc['C']
						else:
							numC = dictPIS[pis][key].nlsc['C']

					except TypeError:
						#dumpObj(dictPIS[pis][key])
						#exit(0)
						numC = 0

					neg = (1 - 0.01082)
					cWithoutIsotopes = neg**numC

					cfM = []
					cfM.append((numC * 0.01082 * neg**(numC - 1) / cWithoutIsotopes))
					cfM.append((0.5 * numC * (numC - 1) * 0.0001170724 * neg**(numC - 2)) / cWithoutIsotopes) # continue here!
					cfM.append(((1/6) * numC * (numC - 1) * (numC - 2) * 0.000001266723 * neg**(numC - 3)) / cWithoutIsotopes)
					cfM.append(((1/12) * numC * (numC - 1) * (numC - 2) * (numC - 3) * 0.000000014 * neg**(numC - 4)) / cWithoutIsotopes)

				if dictPIS[pis][key].chemsc:
					if M1found != []:
						for M1f in M1found:
							if not dictPIS[pis][key].msmse.isCorrectedIsotopic:
								#debug

								# correct the found fragment intensity
								for k in dictPIS[pis][key].msmse.dictIntensity.keys():

									# change intensity of the fragment, if it is already changed
									l = dictPIS[pis]["%4.5f" % M1f]

									# change intensity of the fragment, if it is was not changed
									if l.msmse.dictIntensity[k] > 0.0:
										l.msmse.dictIntensity[k] = l.msmse.dictIntensity[k] - dictPIS[pis][key].msmse.dictIntensity[k] * cfM[0]
								dictPIS[pis][key].msmse.isCorrectedIsotopic = True

					if M2found != []:
						for M2f in M2found:
							if not dictPIS[pis][key].msmse.isCorrectedIsotopic:
								#debug

								# correct the found fragment intensity
								for k in dictPIS[pis][key].msmse.dictIntensity.keys():

									# change intensity of the fragment, if it is already changed
									l = dictPIS[pis]["%4.5f" % M2f]

									# change intensity of the fragment, if it is was not changed
									if l.msmse.dictIntensity[k] > 0.0:
										l.msmse.dictIntensity[k] = l.msmse.dictIntensity[k] - dictPIS[pis][key].msmse.dictIntensity[k] * cfM[1]
								dictPIS[pis][key].msmse.isCorrectedIsotopic = True

					if M3found != []:
						for M3f in M3found:
							if not dictPIS[pis][key].msmse.isCorrectedIsotopic:
								#debug

								# correct the found fragment intensity
								for k in dictPIS[pis][key].msmse.dictIntensity.keys():

									# change intensity of the fragment, if it is already changed
									l = dictPIS[pis]["%4.5f" % M3f]

									# change intensity of the fragment, if it is was not changed
									if l.msmse.dictIntensity[k] > 0.0:
										l.msmse.dictIntensity[k] = l.msmse.dictIntensity[k] - dictPIS[pis][key].msmse.dictIntensity[k] * cfM[2]
								dictPIS[pis][key].msmse.isCorrectedIsotopic = True


	def isotopicCorrectionMSMS(self, artPIS = None, scan = None):

		if Debug("isotopicCorrection"):
			dbgstr  = "\n"
			dbgstr += "\n - - - - - - - - - - - - - - - - - - - - - - - - - - - - "
			dbgstr += "\n -       Isotopic correction on MS/MS spectrum         - "
			dbgstr += "\n - - - - - - - - - - - - - - - - - - - - - - - - - - - - "
			dbgstr += "\n"
			dbgout(dbgstr)

		scan = self.mfqlObj.sc
		listSE = self.mfqlObj.resultSC
		isotopicDistance = 1.0033
		toleranceMS = self.mfqlObj.options['selectionWindow'] #scan.options['MSresolution']
		toleranceMSMS = self.mfqlObj.options['MSMSresolution']

		#for key in dictPrePIS:
		for entry in range(len(listSE) - 1):

			if listSE[entry].listMark != []:

				cID = isotopicDistance / 1.0#listSE[entry].charge

				monoisotopic = 1.0
				actualKey = listSE[entry]
				currentSE = listSE[entry]
				keyIndex = entry + 1
				nextKey = listSE[keyIndex]
				delta = nextKey.precurmass - actualKey.precurmass
				#res = toleranceMS.getTinDA(listSE[entry].precurmass)
				res = toleranceMS

				M4found = []
				M3found = []
				M2found = []
				M1found = []

				while delta <= 5 * cID:

					if (4 * cID <= delta + res and\
						4 * cID >= delta - res):
						M4found.append(nextKey)

					if 3 * cID <= delta + res and\
						3 * cID >= delta - res:
						M3found.append(nextKey)

					if (2 * cID <= delta + res and\
						2 * cID >= delta - res):
						M2found.append(nextKey)

					if 1 * cID <= delta + res and\
						1 * cID >= delta - res:
						M1found.append(nextKey)

					keyIndex += 1
					if keyIndex < len(listSE):
						nextKey = listSE[keyIndex]
						delta = nextKey.precurmass - actualKey.precurmass
					else:
						break

				# collect the overlapping peaks
				# listM => [[M+1], [M+2], [M+3], [M+4]]
				listM = [{}, {}, {}, {}, {}]
				listPIS = []

				for msmse in actualKey.listMSMS:
					for mark in msmse.listMark:
						if not mark.chemsc is None and not mark.nlsc is None and not mark.frsc is None:
							listM[0]['%s' % mark.chemsc] = [mark, []]
							if not mark.chemsc in listPIS:
								listPIS.append(mark.chemsc)

				if M1found != []:
					for msmse in M1found[0].listMSMS:
						for mark in msmse.listMark:
							if not mark.chemsc is None and not mark.nlsc is None and not mark.frsc is None:
								listM[1]['%s' % mark.chemsc] = [mark, []]
				if M2found != []:
					for msmse in M2found[0].listMSMS:
						for mark in msmse.listMark:
							if not mark.chemsc is None and not mark.nlsc is None and not mark.frsc is None:
								listM[2]['%s' % mark.chemsc] = [mark, []]

				if M3found != []:
					for msmse in M3found[0].listMSMS:
						for mark in msmse.listMark:
							if not mark.chemsc is None and not mark.nlsc is None and not mark.frsc is None:
								listM[3]['%s' % mark.chemsc] = [mark, []]

				if M4found != []:
					for msmse in M4found[0].listMSMS:
						for mark in msmse.listMark:
							if not mark.chemsc is None and not mark.nlsc is None and not mark.frsc is None:
								listM[4]['%s' % mark.chemsc] = [mark, []]

				# test for several marks on a single fragment
				for M in listM:
					for pis1 in M.keys():
						for pis2 in M.keys():
							if M[pis1][0].mass == M[pis2][0].mass and pis1 != pis2:
								print "Doubly marked entry"

				# the following has to be done also for MSMS: separate the charges
				# of the fragments
				#for scomp in listSE[entry].listPrecurmassSF:

				#	# sort precurmass sum compositions by charge
				#	if not chargePrecurmassSF.has_key("%d" % abs(scomp.charge)):
				#		chargePrecurmassSF["%d" % abs(scomp.charge)] = []
				#	chargePrecurmassSF["%d" % abs(scomp.charge)].append(scomp)

				### go through all pis and calculate the fragments isotopic distribution in Mtx. This ###
				### is then stored in dictPIS[pis][1].												  ###
				for pis in listM[0].keys():

					if not listM[0][pis][0].chemsc:
						break

					if not listM[0][pis][0].nlsc:
						break

					if not listM[0][pis][0].frsc:
						break

					# takes the values for the isotopes from the neutral loss of M, where (M->I1->I2->...)
					if (M4found != [] or M3found != [] or M2found != [] or M1found != []):

						gotOne = False

						if listM[0][pis][0].isnl:
							elemComp = listM[0][pis][0].nlsc
							elemCompNL = listM[0][pis][0].frsc

						else:
							elemComp = listM[0][pis][0].frsc
							elemCompNL = listM[0][pis][0].nlsc

						# elemetal composition
						if elemComp['H']:
							elemH = elemComp['H']
						else:
							elemH = 0
						if elemComp['C']:
							elemC = elemComp['C']
						else:
							elemC = 0
						if elemComp['O']:
							elemO = elemComp['O']
						else:
							elemO = 0
						if elemComp['N']:
							elemN = elemComp['N']
						else:
							elemN = 0
						if elemComp['S']:
							elemS = elemComp['S']
						else:
							elemS = 0
						if elemComp['P']:
							elemP = elemComp['P']
						else:
							elemP = 0
						# elemental composition of neutral loss
						if elemCompNL['H']:
							elemHNL = elemCompNL['H']
						else:
							elemHNL = 0
						if elemCompNL['C']:
							elemCNL = elemCompNL['C']
						else:
							elemCNL = 0
						if elemCompNL['O']:
							elemONL = elemCompNL['O']
						else:
							elemONL = 0
						if elemCompNL['N']:
							elemNNL = elemCompNL['N']
						else:
							elemNNL = 0
						if elemCompNL['S']:
							elemSNL = elemCompNL['S']
						else:
							elemSNL = 0
						if elemCompNL['P']:
							elemPNL = elemCompNL['P']
						else:
							elemPNL = 0

						if Debug("isotopicCorrection"):
							dbgstr  = "\n"
							dbgstr += "\n*  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *"
							dbgstr += "\n"
							dbgstr += "\nFrag %s with %.4f has intensity:" % (repr(listM[0][pis][0]), listM[0][pis][0].mass)
							for k in listM[0][pis][0].msmse.dictIntensity:
								dbgstr += "\n %.4f " % listM[0][pis][0].msmse.dictIntensity[k]
							dbgstr += "\n"
							dbgstr += "\nPrecur: %s %s" % (listM[0][pis][0].se[0].precurmass, listM[0][pis][0].se[0].listPrecurmassSF)

							dbgstr += "\nPIS: %s" % (pis)
							dbgout(dbgstr)

						(Mtx, monoisotopic) = isotopicValuesInter(elemC, elemH, elemO, elemN, elemS, elemP, elemCNL, elemHNL, elemONL, elemNNL, elemSNL, elemPNL)
						listM[0][pis][1] = Mtx

						if Debug("isotopicCorrection"):
							dbgout("\nNLS: %s" % (elemCompNL))

						if Debug("isotopicCorrection"):
							dbgstr = "F:%s; N:%s\n ------------- \n" % (repr(elemComp), repr(elemCompNL))
							dbgstr += "     F0N0: %.4f\n" % Mtx[0][0]
							dbgstr += "     F0N1: %.4f, F1N0: %.4f\n" % (Mtx[0][1], Mtx[1][0])
							dbgstr += "     F0N2: %.4f, F1N1: %.4f, F2N0: %.4f\n" % (Mtx[0][2], Mtx[1][1], Mtx[2][0])
							dbgstr += "     F0N3: %.4f, F1N2: %.4f, F2N1: %.4f, F3N0: %.4f\n" % (Mtx[0][3], Mtx[1][2], Mtx[2][1], Mtx[3][0])
							dbgstr += "     F0N4: %.4f, F1N3: %.4f, F2N2: %.4f, F3N1: %.4f, F4N0: %.4f\n" % (Mtx[0][4], Mtx[1][3], Mtx[2][2], Mtx[3][1], Mtx[4][0])
							dbgout(dbgstr)


						F0N0 = Mtx[0][0]
						F0N1 = Mtx[0][1]
						F0N2 = Mtx[0][2]
						F0N3 = Mtx[0][3]
						F0N4 = Mtx[0][4]

						F1N0 = Mtx[1][0]
						F1N1 = Mtx[1][1]
						F1N2 = Mtx[1][2]
						F1N3 = Mtx[1][3]

						F2N0 = Mtx[2][0]
						F2N1 = Mtx[2][1]
						F2N2 = Mtx[2][2]

						F3N0 = Mtx[3][0]
						F3N1 = Mtx[3][1]

						F4N0 = Mtx[4][0]

						if M1found != []:

							M = listM[0][pis][0] # listPIS[0] == M1found

							if listM[1].has_key(pis):

								M1 = listM[1][pis][0] # listPIS[0] == M1found

								# prevent double correction
								isIn = False

								# listPIS[0] == M1found fragments
								if M1.msmse.isCorrectedIsotopic.has_key('1'):

									for name in M1.listNames:
										if name in M1.msmse.isCorrectedIsotopic['1']:
											isIn = True

								if not isIn:

									############################
									### Interscan correction ###
									############################

									# store original intensity for dump
									if M1.msmse.dictBeforeIsocoIntensity == {}:
										M1.msmse.dictBeforeIsocoIntensity = deepcopy(M1.msmse.dictIntensity)

									# correct the found fragment intensity
									for k in M1.msmse.dictIntensity.keys():

										if M1.msmse.dictIntensity[k] > 0.0 and M.msmse.dictIntensity[k] > 0.0:
											M1.msmse.dictIntensity[k] = M1.msmse.dictIntensity[k] - M.msmse.dictIntensity[k] * F0N1
											M1.msmse.dictIntensity[k]

										if not Debug("isotopicCorrection"):
											if M1.msmse.dictIntensity[k] < 0.0:
												M1.msmse.dictIntensity[k] = -1

									if M1.msmse.isCorrectedIsotopic.has_key('1'):
										M1.msmse.isCorrectedIsotopic['1'] += M1.listNames
									else:
										M1.msmse.isCorrectedIsotopic['1'] = M1.listNames

									if Debug("isotopicCorrection"):
										dbgstr = "Frag <F0N1> found -> PRC: %.4f MSMS: %.4f '%s' corrected to" % (M1found[0].precurmass, M1.msmse.mass, M1.name)
										for k in M1.msmse.dictIntensity:
											 dbgstr += " %.4f (-%.4f);" % (M1.msmse.dictIntensity[k], M.msmse.dictIntensity[k] * F0N1)
										dbgstr += "\n"
										dbgout(dbgstr)

							############################
							### Intrascan correction ###
							############################

							# index marks for isotope overlapped fragments
							MSMS1found = []

							index = 0
							next = 0

							# let listMSMS be the spectra coming after l.msmse
							# <It is no problem to take l.se[0] because the listMSMS is
							#  the same for all entries of l.se>
							listMSMS = [x for x in M1found[0].listMSMS if x.mass >= M.mass]

							while index + next < (len(listMSMS)):

								res = toleranceMSMS.getTinDA(M.mass)
								monoisotopicPeak = M.mass
								isotopicPeak = listMSMS[index + next].mass
								delta = isotopicPeak - monoisotopicPeak

								if delta <= 4 * cID:

									if 1.0033 <= isotopicPeak - monoisotopicPeak + res / 2 and\
										1.0033 >= isotopicPeak - monoisotopicPeak - res / 2:
										MSMS1found.append(listMSMS[index + next])

								next += 1
								if index + next >= len(listMSMS):
									break

							if MSMS1found != []:
								for M1f in MSMS1found:

									isIn = False
									if M1f.isCorrectedIsotopic.has_key('1i'):
										for name in M1f.listNames:
											if name in M1f.isCorrectedIsotopic['1i']:
												isIn = True

									if not isIn:

										# store original intensity for dump
										if M1f.dictBeforeIsocoIntensity == {}:
											M1f.dictBeforeIsocoIntensity = deepcopy(M1f.dictIntensity)

										# correct the found fragment intensity
										for k in M1f.dictIntensity.keys():

											if M1f.dictIntensity[k] > 0.0 and M1f.dictIntensity[k] > 0.0:
												M1f.dictIntensity[k] = M1f.dictIntensity[k] - M.msmse.dictIntensity[k] * F1N0
											if not Debug("isotopicCorrection"):
												if M1f.dictIntensity[k] < 0.0:
													M1f.dictIntensity[k] = -1

										if M1f.isCorrectedIsotopic.has_key('1i'):
											M1f.isCorrectedIsotopic['1i'] += M1f.listNames
										else:
											M1f.isCorrectedIsotopic['1i'] = M1f.listNames

										if Debug("isotopicCorrection"):
											dbgstr = "Frag <F1N0> found -> PRC: %.4f MSMS: %.4f '%s' corrected to" % (M1found[0].precurmass, M1f.mass, M1f.listNames)
											for k in M1f.dictIntensity:
												dbgstr += " %.4f (-%.4f);" % (M1f.dictIntensity[k], M.msmse.dictIntensity[k] * F1N0)
											dbgstr += "\n"
											dbgout(dbgstr)

						if M2found != []:

							M = listM[0][pis][0]

							if listM[2].has_key(pis):

								M2 = listM[2][pis][0]

								isIn = False
								if M2.msmse.isCorrectedIsotopic.has_key('2'):
									for name in M2.listNames:
										if name in M2.msmse.isCorrectedIsotopic['2']:
											isIn = True

								if not isIn:

									# store original intensity for dump
									if M2.msmse.dictBeforeIsocoIntensity == {}:
										M2.msmse.dictBeforeIsocoIntensity = deepcopy(M2.msmse.dictIntensity)

									for k in M2.msmse.dictIntensity.keys():

										if M2.msmse.dictIntensity[k] > 0.0 and M.msmse.dictIntensity[k] > 0.0:
											M2.msmse.dictIntensity[k] = M2.msmse.dictIntensity[k] - M.msmse.dictIntensity[k] * F0N2

										if not Debug("isotopicCorrection"):
											if M2.msmse.dictIntensity[k] < 0.0:
												M2.msmse.dictIntensity[k] = -1

									if M2.msmse.isCorrectedIsotopic.has_key('2'):
										M2.msmse.isCorrectedIsotopic['2'] += M2.listNames
									else:
										M2.msmse.isCorrectedIsotopic['2'] = M2.listNames

									if Debug("isotopicCorrection"):
										dbgstr = "Frag <F0N2> found -> PRC: %.4f MSMS: %.4f '%s' corrected to" % (M2found[0].precurmass, M2.msmse.mass, M2.name)
										for k in M2.msmse.dictIntensity:
											dbgstr += " %.4f (-%.4f);" % (M2.msmse.dictIntensity[k], M.msmse.dictIntensity[k] * F0N2)
										dbgstr += "\n"
										dbgout(dbgstr)


							############################
							### Intrascan correction ###
							############################

							# index marks for isotope overlapped fragments
							MSMS2found = []
							MSMS1found = []

							index = 0
							next = 0

							# let listMSMS be the spectra coming after l.msmse
							# <It is no problem to take l.se[0] because the listMSMS is
							#  the same for all entries of l.se>
							listMSMS = [x for x in M2found[0].listMSMS if x.mass >= M.mass]

							while index + next < (len(listMSMS)):

								res = toleranceMSMS.getTinDA(M.mass)
								monoisotopicPeak = M.mass#listMSMS[index].mass
								isotopicPeak = listMSMS[index + next].mass
								delta = isotopicPeak - monoisotopicPeak

								if delta <= 4 * cID:

									if 2.0066 <= isotopicPeak - monoisotopicPeak + res and\
										2.0066 >= isotopicPeak - monoisotopicPeak - res:
										MSMS2found.append(listMSMS[index + next])

									if 1.0033 <= isotopicPeak - monoisotopicPeak + res and\
										1.0033 >= isotopicPeak - monoisotopicPeak - res:
										MSMS1found.append(listMSMS[index + next])

								next += 1
								if index + next >= len(listMSMS):
									break

							if MSMS1found != []:
								for M1f in MSMS1found:

									isIn = False
									if M1f.isCorrectedIsotopic.has_key('1i'):
										for name in M1f.listNames:
											if name in M1f.isCorrectedIsotopic['1i']:
												isIn = True

									if not isIn:

										# store original intensity for dump
										if M1f.dictBeforeIsocoIntensity == {}:
											M1f.dictBeforeIsocoIntensity = deepcopy(M1f.dictIntensity)

										# correct the found fragment intensity
										for k in M1f.dictIntensity.keys():

											if M1f.dictIntensity[k] > 0.0 and M1f.dictIntensity[k] > 0.0:
												M1f.dictIntensity[k] = M1f.dictIntensity[k] - M.msmse.dictIntensity[k] * F1N1
											if not Debug("isotopicCorrection"):
												if M1f.dictIntensity[k] < 0.0:
													M1f.dictIntensity[k] = -1

										if M1f.isCorrectedIsotopic.has_key('1i'):
											M1f.isCorrectedIsotopic['1i'] += M1f.listNames
										else:
											M1f.isCorrectedIsotopic['1i'] = M1f.listNames

										if Debug("isotopicCorrection"):
											dbgstr = "Frag <F1N1> found -> PRC: %.4f MSMS: %.4f '%s' corrected to" % (M2found[0].precurmass, M1f.mass, M1f.listNames)
											for k in M1f.dictIntensity:
												dbgstr += " %.4f (-%.4f);" % (M1f.dictIntensity[k], M.msmse.dictIntensity[k] * F1N1)
											dbgstr += "\n"
											dbgout(dbgstr)

							if MSMS2found != []:
								for M2f in MSMS2found:

									isIn = False
									if M2f.isCorrectedIsotopic.has_key('2i'):
										for name in M2f.listNames:
											if name in M2f.isCorrectedIsotopic['2i']:
												isIn = True

									if not isIn:

										# store original intensity for dump
										if M2f.dictBeforeIsocoIntensity == {}:
											M2f.dictBeforeIsocoIntensity = deepcopy(M2f.dictIntensity)

										# correct the found fragment intensity
										for k in M2f.dictIntensity.keys():

											if M2f.dictIntensity[k] > 0.0:
												M2f.dictIntensity[k] = M2f.dictIntensity[k] - M.msmse.dictIntensity[k] * F2N0
											if not Debug("isotopicCorrection"):
												if M2f.dictIntensity[k] < 0.0:
													M2f.dictIntensity[k] = -1

										if M2f.isCorrectedIsotopic.has_key('2i'):
											M2f.isCorrectedIsotopic['2i'] += M2f.listNames
										else:
											M2f.isCorrectedIsotopic['2i'] = M2f.listNames

										if Debug("isotopicCorrection"):
											dbgstr = "Frag <F2N0> found -> PRC: %.4f MSMS: %.4f '%s' corrected to" % (M2found[0].precurmass, M2f.mass, M2f.listNames)
											for k in M2f.dictIntensity:
												dbgstr += " %.4f (-%.4f);" % (M2f.dictIntensity[k], M.msmse.dictIntensity[k] * F2N0)
											dbgstr += "\n"
											dbgout(dbgstr)


						if M3found != [] and listM[3].has_key(pis):

							M = listM[0][pis][0]

							if listM[3].has_key(pis):

								M3 = listM[3][pis][0]

								isIn = False
								if M3.msmse.isCorrectedIsotopic.has_key('3'):
									for name in M3.listNames:
										if name in M3.msmse.isCorrectedIsotopic['3']:
											isIn = True

								if not isIn:

									# store original intensity for dump
									if M3.msmse.dictBeforeIsocoIntensity == {}:
										M3.msmse.dictBeforeIsocoIntensity = deepcopy(M3.msmse.dictIntensity)

									for k in M3.msmse.dictIntensity.keys():

										if M3.msmse.dictIntensity[k] > 0.0 and M.msmse.dictIntensity[k] > 0.0:
											M3.msmse.dictIntensity[k] = M3.msmse.dictIntensity[k] - M.msmse.dictIntensity[k] * F0N3

										if not Debug("isotopicCorrection"):
											if M3.msmse.dictIntensity[k] < 0.0:
												M3.msmse.dictIntensity[k] = -1

									if M3.msmse.isCorrectedIsotopic.has_key('3'):
										M3.msmse.isCorrectedIsotopic['3'] += M3.listNames
									else:
										M3.msmse.isCorrectedIsotopic['3'] = M3.listNames

									if Debug("isotopicCorrection"):
										dbgstr = "Frag <F0N3> found -> PRC: %.4f MSMS: %.4f '%s' corrected to" % (M3found[0].precurmass, M3.msmse.mass, M3.name)

										for k in M3.msmse.dictIntensity:
											dbgstr += " %.4f (-%.4f);" % (M3.msmse.dictIntensity[k], M.msmse.dictIntensity[k] * F0N3)
										dbgstr += "\n"
										dbgout(dbgstr)

							############################
							### Intrascan correction ###
							############################

							# index marks for isotope overlapped fragments
							MSMS3found = []
							MSMS2found = []
							MSMS1found = []

							resolution = self.mfqlObj.options['MSMSresolution'].tolerance
							index = 0
							next = 0

							# let listMSMS be the spectra coming after l.msmse
							# <It is no problem to take l.se[0] because the listMSMS is
							#  the same for all entries of l.se>
							listMSMS = [x for x in M3found[0].listMSMS if x.mass >= M.mass]

							while index + next < (len(listMSMS)):

								res = toleranceMSMS.getTinDA(M.mass)
								monoisotopicPeak = M.mass
								isotopicPeak = listMSMS[index + next].mass

								if isotopicPeak - monoisotopicPeak - res < 4 * 1.0033:

									if 3.0099 <= isotopicPeak - monoisotopicPeak + res and\
										3.0099 >= isotopicPeak - monoisotopicPeak - res:
										MSMS3found.append(listMSMS[index + next])

									if 2.0066 <= isotopicPeak - monoisotopicPeak + res and\
										2.0066 >= isotopicPeak - monoisotopicPeak - res:
										MSMS2found.append(listMSMS[index + next])

									if 1.0033 <= isotopicPeak - monoisotopicPeak + res and\
										1.0033 >= isotopicPeak - monoisotopicPeak - res:
										MSMS1found.append(listMSMS[index + next])

								next += 1
								if index + next >= len(listMSMS):
									break

							if MSMS1found != []:
								for M1f in MSMS1found:

									isIn = False
									if M1f.isCorrectedIsotopic.has_key('1i'):
										for name in M1f.listNames:
											if name in M1f.isCorrectedIsotopic['1i']:
												isIn = True

									if not isIn:

										# store original intensity for dump
										if M1f.dictBeforeIsocoIntensity == {}:
											M1f.dictBeforeIsocoIntensity = deepcopy(M1f.dictIntensity)

										# correct the found fragment intensity
										for k in M1f.dictIntensity.keys():

											if M1f.dictIntensity[k] > 0.0 and M1f.dictIntensity[k] > 0.0:
												M1f.dictIntensity[k] = M1f.dictIntensity[k] - M.msmse.dictIntensity[k] * F1N2
											if not Debug("isotopicCorrection"):
												if M1f.dictIntensity[k] < 0.0:
													M1f.dictIntensity[k] = -1

										if M1f.isCorrectedIsotopic.has_key('1i'):
											M1f.isCorrectedIsotopic['1i'] += M1f.listNames
										else:
											M1f.isCorrectedIsotopic['1i'] = M1f.listNames

										if Debug("isotopicCorrection"):
											dbgstr = "Frag <F1N2> found ->PRC: %.4f MSMS: %.4f '%s' corrected to" % (M3found[0].precurmass, M1f.mass, M1f.listNames)
											for k in M1f.dictIntensity:
												dbgstr += " %.4f (-%.4f);" % (M1f.dictIntensity[k], M.msmse.dictIntensity[k] * F1N2)
											dbgstr += "\n"
											dbgout(dbgstr)

							if MSMS2found != []:
								for M2f in MSMS2found:

									isIn = False
									if M2f.isCorrectedIsotopic.has_key('2i'):
										for name in M2f.listNames:
											if name in M2f.isCorrectedIsotopic['2i']:
												isIn = True

									if not isIn:

										# store original intensity for dump
										if M2f.dictBeforeIsocoIntensity == {}:
											M2f.dictBeforeIsocoIntensity = deepcopy(M2f.dictIntensity)

										# correct the found fragment intensity
										for k in M2f.dictIntensity.keys():

											if M2f.dictIntensity[k] > 0.0 and M2f.dictIntensity[k] > 0.0:
												M2f.dictIntensity[k] = M2f.dictIntensity[k] - M.msmse.dictIntensity[k] * F2N1
											if not Debug("isotopicCorrection"):
												if M2f.dictIntensity[k] < 0.0:
													M2f.dictIntensity[k] = -1

										if M2f.isCorrectedIsotopic.has_key('2i'):
											M2f.isCorrectedIsotopic['2i'] += M2f.listNames
										else:
											M2f.isCorrectedIsotopic['2i'] = M2f.listNames

										if Debug("isotopicCorrection"):
											dbgstr = "Frag <F2N1> found -> PRC: %.f4 MSMS: %.4f '%s' corrected to" % (M3found[0].precurmass, M2f.mass, M2f.listNames)
											for k in M2f.dictIntensity:
												dbgstr += " %.4f (-%.4f);" % (M2f.dictIntensity[k], M.msmse.dictIntensity[k] * F2N1)
											dbgstr += "\n"
											dbgout(dbgstr)


							if MSMS3found != []:
								for M3f in MSMS3found:

									isIn = False
									if M3f.isCorrectedIsotopic.has_key('3i'):
										for name in M3f.listNames:
											if name in M3f.isCorrectedIsotopic['3i']:
												isIn = True

									if not isIn:

										# store original intensity for dump
										if M3f.dictBeforeIsocoIntensity == {}:
											M3f.dictBeforeIsocoIntensity = deepcopy(M3f.dictIntensity)

										# correct the found fragment intensity
										for k in M3f.dictIntensity.keys():

											if M3f.dictIntensity[k] > 0.0 and M3f.dictIntensity[k] > 0.0:
												M3f.dictIntensity[k] = M3f.dictIntensity[k] - M.msmse.dictIntensity[k] * F3N0
											if not Debug("isotopicCorrection"):
												if M3f.dictIntensity[k] < 0.0:
													M3f.dictIntensity[k] = -1

										if M3f.isCorrectedIsotopic.has_key('3i'):
											M3f.isCorrectedIsotopic['3i'] += M3f.listNames
										else:
											M3f.isCorrectedIsotopic['3i'] = M3f.listNames

										if Debug("isotopicCorrection"):
											dbgstr = "Frag <F3N0> found -> PRC: %.4f MSMS: %.4f '%s' corrected to" % (M3found[0].precurmass, M3f.mass, M3f.listNames)
											for k in M3f.dictIntensity:
												dbgstr += " %.4f (-%.4f);" % (M3f.dictIntensity[k], M.msmse.dictIntensity[k] * F3N0)
											dbgstr += "\n"
											dbgout(dbgstr)


						if M4found != []:

							M = listM[0][pis][0]

							if listM[4].has_key(pis):

								M4 = listM[4][pis][0]

								isIn = False
								if M4.msmse.isCorrectedIsotopic.has_key('4'):
									for name in M4.listNames:
										if name in M4.msmse.isCorrectedIsotopic['4']:
											isIn = True

								if not isIn:

									# store original intensity for dump
									if M4.msmse.dictBeforeIsocoIntensity == {}:
										M4.msmse.dictBeforeIsocoIntensity = deepcopy(M4.msmse.dictIntensity)

									for k in M4.msmse.dictIntensity.keys():

										if M4.msmse.dictIntensity[k] > 0.0 and M.msmse.dictIntensity[k] > 0.0:
											M4.msmse.dictIntensity[k] = M4.msmse.dictIntensity[k] - M.msmse.dictIntensity[k] * F0N4

										if not Debug("isotopicCorrection"):
											if M4.msmse.dictIntensity[k] < 0.0:
												M4.msmse.dictIntensity[k] = -1

									if M4.msmse.isCorrectedIsotopic.has_key('4'):
										M4.msmse.isCorrectedIsotopic['4'] += M4.listNames
									else:
										M4.msmse.isCorrectedIsotopic['4'] = M4.listNames

									if Debug("isotopicCorrection"):
										dbgstr = "Frag <F0N4> found -> PRC: %.4f MSMS: %.4f '%s' corrected to" % (M4found[0].precurmass, M4.msmse.mass, M4.name)
										for k in M4.msmse.dictIntensity:
											dbgstr += " %.4f (-%.4f);" % (M4.msmse.dictIntensity[k], M.msmse.dictIntensity[k] * F0N4)
										dbgstr += "\n"
										dbgout(dbgstr)

							############################
							### Intrascan correction ###
							############################

							# index marks for isotope overlapped fragments
							MSMS4found = []
							MSMS3found = []
							MSMS2found = []
							MSMS1found = []

							index = 0
							next = 0

							# let listMSMS be the spectra coming after l.msmse
							# <It is no problem to take l.se[0] because the listMSMS is
							#  the same for all entries of l.se>
							listMSMS = [x for x in M4found[0].listMSMS if x.mass >= M.mass]

							while index + next < (len(listMSMS)):

								res = toleranceMSMS.getTinDA(M.mass)
								monoisotopicPeak = M.mass
								isotopicPeak = listMSMS[index + next].mass

								if isotopicPeak - monoisotopicPeak - res < 5 * 1.0033:

									if 4.0122 <= isotopicPeak - monoisotopicPeak + res and\
										4.0122 >= isotopicPeak - monoisotopicPeak - res:
										MSMS4found.append(listMSMS[index + next])

									if 3.0099 <= isotopicPeak - monoisotopicPeak + res and\
										3.0099 >= isotopicPeak - monoisotopicPeak - res:
										MSMS3found.append(listMSMS[index + next])

									if 2.0066 <= isotopicPeak - monoisotopicPeak + res and\
										2.0066 >= isotopicPeak - monoisotopicPeak - res:
										MSMS2found.append(listMSMS[index + next])

									if 1.0033 <= isotopicPeak - monoisotopicPeak + res and\
										1.0033 >= isotopicPeak - monoisotopicPeak - res:
										MSMS1found.append(listMSMS[index + next])

								next += 1
								if index + next >= len(listMSMS):
									break

							if MSMS1found != []:
								for M1f in MSMS1found:

									isIn = False
									if M1f.isCorrectedIsotopic.has_key('1i'):
										for name in M1f.listNames:
											if name in M1f.isCorrectedIsotopic['1i']:
												isIn = True

									if not isIn:

										# store original intensity for dump
										if M1f.dictBeforeIsocoIntensity == {}:
											M1f.dictBeforeIsocoIntensity = deepcopy(M1f.dictIntensity)

										# correct the found fragment intensity
										for k in M1f.dictIntensity.keys():

											if M1f.dictIntensity[k] > 0.0 and M1f.dictIntensity[k] > 0.0:
												M1f.dictIntensity[k] = M1f.dictIntensity[k] - M.msmse.dictIntensity[k] * F1N3
											if not Debug("isotopicCorrection"):
												if M1f.dictIntensity[k] < 0.0:
													M1f.dictIntensity[k] = -1

										if M1f.isCorrectedIsotopic.has_key('1i'):
											M1f.isCorrectedIsotopic['1i'] += M1f.listNames
										else:
											M1f.isCorrectedIsotopic['1i'] = M1f.listNames

										if Debug("isotopicCorrection"):
											dbgstr = "Frag <F1N3> found -> PRC: %.4f MSMS: %.4f '%s' corrected to" % (M4found[0].precurmass, M1f.mass, M1f.listNames)
											for k in M1f.dictIntensity:
												dbgstr += " %.4f (-%.4f);" % (M1f.dictIntensity[k], M.msmse.dictIntensity[k] * F1N3)
											dbgstr += "\n"
											dbgout(dbgstr)


							if MSMS2found != []:
								for M2f in MSMS2found:

									isIn = False
									if M2f.isCorrectedIsotopic.has_key('2i'):
										for name in M2f.listNames:
											if name in M2f.isCorrectedIsotopic['2i']:
												isIn = True

									if not isIn:

										# store original intensity for dump
										if M2f.dictBeforeIsocoIntensity == {}:
											M2f.dictBeforeIsocoIntensity = deepcopy(M2f.dictIntensity)

										# correct the found fragment intensity
										for k in M2f.dictIntensity.keys():

											if M2f.dictIntensity[k] > 0.0 and M2f.dictIntensity[k] > 0.0:
												M2f.dictIntensity[k] = M2f.dictIntensity[k] - M.msmse.dictIntensity[k] * F2N2
											if not Debug("isotopicCorrection"):
												if M2f.dictIntensity[k] < 0.0:
													M2f.dictIntensity[k] = -1

										if M2f.isCorrectedIsotopic.has_key('2i'):
											M2f.isCorrectedIsotopic['2i'] += M2f.listNames
										else:
											M2f.isCorrectedIsotopic['2i'] = M2f.listNames

										if Debug("isotopicCorrection"):
											dbgstr = "Frag <F2N2> found -> PRC: %.4f MSMS: %.4f '%s' corrected to" % (M4found[0].precurmass, M2f.mass, M2f.listNames)
											for k in M2f.dictIntensity:
												dbgstr += " %.4f (-%.4f);" % (M2f.dictIntensity[k], M.msmse.dictIntensity[k] * F2N2)
											dbgstr += "\n"
											dbgout(dbgstr)


							if MSMS3found != []:
								for M3f in MSMS3found:

									isIn = False
									if M3f.isCorrectedIsotopic.has_key('3i'):
										for name in M3f.listNames:
											if name in M3f.isCorrectedIsotopic['3i']:
												isIn = True

									if not isIn:

										# store original intensity for dump
										if M3f.dictBeforeIsocoIntensity == {}:
											M3f.dictBeforeIsocoIntensity = deepcopy(M3f.dictIntensity)

										# correct the found fragment intensity
										for k in M3f.dictIntensity.keys():

											if M3f.dictIntensity[k] > 0.0 and M3f.dictIntensity[k] > 0.0:
												M3f.dictIntensity[k] = M3f.dictIntensity[k] - M.msmse.dictIntensity[k] * F3N1
											if not Debug("isotopicCorrection"):
												if M3f.dictIntensity[k] < 0.0:
													M3f.dictIntensity[k] = -1

										if M3f.isCorrectedIsotopic.has_key('3i'):
											M3f.isCorrectedIsotopic['3i'] += M3f.listNames
										else:
											M3f.isCorrectedIsotopic['3i'] = M3f.listNames

										if Debug("isotopicCorrection"):
											dbgstr = "Frag <F3N1> found -> PRC: %.4f MSMS: %.4f '%s' corrected to" % (M4found[0].precurmass, M3f.mass, M3f.listNames)
											for k in M3f.dictIntensity:
												dbgstr += " %.4f (-%.4f);" % (M3f.dictIntensity[k], M.msmse.dictIntensity[k] * F3N1)
											dbgstr += "\n"
											dbgout(dbgstr)

							if MSMS4found != []:
								for M4f in MSMS4found:

									isIn = False
									if M4f.isCorrectedIsotopic.has_key('4i'):
										for name in M4f.listNames:
											if name in M4f.isCorrectedIsotopic['4i']:
												isIn = True

									if not isIn:

										# store original intensity for dump
										if M4f.dictBeforeIsocoIntensity == {}:
											M4f.dictBeforeIsocoIntensity = deepcopy(M4f.dictIntensity)

										# correct the found fragment intensity
										for k in M4f.dictIntensity.keys():

											if M4f.dictIntensity[k] > 0.0 and M4f.dictIntensity[k] > 0.0:
												M4f.dictIntensity[k] = M4f.dictIntensity[k] - M.msmse.dictIntensity[k] * F4N0
											if not Debug("isotopicCorrection"):
												if M4f.dictIntensity[k] < 0.0:
													M4f.dictIntensity[k] = -1

										if M4f.isCorrectedIsotopic.has_key('4i'):
											M4f.isCorrectedIsotopic['4i'] += M4f.listNames
										else:
											M4f.isCorrectedIsotopic['4i'] = M4f.listNames

										if Debug("isotopicCorrection"):
											dbgstr = "Frag <F4N0> found -> PRC: %.4f MSMS: %.4f '%s' corrected to" % (M4found[0].precurmass, M4f.mass, M4f.listNames)
											for k in M4f.dictIntensity:
												dbgstr += " %.4f (-%.4f);" % (M4f.dictIntensity[k], M.msmse.dictIntensity[k] * F4N0)
											dbgstr += "\n"
											dbgout(dbgstr)


	def generateReport(self, options = {}):

		noString = re.compile(r'\[(\w+)\]', re.VERBOSE)

		self.listHead = []
		connector = self.mfqlObj.namespaceConnector

		# every query
		for query in self.dictQuery.values():

			self.mfqlObj.currQuery = query
			self.mfqlObj.queryName = query.name

			if query.listVariables != []:
				self.mfqlOutput = True

			### TODO 20.08.2008: variables muessen auf query.sc zugreifen ###
			# every identified set of variables
			for vars in query.listVariables:

				self.mfqlObj.currVars = vars

				boolAdd = True
				rpt = odict()

				# every report variable
				for report in query.listReport:

					# the report entry is a string format
					if len(report) == 3:

						# generate objects for report
						for v in vars:
							if vars[v]:
								globals()[v] = vars[v]

						varsShort = []
						for v in vars.keys():
							varsShort.append('%s' % v.split(connector)[1])
						for i in varsShort:
							for j in varsShort:
								if i != j:
									if re.match(i, j):
										raise LipidXException('vars: %s <-> %s. No variable name is allowed to be contained in another one' % (i,j))

						# if list is not given as string
						if isinstance(report[2], type([])):

							listAttributes = []

							for entry in report[2]:

								#namespacedVariable = self.mfqlObj.queryName + self.mfqlObj.namespaceConnector + entry.variable
								#if self.mfqlObj.currVars.has_key(namespacedVariable) and not self.mfqlObj.currVars[namespacedVariable] is None:

								if isinstance(entry, TypeVariable):
									tmpRpt = TypeExpression(
										isSingleton = True,
										leftSide = entry,
										rightSide = None,
										operator = None,
										environment = self.mfqlObj.queryName,
										mfqlObj = self.mfqlObj).evaluate(mode = None, scane = None, vars = self.mfqlObj.currVars, queryName = self.mfqlObj.queryName, sc = query.sc)
								elif isinstance(entry, TypeExpression) or isinstance(entry, TypeElementSequence):
									tmpRpt = entry.evaluate(mode = None, scane = None, vars = self.mfqlObj.currVars, queryName = self.mfqlObj.queryName, sc = query.sc)
								else:
									raise LipidXException("Error with data type in REPORT")

								if tmpRpt is None:
									raise LipidXException("Something wrong in query %s with "\
											"variable %s." % (self.mfqlObj.queryName, entry.name))

								# check if report contains a dictionary like for the intensity
								if tmpRpt.isType(TYPE_DICT_INTENS):
									pass
								elif tmpRpt.isType(TYPE_STRING):
									listAttributes.append(tmpRpt.string)
								elif tmpRpt.isType(TYPE_CHEMSC):
									listAttributes.append(tmpRpt.chemsc.getWeight())
								else:
									listAttributes.append(tmpRpt.float)

							strCorr = '(%.9f' % listAttributes[0]
							for attr in listAttributes[1:]:
								strCorr += ",%.9f" % attr
							strCorr += ')'
							str = eval(report[1] + ' % ' + strCorr)

							rpt[report[0]] = str

						else:
							strReportVars = report[2]
							for v in vars.keys():
								strReportVars = re.sub('%s' % v.split(connector)[1], v, strReportVars)

							# make input more user friendly
							try:
								strCorr = noString.sub('[\'\g<1>\']', strReportVars.strip('"'))
								try:
									str = eval(report[1] + ' % ' + strCorr)
								except TypeError, detail:
									dbgout("TypeError in report %s: %s" % (report[0], detail))
									str = ''

								except AttributeError, detail:
									#log.error("AttributeError in report (%s): %s" % (report[0], detail), extra = {'func' : ''})
									str = ''

								except NameError, detail:
									#log.error("NameError in %s's report (%s): %s" % (query.name, report[0], detail), extra = {'func' : ''})
									str = ''

								rpt[report[0]] = str

							except NameError:
								boolAdd = False

							except SyntaxError, detail:
								detail = "At variable %s in REPORT: %s" % (report[0], detail)
								raise SyntaxErrorException(detail,
										"",
										query.name,
										0)


					# the report entry is an expression
					elif len(report) == 2:

						if isinstance(report[1], TypeVariable):
							tmpRpt = TypeExpression(
								isSingleton = True,
								leftSide = report[1],
								rightSide = None,
								operator = None,
								environment = self.mfqlObj.queryName,
								mfqlObj = self.mfqlObj).evaluate(mode = None, scane = None, vars = self.mfqlObj.currVars, queryName = self.mfqlObj.queryName, sc = query.sc)

						elif isinstance(report[1], TypeExpression):
							tmpRpt = report[1].evaluate(mode = None, scane = None, vars = vars, queryName = self.mfqlObj.queryName, sc = query.sc, varname = report[0])

						elif isinstance(report[1], TypeFunction):
							#def evaluate(self, scane, vars, env):
							tmpRpt = report[1].evaluate(scane = None, vars = vars, env = None, queryName = self.mfqlObj.queryName, sc = query.sc)

						elif isinstance(report[1], TypeString):
							tmpRpt = TypeTmpResult(
									options = None,
									chemsc = None,
									float = None,
									string = report[1].string,
									dictIntensity = None,
									type = TYPE_STRING
									)

						elif isinstance(report[1], TypeFloat):
							tmpRpt = TypeTmpResult(
									options = None,
									chemsc = None,
									float = report[1].float,
									string = None,
									dictIntensity = None,
									type = TYPE_FLOAT)

						else:
							tmpRpt = None

						if tmpRpt:
							# check if report contains a dictionary like for the intensity
							#if tmpRpt.dictIntensity:
							if tmpRpt.type == TYPE_DICT_INTENS:

								for k in self.mfqlObj.sc.listSamples:
									strK = '%s:%s' % (report[0], k)
									if tmpRpt.dictIntensity.has_key(k):
										rpt[strK] = "%.1f" % (tmpRpt.dictIntensity[k])
										#rpt[strK] = int(tmpRpt.dictIntensity[k])
									else:
										rpt[strK] = "0.0"#int(0.0)
							else:
								rpt[report[0]] = tmpRpt

						else:
							if report[1].attribute.lower() == 'intensity':
								for k in self.mfqlObj.sc.listSamples:
									strK = '%s:%s' % (report[0], k)
									rpt[strK] = None
							else:
								rpt[report[0]] = tmpRpt

				if query.reportHeads == []:
					query.reportHeads = rpt.keys()
				self.listHead = connectLists(self.listHead, query.reportHeads)

				# append the dict entry to the result list

				if boolAdd:
					query.listReportOut.append(rpt)

		# if there are results, then there is a self.listHead
		if self.listHead:

			for query in self.dictQuery.values():

				dataMatrix = TypeDataMatrix('')
				for key in self.listHead:
					dataMatrix.dataR[key] = []

				# csv with tabs or with commas ? ... As you wish !
				seperator = self.mfqlObj.outputSeperator

				str = ''
				for rpt in query.listReportOut:
					for key in self.listHead:
						if rpt.has_key(key):
							if key != rpt.keys()[-1]:
								str += "%s%s" % (rpt[key], seperator)
								dataMatrix.dataR[key].append(rpt[key])
							else:
								if key == self.listHead[-1]:
									str += "%s" % rpt[key]
									dataMatrix.dataR[key].append(rpt[key])
								else:
									str += "%s%s" % (rpt[key], seperator)
									dataMatrix.dataR[key].append(rpt[key])
						else:
							dataMatrix.dataR[key].append(None)
							#if str != '' and str[-2] != seperator:
							#	str += '%s' % seperator
							if not key == self.listHead[-1]:
								str += "None%s " % seperator
							else:
								str += "None"
					str += '\n'

				# copy the output string to the query object
				if str != "":
					mfqlOutput = True

				query.strOutput = str

				################################
				### process the  Data Matrix ###

				# a routine to put the precursor intensity to zero where
				# the fragment was not found

				# make a index
				length = 0
				for column in dataMatrix.dataR.keys():
					if len(dataMatrix.dataR[column]) > length:
						length = len(dataMatrix.dataR[column])

				dataMatrix.dataR['INDEX'] = []
				for i in range(length):
					dataMatrix.dataR['INDEX'].append(i)

				dataMatrix.initiate('INDEX')

				### correct precursor intensities ###
				# correct precursor intensities to zero, if there was no fragment
				if options['intensityCorrection']:
					precursorPrefix = options['intensityCorrectionPrecursor']
					fragmentPrefix = options['intensityCorrectionFragment']
					mPrecursorPrefix = re.compile('(%s.*):(.*)' % precursorPrefix)
					mFragmentPrefix = re.compile('(%s.*):(.*)' % fragmentPrefix)

					# go through the rows
					for i in range(length):

						# go through fragments
						for k in dataMatrix.dataR.keys():
							m = mFragmentPrefix.match(k)
							if m is not None:# == fragmentPrefix:
								if float(dataMatrix.dataR[k][i]) <= 0.0:

									# go through precursors, find the matching precursor
									for l in dataMatrix.dataR.keys():
										n = mPrecursorPrefix.match(l)
										if n is not None:# == fragmentPrefix:
											dataMatrix.dataR["%s:%s" % (n.group(1), m.group(2))][i] = "0.0"

						# go through precursors
						for k in dataMatrix.dataR.keys():
							m = mPrecursorPrefix.match(k)
							if m is not None:
								if float(dataMatrix.dataR[k][i]) <= 0.0:

									# go through precursors, find the matching precursor
									for l in dataMatrix.dataR.keys():
										n = mFragmentPrefix.match(l)
										if n is not None:
											dataMatrix.dataR["%s:%s" % (n.group(1), m.group(2))][i] = "0.0"

					# make a index
					length = 0
					for column in dataMatrix.dataR.keys():
						if len(dataMatrix.dataR[column]) > length:
							length = len(dataMatrix.dataR[column])

					dataMatrix.transpose()

					query.strOutput = dataMatrix.getQueryString()

					### end correct precursor intensities ###

				dataKeys = dataMatrix.getRowLabels()
				dataMatrix.convertToFloat()
				query.dataMatrix = dataMatrix.dataR

				### end Data Matrix ###
				#######################

				## convert data types to floating point numbers in the dataMatrix
				#for key in dataKeys:
				#	m = query.dataMatrix[key]
				#	for index in range(len(m)):
				#		if isinstance(m[index], TypeTmpResult):
				#			if m[index].getFloat():
				#				if m[index].getFloat() >= 0.0:
				#					m[index] = m[index].getFloat()
				#				else:
				#					m[index] = 0.0
				#			elif m[index] == "None":
				#				m[index] = 0.0
				#			elif m[index] == "-1":
				#				m[index] = 0.0
				#			elif not m[index]:
				#				m[index] = 0.0

				#		elif isinstance(m[index], type("")):
				#			m[index] = m[index]
				#
				#		elif isinstance(m[index], int):
				#			m[index] = float(m[index])
				#
				#		elif isinstance(m[index], float):
				#			m[index] = float(m[index])
				#
				#		else:
				#			m[index] = 0.0

				# transpose the dataMatrix to give more possibilities in statistics (with R e.g.)
				#dataMatrixTransp = []
				#for index in len(dataMatrix.values()[0]):
				#	dataMatrixTrans = []
				#	for key in dataMatrix.keys():
				#		dataMatrixTrans.append(
				## seperate MS species from MS/MS species
				## for this, the 'MASS' key is neccessary
				#dataMatrixMSMS = {}
				#for index in len(dataMatrix['MASS']):
				#	if dataMatrix['MASS'][index] in dataMatrixMSMS[]



	def pickleResult(self):
		pass

	def generateStatistics(self, options):

		#import matplotlib
		#matplotlib.use('Pdf')
		#import pylab as p
		import re

		# query: dataMatrix, name, listReport, mfqlObj, listReportOut, listVariables, sc, reportHeads, strOutput

		# this routine sums up the molecular species. I.e. for example:
		# PE [18:0/16:1] and PE [18:1/16:0] to PE [34:1]
		if options['sumFattyAcids'] == 'True':

			lipidName = 'NAME' # the column which contains the lipid name (in opposite to lipid species)
			fragmentColumn = 'FRAGINTENS' # the column containing the fragment intensities
			for query in self.dictQuery.values():

				if hasattr(query, "dataMatrix"):

					d = query.dataMatrix

					# collect all samples, i.e. all headers which are intensity headers
					intensitySamples = []
					r = re.compile('(%s*):.*' % fragmentColumn)
					for column in d.keys():
						m = r.match(column)
						if m:
							intensitySamples.append(column)

					index = 0
					while index < len(query.dataMatrix.values()[0]) - 1:

						if d[lipidName][index] == d[lipidName][index+1]:
							for sample in intensitySamples:
								d[sample][index] += d[sample][index+1]

							for everyKey in d.keys():
								del d[everyKey][index+1]

						else:
							index += 1

		#intensitySamples = ['INTENS', 'FAS']
		length = 0
		# calculate total ion count for every query by giving the name of the intensity list
		for query in self.dictQuery.values():

			if hasattr(query, "dataMatrix"):

				intensitySamples = []
				dataKeys = query.dataMatrix.keys()

				# attributes in which to store the statistical data
				query.statisticalData = {}

				dictTotalIonCount = odict()
				dictRelativeAbundance = odict()
				dictAverage = odict()
				dictStdev = odict()
				dictStdev2 = odict()
				allSampleKeys = []

				# collect all samples, i.e. all headers which are intensity headers
				r = re.compile('([A-z]*):.*')
				for key in dataKeys:
					m = r.match(key)
					if m:
						if not m.group(1) in intensitySamples:
							intensitySamples.append(m.group(1))

				for smplIntensity in intensitySamples:

					# define some useful variables
					sampleKeys = []
					for key in dataKeys:
						if re.match('.*(%s):.*' % smplIntensity, key):
							sampleKeys.append(key)
					allSampleKeys += sampleKeys

					# calculate the total ion count
					for sample in sampleKeys:
						dictTotalIonCount[sample] = 0.0
						data = sorted(query.dataMatrix[sample])

						for index in range(len(data)):
							try:
								if data[index] != data[index + 1]:
									if data[index] > 0.0:
										dictTotalIonCount[sample] += data[index]
							except IndexError:
								if data[index] > 0.0:
									try:
										dictTotalIonCount[sample] += data[index]

									except TypeError:
										raise TypeError

					# calculate relative abundances
					for sample in sampleKeys:
						dictRelativeAbundance[sample] = []
						data = query.dataMatrix[sample]

						for x in data:
							try:
								dictRelativeAbundance[sample].append(x / dictTotalIonCount[sample])
							except ZeroDivisionError:
								dictRelativeAbundance[sample].append(0.0)

					# calculate average
					dictAverage[smplIntensity] = []
					length = len(dictRelativeAbundance.values()[0])
					for index in range(length):
						sum = 0
						for sample in sampleKeys:
							sum += dictRelativeAbundance[sample][index]

						dictAverage[smplIntensity].append(sum / len(sampleKeys))

					# calculate standard deviation
					dictStdev[smplIntensity] = []
					length = len(dictRelativeAbundance.values()[0])
					for index in range(length):
						sum = []
						for sample in sampleKeys:
							sum.append(dictRelativeAbundance[sample][index])

						dictStdev[smplIntensity].append(np.std(np.array(sum)))

					# calculate standard deviation to confirm numpy's version
					#dictStdev2[smplIntensity] = []
					#length = len(dictRelativeAbundance.values()[0])
					#for index in range(length):
					#	sum = []
					#	for sample in sampleKeys:
					#		sum.append((dictRelativeAbundance[sample][index] - dictAverage[smplIntensity][index])**2)
					#	avg = (math.fsum(sum) / len(sampleKeys))

					#	dictStdev2[smplIntensity].append(math.sqrt(avg))


				query.statisticalData['relativeAbundance'] = deepcopy(dictRelativeAbundance)
				query.statisticalData['totalIonCount'] = deepcopy(dictTotalIonCount)
				query.statisticalData['average'] = deepcopy(dictAverage)
				query.statisticalData['stdev'] = deepcopy(dictStdev)
				#query.statisticalData['stdev2'] = deepcopy(dictStdev2)

				# put the resulting statistics at the end of the output
				str = ''
				for index in range(len(query.dataMatrix.values()[0])):
					for key in dataKeys:
						str += '%s,' % query.dataMatrix[key][index]
					#str += ','
					for key in allSampleKeys:
						str += '%.12f,' % query.statisticalData['relativeAbundance'][key][index]
					#str += ','

					# the average by smplIntensity
					for i in intensitySamples:
						str += '%.12f,' % (query.statisticalData['average'][i][index])
					# the standard deviation by smplIntensity
					for i in intensitySamples:
						str += '%.12f,' % (query.statisticalData['stdev'][i][index])
					str += '\n'

				str += '\n'
				for key in dataKeys:
					if query.statisticalData['totalIonCount'].has_key(key):
						str += '%.4f,' % query.statisticalData['totalIonCount'][key]
					else:
						str += ','

				str += '\n'

				query.strOutput = str

		heads = ['INDEX']
		# normal abundances
		#for key in dataKeys:
		#	heads.append(key)
			#str += '%s,' % key
		#str += ','
		# relative abundances
		for key in allSampleKeys:
			heads.append('REL_%s' % key)
			#str += 'REL:%s,' % key
		#str += ','
		for key in intensitySamples:
			heads.append('AVG_%s' % key)
		for key in intensitySamples:
			heads.append('STDEV_%s' % key)
			#str += 'AVG:%s,' % key

		self.listHead += heads


	def generateGraphics(self):

		import matplotlib
		#matplotlib.use('Pdf')
		from matplotlib.backends.backend_pdf import PdfPages
		import pylab as p

		# query: dataMatrix, name, listReport, mfqlObj, listReportOut, listVariables, sc, reportHeads, strOutput

		pdf = PdfPages('multipages_pdf.pdf')

		### routine for total ion count graph ###
		dictTotalIonCount = {}
		for query in self.dictQuery.values():

			# totalIonCount: {sample : total ion count} for lipid class query.name
			dictTotalIonCount[query.name] = query.statisticalData['totalIonCount']

		dataKeys = dictTotalIonCount.keys() # lipid classes
		dataLen = len(dictTotalIonCount.values()[0].values()) # number of samples
		data = dictTotalIonCount

		# add the figure to the pdf
		fig = p.figure()
		ax = fig.add_subplot(1,1,1)

		group_labels = []
		listAllIntensities = []
		keys = data[dataKeys[0]]
		for jkey in keys:
			group_labels.append(jkey) # sample names
			for ikey in dataKeys: # lipid class names
				listAllIntensities.append(float(data[ikey][jkey]))
				group_labels.append('')


		n = len(listAllIntensities)
		nbox = len(dataKeys)
		ind = range(n)

		listStandardColors = ['aqua', 'black', 'blue', 'fuchsia', 'gray', 'green', 'lime',
			'maroon', 'navy', 'olive', 'purple', 'red', 'silver', 'teal', 'white', 'yellow']
		listColor = []
		for j in range(dataLen):
			for i in range(len(dataKeys)):
				listColor.append(listStandardColors[i%15])

		assert len(listAllIntensities) == len(listColor)
		ax.bar(ind, listAllIntensities, color = listColor, align = 'center')
		ax.set_ylabel('Counts')
		ax.set_title('Eat this', fontstyle = 'italic')

		p.legend(dataKeys, loc='upper left')
		# This sets the ticks on the x axis to be exactly where we put
		# the center of the bars.
		ax.set_xticks(ind)

		ax.set_xticklabels(group_labels)

		# Extremely nice function to auto-rotate the x axis labels.
		# It was made for dates (hence the name) but it works
		# for any long x tick labels
		fig.autofmt_xdate()

		#p.show()
		#p.savefig('test.pdf')
		p.savefig(pdf, format = 'pdf')
		p.close()

		pdf.close()


		# first try: put out all found species with their abundance for all spectra
		if False:
			for query in self.dictQuery.values():

				if hasattr(query, "dataMatrix"):

					dataKeys = query.dataMatrix.keys()
					dataLen = len(query.dataMatrix.values()[0])

					fig = p.figure()
					ax = fig.add_subplot(1,1,1)

					listAllIntensities = []
					for i in range(dataLen):
						for j in dataKeys[5:]:
							listAllIntensities.append(float(query.dataMatrix[j][i]))

					n = len(listAllIntensities)
					nbox = len(dataKeys[5:])
					ind = range(n)

					#dataError = [float(x[:-3]) for x in query.dataMatrix['ERROR']]
					#err = []
					#for index in range(len(y)):
					#	err.append((y[index] / 1000000) * dataError[index])

					# generate the colorset
					# valid color names: aqua, black, blue, fuchsia, gray, green, lime, maroon, navy,
					# 	olive, purple, red, silver, teal, white, and yellow.

					listStandardColors = ['aqua', 'black', 'blue', 'fuchsia', 'gray', 'green', 'lime',
						'maroon', 'navy', 'olive', 'purple', 'red', 'silver', 'teal', 'white', 'yellow']
					listColor = []
					for j in range(dataLen):
						for i in range(nbox):
							listColor.append(listStandardColors[i%15])

					assert len(listAllIntensities) == len(listColor)
					ax.bar(ind, listAllIntensities, color = listColor, align = 'center')
					ax.set_ylabel('Counts')
					ax.set_title('Eat this', fontstyle = 'italic')

					# This sets the ticks on the x axis to be exactly where we put
					# the center of the bars.
					ax.set_xticks(ind)

					group_labels = query.dataMatrix[dataKeys[1]]

					ax.set_xticklabels(group_labels)

					# Extremely nice function to auto-rotate the x axis labels.
					# It was made for dates (hence the name) but it works
					# for any long x tick labels
					fig.autofmt_xdate()

					p.show()
					#p.savefig('test.pdf')


	def checkIsobaricSpeciesBeforeSUCHTHAT(self):
		return True

		listSCMS = []
		listSCMSMS = []
		for query in self.dictQuery:
			for i in self.dictQuery[query].listVariables:
				for j in i.keys():
					#if repr(i[j]).split(':')[-1] == "MS1+" or repr(i[j]).split(':')[-1] == "MS1-": # depricated
					if i[j].type == 0:
						listSCMS.append(i[j])
					#if repr(i[j]).split(':')[-1] == "MS2+" or repr(i[j]).split(':')[-1] == "MS2-": # depricated
					if i[j].type == 1:
						listSCMSMS.append(i[j])

		listSCMS.sort(cmp = lambda x,y: cmp(x.mass, y.mass))
		listSCMSMS.sort(cmp = lambda x,y: cmp(x.mass, y.mass))

		index = 0
		isospec = 0
		while index < len(listSCMS) - 1:
			lookahead = 1
			isospecFound = False
			while listSCMS[index].mass == listSCMS[index + lookahead].mass and\
				index + lookahead < len(listSCMS) - 1:
				listSCMS[index].isobaric = '%s' % listSCMS[index + lookahead].name
				listSCMS[index + lookahead].isobaric = '%s' % listSCMS[index].name
				lookahead += 1
				isospecFound = True

			if isospecFound:
				isospec += 1

			index += lookahead

		index = 0
		isospec = 0
		while index < len(listSCMSMS) - 1:
			lookahead = 1
			isospecFound = False
			while listSCMSMS[index].mass == listSCMSMS[index + lookahead].mass and\
				index + lookahead < len(listSCMSMS) - 1:
				listSCMSMS[index].isobaric = '%s' % listSCMSMS[index + lookahead].name
				listSCMSMS[index + lookahead].isobaric = '%s' % listSCMSMS[index].name
				lookahead += 1
				isospecFound = True

			if isospecFound:
				isospec += 1

			index += lookahead

	def checkIsobaricSpeciesAfterSUCHTHAT(self):

		listSCMS = []
		listSCMSMS = []
		for query in self.dictQuery:
			for i in self.dictQuery[query].listVariables:
				for j in i.keys():
					#if repr(i[j]).split(':')[-1] == "MS1+" or repr(i[j]).split(':')[-1] == "MS1-": # depricated
					if i[j].type == 0:
						listSCMS.append(i[j])
					#if repr(i[j]).split(':')[-1] == "MS2+" or repr(i[j]).split(':')[-1] == "MS2-": # depricated
					if i[j].type == 1:
						listSCMSMS.append(i[j])

		listSCMS.sort(cmp = lambda x,y: cmp(x.mass, y.mass))
		listSCMSMS.sort(cmp = lambda x,y: cmp(x.mass, y.mass))

		index = 0
		isospec = 0
		while index < len(listSCMS) - 1:
			lookahead = 1
			isospecFound = False
			while listSCMS[index].mass == listSCMS[index + lookahead].mass and\
				index + lookahead < len(listSCMS) - 1:
				#listSCMS[index].isobaric = '<%s>' % listSCMS[index].isobaric
				#listSCMS[index + lookahead].isobaric = '<%s>' % listSCMS[index + lookahead].isobaric
				if not listSCMS[index].name == listSCMS[index + lookahead].name:
					if not listSCMS[index + lookahead].name in listSCMS[index].isobaric:
						listSCMS[index].isobaric.append(listSCMS[index + lookahead].name)
						listSCMS[index + lookahead].isobaric.append(listSCMS[index].name)
					#else:
					#	for entry in listSCMS[index + lookahead].isobaric:
					#		if not entry in listSCMS[index].isobaric:
					#			listSCMS[index].isobaric.append(entry)


				lookahead += 1
				isospecFound = True

			if isospecFound:
				isospec += 1

			index += lookahead


		index = 0
		isospec = 0
		while index < len(listSCMSMS) - 1:
			lookahead = 1
			isospecFound = False
			while listSCMSMS[index].mass == listSCMSMS[index + lookahead].mass and\
				index + lookahead < len(listSCMSMS) - 1:
				#listSCMSMS[index].isobaric = '<%s>' % listSCMSMS[index].isobaric
				#listSCMSMS[index + lookahead].isobaric = '<%s>' % listSCMSMS[index + lookahead].isobaric
				if not listSCMSMS[index].name == listSCMSMS[index + lookahead].name:
					if listSCMSMS[index].isobaric == []:
						listSCMSMS[index].isobaric.append(listSCMSMS[index + lookahead].name)
					else:
						for entry in listSCMSMS[index + lookahead].isobaric:
							if not entry in listSCMSMS[index].isobaric:
								listSCMSMS[index].isobaric.append(entry)

				lookahead += 1
				isospecFound = True

			if isospecFound:
				isospec += 1

			index += lookahead

	def removePermutations(self):

		for query in self.dictQuery:

			# DEBUG explanation
			# before, the output list (self.dictQuery[query].listVariables) was always just populated with the first
			# element in this line:
			# listVar_noPermutations = [listVar[0]]
			# which was always the one with the lowest errppm, as self.dictQuery[query].listVariables before this
			# function is sorted by errppm ascending but not absolute errppm
			# Another approach would be to find the code, where self.dictQuery[query].listVariables is sorted
			# originally.

			# FIX
			listVar = []

			a = self.dictQuery[query].listVariables


			if self.dictQuery[query].listVariables:
				# note that the Precursor is identified by MS1+ scope and Fragment (from MSMS) is identified by MS2+

				# MS1 only
				if all(v.scope == "MS1+" for v in self.dictQuery[query].listVariables[0].values()):
					for i in self.dictQuery[query].listVariables:
						listVar.append(sorted(i.items(), key=lambda x: x[1].mass))

				# with MS2
				else:
					for i in sorted(self.dictQuery[query].listVariables, key=lambda d: abs(next(v for v in d.values() if v.scope == "MS1+").errppm)):
						listVar.append(sorted(i.items(), key=lambda x: x[1].mass))
				# /FIX

			# if there are no variables, we don't need to do anything
			if len(listVar) > 0:

				listVar_noPermutations = [listVar[0]]
				for i in listVar:

					# check every entry
					isIn = False
					for j in listVar_noPermutations:

						# compare two lists
						lists_are_same = True
						for index in range(len(i)):

							# DEBUG explanation: in here, all following entries are sorted out, because they have the same
							# chemical structure. The only one left, was the one with lowest errppm but not absolute
							# lowest errpm

							# DEBUG explanation: this always holds, hence lists_are_same is always True
							if i[index][1].chemsc != j[index][1].chemsc:
								lists_are_same = False
								break

						if lists_are_same:
							isIn = True
							break

					# DEBUG explanation: therefore, this is never met
					if not isIn:
						listVar_noPermutations.append(i)

				# FIX
				# sort by mass after permutations are removed
				listVar_noPermutations = sorted(listVar_noPermutations, key=lambda x: x[-1][1].mass)
				# /FIX

				self.dictQuery[query].listVariables = []

				# Append the sorted elements to self.dictQuery[query].listVariables
				self.dictQuery[query].listVariables = [dict(i) for i in listVar_noPermutations]

class TypeQuery:

	def __init__(self, mfqlObj = None, id = None, report = None, withSuchthat = False):

		# this is {'identifyer' : TypeQuery}
		self.name = id

		# storage for the resulting variables
		self.listVariables = []

		# this is set of the report formats
		self.listReport = report

		# this is list of the ouput hash of the reports
		self.listReportOut = []

		# the obligatory mfqlObj
		self.mfqlObj = mfqlObj

		# isTakenBySuchthat is used for the complement MasterScan.
		# it should actually be checked if it is still nesseccary
		if not withSuchthat:
			for se in self.mfqlObj.sc.listSurveyEntry:
				# for now MSMSentries don't have listVariable. Technically
				# I don't find a reason to give it to them, because
				# every interpretation of the MasterScan is based on the SurveyEntry
				if se.listVariables != []:
					se.isTakenBySuchthat = True

		# a list for the report storing the names of the columns
		self.reportHeads = []


class DataPoint:

	def __init__(self,
			indexKey,
			rowKey,
			data):
		self.indexKey = indexKey
		self.data = data
		self.rowKey = rowKey

	def __repr__(self):
		str = '\t, '
		if isinstance(self.data, type([])):
			for i in self.rowKey:
				str += '%s,' % i
			str += '\n'
			str += '%s, ' % self.indexKey
			for i in self.data:
				str += '%s,' % repr(i)

		else:
			str += '%s\n' % self.rowKey
			str += '%s' % repr(self.data)

		str += '\n'

		return str

class TypeDataMatrix:

	def __init__(self, primaryKey):
		self.dataR = odict() # the original data set as it comes from the output
		self.dataL = odict() # the transposed data set using the primaryKey
		self.primaryKey = ''
		self.dataRKeys = odict()

	def __repr__(self):
		'''Prints the whole data content to the file specified.'''

		str = ''
		for key in self.dataRKeys:
			str += '%s,' % key
		str += '\n'

		for primKey in self.dataL.keys():
			str += '%s,' % primKey
			for e in self.dataL[primKey]:
				if isinstance(e, TypeTmpResult):
					str += '%s,' % e.string
				elif isinstance(e, type('')):
					str += '%s,' % e
				else:
					str += '%f,' % e
			str += '\n'

		return str

	def getQueryString(self):
		'''Prints the whole data content to the file specified.'''

		str = ''
		for primKey in self.dataL.keys():
			#str += '%s,' % primKey
			for e in self.dataL[primKey]:
				if isinstance(e, TypeTmpResult):
					str += '%s,' % e.string
				elif isinstance(e, type('')):
					str += '%s,' % e
				else:
					str += '%f,' % e
			str += '\n'
		return str

	def initiate(self, primaryKey):
		self.primaryKey = primaryKey
		self.dataRKeys = self.dataR.keys()
		self.convertToFloat()
		#self.transpose()
		#self.sumFattyAcids('FAS', 'MASS')
		#self.genIonSum()
		#self.dump('C:\Users\The Duke\My_Projects\LipidXStatistics\ecoli-MS1-100000-MS2-30000\statistics-debug.csv')
		#self.getValues('SPECIE', 'FAS')

	def dump(self, file):
		'''Dumps the whole data content to the file specified.'''

		str = ''
		for key in self.dataRKeys:
			str += '%s,' % key
		str += '\n'

		for primKey in self.dataL.keys():
			str += '%s,' % primKey
			for e in self.dataL[primKey]:
				if isinstance(e, TypeTmpResult):
					str += '%s,' % e.string
				elif isinstance(e, type('')):
					str += '%s,' % e
				else:
					str += '%f,' % e
			str += '\n'

		with open(file, 'a') as f:
			f.write(str)

	def showGraphics(self):

		import matplotlib
		from matplotlib.backends.backend_pdf import PdfPages

		# init the pdf output
		pdf = PdfPages('multipages_pdf.pdf')

		dataKeys = dictTotalIonCount.keys() # lipid classes
		dataLen = len(dictTotalIonCount.values()[0].values()) # number of samples
		data = dictTotalIonCount

		fig = p.figure()
		ax = fig.add_subplot(1,1,1)

	def getRowLabels(self):
		return self.dataRKeys

	def getColumnLabels(self):
		return self.dataL.keys()

	def getValues(self, label, content):

		r = re.compile('(%s):.*' % intensityRow)

		dictOut = {}
		for indexKey in self.dataL.keys():
			indexLabel = dataRKeys.index(label)
			indexContent = dataRKeys.index(content)
			if not dictOut.has_key(self.dataL[indexKey][indexLabel]):
				dictOut[self.dataL[indexKey][indexLabel]] = self.dataL[indexKey][indexContent]

	def getIntensity(self, intensityRow, index = None):
		'''Returns a dictionary with the primary key and the
		rows filled with just the intensity values of interest.
		E.g.: retIntensity[pKey] = [2.1, 3.0, 2.4, 4.0]'''

		retIntensity = {}
		r = re.compile('(%s):.*' % intensityRow)

		if not index:
			for indexKey in self.dataL.keys():
				for key in self.dataRKeys:
					m = r.match(key)
					if m:
						if not indexKey in retIntensity:
							retIntensity[indexKey] = DataPoint(indexKey, [], [])
						index = self.dataRKeys.index(key)
						retIntensity[indexKey].data.append(self.dataL[indexKey][index])
						retIntensity[indexKey].rowKey.append(key)
		else:
			retIntensity = DataPoint(index, [], [])
			for key in self.dataRKeys:
				m = r.match(key)
				if m:
					indexRow = self.dataRKeys.index(key)
					retIntensity.data.append(self.dataL[index][indexRow])
					retIntensity.rowKey.append(key)

		return retIntensity

	def transpose(self):
		'''The function name describes the function well.'''

		for index in range(len(self.dataR[self.primaryKey])):
			indexKey = "%s" % self.dataR[self.primaryKey][index]
			if indexKey != '[]':
				if not indexKey in self.dataL.keys():
					self.dataL[indexKey] = []
				dummy = []
				for key in self.dataRKeys:
					self.dataL[indexKey].append(self.dataR[key][index])

	def sumFattyAcids(self, faRow, indicatorRow):
		'''This method sums all fatty acids belonging to one
		precursor and puts the result as rows at the end of the
		data matrix.'''

		if self.dataL == {}: return None

		# gen an index dictionary to map array index to dictionary keys
		dicIndex = dict(zip(self.dataL.keys(), range(len(self.dataL.keys()))))
		indexDic = dict((str(k), v) for k, v in zip(range(len(self.dataL.keys())), self.dataL.keys()))

		# get index of the indicator row
		indicatorIndex = self.dataRKeys.index(indicatorRow)
		index = 0

		# add new keys to the dataMatrix which point to the sum
		fa = self.getIntensity(faRow, self.dataL.keys()[0]) # take the fatty acid entries of the first column
		for key in fa.rowKey:
			self.dataRKeys.append("SUM_%s" % key) # generate the keys for the sum of the fatty acids

		while index < len(self.dataL.values()):
			n = 1
			fa1 = self.getIntensity(faRow, indexDic[str(index)]) # fa1 is from DataPoint type
			sum = fa1.data

			try:
				while self.dataL.values()[index + n][indicatorIndex] == self.dataL.values()[index][indicatorIndex]:
					fa2 = self.getIntensity(faRow, indexDic[str(index + n)])

					for i in range(len(fa1.data)):
						sum[i] = sum[i] + fa2.data[i]

					n += 1

			except IndexError:
				pass

			# append the sum list at the end of the entry
			for i in range(n):
				for e in sum:
					self.dataL.values()[index + i].append(e)

			index += n

	def genIonSum(self):

		#r = re.compile('(%s):.*' % intensityRow)
		retSum = dict([(x, 0.0) for x in self.dataRKeys])

		for primKey in self.dataL:
			for rowKey in retSum.keys():
				try:
					e = float(self.dataL[primKey][self.dataRKeys.index(rowKey)])
				except ValueError:
					e = 0.0
				except AttributeError:
					e = 0.0

				retSum[rowKey] += e

		self.dataL['IonSum'] = []
		for key in self.dataRKeys:
			self.dataL['IonSum'].append(retSum[key])

	def convertToFloat(self):

		matchFloat = re.compile("^[+-]?\d+\.?\d*$")

		# convert data types to floating point numbers in the dataMatrix
		for key in self.dataR.keys():
			m = self.dataR[key]
			for index in range(len(m)):
				if isinstance(m[index], TypeTmpResult):
					if m[index].type == TYPE_FLOAT:
						if m[index].getFloat() >= 0.0:
							m[index] = m[index].getFloat()
						else:
							m[index] = 0.0
					elif m[index].type == TYPE_NONE:
						m[index] = 0.0
					elif m[index].type == TYPE_CHEMSC:
						m[index] = repr(m[index].chemsc)
					elif m[index].type == TYPE_STRING:
						m[index] = m[index].string
					elif m[index].type == TYPE_BOOL:
						m[index] = 0.0

				elif m[index] == "-1":
					m[index] = 0.0

				elif not m[index]:
					m[index] = 0.0

				elif isinstance(m[index], type("")):
					if matchFloat.match(m[index]):
						m[index] = float(m[index])

				elif isinstance(m[index], int):
					m[index] = float(m[index])

				elif isinstance(m[index], float):
					pass

				else:
					m[index] = 0.0


