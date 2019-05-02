import warnings

from data_structs import Obj, ElementSeq, Evaluable, Func


def funcCall(func):
    # todo make this better from the parser
    operation = func.func
    warnings.warn('only evaluates first item in list', DeprecationWarning)
    on = evaluate(func.on[0])
    return 'do {} on {}'.format(operation, on)

def getObj(object):
    return str(object)


def ElementSeq2df(elementSeq):
    return elementSeq.txt


def evaluate(evaluable):
    if isinstance(evaluable, Obj):
        return getObj(evaluable)
    elif isinstance(evaluable, ElementSeq):
        return ElementSeq2df(evaluable)
    elif isinstance(evaluable, Func):
        return funcCall(evaluable)
    elif isinstance(evaluable, Evaluable):
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


if __name__ == '__main__':
    suchthat = Evaluable(operation='AND', term_1=Evaluable(operation='AND', term_1=Func(func='isOdd', on=[
        Obj(p_rule='p_withAttr_accessItem_', p_values=['pr', '.', 'chemsc', '[', 'H', ']'])]), term_2=Func(func='isOdd',
                                                                                                           on=[
                                                                                                               Evaluable(
                                                                                                                   operation='*',
                                                                                                                   term_1=Obj(
                                                                                                                       p_rule='p_withAttr_accessItem_',
                                                                                                                       p_values=[
                                                                                                                           'pr',
                                                                                                                           '.',
                                                                                                                           'chemsc',
                                                                                                                           '[',
                                                                                                                           'db',
                                                                                                                           ']']),
                                                                                                                   term_2=2)])),
                         term_2=Evaluable(operation='==', term_1=Evaluable(operation='+',
                                                                           term_1=Evaluable(operation='+', term_1=Obj(
                                                                               p_rule='p_withAttr_id',
                                                                               p_values=['FA1', '.', 'chemsc']),
                                                                                            term_2=Obj(
                                                                                                p_rule='p_withAttr_id',
                                                                                                p_values=['FA2', '.',
                                                                                                          'chemsc'])),
                                                                           term_2=ElementSeq(txt='C9 H19 N1 O6 P1')),
                                          term_2=Obj(p_rule='p_withAttr_id', p_values=['pr', '.', 'chemsc'])))
    res = suchthat2df(suchthat)
    print(res)
