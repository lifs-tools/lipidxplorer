#from lpdxChemsf import *
from lx.exceptions import SyntaxErrorException
from lx.mfql.runtimeStatic import TypeExpression
#from lx.mfql.runtimeStatic import *
from lx.mfql.constants import *
from copy import copy


def func(float):
	return float**2

def isEven(float):
	if float % 2 == 0:
		return True
	else:
		return False

def isEvenNominal(float):
	f = int(float)
	if f % 2 == 0:
		return True
	else:
		return False

def isOddNominal(float):
	f = int(float)
	if f % 2 == 0:
		return True
	else:
		return False

def isOdd(float):
	if float % 2 == 1:
		return True
	else:
		return False

def sub(sc1, sc2):
	return (sc1 - sc2)

def sumIntensity(*input):

	result = ''
	return input

class InternFunctions:

	def __init__(self, vars, mfqlObj):
		self.listFuns = ['sumIntensity', 'column', 'avg', 'abs', 'score',
				'isStandard', 'nbsmpls', 'medianU', 'medianL']
		self.listPostFuns = ['isStandard']
		self.vars = vars
		self.mfqlObj = mfqlObj

	#def startFun(self, fun, args, vars):
	def startFun(self, fun, args, vars):

		currArguments = copy(args)

		### if it is a postFunction, redirect it to pospostFunction() ###

		if fun == 'isStandard' and len(currArguments) == 3:

			# collect arguments
			varName = self.mfqlObj.queryName + self.mfqlObj.namespaceConnector + currArguments[0].name
			globSample = currArguments[1].string
			scope = currArguments[2].string

			funName = 'isStandard'
			funArgs = [self.mfqlObj.queryName + self.mfqlObj.namespaceConnector + currArguments[0].name,
						currArguments[1].string,
						currArguments[2].string]

			# direct function call to post functions
			if self.mfqlObj.queryName not in self.mfqlObj.dictPostFuns:
				self.mfqlObj.dictPostFuns[self.mfqlObj.queryName] = {funName : funArgs}

			return True

		if fun == 'isStandard' and len(currArguments) == 2:

			# collect arguments
			varName = self.mfqlObj.queryName + self.mfqlObj.namespaceConnector + currArguments[0].name
			scope = currArguments[1].string

			funName = 'isStandard'
			funArgs = [self.mfqlObj.queryName + self.mfqlObj.namespaceConnector + currArguments[0].name,
						currArguments[1].string]

			# direct function call to post functions
			if self.mfqlObj.queryName not in self.mfqlObj.dictPostFuns:
				self.mfqlObj.dictPostFuns[self.mfqlObj.queryName] = {funName : funArgs}

			return True

		### evaluate Arguments ###

		boolEvaluated = False

		while not boolEvaluated:
			boolEvaluated = True
			for index in range(len(currArguments)):
				if isinstance(currArguments[index], TypeExpression):
					currArguments[index] = currArguments[index].evaluate(mode = None, scane = None, vars = self.mfqlObj.currVars,
							queryName = self.mfqlObj.queryName, sc = self.mfqlObj.sc)
				elif isinstance(currArguments[index], TypeFloat):
					leftSide = TypeTmpResult(
									options = None,
									type = TYPE_FLOAT,
									float = currArguments[index].float,
									dictIntensity = None,
									chemsc = None)
				elif isinstance(currArguments[index], TypeTmpResult):
					pass
				elif isinstance(currArguments[index], TypeVariable):
					boolEvaluated = False
					currArguments[index] = TypeExpression(
						isSingleton = True,
						leftSide = currArguments[index],
						rightSide = None,
						operator = None,
						environment = self.mfqlObj.queryName,
						mfqlObj = self.mfqlObj).evaluate(mode = None, scane = None, vars = self.mfqlObj.currVars,
							queryName = self.mfqlObj.queryName, sc = None)#self.mfqlObj.sc)
				elif isinstance(currArguments[index], TypeFunction):
					boolEvaluated = False
					currArguments[index] = currArguments[index].evaluate(scane, self.mfqlObj.currVars, self.environment, queryName)
				elif isinstance(currArguments[index], type(0.0)):
					boolEvaluated = False
					currArguments[index] = TypeTmpResult(
									options = None,
									type = TYPE_FLOAT,
									float = currArguments[index],
									dictIntensity = None,
									chemsc = None)
		if currArguments[0]:

			### process functions ###

			if fun == 'nbsmpls':

				# generate the result as TypeTmpResult
				result = TypeTmpResult(
								options = None,
								type = TYPE_FLOAT,
								chemsc = None,
								float = len(self.mfqlObj.sc.listSamples),
								string = None,
								dictIntensity = None)

			if fun == 'score':

				if self.mfqlObj.sc.options['MSMSaccuracy'].ppm:

					# collect the intensities, get rid of double entries
					# first argument is the intensity dictionary
					sum = 0
					for arg in currArguments:
						if arg:
							sum += abs(arg.errppm)
						else:
							sum += 0
					avg = sum / len(currArguments)

					score = "%.2f" % (1 - (avg / self.mfqlObj.sc.options['MSMSaccuracy'].ppm))

				elif self.mfqlObj.sc.options['MSMSaccuracy'].da:

					# collect the intensities, get rid of double entries
					# first argument is the intensity dictionary
					sum = 0
					for arg in currArguments:
						if arg:
							sum += abs(arg.errda)
						else:
							sum += 0
					avg = sum / len(currArguments)

					score = "%.2f" % (1 - (avg / self.mfqlObj.sc.options['MSMSaccuracy'].da))

				# generate the result as TypeTmpResult
				result = TypeTmpResult(
								options = None,
								type = TYPE_STRING,
								chemsc = None,
								float = None,
								string = score,
								dictIntensity = None)

			if fun == 'avg':

				if len(currArguments) == 1:

					if currArguments[0].dictIntensity:

						# collect the intensities, get rid of double entries
						# first argument is the intensity dictionary
						sum = 0
						for key in list(currArguments[0].dictIntensity.keys()):
							if currArguments[0].dictIntensity[key] != '-1':
								sum += currArguments[0].dictIntensity[key]
							else:
								sum += 0
						avg = sum / len(list(currArguments[0].dictIntensity.keys()))

						# generate the result as TypeTmpResult
						result = TypeTmpResult(
										options = None,
										type = TYPE_FLOAT,
										chemsc = None,
										float = avg,
										dictIntensity = None)

				else:

					# collect the intensities, get rid of double entries
					# first argument is the intensity dictionary
					sum = 0
					for arg in currArguments:
						if arg:
							sum += arg.float
						else:
							sum += 0
					avg = sum / len(currArguments)

					# generate the result as TypeTmpResult
					result = TypeTmpResult(
									options = None,
									type = TYPE_FLOAT,
									chemsc = None,
									float = avg,
									dictIntensity = None)

			if fun == 'medianU': # median - take lower median if list is even

				if len(currArguments) == 1:

					if currArguments[0].dictIntensity:

						d = sorted(currArguments[0].dictIntensity.values())
						dl = len(d)

						if dl % 2 == 1:
							median = d[(dl + 1) / 2 - 1]
						else:
							median = d[dl / 2] # take upper median

						# generate the result as TypeTmpResult
						result = TypeTmpResult(
										options = None,
										type = TYPE_FLOAT,
										chemsc = None,
										float = median,
										dictIntensity = None)

				else:

					# collect the intensities, get rid of double entries
					# first argument is the intensity dictionary

					d = sorted(currArguments)
					dl = len(d)

					if dl % 2 == 1:
						median = d[(dl + 1) / 2 - 1]
					else:
						median = d[dl / 2] # take upper median

					# generate the result as TypeTmpResult
					result = TypeTmpResult(
									options = None,
									type = TYPE_FLOAT,
									chemsc = None,
									float = median,
									dictIntensity = None)

			if fun == 'medianL': # median - take lower median if list is even

				if len(currArguments) == 1:

					if currArguments[0].dictIntensity:

						d = sorted(currArguments[0].dictIntensity.values())
						dl = len(d)

						if dl % 2 == 1:
							median = d[(dl + 1) / 2 - 1]
						else:
							median = d[dl / 2 - 1] # take lower median

						# generate the result as TypeTmpResult
						result = TypeTmpResult(
										options = None,
										type = TYPE_FLOAT,
										chemsc = None,
										float = median,
										dictIntensity = None)

				else:

					# collect the intensities, get rid of double entries
					# first argument is the intensity dictionary

					d = sorted(currArguments)
					dl = len(d)

					if dl % 2 == 1:
						median = d[(dl + 1) / 2 - 1]
					else:
						median = d[dl / 2 - 1] # take lower median

					# generate the result as TypeTmpResult
					result = TypeTmpResult(
									options = None,
									type = TYPE_FLOAT,
									chemsc = None,
									float = median,
									dictIntensity = None)

			if fun == 'abs':

				if len(currArguments) == 1:

					if currArguments[0].dictIntensity:

						# collect the intensities, get rid of double entries
						# first argument is the intensity dictionary
						sum = 0
						for key in list(currArguments[0].dictIntensity.keys()):
							if currArguments[0].dictIntensity[key] != '-1':
								currArguments[0].dictIntensity[key] = abs(currArguments[0].dictIntensity[key])

						# generate the result as TypeTmpResult
						result = TypeTmpResult(
										options = None,
										type = TYPE_DICT_INTENS,
										chemsc = None,
										float = None,
										dictIntensity = currArguments[0].dictIntensity)

					else:

						if currArguments[0].float < 0.0:
							absolute = 0 - currArguments[0].float
						else:
							absolute = currArguments[0].float

						# generate the result as TypeTmpResult
						result = TypeTmpResult(
										options = None,
										type = TYPE_FLOAT,
										chemsc = None,
										float = absolute,
										dictIntensity = None)
				else:
					raise AttributeError("Only one attribute allowed for the function abs()")


			if fun == 'sumIntensity':

				### sum the given intensities iff the peaks are different ###

				#try:
				#	# get vars from the functions attributes
				#	v = []
				#	for i in currArguments:
				#		v.append(i)
				#		varName = self.mfqlObj.queryName + self.mfqlObj.namespaceConnector + i.name
				#		#if vars.has_key(varName):
				#		#	v.append(vars[varName])
				#except AttributeError as detail:
				#	raise SyntaxErrorException("ERROR: Function sumIntensity() in %s got wrong"  % self.mfqlObj.queryName +\
				#		" type of arguments. It should be just the variable names. %s" % detail,
				#		"",
				#		self.mfqlObj.queryName,
				#		0)

				#	return -1

				v = []
				for i in currArguments:
					if i.isType(TYPE_DICT_INTENS):
						v.append(i)
					else:
						raise SyntaxErrorException("ERROR: Function sumIntensity() in %s got wrong"  % self.mfqlObj.queryName +\
						" type of arguments. It should be '.intensity'.",
						"",
						self.mfqlObj.queryName,
						0)

				# collect the intensities, get rid of double entries
				toSum = [v[0]]
				samples = list(v[0].dictIntensity.keys())
				for i in v[1:]:
					isIn = False
					for j in toSum:
						#if i.mass == j.mass:
						for sample in samples:
							if i.dictIntensity[sample] != j.dictIntensity[sample]:
								isIn = True

					if isIn:
						toSum.append(i)

				# sum the intensities
				dictIntensityResult = {}
				for i in toSum:
					isotopeMode = True
					for k in samples:
						if k in dictIntensityResult:

							if i.dictIntensity[k] >= 0.0:
								isotopeMode = False

							if isotopeMode:
								dictIntensityResult[k] += i.dictIntensity[k]
							else:
								if i.dictIntensity[k] <= 0.0:
									pass
								else:
									dictIntensityResult[k] += i.dictIntensity[k]

						else:
							dictIntensityResult[k] = i.dictIntensity[k]


				# generate the result as TypeTmpResult
				result = TypeTmpResult(
								options = None,
								type = TYPE_DICT_INTENS,
								chemsc = None,
								float = None,
								dictIntensity = dictIntensityResult)

			if fun == 'column':

				### return the intensities of the samples specified with a regular expression ###

				import re

				varName = self.mfqlObj.queryName + self.mfqlObj.namespaceConnector + currArguments[0].name

				# get vars from the functions attributes
				v = None
				if varName in vars:
					v = vars[varName]

				dictIntensityResult = {}
				if v:
					for i in list(v.intensity.keys()):
						if re.match(currArguments[1].string, i):
							dictIntensityResult[i] = v.intensity[i]

				# generate the result as TypeTmpResult
				result = TypeTmpResult(
								options = None,
								type = TYPE_DICT_INTENS,
								chemsc = None,
								float = None,
								dictIntensity = dictIntensityResult)
				result.flag_dI_regExp = True

			return result

		else:
			return None

	def __getitem__(self, num):
		return self.listFuns[num]

