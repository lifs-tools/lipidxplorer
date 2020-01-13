# from http://www.dalkescientific.com/writings/NBN/parsing_with_ply.html


# A grammar for chemical equations like "H2O", "CH3COOH" and "H2SO4"
# Uses David Beazley's PLY parser.
# Implements two functions: count the total number of atoms in the equation and
#   count the number of times each element occurs in the equation.

import ply.lex as lex

tokens = (
    "SYMBOL",
    "NUM",
    "DOT",
    'LPAREN',
    'RPAREN'
)

t_SYMBOL = (
    r"C[laroudsemf]?|Os?|N[eaibdpos]?|S[icernbmg]?|P[drmtboau]?|"
    r"H[eofgas]?|A[lrsgutcm]|B[eraik]?|Dy|E[urs]|F[erm]?|G[aed]|"
    r"I[nr]?|Kr?|L[iaur]|M[gnodt]|R[buhenaf]|T[icebmalh]|"
    r"U|V|W|Xe|Yb?|Z[nr]")
t_DOT  = r'\.'
t_LPAREN  = r'\['
t_RPAREN  = r'\]'

def t_NUM(t):
    r"\d+"
    t.value = int(t.value)
    return t

t_ignore  = ' \t'

def t_error(t):
    raise TypeError("Unknown text '%s'" % (t.value,))


lexer = lex.lex()

data = '''C[41..49] H[30..200] O[2] N[1]'''
 
 # Give the lexer some input
lexer.input(data)
 
 # Tokenize
while True:
    tok = lexer.token()
    if not tok: 
        break      # No more input
    print(tok)