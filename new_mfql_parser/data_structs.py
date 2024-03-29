from collections import namedtuple

mfql_dict = {}
Var = namedtuple("Var", "id object Options")
Obj = namedtuple("Obj", "p_rule p_values")
Func = namedtuple("Func", "func on")
ElementSeq = namedtuple("ElementSeq", "txt")
Evaluable = namedtuple("Evaluable", "operation term_1 term_2")
ReportItem = namedtuple("ReportItem", "id p_values")
