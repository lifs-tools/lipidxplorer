import warnings

import ply.yacc as yacc

from data_structs import mfql_dict, Var, Obj, ElementSeq, Evaluable, ReportItem, Func
from mfql_lexer import tokens, lexer

tokens = tokens  # for linting

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
    '''program  : script  SEMICOLON
                | script '''
    #todo make mfql linter, remove  trailing semicolon
    p[0] = p[1]


def p_script(p):
    '''script : scriptname variablesSection identificationSection suchthatSection reportSection'''
    mfql_dict['scriptname'] = p[1]
    mfql_dict['variables'] = p[2]
    mfql_dict['identification'] = p[3]
    mfql_dict['suchthat'] = p[4]
    mfql_dict['report'] = p[5]
    p[0] = mfql_dict

def p_script1(p):
    '''script : scriptname variablesSection identificationSection reportSection'''
    mfql_dict['scriptname'] = p[1]
    mfql_dict['variables'] = p[2]
    mfql_dict['identification'] = p[3]
    mfql_dict['suchthat'] = None
    mfql_dict['report'] = p[4]
    p[0] = mfql_dict


### VARIABLES ###

def p_scriptname(p):
    '''scriptname : QUERYNAME IS ID SEMICOLON'''
    p[0] = p[3]


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
    '''var : DEFINE ID IS object WITH optioncontent SEMICOLON'''
    p[0] = Var(p[2], p[4], p[6])

def p_var_no_opts(p):
    '''var : DEFINE ID IS object SEMICOLON'''
    p[0] = Var(p[2], p[4], None)


def p_var_nl(p):
    '''var : DEFINE ID IS object WITH  optioncontent AS NEUTRALLOSS SEMICOLON'''
    options = p[6]
    option = {'CHG':0}
    options.update(option)
    p[0] = Var(p[2], p[4], options)

def p_var_nl_no_opt(p):
    '''var : DEFINE ID IS object AS NEUTRALLOSS SEMICOLON'''
    option = {'CHG': 0}
    p[0] = Var(p[2], p[4], option)


### OBJECT ###

def p_object_withAttr(p):
    '''object : withAttr
            | onlyObj'''
    p[0] = p[1]


### OBJECT/VARCONTENT ###

def p_onlyObj_ID_itemAccess(p):
    '''onlyObj : ID LBRACE ID RBRACE'''
    p[0] = Obj('p_onlyObj_ID_itemAccess', p[1:])


def p_onlyObj_ID(p):
    '''onlyObj : ID
                | list
                | varcontent'''
    p[0] = p[1]

def p_onlyObj_function1(p):
    '''onlyObj : ID LPAREN arguments RPAREN LBRACE ID RBRACE'''
    warnings.warn('undefined functionality', UserWarning)
    p[0] = Obj('p_onlyObj_function1', p[1:])


def p_onlyObj_function2(p):
    '''onlyObj : ID LPAREN arguments RPAREN'''
    p[0] = Func(p[1], p[3])


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


def p_optioncontent_cont(p):
    '''optioncontent : optioncontent COMMA optionentry'''
    p[1].update(p[3]) # they are dicts
    p[0] = p[1]

def p_optioncontent_obj(p):
    '''optioncontent : optionentry'''
    p[0] = p[1]


def p_optionentry_dbr(p):
    '''optionentry : DBR IS LPAREN object COMMA object RPAREN'''
    p[0] = {"dbr": (p[4], p[6])}


def p_optionentry_chg(p):
    '''optionentry : CHG IS INTEGER'''
    p[0] = {"chg": int(p[3])}


def p_optionentry_massrange(p):
    '''optionentry : MASSRANGE IS LPAREN object COMMA object RPAREN'''
    p[0] = {"massrange": (float(p[4]), float(p[6]))}


def p_optionentry_minocc(p):
    '''optionentry : MINOCC IS object'''
    p[0] = {"minocc", p[3]}


def p_optionentry_maxocc(p):
    '''optionentry : MAXOCC IS object'''
    p[0] = {"maxocc", p[3]}


def p_optionentry_TOLERANCE(p):
    '''optionentry : TOLERANCE IS tolerancetype'''
    p[0] = {"tolerance", p[3]}


def p_tolerancetype(p):
    '''tolerancetype : FLOAT DA
                     | FLOAT PPM
                     | INTEGER DA
                      | INTEGER RES
                     | INTEGER PPM'''

    if float(p[1]) <= 0.0:
        raise ValueError(
            "Tolerance value as given in the query '%s' can not be less than zero" % p.lexpos  )

    p[0] = (p[2].lower(), float(p[1]))


# --
# identification part
# see https://github.com/dabeaz/ply/blob/master/example/GardenSnake/GardenSnake.py
# https://github.com/dabeaz/ply/blob/master/example/calc/calc.py

def p_identificationSection(p):
    '''identificationSection : IDENTIFY marks '''
    p[0] = p[2]

def p_marks(p):
    '''marks : boolmarks'''
    p[0] = p[1]


def p_booleanterm_paren(p):
    '''boolmarks : LPAREN boolmarks RPAREN'''
    p[0] = p[2]

def p_boolmarks_not(p):
    '''boolmarks : NOT boolmarks'''

    p[0] = Evaluable('Not', p[2], None)


def p_boolmarks_or(p):
    '''boolmarks : boolmarks OR boolmarks'''
    p[0] = Evaluable('OR', p[1], p[3])


def p_boolmarks_and(p):
    '''boolmarks : boolmarks AND boolmarks'''
    p[0] = Evaluable('AND', p[1], p[3])

def p_boolmarks_if(p):
    # todo how is this differenc to the other if?
    '''boolmarks : boolmarks IFA boolmarks'''
    # p[0] = Evaluable('p_boolmarks_if', p[1:])
    raise NotImplementedError(' not sure what the {} should do'.format(p[2]))

def p_boolmarks_onlyif(p):
    '''boolmarks : boolmarks IFF boolmarks'''
    # p[0] = Evaluable('p_boolmarks_onlyif', p[1:])
    raise NotImplementedError(' not sure what the {} should do'.format(p[2]))


def p_boolmarks_arrow(p):
    '''boolmarks : boolmarks ARROW boolmarks'''
    # p[0] = Evaluable('p_boolmarks_arrow', p[1:])
    raise NotImplementedError(' not sure what the {} should do'.format(p[2]))


def p_boolmarks_le(p):
    '''boolmarks : boolmarks LE boolmarks'''
    # todo why is this here? its the  only one in the identificaion section
    p[0] = Evaluable(p[2], p[1], p[3])  # LE

def p_boolmarks_toScan(p):
    '''boolmarks : scan'''
    p[0] = p[1]

#---------------
# https://www.dabeaz.com/ply/PLYTalk.pdf
def p_suchthatSection(p):
    '''suchthatSection : SUCHTHAT booleanterm'''
    p[0] = p[2]

def p_booleanterm_logic(p):
    '''booleanterm : booleanterm AND booleanterm
                   | booleanterm OR  booleanterm'''

    p[0] = Evaluable(p[2], p[1], p[3])  #and or


def p_booleanterm_brackets(p):
    '''booleanterm : LPAREN booleanterm RPAREN'''
    p[0] = p[2]


def p_booleanterm_not(p):
    '''booleanterm : NOT booleanterm'''
    p[0] = Evaluable('NOT', p[2], None)


def p_booleanterm_expr(p):
    '''booleanterm : expr'''
    p[0] = p[1]

def p_booleanterm_expression(p):
    '''booleanterm : object'''
    p[0] = p[1]


def p_expr_multi(p):
    '''expr : expression EQUALS expression
            | expression GT expression
            | expression GE expression
            | expression LE expression
            | expression LT expression
            | expression NE expression
            | expression ARROWR expression  '''

    p[0] = Evaluable(p[2], p[1], p[3])


def p_expression_struct(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression '''
    p[0] = Evaluable(p[2], p[1], p[3])  # +- */

def p_expression_struct1(p):
    '''expression : MINUS expression %prec UMINUS'''
    p[0] = Evaluable('-', p[2], None)


def p_expression_attribute(p):
    '''expression : LPAREN expression RPAREN LBRACE ID RBRACE'''
    p[0] = Evaluable('p_expression_attribute', p[2], p[5])


def p_expression_paren(p):
    '''expression : LPAREN expression RPAREN'''
    p[0] = p[2]


def p_expression_content(p):
    '''expression : object'''
    p[0] = p[1]

### SCAN ###

def p_scan_object(p):
    '''scan : object IN scope'''
    p[0] = Evaluable('IN', p[1], p[3])


def p_scope(p):
    '''scope : MS1 MINUS
             | MS1 PLUS
             | MS2 PLUS
             | MS2 MINUS'''

    p[0] = p[1] + p[2]

#---
def p_reportSection(p):
    '''reportSection : REPORT reportContent'''
    p[0] = p[2]


def p_reportContent_cont(p):
    '''reportContent : reportContent reportItem'''
    p[0] = p[1] + [p[2]]


def p_reportContent_single(p):
    '''reportContent : reportItem'''
    p[0] = [p[1]]


def p_rContent(p):
    '''reportItem : ID IS STRING PERCENT STRING SEMICOLON
                | ID IS STRING PERCENT LPAREN arguments RPAREN SEMICOLON
                | ID IS expression SEMICOLON'''

    p[0] = ReportItem(p[1], p[3:-1])


def p_error(p):
    if not p:
        raise SyntaxError("SYNTAX ERROR at EOF")
    else:
        detail = "Syntax error at '%s' in file at position %s %s" % (p .value,p.lineno , p.lexpos)
        raise SyntaxError(detail)


parser = yacc.yacc(debug=0, optimize=1)

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
        FA1I = FA2.intensity;rrererrrrrrrrrrre

        FA2M = FA1.mass; 
        FA2C = "%d" % "((FA1.chemsc)[C])";
        FA2DB = "%d" % "((FA1.chemsc)[db] - 1.5)"; 
        FA2ERR = "%2.2f" % "(FA1.errppm)";
        FA2I = FA1.intensity;
        ;

    ################ end script ##################

    '''

    result = parser.parse(mfql, lexer = lexer, debug=0)
    expected = '''
    {'report': [ReportItem(id='PRM', p_values=[Obj(p_rule='p_withAttr_id', p_values=['pr', '.', 'mass'])]), ReportItem(id='EC', p_values=[Obj(p_rule='p_withAttr_id', p_values=['pr', '.', 'chemsc'])]), ReportItem(id='CLASS', p_values=['"PC"', '%', '"()"']), ReportItem(id='PRC', p_values=['"%d"', '%', '"((pr.chemsc)[C] - 9)"']), ReportItem(id='PRDB', p_values=['"%d"', '%', '"((pr.chemsc)[db] - 2.5)"']), ReportItem(id='PROH', p_values=['"%d"', '%', '"((pr.chemsc)[O] - 10)"']), ReportItem(id='SPECIE', p_values=['"PC %d:%d:%d"', '%', '"((pr.chemsc)[C]-9, pr.chemsc[db] - 2.5, pr.chemsc[O]-10)"']), ReportItem(id='PRERR', p_values=['"%2.2f"', '%', '"(pr.errppm)"']), ReportItem(id='PRI', p_values=[Obj(p_rule='p_withAttr_id', p_values=['pr', '.', 'intensity'])]), ReportItem(id='FA1M', p_values=[Obj(p_rule='p_withAttr_id', p_values=['FA2', '.', 'mass'])]), ReportItem(id='FA1C', p_values=['"%d"', '%', '"((FA2.chemsc)[C])"']), ReportItem(id='FA1DB', p_values=['"%d"', '%', '"((FA2.chemsc)[db] - 1.5)"']), ReportItem(id='FA1ERR', p_values=['"%2.2f"', '%', '"(FA2.errppm)"']), ReportItem(id='FA1I', p_values=[Obj(p_rule='p_withAttr_id', p_values=['FA2', '.', 'intensity'])]), ReportItem(id='FA2M', p_values=[Obj(p_rule='p_withAttr_id', p_values=['FA1', '.', 'mass'])]), ReportItem(id='FA2C', p_values=['"%d"', '%', '"((FA1.chemsc)[C])"']), ReportItem(id='FA2DB', p_values=['"%d"', '%', '"((FA1.chemsc)[db] - 1.5)"']), ReportItem(id='FA2ERR', p_values=['"%2.2f"', '%', '"(FA1.errppm)"']), ReportItem(id='FA2I', p_values=[Obj(p_rule='p_withAttr_id', p_values=['FA1', '.', 'intensity'])])], 'scriptname': 'PCFAS', 'identification': Evaluable(operation='AND', term_1=Evaluable(operation='AND', term_1=Evaluable(operation='IN', term_1='pr', term_2='MS1-'), term_2=Evaluable(operation='IN', term_1='FA1', term_2='MS2-')), term_2=Evaluable(operation='IN', term_1='FA2', term_2='MS2-')), 'variables': [Var(id='pr', object=ElementSeq(txt='C[30..80] H[40..300] O[10] N[1] P[1]'), Options={'dbr': (2.5, 14.5), 'chg': -1}), Var(id='FA1', object=ElementSeq(txt='C[10..40] H[20..100] O[2]'), Options={'dbr': (1.5, 7.5), 'chg': -1}), Var(id='FA2', object=ElementSeq(txt='C[10..40] H[20..100] O[2]'), Options={'dbr': (1.5, 7.5), 'chg': -1})], 'suchthat': Evaluable(operation='AND', term_1=Evaluable(operation='AND', term_1=Func(func='isOdd', on=[Obj(p_rule='p_withAttr_accessItem_', p_values=['pr', '.', 'chemsc', '[', 'H', ']'])]), term_2=Func(func='isOdd', on=[Evaluable(operation='*', term_1=Obj(p_rule='p_withAttr_accessItem_', p_values=['pr', '.', 'chemsc', '[', 'db', ']']), term_2=2)])), term_2=Evaluable(operation='==', term_1=Evaluable(operation='+', term_1=Evaluable(operation='+', term_1=Obj(p_rule='p_withAttr_id', p_values=['FA1', '.', 'chemsc']), term_2=Obj(p_rule='p_withAttr_id', p_values=['FA2', '.', 'chemsc'])), term_2=ElementSeq(txt='C9 H19 N1 O6 P1')), term_2=Obj(p_rule='p_withAttr_id', p_values=['pr', '.', 'chemsc'])))}
 '''
    expected = expected.strip()
    print(result)
    assert (str(result) == expected)
