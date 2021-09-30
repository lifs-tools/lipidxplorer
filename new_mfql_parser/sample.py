from mfql_Parser import parser
from mfql_lexer import lexer
from nearest import nearest
from spectra_tools import get_triggerScan, specta_df_fromCSV
from suchthat2df import suchthat2df
from var2df import var2df

expected_mfql_parse = """
    {'report': [ReportItem(id='PRM', p_values=[Obj(p_rule='p_withAttr_id', p_values=['pr', '.', 'mass'])]), ReportItem(id='EC', p_values=[Obj(p_rule='p_withAttr_id', p_values=['pr', '.', 'chemsc'])]), ReportItem(id='CLASS', p_values=['"PC"', '%', '"()"']), ReportItem(id='PRC', p_values=['"%d"', '%', '"((pr.chemsc)[C] - 9)"']), ReportItem(id='PRDB', p_values=['"%d"', '%', '"((pr.chemsc)[db] - 2.5)"']), ReportItem(id='PROH', p_values=['"%d"', '%', '"((pr.chemsc)[O] - 10)"']), ReportItem(id='SPECIE', p_values=['"PC %d:%d:%d"', '%', '"((pr.chemsc)[C]-9, pr.chemsc[db] - 2.5, pr.chemsc[O]-10)"']), ReportItem(id='PRERR', p_values=['"%2.2f"', '%', '"(pr.errppm)"']), ReportItem(id='PRI', p_values=[Obj(p_rule='p_withAttr_id', p_values=['pr', '.', 'intensity'])]), ReportItem(id='FA1M', p_values=[Obj(p_rule='p_withAttr_id', p_values=['FA2', '.', 'mass'])]), ReportItem(id='FA1C', p_values=['"%d"', '%', '"((FA2.chemsc)[C])"']), ReportItem(id='FA1DB', p_values=['"%d"', '%', '"((FA2.chemsc)[db] - 1.5)"']), ReportItem(id='FA1ERR', p_values=['"%2.2f"', '%', '"(FA2.errppm)"']), ReportItem(id='FA1I', p_values=[Obj(p_rule='p_withAttr_id', p_values=['FA2', '.', 'intensity'])]), ReportItem(id='FA2M', p_values=[Obj(p_rule='p_withAttr_id', p_values=['FA1', '.', 'mass'])]), ReportItem(id='FA2C', p_values=['"%d"', '%', '"((FA1.chemsc)[C])"']), ReportItem(id='FA2DB', p_values=['"%d"', '%', '"((FA1.chemsc)[db] - 1.5)"']), ReportItem(id='FA2ERR', p_values=['"%2.2f"', '%', '"(FA1.errppm)"']), ReportItem(id='FA2I', p_values=[Obj(p_rule='p_withAttr_id', p_values=['FA1', '.', 'intensity'])])], 'scriptname': 'PCFAS', 'identification': Evaluable(operation='AND', term_1=Evaluable(operation='AND', term_1=Evaluable(operation='IN', term_1='pr', term_2='MS1-'), term_2=Evaluable(operation='IN', term_1='FA1', term_2='MS2-')), term_2=Evaluable(operation='IN', term_1='FA2', term_2='MS2-')), 'variables': [Var(id='pr', object=ElementSeq(txt='C[30..80] H[40..300] O[10] N[1] P[1]'), Options={'dbr': (2.5, 14.5), 'chg': -1}), Var(id='FA1', object=ElementSeq(txt='C[10..40] H[20..100] O[2]'), Options={'dbr': (1.5, 7.5), 'chg': -1}), Var(id='FA2', object=ElementSeq(txt='C[10..40] H[20..100] O[2]'), Options={'dbr': (1.5, 7.5), 'chg': -1})], 'suchthat': Evaluable(operation='AND', term_1=Evaluable(operation='AND', term_1=Func(func='isOdd', on=[Obj(p_rule='p_withAttr_accessItem_', p_values=['pr', '.', 'chemsc', '[', 'H', ']'])]), term_2=Func(func='isOdd', on=[Evaluable(operation='*', term_1=Obj(p_rule='p_withAttr_accessItem_', p_values=['pr', '.', 'chemsc', '[', 'db', ']']), term_2=2)])), term_2=Evaluable(operation='==', term_1=Evaluable(operation='+', term_1=Evaluable(operation='+', term_1=Obj(p_rule='p_withAttr_id', p_values=['FA1', '.', 'chemsc']), term_2=Obj(p_rule='p_withAttr_id', p_values=['FA2', '.', 'chemsc'])), term_2=ElementSeq(txt='C9 H19 N1 O6 P1')), term_2=Obj(p_rule='p_withAttr_id', p_values=['pr', '.', 'chemsc'])))}
"""
expected_mfql_lex = """
LexToken(QUERYNAME,'QUERYNAME',5,143)^LexToken(IS,'=',5,153)^LexToken(ID,'PCFAS',5,155)^LexToken(SEMICOLON,';',5,160)^LexToken(DEFINE,'DEFINE',6,163)^LexToken(ID,'pr',6,170)^LexToken(IS,'=',6,173)^LexToken(SFSTRING,"'C[30..80] H[40..300] O[10] N[1] P[1]'",6,175)^LexToken(WITH,'WITH',6,214)^LexToken(DBR,'DBR',6,219)^LexToken(IS,'=',6,223)^LexToken(LPAREN,'(',6,225)^LexToken(FLOAT,'2.5',6,226)^LexToken(COMMA,',',6,229)^LexToken(FLOAT,'14.5',6,230)^LexToken(RPAREN,')',6,234)^LexToken(COMMA,',',6,235)^LexToken(CHG,'CHG',6,237)^LexToken(IS,'=',6,241)^LexToken(INTEGER,'-1',6,243)^LexToken(SEMICOLON,';',6,245)^LexToken(DEFINE,'DEFINE',7,248)^LexToken(ID,'FA1',7,255)^LexToken(IS,'=',7,259)^LexToken(SFSTRING,"'C[10..40] H[20..100] O[2]'",7,261)^LexToken(WITH,'WITH',7,289)^LexToken(DBR,'DBR',7,294)^LexToken(IS,'=',7,298)^LexToken(LPAREN,'(',7,300)^LexToken(FLOAT,'1.5',7,301)^LexToken(COMMA,',',7,304)^LexToken(FLOAT,'7.5',7,305)^LexToken(RPAREN,')',7,308)^LexToken(COMMA,',',7,309)^LexToken(CHG,'CHG',7,311)^LexToken(IS,'=',7,315)^LexToken(INTEGER,'-1',7,317)^LexToken(SEMICOLON,';',7,319)^LexToken(DEFINE,'DEFINE',8,322)^LexToken(ID,'FA2',8,329)^LexToken(IS,'=',8,333)^LexToken(SFSTRING,"'C[10..40] H[20..100] O[2]'",8,334)^LexToken(WITH,'WITH',8,362)^LexToken(DBR,'DBR',8,367)^LexToken(IS,'=',8,371)^LexToken(LPAREN,'(',8,373)^LexToken(FLOAT,'1.5',8,374)^LexToken(COMMA,',',8,377)^LexToken(FLOAT,'7.5',8,378)^LexToken(RPAREN,')',8,381)^LexToken(COMMA,',',8,382)^LexToken(CHG,'CHG',8,384)^LexToken(IS,'=',8,388)^LexToken(INTEGER,'-1',8,390)^LexToken(SEMICOLON,';',8,392)^LexToken(IDENTIFY,'IDENTIFY',10,395)^LexToken(ID,'pr',11,405)^LexToken(IN,'IN',11,408)^LexToken(MS1,'MS1',11,411)^LexToken(MINUS,'-',11,414)^LexToken(AND,'AND',11,416)^LexToken(ID,'FA1',12,421)^LexToken(IN,'IN',12,425)^LexToken(MS2,'MS2',12,428)^LexToken(MINUS,'-',12,431)^LexToken(AND,'AND',12,433)^LexToken(ID,'FA2',13,438)^LexToken(IN,'IN',13,442)^LexToken(MS2,'MS2',13,445)^LexToken(MINUS,'-',13,448)^LexToken(SUCHTHAT,'SUCHTHAT',15,451)^LexToken(ID,'isOdd',16,461)^LexToken(LPAREN,'(',16,466)^LexToken(ID,'pr',16,467)^LexToken(DOT,'.',16,469)^LexToken(ID,'chemsc',16,470)^LexToken(LBRACE,'[',16,476)^LexToken(ID,'H',16,477)^LexToken(RBRACE,']',16,478)^LexToken(RPAREN,')',16,479)^LexToken(AND,'AND',16,481)^LexToken(ID,'isOdd',17,486)^LexToken(LPAREN,'(',17,491)^LexToken(ID,'pr',17,492)^LexToken(DOT,'.',17,494)^LexToken(ID,'chemsc',17,495)^LexToken(LBRACE,'[',17,501)^LexToken(ID,'db',17,502)^LexToken(RBRACE,']',17,504)^LexToken(TIMES,'*',17,505)^LexToken(INTEGER,'2',17,506)^LexToken(RPAREN,')',17,507)^LexToken(AND,'AND',17,509)^LexToken(ID,'FA1',18,514)^LexToken(DOT,'.',18,517)^LexToken(ID,'chemsc',18,518)^LexToken(PLUS,'+',18,525)^LexToken(ID,'FA2',18,527)^LexToken(DOT,'.',18,530)^LexToken(ID,'chemsc',18,531)^LexToken(PLUS,'+',18,538)^LexToken(SFSTRING,"'C9 H19 N1 O6 P1'",18,540)^LexToken(EQUALS,'==',18,558)^LexToken(ID,'pr',18,561)^LexToken(DOT,'.',18,563)^LexToken(ID,'chemsc',18,564)^LexToken(REPORT,'REPORT',20,572)^LexToken(ID,'PRM',21,580)^LexToken(IS,'=',21,584)^LexToken(ID,'pr',21,586)^LexToken(DOT,'.',21,588)^LexToken(ID,'mass',21,589)^LexToken(SEMICOLON,';',21,593)^LexToken(ID,'EC',22,596)^LexToken(IS,'=',22,599)^LexToken(ID,'pr',22,601)^LexToken(DOT,'.',22,603)^LexToken(ID,'chemsc',22,604)^LexToken(SEMICOLON,';',22,610)^LexToken(ID,'CLASS',23,613)^LexToken(IS,'=',23,619)^LexToken(STRING,'"PC"',23,621)^LexToken(PERCENT,'%',23,626)^LexToken(STRING,'"()"',23,628)^LexToken(SEMICOLON,';',23,632)^LexToken(ID,'PRC',25,636)^LexToken(IS,'=',25,640)^LexToken(STRING,'"%d"',25,642)^LexToken(PERCENT,'%',25,647)^LexToken(STRING,'"((pr.chemsc)[C] - 9)"',25,649)^LexToken(SEMICOLON,';',25,671)^LexToken(ID,'PRDB',26,674)^LexToken(IS,'=',26,679)^LexToken(STRING,'"%d"',26,681)^LexToken(PERCENT,'%',26,686)^LexToken(STRING,'"((pr.chemsc)[db] - 2.5)"',26,688)^LexToken(SEMICOLON,';',26,713)^LexToken(ID,'PROH',27,716)^LexToken(IS,'=',27,721)^LexToken(STRING,'"%d"',27,723)^LexToken(PERCENT,'%',27,728)^LexToken(STRING,'"((pr.chemsc)[O] - 10)"',27,730)^LexToken(SEMICOLON,';',27,753)^LexToken(ID,'SPECIE',28,756)^LexToken(IS,'=',28,763)^LexToken(STRING,'"PC %d:%d:%d"',28,765)^LexToken(PERCENT,'%',28,779)^LexToken(STRING,'"((pr.chemsc)[C]-9, pr.chemsc[db] - 2.5, pr.chemsc[O]-10)"',28,781)^LexToken(SEMICOLON,';',28,839)^LexToken(ID,'PRERR',30,846)^LexToken(IS,'=',30,852)^LexToken(STRING,'"%2.2f"',30,854)^LexToken(PERCENT,'%',30,862)^LexToken(STRING,'"(pr.errppm)"',30,864)^LexToken(SEMICOLON,';',30,877)^LexToken(ID,'PRI',31,880)^LexToken(IS,'=',31,884)^LexToken(ID,'pr',31,886)^LexToken(DOT,'.',31,888)^LexToken(ID,'intensity',31,889)^LexToken(SEMICOLON,';',31,898)^LexToken(ID,'FA1M',33,902)^LexToken(IS,'=',33,907)^LexToken(ID,'FA2',33,909)^LexToken(DOT,'.',33,912)^LexToken(ID,'mass',33,913)^LexToken(SEMICOLON,';',33,917)^LexToken(ID,'FA1C',34,920)^LexToken(IS,'=',34,925)^LexToken(STRING,'"%d"',34,927)^LexToken(PERCENT,'%',34,932)^LexToken(STRING,'"((FA2.chemsc)[C])"',34,934)^LexToken(SEMICOLON,';',34,953)^LexToken(ID,'FA1DB',35,956)^LexToken(IS,'=',35,962)^LexToken(STRING,'"%d"',35,964)^LexToken(PERCENT,'%',35,969)^LexToken(STRING,'"((FA2.chemsc)[db] - 1.5)"',35,971)^LexToken(SEMICOLON,';',35,997)^LexToken(ID,'FA1ERR',36,1007)^LexToken(IS,'=',36,1014)^LexToken(STRING,'"%2.2f"',36,1016)^LexToken(PERCENT,'%',36,1024)^LexToken(STRING,'"(FA2.errppm)"',36,1026)^LexToken(SEMICOLON,';',36,1040)^LexToken(ID,'FA1I',37,1043)^LexToken(IS,'=',37,1048)^LexToken(ID,'FA2',37,1050)^LexToken(DOT,'.',37,1053)^LexToken(ID,'intensity',37,1054)^LexToken(SEMICOLON,';',37,1063)^LexToken(ID,'FA2M',39,1067)^LexToken(IS,'=',39,1072)^LexToken(ID,'FA1',39,1074)^LexToken(DOT,'.',39,1077)^LexToken(ID,'mass',39,1078)^LexToken(SEMICOLON,';',39,1082)^LexToken(ID,'FA2C',40,1085)^LexToken(IS,'=',40,1090)^LexToken(STRING,'"%d"',40,1092)^LexToken(PERCENT,'%',40,1097)^LexToken(STRING,'"((FA1.chemsc)[C])"',40,1099)^LexToken(SEMICOLON,';',40,1118)^LexToken(ID,'FA2DB',41,1121)^LexToken(IS,'=',41,1127)^LexToken(STRING,'"%d"',41,1129)^LexToken(PERCENT,'%',41,1134)^LexToken(STRING,'"((FA1.chemsc)[db] - 1.5)"',41,1136)^LexToken(SEMICOLON,';',41,1162)^LexToken(ID,'FA2ERR',42,1168)^LexToken(IS,'=',42,1175)^LexToken(STRING,'"%2.2f"',42,1177)^LexToken(PERCENT,'%',42,1185)^LexToken(STRING,'"(FA1.errppm)"',42,1187)^LexToken(SEMICOLON,';',42,1201)^LexToken(ID,'FA2I',43,1204)^LexToken(IS,'=',43,1209)^LexToken(ID,'FA1',43,1211)^LexToken(DOT,'.',43,1214)^LexToken(ID,'intensity',43,1215)^LexToken(SEMICOLON,';',43,1224)^LexToken(SEMICOLON,';',44,1227)
        """


if __name__ == "__main__":
    print("Testing the parser")
    print("read mfql")
    with open("sample.mfql", "rU") as f:
        mfql = f.read()

    print("lex mfql")
    lexer.input(mfql)

    tokens = []
    # Tokenize
    while True:
        tok = lexer.token()
        if not tok:
            break  # No more input
        tokens.append(tok)

    tokens = "^".join(map(str, tokens))

    print("check lex")
    assert tokens == expected_mfql_lex.strip()

    print("parse mfql")
    result = parser.parse(mfql)
    print("check mfql")
    assert str(result) == expected_mfql_parse.strip()

    print("get spectra")
    df = specta_df_fromCSV("spectra.csv")
    # todo redefine this
    sel_df = df.loc[
        df.filterLine.str.contains("888")
    ].copy()  # copy to avoid pandas warnings
    print("add pr-fa link")
    triggerScan, triggeredScans = get_triggerScan(df)
    print(sel_df.head())
    print("trigger scans")
    print([triggerScan[s] for s in sel_df.scanNum.unique()])

    print("get identifications")
    variables = result["variables"]
    var_dfs = {var.id: var2df(var) for var in variables}
    var_df = var_dfs[var_dfs.keys()[0]]
    print(var_df.head())

    var_dfs = {var.id: var2df(var) for var in variables}

    print("find closest masses")
    nearest_idx = nearest(sel_df.mz, var_df.m)
    nearest_val = var_df.m.iloc[nearest_idx].tolist()  # to list because index
    sel_df.loc[:, "nearest_idx"] = nearest_idx
    sel_df.loc[:, "nearest_val"] = nearest_val
    print(sel_df.head())

    print("do suchthat")
    suchthat = result["suchthat"]
    print(suchthat)
    suchthat2df(suchthat, var_dfs)
