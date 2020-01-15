import warnings

from data_structs import Obj, ElementSeq, Evaluable, Func

def txt(evaluable):
    if type(evaluable) in [int,float]:
        res = str(evaluable)
    elif isinstance(evaluable, list):
        if len(evaluable) == 1 :
            res = txt(evaluable[0])
    elif isinstance(evaluable, Evaluable):
        res = f'{txt(evaluable.term_1)} {evaluable.operation} {txt(evaluable.term_2)}'
    elif isinstance(evaluable, Func):
        if evaluable.func == 'isOdd':
            res = f'{txt(evaluable.on)} % 2 == 0'
    elif isinstance(evaluable, Obj):
        if evaluable.p_rule == 'p_withAttr_accessItem_':
            if evaluable.p_values[2] == 'chemsc':
                res = f'{evaluable.p_values[0]}_{evaluable.p_values[-2]}'
        elif evaluable.p_rule == 'p_withAttr_id':
            if evaluable.p_values[2] == 'chemsc':
                res = f'{evaluable.p_values[0]}_m'
    elif isinstance(evaluable, ElementSeq):
        res = '999'
    else:
        warnings.warn(f'could not evaluate {evaluable}')
        res = str(evaluable)
    
    if res == None: warnings.warn(f'did not evaluate {evaluable}')
    return res

def suchthat2txt(suchthat):
    return txt(suchthat)


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
    res = suchthat2txt(suchthat)
    print(res)
