### functions returning the content of objects ###
import sys, traceback, threading, re
from UserDict import DictMixin

class staticTypeDict(DictMixin):
	'''A static typed dictionary'''

	def __init__(self):
		self._data = {}
		self._type = {}

	def __setitem__(self, key, value):
		'''If value is a tuple with (value, type),
		it sets the type of the element. Having it
		singleton sets the value after checking the
		type.'''

		if not isinstance(value, type(())):
			if key in self._data.keys():
				if not self._type[key] == type(value):
					raise TypeError(value)
				else:
					self._data[key] = value

		elif isinstance(value, type(())):
			self._data[key] = value[0]
			self._type[key] = value[1]

	def __getitem__(self, key):
		return self._data[key]

	def __delitem__(self, key):
		del self._data[key]

	def __repr__(self):
		result = []
		for key in self._data.keys():
			result.append('%s: %s' % (repr(key), repr(self._data[key])))
		return ''.join(['{', ', '.join(result), '}'])

	def keys(self):
		return list(self._data.keys())

	def copy(self):
		copyDict = staticTypeDict()
		copyDict._data = self._data.copy()
		copyDict._type = self._type[:]
		return copyDict

	def sort(self, *args, **kwargs):
		self._data.keys.sort(*args, **kwargs)



class odict(DictMixin):

	def __init__(self):
		self._keys = []
		self._data = {}

	def __setitem__(self, key, value):
		if key not in self._data:
			self._keys.append(key)
		self._data[key] = value


	def __getitem__(self, key):
		return self._data[key]

	def __delitem__(self, key):
		del self._data[key]
		self._keys.remove(key)

	def __repr__(self):
		result = []
		for key in self._keys:
			result.append('%s: %s' % (repr(key), repr(self._data[key])))
		return ''.join(['{', ', '.join(result), '}'])

	def keys(self):
		return list(self._keys)

	def values_sorted(self):
		l = []
		for i in self._keys:
			l.append(self._data[i])
		return l

	def copy(self):
		copyDict = odict()
		copyDict._data = self._data.copy()
		copyDict._keys = self._keys[:]
		return copyDict

	def sort(self, *args, **kwargs):
		self._keys.sort(*args, **kwargs)

# for exception forwarding
def formatExceptionInfo(maxTBlevel=None):
    cla, exc, trbk = sys.exc_info()
    excName = cla.__name__
    try:
        #excArgs = exc.__dict__["args"]
        excArgs = exc.args
    except KeyError:
        excArgs = "<no args>"
    excTb = traceback.format_tb(trbk, maxTBlevel)
    return (excName, excArgs, excTb, exc)

def combinations_with_replacement(iterable, r):
    # combinations_with_replacement('ABC', 2) --> AA AB AC BB BC CC
    pool = tuple(iterable)
    n = len(pool)
    if not n and r:
        return
    indices = [0] * r
    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(range(r)):
            if indices[i] != n - 1:
                break
        else:
            return
        indices[i:] = [indices[i] + 1] * (r - i)
        yield tuple(pool[i] for i in indices)

def permutations(iterable, r=None):
    # permutations('ABCD', 2) --> AB AC AD BA BC BD CA CB CD DA DB DC
    # permutations(range(3)) --> 012 021 102 120 201 210
    pool = tuple(iterable)
    n = len(pool)
    r = n if r is None else r
    if r > n:
        return
    indices = range(n)
    cycles = range(n, n-r, -1)
    yield tuple(pool[i] for i in indices[:r])
    while n:
        for i in reversed(range(r)):
            cycles[i] -= 1
            if cycles[i] == 0:
                indices[i:] = indices[i+1:] + indices[i:i+1]
                cycles[i] = n - i
            else:
                j = cycles[i]
                indices[i], indices[-j] = indices[-j], indices[i]
                yield tuple(pool[i] for i in indices[:r])
                break
        else:
            return


### some helpful functions ###
def op(operator, left, right):
	if operator == '+':
		return left + right
	if operator == '-':
		return left - right
	if operator == '*':
		return left * right
	if operator == '/':
		if float(right) != 0.0:
			return left / right
		else:
			return 0.0

def removePermutations(listVariables):

	for i in listVariables:
		i.sort(cmp = peakMarking.TypeMark.cmpMassPermutation)
		#i.sort()

	listOut = []
	for i in listVariables:
		isIn = False
		for j in listOut:
			same = True
			for index in range(len(i)):

				# compare chemical sum compositions, to see, if the fragments are the same
				if i[index].chemsc != j[index].chemsc:
					same = False
			if same:
				isIn = True

		if not isIn:
			listOut.append(i)

	return listOut

def connectLists(pivotList, additionalList):
	result = []
	for p in pivotList:
		if p in additionalList:
			result.append(p)
			del additionalList[additionalList.index(p)]
		else:
			#result.append(None)
			result.append(p)

	#if s:
	if additionalList != []:
		for a in additionalList:
			result.append(a)

	return result

mkCrossProduct = lambda ss,row=[],level=0: len(ss)>1 \
	and reduce(lambda x,y:x+y,[mkCrossProduct(ss[1:],row+[i],level+1) for i in ss[0]]) \
	or [row+[i] for i in ss[0]]

def mkCrossProduct2(*args):
	ans = [[]]
	for arg in args:
		ans = [x+[y] for x in ans for y in arg]
	return ans

def mkCrossProduct3(*sets):
	wheels = map(iter, sets) # wheels like in an odometer
	digits = [it.next() for it in wheels]
	while True:
		yield digits[:]
		for i in range(len(digits)-1, -1, -1):
			try:
				digits[i] = wheels[i].next()
				break
			except StopIteration:
				wheels[i] = iter(sets[i])
				digits[i] = wheels[i].next()
		else:
			break

def print_exc_plus():
	"""
	Print the usual traceback information, followed by a listing of all the
	local variables in each frame.
	"""
	tb = sys.exc_info()[2]
	stack = []

	while tb:
		stack.append(tb.tb_frame)
		tb = tb.tb_next

#	while 1:
#		if not tb.tb_next:
#			break
#		tb = tb.tb_next
#	stack = []
#	f = tb.tb_frame
#	while f:
#		stack.append(f)
#		f = f.f_back
#	stack.reverse()

	traceback.print_exc()
	print "Locals by frame, innermost last"
	for frame in stack:
		print
		print "Frame %s in %s at line %s" % (frame.f_code.co_name,
			frame.f_code.co_filename,
			frame.f_lineno)
		for key, value in frame.f_locals.items():
			print "\t%20s = " % key,
			#We have to be careful not to cause a new error in our error
			#printer! Calling str() on an unknown object could cause an
			#error we don't want.
			try:
				print value
			except:
				print "<ERROR WHILE PRINTING VALUE>"

def printDict(di, format="%-25s %s"):
	for (key, val) in di.items():
		print format % (str(key)+':', val)

def dumpObj(obj, maxlen=77, lindent=24, maxspew=600):
	"""Print a nicely formatted overview of an object.

	The output lines will be wrapped at maxlen, with lindent of space
	for names of attributes.  A maximum of maxspew characters will be
	printed for each attribute value.

	You can hand dumpObj any data type -- a module, class, instance,
	new class.

	Note that in reformatting for compactness the routine trashes any
	formatting in the docstrings it prints.

	Example:
	>>> class Foo(object):
	  a = 30
	  def bar(self, b):
	   "A silly method"
	   return a*b
	... ... ... ...
	>>> foo = Foo()
	>>> dumpObj(foo)
	Instance of class 'Foo' as defined in module __main__ with id 136863308
	Documentation string:   None
	Built-in Methods:	__delattr__, __getattribute__, __hash__, __init__
		  __new__, __reduce__, __repr__, __setattr__,
		  __str__
	Methods:
		 bar	   "A silly method"
	Attributes:
		 __dict__	 {}
		 __weakref__	 None
		 a		 30
	"""

	import types

	# Formatting parameters.
	ltab	= 2	# initial tab in front of level 2 text

	# There seem to be a couple of other types; gather templates of them
	MethodWrapperType = type(object().__hash__)

	#
	# Gather all the attributes of the object
	#
	objclass  = None
	objdoc	= None
	objmodule = '<None defined>'

	methods   = []
	builtins  = []
	classes   = []
	attrs	 = []
	for slot in dir(obj):
		attr = getattr(obj, slot)
		if   slot == '__class__':
			objclass = attr.__name__
		elif slot == '__doc__':
			objdoc = attr
		elif slot == '__module__':
			objmodule = attr
		elif (isinstance(attr, types.BuiltinMethodType) or
	 isinstance(attr, MethodWrapperType)):
			builtins.append( slot )
		elif (isinstance(attr, types.MethodType) or
	 isinstance(attr, types.FunctionType)):
			methods.append( (slot, attr) )
		elif isinstance(attr, types.TypeType):
			classes.append( (slot, attr) )
		else:
			attrs.append( (slot, attr) )

	#
	# Organize them
	#
	methods.sort()
	builtins.sort()
	classes.sort()
	attrs.sort()

	#
	# Print a readable summary of those attributes
	#
	normalwidths = [lindent, maxlen - lindent]
	tabbedwidths = [ltab, lindent-ltab, maxlen - lindent - ltab]

	def truncstring(s, maxlen):
		if len(s) > maxlen:
			return s[0:maxlen] + ' ...(%d more chars)...' % (len(s) - maxlen)
		else:
			return s

	# Summary of introspection attributes
	if objclass == '':
		objclass = type(obj).__name__
	intro = "Instance of class '%s' as defined in module %s with id %d" % \
			(objclass, objmodule, id(obj))
	print '\n'.join(prettyPrint(intro, maxlen))

	# Object's Docstring
	if objdoc is None:
		objdoc = str(objdoc)
	else:
		objdoc = ('"""' + objdoc.strip()  + '"""')
	print
	print prettyPrintCols( ('Documentation string:',
				truncstring(objdoc, maxspew)),
		normalwidths, ' ')

	# Built-in methods
	if builtins:
		bi_str   = delchars(str(builtins), "[']") or str(None)
		print
		print prettyPrintCols( ('Built-in Methods:',
		truncstring(bi_str, maxspew)),
		 normalwidths, ', ')

	# Classes
	if classes:
		print
		print 'Classes:'
	for (classname, classtype) in classes:
		classdoc = getattr(classtype, '__doc__', None) or '<No documentation>'
		print prettyPrintCols( ('',
		classname,
		truncstring(classdoc, maxspew)),
		 tabbedwidths, ' ')

	# User methods
	if methods:
		print
		print 'Methods:'
	for (methodname, method) in methods:
		methoddoc = getattr(method, '__doc__', None) or '<No documentation>'
		print prettyPrintCols( ('',
		methodname,
		truncstring(methoddoc, maxspew)),
		 tabbedwidths, ' ')

	# Attributes
	if attrs:
		print
		print 'Attributes:'
	for (attr, val) in attrs:
		print prettyPrintCols( ('',
		attr,
		truncstring(str(val), maxspew)),
		 tabbedwidths, ' ')

def prettyPrintCols(strings, widths, split=' '):
	"""Pretty prints text in colums, with each string breaking at
	split according to prettyPrint.  margins gives the corresponding
	right breaking point."""

	assert len(strings) == len(widths)

	strings = map(nukenewlines, strings)

	# pretty print each column
	cols = [''] * len(strings)
	for i in range(len(strings)):
		cols[i] = prettyPrint(strings[i], widths[i], split)

	# prepare a format line
	format = ''.join(["%%-%ds" % width for width in widths[0:-1]]) + "%s"

	def formatline(*cols):
		return format % tuple(map(lambda s: (s or ''), cols))

	# generate the formatted text
	return '\n'.join(map(formatline, *cols))

def prettyPrint(string, maxlen=75, split=' '):
	"""Pretty prints the given string to break at an occurrence of
	split where necessary to avoid lines longer than maxlen.

	This will overflow the line if no convenient occurrence of split
	is found"""

	# Tack on the splitting character to guarantee a final match
	string += split

	lines   = []
	oldeol  = 0
	eol	 = 0
	while not (eol == -1 or eol == len(string)-1):
		eol = string.rfind(split, oldeol, oldeol+maxlen+len(split))
		lines.append(string[oldeol:eol])
		oldeol = eol + len(split)

	return lines

def nukenewlines(string):
	"""Strip newlines and any trailing/following whitespace; rejoin
	with a single space where the newlines were.

	Bug: This routine will completely butcher any whitespace-formatted
	text."""

	if not string: return ''
	lines = string.splitlines()
	return ' '.join( [line.strip() for line in lines] )

def delchars(str, chars):
	"""Returns a string for which all occurrences of characters in
	chars have been removed."""

	# Translate demands a mapping string of 256 characters;
	# whip up a string that will leave all characters unmolested.
	identity = ''.join([chr(x) for x in range(256)])

	return str.translate(identity, chars)


def dbgout(text):
	#print "[%s] %s" % (sys._getframe(1).f_code.co_name, text)
	print text
	return None

def reportout(text):
	print text
	return None

def strToBool(s):

	if isinstance(s, type(True)):
		return s

	if re.match('True', s):
		return True
	elif re.match('False', s):
		return False
	else:
		return False

def tidy_float(s):
	"""Return tidied float representation.
	Remove superflous leading/trailing zero digits.
	Remove '.' if value is an integer.
	Return '****' if float(s) fails.
	"""
	s = str(s)

	# float?
	try:
		f = float(s)
	except ValueError:
		return '****'
	# int?
	try:
		i = int(s)
		return str(i)
	except ValueError:
		pass
	# scientific notation?
	if 'e' in s or 'E' in s:
		t = s.lstrip('0')
		if t.startswith('.'): t = '0' + t
		return t
	# float with integral value (includes zero)?
	i = int(f)
	if i == f:
		return str(i)
	assert '.' in s
	t = s.strip('0')
	if t.startswith('.'): t = '0' + t
	if t.endswith('.'): t += '0'
	return t

def number_shaver(ch,
	regx = re.compile('(?<![\d.])0*(?:'
					  '(\d+)\.?|\.(0)'
					  '|(\.\d+?)|(\d+\.\d+?)'
					  ')0*(?![\d.])')  ,
	repl = lambda mat: mat.group(mat.lastindex)
					if mat.lastindex!=3
					else '0' + mat.group(3) ):

	return regx.sub(repl,ch)

# This routine was written by Tim Peters and is freeware
def permute2(seqs):
	n = len(seqs)
	if n == 0:
		return []
	if n == 1:
		return map(lambda i: (i,), seqs[0])
	# find good splitting point
	prods = []
	prod = 1
	for x in seqs:
		prod = prod * len(x)
		prods.append(prod)
	for i in range(n):
		if prods[i] ** 2 >= prod:
			break
	n = min(i + 1, n - 1)
	a = permute2(seqs[:n])
	b = permute2(seqs[n:])
	sprayb = []
	lena = len(a)
	for x in b:
		sprayb[len(sprayb):] = [x] * lena
	import operator
	return map(operator.add, a * len(b), sprayb)

# kSubset() and nkRange: Copyright 2006 Gerard Flanagan
def kSubsets( alist, k ):
    n = len(alist)
    for vector in nkRange(n, k):
        ret = []
        for i in vector:
            ret.append( alist[i-1] )
        yield ret

def nkRange(n,k):
    m = n - k + 1
    indexer = range(0, k)
    vector = range(1, k+1)
    last = range(m, n+1)
    yield vector
    while vector != last:
        high_value = -1
        high_index = -1
        for i in indexer:
            val = vector[i]
            if val > high_value and val < m + i:
                high_value = val
                high_index = i
        for j in range(k - high_index):
            vector[j+high_index] = high_value + j + 1
        yield vector

# allcombinations(); 2006-06-27 00:12:43; by GustavoNiemeyer; http://labix.org/snippets/permutations

def allcombinations(lst):
    queue = [-1]
    lenlst = len(lst)
    while queue:
        i = queue[-1]+1
        if i == lenlst:
            queue.pop()
        else:
            queue[-1] = i
            yield [lst[j] for j in queue]
            if len(queue) < lenlst:
                queue.append(-1)

def atLeastOneisIn(lst1, lst2):
	for i in lst1:
		if i in lst2:
			return True
	return False

def sortDictKeys(adict, compare = 'string'):
	items = adict.items()
	if compare == 'float':
		items.sort(cmp = lambda i,j : (cmp(float(i[0]), float(j[0]))))
	else:
		items.sort()
	return [key for key, value in items]

def uniqueLists(lst):
	lst.sort()
	last = lst[0]
	lasti = i = 1
	while i < len(lst):
		if len(lst[i]) == len(last):
			for j in range(len(lst[i])):
				if lst[i][j] != last[j]:
					lst[lasti] = last = lst[i]
					lasti += 1
		else:
			lst[lasti] = last = lst[i]
			lasti += 1
		i += 1
	return lst[:lasti]

def unique(l):
	last = l[0]
	lasti = i = 1
	while i < len(l):
		if l[i] != last:
			l[lasti] = last = l[i]
			lasti += 1
		i += 1
	return l[:lasti]

def reduceDoubleListEntries(list):
	l = []
	for i in range(len(list)):
		if not list[i] in l:
			l.append(list[i])

	return l

def intersect(seq1, seq2):
    res = []                     # start empty
    for x in seq1:               # scan seq1
        if x in seq2:            # common item?
            res.append(x)        # add to end
    return res

def union(seq1, seq2):
	res = []                     # start empty
	for x in seq1:               # scan seq1
		res.append(x)        # add to end
	for x in seq2:
		if not x in res:
			res.append(x)
	return res

def unionSF(seq1, seq2, newTag):
	res = []                     # start empty
	for x in seq1:               # scan seq1
		res.append(x)        # add to end
	for x in seq2:
		if not x in res:
			x.scriptTag = [newTag]
			res.append(x)
		else:
			x.scriptTag.append(newTag)
	return res

def log(str):

	print "[", sys._getframe(1).f_code.co_name,"]\n", str
	print ""

def xlcmp(x, yin):
	different = True
	y = deepcopy(yin)
	for i in x:
		if i in y: del y[y.index(i)]
		else: different = False

	if not different: return 0
	else: return -1

def sort_by_attr2_old(seq, attr):
#	intermed = [ (getattr(seq[i][0],attr), i, seq[i][0]) for i in xrange(len(seq)) ]

	inter = []
	for i in xrange(len(seq)):
		if not isinstance(seq[i][0], str):
			inter.append((getattr(seq[i][0],attr), i, seq[i][0]))
		else:
			inter.append((seq[i][0], i, seq[i][0]))
	inter.sort()
	return [ [tup[-1]] for tup in inter ]

def sort_by_attr2(seq, attr):
#	intermed = [ (getattr(seq[i][0],attr), i, seq[i][0]) for i in xrange(len(seq)) ]

	inter = []
	for i in xrange(len(seq)):
		if not isinstance(seq[i], str):
			inter.append((getattr(seq[i],attr), i, seq[i]))
		else:
			inter.append((seq[i], i, seq[i]))
	inter.sort()
	return [ [tup[-1]] for tup in inter ]


'''
ansi.py

ANSI Terminal Interface

(C)opyright 2000 Jason Petrone <jp_py@demonseed.net>
All Rights Reserved

Color Usage:
  print RED + 'this is red' + RESET
  print BOLD + GREEN + WHITEBG + 'this is bold green on white' + RESET

Commands:
  def move(new_x, new_y): 'Move cursor to new_x, new_y'
  def moveUp(lines): 'Move cursor up # of lines'
  def moveDown(lines): 'Move cursor down # of lines'
  def moveForward(chars): 'Move cursor forward # of chars'
  def moveBack(chars): 'Move cursor backward # of chars'
  def save(): 'Saves cursor position'
  def restore(): 'Restores cursor position'
  def clear(): 'Clears screen and homes cursor'
  def clrtoeol(): 'Clears screen to end of line'
'''

################################
# C O L O R  C O N S T A N T S #
################################
BLACK = '\033[30m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'
WHITE = '\033[37m'

RESET = '\033[0;0m'
BOLD = '\033[1m'
REVERSE = '\033[2m'

BLACKBG = '\033[40m'
REDBG = '\033[41m'
GREENBG = '\033[42m'
YELLOWBG = '\033[43m'
BLUEBG = '\033[44m'
MAGENTABG = '\033[45m'
CYANBG = '\033[46m'
WHITEBG = '\033[47m'

def move(new_x, new_y):
  'Move cursor to new_x, new_y'
  print '\033[' + str(new_x) + ';' + str(new_y) + 'H'

def moveUp(lines):
  'Move cursor up # of lines'
  print '\033[' + str(lines) + 'A'

def moveDown(lines):
  'Move cursor down # of lines'
  print '\033[' + str(lines) + 'B'

def moveForward(chars):
  'Move cursor forward # of chars'
  print '\033[' + str(chars) + 'C'

def moveBack(chars):
  'Move cursor backward # of chars'
  print '\033[' + str(chars) + 'D'

def save():
  'Saves cursor position'
  print '\033[s'

def restore():
  'Restores cursor position'
  print '\033[u'

def clear():
  'Clears screen and homes cursor'
  print '\033[2J'

def clrtoeol():
  'Clears screen to end of line'
  print '\033[K'


