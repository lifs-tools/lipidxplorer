from collections import namedtuple

mfql_dict = {}
Var = namedtuple('Var', 'id object Options')
Obj = namedtuple('Obj', 'p_rule p_values')
Func = namedtuple('Func', 'func on')
ElementSeq = namedtuple('ElementSeq', 'txt')
Evaluable = namedtuple('Evaluable', 'operation term_1 term_2')
ReportItem = namedtuple('ReportItem', 'id p_values is_PCT_format')
ReportCol = namedtuple('ReportCol', 'col_name col_fortmat, col_eval_txt')


