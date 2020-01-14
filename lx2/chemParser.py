# from http://www.dalkescientific.com/writings/NBN/parsing_with_ply.html


# A grammar for chemical equations like "H2O", "CH3COOH" and "H2SO4"
# Uses David Beazley's PLY parser.
# Implements two functions: count the total number of atoms in the equation and
#   count the number of times each element occurs in the equation.

import ply.lex as lex
import ply.yacc as yacc

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

def p_chemical_equation(p):
    """
    chemical_equation :
    chemical_equation : species_list
    """
    if len(p) == 1:
        # the empty string means there are no atomic symbols
        p[0] = {}
    else:
        p[0] = p[1]

def p_species_list(p):
    "species_list :  species_list species"
    p[1].update(p[2])
    p[0] = p[1]

def p_species(p):
    "species_list : species"
    p[0] = p[1]

def p_single_species(p):
    """
    species : SYMBOL
    species : SYMBOL NUM
    species : SYMBOL LPAREN NUM RPAREN
    species : SYMBOL LPAREN NUM DOT DOT NUM RPAREN
    """
    if len(p) == 2:
        p[0] = {p[1]: (1,1)}
    elif len(p) == 3:
        p[0] = {p[1]: (p[2],p[2])}
    elif len(p) == 5:
        p[0] = {p[1]: (p[3],p[3])}
    elif len(p) == 8:
        p[0] = {p[1]: (p[3],p[6])}

def p_error(p):
    raise TypeError("unknown text at %r" % (p.value,))

parser = yacc.yacc(debug=0, optimize=1)

def txt2dict(txt):
    return parser.parse(txt)