#!/usr/bin/python

import os, sys
#sys.path.append('../lib')
#sys.path.insert(0,'../..')

from . import ply.lex as lex
from lx.exceptions import SyntaxErrorException
from .chemParser import parseElemSeq
import time

keywords = (
	'IDENTIFY', 'WITH', 'WHERE', 'AND', 'OR', 'NO',
	'TOLERANCE', 'MINOCC', 'MAXOCC', 'MASSRANGE', 'DBR', 'CHG',
	'NOT', 'DA', 'PPM', 'RES', 'DEFINE', 'IN', 'MS1', 'MS2',
	'RETENTIONTIME', 'REPORT', 'SUCHTHAT',
	'FOR', 'CROSSPROD', 'EVERY', 'PRECURSOR', 'OF', 'CHECK', 'IF',
	'QUERYNAME', 'INTERPRETATION', 'AS', 'NEUTRALLOSS'
)

# list of token names
tokens = keywords + (
	'EQUALS', 'IS', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'LPAREN',
	'RPAREN', 'LT', 'LE', 'GT', 'GE', 'IFA', 'IFF', 'NE', 'UPARROW', 'COMMA', 'SEMICOLON',
	'FLOAT', 'STRING', 'ID', 'INTEGER', 'DOT', 'PERCENT', 'LBRACE',
	'RBRACE', 'LBRACKET', 'RBRACKET', 'SFSTRING', 'ARROW'
)

# ignoring characters (space and tab)
#t_ignore_WHITESPACE = r'\s'
#t_ignore_TAB = r'\t'
#t_ignore_COMMENT = r'\#.*'


def t_COMMENT(t):
	r'\#.*'
	pass

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
t_UPARROW = r'\^'
t_ARROW   = r'->'
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
t_ignore = '\t'

def t_NEWLINE(t):
	r'\n'
	t.lexer.lineno += 1

def t_error(t):
#	print "Illegal character", t.value[0]
	t.lexer.skip(1)

# build lexer
import re
lexer = lex.lex(reflags = re.I, debug = 0, optimize = 0)


###############################################################################
########################### Parser starts here ################################
###############################################################################

from . import ply.yacc as yacc

# for the testing: the first semantics

# current scope
namespace = {}
scanResults = {}

# name of the identification
strIdentification = ''

# options 
optionsDBR = []
optionsCHG = 0
optionsMASSRANGE = []
optionsMINOCC = 0.0
optionsRETENTIONTIME = 0.0
optionsTOLERANCE = None

globalPrecursor = {}
programMode = ''

precedence = (
	('nonassoc', 'LT', 'GT', 'GE', 'LE'),
	('left', 'OR'),
	('left', 'AND', 'IFF', 'ARROW', 'CROSSPROD'),
	('left', 'NOT'),
	('left', 'PLUS', 'MINUS'),
	('left', 'TIMES', 'DIVIDE')
#	('right', 'UMINUS')
	)

### PROGRAMM ###

def p_program_multi(p):
	'''program  : program script SEMICOLON'''


def p_program_single(p):
	'''program  : script SEMICOLON'''

def p_script(p):
	'''script  : scriptname variables identification
			   | identification'''

	global numQueries
	numQueries += 1


def p_script_error(p):
	'''script : error variables identification'''
	print("SYNTAX ERROR: 'QUERYNAME' is missing")


### VARIABLES ###

def p_scriptname(p):
	'''scriptname : QUERYNAME IS getQueryName SEMICOLON'''

def p_getQueryName(p):
	'''getQueryName : ID'''

	global listQueryNames
	if p[1] in listQueryNames:
		raise SyntaxErrorException("A double query name ('%s') occured. This must not be!" % p[1], mfqlObj.filename, mfqlObj.queryName, p.lexer.lineno)
	else:
		listQueryNames.append(p[1])
	mfqlObj.queryName = p[1]

def p_variables_loop(p):
	'''variables : variables var'''

def p_variables_endloop(p):
	'''variables : var'''

def p_var_normal(p):
	'''var : DEFINE ID IS object options SEMICOLON
			| DEFINE ID IS object options AS NEUTRALLOSS SEMICOLON'''

def p_var_list(p):
	'''var : DEFINE list IS object options SEMICOLON'''

def p_var_emptyVar(p):
	'''var : DEFINE ID options SEMICOLON'''

def p_object_withAttr(p):
	'''object : withAttr'''

def p_object_onlyObj(p):
	'''object : onlyObj'''


### OBJECT/VARCONTENT ###

def p_onlyObj_ID_itemAccess(p):
	'''onlyObj : ID LBRACE ID RBRACE'''

def p_onlyObj_ID(p):
	'''onlyObj : ID'''

def p_onlyObj_list(p):
	'''onlyObj : list'''

def p_onlyObj_varcontent(p):
	'''onlyObj : varcontent'''

def p_onlyObj_function1(p):
	'''onlyObj : ID LPAREN arguments RPAREN LBRACE ID RBRACE'''

def p_onlyObj_function2(p):
	'''onlyObj : ID LPAREN arguments RPAREN'''

def p_withAttr_accessItem_(p):
	'''withAttr : ID DOT ID LBRACE ID RBRACE'''

def p_withAttr_accessItem_string(p):
	'''withAttr : ID DOT ID LBRACE STRING RBRACE'''

def p_withAttr_id(p):
	'''withAttr : ID DOT ID'''

def p_withAttr_varcontent(p):
	'''withAttr : varcontent DOT ID'''

def p_withAttr_list(p):
	'''withAttr : list DOT ID'''

def p_arguments_single(p):
	'''arguments : expression'''

def p_arguments_multi(p):
	'''arguments : arguments COMMA expression'''

def p_list(p):
	'''list : LBRACKET listcontent RBRACKET'''

def p_listcontent_cont(p):
	'''listcontent : listcontent COMMA object'''

def p_listcontent_obj(p):
	'''listcontent : object'''

def p_varcontent_tolerance(p):
	'''varcontent : tolerancetype'''

def p_varcontent_float(p):
	'''varcontent : FLOAT'''

def p_varcontent_integer(p):
	'''varcontent : INTEGER
				  | PLUS INTEGER'''
	
def p_varcontent_signedInteger(p):
	'''varcontent : MINUS INTEGER'''
	
def p_varcontent_string(p):
	'''varcontent : STRING'''

def p_varcontent_sfstring(p):
	'''varcontent : SFSTRING'''
#	try:
#		es = lpdxParser.parseElemSeq(p[1].strip('\''))
#	except SyntaxErrorException as e:
#		raise lpdxUIExceptions.SyntaxErrorException(e.p_value, mfqlObj.filename, mfqlObj.queryName, p.lexer.lineno)
	es = parseElemSeq(p[1].strip('\''))

def p_options_there(p):
	'''options : WITH optioncontent'''

def p_options_not_there(p):
	'''options :'''

def p_optioncontent_cont(p):
	'''optioncontent : optioncontent COMMA optionentry'''

def p_optioncontent_obj(p):
	'''optioncontent : optionentry'''
	
def p_optionentry_dbr(p):
	'''optionentry : DBR IS LPAREN object COMMA object RPAREN'''

def p_optionentry_chg(p):
	'''optionentry : CHG IS INTEGER'''

def p_optionentry_massrange(p):
	'''optionentry : MASSRANGE IS LPAREN object COMMA object RPAREN'''

def p_optionentry_minocc(p):
	'''optionentry : MINOCC IS object'''

def p_optionentry_maxocc(p):
	'''optionentry : MAXOCC IS object'''

def p_optionentry_retentiontime(p):
	'''optionentry : RETENTIONTIME IS object'''

def p_optionentry_TOLERANCE(p):
	'''optionentry : TOLERANCE IS tolerancetype'''

def p_tolerancetype(p):
	'''tolerancetype : FLOAT DA
					 | FLOAT PPM
					 | INTEGER DA
		 			 | INTEGER RES
					 | INTEGER PPM'''

def p_identification_normal_old(p):
	'''identification : IDENTIFY tagname WHERE marks evalMarks suchthat REPORT report
		  			  | IDENTIFY tagname WHERE marks evalMarks REPORT report'''

def p_identification_interpretatin_old(p):
	'''identification : IDENTIFY tagname WHERE marks evalMarks suchthat interpretation REPORT report
		  			  | IDENTIFY tagname WHERE marks evalMarks interpretation REPORT report'''

def p_identification_normal_new(p):
	'''identification : IDENTIFY marks evalMarks suchthat REPORT report
		  			  | IDENTIFY marks evalMarks REPORT report'''
		
def p_identification_interpretation_new(p):
	'''identification : IDENTIFY marks evalMarks suchthat interpretation REPORT report
		  			  | IDENTIFY marks evalMarks interpretation REPORT report'''

def p_tagname(p):
	'''tagname : ID'''
	
def p_scinput(p):
	'''scinput : ID'''

def p_marks(p):
	'''marks : boolmarks'''

def p_booleanterm_paren(p):
	'''boolmarks : LPAREN boolmarks RPAREN'''

def p_boolmarks_not(p):
	'''boolmarks : NOT boolmarks'''

def p_boolmarks_or(p):
	'''boolmarks : boolmarks OR boolmarks'''

def p_boolmarks_and(p):
	'''boolmarks : boolmarks AND boolmarks'''

def p_boolmarks_if(p):
	'''boolmarks : boolmarks IFA boolmarks'''

def p_boolmarks_onlyif(p):
	'''boolmarks : boolmarks IFF boolmarks'''

def p_boolmarks_arrow(p):
	'''boolmarks : boolmarks ARROW boolmarks'''

def p_boolmarks_le(p):
	'''boolmarks : boolmarks LE boolmarks'''

def p_boolmarks_toScan(p):
	'''boolmarks : scan'''

def p_evalMarks(p):
	'''evalMarks : '''
				
def p_suchthat_single(p):
	'''suchthat : SUCHTHAT body'''

def p_body_bool(p):
	'''body : bterm'''
	
def p_bterm(p):
	'''bterm : booleanterm'''

def p_booleanterm_logic(p):
	'''booleanterm : booleanterm AND booleanterm
				   | booleanterm OR  booleanterm'''

def p_booleanterm_brackets(p):
	'''booleanterm : LPAREN booleanterm RPAREN'''

def p_booleanterm_not(p):
	'''booleanterm : NOT booleanterm'''

def p_booleanterm_expr(p):
	'''booleanterm : expr'''

def p_booleanterm_expression(p):
	'''booleanterm : object'''

def p_expr_multi(p):
	'''expr : expression EQUALS expression options
			| expression GT expression options
			| expression GE expression options 
			| expression LE expression options
			| expression LT expression options
			| expression NE expression options'''

def p_expression_struct(p):
	'''expression : expression PLUS expression
	  | expression MINUS expression
	  | expression TIMES expression
	  | expression DIVIDE expression'''

def p_expression_attribute(p):
	'''expression : LPAREN expression RPAREN LBRACE ID RBRACE'''

def p_expression_paren(p):
	'''expression : LPAREN expression RPAREN'''

def p_expression_content(p):
	'''expression : object'''

def p_interpret(p):
	'''interpretation : INTERPRETATION expr'''

def p_scan_object(p):
	'''scan : object IN scope options'''

def p_scope(p):
	'''scope : MS1 MINUS
			 | MS1 PLUS
			 | MS2 PLUS
			 | MS2 MINUS'''

def p_report(p):
	'''report : reportContent'''
	
def p_reportContent_cont(p):
	'''reportContent : reportContent rContent'''

def p_reportContent_single(p):
	'''reportContent : rContent'''

def p_rContent(p):
	'''rContent : ID IS STRING PERCENT STRING SEMICOLON
				| ID IS expression SEMICOLON'''

def p_error(p):
	if not p:
		print("SYNTAX ERROR at EOF in %s" % mfqlObj.filename)
		raise SyntaxErrorException("SYNTAX ERROR at EOF", mfqlObj.filename, mfqlObj.queryName, -1)
	else:
		print("Syntax error after '%s'\nfile: \t%s\nquery: \t%s\nline: \t%s" % (p.value, mfqlObj.filename, mfqlObj.queryName, p.lexer.lineno))
		raise SyntaxErrorException(None, mfqlObj.filename, mfqlObj.queryName, p.lexer.lineno)

parser = yacc.yacc(debug = 1, optimize = 0)
#bparser = yacc.yacc(method = 'LALR')

def startSyntaxCheck(dictData, mfqlObjIn):

	global mfqlObj
	global numQueries
	global listQueryNames

	listQueryNames = []
	numQueries = 0
	mfqlObj = mfqlObjIn
	mfqlObj.namespaceConnector = '_'

	### do the IDENTIFY(cation) ###
	for k in list(dictData.keys()):

		mfqlObj.filename = k

		lexer.lineno = 1
		mfqlObj.parsePart = 'identification'
		p = parser.parse(dictData[k], lexer = lexer)

		mfqlObj.reset()

	return numQueries

