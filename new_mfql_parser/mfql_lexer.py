import ply.lex as lex
import re

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

#

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
	pass

def t_WS(t):
	r'[ \t]+'
	pass

def t_WS_NL(t):
	r'(([ \t]*)\n)'
	t.lexer.lineno += t.value.count("\n")
	pass


def t_UNDERSCORE(t):
	r'_'
	raise SyntaxErrorException("In query %s, line %d: No underscore allowed." % (mfqlObj.filename, t.lexer.lineno),
			mfqlObj.filename,
			"",
			0)

def t_error(t):
	if not ord(t.value[0]) == 13:
		print "Illegal character %s (%s) in line %d" % (t.value[0], ord(t.value[0]), t.lexer.lineno)
	t.lexer.skip(1)


lexer = lex.lex(reflags = re.I, debug = 0, optimize = 0)


if __name__ == '__main__':

    mfql = '''
    ##########################################################
    # Identify PC SPCCIES #
    ##########################################################

    QUERYNAME = PCFAS;
    	DEFINE pr = 'C[30..80] H[40..300] O[10] N[1] P[1]' WITH DBR = (2.5,14.5), CHG = -1;
    	DEFINE FA1 = 'C[10..40] H[20..100] O[2]' WITH DBR = (1.5,7.5), CHG = -1;
    	DEFINE FA2 ='C[10..40] H[20..100] O[2]' WITH DBR = (1.5,7.5), CHG = -1;

    IDENTIFYjup
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

    lexer.input(mfql)

    # Tokenize
    while True:
        tok = lexer.token()
        if not tok:
            break  # No more input
        print(tok)
