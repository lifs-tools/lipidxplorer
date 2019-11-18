import ply.lex as lex

from lx.mfql.runtimeStatic import *
from lx.mfql.runtimeExecution import *
from lx.mfql.peakMarking import TypeScan, TypeMarkTerm
from lx.mfql.chemParser import parseElemSeq
from lx.mfql.chemsc import ElementSequence, SCConstraint
from lx.spectraContainer import SurveyEntry
from lx.mfql.generateMasterScan import genMasterScan, saveMasterScan
from lx.exceptions import SyntaxErrorException
import time

keywords = (
	'IDENTIFY', 'WITH', 'WHERE', 'AND', 'OR',
	'TOLERANCE', 'MINOCC', 'MAXOCC', 'MASSRANGE', 'DBR', 'CHG',
	'NOT', 'DA', 'PPM', 'RES', 'DEFINE', 'IN', 'MS1', 'MS2',
	'REPORT', 'SUCHTHAT',
	'QUERYNAME', 'AS', 'NEUTRALLOSS'
)

# list of token names
tokens = keywords + (
	'EQUALS', 'IS', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'LPAREN',
	'RPAREN', 'LT', 'LE', 'GT', 'GE', 'IFA', 'IFF', 'NE', 'COMMA', 'SEMICOLON',
	'FLOAT', 'STRING', 'ID', 'INTEGER', 'DOT', 'PERCENT', 'LBRACE',
	'RBRACE', 'LBRACKET', 'RBRACKET', 'SFSTRING', 'ARROW', 'ARROWR'
)

# ignoring characters (space and tab)
#t_ignore_WHITESPACE = r'\s'
#t_ignore_TAB = r'\t'
#t_ignore_COMMENT = r'\#.*'
#t_ignore_CR = r'\n'


#def t_CR(t):
#	r'\r'
#	pass

#def t_CRNL(t):
#	r'\r\n'
#	pass

def t_ID(t):
	r'[a-zA-Z$][a-zA-Z$0-9]*'
	if t.value in keywords or t.value.upper() in keywords:
		t.type = t.value.upper()
	return t

# regular expression rules for simple tokens
t_EQUALS  = r'=='
t_IS	  = r'='
t_PLUS	= r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_LBRACE  = r'\['
t_RBRACE  = r'\]'
t_LBRACKET= r'\{'
t_RBRACKET= r'\}'
t_LE	  = r'<='
t_NE	  = r'<>'
t_LT	  = r'<'
t_GE	  = r'>='
t_GT	  = r'>'
t_ARROW   = r'->'
t_ARROWR  = r'<~'
t_IFA	  = r'=>'
t_IFF	  = r'<=>'
t_COMMA   = r'\,'
t_SEMICOLON = r';'
t_FLOAT   = r'(\+|-)?((\d*\.\d+)(E[\+-]?\d+)?|([1-9]\d*E[\+-]?\d+))'
t_INTEGER = r'(\+|-)?\d+'
t_STRING  = r'\".*?\"'
t_SFSTRING  = r'\'.*?\''
t_DOT	  = r'\.'
t_PERCENT = r'%'

#t_ignore = '\t\n'
#t_ignore = ' \t'

def t_comment(t):
	r'[ ]*\043[^\n]*'
	t.lexer.lineno += t.value.count("\n")
	pass

def t_WS(t):
	r'[ \t]+'
	pass

def t_WS_NL(t):
	r'(([ \t]*)\n)'
	t.lexer.lineno += t.value.count("\n")
	pass

#def t_NEWLINE(t):
#	r'\n+'
#	t.lexer.lineno += t.value.count("\n")
#	print ">>> NL", t.value.count("\n")
#
#def t_TAB(t):
#	r'\t'
#	pass

def t_UNDERSCORE(t):
	r'_'
	raise SyntaxErrorException("In query %s, line %d: No underscore allowed." % (mfqlObj.filename, t.lexer.lineno),
			mfqlObj.filename,
			"",
			0)

def t_error(t):
	if not ord(t.value[0]) == 13:
		print("Illegal character %s (%s) in line %d" % (t.value[0], ord(t.value[0]), t.lexer.lineno))
	t.lexer.skip(1)

# build lexer
import re
lexer = lex.lex(reflags = re.I, debug = 0, optimize = 0)


###############################################################################
########################### Parser starts here ################################
###############################################################################

import ply.yacc as yacc

# for the testing: the first semantics

# current scope
namespace = {}
scanResults = {}

# name of the identification
strIdentification = ''

globalPrecursor = {}
programMode = ''

precedence = (
	('left', 'OR'),
	('left', 'AND', 'IFF', 'IFA', 'ARROW'),
	('left', 'EQUALS', 'NE'),
	('nonassoc', 'LT', 'GT', 'GE', 'LE', 'ARROWR'),
	('left', 'PLUS', 'MINUS'),
	('left', 'TIMES', 'DIVIDE'),
	('left', 'NOT'),
	('right', 'UMINUS')
	)

### PROGRAMM ###

def p_program_multi(p):
	'''program  : program script SEMICOLON'''


def p_program_single(p):
	'''program  : script SEMICOLON'''

	p[0] = mfqlObj.dictDefinitionTable

def p_script(p):
	'''script  : scriptname variables identification
			   | identification'''

def p_script_error(p):
	'''script : error variables identification'''
	print("SYNTAX ERROR: 'QUERYNAME' is missing")


### VARIABLES ###

def p_scriptname(p):
	'''scriptname : QUERYNAME IS getQueryName SEMICOLON'''

	global gprogressCount
	global numQueries

	if mfqlObj.parsePart == 'identification' or mfqlObj.parsePart == 'genTargetList':

		numQueries += 1
		if numQueries > 1:
			raise SyntaxErrorException("There is only one query per *.mfql file allowed!",
					mfqlObj.filename,
					0)

		mfqlObj.listQueryNames.append(p[3])
		mfqlObj.dictEnvironment[p[3]] = []
		mfqlObj.scan = TypeScan(mfqlObj = mfqlObj)
		mfqlObj.scan.scanTerm = []
		mfqlObj.scan.wasOR = False
		mfqlObj.dictDefinitionTable[mfqlObj.queryName] = {}

		#gprogressCount += 1
		#if gparent:
		#	(cont, skip) = gparent.debug.progressDialog.Update(gprogressCount)
		#	if not cont:
		#		gparent.debug.progressDialog.Destroy()
		#		return gparent.CONST_THREAD_USER_ABORT


	p[0] = p[3]

def p_getQueryName(p):
	'''getQueryName : ID'''

#	'''tagname : ID'''
	mfqlObj.queryName = p[1]


def p_variables_loop(p):
	'''variables : variables var'''

def p_variables_endloop(p):
	'''variables : var'''

def p_var_normal(p):
	'''var : DEFINE ID IS object options SEMICOLON
			| DEFINE ID IS object options AS NEUTRALLOSS SEMICOLON'''

	if len(p) == 7 and p[5] != None:
		p[4].addOptions(p[5])

	elif len(p) == 9:
		if p[5] != None: # options are given
			index = 0

			# accidantly the user could have added a CHG option,
			# although it is a neutral loss
			while index < len(p[5]):
				if p[5][index][0] == "chg":
					del p[5][index]
				else:
					index += 1
			p[5].append(("chg", 0))
			p[4].addOptions(p[5])
		else:
			p[4].addOptions([("chg", 0)])

#	if isinstance(p[4], TypeList):
#		for n in p[4]:
#			if mfqlObj.queryName and mfqlObj.queryName != "":
#				name = mfqlObj.queryName + mfqlObj.namespaceConnector + n.variable
#			else:
#				name = n.variable
#			mfqlObj.dictDefinitionTable[mfqlObj.queryName][name] = deepcopy(p[4])
#
#	else:

	if mfqlObj.queryName and mfqlObj.queryName != "":
		name = mfqlObj.queryName + mfqlObj.namespaceConnector + p[2]
	else:
		name = p[2]

	mfqlObj.dictDefinitionTable[mfqlObj.queryName][name] = p[4]

#def p_var_list(p):
#	'''var : DEFINE list IS object options SEMICOLON'''

#	if len(p) == 7 and p[5] != None:
#		p[4].addOptions(p[5])

#	for n in p[2]:
#		if mfqlObj.queryName and mfqlObj.queryName != "":
#			name = mfqlObj.queryName + mfqlObj.namespaceConnector + n.variable
#		else:
#			name = n.variable
#		mfqlObj.dictDefinitionTable[mfqlObj.queryName][name] = deepcopy(p[4])

def p_var_emptyVar(p):
	'''var : DEFINE ID options SEMICOLON'''

	if len(p) == 5 and p[3] != None:
		o = TypeSFConstraint(elementSequence = ElementSequence())
		o.addOptions(p[3])
	else:
		o = TypeSFConstraint(elementSequence = None)

	if mfqlObj.queryName and mfqlObj.queryName != "":
		name = mfqlObj.queryName + mfqlObj.namespaceConnector + p[2]
	else:
		name = p[2]
	mfqlObj.dictDefinitionTable[mfqlObj.queryName][name] = o

### OBJECT ###

def p_object_withAttr(p):
	'''object : withAttr'''
	p[0] = p[1]

def p_object_onlyObj(p):
	'''object : onlyObj'''

	if len(p) == 2:
		p[0] = p[1]


### OBJECT/VARCONTENT ###

def p_onlyObj_ID_itemAccess(p):
	'''onlyObj : ID LBRACE ID RBRACE'''
	p[0] = TypeVariable(variable = p[1], item = p[3])
	mfqlObj.listDataTable.append(p[0])

def p_onlyObj_ID(p):
	'''onlyObj : ID'''
	p[0] = TypeVariable(variable = p[1])
	mfqlObj.listDataTable.append(p[0])

def p_onlyObj_list(p):
	'''onlyObj : list'''
	p[0] = TypeList(list = p[1])

	#mfqlObj.listDataTable.append(p[1])

def p_onlyObj_varcontent(p):
	'''onlyObj : varcontent'''
	p[0] = p[1]

def p_onlyObj_function1(p):
	'''onlyObj : ID LPAREN arguments RPAREN LBRACE ID RBRACE'''
	p[0] = TypeFunction(name = p[1], arguments = p[3], mfqlObj = mfqlObj, item = p[6])
	mfqlObj.listDataTable.append(p[1])

def p_onlyObj_function2(p):
	'''onlyObj : ID LPAREN arguments RPAREN'''
	p[0] = TypeFunction(name = p[1], arguments = p[3], mfqlObj = mfqlObj)
	mfqlObj.listDataTable.append(p[1])

def p_withAttr_accessItem_(p):
	'''withAttr : ID DOT ID LBRACE ID RBRACE'''
	#p[0] = TypeItem(variable = p[1], attribute = p[3], item = p[5])
	p[0] = TypeVariable(variable = p[1], attribute = p[3], item = p[5])
	mfqlObj.listDataTable.append(p[0])

def p_withAttr_accessItem_string(p):
	'''withAttr : ID DOT ID LBRACE STRING RBRACE'''
	#p[0] = TypeItem(variable = p[1], attribute = p[3], item = p[5])
	p[0] = TypeVariable(variable = p[1], attribute = p[3], item = p[5])
	mfqlObj.listDataTable.append(p[0])

def p_withAttr_id(p):
	'''withAttr : ID DOT ID'''
#	p[0] = TypeAttribute(
#		variable = mfqlObj.dictDefinitionTable[p[1]],
#		attribute = p[3])
	p[0] = TypeVariable(variable = p[1], attribute = p[3])

	mfqlObj.listDataTable.append(p[0])

def p_withAttr_varcontent(p):
	'''withAttr : varcontent DOT ID'''
	#p[0] = TypeAttribute(mass = p[1], attribute = p[3])
	p[0] = TypeVariable(variable = p[1], attribute = p[3])

	mfqlObj.listDataTable.append(p[0])

def p_withAttr_list(p):
	'''withAttr : list DOT ID'''
	p[0] = TypeAttribute(sequence = p[1], attribute = p[3])

	mfqlObj.listDataTable.append(p[0])

def p_arguments_empty(p):
	'''arguments :'''
	p[0] = None

def p_arguments_single(p):
	'''arguments : expression'''
	p[0] = [p[1]]

def p_arguments_multi(p):
	'''arguments : arguments COMMA expression'''
	p[0] = p[1]
	p[0].append(p[3])


### LIST ###

def p_list(p):
	'''list : LBRACKET listcontent RBRACKET'''
	#'''list : LPAREN listcontent RPAREN'''

	p[0] = p[2]
	mfqlObj.listDataTable.append(p[0])

def p_listcontent_cont(p):
	'''listcontent : listcontent COMMA object'''

	p[0] = p[1]
	if len(p) == 4:
		p[0].append(p[3])

def p_listcontent_obj(p):
	'''listcontent : object'''

	if len(p) == 2:
		p[0] = [p[1]]

### VARCONTENT ###

def p_varcontent_tolerance(p):
	'''varcontent : tolerancetype'''

	p[0] = p[1]

def p_varcontent_float(p):
	'''varcontent : FLOAT'''

	p[0] = TypeFloat(float = float(p[1]), mass = float(p[1]))

#def p_varcontent_negfloat(p):
#	'''varcontent : MINUS FLOAT'''
#
#	p[0] = TypeFloat(float = -float(p[1]), mass = -float(p[1]))

def p_varcontent_integer(p):
	'''varcontent : INTEGER
				  | PLUS INTEGER
				  | MINUS INTEGER'''

	if len(p) == 2:
		p[0] = TypeFloat(float = float(p[1]), mass = float(p[1]))
	else:
		if p[1] == 'PLUS':
			p[0] = TypeFloat(float = float(p[2]), mass = float(p[2]))
		else:
			p[0] = TypeFloat(float = -float(p[2]), mass = -float(p[2]))

#def p_varcontent_signedInteger(p):
#	'''varcontent : MINUS INTEGER'''
#
#	p[0] = TypeFloat(float = -float(p[2]), mass = -float(p[2]))

def p_varcontent_string(p):
	'''varcontent : STRING'''

	p[0] = TypeString(string = p[1].strip('"'))
	#p[0] = TypeMassList(file = p[1].strip('"'))

def p_varcontent_sfstring(p):
	'''varcontent : SFSTRING'''

	es = parseElemSeq(p[1].strip('\''))
	if isinstance(es, SCConstraint):
		p[0] = TypeSFConstraint(elementSequence = es)
	else:
		p[0] = TypeElementSequence(elementSequence = es, options = {})

### OPTIONS ###

def p_options_there(p):
	'''options : WITH optioncontent'''
	p[0] = p[2]

def p_options_not_there(p):
	'''options :'''

def p_optioncontent_cont(p):
	'''optioncontent : optioncontent COMMA optionentry'''
	p[0] = p[1]
	p[0].append(p[3])

def p_optioncontent_obj(p):
	'''optioncontent : optionentry'''
	p[0] = [p[1]]


def p_optionentry_dbr(p):
	'''optionentry : DBR IS LPAREN object COMMA object RPAREN'''
	p[0] = ("dbr", [p[4], p[6]])

def p_optionentry_chg(p):
	'''optionentry : CHG IS INTEGER'''
	p[0] = ("chg", int(p[3]))

def p_optionentry_massrange(p):
	'''optionentry : MASSRANGE IS LPAREN object COMMA object RPAREN'''
	p[0] = ("massrange", [int(p[4].float), int(p[6].float)])

def p_optionentry_minocc(p):
	'''optionentry : MINOCC IS object'''
	p[0] = ("minocc", p[3])

def p_optionentry_maxocc(p):
	'''optionentry : MAXOCC IS object'''
	p[0] = ("maxocc", p[3])

def p_optionentry_TOLERANCE(p):
	'''optionentry : TOLERANCE IS tolerancetype'''
	p[0] = ("tolerance", p[3])

def p_tolerancetype(p):
	'''tolerancetype : FLOAT DA
					 | FLOAT PPM
					 | INTEGER DA
		 			 | INTEGER RES
					 | INTEGER PPM'''

	if float(p[1]) <= 0.0:
		raise LogicErrorException(
			"Tolerance value as given in the query '%s' can not be smaller" % mfqlObj.queryName +\
			" or equal zero")

	p[0] = TypeTolerance(p[2].lower(), float(p[1]))


# identification part
def p_identification_normal_old(p):
	'''identification : IDENTIFY tagname WHERE marks evalMarks suchthat REPORT report
		  			  | IDENTIFY tagname WHERE marks evalMarks REPORT report'''

	raise LipidXException("Please remove the query name after 'IDENTIFY'." + \
			" This is not supported anymore.")

	### next the report is generated ###

	if mfqlObj.parsePart == 'genTargetList':
		genMasterScan(mfqlObj)

	elif mfqlObj.parsePart == 'identification':
		print("generating combinatorics ...", end=' ')
		for se in mfqlObj.sc.listSurveyEntry:
			mfqlObj.genVariables_new(se, mfqlObj.dictEmptyVariables)
		print("%.2f sec." % time.clock())

	if len(p) == 8:

		mfqlObj.suchthatApplied = False
		if mfqlObj.parsePart == 'identification':
			query = TypeQuery(mfqlObj = mfqlObj,
							id = mfqlObj.queryName,
							report = p[7],
							withSuchthat = False)

			mfqlObj.result.dictQuery[mfqlObj.queryName] = query

	if len(p) == 9:

		mfqlObj.suchthatApplied = True
		if mfqlObj.parsePart == 'identification':
			query = TypeQuery(mfqlObj = mfqlObj,
							id = mfqlObj.queryName,
							report = p[8],
							withSuchthat = True)

			mfqlObj.result.dictQuery[mfqlObj.queryName] = query

		if mfqlObj.parsePart == 'report':
			mfqlObj.result.dictQuery[mfqlObj.queryName].listVariables = p[6]

def p_identification_normal_new(p):
	'''identification : IDENTIFY marks evalMarks suchthat REPORT report
		  			  | IDENTIFY marks evalMarks REPORT report'''

	### next the report is generated ###

	if mfqlObj.parsePart == 'genTargetList':
		genMasterScan(mfqlObj)

	elif mfqlObj.parsePart == 'identification':
		print("generating combinatorics ...", end=' ')
		for se in mfqlObj.sc.listSurveyEntry:
			mfqlObj.genVariables_new(se, mfqlObj.dictEmptyVariables)
		print("%.2f sec." % time.clock())

	if mfqlObj.parsePart == 'identification':
		print("generating combinatorics ...", end=' ')
		for se in mfqlObj.sc.listSurveyEntry:
			mfqlObj.genVariables_new(se, mfqlObj.dictEmptyVariables)
		print("%.2f sec." % time.clock())


	if len(p) == 6:

		mfqlObj.suchthatApplied = False
		if mfqlObj.parsePart == 'identification':
			query = TypeQuery(mfqlObj = mfqlObj,
							id = mfqlObj.queryName,
							report = p[5])

			mfqlObj.result.dictQuery[mfqlObj.queryName] = query

	if len(p) == 7:

		mfqlObj.suchthatApplied = True
		if mfqlObj.parsePart == 'identification':
			query = TypeQuery(mfqlObj = mfqlObj,
							id = mfqlObj.queryName,
							report = p[6])

			mfqlObj.result.dictQuery[mfqlObj.queryName] = query

		if mfqlObj.parsePart == 'report':
			mfqlObj.result.dictQuery[mfqlObj.queryName].listVariables = p[4]


def p_tagname(p):
	'''tagname : ID'''

	#mfqlObj.queryName = p[1]

	#if mfqlObj.parsePart == 'identification':
	#	mfqlObj.dictEnvironment[p[1]] = []
	#	mfqlObj.scan = TypeScan(mfqlObj = mfqlObj)
	#	mfqlObj.scan.scanTerm = []
	#	mfqlObj.scan.wasOR = False

	p[0] = p[1]

def p_marks(p):
	'''marks : boolmarks'''
#	mfqlObj.scan = TypeScan(mfqlObj = mfqlObj)
#	mfqlObj.scan.scanTerm = []

	if mfqlObj.parsePart == 'identification':
		if not mfqlObj.scan.wasOR:
			mfqlObj.scan.scanTerm.append(p[1])

			# find variables which are DEFINEd but not used in IDENTIFY
			# they might be used later in SUCHTHAT
			for i in list(mfqlObj.dictDefinitionTable[mfqlObj.queryName].keys()):
				if not i in [x.name for x in p[1].list()]:
					name = i.split(mfqlObj.namespaceConnector)
					raise SyntaxErrorException("The variable '%s' in query '%s'has to be used in IDENTIFY" %\
							(name[1], name[0]),
							name[0],
							0)
							#mfqlObj.addEmptyVariable(i,
							#mfqlObj.dictDefinitionTable[mfqlObj.queryName][i])

	#mfqlObj.scan.scanTerm = p[1]

def p_booleanterm_paren(p):
	'''boolmarks : LPAREN boolmarks RPAREN'''
	p[0] = TypeMarkTerm(
			rightSide = p[2],
			leftSide = None,
			boolOp = None,
			mfqlObj = mfqlObj)

def p_boolmarks_not(p):
	'''boolmarks : NOT boolmarks'''

	p[0] = TypeMarkTerm(
			rightSide = p[2],
			leftSide = None,
			boolOp = 'NOT',
			mfqlObj = mfqlObj)

def p_boolmarks_or(p):
	'''boolmarks : boolmarks OR boolmarks'''

	p[0] = TypeMarkTerm(
			leftSide = p[1],
			rightSide = p[3],
			boolOp = p[2],
			mfqlObj = mfqlObj)

def p_boolmarks_and(p):
	'''boolmarks : boolmarks AND boolmarks'''

	p[0] = TypeMarkTerm(
			leftSide = p[1],
			rightSide = p[3],
			boolOp = p[2],
			mfqlObj = mfqlObj)
#	p[0] = ('and', p[1], p[3])

def p_boolmarks_if(p):
	'''boolmarks : boolmarks IFA boolmarks'''

	p[0] = TypeMarkTerm(
			leftSide = p[1],
			rightSide = p[3],
			boolOp = p[2],
			mfqlObj = mfqlObj)
#	p[0] = ('if', p[1], p[3])

def p_boolmarks_onlyif(p):
	'''boolmarks : boolmarks IFF boolmarks'''

	p[0] = TypeMarkTerm(
			leftSide = p[1],
			rightSide = p[3],
			boolOp = p[2],
			mfqlObj = mfqlObj)
#	p[0] = ('iff', p[1], p[3])

def p_boolmarks_arrow(p):
	'''boolmarks : boolmarks ARROW boolmarks'''

	p[0] = TypeMarkTerm(
			leftSide = p[1],
			rightSide = p[3],
			boolOp = p[2],
			mfqlObj = mfqlObj)
#	p[0] = ('iff', p[1], p[3])

def p_boolmarks_le(p):
	'''boolmarks : boolmarks LE boolmarks'''

	p[0] = TypeMarkTerm(
			leftSide = p[1],
			rightSide = p[3],
			boolOp = p[2],
			mfqlObj = mfqlObj)
#	p[0] = ('iff', p[1], p[3])

def p_boolmarks_toScan(p):
	'''boolmarks : scan'''

	p[0] = TypeMarkTerm(
			rightSide = p[1],
			leftSide = None,
			boolOp = None,
			mfqlObj = mfqlObj)

def p_evalMarks(p):
	'''evalMarks : '''
	if mfqlObj.parsePart == 'identification':
		print("IDENTIFY the masses of interest ...", end=' ')
		mfqlObj.scan.evaluate()
		print("%.2f sec." % time.clock())
	pass

def p_suchthat_single(p):
	'''suchthat : SUCHTHAT body'''
	p[0] = p[2]

#def p_suchthat_multi(p):
#	'''suchthat : LPAREN suchthat RPAREN suchthat'''

def p_body_bool(p):
	'''body : bterm'''
	p[0] = p[1]

def p_bterm(p):
	'''bterm : booleanterm'''

	report = []

	# apply SUCHTHAT filter if vars were found
	if mfqlObj.parsePart == 'report':

		print("testing constraints of SUCHTHAT ...", end=' ')
		report = []
		count = 0
		for se in mfqlObj.result[mfqlObj.queryName].sc:

			if se.listVariables != []:

				### add the empty variables to the 'normal'
				#listVariables = []
				#for empty_var in mfqlObj.dictEmptyVariables[mfqlObj.queryName]:
				#	listVariables.append([empty_var])

				for vars in se.listVariables:# + mfqlObj.dictEmptyVariables[mfqlObj.queryName]:

					# check if the variable of se contain at least one coming from the current query
					isIn = False
					for key in list(vars.keys()):
						if mfqlObj.queryName == key.split(mfqlObj.namespaceConnector)[0]:
							isIn = True
							break

					if isIn:

						# add the empty vars to the list of variables
						#if mfqlObj.dictEmptyVariables.has_key(mfqlObj.queryName):
						if False:
							for empty_var in mfqlObj.dictEmptyVariables[mfqlObj.queryName]:
								list_empty_vars = mfqlObj.dictEmptyVariables[mfqlObj.queryName][empty_var]

								for e in list_empty_vars:
									vars_plus_empty = vars
									vars_plus_empty[empty_var] = e

									if vars_plus_empty != {}:

										count += len(vars_plus_empty)

										mfqlObj.currVars = vars_plus_empty

										# filter with expressions evaluate()
										tmpRes = [vars_plus_empty, p[1].evaluate(
													scane = None,
													mode = 'sc',
													vars = vars_plus_empty,
													queryName = mfqlObj.queryName)]

										if tmpRes[1] != []:
											for key in list(vars_plus_empty.keys()):
												for se in vars_plus_empty[key].se:
													if se:
														se.isTakenBySuchthat = True
													else: # this is a virtual SurveyEntry
														artSE = SurveyEntry(
															msmass = vars_plus_empty[key].mass,
															smpl = key,
															peaks = [],
															charge = 0,
															polarity = 0,
															dictScans = {},
															dictBasePeakIntensity = {})
														artSE.isTakenBySuchthat = True
														vars_plus_empty[key].se = artSE

												if vars_plus_empty[key].msmse:
													vars_plus_empty[key].msmse.isTakenBySuchthat = True
											report.append(vars_plus_empty)

						else:

							if vars != {}:

								count += len(vars)

								mfqlObj.currVars = vars

								# filter with expressions evaluate()
								tmpRes = [vars, p[1].evaluate(
											scane = None,
											mode = 'sc',
											vars = vars,
											queryName = mfqlObj.queryName)]

								if tmpRes[1] != []:
									for key in list(vars.keys()):
										for se in vars[key].se:
											if se:
												se.isTakenBySuchthat = True
											else: # this is a virtual SurveyEntry
												artSE = SurveyEntry(
													msmass = vars[key].mass,
													smpl = key,
													peaks = [],
													charge = 0,
													polarity = 0,
													dictScans = {},
													dictBasePeakIntensity = {})
												artSE.isTakenBySuchthat = True
												vars[key].se = artSE

										if vars[key].msmse:
											vars[key].msmse.isTakenBySuchthat = True
									report.append(vars)

								#result.append(tmpRes)

		p[0] = report
		print("%.2f sec. for %d comparisons" % (time.clock(), count))

def p_booleanterm_logic(p):
	'''booleanterm : booleanterm AND booleanterm
				   | booleanterm OR  booleanterm'''

	p[0] = TypeBooleanTerm(
			sign = True,
			leftSide = p[1],
			rightSide = p[3],
			boolOp = p[2],
			mfqlObj = mfqlObj,
			environment = mfqlObj.queryName)

def p_booleanterm_brackets(p):
	'''booleanterm : LPAREN booleanterm RPAREN'''

	p[0] = TypeBooleanTerm(
			sign = True,
			rightSide = p[2],
			leftSide = None,
			boolOp = None,
			mfqlObj = mfqlObj,
			environment = mfqlObj.queryName)

def p_booleanterm_not(p):
	'''booleanterm : NOT booleanterm'''

	p[0] = TypeBooleanTerm(
			sign = False,
			rightSide = p[2],
			leftSide = None,
			boolOp = None,
			mfqlObj = mfqlObj,
			environment = mfqlObj.queryName)

def p_booleanterm_expr(p):
	'''booleanterm : expr'''

	p[0] = TypeBooleanTerm(
			sign = True,
			rightSide = p[1],
			leftSide = None,
			boolOp = None,
			mfqlObj = mfqlObj,
			environment = mfqlObj.queryName)

def p_booleanterm_expression(p):
	'''booleanterm : object'''

	p[0] = TypeBooleanTerm(
			sign = True,
			rightSide = p[1],
			leftSide = None,
			boolOp = None,
			mfqlObj = mfqlObj,
			environment = mfqlObj.queryName)

def p_expr_multi(p):
	'''expr : expression EQUALS expression options
			| expression GT expression options
			| expression GE expression options
			| expression LE expression options
			| expression LT expression options
			| expression NE expression options
			| expression ARROWR expression options '''

	p[0] = TypeExpr(
				leftSide = p[1],
				cmpOp = p[2],
				rightSide = p[3],
				mfqlObj = mfqlObj,
				options = p[4],
				environment = mfqlObj.queryName)

def p_expression_struct(p):
	'''expression : expression PLUS expression
				  | expression MINUS expression
				  | expression TIMES expression
				  | expression DIVIDE expression
				  | MINUS expression %prec UMINUS'''

	p[0] = TypeExpression(
				isSingleton = False,
				leftSide = p[1],
				operator = p[2],
				rightSide = p[3],
				mfqlObj = mfqlObj,
				environment = mfqlObj.queryName)

#	p[0].evaluate()

	pass

def p_expression_attribute(p):
	'''expression : LPAREN expression RPAREN LBRACE ID RBRACE'''

	p[0] = TypeExpression(
				isSingleton = True,
				leftSide = None,
				operator = None,
				rightSide = p[2],
				mfqlObj = mfqlObj,
				environment = mfqlObj.queryName,
				item = p[5])
	#p[0] = p[2]

def p_expression_paren(p):
	'''expression : LPAREN expression RPAREN'''
	p[0] = p[2]

def p_expression_content(p):
	'''expression : object'''

	if isinstance(p[1], TypeVariable):
		if p[1].variable:
			p[0] = p[1]

	elif isinstance(p[1], TypeFunction):
		p[0] = p[1]
	else:
		p[0] = p[1]



### SCAN ###

def p_scan_object(p):
	'''scan : object IN scope options'''

	if not isinstance(p[1], TypeVariable):
		raise LipidXException

	if p[1].variable:
		v = mfqlObj.queryName + mfqlObj.namespaceConnector + p[1].variable

	# set the variable
	try:
		mfqlObj.dictDefinitionTable[mfqlObj.queryName][v].name = v
	except KeyError:
		raise SyntaxErrorException(
				"Variable \"%s\" in query \"%s\" does not exist." % (p[1].variable, mfqlObj.queryName),
				mfqlObj.filename,
				0)

	if isinstance(mfqlObj.dictDefinitionTable[mfqlObj.queryName][v], TypeList):
		mfqlObj.dictDefinitionTable[mfqlObj.queryName][v].nameList()

	mfqlObj.dictDefinitionTable[mfqlObj.queryName][v].scope = p[3]

	mfqlObj.dictScanTable[v] = p[3]

	if p[4]:
		for o in p[4]:
			mfqlObj.dictDefinitionTable[mfqlObj.queryName][v].options[o[0]] = o[1]

	### read massrange from sc-constraint ###
	if isinstance(mfqlObj.dictDefinitionTable[mfqlObj.queryName][v], TypeSFConstraint):

		scConst = mfqlObj.dictDefinitionTable[mfqlObj.queryName][v].elementSequence

		if scConst:
			if p[3] == 'MS1+' or p[3] == 'MS1-':
				massrange = scConst.getMassRange()
				mfqlObj.dictDefinitionTable[mfqlObj.queryName][v].options['massrange'] = massrange

			elif p[3] == 'MS2+' and mfqlObj.dictDefinitionTable[mfqlObj.queryName][v].elementSequence.polarity == 1:
				massrange = scConst.getMassRange()
				mfqlObj.dictDefinitionTable[mfqlObj.queryName][v].options['massrange'] = massrange

			elif p[3] == 'MS2-' and mfqlObj.dictDefinitionTable[mfqlObj.queryName][v].elementSequence.polarity == -1:
				massrange = scConst.getMassRange()
				mfqlObj.dictDefinitionTable[mfqlObj.queryName][v].options['massrange'] = massrange

	elif isinstance(mfqlObj.dictDefinitionTable[mfqlObj.queryName][v], TypeFloat):
		pass

	### check for the tolerance settings ###
	if not 'tolerance' in mfqlObj.dictDefinitionTable[mfqlObj.queryName][v].options:
		if p[3] == "MS1+" or p[3] == "MS1-":
			mfqlObj.precursor = mfqlObj.dictDefinitionTable[mfqlObj.queryName][v]
		if p[3] == "MS2+" or p[3] == "MS2-":
			pass

	p[0] = mfqlObj.dictDefinitionTable[mfqlObj.queryName][v]

def p_scope(p):
	'''scope : MS1 MINUS
			 | MS1 PLUS
			 | MS2 PLUS
			 | MS2 MINUS'''

	p[0] = p[1] + p[2]

def p_report(p):
	'''report : reportContent'''
	p[0] = p[1]

def p_reportContent_cont(p):
	'''reportContent : reportContent rContent'''
	p[0] = p[1]
	p[0].append(p[2])

def p_reportContent_single(p):
	'''reportContent : rContent'''
	p[0] = [p[1]]

def p_rContent(p):
	'''rContent : ID IS STRING PERCENT STRING SEMICOLON
				| ID IS STRING PERCENT LPAREN arguments RPAREN SEMICOLON
				| ID IS expression SEMICOLON'''

	if len(p) == 7:
		p[0] = (p[1], p[3], p[5])
	if len(p) == 9:
		p[0] = (p[1], p[3], p[6])
	if len(p) == 5:
		p[0] = (p[1], p[3])

def p_error(p):
	if not p:
		print("SYNTAX ERROR at EOF")
		raise SyntaxErrorException("SYNTAX ERROR at EOF")
	else:
		#print "SYNTAX ERROR at '%s' in line %d of file '%s' " % (p.value, p.lineno, mfqlObj.queryName)
		#detail = "Syntax error at '%s' in file '%s' in line '%d'" % (p.value, mfqlObj.filename, p.lexer.lineno)
		detail = "Syntax error at '%s' in file '%s'" % (p.value, mfqlObj.filename)
		raise SyntaxErrorException(detail,
				"",
				mfqlObj.filename,
				0)

parser = yacc.yacc(debug = 0, optimize = 0)
#bparser = yacc.yacc(method = 'LALR')

def startParsing(dictData, mfqlObjIn, ms, isotopicCorrectionMS, isotopicCorrectionMSMS,
		complementSC, parent, progressCount, generateStatistics, mode = ""):

	time.clock()

	global mfqlObj
	global gprogressCount
	global numQueries

	mfqlObj = mfqlObjIn
	mfqlObj.namespaceConnector = '_'
	gprogressCount = progressCount

	options = mfqlObj.options

	if mode == 'generateTargetList':

		###  ###
		for k in list(dictData.keys()):

			mfqlObj.filename = k
			numQueries = 0

			mfqlObj.parsePart = 'genTargetList'
			lexer.lineno = 1
			parser.parse(dictData[k], lexer = lexer, debug = 0)

			mfqlObj.reset()

		saveMasterScan(mfqlObj)

	### do the IDENTIFY(cation) ###
	for k in list(dictData.keys()):

		mfqlObj.filename = k
		numQueries = 0

		mfqlObj.parsePart = 'identification'
		lexer.lineno = 1
		parser.parse(dictData[k], lexer = lexer, debug = 0)

		mfqlObj.reset()

	if isotopicCorrectionMS:
		#mfqlObj.result.isotopicCorrectionMSMS()
		print("type II isotopic correction in MS ...", end=' ')
		mfqlObj.result.isotopicCorrectionMS()

		#gprogressCount += 1
		#if parent:
		#	(cont, skip) = parent.debug.progressDialog.Update(gprogressCount)
		#	if not cont:
		#		parent.debug.progressDialog.Destroy()
		#		return parent.CONST_THREAD_USER_ABORT

		print("%.2f sec." % time.clock())
	else:
		print("type II isotopic correction for MS is switched off")

	# testwise put it here before MS/MS correction, because MS/MS correction has to
	# note the change first
	print("generating result MasterScan ...", end=' ')
	mfqlObj.result.generateResultSC()
	print("%.2f sec." % time.clock())

	## debugging ###
	#for se in mfqlObj.result.mfqlObj.resultSC:
		#for msmse in se.listMSMS:
		#	print msmse.mass, msmse.listMark
		#	for mark in msmse.listMark:
		#		print mark.name, [x.precurmass for x in mark.se], mark.frsc, mark.nlsc
		#		print mark.intensity

	if isotopicCorrectionMSMS:
		print("type II isotopic correction in MS/MS ...", end=' ')
		mfqlObj.result.isotopicCorrectionMSMS()

		#gprogressCount += 1
		#if parent:
		#	(cont, skip) = parent.debug.progressDialog.Update(gprogressCount)
		#	if not cont:
		#		parent.debug.progressDialog.Destroy()
		#		return parent.CONST_THREAD_USER_ABORT

		print("%.2f sec." % time.clock())
	else:
		print("type II isotopic correction for MS/MS is switched off")

	if not Debug("noMonoisotopicCorrection"):
		print("type I isotopic correction in MS and MS/MS ...", end=' ')
		if isotopicCorrectionMS or isotopicCorrectionMSMS:
			mfqlObj.result.correctMonoisotopicPeaks()
		print("%.2f sec." % time.clock())

	if Debug("removeIsotopes"):# and (isotopicCorrectionMS or isotopicCorrectionMSMS):
		mfqlObj.result.removeIsotopicCorrected()

	print("generate query result MasterScans ...", end=' ')
	mfqlObj.result.generateQueryResultSC()
	print("%.2f sec." % time.clock())

	#for q in mfqlObj.result.dictQuery.keys():
	#	print ">>>", q
	#	for se in mfqlObj.result.dictQuery[q]:
	#		print ">>>", se
	#		for msmse in se.listMSMS:
	#			print ">>> >>>", len(msmse.listMark)

	# check for isobaric species
	print("checking if there are isobaric species ...", end=' ')
	mfqlObj.result.checkIsobaricSpeciesBeforeSUCHTHAT()
	print("%.2f sec." % time.clock())

	### do the REPORT ###
	for k in list(dictData.keys()):

		#log.setLevel(logging.INFO)
		#log.info("Processing %s", k, extra = func)

		mfqlObj.filename = k

		mfqlObj.parsePart = 'report'

		lexer.lineno = 1
		parser.parse(dictData[k], lexer = lexer, tracking = True)

	if complementSC:

		#mfqlObj.result.isotopicCorrectionMSMS()
		#print "de-isotoping MS ...",
		#mfqlObj.result.deIsotopingMS_complement()
		#print "%.2f sec." % time.clock()

		#print "de-isotoping MS ...",
		#mfqlObj.result.deIsotopingMSMS_complement()
		#print "%.2f sec." % time.clock()

		print("generate complement MasterScan ...")
		mfqlObj.result.generateComplementSC()
		print("%.2f sec." % time.clock())

	if options['noPermutations']:
		mfqlObj.result.removePermutations()

	## debugging ###
	#for se in mfqlObj.result.mfqlObj.resultSC:
	#	print ">>>", se
	#	for msmse in se.listMSMS:
	#		print msmse.mass, msmse.listMark
	#		for mark in msmse.listMark:
	#			print mark.name, [x.precurmass for x in mark.se], mark.frsc, mark.nlsc
	#			print mark.intensity

	print("checking if there are still isobaric species ...", end=' ')
	mfqlObj.result.checkIsobaricSpeciesAfterSUCHTHAT()
	print("%.2f sec." % time.clock())

	print("generate report ...", end=' ')
	mfqlObj.result.generateReport(options)
	print("%.2f sec." % time.clock())

	if generateStatistics and mfqlObj.result.mfqlOutput:
		print("generate statistics ...", end=' ')
		mfqlObj.result.generateStatistics(options)
		print("%.2f sec." % time.clock())

	#print "generate graphics ...",
	#mfqlObj.result.generateGraphics()
	#print "%.2f sec." % time.clock()

		#if yacc.error:
		#	print "ERROR", yacc.error
		#	return None

	del gprogressCount

	gprogressCount = 0
	if parent:
		return (gprogressCount, parent.CONST_THREAD_SUCCESSFUL)
	else:
		return (gprogressCount, None)

