# lextab.py. This file automatically created by PLY (version 3.11). Don't edit!
_tabversion = "3.10"
_lextokens = set(
    (
        "AND",
        "ARROW",
        "ARROWR",
        "AS",
        "CHG",
        "COMMA",
        "DA",
        "DBR",
        "DEFINE",
        "DIVIDE",
        "DOT",
        "EQUALS",
        "FLOAT",
        "GE",
        "GT",
        "ID",
        "IDENTIFY",
        "IFA",
        "IFF",
        "IN",
        "INTEGER",
        "IS",
        "LBRACE",
        "LBRACKET",
        "LE",
        "LPAREN",
        "LT",
        "LTUPLE",
        "MASSRANGE",
        "MAXOCC",
        "MINOCC",
        "MINUS",
        "MS1",
        "MS2",
        "NE",
        "NEUTRALLOSS",
        "NOT",
        "OR",
        "PERCENT",
        "PLUS",
        "PPM",
        "QUERYNAME",
        "RBRACE",
        "RBRACKET",
        "REPORT",
        "RES",
        "RPAREN",
        "RTUPLE",
        "SEMICOLON",
        "SFSTRING",
        "STRING",
        "SUCHTHAT",
        "TIMES",
        "TOLERANCE",
        "WITH",
    )
)
_lexreflags = 64
_lexliterals = ""
_lexstateinfo = {"INITIAL": "inclusive"}
_lexstatere = {
    "INITIAL": [
        (
            '(?P<t_LTUPLE>\\"\\()|(?P<t_RTUPLE>\\)\\")|(?P<t_ID>[a-zA-Z$][a-zA-Z$0-9]*)|(?P<t_comment>[ ]*\\043[^\\n]*)|(?P<t_WS>[ \\t]+)|(?P<t_WS_NL>(([ \\t]*)\\n))|(?P<t_UNDERSCORE>_)|(?P<t_FLOAT>(\\+|-)?((\\d*\\.\\d+)(E[\\+-]?\\d+)?|([1-9]\\d*E[\\+-]?\\d+)))|(?P<t_INTEGER>(\\+|-)?\\d+)|(?P<t_STRING>\\".*?\\")|(?P<t_SFSTRING>\\\'.*?\\\')|(?P<t_IFF><=>)|(?P<t_EQUALS>==)|(?P<t_PLUS>\\+)|(?P<t_TIMES>\\*)|(?P<t_LPAREN>\\()|(?P<t_RPAREN>\\))|(?P<t_LBRACE>\\[)|(?P<t_RBRACE>\\])|(?P<t_LBRACKET>\\{)|(?P<t_RBRACKET>\\})|(?P<t_LE><=)|(?P<t_NE><>)|(?P<t_GE>>=)|(?P<t_ARROW>->)|(?P<t_ARROWR><~)|(?P<t_IFA>=>)|(?P<t_COMMA>\\,)|(?P<t_DOT>\\.)|(?P<t_IS>=)|(?P<t_MINUS>-)|(?P<t_DIVIDE>/)|(?P<t_LT><)|(?P<t_GT>>)|(?P<t_SEMICOLON>;)|(?P<t_PERCENT>%)',
            [
                None,
                ("t_LTUPLE", "LTUPLE"),
                ("t_RTUPLE", "RTUPLE"),
                ("t_ID", "ID"),
                ("t_comment", "comment"),
                ("t_WS", "WS"),
                ("t_WS_NL", "WS_NL"),
                None,
                None,
                ("t_UNDERSCORE", "UNDERSCORE"),
                (None, "FLOAT"),
                None,
                None,
                None,
                None,
                None,
                (None, "INTEGER"),
                None,
                (None, "STRING"),
                (None, "SFSTRING"),
                (None, "IFF"),
                (None, "EQUALS"),
                (None, "PLUS"),
                (None, "TIMES"),
                (None, "LPAREN"),
                (None, "RPAREN"),
                (None, "LBRACE"),
                (None, "RBRACE"),
                (None, "LBRACKET"),
                (None, "RBRACKET"),
                (None, "LE"),
                (None, "NE"),
                (None, "GE"),
                (None, "ARROW"),
                (None, "ARROWR"),
                (None, "IFA"),
                (None, "COMMA"),
                (None, "DOT"),
                (None, "IS"),
                (None, "MINUS"),
                (None, "DIVIDE"),
                (None, "LT"),
                (None, "GT"),
                (None, "SEMICOLON"),
                (None, "PERCENT"),
            ],
        )
    ]
}
_lexstateignore = {"INITIAL": ""}
_lexstateerrorf = {"INITIAL": "t_error"}
_lexstateeoff = {}
