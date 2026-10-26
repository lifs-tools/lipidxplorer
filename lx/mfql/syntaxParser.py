#!/usr/bin/python
"""Syntax check for MFQL queries, without spectra and without running them.

Used by the MFQL editor (marks errors while typing and on save) and by
startSyntaxCheck() for a check of several files before a run.

The grammar below must accept exactly what the real parser
(lx/mfql/mfqlParser.py) accepts. tests/test_syntax_parser.py compares the
two grammars and fails if they drift apart; when the MFQL language changes
in mfqlParser.py, change the same rule here.

Changes against the old (Python 2) version of this file:
  * Python 3 (print(), absolute import of chemParser)
  * keywords, tokens, precedence and rules made identical to mfqlParser.py.
    Removed: INTERPRETATION, RETENTIONTIME, DEFINE {list}, scinput and the
    unused keywords NO FOR CROSSPROD EVERY PRECURSOR OF CHECK IF. They made
    valid queries fail, e.g. every query with a variable called "Precursor".
    Added: '<~', unary minus, f() without arguments and
    REPORT  x = "..." % (args);
  * lexer rules (comments, white space, line counting) as in mfqlParser.py
  * errors carry message, line, column and file; SYNTAX ERROR at EOF and
    p_error no longer pass the arguments of SyntaxErrorException in the
    wrong order
  * checks the real run only does after loading spectra are done here:
    undefined / unused variables, bad sum compositions, tolerance <= 0,
    one query per file, old "IDENTIFY name WHERE" form, underscores
  * own parse tables in memory (no parser.out / parsetab.py written, no
    clash with mfqlParser's parsetab.py)
  * no global mfqlObj needed; checkText() for the editor
"""

import re
import threading

import ply.lex as lex
import ply.yacc as yacc

from lx.exceptions import SyntaxErrorException
from lx.mfql.chemParser import parseElemSeq


###############################################################################
################################## Results ####################################
###############################################################################

class MFQLSyntaxError(SyntaxErrorException):
	"""One problem in a query.

	Is a SyntaxErrorException, so existing handlers keep working.
	p_value: message; fileName, queryName; lineno, column (1-based);
	offset, length: character position in the checked text;
	severity: "error" or "warning".
	"""

	def __init__(self, message, fileName, queryName, lineno, column=1,
				offset=0, length=1, severity="error"):
		SyntaxErrorException.__init__(self, message, queryName, lineno)
		self.message = message
		self.fileName = fileName
		self.filename = fileName
		self.column = column
		self.offset = offset
		self.length = max(1, length)
		self.severity = severity
		# old names used by MFQLProblem
		self.line = lineno

	def __str__(self):
		where = "line %d" % self.lineno
		if self.fileName:
			where = "%s, %s" % (self.fileName, where)
		return "%s: %s" % (where, self.message)


class _Stop(Exception):
	"""Ends the parse at the first error."""


class _Var:
	"""A variable as written in the query, with its position."""

	def __init__(self, name, offset):
		self.name = name
		self.offset = offset


class _Check:
	"""State of one checked text."""

	def __init__(self, text, filename):
		self.text = text
		self.filename = filename
		self.problems = []
		self.queryName = ""
		self.numQueries = 0
		self.defined = {}		# variable -> offset of its DEFINE
		self.used = set()

	def problem(self, message, offset, length=1, severity="error"):
		lineno, column = _lineAndColumn(self.text, offset)
		p = MFQLSyntaxError(message, self.filename, self.queryName, lineno,
				column, offset, length, severity)
		self.problems.append(p)
		return p

	def stop(self, message, offset, length=1):
		self.problem(message, offset, length)
		raise _Stop()


_check = None				# the _Check of the parse in progress
_lock = threading.Lock()

_LINEBREAK = re.compile(r'\r\n|\r|\n')


def _lineAndColumn(text, offset):
	offset = max(0, min(offset, len(text)))
	lineno, start = 1, 0
	for m in _LINEBREAK.finditer(text, 0, offset):
		lineno += 1
		start = m.end()
	return lineno, offset - start + 1


###############################################################################
################################### Lexer #####################################
###############################################################################

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

def t_comment(t):
	r'[ ]*\043[^\n]*'
	t.lexer.lineno += t.value.count("\n")

def t_WS(t):
	r'[ \t]+'

def t_WS_NL(t):
	r'(([ \t]*)\n)'
	t.lexer.lineno += t.value.count("\n")

def t_UNDERSCORE(t):
	r'_'
	_check.stop("No underscore allowed.", t.lexpos)

def t_error(t):
	# the real parser skips characters it cannot read; so do we, with a warning
	if t.value[0] != '\r':
		_check.problem("Illegal character '%s' (it is ignored when the query runs)." % t.value[0],
				t.lexpos, 1, "warning")
	t.lexer.skip(1)

# build lexer
lexer = lex.lex(reflags = re.I, debug = 0, optimize = 0)


###############################################################################
########################### Parser starts here ################################
###############################################################################

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

def p_script(p):
	'''script  : scriptname variables identification
			   | identification'''

def p_script_error(p):
	'''script : error variables identification'''

### VARIABLES ###

def p_scriptname(p):
	'''scriptname : QUERYNAME IS getQueryName SEMICOLON'''
	_check.numQueries += 1
	if _check.numQueries > 1:
		_check.stop("There is only one query per *.mfql file allowed!", p.lexpos(1), len(p[1]))

def p_getQueryName(p):
	'''getQueryName : ID'''
	_check.queryName = p[1]
	_check.defined = {}
	_check.used = set()

def p_variables_loop(p):
	'''variables : variables var'''

def p_variables_endloop(p):
	'''variables : var'''

def p_var_normal(p):
	'''var : DEFINE ID IS object options SEMICOLON
			| DEFINE ID IS object options AS NEUTRALLOSS SEMICOLON'''
	_check.defined.setdefault(p[2], p.lexpos(2))

def p_var_emptyVar(p):
	'''var : DEFINE ID options SEMICOLON'''
	_check.defined.setdefault(p[2], p.lexpos(2))

### OBJECT ###

def p_object_withAttr(p):
	'''object : withAttr'''
	p[0] = p[1]

def p_object_onlyObj(p):
	'''object : onlyObj'''
	p[0] = p[1]

### OBJECT/VARCONTENT ###

def p_onlyObj_ID_itemAccess(p):
	'''onlyObj : ID LBRACE ID RBRACE'''
	p[0] = _Var(p[1], p.lexpos(1))

def p_onlyObj_ID(p):
	'''onlyObj : ID'''
	p[0] = _Var(p[1], p.lexpos(1))

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
	p[0] = _Var(p[1], p.lexpos(1))

def p_withAttr_accessItem_string(p):
	'''withAttr : ID DOT ID LBRACE STRING RBRACE'''
	p[0] = _Var(p[1], p.lexpos(1))

def p_withAttr_id(p):
	'''withAttr : ID DOT ID'''
	p[0] = _Var(p[1], p.lexpos(1))

def p_withAttr_varcontent(p):
	'''withAttr : varcontent DOT ID'''

def p_withAttr_list(p):
	'''withAttr : list DOT ID'''

def p_arguments_empty(p):
	'''arguments :'''

def p_arguments_single(p):
	'''arguments : expression'''

def p_arguments_multi(p):
	'''arguments : arguments COMMA expression'''

### LIST ###

def p_list(p):
	'''list : LBRACKET listcontent RBRACKET'''

def p_listcontent_cont(p):
	'''listcontent : listcontent COMMA object'''

def p_listcontent_obj(p):
	'''listcontent : object'''

### VARCONTENT ###

def p_varcontent_tolerance(p):
	'''varcontent : tolerancetype'''

def p_varcontent_float(p):
	'''varcontent : FLOAT'''

def p_varcontent_integer(p):
	'''varcontent : INTEGER
				  | PLUS INTEGER
				  | MINUS INTEGER'''

def p_varcontent_string(p):
	'''varcontent : STRING'''

def p_varcontent_sfstring(p):
	'''varcontent : SFSTRING'''
	formula = p[1].strip("'")
	try:
		parseElemSeq(formula)
	except Exception as e:		# ValueError / SyntaxErrorException from chemParser
		_check.stop(*_formulaError(e, formula, p.lexpos(1) + 1))

### OPTIONS ###

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

def p_optionentry_TOLERANCE(p):
	'''optionentry : TOLERANCE IS tolerancetype'''

def p_tolerancetype(p):
	'''tolerancetype : FLOAT DA
					 | FLOAT PPM
					 | INTEGER DA
		 			 | INTEGER RES
					 | INTEGER PPM'''
	if float(p[1]) <= 0.0:
		_check.stop("Tolerance value as given in the query '%s' can not be smaller or equal zero"
				% _check.queryName, p.lexpos(1), len(p[1]))

### IDENTIFICATION ###

def p_identification_normal_old(p):
	'''identification : IDENTIFY tagname WHERE marks evalMarks suchthat REPORT report
		  			  | IDENTIFY tagname WHERE marks evalMarks REPORT report'''
	_check.stop("Please remove the query name after 'IDENTIFY'. This is not supported anymore.",
			p.lexpos(2), len(p[2]))

def p_identification_normal_new(p):
	'''identification : IDENTIFY marks evalMarks suchthat REPORT report
		  			  | IDENTIFY marks evalMarks REPORT report'''

def p_tagname(p):
	'''tagname : ID'''
	p[0] = p[1]

def p_marks(p):
	'''marks : boolmarks'''
	# as in the real run: every DEFINEd variable has to be used in IDENTIFY
	for var, offset in _check.defined.items():
		if var not in _check.used:
			_check.stop("The variable '%s' in query '%s' has to be used in IDENTIFY"
					% (var, _check.queryName), offset, len(var))

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

### SUCHTHAT ###

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
			| expression NE expression options
			| expression ARROWR expression options '''

def p_expression_struct(p):
	'''expression : expression PLUS expression
				  | expression MINUS expression
				  | expression TIMES expression
				  | expression DIVIDE expression
				  | MINUS expression %prec UMINUS'''

def p_expression_attribute(p):
	'''expression : LPAREN expression RPAREN LBRACE ID RBRACE'''

def p_expression_paren(p):
	'''expression : LPAREN expression RPAREN'''

def p_expression_content(p):
	'''expression : object'''

### SCAN ###

def p_scan_object(p):
	'''scan : object IN scope options'''
	obj = p[1]
	if not isinstance(obj, _Var):
		_check.stop("Only a DEFINEd variable can be used with IN.", p.lexpos(2), len(p[2]))
	if obj.name not in _check.defined:
		_check.stop("Variable \"%s\" in query \"%s\" does not exist."
				% (obj.name, _check.queryName), obj.offset, len(obj.name))
	_check.used.add(obj.name)

def p_scope(p):
	'''scope : MS1 MINUS
			 | MS1 PLUS
			 | MS2 PLUS
			 | MS2 MINUS'''

### REPORT ###

def p_report(p):
	'''report : reportContent'''

def p_reportContent_cont(p):
	'''reportContent : reportContent rContent'''

def p_reportContent_single(p):
	'''reportContent : rContent'''

def p_rContent(p):
	'''rContent : ID IS STRING PERCENT STRING SEMICOLON
				| ID IS STRING PERCENT LPAREN arguments RPAREN SEMICOLON
				| ID IS expression SEMICOLON'''

### ERRORS ###

def p_error(p):
	if not p:
		_check.stop("Unexpected end of the query. Is the final ';' missing?",
				max(0, len(_check.text.rstrip()) - 1))
	value = str(p.value)
	message = "Syntax error at '%s'." % value
	# Most common mistake: a line that does not end with ';'. The error is
	# then reported at the first word of the next line.
	text = _check.text
	lineStart = max(text.rfind("\n", 0, p.lexpos), text.rfind("\r", 0, p.lexpos)) + 1
	before = text[:p.lexpos].rstrip()
	if not text[lineStart:p.lexpos].strip() and before and not before.endswith(";"):
		message += " Is the ';' missing at the end of the line before?"
	_check.stop(message, p.lexpos, len(value))


def _formulaError(exc, formula, start):
	"""(message, offset, length) for an error from chemParser.parseElemSeq."""
	detail = getattr(exc, "p_value", None)
	if detail:
		return "Invalid sum composition '%s': %s" % (formula, detail), start, len(formula)
	lines = str(exc).splitlines()
	first = re.sub(r"character\d+:?$", "character", lines[0].strip()) if lines else ""
	first = first.replace("Syntax Error: ", "")
	# chemParser marks the position with a caret line: "    ^"
	caret = next((l.index("^") for l in lines if l.strip() == "^"), None)
	if caret is not None and caret < len(formula):
		if first.endswith("unexpected character"):
			first += " '%s'" % formula[caret]
		return "Invalid sum composition '%s': %s" % (formula, first), start + caret, 1
	return "Invalid sum composition '%s': %s" % (formula, first), start, len(formula)


# Own tables in memory: nothing is written next to this file, and the
# tables of mfqlParser (parsetab.py) are never read or overwritten.
parser = yacc.yacc(debug = False, write_tables = False, optimize = False,
		tabmodule = 'syntaxParser_parsetab', errorlog = yacc.NullLogger())


###############################################################################
################################### API #######################################
###############################################################################

def _onlyComments(text):
	return all(not line.strip() or line.lstrip().startswith("#")
			for line in _LINEBREAK.split(text))


def checkText(text, filename=""):
	"""Check one query text. Returns a list of MFQLSyntaxError (errors and
	warnings, errors first); an empty list means the query is fine.

	Stops at the first error. Never raises for problems in the query.
	"""
	global _check
	if _onlyComments(text):
		return []		# new, empty file: nothing to complain about
	with _lock:
		_check = _Check(text, filename)
		try:
			lexer.lineno = 1
			parser.parse(text, lexer = lexer, tracking = True)
		except _Stop:
			pass
		finally:
			problems, _check = _check.problems, None
	problems.sort(key = lambda p: (p.severity != "error", p.offset))
	return problems


def startSyntaxCheck(dictData, mfqlObjIn = None):
	"""Check several queries {filename: text} before a run.

	Raises the first MFQLSyntaxError (a SyntaxErrorException) found, with
	file name, line and message. Returns the number of queries.
	mfqlObjIn is accepted for compatibility and not needed.
	"""
	numQueries = 0
	for filename, text in dictData.items():
		errors = [p for p in checkText(text, filename) if p.severity == "error"]
		if errors:
			raise errors[0]
		if not _onlyComments(text):
			numQueries += 1
	return numQueries
