import ply.lex as lex
import re

keywords = (
    'IDENTIFY', 'WITH', 'AND', 'OR',
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
    raise SyntaxError("In query  No underscore allowed.")

def t_error(t):
    if not ord(t.value[0]) == 13:
        raise SyntaxError("Illegal character %s (%s) in line %d" % (t.value[0], ord(t.value[0]), t.lexer.lineno))
    t.lexer.skip(1)

# build lexer

lexer = lex.lex(reflags = re.I, debug = 0, optimize = 1)


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

    lexer.input(mfql)

    expected = '''
        [LexToken(QUERYNAME,'QUERYNAME',6,160), LexToken(IS,'=',6,170), LexToken(ID,'PCFAS',6,172), LexToken(SEMICOLON,';',6,177), LexToken(DEFINE,'DEFINE',7,187), LexToken(ID,'pr',7,194), LexToken(IS,'=',7,197), LexToken(SFSTRING,"'C[30..80] H[40..300] O[10] N[1] P[1]'",7,199), LexToken(WITH,'WITH',7,238), LexToken(DBR,'DBR',7,243), LexToken(IS,'=',7,247), LexToken(LPAREN,'(',7,249), LexToken(FLOAT,'2.5',7,250), LexToken(COMMA,',',7,253), LexToken(FLOAT,'14.5',7,254), LexToken(RPAREN,')',7,258), LexToken(COMMA,',',7,259), LexToken(CHG,'CHG',7,261), LexToken(IS,'=',7,265), LexToken(INTEGER,'-1',7,267), LexToken(SEMICOLON,';',7,269), LexToken(DEFINE,'DEFINE',8,279), LexToken(ID,'FA1',8,286), LexToken(IS,'=',8,290), LexToken(SFSTRING,"'C[10..40] H[20..100] O[2]'",8,292), LexToken(WITH,'WITH',8,320), LexToken(DBR,'DBR',8,325), LexToken(IS,'=',8,329), LexToken(LPAREN,'(',8,331), LexToken(FLOAT,'1.5',8,332), LexToken(COMMA,',',8,335), LexToken(FLOAT,'7.5',8,336), LexToken(RPAREN,')',8,339), LexToken(COMMA,',',8,340), LexToken(CHG,'CHG',8,342), LexToken(IS,'=',8,346), LexToken(INTEGER,'-1',8,348), LexToken(SEMICOLON,';',8,350), LexToken(DEFINE,'DEFINE',9,360), LexToken(ID,'FA2',9,367), LexToken(IS,'=',9,371), LexToken(SFSTRING,"'C[10..40] H[20..100] O[2]'",9,372), LexToken(WITH,'WITH',9,400), LexToken(DBR,'DBR',9,405), LexToken(IS,'=',9,409), LexToken(LPAREN,'(',9,411), LexToken(FLOAT,'1.5',9,412), LexToken(COMMA,',',9,415), LexToken(FLOAT,'7.5',9,416), LexToken(RPAREN,')',9,419), LexToken(COMMA,',',9,420), LexToken(CHG,'CHG',9,422), LexToken(IS,'=',9,426), LexToken(INTEGER,'-1',9,428), LexToken(SEMICOLON,';',9,430), LexToken(IDENTIFY,'IDENTIFY',11,437), LexToken(ID,'pr',12,454), LexToken(IN,'IN',12,457), LexToken(MS1,'MS1',12,460), LexToken(MINUS,'-',12,463), LexToken(AND,'AND',12,465), LexToken(ID,'FA1',13,477), LexToken(IN,'IN',13,481), LexToken(MS2,'MS2',13,484), LexToken(MINUS,'-',13,487), LexToken(AND,'AND',13,489), LexToken(ID,'FA2',14,501), LexToken(IN,'IN',14,505), LexToken(MS2,'MS2',14,508), LexToken(MINUS,'-',14,511), LexToken(SUCHTHAT,'SUCHTHAT',16,518), LexToken(ID,'isOdd',17,535), LexToken(LPAREN,'(',17,540), LexToken(ID,'pr',17,541), LexToken(DOT,'.',17,543), LexToken(ID,'chemsc',17,544), LexToken(LBRACE,'[',17,550), LexToken(ID,'H',17,551), LexToken(RBRACE,']',17,552), LexToken(RPAREN,')',17,553), LexToken(AND,'AND',17,555), LexToken(ID,'isOdd',18,567), LexToken(LPAREN,'(',18,572), LexToken(ID,'pr',18,573), LexToken(DOT,'.',18,575), LexToken(ID,'chemsc',18,576), LexToken(LBRACE,'[',18,582), LexToken(ID,'db',18,583), LexToken(RBRACE,']',18,585), LexToken(TIMES,'*',18,586), LexToken(INTEGER,'2',18,587), LexToken(RPAREN,')',18,588), LexToken(AND,'AND',18,590), LexToken(ID,'FA1',19,602), LexToken(DOT,'.',19,605), LexToken(ID,'chemsc',19,606), LexToken(PLUS,'+',19,613), LexToken(ID,'FA2',19,615), LexToken(DOT,'.',19,618), LexToken(ID,'chemsc',19,619), LexToken(PLUS,'+',19,626), LexToken(SFSTRING,"'C9 H19 N1 O6 P1'",19,628), LexToken(EQUALS,'==',19,646), LexToken(ID,'pr',19,649), LexToken(DOT,'.',19,651), LexToken(ID,'chemsc',19,652), LexToken(REPORT,'REPORT',21,664), LexToken(ID,'PRM',22,679), LexToken(IS,'=',22,683), LexToken(ID,'pr',22,685), LexToken(DOT,'.',22,687), LexToken(ID,'mass',22,688), LexToken(SEMICOLON,';',22,692), LexToken(ID,'EC',23,702), LexToken(IS,'=',23,705), LexToken(ID,'pr',23,707), LexToken(DOT,'.',23,709), LexToken(ID,'chemsc',23,710), LexToken(SEMICOLON,';',23,716), LexToken(ID,'CLASS',24,726), LexToken(IS,'=',24,732), LexToken(STRING,'"PC"',24,734), LexToken(PERCENT,'%',24,739), LexToken(STRING,'"()"',24,741), LexToken(SEMICOLON,';',24,745), LexToken(ID,'PRC',26,756), LexToken(IS,'=',26,760), LexToken(STRING,'"%d"',26,762), LexToken(PERCENT,'%',26,767), LexToken(STRING,'"((pr.chemsc)[C] - 9)"',26,769), LexToken(SEMICOLON,';',26,791), LexToken(ID,'PRDB',27,801), LexToken(IS,'=',27,806), LexToken(STRING,'"%d"',27,808), LexToken(PERCENT,'%',27,813), LexToken(STRING,'"((pr.chemsc)[db] - 2.5)"',27,815), LexToken(SEMICOLON,';',27,840), LexToken(ID,'PROH',28,850), LexToken(IS,'=',28,855), LexToken(STRING,'"%d"',28,857), LexToken(PERCENT,'%',28,862), LexToken(STRING,'"((pr.chemsc)[O] - 10)"',28,864), LexToken(SEMICOLON,';',28,887), LexToken(ID,'SPECIE',29,897), LexToken(IS,'=',29,904), LexToken(STRING,'"PC %d:%d:%d"',29,906), LexToken(PERCENT,'%',29,920), LexToken(STRING,'"((pr.chemsc)[C]-9, pr.chemsc[db] - 2.5, pr.chemsc[O]-10)"',29,922), LexToken(SEMICOLON,';',29,980), LexToken(ID,'PRERR',31,995), LexToken(IS,'=',31,1001), LexToken(STRING,'"%2.2f"',31,1003), LexToken(PERCENT,'%',31,1011), LexToken(STRING,'"(pr.errppm)"',31,1013), LexToken(SEMICOLON,';',31,1026), LexToken(ID,'PRI',32,1036), LexToken(IS,'=',32,1040), LexToken(ID,'pr',32,1042), LexToken(DOT,'.',32,1044), LexToken(ID,'intensity',32,1045), LexToken(SEMICOLON,';',32,1054), LexToken(ID,'FA1M',34,1065), LexToken(IS,'=',34,1070), LexToken(ID,'FA2',34,1072), LexToken(DOT,'.',34,1075), LexToken(ID,'mass',34,1076), LexToken(SEMICOLON,';',34,1080), LexToken(ID,'FA1C',35,1091), LexToken(IS,'=',35,1096), LexToken(STRING,'"%d"',35,1098), LexToken(PERCENT,'%',35,1103), LexToken(STRING,'"((FA2.chemsc)[C])"',35,1105), LexToken(SEMICOLON,';',35,1124), LexToken(ID,'FA1DB',36,1134), LexToken(IS,'=',36,1140), LexToken(STRING,'"%d"',36,1142), LexToken(PERCENT,'%',36,1147), LexToken(STRING,'"((FA2.chemsc)[db] - 1.5)"',36,1149), LexToken(SEMICOLON,';',36,1175), LexToken(ID,'FA1ERR',37,1190), LexToken(IS,'=',37,1197), LexToken(STRING,'"%2.2f"',37,1199), LexToken(PERCENT,'%',37,1207), LexToken(STRING,'"(FA2.errppm)"',37,1209), LexToken(SEMICOLON,';',37,1223), LexToken(ID,'FA1I',38,1233), LexToken(IS,'=',38,1238), LexToken(ID,'FA2',38,1240), LexToken(DOT,'.',38,1243), LexToken(ID,'intensity',38,1244), LexToken(SEMICOLON,';',38,1253), LexToken(ID,'FA2M',40,1264), LexToken(IS,'=',40,1269), LexToken(ID,'FA1',40,1271), LexToken(DOT,'.',40,1274), LexToken(ID,'mass',40,1275), LexToken(SEMICOLON,';',40,1279), LexToken(ID,'FA2C',41,1290), LexToken(IS,'=',41,1295), LexToken(STRING,'"%d"',41,1297), LexToken(PERCENT,'%',41,1302), LexToken(STRING,'"((FA1.chemsc)[C])"',41,1304), LexToken(SEMICOLON,';',41,1323), LexToken(ID,'FA2DB',42,1333), LexToken(IS,'=',42,1339), LexToken(STRING,'"%d"',42,1341), LexToken(PERCENT,'%',42,1346), LexToken(STRING,'"((FA1.chemsc)[db] - 1.5)"',42,1348), LexToken(SEMICOLON,';',42,1374), LexToken(ID,'FA2ERR',43,1389), LexToken(IS,'=',43,1396), LexToken(STRING,'"%2.2f"',43,1398), LexToken(PERCENT,'%',43,1406), LexToken(STRING,'"(FA1.errppm)"',43,1408), LexToken(SEMICOLON,';',43,1422), LexToken(ID,'FA2I',44,1432), LexToken(IS,'=',44,1437), LexToken(ID,'FA1',44,1439), LexToken(DOT,'.',44,1442), LexToken(ID,'intensity',44,1443), LexToken(SEMICOLON,';',44,1452), LexToken(SEMICOLON,';',45,1462)]
    '''
    expected = expected.strip()

    result = []
    # Tokenize
    while True:
        tok = lexer.token()
        if not tok:
            break  # No more input
        result.append(tok)

    assert (expected == str(result).strip())
