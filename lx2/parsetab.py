
# parsetab.py
# This file is automatically generated. Do not edit.
# pylint: disable=W,C,R
_tabversion = '3.10'

_lr_method = 'LALR'

_lr_signature = 'leftORleftANDIFFIFAARROWleftEQUALSNEnonassocLTGTGELEARROWRleftPLUSMINUSleftTIMESDIVIDEleftNOTrightUMINUSAND ARROW ARROWR AS CHG COMMA DA DBR DEFINE DIVIDE DOT EQUALS FLOAT GE GT ID IDENTIFY IFA IFF IN INTEGER IS LBRACE LBRACKET LE LPAREN LT LTUPLE MASSRANGE MAXOCC MINOCC MINUS MS1 MS2 NE NEUTRALLOSS NOT OR PERCENT PLUS PPM QUERYNAME RBRACE RBRACKET REPORT RES RPAREN RTUPLE SEMICOLON SFSTRING STRING SUCHTHAT TIMES TOLERANCE WITHprogram  : script  SEMICOLON\n                | script script : scriptname variablesSection identificationSection suchthatSection reportSectionscript : scriptname variablesSection identificationSection reportSectionscriptname : QUERYNAME IS ID SEMICOLONvariablesSection : variablesvariables : variables varvariables : varvar : DEFINE ID IS object WITH optioncontent SEMICOLONvar : DEFINE ID IS object SEMICOLONvar : DEFINE ID IS object WITH  optioncontent AS NEUTRALLOSS SEMICOLONvar : DEFINE ID IS object AS NEUTRALLOSS SEMICOLONobject : withAttr\n            | onlyObjonlyObj : ID LBRACE ID RBRACEonlyObj : ID\n                | list\n                | varcontentonlyObj : ID LPAREN arguments RPAREN LBRACE ID RBRACEonlyObj : ID LPAREN arguments RPARENwithAttr : ID DOT ID LBRACE ID RBRACEwithAttr : ID DOT ID LBRACE STRING RBRACEwithAttr : ID DOT IDwithAttr : varcontent DOT IDwithAttr : list DOT IDarguments : expressionarguments : arguments COMMA expressionlist : LBRACKET listcontent RBRACKETlistcontent : listcontent COMMA objectlistcontent : objectvarcontent : tolerancetypevarcontent : FLOATvarcontent : INTEGER\n                  | PLUS INTEGERvarcontent : MINUS INTEGERvarcontent : STRINGvarcontent : SFSTRINGoptioncontent : optioncontent COMMA optionentryoptioncontent : optionentryoptionentry : DBR IS LPAREN object COMMA object RPARENoptionentry : CHG IS INTEGERoptionentry : MASSRANGE IS LPAREN object COMMA object RPARENoptionentry : MINOCC IS objectoptionentry : MAXOCC IS objectoptionentry : TOLERANCE IS tolerancetypetolerancetype : FLOAT DA\n                     | FLOAT PPM\n                     | INTEGER DA\n                      | INTEGER RES\n                     | INTEGER PPMidentificationSection : IDENTIFY marks marks : boolmarksboolmarks : LPAREN boolmarks RPARENboolmarks : NOT boolmarksboolmarks : boolmarks OR boolmarksboolmarks : boolmarks AND boolmarksboolmarks : boolmarks IFA boolmarksboolmarks : boolmarks IFF boolmarksboolmarks : boolmarks ARROW boolmarksboolmarks : boolmarks LE boolmarksboolmarks : scansuchthatSection : SUCHTHAT booleantermbooleanterm : booleanterm AND booleanterm\n                   | booleanterm OR  booleantermbooleanterm : LPAREN booleanterm RPARENbooleanterm : NOT booleantermbooleanterm : exprbooleanterm : objectexpr : expression EQUALS expression\n            | expression GT expression\n            | expression GE expression\n            | expression LE expression\n            | expression LT expression\n            | expression NE expression\n            | expression ARROWR expression  expression : expression PLUS expression\n                  | expression MINUS expression\n                  | expression TIMES expression\n                  | expression DIVIDE expression expression : MINUS expression %prec UMINUSexpression : LPAREN expression RPAREN LBRACE ID RBRACEexpression : LPAREN expression RPARENexpression : objectscan : object IN scopescope : MS1 MINUS\n             | MS1 PLUS\n             | MS2 PLUS\n             | MS2 MINUSreportSection : REPORT reportContentreportContent : reportContent reportItemreportContent : reportItemreportItem : ID IS STRING PERCENT LTUPLE arguments RTUPLE SEMICOLON\n                | ID IS STRING PERCENT LPAREN arguments RPAREN SEMICOLON\n                | ID IS expression SEMICOLON'
    
_lr_action_items = {'QUERYNAME':([0,],[4,]),'$end':([1,2,5,17,41,49,50,96,157,199,200,],[0,-2,-1,-4,-3,-89,-91,-90,-94,-92,-93,]),'SEMICOLON':([2,15,17,26,27,28,29,30,31,32,33,34,37,41,49,50,66,67,68,69,70,71,72,75,92,93,95,96,108,112,113,114,122,130,131,132,133,135,136,142,143,146,147,154,157,175,176,178,179,181,183,184,185,188,191,195,196,199,200,203,204,],[5,40,-4,-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,-3,-89,-91,-46,-47,-48,-49,-50,-34,-35,117,-80,-33,-83,-90,-23,-24,-25,-28,-82,-76,-77,-78,-79,-36,157,-15,-20,162,-39,171,-94,-21,-22,192,-38,-41,-43,-44,-45,-81,-19,199,200,-92,-93,-40,-42,]),'DEFINE':([3,7,8,13,40,117,162,171,192,],[9,9,-8,-7,-5,-10,-9,-12,-11,]),'IS':([4,14,51,148,149,150,151,152,153,],[10,39,97,165,166,167,168,169,170,]),'IDENTIFY':([6,7,8,13,117,162,171,192,],[12,-6,-8,-7,-10,-9,-12,-11,]),'ID':([9,10,12,18,19,22,23,38,39,43,44,48,49,50,52,53,54,55,56,57,61,62,63,64,65,76,77,81,82,83,84,85,86,87,88,89,90,91,94,96,97,115,141,144,155,157,160,168,169,173,174,180,182,197,198,199,200,],[14,15,28,28,51,28,28,28,28,28,28,28,51,-91,28,28,28,28,28,28,108,109,28,112,113,28,28,28,28,28,28,28,28,28,28,28,28,28,28,-90,28,28,158,28,172,-94,177,28,28,28,28,28,28,28,28,-92,-93,]),'SUCHTHAT':([11,20,21,24,59,98,99,100,101,102,103,104,105,137,138,139,140,],[18,-51,-52,-61,-54,-55,-56,-57,-58,-59,-60,-53,-84,-85,-86,-87,-88,]),'REPORT':([11,16,20,21,24,26,27,28,29,30,31,32,33,34,37,42,45,46,59,66,67,68,69,70,71,80,92,93,95,98,99,100,101,102,103,104,105,108,112,113,114,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,137,138,139,140,142,143,175,176,188,191,],[19,19,-51,-52,-61,-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,-62,-67,-68,-54,-46,-47,-48,-49,-50,-34,-66,-80,-33,-83,-55,-56,-57,-58,-59,-60,-53,-84,-23,-24,-25,-28,-63,-64,-65,-82,-69,-70,-71,-72,-73,-74,-75,-76,-77,-78,-79,-85,-86,-87,-88,-15,-20,-21,-22,-81,-19,]),'LPAREN':([12,18,22,23,28,43,44,48,52,53,54,55,56,57,63,76,77,81,82,83,84,85,86,87,88,89,90,91,94,97,144,156,165,167,173,174,],[22,43,22,22,63,43,43,94,22,22,22,22,22,22,94,43,43,94,94,94,94,94,94,94,94,94,94,94,94,94,94,174,180,182,94,94,]),'NOT':([12,18,22,23,43,44,52,53,54,55,56,57,76,77,],[23,44,23,23,44,44,23,23,23,23,23,23,44,44,]),'FLOAT':([12,18,22,23,38,39,43,44,48,52,53,54,55,56,57,63,76,77,81,82,83,84,85,86,87,88,89,90,91,94,97,115,144,168,169,170,173,174,180,182,197,198,],[33,33,33,33,33,33,33,33,33,33,33,33,33,33,33,33,33,33,33,33,33,33,33,33,33,33,33,33,33,33,33,33,33,33,33,186,33,33,33,33,33,33,]),'INTEGER':([12,18,22,23,35,36,38,39,43,44,48,52,53,54,55,56,57,63,76,77,81,82,83,84,85,86,87,88,89,90,91,94,97,115,144,166,168,169,170,173,174,180,182,197,198,],[34,34,34,34,71,72,34,34,34,34,93,34,34,34,34,34,34,34,34,34,34,34,34,34,34,34,34,34,34,34,34,34,34,34,34,181,34,34,187,34,34,34,34,34,34,]),'PLUS':([12,18,22,23,26,27,28,29,30,31,32,33,34,37,38,39,43,44,46,47,48,52,53,54,55,56,57,63,66,67,68,69,70,71,76,77,79,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,97,106,107,108,111,112,113,114,115,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,142,143,144,161,168,169,173,174,175,176,180,182,188,191,197,198,],[35,35,35,35,-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,35,35,35,35,-83,88,35,35,35,35,35,35,35,35,-46,-47,-48,-49,-50,-34,35,35,88,35,35,35,35,35,35,35,35,35,35,35,-80,-33,35,-83,35,138,139,-23,88,-24,-25,-28,35,-82,88,88,88,88,88,88,88,-76,-77,-78,-79,88,-36,88,-15,-20,35,88,35,35,35,35,-21,-22,35,35,-81,-19,35,35,]),'MINUS':([12,18,22,23,26,27,28,29,30,31,32,33,34,37,38,39,43,44,46,47,48,52,53,54,55,56,57,63,66,67,68,69,70,71,76,77,79,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,97,106,107,108,111,112,113,114,115,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,142,143,144,161,168,169,173,174,175,176,180,182,188,191,197,198,],[36,48,36,36,-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,36,36,48,48,-83,89,48,36,36,36,36,36,36,48,-46,-47,-48,-49,-50,-34,48,48,89,48,48,48,48,48,48,48,48,48,48,48,-80,-33,48,-83,48,137,140,-23,89,-24,-25,-28,36,-82,89,89,89,89,89,89,89,-76,-77,-78,-79,89,-36,89,-15,-20,48,89,36,36,48,48,-21,-22,36,36,-81,-19,36,36,]),'STRING':([12,18,22,23,38,39,43,44,48,52,53,54,55,56,57,63,76,77,81,82,83,84,85,86,87,88,89,90,91,94,97,115,141,144,168,169,173,174,180,182,197,198,],[29,29,29,29,29,29,29,29,29,29,29,29,29,29,29,29,29,29,29,29,29,29,29,29,29,29,29,29,29,29,135,29,159,29,29,29,29,29,29,29,29,29,]),'SFSTRING':([12,18,22,23,38,39,43,44,48,52,53,54,55,56,57,63,76,77,81,82,83,84,85,86,87,88,89,90,91,94,97,115,144,168,169,173,174,180,182,197,198,],[37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,37,]),'LBRACKET':([12,18,22,23,38,39,43,44,48,52,53,54,55,56,57,63,76,77,81,82,83,84,85,86,87,88,89,90,91,94,97,115,144,168,169,173,174,180,182,197,198,],[38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,38,]),'OR':([21,24,26,27,28,29,30,31,32,33,34,37,42,45,46,58,59,66,67,68,69,70,71,78,80,92,93,95,98,99,100,101,102,103,104,105,108,112,113,114,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,137,138,139,140,142,143,175,176,188,191,],[52,-61,-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,77,-67,-68,52,-54,-46,-47,-48,-49,-50,-34,77,-66,-80,-33,-83,-55,-56,-57,-58,-59,-60,-53,-84,-23,-24,-25,-28,-63,-64,-65,-82,-69,-70,-71,-72,-73,-74,-75,-76,-77,-78,-79,-85,-86,-87,-88,-15,-20,-21,-22,-81,-19,]),'AND':([21,24,26,27,28,29,30,31,32,33,34,37,42,45,46,58,59,66,67,68,69,70,71,78,80,92,93,95,98,99,100,101,102,103,104,105,108,112,113,114,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,137,138,139,140,142,143,175,176,188,191,],[53,-61,-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,76,-67,-68,53,-54,-46,-47,-48,-49,-50,-34,76,-66,-80,-33,-83,53,-56,-57,-58,-59,-60,-53,-84,-23,-24,-25,-28,-63,76,-65,-82,-69,-70,-71,-72,-73,-74,-75,-76,-77,-78,-79,-85,-86,-87,-88,-15,-20,-21,-22,-81,-19,]),'IFA':([21,24,58,59,98,99,100,101,102,103,104,105,137,138,139,140,],[54,-61,54,-54,54,-56,-57,-58,-59,-60,-53,-84,-85,-86,-87,-88,]),'IFF':([21,24,58,59,98,99,100,101,102,103,104,105,137,138,139,140,],[55,-61,55,-54,55,-56,-57,-58,-59,-60,-53,-84,-85,-86,-87,-88,]),'ARROW':([21,24,58,59,98,99,100,101,102,103,104,105,137,138,139,140,],[56,-61,56,-54,56,-56,-57,-58,-59,-60,-53,-84,-85,-86,-87,-88,]),'LE':([21,24,26,27,28,29,30,31,32,33,34,37,46,47,58,59,66,67,68,69,70,71,79,92,93,95,98,99,100,101,102,103,104,105,108,112,113,114,122,130,131,132,133,137,138,139,140,142,143,175,176,188,191,],[57,-61,-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,-83,84,57,-54,-46,-47,-48,-49,-50,-34,84,-80,-33,-83,57,57,57,57,57,None,-53,-84,-23,-24,-25,-28,-82,-76,-77,-78,-79,-85,-86,-87,-88,-15,-20,-21,-22,-81,-19,]),'RPAREN':([24,26,27,28,29,30,31,32,33,34,37,45,46,58,59,66,67,68,69,70,71,72,78,79,80,92,93,95,98,99,100,101,102,103,104,105,108,110,111,112,113,114,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,137,138,139,140,142,143,161,175,176,188,190,191,201,202,],[-61,-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,-67,-68,104,-54,-46,-47,-48,-49,-50,-34,-35,121,122,-66,-80,-33,-83,-55,-56,-57,-58,-59,-60,-53,-84,-23,143,-26,-24,-25,-28,-63,-64,-65,-82,-69,-70,-71,-72,-73,-74,-75,-76,-77,-78,-79,122,-85,-86,-87,-88,-15,-20,-27,-21,-22,-81,196,-19,203,204,]),'IN':([25,26,27,28,29,30,31,32,33,34,37,66,67,68,69,70,71,72,108,112,113,114,142,143,175,176,191,],[60,-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,-46,-47,-48,-49,-50,-34,-35,-23,-24,-25,-28,-15,-20,-21,-22,-19,]),'EQUALS':([26,27,28,29,30,31,32,33,34,37,46,47,66,67,68,69,70,71,79,92,93,95,108,112,113,114,122,130,131,132,133,142,143,175,176,188,191,],[-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,-83,81,-46,-47,-48,-49,-50,-34,81,-80,-33,-83,-23,-24,-25,-28,-82,-76,-77,-78,-79,-15,-20,-21,-22,-81,-19,]),'GT':([26,27,28,29,30,31,32,33,34,37,46,47,66,67,68,69,70,71,79,92,93,95,108,112,113,114,122,130,131,132,133,142,143,175,176,188,191,],[-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,-83,82,-46,-47,-48,-49,-50,-34,82,-80,-33,-83,-23,-24,-25,-28,-82,-76,-77,-78,-79,-15,-20,-21,-22,-81,-19,]),'GE':([26,27,28,29,30,31,32,33,34,37,46,47,66,67,68,69,70,71,79,92,93,95,108,112,113,114,122,130,131,132,133,142,143,175,176,188,191,],[-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,-83,83,-46,-47,-48,-49,-50,-34,83,-80,-33,-83,-23,-24,-25,-28,-82,-76,-77,-78,-79,-15,-20,-21,-22,-81,-19,]),'LT':([26,27,28,29,30,31,32,33,34,37,46,47,66,67,68,69,70,71,79,92,93,95,108,112,113,114,122,130,131,132,133,142,143,175,176,188,191,],[-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,-83,85,-46,-47,-48,-49,-50,-34,85,-80,-33,-83,-23,-24,-25,-28,-82,-76,-77,-78,-79,-15,-20,-21,-22,-81,-19,]),'NE':([26,27,28,29,30,31,32,33,34,37,46,47,66,67,68,69,70,71,79,92,93,95,108,112,113,114,122,130,131,132,133,142,143,175,176,188,191,],[-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,-83,86,-46,-47,-48,-49,-50,-34,86,-80,-33,-83,-23,-24,-25,-28,-82,-76,-77,-78,-79,-15,-20,-21,-22,-81,-19,]),'ARROWR':([26,27,28,29,30,31,32,33,34,37,46,47,66,67,68,69,70,71,79,92,93,95,108,112,113,114,122,130,131,132,133,142,143,175,176,188,191,],[-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,-83,87,-46,-47,-48,-49,-50,-34,87,-80,-33,-83,-23,-24,-25,-28,-82,-76,-77,-78,-79,-15,-20,-21,-22,-81,-19,]),'TIMES':([26,27,28,29,30,31,32,33,34,37,46,47,66,67,68,69,70,71,79,92,93,95,108,111,112,113,114,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,142,143,161,175,176,188,191,],[-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,-83,90,-46,-47,-48,-49,-50,-34,90,-80,-33,-83,-23,90,-24,-25,-28,-82,90,90,90,90,90,90,90,90,90,-78,-79,90,-36,90,-15,-20,90,-21,-22,-81,-19,]),'DIVIDE':([26,27,28,29,30,31,32,33,34,37,46,47,66,67,68,69,70,71,79,92,93,95,108,111,112,113,114,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,142,143,161,175,176,188,191,],[-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,-83,91,-46,-47,-48,-49,-50,-34,91,-80,-33,-83,-23,91,-24,-25,-28,-82,91,91,91,91,91,91,91,91,91,-78,-79,91,-36,91,-15,-20,91,-21,-22,-81,-19,]),'RBRACKET':([26,27,28,29,30,31,32,33,34,37,66,67,68,69,70,71,72,73,74,108,112,113,114,142,143,145,175,176,191,],[-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,-46,-47,-48,-49,-50,-34,-35,114,-30,-23,-24,-25,-28,-15,-20,-29,-21,-22,-19,]),'COMMA':([26,27,28,29,30,31,32,33,34,37,66,67,68,69,70,71,72,73,74,92,93,95,108,110,111,112,113,114,122,130,131,132,133,142,143,145,146,147,161,175,176,179,181,183,184,185,188,189,190,191,193,194,203,204,],[-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,-46,-47,-48,-49,-50,-34,-35,115,-30,-80,-33,-83,-23,144,-26,-24,-25,-28,-82,-76,-77,-78,-79,-15,-20,-29,164,-39,-27,-21,-22,-38,-41,-43,-44,-45,-81,144,144,-19,197,198,-40,-42,]),'WITH':([26,27,28,29,30,31,32,33,34,37,66,67,68,69,70,71,72,75,108,112,113,114,142,143,175,176,191,],[-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,-46,-47,-48,-49,-50,-34,-35,116,-23,-24,-25,-28,-15,-20,-21,-22,-19,]),'AS':([26,27,28,29,30,31,32,33,34,37,66,67,68,69,70,71,72,75,108,112,113,114,142,143,146,147,175,176,179,181,183,184,185,191,203,204,],[-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,-46,-47,-48,-49,-50,-34,-35,118,-23,-24,-25,-28,-15,-20,163,-39,-21,-22,-38,-41,-43,-44,-45,-19,-40,-42,]),'RTUPLE':([26,27,28,29,30,31,32,33,34,37,66,67,68,69,70,71,92,93,95,108,111,112,113,114,122,130,131,132,133,142,143,161,175,176,188,189,191,],[-13,-14,-16,-36,-18,-17,-31,-32,-33,-37,-46,-47,-48,-49,-50,-34,-80,-33,-83,-23,-26,-24,-25,-28,-82,-76,-77,-78,-79,-15,-20,-27,-21,-22,-81,195,-19,]),'DOT':([28,29,30,31,32,33,34,37,66,67,68,69,70,71,72,93,114,135,],[61,-36,64,65,-31,-32,-33,-37,-46,-47,-48,-49,-50,-34,-35,-33,-28,-36,]),'LBRACE':([28,108,122,143,],[62,141,155,160,]),'DA':([33,34,93,186,187,],[66,68,68,66,68,]),'PPM':([33,34,93,186,187,],[67,70,70,67,70,]),'RES':([34,93,187,],[69,69,69,]),'MS1':([60,],[106,]),'MS2':([60,],[107,]),'RBRACE':([109,158,159,172,177,],[142,175,176,188,191,]),'DBR':([116,164,],[148,148,]),'CHG':([116,164,],[149,149,]),'MASSRANGE':([116,164,],[150,150,]),'MINOCC':([116,164,],[151,151,]),'MAXOCC':([116,164,],[152,152,]),'TOLERANCE':([116,164,],[153,153,]),'NEUTRALLOSS':([118,163,],[154,178,]),'PERCENT':([135,],[156,]),'LTUPLE':([156,],[173,]),}

_lr_action = {}
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = {}
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'program':([0,],[1,]),'script':([0,],[2,]),'scriptname':([0,],[3,]),'variablesSection':([3,],[6,]),'variables':([3,],[7,]),'var':([3,7,],[8,13,]),'identificationSection':([6,],[11,]),'suchthatSection':([11,],[16,]),'reportSection':([11,16,],[17,41,]),'marks':([12,],[20,]),'boolmarks':([12,22,23,52,53,54,55,56,57,],[21,58,59,98,99,100,101,102,103,]),'scan':([12,22,23,52,53,54,55,56,57,],[24,24,24,24,24,24,24,24,24,]),'object':([12,18,22,23,38,39,43,44,48,52,53,54,55,56,57,63,76,77,81,82,83,84,85,86,87,88,89,90,91,94,97,115,144,168,169,173,174,180,182,197,198,],[25,46,25,25,74,75,46,46,95,25,25,25,25,25,25,95,46,46,95,95,95,95,95,95,95,95,95,95,95,95,95,145,95,183,184,95,95,193,194,201,202,]),'withAttr':([12,18,22,23,38,39,43,44,48,52,53,54,55,56,57,63,76,77,81,82,83,84,85,86,87,88,89,90,91,94,97,115,144,168,169,173,174,180,182,197,198,],[26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,]),'onlyObj':([12,18,22,23,38,39,43,44,48,52,53,54,55,56,57,63,76,77,81,82,83,84,85,86,87,88,89,90,91,94,97,115,144,168,169,173,174,180,182,197,198,],[27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,]),'varcontent':([12,18,22,23,38,39,43,44,48,52,53,54,55,56,57,63,76,77,81,82,83,84,85,86,87,88,89,90,91,94,97,115,144,168,169,173,174,180,182,197,198,],[30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,]),'list':([12,18,22,23,38,39,43,44,48,52,53,54,55,56,57,63,76,77,81,82,83,84,85,86,87,88,89,90,91,94,97,115,144,168,169,173,174,180,182,197,198,],[31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,]),'tolerancetype':([12,18,22,23,38,39,43,44,48,52,53,54,55,56,57,63,76,77,81,82,83,84,85,86,87,88,89,90,91,94,97,115,144,168,169,170,173,174,180,182,197,198,],[32,32,32,32,32,32,32,32,32,32,32,32,32,32,32,32,32,32,32,32,32,32,32,32,32,32,32,32,32,32,32,32,32,32,32,185,32,32,32,32,32,32,]),'booleanterm':([18,43,44,76,77,],[42,78,80,119,120,]),'expr':([18,43,44,76,77,],[45,45,45,45,45,]),'expression':([18,43,44,48,63,76,77,81,82,83,84,85,86,87,88,89,90,91,94,97,144,173,174,],[47,79,47,92,111,47,47,123,124,125,126,127,128,129,130,131,132,133,134,136,161,111,111,]),'reportContent':([19,],[49,]),'reportItem':([19,49,],[50,96,]),'listcontent':([38,],[73,]),'scope':([60,],[105,]),'arguments':([63,173,174,],[110,189,190,]),'optioncontent':([116,],[146,]),'optionentry':([116,164,],[147,179,]),}

_lr_goto = {}
for _k, _v in _lr_goto_items.items():
   for _x, _y in zip(_v[0], _v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = {}
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> program","S'",1,None,None,None),
  ('program -> script SEMICOLON','program',2,'p_program','mfql_Parser.py',23),
  ('program -> script','program',1,'p_program','mfql_Parser.py',24),
  ('script -> scriptname variablesSection identificationSection suchthatSection reportSection','script',5,'p_script','mfql_Parser.py',30),
  ('script -> scriptname variablesSection identificationSection reportSection','script',4,'p_script1','mfql_Parser.py',39),
  ('scriptname -> QUERYNAME IS ID SEMICOLON','scriptname',4,'p_scriptname','mfql_Parser.py',51),
  ('variablesSection -> variables','variablesSection',1,'p_variablesSection','mfql_Parser.py',58),
  ('variables -> variables var','variables',2,'p_variables_loop','mfql_Parser.py',62),
  ('variables -> var','variables',1,'p_variables_endloop','mfql_Parser.py',67),
  ('var -> DEFINE ID IS object WITH optioncontent SEMICOLON','var',7,'p_var_normal','mfql_Parser.py',72),
  ('var -> DEFINE ID IS object SEMICOLON','var',5,'p_var_no_opts','mfql_Parser.py',76),
  ('var -> DEFINE ID IS object WITH optioncontent AS NEUTRALLOSS SEMICOLON','var',9,'p_var_nl','mfql_Parser.py',81),
  ('var -> DEFINE ID IS object AS NEUTRALLOSS SEMICOLON','var',7,'p_var_nl_no_opt','mfql_Parser.py',88),
  ('object -> withAttr','object',1,'p_object_withAttr','mfql_Parser.py',96),
  ('object -> onlyObj','object',1,'p_object_withAttr','mfql_Parser.py',97),
  ('onlyObj -> ID LBRACE ID RBRACE','onlyObj',4,'p_onlyObj_ID_itemAccess','mfql_Parser.py',104),
  ('onlyObj -> ID','onlyObj',1,'p_onlyObj_ID','mfql_Parser.py',109),
  ('onlyObj -> list','onlyObj',1,'p_onlyObj_ID','mfql_Parser.py',110),
  ('onlyObj -> varcontent','onlyObj',1,'p_onlyObj_ID','mfql_Parser.py',111),
  ('onlyObj -> ID LPAREN arguments RPAREN LBRACE ID RBRACE','onlyObj',7,'p_onlyObj_function1','mfql_Parser.py',115),
  ('onlyObj -> ID LPAREN arguments RPAREN','onlyObj',4,'p_onlyObj_function2','mfql_Parser.py',121),
  ('withAttr -> ID DOT ID LBRACE ID RBRACE','withAttr',6,'p_withAttr_accessItem_','mfql_Parser.py',126),
  ('withAttr -> ID DOT ID LBRACE STRING RBRACE','withAttr',6,'p_withAttr_accessItem_string','mfql_Parser.py',131),
  ('withAttr -> ID DOT ID','withAttr',3,'p_withAttr_id','mfql_Parser.py',136),
  ('withAttr -> varcontent DOT ID','withAttr',3,'p_withAttr_varcontent','mfql_Parser.py',141),
  ('withAttr -> list DOT ID','withAttr',3,'p_withAttr_list','mfql_Parser.py',146),
  ('arguments -> expression','arguments',1,'p_arguments_single','mfql_Parser.py',151),
  ('arguments -> arguments COMMA expression','arguments',3,'p_arguments_multi','mfql_Parser.py',156),
  ('list -> LBRACKET listcontent RBRACKET','list',3,'p_list','mfql_Parser.py',163),
  ('listcontent -> listcontent COMMA object','listcontent',3,'p_listcontent_cont','mfql_Parser.py',168),
  ('listcontent -> object','listcontent',1,'p_listcontent_obj','mfql_Parser.py',173),
  ('varcontent -> tolerancetype','varcontent',1,'p_varcontent_tolerance','mfql_Parser.py',180),
  ('varcontent -> FLOAT','varcontent',1,'p_varcontent_float','mfql_Parser.py',185),
  ('varcontent -> INTEGER','varcontent',1,'p_varcontent_integer','mfql_Parser.py',190),
  ('varcontent -> PLUS INTEGER','varcontent',2,'p_varcontent_integer','mfql_Parser.py',191),
  ('varcontent -> MINUS INTEGER','varcontent',2,'p_varcontent_integer_min','mfql_Parser.py',196),
  ('varcontent -> STRING','varcontent',1,'p_varcontent_string','mfql_Parser.py',201),
  ('varcontent -> SFSTRING','varcontent',1,'p_varcontent_sfstring','mfql_Parser.py',206),
  ('optioncontent -> optioncontent COMMA optionentry','optioncontent',3,'p_optioncontent_cont','mfql_Parser.py',215),
  ('optioncontent -> optionentry','optioncontent',1,'p_optioncontent_obj','mfql_Parser.py',220),
  ('optionentry -> DBR IS LPAREN object COMMA object RPAREN','optionentry',7,'p_optionentry_dbr','mfql_Parser.py',225),
  ('optionentry -> CHG IS INTEGER','optionentry',3,'p_optionentry_chg','mfql_Parser.py',230),
  ('optionentry -> MASSRANGE IS LPAREN object COMMA object RPAREN','optionentry',7,'p_optionentry_massrange','mfql_Parser.py',235),
  ('optionentry -> MINOCC IS object','optionentry',3,'p_optionentry_minocc','mfql_Parser.py',240),
  ('optionentry -> MAXOCC IS object','optionentry',3,'p_optionentry_maxocc','mfql_Parser.py',245),
  ('optionentry -> TOLERANCE IS tolerancetype','optionentry',3,'p_optionentry_TOLERANCE','mfql_Parser.py',250),
  ('tolerancetype -> FLOAT DA','tolerancetype',2,'p_tolerancetype','mfql_Parser.py',255),
  ('tolerancetype -> FLOAT PPM','tolerancetype',2,'p_tolerancetype','mfql_Parser.py',256),
  ('tolerancetype -> INTEGER DA','tolerancetype',2,'p_tolerancetype','mfql_Parser.py',257),
  ('tolerancetype -> INTEGER RES','tolerancetype',2,'p_tolerancetype','mfql_Parser.py',258),
  ('tolerancetype -> INTEGER PPM','tolerancetype',2,'p_tolerancetype','mfql_Parser.py',259),
  ('identificationSection -> IDENTIFY marks','identificationSection',2,'p_identificationSection','mfql_Parser.py',274),
  ('marks -> boolmarks','marks',1,'p_marks','mfql_Parser.py',278),
  ('boolmarks -> LPAREN boolmarks RPAREN','boolmarks',3,'p_booleanterm_paren','mfql_Parser.py',283),
  ('boolmarks -> NOT boolmarks','boolmarks',2,'p_boolmarks_not','mfql_Parser.py',287),
  ('boolmarks -> boolmarks OR boolmarks','boolmarks',3,'p_boolmarks_or','mfql_Parser.py',293),
  ('boolmarks -> boolmarks AND boolmarks','boolmarks',3,'p_boolmarks_and','mfql_Parser.py',298),
  ('boolmarks -> boolmarks IFA boolmarks','boolmarks',3,'p_boolmarks_if','mfql_Parser.py',302),
  ('boolmarks -> boolmarks IFF boolmarks','boolmarks',3,'p_boolmarks_onlyif','mfql_Parser.py',308),
  ('boolmarks -> boolmarks ARROW boolmarks','boolmarks',3,'p_boolmarks_arrow','mfql_Parser.py',314),
  ('boolmarks -> boolmarks LE boolmarks','boolmarks',3,'p_boolmarks_le','mfql_Parser.py',320),
  ('boolmarks -> scan','boolmarks',1,'p_boolmarks_toScan','mfql_Parser.py',325),
  ('suchthatSection -> SUCHTHAT booleanterm','suchthatSection',2,'p_suchthatSection','mfql_Parser.py',331),
  ('booleanterm -> booleanterm AND booleanterm','booleanterm',3,'p_booleanterm_logic','mfql_Parser.py',335),
  ('booleanterm -> booleanterm OR booleanterm','booleanterm',3,'p_booleanterm_logic','mfql_Parser.py',336),
  ('booleanterm -> LPAREN booleanterm RPAREN','booleanterm',3,'p_booleanterm_brackets','mfql_Parser.py',342),
  ('booleanterm -> NOT booleanterm','booleanterm',2,'p_booleanterm_not','mfql_Parser.py',347),
  ('booleanterm -> expr','booleanterm',1,'p_booleanterm_expr','mfql_Parser.py',352),
  ('booleanterm -> object','booleanterm',1,'p_booleanterm_expression','mfql_Parser.py',356),
  ('expr -> expression EQUALS expression','expr',3,'p_expr_multi','mfql_Parser.py',361),
  ('expr -> expression GT expression','expr',3,'p_expr_multi','mfql_Parser.py',362),
  ('expr -> expression GE expression','expr',3,'p_expr_multi','mfql_Parser.py',363),
  ('expr -> expression LE expression','expr',3,'p_expr_multi','mfql_Parser.py',364),
  ('expr -> expression LT expression','expr',3,'p_expr_multi','mfql_Parser.py',365),
  ('expr -> expression NE expression','expr',3,'p_expr_multi','mfql_Parser.py',366),
  ('expr -> expression ARROWR expression','expr',3,'p_expr_multi','mfql_Parser.py',367),
  ('expression -> expression PLUS expression','expression',3,'p_expression_struct','mfql_Parser.py',373),
  ('expression -> expression MINUS expression','expression',3,'p_expression_struct','mfql_Parser.py',374),
  ('expression -> expression TIMES expression','expression',3,'p_expression_struct','mfql_Parser.py',375),
  ('expression -> expression DIVIDE expression','expression',3,'p_expression_struct','mfql_Parser.py',376),
  ('expression -> MINUS expression','expression',2,'p_expression_struct1','mfql_Parser.py',380),
  ('expression -> LPAREN expression RPAREN LBRACE ID RBRACE','expression',6,'p_expression_attribute','mfql_Parser.py',385),
  ('expression -> LPAREN expression RPAREN','expression',3,'p_expression_paren','mfql_Parser.py',390),
  ('expression -> object','expression',1,'p_expression_content','mfql_Parser.py',395),
  ('scan -> object IN scope','scan',3,'p_scan_object','mfql_Parser.py',401),
  ('scope -> MS1 MINUS','scope',2,'p_scope','mfql_Parser.py',406),
  ('scope -> MS1 PLUS','scope',2,'p_scope','mfql_Parser.py',407),
  ('scope -> MS2 PLUS','scope',2,'p_scope','mfql_Parser.py',408),
  ('scope -> MS2 MINUS','scope',2,'p_scope','mfql_Parser.py',409),
  ('reportSection -> REPORT reportContent','reportSection',2,'p_reportSection','mfql_Parser.py',415),
  ('reportContent -> reportContent reportItem','reportContent',2,'p_reportContent_cont','mfql_Parser.py',420),
  ('reportContent -> reportItem','reportContent',1,'p_reportContent_single','mfql_Parser.py',425),
  ('reportItem -> ID IS STRING PERCENT LTUPLE arguments RTUPLE SEMICOLON','reportItem',8,'p_rContent','mfql_Parser.py',430),
  ('reportItem -> ID IS STRING PERCENT LPAREN arguments RPAREN SEMICOLON','reportItem',8,'p_rContent','mfql_Parser.py',431),
  ('reportItem -> ID IS expression SEMICOLON','reportItem',4,'p_rContent','mfql_Parser.py',432),
]
