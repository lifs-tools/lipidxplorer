from data_structs import Evaluable, Obj, ElementSeq


def evaluate(evaluable):
    # process like swagger, see python_mztab

    operation, term_1, term_2 = evaluable
    print('>>>>')
    print(operation)
    print(evaluate(term_1))
    print(evaluate(term_2))
    print('<<<<')

    # eval() # use this to evaluate???
    res_df = None  # result is a dataframe with the evaluated results
    return res_df  # a list of masses and thir data

def suchthat2df(suchthat):
    return evaluate(str(suchthat))


if __name__ == '__main__':
    suchthat = Evaluable(operation='AND', term_1=Evaluable(operation='AND', term_1=Obj(p_rule='p_onlyObj_function2',
                                                                                       p_values=['isOdd', '(', [Obj(
                                                                                           p_rule='p_withAttr_accessItem_',
                                                                                           p_values=['pr', '.',
                                                                                                     'chemsc', '[', 'H',
                                                                                                     ']'])], ')']),
                                                           term_2=Obj(p_rule='p_onlyObj_function2',
                                                                      p_values=['isOdd', '(', [Evaluable(operation='*',
                                                                                                         term_1=Obj(
                                                                                                             p_rule='p_withAttr_accessItem_',
                                                                                                             p_values=[
                                                                                                                 'pr',
                                                                                                                 '.',
                                                                                                                 'chemsc',
                                                                                                                 '[',
                                                                                                                 'db',
                                                                                                                 ']']),
                                                                                                         term_2=2)],
                                                                                ')'])), term_2=Evaluable(operation='==',
                                                                                                         term_1=Evaluable(
                                                                                                             operation='+',
                                                                                                             term_1=Evaluable(
                                                                                                                 operation='+',
                                                                                                                 term_1=Obj(
                                                                                                                     p_rule='p_withAttr_id',
                                                                                                                     p_values=[
                                                                                                                         'FA1',
                                                                                                                         '.',
                                                                                                                         'chemsc']),
                                                                                                                 term_2=Obj(
                                                                                                                     p_rule='p_withAttr_id',
                                                                                                                     p_values=[
                                                                                                                         'FA2',
                                                                                                                         '.',
                                                                                                                         'chemsc'])),
                                                                                                             term_2=ElementSeq(
                                                                                                                 txt='C9 H19 N1 O6 P1')),
                                                                                                         term_2=Obj(
                                                                                                             p_rule='p_withAttr_id',
                                                                                                             p_values=[
                                                                                                                 'pr',
                                                                                                                 '.',
                                                                                                                 'chemsc'])))

    res = suchthat2df(suchthat)
    print(res)
