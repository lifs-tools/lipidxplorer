from collections import namedtuple
import ply.yacc as yacc
from mfql_lexer import tokens, lexer

mfql_dict = {}
Var = namedtuple('Var', 'id object Options')
Options = namedtuple('Options', 'dbr_l dbr_h chg')
Obj = namedtuple('Obj', 'p_rule p_values')
ElementSeq = namedtuple('ElementSeq', 'str')
Evaluable = namedtuple('Evaluable', 'p_method , p_values')
ReportItem = namedtuple('ReportItem', 'id p_values')

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


def p_program(p):
    '''program  : script SEMICOLON
                | script'''
    #todo make mfql linter, remove depicated trailing semicolon
    p[0] = p[1]


# def p_script(p):
#     '''script  : scriptname variablesSection identification'''
#     mfql_dict['scriptname'] = p[1]
#     mfql_dict['variables'] = p[2]
#     mfql_dict['identification'] = p[3]
#
#     p[0] = mfql_dict

def p_script(p):
    '''script : scriptname variablesSection identificationSection suchthatSection reportSection SEMICOLON'''
    mfql_dict['scriptname'] = p[1]
    mfql_dict['variables'] = p[2]
    mfql_dict['identification'] = p[3]
    mfql_dict['suchthat'] = p[4]
    mfql_dict['report'] = p[5]
    p[0] = mfql_dict

def p_script1(p):
    '''script : scriptname variablesSection identificationSection reportSection SEMICOLON'''
    mfql_dict['scriptname'] = p[1]
    mfql_dict['variables'] = p[2]
    mfql_dict['identification'] = p[3]
    mfql_dict['suchthat'] = None
    mfql_dict['report'] = p[4]
    p[0] = mfql_dict


### VARIABLES ###

def p_scriptname(p):
    '''scriptname : QUERYNAME IS getQueryName SEMICOLON'''
    p[0] = p[3]


def p_getQueryName(p):
    '''getQueryName : ID'''
    p[0] = p[1]


# ----

def p_variablesSection(p):
    '''variablesSection : variables'''
    p[0] = p[1]

def p_variables_loop(p):
    '''variables : variables var'''
    p[0] = p[1] + [p[2]]


def p_variables_endloop(p):
    '''variables : var'''
    p[0] = [p[1]]


def p_var_normal(p):
    '''var : DEFINE ID IS object options SEMICOLON'''
    p[0] = Var(p[2], p[4], p[5])


def p_var_nl(p):
    '''var : DEFINE ID IS object options AS NEUTRALLOSS SEMICOLON'''
    options = p[5]
    options.chg = 0
    p[0] = Var(p[2], p[4], options)


def p_var_emptyVar(p):
    '''var : DEFINE ID options SEMICOLON'''
    p[0] = Var(p[2], None, p[2])


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
    p[0] = Obj('p_onlyObj_ID_itemAccess', p[1:])


def p_onlyObj_ID(p):
    '''onlyObj : ID'''
    p[0] = Obj('p_onlyObj_ID', p[1:])


def p_onlyObj_list(p):
    '''onlyObj : list'''
    p[0] = Obj('p_onlyObj_list', p[1:])


def p_onlyObj_varcontent(p):
    '''onlyObj : varcontent'''
    p[0] = p[1]


def p_onlyObj_function1(p):
    '''onlyObj : ID LPAREN arguments RPAREN LBRACE ID RBRACE'''
    p[0] = Obj('p_onlyObj_function1', p[1:])


def p_onlyObj_function2(p):
    '''onlyObj : ID LPAREN arguments RPAREN'''
    p[0] = Obj('p_onlyObj_function2', p[1:])


def p_withAttr_accessItem_(p):
    '''withAttr : ID DOT ID LBRACE ID RBRACE'''
    p[0] = Obj('p_withAttr_accessItem_', p[1:])


def p_withAttr_accessItem_string(p):
    '''withAttr : ID DOT ID LBRACE STRING RBRACE'''
    p[0] = Obj('p_withAttr_accessItem_string', p[1:])


def p_withAttr_id(p):
    '''withAttr : ID DOT ID'''
    p[0] = Obj('p_withAttr_id', p[1:])


def p_withAttr_varcontent(p):
    '''withAttr : varcontent DOT ID'''
    p[0] = Obj('p_withAttr_varcontent', p[1:])


def p_withAttr_list(p):
    '''withAttr : list DOT ID'''
    p[0] = Obj('p_withAttr_list', p[1:])


# -----
def p_arguments_empty(p):
    '''arguments :'''
    # TODO this should not be processed
    p[0] = None


def p_arguments_single(p):
    '''arguments : expression'''
    p[0] = [p[1]]


def p_arguments_multi(p):
    '''arguments : arguments COMMA expression'''
    p[0] = p[1] + [p[3]]


### LIST ###

def p_list(p):
    '''list : LBRACKET listcontent RBRACKET'''
    p[0] = p[2]


def p_listcontent_cont(p):
    '''listcontent : listcontent COMMA object'''
    p[0] = p[1] + [p[3]]


def p_listcontent_obj(p):
    '''listcontent : object'''
    p[0] = [p[1]]


### VARCONTENT ###

def p_varcontent_tolerance(p):
    '''varcontent : tolerancetype'''
    p[0] = p[1]


def p_varcontent_float(p):
    '''varcontent : FLOAT'''
    p[0] = float(p[1])


def p_varcontent_integer(p):
    '''varcontent : INTEGER
                  | PLUS INTEGER'''
    p[0] = int(''.join(p[1:]))


def p_varcontent_integer_min(p):
    '''varcontent : MINUS INTEGER'''
    p[0] = -1 * int(p[2])


def p_varcontent_string(p):
    '''varcontent : STRING'''
    p[0] = p[1].strip('"')


def p_varcontent_sfstring(p):
    '''varcontent : SFSTRING'''
    # TODO try parseElemSeq(p[1].strip('\''))
    p[0] = ElementSeq(p[1].strip('\''))


### OPTIONS ###

def p_options_there(p):
    '''options : WITH optioncontent'''
    p[0] = p[2]


def p_options_not_there(p):
    # TODO this should be eliminated
    '''options :'''


def p_optioncontent_cont(p):
    # TODO did I see this before?
    '''optioncontent : optioncontent COMMA optionentry'''
    p[0] = p[1] + [p[2]]


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
        raise ValueError(
            "Tolerance value as given in the query '%s' can not be smaller" % mfqlObj.queryName + \
            " or equal zero")

    p[0] = (p[2].lower(), float(p[1]))


# --
# identification part
# see https://github.com/dabeaz/ply/blob/master/example/GardenSnake/GardenSnake.py
# https://github.com/dabeaz/ply/blob/master/example/calc/calc.py

def p_identificationSection(p):
    '''identificationSection : IDENTIFY marks evalMarks '''
    #todo check what these are
    p[0] = (p[2],p[2])

def p_marks(p):
    '''marks : boolmarks'''
    p[0] = p[1]


def p_booleanterm_paren(p):
    '''boolmarks : LPAREN boolmarks RPAREN'''
    p[0] = Evaluable('p_booleanterm_paren', p[1:])


def p_boolmarks_not(p):
    '''boolmarks : NOT boolmarks'''

    p[0] = Evaluable('p_boolmarks_not', p[1:])


def p_boolmarks_or(p):
    '''boolmarks : boolmarks OR boolmarks'''
    p[0] = Evaluable('p_boolmarks_or', p[1:])


def p_boolmarks_and(p):
    '''boolmarks : boolmarks AND boolmarks'''
    p[0] = Evaluable('p_boolmarks_and', p[1:])


def p_boolmarks_if(p):
    # todo how is this differenc to the other if?
    '''boolmarks : boolmarks IFA boolmarks'''

    p[0] = Evaluable('p_boolmarks_if', p[1:])


def p_boolmarks_onlyif(p):
    '''boolmarks : boolmarks IFF boolmarks'''

    p[0] = Evaluable('p_boolmarks_onlyif', p[1:])


def p_boolmarks_arrow(p):
    '''boolmarks : boolmarks ARROW boolmarks'''

    p[0] = Evaluable('p_boolmarks_arrow', p[1:])


def p_boolmarks_le(p):
    '''boolmarks : boolmarks LE boolmarks'''
    p[0] = Evaluable('p_boolmarks_le', p[1:])


def p_boolmarks_toScan(p):
    '''boolmarks : scan'''

    p[0] = Evaluable('p_boolmarks_toScan', p[1:])


def p_evalMarks(p):
    '''evalMarks : '''
    # todo this should not happen


#---------------
# https://www.dabeaz.com/ply/PLYTalk.pdf
def p_suchthatSection(p):
    '''suchthatSection : SUCHTHAT body'''
    p[0] = p[2]

# def p_suchthat_single(p):
#     '''suchthat : SUCHTHAT body'''
#     p[0] = p[2]


def p_body_bool(p):
    '''body : bterm'''
    # TODO redundant why is this here?
    p[0] = p[1]


def p_bterm(p):
    '''bterm : booleanterm'''
    p[0] = p[1]


def p_booleanterm_logic(p):
    '''booleanterm : booleanterm AND booleanterm
                   | booleanterm OR  booleanterm'''

    p[0] = Evaluable('p_booleanterm_logic', p[1:])


def p_booleanterm_brackets(p):
    '''booleanterm : LPAREN booleanterm RPAREN'''

    p[0] = Evaluable('p_booleanterm_brackets', p[1:])


def p_booleanterm_not(p):
    '''booleanterm : NOT booleanterm'''

    p[0] = Evaluable('p_booleanterm_not', p[1:])


def p_booleanterm_expr(p):
    '''booleanterm : expr'''

    p[0] = Evaluable('p_booleanterm_expr', p[1:])


def p_booleanterm_expression(p):
    '''booleanterm : object'''

    p[0] = Evaluable('p_booleanterm_expression', p[1:])


def p_expr_multi(p):
    '''expr : expression EQUALS expression options
            | expression GT expression options
            | expression GE expression options
            | expression LE expression options
            | expression LT expression options
            | expression NE expression options
            | expression ARROWR expression options '''

    p[0] = Evaluable('p_expr_multi', p[1:])


def p_expression_struct(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | MINUS expression %prec UMINUS'''

    p[0] = Evaluable('p_expression_struct', p[1:])


def p_expression_attribute(p):
    '''expression : LPAREN expression RPAREN LBRACE ID RBRACE'''
    p[0] = Evaluable('p_expression_attribute', p[1:])


def p_expression_paren(p):
    '''expression : LPAREN expression RPAREN'''
    p[0] = Evaluable('p_expression_paren', p[1:])


def p_expression_content(p):
    '''expression : object'''
    p[0] = Evaluable('p_expression_content', p[1:])


### SCAN ###

def p_scan_object(p):
    '''scan : object IN scope options'''
    p[0] = Evaluable('p_scan_object', p[1:])


def p_scope(p):
    '''scope : MS1 MINUS
             | MS1 PLUS
             | MS2 PLUS
             | MS2 MINUS'''

    p[0] = p[1] + p[2]

#---
def p_reportSection(p):
    '''reportSection : REPORT reportContent'''
    p[0]=p[2]


def p_reportContent_cont(p):
    '''reportContent : reportContent reportItem'''
    # TODO improve format here
    p[0] = p[1] + [p[2]]


def p_reportContent_single(p):
    '''reportContent : reportItem'''
    p[0] = [p[1]]


def p_rContent(p):
    '''reportItem : ID IS STRING PERCENT STRING SEMICOLON
                | ID IS STRING PERCENT LPAREN arguments RPAREN SEMICOLON
                | ID IS expression SEMICOLON'''

    p[0] = ReportItem(p[1], p[3:])


def p_error(p):
    if not p:
        raise SyntaxError("SYNTAX ERROR at EOF")
    else:
        detail = "Syntax error at '%s' in file at position %s %s" % (p .value,p.lineno , p.lexpos)
        raise SyntaxError(detail)


parser = yacc.yacc(debug=0, optimize=1)
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

    result = parser.parse(mfql, lexer = lexer, debug=1)
    expected = '''
    {'variables': [Var(id='pr', object=ElementSeq(str='C[30..80] H[40..300] O[10] N[1] P[1]'), Options=[('dbr', [2.5, 14.5]), ',']), Var(id='FA1', object=ElementSeq(str='C[10..40] H[20..100] O[2]'), Options=[('dbr', [1.5, 7.5]), ',']), Var(id='FA2', object=ElementSeq(str='C[10..40] H[20..100] O[2]'), Options=[('dbr', [1.5, 7.5]), ','])], 'scriptname': 'PCFAS', 'identification': None, 'marks': Evaluable(p_method='p_boolmarks_and', p_values=[Evaluable(p_method='p_boolmarks_and', p_values=[Evaluable(p_method='p_boolmarks_toScan', p_values=[Evaluable(p_method='p_scan_object', p_values=[Obj(p_rule='p_onlyObj_ID', p_values=['pr']), 'IN', 'MS1-', None])]), 'AND', Evaluable(p_method='p_boolmarks_toScan', p_values=[Evaluable(p_method='p_scan_object', p_values=[Obj(p_rule='p_onlyObj_ID', p_values=['FA1']), 'IN', 'MS2-', None])])]), 'AND', Evaluable(p_method='p_boolmarks_toScan', p_values=[Evaluable(p_method='p_scan_object', p_values=[Obj(p_rule='p_onlyObj_ID', p_values=['FA2']), 'IN', 'MS2-', None])])]), 'report': [Var(id='pr', object=ElementSeq(str='C[30..80] H[40..300] O[10] N[1] P[1]'), Options=[('dbr', [2.5, 14.5]), ',']), Var(id='FA1', object=ElementSeq(str='C[10..40] H[20..100] O[2]'), Options=[('dbr', [1.5, 7.5]), ',']), Var(id='FA2', object=ElementSeq(str='C[10..40] H[20..100] O[2]'), Options=[('dbr', [1.5, 7.5]), ','])], 'suchthat': Evaluable(p_method='p_booleanterm_logic', p_values=[Evaluable(p_method='p_booleanterm_logic', p_values=[Evaluable(p_method='p_booleanterm_expression', p_values=[Obj(p_rule='p_onlyObj_function2', p_values=['isOdd', '(', [Evaluable(p_method='p_expression_content', p_values=[Obj(p_rule='p_withAttr_accessItem_', p_values=['pr', '.', 'chemsc', '[', 'H', ']'])])], ')'])]), 'AND', Evaluable(p_method='p_booleanterm_expression', p_values=[Obj(p_rule='p_onlyObj_function2', p_values=['isOdd', '(', [Evaluable(p_method='p_expression_struct', p_values=[Evaluable(p_method='p_expression_content', p_values=[Obj(p_rule='p_withAttr_accessItem_', p_values=['pr', '.', 'chemsc', '[', 'db', ']'])]), '*', Evaluable(p_method='p_expression_content', p_values=[2])])], ')'])])]), 'AND', Evaluable(p_method='p_booleanterm_expr', p_values=[Evaluable(p_method='p_expr_multi', p_values=[Evaluable(p_method='p_expression_struct', p_values=[Evaluable(p_method='p_expression_struct', p_values=[Evaluable(p_method='p_expression_content', p_values=[Obj(p_rule='p_withAttr_id', p_values=['FA1', '.', 'chemsc'])]), '+', Evaluable(p_method='p_expression_content', p_values=[Obj(p_rule='p_withAttr_id', p_values=['FA2', '.', 'chemsc'])])]), '+', Evaluable(p_method='p_expression_content', p_values=[ElementSeq(str='C9 H19 N1 O6 P1')])]), '==', Evaluable(p_method='p_expression_content', p_values=[Obj(p_rule='p_withAttr_id', p_values=['pr', '.', 'chemsc'])]), None])])]), 'evalMarks': Evaluable(p_method='p_boolmarks_and', p_values=[Evaluable(p_method='p_boolmarks_and', p_values=[Evaluable(p_method='p_boolmarks_toScan', p_values=[Evaluable(p_method='p_scan_object', p_values=[Obj(p_rule='p_onlyObj_ID', p_values=['pr']), 'IN', 'MS1-', None])]), 'AND', Evaluable(p_method='p_boolmarks_toScan', p_values=[Evaluable(p_method='p_scan_object', p_values=[Obj(p_rule='p_onlyObj_ID', p_values=['FA1']), 'IN', 'MS2-', None])])]), 'AND', Evaluable(p_method='p_boolmarks_toScan', p_values=[Evaluable(p_method='p_scan_object', p_values=[Obj(p_rule='p_onlyObj_ID', p_values=['FA2']), 'IN', 'MS2-', None])])])}
    '''
    expected = expected.strip()
    print(str(result) == expected)
