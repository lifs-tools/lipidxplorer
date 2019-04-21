import ply.yacc as yacc
from mfql_lexer import tokens

mfql_dict = {}

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
import ply.yacc as yacc
from mfql_lexer import tokens

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
    raise NotImplementedError('not implemented')

def p_program_single(p):
	'''program  : script SEMICOLON'''
    print(' its done this is why he needs an extra semicoloni, maybe compare p[1] to mfql_dict')
    print(mfql_dict == p[1])
    p[0] = p[1]

def p_script(p):
	'''script  : scriptname variables identification
			   | identification'''
    raise NotImplementedError('not implemented')


def p_script_error(p):
	'''script : error variables identification'''
	raise SyntaxError"SYNTAX ERROR: 'QUERYNAME' is missing"

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
		print "generating combinatorics ...",
		for se in mfqlObj.sc.listSurveyEntry:
			mfqlObj.genVariables_new(se, mfqlObj.dictEmptyVariables)
		print "%.2f sec." % time.clock()

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
		print "generating combinatorics ...",
		for se in mfqlObj.sc.listSurveyEntry:
			mfqlObj.genVariables_new(se, mfqlObj.dictEmptyVariables)
		print "%.2f sec." % time.clock()

	if mfqlObj.parsePart == 'identification':
		print "generating combinatorics ...",
		for se in mfqlObj.sc.listSurveyEntry:
			mfqlObj.genVariables_new(se, mfqlObj.dictEmptyVariables)
		print "%.2f sec." % time.clock()


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
			for i in mfqlObj.dictDefinitionTable[mfqlObj.queryName].keys():
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
		print "IDENTIFY the masses of interest ...",
		mfqlObj.scan.evaluate()
		print "%.2f sec." % time.clock()
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

		print "testing constraints of SUCHTHAT ...",
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
					for key in vars.keys():
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
											for key in vars_plus_empty.keys():
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
									for key in vars.keys():
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
		print "%.2f sec. for %d comparisons" % (time.clock(), count)

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
		print "SYNTAX ERROR at EOF"
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

if __name__ == '__main__':
    mfql = '''
    ##########################################################
    # Identify PC SPCCIES #
    ##########################################################

    QUERYNAME = PCFAS;
        DEFINE pr = 'C[30..80] H[40..300] O[10] N[1] P[1]' WITH DBR = (2.5,14.5), CHG = -1;
        DEFINE FA1 = 'C[10..40] H[20..100] O[2]' WITH DBR = (1.5,7.5), CHG = -1;
        DEFINE FA2 ='C[10..40] H[20..100] O[2]' WITH DBR = (1.5,7.5), CHG = -1;

    IDENTIFY
        pr IN MS1- AND
        FA1 IN MS2- AND
        FA2 IN MS2-

    SUCHTHAT
        isOdd(pr.chemsc[H]) AND
        isOdd(pr.chemsc[db]*2) AND
        FA1.chemsc + FA2.chemsc + 'C9 H19 N1 O6 P1' == pr.chemsc

    REPORT
        PRM = pr.mass;
        EC = pr.chemsc;
        CLASS = "PC" % "()";

        PRC = "%d" % "((pr.chemsc)[C] - 9)";
        PRDB = "%d" % "((pr.chemsc)[db] - 2.5)";
        PROH = "%d" % "((pr.chemsc)[O] - 10)";
        SPECIE = "PC %d:%d:%d" % "((pr.chemsc)[C]-9, pr.chemsc[db] - 2.5, pr.chemsc[O]-10)";

            PRERR = "%2.2f" % "(pr.errppm)";
        PRI = pr.intensity;

        FA1M = FA2.mass; 
        FA1C = "%d" % "((FA2.chemsc)[C])";
        FA1DB = "%d" % "((FA2.chemsc)[db] - 1.5)"; 
            FA1ERR = "%2.2f" % "(FA2.errppm)";
        FA1I = FA2.intensity;

        FA2M = FA1.mass; 
        FA2C = "%d" % "((FA1.chemsc)[C])";
        FA2DB = "%d" % "((FA1.chemsc)[db] - 1.5)"; 
            FA2ERR = "%2.2f" % "(FA1.errppm)";
        FA2I = FA1.intensity;
        ; 

    ################ end script ##################

    '''

    result = parser.parse(mfql)
    print(result)

# def p_program_multi(p):
#     '''program  : program script SEMICOLON''' #todo remove this step

def p_program_single(p):
    '''program  : script SEMICOLON'''
    print(' done....he needs an extra semicoloni, maybe compare p[1] to mfql_dict' )
    print(mfql_dict == p[1])
    p[0] = p[1]

# def p_script(p):
#     '''script  : scriptname variables identification
#                | identification'''


# def p_script_error(p):
#     '''script : error variables identification'''
#     print "SYNTAX ERROR: 'QUERYNAME' is missing"


### VARIABLES ###

def p_scriptname(p):
    '''scriptname : QUERYNAME IS getQueryName SEMICOLON'''
    p[0] = p[3]

def p_getQueryName(p):
    '''getQueryName : ID'''
    mfql_dict['queryName'] = p[1]

def p_variables_loop(p):
    '''variables : variables var'''
    p[0] = p[1] + [p[2]]

def p_variables_endloop(p):
    '''variables : var'''
    p[0] = [p[1]]


def p_var_normal(p):
    '''var : DEFINE ID IS object options SEMICOLON
            | DEFINE ID IS object options AS NEUTRALLOSS SEMICOLON'''


def p_var_emptyVar(p):
    '''var : DEFINE ID options SEMICOLON'''

    if len(p) == 5 and p[3] != None:
        o = TypeSFConstraint(elementSequence=ElementSequence())
        o.addOptions(p[3])
    else:
        o = TypeSFConstraint(elementSequence=None)

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
    p[0] = TypeVariable(variable=p[1], item=p[3])
    mfqlObj.listDataTable.append(p[0])


def p_onlyObj_ID(p):
    '''onlyObj : ID'''
    p[0] = TypeVariable(variable=p[1])
    mfqlObj.listDataTable.append(p[0])


def p_onlyObj_list(p):
    '''onlyObj : list'''
    p[0] = TypeList(list=p[1])


def p_onlyObj_varcontent(p):
    '''onlyObj : varcontent'''
    p[0] = p[1]


def p_onlyObj_function1(p):
    '''onlyObj : ID LPAREN arguments RPAREN LBRACE ID RBRACE'''
    p[0] = TypeFunction(name=p[1], arguments=p[3], mfqlObj=mfqlObj, item=p[6])
    mfqlObj.listDataTable.append(p[1])


def p_onlyObj_function2(p):
    '''onlyObj : ID LPAREN arguments RPAREN'''
    p[0] = TypeFunction(name=p[1], arguments=p[3], mfqlObj=mfqlObj)
    mfqlObj.listDataTable.append(p[1])


def p_withAttr_accessItem_(p):
    '''withAttr : ID DOT ID LBRACE ID RBRACE'''
    # p[0] = TypeItem(variable = p[1], attribute = p[3], item = p[5])
    p[0] = TypeVariable(variable=p[1], attribute=p[3], item=p[5])
    mfqlObj.listDataTable.append(p[0])


def p_withAttr_accessItem_string(p):
    '''withAttr : ID DOT ID LBRACE STRING RBRACE'''
    # p[0] = TypeItem(variable = p[1], attribute = p[3], item = p[5])
    p[0] = TypeVariable(variable=p[1], attribute=p[3], item=p[5])
    mfqlObj.listDataTable.append(p[0])


def p_withAttr_id(p):
    '''withAttr : ID DOT ID'''
    #	p[0] = TypeAttribute(
    #		variable = mfqlObj.dictDefinitionTable[p[1]],
    #		attribute = p[3])
    p[0] = TypeVariable(variable=p[1], attribute=p[3])

    mfqlObj.listDataTable.append(p[0])


def p_withAttr_varcontent(p):
    '''withAttr : varcontent DOT ID'''
    # p[0] = TypeAttribute(mass = p[1], attribute = p[3])
    p[0] = TypeVariable(variable=p[1], attribute=p[3])

    mfqlObj.listDataTable.append(p[0])


def p_withAttr_list(p):
    '''withAttr : list DOT ID'''
    p[0] = TypeAttribute(sequence=p[1], attribute=p[3])

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
    # '''list : LPAREN listcontent RPAREN'''

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


# p[0] = TypeFloat(float = float(p[1]), mass = float(p[1]))

# def p_varcontent_negfloat(p):
#	'''varcontent : MINUS FLOAT'''
#
#	p[0] = TypeFloat(float = -float(p[1]), mass = -float(p[1]))

def p_varcontent_integer(p):
    '''varcontent : INTEGER
                  | PLUS INTEGER
                  | MINUS INTEGER'''

    if len(p) == 2:
        p[0] = TypeFloat(float=float(p[1]), mass=float(p[1]))
    else:
        if p[1] == 'PLUS':
            p[0] = TypeFloat(float=float(p[2]), mass=float(p[2]))
        else:
            p[0] = TypeFloat(float=-float(p[2]), mass=-float(p[2]))


# def p_varcontent_signedInteger(p):
#	'''varcontent : MINUS INTEGER'''
#
#	p[0] = TypeFloat(float = -float(p[2]), mass = -float(p[2]))

def p_varcontent_string(p):
    '''varcontent : STRING'''

    p[0] = TypeString(string=p[1].strip('"'))


# p[0] = TypeMassList(file = p[1].strip('"'))

def p_varcontent_sfstring(p):
    '''varcontent : SFSTRING'''


# es = parseElemSeq(p[1].strip('\''))
# if isinstance(es, SCConstraint):
# 	p[0] = TypeSFConstraint(elementSequence = es)
# else:
# 	p[0] = TypeElementSequence(elementSequence = es, options = {})

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
            "Tolerance value as given in the query '%s' can not be smaller" % mfqlObj.queryName + \
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
        print "generating combinatorics ...",
        for se in mfqlObj.sc.listSurveyEntry:
            mfqlObj.genVariables_new(se, mfqlObj.dictEmptyVariables)
        print "%.2f sec." % time.clock()

    if len(p) == 8:

        mfqlObj.suchthatApplied = False
        if mfqlObj.parsePart == 'identification':
            query = TypeQuery(mfqlObj=mfqlObj,
                              id=mfqlObj.queryName,
                              report=p[7],
                              withSuchthat=False)

            mfqlObj.result.dictQuery[mfqlObj.queryName] = query

    if len(p) == 9:

        mfqlObj.suchthatApplied = True
        if mfqlObj.parsePart == 'identification':
            query = TypeQuery(mfqlObj=mfqlObj,
                              id=mfqlObj.queryName,
                              report=p[8],
                              withSuchthat=True)

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
        print "generating combinatorics ...",
        for se in mfqlObj.sc.listSurveyEntry:
            mfqlObj.genVariables_new(se, mfqlObj.dictEmptyVariables)
        print "%.2f sec." % time.clock()

    if mfqlObj.parsePart == 'identification':
        print "generating combinatorics ...",
        for se in mfqlObj.sc.listSurveyEntry:
            mfqlObj.genVariables_new(se, mfqlObj.dictEmptyVariables)
        print "%.2f sec." % time.clock()

    if len(p) == 6:

        mfqlObj.suchthatApplied = False
        if mfqlObj.parsePart == 'identification':
            query = TypeQuery(mfqlObj=mfqlObj,
                              id=mfqlObj.queryName,
                              report=p[5])

            mfqlObj.result.dictQuery[mfqlObj.queryName] = query

    if len(p) == 7:

        mfqlObj.suchthatApplied = True
        if mfqlObj.parsePart == 'identification':
            query = TypeQuery(mfqlObj=mfqlObj,
                              id=mfqlObj.queryName,
                              report=p[6])

            mfqlObj.result.dictQuery[mfqlObj.queryName] = query

        if mfqlObj.parsePart == 'report':
            mfqlObj.result.dictQuery[mfqlObj.queryName].listVariables = p[4]


def p_tagname(p):
    '''tagname : ID'''

    # mfqlObj.queryName = p[1]

    # if mfqlObj.parsePart == 'identification':
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
            for i in mfqlObj.dictDefinitionTable[mfqlObj.queryName].keys():
                if not i in [x.name for x in p[1].list()]:
                    name = i.split(mfqlObj.namespaceConnector)
                    raise SyntaxErrorException("The variable '%s' in query '%s'has to be used in IDENTIFY" % \
                                               (name[1], name[0]),
                                               name[0],
                                               0)
        # mfqlObj.addEmptyVariable(i,
        # mfqlObj.dictDefinitionTable[mfqlObj.queryName][i])


# mfqlObj.scan.scanTerm = p[1]

def p_booleanterm_paren(p):
    '''boolmarks : LPAREN boolmarks RPAREN'''
    p[0] = TypeMarkTerm(
        rightSide=p[2],
        leftSide=None,
        boolOp=None,
        mfqlObj=mfqlObj)


def p_boolmarks_not(p):
    '''boolmarks : NOT boolmarks'''

    p[0] = TypeMarkTerm(
        rightSide=p[2],
        leftSide=None,
        boolOp='NOT',
        mfqlObj=mfqlObj)


def p_boolmarks_or(p):
    '''boolmarks : boolmarks OR boolmarks'''

    p[0] = TypeMarkTerm(
        leftSide=p[1],
        rightSide=p[3],
        boolOp=p[2],
        mfqlObj=mfqlObj)


def p_boolmarks_and(p):
    '''boolmarks : boolmarks AND boolmarks'''

    p[0] = TypeMarkTerm(
        leftSide=p[1],
        rightSide=p[3],
        boolOp=p[2],
        mfqlObj=mfqlObj)


#	p[0] = ('and', p[1], p[3])

def p_boolmarks_if(p):
    '''boolmarks : boolmarks IFA boolmarks'''

    p[0] = TypeMarkTerm(
        leftSide=p[1],
        rightSide=p[3],
        boolOp=p[2],
        mfqlObj=mfqlObj)


#	p[0] = ('if', p[1], p[3])

def p_boolmarks_onlyif(p):
    '''boolmarks : boolmarks IFF boolmarks'''

    p[0] = TypeMarkTerm(
        leftSide=p[1],
        rightSide=p[3],
        boolOp=p[2],
        mfqlObj=mfqlObj)


#	p[0] = ('iff', p[1], p[3])

def p_boolmarks_arrow(p):
    '''boolmarks : boolmarks ARROW boolmarks'''

    p[0] = TypeMarkTerm(
        leftSide=p[1],
        rightSide=p[3],
        boolOp=p[2],
        mfqlObj=mfqlObj)


#	p[0] = ('iff', p[1], p[3])

def p_boolmarks_le(p):
    '''boolmarks : boolmarks LE boolmarks'''

    p[0] = TypeMarkTerm(
        leftSide=p[1],
        rightSide=p[3],
        boolOp=p[2],
        mfqlObj=mfqlObj)


#	p[0] = ('iff', p[1], p[3])

def p_boolmarks_toScan(p):
    '''boolmarks : scan'''

    p[0] = TypeMarkTerm(
        rightSide=p[1],
        leftSide=None,
        boolOp=None,
        mfqlObj=mfqlObj)


def p_evalMarks(p):
    '''evalMarks : '''
    if mfqlObj.parsePart == 'identification':
        print "IDENTIFY the masses of interest ...",
        mfqlObj.scan.evaluate()
        print "%.2f sec." % time.clock()
    pass


def p_suchthat_single(p):
    '''suchthat : SUCHTHAT body'''
    p[0] = p[2]


# def p_suchthat_multi(p):
#	'''suchthat : LPAREN suchthat RPAREN suchthat'''

def p_body_bool(p):
    '''body : bterm'''
    p[0] = p[1]


def p_bterm(p):
    '''bterm : booleanterm'''

    report = []

    # apply SUCHTHAT filter if vars were found
    if mfqlObj.parsePart == 'report':

        print "testing constraints of SUCHTHAT ...",
        report = []
        count = 0
        for se in mfqlObj.result[mfqlObj.queryName].sc:

            if se.listVariables != []:

                ### add the empty variables to the 'normal'
                # listVariables = []
                # for empty_var in mfqlObj.dictEmptyVariables[mfqlObj.queryName]:
                #	listVariables.append([empty_var])

                for vars in se.listVariables:  # + mfqlObj.dictEmptyVariables[mfqlObj.queryName]:

                    # check if the variable of se contain at least one coming from the current query
                    isIn = False
                    for key in vars.keys():
                        if mfqlObj.queryName == key.split(mfqlObj.namespaceConnector)[0]:
                            isIn = True
                            break

                    if isIn:

                        # add the empty vars to the list of variables
                        # if mfqlObj.dictEmptyVariables.has_key(mfqlObj.queryName):
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
                                            scane=None,
                                            mode='sc',
                                            vars=vars_plus_empty,
                                            queryName=mfqlObj.queryName)]

                                        if tmpRes[1] != []:
                                            for key in vars_plus_empty.keys():
                                                for se in vars_plus_empty[key].se:
                                                    if se:
                                                        se.isTakenBySuchthat = True
                                                    else:  # this is a virtual SurveyEntry
                                                        artSE = SurveyEntry(
                                                            msmass=vars_plus_empty[key].mass,
                                                            smpl=key,
                                                            peaks=[],
                                                            charge=0,
                                                            polarity=0,
                                                            dictScans={},
                                                            dictBasePeakIntensity={})
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
                                    scane=None,
                                    mode='sc',
                                    vars=vars,
                                    queryName=mfqlObj.queryName)]

                                if tmpRes[1] != []:
                                    for key in vars.keys():
                                        for se in vars[key].se:
                                            if se:
                                                se.isTakenBySuchthat = True
                                            else:  # this is a virtual SurveyEntry
                                                artSE = SurveyEntry(
                                                    msmass=vars[key].mass,
                                                    smpl=key,
                                                    peaks=[],
                                                    charge=0,
                                                    polarity=0,
                                                    dictScans={},
                                                    dictBasePeakIntensity={})
                                                artSE.isTakenBySuchthat = True
                                                vars[key].se = artSE

                                        if vars[key].msmse:
                                            vars[key].msmse.isTakenBySuchthat = True
                                    report.append(vars)

            # result.append(tmpRes)

        p[0] = report
        print "%.2f sec. for %d comparisons" % (time.clock(), count)


def p_booleanterm_logic(p):
    '''booleanterm : booleanterm AND booleanterm
                   | booleanterm OR  booleanterm'''

    p[0] = TypeBooleanTerm(
        sign=True,
        leftSide=p[1],
        rightSide=p[3],
        boolOp=p[2],
        mfqlObj=mfqlObj,
        environment=mfqlObj.queryName)


def p_booleanterm_brackets(p):
    '''booleanterm : LPAREN booleanterm RPAREN'''

    p[0] = TypeBooleanTerm(
        sign=True,
        rightSide=p[2],
        leftSide=None,
        boolOp=None,
        mfqlObj=mfqlObj,
        environment=mfqlObj.queryName)


def p_booleanterm_not(p):
    '''booleanterm : NOT booleanterm'''

    p[0] = TypeBooleanTerm(
        sign=False,
        rightSide=p[2],
        leftSide=None,
        boolOp=None,
        mfqlObj=mfqlObj,
        environment=mfqlObj.queryName)


def p_booleanterm_expr(p):
    '''booleanterm : expr'''

    p[0] = TypeBooleanTerm(
        sign=True,
        rightSide=p[1],
        leftSide=None,
        boolOp=None,
        mfqlObj=mfqlObj,
        environment=mfqlObj.queryName)


def p_booleanterm_expression(p):
    '''booleanterm : object'''

    p[0] = TypeBooleanTerm(
        sign=True,
        rightSide=p[1],
        leftSide=None,
        boolOp=None,
        mfqlObj=mfqlObj,
        environment=mfqlObj.queryName)


def p_expr_multi(p):
    '''expr : expression EQUALS expression options
            | expression GT expression options
            | expression GE expression options
            | expression LE expression options
            | expression LT expression options
            | expression NE expression options
            | expression ARROWR expression options '''

    p[0] = TypeExpr(
        leftSide=p[1],
        cmpOp=p[2],
        rightSide=p[3],
        mfqlObj=mfqlObj,
        options=p[4],
        environment=mfqlObj.queryName)


def p_expression_struct(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | MINUS expression %prec UMINUS'''

    p[0] = TypeExpression(
        isSingleton=False,
        leftSide=p[1],
        operator=p[2],
        rightSide=p[3],
        mfqlObj=mfqlObj,
        environment=mfqlObj.queryName)

    #	p[0].evaluate()

    pass


def p_expression_attribute(p):
    '''expression : LPAREN expression RPAREN LBRACE ID RBRACE'''

    p[0] = TypeExpression(
        isSingleton=True,
        leftSide=None,
        operator=None,
        rightSide=p[2],
        mfqlObj=mfqlObj,
        environment=mfqlObj.queryName,
        item=p[5])


# p[0] = p[2]

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
        print "SYNTAX ERROR at EOF"
        raise SyntaxErrorException("SYNTAX ERROR at EOF")
    else:
        # print "SYNTAX ERROR at '%s' in line %d of file '%s' " % (p.value, p.lineno, mfqlObj.queryName)
        # detail = "Syntax error at '%s' in file '%s' in line '%d'" % (p.value, mfqlObj.filename, p.lexer.lineno)
        detail = "Syntax error at '%s' in file '%s'" % (p.value, mfqlObj.filename)
        raise SyntaxErrorException(detail,
                                   "",
                                   mfqlObj.filename,
                                   0)


parser = yacc.yacc(debug=0, optimize=0)
# bparser = yacc.yacc(method = 'LALR')

if __name__ == '__main__':
    mfql = '''
    ##########################################################
    # Identify PC SPCCIES #
    ##########################################################

    QUERYNAME = PCFAS;
        DEFINE pr = 'C[30..80] H[40..300] O[10] N[1] P[1]' WITH DBR = (2.5,14.5), CHG = -1;
        DEFINE FA1 = 'C[10..40] H[20..100] O[2]' WITH DBR = (1.5,7.5), CHG = -1;
        DEFINE FA2 ='C[10..40] H[20..100] O[2]' WITH DBR = (1.5,7.5), CHG = -1;

    IDENTIFY
        pr IN MS1- AND
        FA1 IN MS2- AND
        FA2 IN MS2-

    SUCHTHAT
        isOdd(pr.chemsc[H]) AND
        isOdd(pr.chemsc[db]*2) AND
        FA1.chemsc + FA2.chemsc + 'C9 H19 N1 O6 P1' == pr.chemsc

    REPORT
        PRM = pr.mass;
        EC = pr.chemsc;
        CLASS = "PC" % "()";

        PRC = "%d" % "((pr.chemsc)[C] - 9)";
        PRDB = "%d" % "((pr.chemsc)[db] - 2.5)";
        PROH = "%d" % "((pr.chemsc)[O] - 10)";
        SPECIE = "PC %d:%d:%d" % "((pr.chemsc)[C]-9, pr.chemsc[db] - 2.5, pr.chemsc[O]-10)";

            PRERR = "%2.2f" % "(pr.errppm)";
        PRI = pr.intensity;

        FA1M = FA2.mass; 
        FA1C = "%d" % "((FA2.chemsc)[C])";
        FA1DB = "%d" % "((FA2.chemsc)[db] - 1.5)"; 
            FA1ERR = "%2.2f" % "(FA2.errppm)";
        FA1I = FA2.intensity;

        FA2M = FA1.mass; 
        FA2C = "%d" % "((FA1.chemsc)[C])";
        FA2DB = "%d" % "((FA1.chemsc)[db] - 1.5)"; 
            FA2ERR = "%2.2f" % "(FA1.errppm)";
        FA2I = FA1.intensity;
        ; 

    ################ end script ##################

    '''

    result = parser.parse(mfql)
    print(result)
