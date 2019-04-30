from collections import namedtuple

mfql_dict = {}
Var = namedtuple('Var', 'id object Options')
Obj = namedtuple('Obj', 'p_rule p_values')
ElementSeq = namedtuple('ElementSeq', 'txt')
Evaluable = namedtuple('Evaluable', 'p_method , p_values')
ReportItem = namedtuple('ReportItem', 'id p_values')

