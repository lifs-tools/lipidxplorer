from collections import  namedtuple
import ply.yacc as yacc
from mfql_lexer import tokens

mfql_dict = {}
Var = namedtuple('Var','id object Options')
Options = namedtuple('Options', 'dbr_l dbr_h chg')
Var_in_ms =namedtuple('Var_in_ms','var ms')
Binop = namedtuple('Binop','op  left right')

# see https://github.com/dabeaz/ply/blob/master/example/newclasscalc/calc.py
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

################
### PROGRAMM ###
def p_program_single(p):
    '''program  : script SEMICOLON'''
    print(' its done this is why he needs an extra semicoloni, maybe compare p[1] to mfql_dict' )
    print(mfql_dict == p[1])
    p[0] = p[1]

def p_script(p):
    '''script  : scriptname variablesSection identificationSection suchthatSection reportSection'''
    mfql_dict['scriptname'] = p[1]
    mfql_dict['variables'] = p[2]
    mfql_dict['identification'] = p[3]
    mfql_dict['suchthat'] = p[4]
    mfql_dict['report'] = p[5]
    p[0] = mfql_dict

def p_script1(p):
    '''script  : scriptname variables identificationSection reportSection'''
    mfql_dict['scriptname'] = p[1]
    mfql_dict['variables'] = p[2]
    mfql_dict['identification'] = p[3]
    mfql_dict['suchthat'] = None
    mfql_dict['report'] = p[4]
    p[0] = mfql_dict


def p_scriptname(p):
    '''scriptname : QUERYNAME IS ID SEMICOLON'''
    p[0] = p[3]


def p_variables(p):
    '''variables : variables var'''
    p[0] = p[1] + [p[2]]

def p_variable(p):
    '''variables : var'''
    p[0] = [p[1]]

def p_var_normal(p):
    '''var : DEFINE ID IS object WITH options SEMICOLON'''
    p[0]=Var(p[2], p[4], p[5])

def p_var_nl(p):
    '''var : DEFINE ID IS object WITH options AS NEUTRALLOSS SEMICOLON'''
    options = p[5]
    options.chg = 0
    p[0]=Var(p[2], p[4], options)
    print('check neutral loss')

def p_object(p):
    '''object : SFSTRING'''
    p[0] = p[1]

def p_options(p):
    '''options : option COMMA option''' # two options
    option1 = p[1]
    option2 = p[3]
    option_1_2 = [attr1 if attr1 is not None else attr2 for attr1, attr2 in zip(option1, option2)]
    p[0] = Options(*option_1_2)

def p_options(p):
    '''options : option''' # one option
    p[0] = p[1]

def p_option_dbr(p):
    '''option : DBR IS LPAREN object COMMA object RPAREN'''
    p[0] = Options(float(p[4]), float(p[6]), None)

def p_option_chg(p):
    '''option : CHG IS INTEGER'''
    p[0] = Options(None, None, int(p[3]))
#--

# see https://github.com/dabeaz/ply/blob/master/example/GardenSnake/GardenSnake.py
# https://github.com/dabeaz/ply/blob/master/example/calc/calc.py
def p_identificationSection(p):
    '''identificationSection : IDENTIFY op_tree'''
    p[0] = p[2]


def p_only_Statement(p):
    '''op_tree : statement'''
    p[0] = p[1]

def p_statement_in(p):
    '''statement : ID IN scope '''
    if p[1] not in [ var.id for var in mfql_dict['variables']]:
        print('var {} not defined'.format(p[1]))
    p[0] = Var_in_ms(p[1], p[3])

def p_scope(p):
    '''scope : MS1 MINUS
             | MS1 PLUS
             | MS2 PLUS
             | MS2 MINUS'''

    p[0] = p[1] + p[2]
#---

def p_op_tree(p):
    '''op_tree : binop'''
    p[0] = p[1]

def p_binop(p):
    '''binop : binop AND binop
            | binop OR binop'''
    p[0] = Binop(p[2],p[1],p[3])

def p_binop_end(p):
    '''binop : statement'''
    p[0] = p[1]

#---
def p_binop_parenthesis(p):
    " binop : LPAREN binop RPAREN"
    p[0] = Binop(p[1], p[2], None)

def p_binop_not(p):
    " binop : NOT binop"
    p[0] = Binop(p[1], p[2], None)

#---------------
def p_suchthatSection(p):
    '''suchthatSection : SUCHTHAT suchthat'''
    p[0] = p[2]

def p_suchthat(p):
    '''suchthat : booleanterm '''
    p[0] = p[1]

def p_booleanterm_logic(p):
    '''booleanterm : booleanterm AND booleanterm
                   | booleanterm OR  booleanterm'''
    p[0] = Binop(p[2],p[1],p[3])

def p_booleanterm_brackets(p):
    '''booleanterm : LPAREN booleanterm RPAREN'''
    p[0] = Binop(p[1],p[2],None)

def p_booleanterm_not(p):
    '''booleanterm : NOT booleanterm'''
    p[0] = Binop(p[1], p[2], None)

def p_booleanterm_expr(p):
    '''booleanterm : expr'''
    p[0] = Binop('expr', p[1], None)

def p_booleanterm_obj(p):
    '''booleanterm : object'''
    p[0] = Binop('object', p[1], None)

def p_expr_multi(p):
    '''expr : expression EQUALS expression
            | expression GT expression
            | expression GE expression
            | expression LE expression
            | expression LT expression
            | expression NE expression
            | expression ARROWR expression'''
    p[0] = Binop(p[2], p[1], p[3])

def p_expression_struct(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | MINUS expression %prec UMINUS'''
    p[0] = Binop(p[2], p[1], p[3])

def p_expression_paren(p):
    '''expression : LPAREN expression RPAREN'''
    p[0] = p[2]

def p_expression_content(p):
    '''expression : object'''
    p[0] = p[1]

#-------------------------
def p_reportSection(p):
    '''reportSection : REPORT report'''
    p[0]=p[2]

def p_report_1(p):
    '''report : report_items'''
    p[0] = p[1]

def p_report_items_1(p):
    '''report_items : report_item'''
    p[0] = p[1]

def report_items(p):
    '''report_items : report_items report_item'''
    items_dict = p[1]
    p[0] = items_dict.update(p[2])


def p_report_item(p):
    '''report_item : ID IS STRING SEMICOLON'''
    p[0] = {p[1]:p[3]}

#--
def p_error(p):
    if not p:
        print "SYNTAX ERROR at EOF"
        raise EOFError("SYNTAX ERROR at EOF")
    else:
        detail = "Syntax error at '%s'" % (p.value )
        raise SyntaxError(detail)

#######

parser = yacc.yacc(debug=1, optimize=0)
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
