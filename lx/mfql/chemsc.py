## chemical elements parser ###
# published Tue, 30 Mar 1999 01:50:10 by Tim Peters #

### TODO ###
#	. adding chemsf together
###	  ###

import sys
import os

from copy import deepcopy, copy
from lx.mfql.runtimeStatic import TypeTolerance

import lx.mfql.calcsf_cached as calcsf
from functools import total_ordering

sys.path.append(".." + os.sep + "lib" + os.sep)



#define C 12.0
#define H 1.0078250321
#define N 14.0030740052
#define P 30.97376151
#define O 15.9949146221
#define S 31.97207069
#define NA 22.98976967
#define D 2.0141017780
#define CI 13.0033548378
#define LI 7.016003
#define NI 15.0001088984

# symbol, name, atomic number, molecular weight
_data = r"""'C', 'Carbon', 12.0
'H', 'Hydrogen', 1.0078250321
'N', 'Nitrogen', 14.0030740052
'P', 'Phosphorous', 30.97376151
'O', 'Oxygen', 15.9949146221
'Na', 'Sodium', 22.98976967
'S', 'Sulfur', 31.97207069
'I', 'Iodine', 126.904477
'D', 'Deuterium', 2.0141017780
'Ci', '13C', 13.0033548378
'Cl', 'Chloride', 34.968852
'Li', 'Lithium7', 7.016003
'Ni', '15N', 15.0001088984
'F', 'Fluorine', 18.9984032
'K', 'Potassium', 38.963708
'Cs', 'Cesium', 132.905433
'Br', 'Bromine', 78.918336
'Ag', 'Silver', 106.905095
'Al', 'Aluminium', 26.981541
'W', 'Tungsten', 183.950952
'Ti', 'Titanium', 47.947947"""

#class Element:
#	def __init__(self, symbol, name, molweight, count = 0):
#		"""An element. If count == 0 then range == []"""
#		self.sym = symbol
#		self.name = name
#		self.mw = molweight
#		if count != 0:
#			self._range = [count]
#		else:
#			self._range = []

#	def set_count(self, n):
#		self._range = [n]

#	def set_range(self, l, r, s = 1):
#		self._range = range(l,r,s)

#	def set_enum(self, enum):
#		self._range = sorted(enum)

#	def getweight(self):
#		return self.mw * self._range[0]

#	def addsyms(self, weight, result):
#		result[self.sym] = result.get(self.sym, 0) + weight

class Element:

	def __init__(self, symbol, name, molweight):
		self.sym = symbol
		self.name = name
		self.mw = molweight
		self._count = 1 # initialization
		self._constElement = False
		self._enumElement = False
		self._rangeElement = False

	def set_count(self, n):
		raise Exception("To be implemented...")
		pass

	def set_range(self, l, r, s = 1):
		raise Exception("To be implemented...")
		pass

	def set_enum(self, enum):
		raise Exception("To be implemented...")
		pass

	def get_count(self, n):
		raise Exception("To be implemented...")
		pass

	def get_sym(self, n):
		raise Exception("To be implemented...")
		pass

	def get_range(self, l, r, s = 1):
		raise Exception("To be implemented...")
		pass

	def get_enum(self, enum):
		raise Exception("To be implemented...")
		pass

	def get_weight(self):
		raise Exception("To be implemented...")
		pass

	def addsyms(self, weight, result):
		raise Exception("To be implemented...")
		pass

def build_dict(s):
	answer = {}
	for line in s.split("\n"):
		symbol, name, weight = eval(line)
		answer[symbol] = Element(symbol, name, weight)
	return answer

sym2elt = build_dict(_data)





class ConstElement(Element):

	def __init__(self, symbol, name, molweight, count = 0):

		Element.__init__(self, symbol, name, molweight)

		self._count = count

	def set_count(self, n):
		self._count = n

	def set_range(self, l, r, s = 1):
		raise TypeError("Setting a range for ConstElement is not possible")

	def set_enum(self, enum):
		raise TypeError("Setting a enumeration for ConstElement is not possible")

	def get_count(self):
		return self._count

	def get_range(self):
		raise TypeError("Getting a range for ConstElement is not possible")

	def get_enum(self):
		raise TypeError("Getting a enum for ConstElement is not possible")

	def get_weight(self):
		return self.mw * self._count

	def addsyms(self, weight, result):
		result[self.sym] = result.get(self.sym, 0) + weight

def build_dict_const(s):
	answer = {}
	for line in s.split("\n"):
		symbol, name, weight = eval(line)
		answer[symbol] = ConstElement(symbol, name, weight)
	return answer

sym2elt_const = build_dict_const(_data)
del _data












class RangeElement(Element):
	def __init__(self, symbol, name, molweight, count = 0):
		"""An element. If count == 0 then range == []"""

		Element.__init__(self,symbol, name, molweight)

		if count != 0:
			self._range = [count]
		else:
			self._range = []

	def set_count(self, n):
		self._range = [n]
		self._constElement = True

	def set_range(self, l, r, s = 1):
		self._range = list(range(l,r,s))
		self._rangeElement = True

	def set_enum(self, enum):
		self._range = sorted(enum)
		self._enumElement = True

	def get_count(self):
		raise TypeError("Getting a count for ConstElement is not possible")

	def get_range(self):
		return self._range

	def get_enum(self):
		return self._enum

	def get_weight(self):
		return self.mw * self._range[0]

	def addsyms(self, weight, result):
		result[self.sym] = result.get(self.sym, 0) + weight

	def isEnum(self):
		return self._enumElement

	def isRange(self):
		return self._rangeElement

	def isConst(self):
		return self._constElement

def diff(n1, n2):
	if n1 - n2 >= 0:
		return (n1 - n2)
	else:
		return 0



###### Ballal edited it 

@total_ordering
class ElementSequence:
	def __init__(self):
		self.charge = 0
		self.polarity = 0
		self._seq = {}  # symbol -> ConstElement
		self._db = None
		self._weight = None
		self.scriptTag = []

	def append(self, t):
		self._seq[t.sym] = t

	def checkElements(self):
		for i in self._seq.values():
			if not isinstance(i, ConstElement):
				raise TypeError("ElementSequence only allows ConstElement")

	def get_seq(self):
		return self._seq

	def get_element(self, e):
		return self._seq.get(e)

	def keys(self):
		return list(self._seq.keys())

	def values(self):
		return list(self._seq.values())

	def __len__(self):
		return len(self._seq)

	def __repr__(self):
		return " ".join(f"{e.sym}{e._count}" for e in self._seq.values())

	def __eq__(self, other):
		if not isinstance(other, ElementSequence):
			return NotImplemented
		return all(
			self._seq.get(sym, ConstElement(sym, "", 0, 0))._count ==
			other._seq.get(sym, ConstElement(sym, "", 0, 0))._count
			for sym in set(self._seq) | set(other._seq)
		)

	def __lt__(self, other):
		if not isinstance(other, ElementSequence):
			return NotImplemented
		# Sort elements by symbol for consistent comparison
		self_items = sorted((k, v._count) for k, v in self._seq.items())
		other_items = sorted((k, v._count) for k, v in other._seq.items())
		return self_items < other_items

	def __hash__(self):
		return hash(tuple(sorted((k, v._count) for k, v in self._seq.items())))

	def sorted(self):
		return sorted(self._seq.values(), key=lambda x: x.sym)

	def __delitem__(self, key):
		del self._seq[key]

	def __getitem__(self, key):
		if key == 'db':
			return self.get_DB()
		return self._seq.get(key)._count if key in self._seq else 0

	def __setitem__(self, key, value):
		if key in self._seq:
			self._seq[key]._count = value
		else:
			raise KeyError(f"Element '{key}' not found in sequence")

	def __add__(self, other):
		result = deepcopy(self)
		for key in set(result._seq) | set(other._seq):
			if key in result._seq and key in other._seq:
				result._seq[key]._count += other._seq[key]._count
			elif key in other._seq:
				result._seq[key] = deepcopy(other._seq[key])
		result._weight = None
		result._db = None
		return result

	def __sub__(self, other):
		result = deepcopy(self)
		for key in other._seq:
			if key in result._seq:
				result._seq[key]._count -= other._seq[key]._count
				if result._seq[key]._count <= 0:
					del result._seq[key]
		result._weight = None
		result._db = None
		return result

	def __mul__(self, factor):
		result = deepcopy(self)
		for k in result._seq:
			result._seq[k]._count *= factor
		result._weight = None
		result._db = None
		return result

	def get_DB(self):
		if self._db is not None:
			return self._db
		cRDB = 2
		cRDB += (self['C'] * 2) + (self['H'] * -1) + (self['Cl'] * -1) + \
				self['N'] + (self['Na'] * -1) + self['P'] - \
				self['D'] + (self['Ci'] * 2) + self['Ni'] - self['F'] + \
				(self['I'] * 5) - self['K'] - self['Cs'] - \
				self['Br'] + (self['Li'] * -1)
		self._db = cRDB / 2.0
		return self._db

	def getWeight(self, truemz=False):
		if self._weight is not None:
			return self._weight
		total = sum(e.get_weight() for e in self._seq.values())
		if self.charge != 0:
			total += self.charge * -0.00055
			if not truemz:
				total /= abs(self.charge)
		self._weight = total
		return self._weight

	def set_charge(self, c):
		self.charge = c
		self.polarity = (1 if c > 0 else -1 if c < 0 else 0)
 
##################################
 


class SCConstraint(ElementSequence):

	def __init__(self):

		ElementSequence.__init__(self)

		self.lwBoundDbEq = 0
		self.upBoundDbEq = 0

	def append(self, t):
		self._seq[t.sym] = t

	def checkElements(self):
		for i in list(self._seq.values()):
			if i.__class__ != RangeElement:
				raise TypeError("SCConstraint only allows RangeElement")

	def getMassRange(self):

		minMass = 0
		maxMass = 0
		for i in list(self._seq.keys()):
			minMass += self._seq[i]._range[0] * self._seq[i].mw
			maxMass += self._seq[i]._range[-1] * self._seq[i].mw

		if minMass == maxMass:
			minMass -= 1
			maxMass += 1
		#print(".........getMassRange...........",minMass / abs(self.charge), maxMass / abs(self.charge))
		return (minMass / abs(self.charge), maxMass / abs(self.charge))

	def __getitem__(self, elem):
		"""in: Symbol of an element

		out: the Element Object or None if it is not in the sequence"""

		if elem == 'db':
			raise TypeError("Cannot retrieve the double bonds from a SC constraint")
		else:
			try:
				return self._seq[elem]._range
			except KeyError:
				return [0]

		return 0

	def __repr__(self):
		""" Return sum form in a good readable string """
		l = ""
		for i in list(self._seq.values()):

			if i.isEnum():
				l = l + i.sym + "["
				for j in i._range:
					l += "%d," % j
				l = l[:-1]
				l += "] "
			elif i.isConst():
				l = l + i.sym + "[" + repr(i._range[0]) + "] "
			else:
				l = l + i.sym + "[" + repr(i._range[0]) + ".." + repr(i._range[-1]) + "] "

		return l

	def get_norangeElemSeq(self):
		"""returns a list of all possible ElemSeq which fitting the
		constrains of the ranges."""

		l = []

		if self[H]:
			rangeH = self[H]._range
		else:
			rangeH = [0]
		if self[N]:
			rangeN = self[N]._range
		else:
			rangeN = [0]
		if self[C]:
			rangeC = self[C]._range
		else:
			rangeC = [0]
		if self[P]:
			rangeP = self[P]._range
		else:
			rangeP = [0]
		if self[O]:
			rangeO = self[O]._range
		else:
			rangeO = [0]
		if self[S]:
			rangeS = self[S]._range
		else:
			rangeS = [0]
		if self[Na]:
			rangeNa = self[Na]._range
		else:
			rangeNa = [0]
		if self[D]:
			rangeD = self[D]._range
		else:
			rangeD = [0]
		if self[Ci]:
			rangeCi = self[Ci]._range
		else:
			rangeCi = [0]
		if self[Cl]:
			rangeCl = self[Cl]._range
		else:
			rangeCl = [0]
		if self[Li]:
			rangeLi = self[Li]._range
		else:
			rangeLi = [0]
		if self[Ni]:
			rangeNi = self[Ni]._range
		else:
			rangeNi = [0]

		for iD in rangeD:
			elemD = (sym2elt_const['D'])
			elemD.set_count(iD)
			for iCl in rangeCl:
				elemCl = (sym2elt_const['Cl'])
				elemCl.set_count(iCl)
				for iLi in rangeLi:
					elemLi = (sym2elt_const['Li'])
					elemLi.set_count(iLi)
					for iCi in rangeCi:
						elemCi = (sym2elt_const['Ci'])
						elemCi.set_count(iCi)
						for iNi in rangeNi:
							elemNi = (sym2elt_const['Ni'])
							elemNi.set_count(iNi)
							for iNa in rangeNa:
								elemNa = (sym2elt_const['Na'])
								elemNa.set_count(iNa)
								for iS in rangeS:
									elemS = (sym2elt_const['S'])
									elemS.set_count(iS)
									for iN in rangeN:
										elemN = (sym2elt_const['N'])
										elemN.set_count(iN)
										for iP in rangeP:
											elemP = (sym2elt_const['P'])
											elemP.set_count(iP)
											for iO in rangeO:
												elemO = (sym2elt_const['O'])
												elemO.set_count(iO)
												for iC in rangeC:
													elemC = (sym2elt_const['C'])
													elemC.set_count(iC)
													for iH in rangeH:
														elemH = (sym2elt_const['H'])
														elemH.set_count(iH)

														#cRDB = 2.0;
														#cRDB += ((float)((jC * 2) + (jH * -1) + jN + (jNa * -1) + (jP))) / 2.0;
														#(C - (H/2) + 1 + N/2)
														#print 2*iC + 2 + iN - 2 * self.lwBoundDbEq, 2*iC + 2 + iN - 2 * self.upBoundDbEq

														cRDB = 2.0
														cRDB += ((iC * 2) + (iH * -1) + iN + (iCl * -1) + (iNa * -1) + (iP) - (iD) + (iCi * 2) + (iNi)) / 2.0 + (iLi * -1)

														# old version
														#cRDB = iC - (iH + iNa)/2 + 1 + iN/2
														if self.lwBoundDbEq <= cRDB and cRDB <= self.upBoundDbEq:
															mass = sym2elt['C'].mw * iC + \
																	sym2elt['H'].mw * iH + \
																	sym2elt['O'].mw * iO + \
																	sym2elt['P'].mw * iP + \
																	sym2elt['N'].mw * iN + \
																	sym2elt['S'].mw * iS + \
																	sym2elt['Na'].mw * iNa + \
																	sym2elt['D'].mw * iD + \
																	sym2elt['Ci'].mw * iCi + \
																	sym2elt['Cl'].mw * iCl + \
																	sym2elt['Li'].mw * iLi + \
																	sym2elt['Ni'].mw * iNi + \
																	sym2elt['F'].mw * iF
															#if (((iN != 0) and (int(mass) % 2) == ((abs(self.charge) % 2) + (iN % 2)) % 2) or (iN == 0)):
															if ((int(mass) % 2) == ((abs(self.charge) % 2) + (iN % 2)) % 2):

																elemseq = ElementSequence()
																elemseq.append(elemC)
																elemseq.append(elemH)
																elemseq.append(elemP)
																elemseq.append(elemN)
																elemseq.append(elemO)
																elemseq.append(elemS)
																elemseq.append(elemNa)
																elemseq.append(elemD)
																elemseq.append(elemCi)
																elemseq.append(elemCl)
																elemseq.append(elemLi)
																elemseq.append(elemNi)
																elemseq.append(elemF)

																elemseq.set_charge(self.charge)
																elemseq.set_db(self.lwBoundDbEq, self.upBoundDbEq)

																l.append(deepcopy(elemseq))


		return l

	def set_db(self, lwBound, upBound):
		self.lwBoundDbEq = lwBound
		self.upBoundDbEq = upBound

	def covers(self, elemseq):
		"""See if the self sc constraint covers the given elemseq"""
		import types

		if type(elemseq) == list:
			flagelem = False
			for k in elemseq:
				if self.covers(k):
					flagelem = True
			return flagelem
		else:
			if elemseq.__class__ != ElementSequence:
				raise TypeError("covers() needs an ElementSequence as parameter")

			for elem in list(elemseq.keys()):
				if elem in self._seq and elemseq[elem] in self._seq[elem]._range:
					pass
				else:
					return False

		return True

	def solveWithCalcSF(self, m, tolerance):
		""" Check for Lipid class. Arguments and output is the same as for
		solveEQ()
		IN: mass by float,
		tolerance as resolution"""

#		if abs(self.charge) > 1:
#			print "solveWithCalcSF() works only for charges -1 and 1!"
#			exit(0)

		res = []

		# symbol list of the sequence
		l = []
		for i in list(self._seq.values()):
			l.append(i.sym)

		if isinstance(tolerance, TypeTolerance):
			if not tolerance.tolerance:
				t = tolerance.da
			else:
				t = m / tolerance.tolerance
		else:
			t = m / tolerance
		#print "Tolarance in solveWithCalcSF()...........: ", t
		elemC = self.get_element('C')
		elemH = self.get_element('H')
		elemO = self.get_element('O')
		elemN = self.get_element('N')
		elemP = self.get_element('P')
		elemS = self.get_element('S')
		elemI = self.get_element('I')
		elemNa = self.get_element('Na')
		elemD = self.get_element('D')
		elemCi = self.get_element('Ci')
		elemCl = self.get_element('Cl')
		elemLi = self.get_element('Li')
		elemNi = self.get_element('Ni')
		elemF = self.get_element('F')
		elemK = self.get_element('K')
		elemCs = self.get_element('Cs')
		elemBr = self.get_element('Br')
		elemAg = self.get_element('Ag')
		elemAl = self.get_element('Al')
		elemW = self.get_element('W')
		elemTi = self.get_element('Ti')

		if elemC:
			lwBndC = elemC._range[0]
			upBndC = elemC._range[-1]
		else:
			lwBndC = 0
			upBndC = 0

		if elemH:
			lwBndH = elemH._range[0]
			upBndH = elemH._range[-1]
		else:
			lwBndH = 0
			upBndH = 0

		if elemO:
			lwBndO = elemO._range[0]
			upBndO = elemO._range[-1]
		else:
			lwBndO = 0
			upBndO = 0

		if elemN:
			lwBndN = elemN._range[0]
			upBndN = elemN._range[-1]
		else:
			lwBndN = 0
			upBndN = 0

		if elemP:
			lwBndP = elemP._range[0]
			upBndP = elemP._range[-1]
		else:
			lwBndP = 0
			upBndP = 0

		if elemS:
			lwBndS = elemS._range[0]
			upBndS = elemS._range[-1]
		else:
			lwBndS = 0
			upBndS = 0

		if elemNa:
			lwBndNa = elemNa._range[0]
			upBndNa = elemNa._range[-1]
		else:
			lwBndNa = 0
			upBndNa = 0

		if elemD:
			lwBndD = elemD._range[0]
			upBndD = elemD._range[-1]
		else:
			lwBndD = 0
			upBndD = 0

		if elemCi:
			lwBndCi = elemCi._range[0]
			upBndCi = elemCi._range[-1]
		else:
			lwBndCi = 0
			upBndCi = 0

		if elemCl:
			lwBndCl = elemCl._range[0]
			upBndCl = elemCl._range[-1]
		else:
			lwBndCl = 0
			upBndCl = 0

		if elemLi:
			lwBndLi = elemLi._range[0]
			upBndLi = elemLi._range[-1]
		else:
			lwBndLi = 0
			upBndLi = 0

		if elemNi:
			lwBndNi = elemNi._range[0]
			upBndNi = elemNi._range[-1]
		else:
			lwBndNi = 0
			upBndNi = 0

		if elemF:
			lwBndF = elemF._range[0]
			upBndF = elemF._range[-1]
		else:
			lwBndF = 0
			upBndF = 0

		if elemI:
			lwBndI = elemI._range[0]
			upBndI = elemI._range[-1]
		else:
			lwBndI = 0
			upBndI = 0

		if elemK:
			lwBndK = elemK._range[0]
			upBndK = elemK._range[-1]
		else:
			lwBndK = 0
			upBndK = 0

		if elemCs:
			lwBndCs = elemCs._range[0]
			upBndCs = elemCs._range[-1]
		else:
			lwBndCs = 0
			upBndCs = 0

		if elemBr:
			lwBndBr = elemBr._range[0]
			upBndBr = elemBr._range[-1]
		else:
			lwBndBr = 0
			upBndBr = 0

		if elemAg:
			lwBndAg = elemAg._range[0]
			upBndAg = elemAg._range[-1]
		else:
			lwBndAg = 0
			upBndAg = 0

		if elemAl:
			lwBndAl = elemAl._range[0]
			upBndAl = elemAl._range[-1]
		else:
			lwBndAl = 0
			upBndAl = 0

		if elemW:
			lwBndW = elemW._range[0]
			upBndW = elemW._range[-1]
		else:
			lwBndW = 0
			upBndW = 0

		if elemTi:
			lwBndTi = elemTi._range[0]
			upBndTi = elemTi._range[-1]
		else:
			lwBndTi = 0
			upBndTi = 0

		#print ">>>"
		#print "C", lwBndC, upBndC, "H", lwBndH, upBndH, "O", lwBndO, upBndO, "N", lwBndN, upBndN, "P", lwBndP, upBndP,
		#print "S", lwBndS, upBndS, "Na", lwBndNa, upBndNa, "Cl", lwBndCl, upBndCl
		#print m, t, self.charge
		#print "<<<"

		#erg = calcsf.totalcalcsf(lwBndC, upBndC,

		erg = calcsf.calcsf((lwBndC, upBndC,
								lwBndH, upBndH,
								lwBndO, upBndO,
								lwBndN, upBndN,
								lwBndP, upBndP,
								lwBndS, upBndS,
								lwBndNa, upBndNa,
								lwBndD, upBndD,
								lwBndCi, upBndCi,
								lwBndCl, upBndCl,
								lwBndLi, upBndLi,
								lwBndNi, upBndNi,
								lwBndF, upBndF,
								lwBndI, upBndI,
								lwBndAg, lwBndAg,
								lwBndAl, lwBndAl,
								lwBndW, lwBndW,
								lwBndTi, lwBndTi,
								#lwBndK, upBndK,
								#lwBndCs, upBndCs,
								#lwBndBr, upBndBr,
								m, t, self.lwBoundDbEq, self.upBoundDbEq, int(self.charge)))

		for i in erg:

			# make new ElementSequence
			elemseq = ElementSequence()

			if i[0] > 0:
				elemseq.append(copy(sym2elt_const['C']))
				elemseq._seq['C']._count = i[0]
			if i[1] > 0:
				elemseq.append(copy(sym2elt_const['H']))
				elemseq._seq['H']._count = i[1]
			if i[2] > 0:
				elemseq.append(copy(sym2elt_const['O']))
				elemseq._seq['O']._count = i[2]
			if i[3] > 0:
				elemseq.append(copy(sym2elt_const['N']))
				elemseq._seq['N']._count = i[3]
			if i[4] > 0:
				elemseq.append(copy(sym2elt_const['P']))
				elemseq._seq['P']._count = i[4]
			if i[5] > 0:
				elemseq.append(copy(sym2elt_const['S']))
				elemseq._seq['S']._count = i[5]
			if i[6] > 0:
				elemseq.append(copy(sym2elt_const['Na']))
				elemseq._seq['Na']._count = i[6]
			if i[7] > 0:
				elemseq.append(copy(sym2elt_const['D']))
				elemseq._seq['D']._count = i[7]
			if i[8] > 0:
				elemseq.append(copy(sym2elt_const['Ci']))
				elemseq._seq['Ci']._count = i[8]
			if i[9] > 0:
				elemseq.append(copy(sym2elt_const['Cl']))
				elemseq._seq['Cl']._count = i[9]
			if i[10] > 0:
				elemseq.append(copy(sym2elt_const['Li']))
				elemseq._seq['Li']._count = i[10]
			if i[11] > 0:
				elemseq.append(copy(sym2elt_const['Ni']))
				elemseq._seq['Ni']._count = i[11]
			if i[12] > 0:
				elemseq.append(copy(sym2elt_const['F']))
				elemseq._seq['F']._count = i[12]
			if i[13] > 0:
				elemseq.append(copy(sym2elt_const['I']))
				elemseq._seq['I']._count = i[13]
			if i[14] > 0:
				elemseq.append(copy(sym2elt_const['Ag']))
				elemseq._seq['Ag']._count = i[14]
			if i[15] > 0:
				elemseq.append(copy(sym2elt_const['Al']))
				elemseq._seq['Al']._count = i[15]
			if i[16] > 0:
				elemseq.append(copy(sym2elt_const['W']))
				elemseq._seq['W']._count = i[16]
			if i[17] > 0:
				elemseq.append(copy(sym2elt_const['Ti']))
				elemseq._seq['Ti']._count = i[17]
			#if i[14] > 0:
			#	elemseq.append(copy(sym2elt_const['K']))
			#	elemseq._seq['K']._count = i[14]
			#if i[15] > 0:
			#	elemseq.append(copy(sym2elt_const['Cs']))
			#	elemseq._seq['Cs']._count = i[15]
			#if i[16] > 0:
			#	elemseq.append(copy(sym2elt_const['Br']))
			#	elemseq._seq['Br']._count = i[16]

			elemseq.charge = self.charge

			if elemseq.charge > 0:
				self.polarity = 1
			elif elemseq.charge < 0:
				self.polarity = -1
			else:
				self.polarity = 0

			res.append(deepcopy(elemseq))

		return res

	def subWoRange(self, elemseq):
		""" This is a version of sub, which does not consider elem ranges which
		are bigger than 1. So it is possible to substract an ElementSequence from
		a sf-constrain.
		"""
		buf = deepcopy(self)
		for i in list(elemseq.keys()):
			if i.sym in self:
				# normal case
				if len(self._seq[i.sym]._range) == 1 and len(i._range) == 1:
					elem._range[0] -= i._range[0]
					if elem._range[0] < 0:
						raise ValueError("negative element substraction")
				# negative substraction
				elif len(elem._range) == 0 and len(i._range) == 1:
					raise ValueError("negative element substraction")
				# one of both have a range instead of a integer
				elif len(elem._range) > 1 or len(i._range) > 1:
					pass
				else:
					raise TypeError("Substraction not possible because of element values")
		return buf

def calcSFbyMass(mass, sfconstraint, tolerance, nearest=False):
	"""IN: mass in m/z,
	sf-constraint,
	tolerance in resolution type,
	nearest in Boolean
OUT: list of SurveyEntry
"""
	#print("calcSFbyMass......... mass, sfconstraint, tolerance, nearest ", mass,sfconstraint, tolerance,nearest)
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


