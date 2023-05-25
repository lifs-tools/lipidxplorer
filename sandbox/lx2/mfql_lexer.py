import ply.lex as lex
import re

keywords = (
    "IDENTIFY",
    "WITH",
    "AND",
    "OR",
    "TOLERANCE",
    "MINOCC",
    "MAXOCC",
    "MASSRANGE",
    "DBR",
    "CHG",
    "NOT",
    "DA",
    "PPM",
    "RES",
    "DEFINE",
    "IN",
    "MS1",
    "MS2",
    "REPORT",
    "SUCHTHAT",
    "QUERYNAME",
    "AS",
    "NEUTRALLOSS",
)

# list of token names
tokens = keywords + (
    "EQUALS",
    "IS",
    "PLUS",
    "MINUS",
    "TIMES",
    "DIVIDE",
    "LPAREN",
    "RPAREN",
    "LT",
    "LE",
    "GT",
    "GE",
    "IFA",
    "IFF",
    "NE",
    "COMMA",
    "SEMICOLON",
    "FLOAT",
    "STRING",
    "ID",
    "INTEGER",
    "DOT",
    "PERCENT",
    "LBRACE",
    "RBRACE",
    "LBRACKET",
    "RBRACKET",
    "SFSTRING",
    "ARROW",
    "ARROWR",
    "LTUPLE",
    "RTUPLE",
)

# https://stackoverflow.com/questions/2910338/python-yacc-lexer-token-priority
def t_LTUPLE(t):
    r"\"\("
    return t


def t_RTUPLE(t):
    r"\)\" "
    return t


def t_ID(t):
    r"[a-zA-Z$][a-zA-Z$0-9]*"
    if t.value in keywords or t.value.upper() in keywords:
        t.type = t.value.upper()
    return t


# regular expression rules for simple tokens
t_EQUALS = r"=="
t_IS = r"="
t_PLUS = r"\+"
t_MINUS = r"-"
t_TIMES = r"\*"
t_DIVIDE = r"/"
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_LBRACE = r"\["
t_RBRACE = r"\]"
t_LBRACKET = r"\{"
t_RBRACKET = r"\}"
t_LE = r"<="
t_NE = r"<>"
t_LT = r"<"
t_GE = r">="
t_GT = r">"
t_ARROW = r"->"
t_ARROWR = r"<~"
t_IFA = r"=>"
t_IFF = r"<=>"
t_COMMA = r"\,"
t_SEMICOLON = r";"
t_FLOAT = r"(\+|-)?((\d*\.\d+)(E[\+-]?\d+)?|([1-9]\d*E[\+-]?\d+))"
t_INTEGER = r"(\+|-)?\d+"
t_STRING = r"\".*?\""
t_SFSTRING = r"\'.*?\'"
t_DOT = r"\."
t_PERCENT = r"%"


def t_comment(t):
    r"[ ]*\043[^\n]*"
    t.lexer.lineno += t.value.count("\n")
    pass


def t_WS(t):
    r"[ \t]+"
    pass


def t_WS_NL(t):
    r"(([ \t]*)\n)"
    t.lexer.lineno += t.value.count("\n")
    pass


def t_UNDERSCORE(t):
    r"_"
    raise SyntaxError("In query  No underscore allowed.")


def t_error(t):
    if not ord(t.value[0]) == 13:
        raise SyntaxError(
            "Illegal character %s (%s) in line %d"
            % (t.value[0], ord(t.value[0]), t.lexer.lineno)
        )
    t.lexer.skip(1)


# build lexer

lexer = lex.lex(debug=False, optimize=True)
