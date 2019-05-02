from data_structs import Obj, ElementSeq


def getObj(object):
    return str(object)


def ElementSeq2df(elementSeq):
    return elementSeq.txt

def evaluate(evaluable):
    if isinstance(evaluable, Obj):
        return getObj(evaluable)
    elif isinstance(evaluable, ElementSeq):
        return ElementSeq2df(evaluable)

    # process like swagger, see python_mztab
    print('>>>>')
    print(evaluable.operation)
    print(evaluate(evaluable.term_1))
    print(evaluate(evaluable.term_2))
    print('<<<<')

    # eval() # use this to evaluate???
    res_df = None  # result is a dataframe with the evaluated results
    return res_df  # a list of masses and thir data

def suchthat2df(suchthat):
    return evaluate(suchthat)

# if __name__ == '__main__':
#     suchthat = Evaluable(operation='AND', term_1=Evaluable(operation='AND', term_1=Evaluable(operation='isOdd', term_1=[Obj(p_rule='pr', p_values=['.', 'chemsc', '[', 'H', ']'])], term_2=None), term_2=Evaluable(operation='isOdd', term_1=[Evaluable(operation='*', term_1=Obj(p_rule='pr', p_values=['.', 'chemsc', '[', 'db', ']']), term_2=2)], term_2=None)), term_2=Evaluable(operation='==', term_1=Evaluable(operation='+', term_1=Evaluable(operation='+', term_1=Obj(p_rule='p_withAttr_id', p_values=['FA1', '.', 'chemsc']), term_2=Obj(p_rule='p_withAttr_id', p_values=['FA2', '.', 'chemsc'])), term_2=ElementSeq(txt='C9 H19 N1 O6 P1')), term_2=Obj(p_rule='p_withAttr_id', p_values=['pr', '.', 'chemsc'])))
#
#     res = suchthat2df(suchthat)
#     print(res)
