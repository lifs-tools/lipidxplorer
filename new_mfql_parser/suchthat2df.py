from data_structs import Evaluable, Obj, ElementSeq


def evaluate(evaluable):
    # process like swagger, see python_mztab

    p_method, p_values = evaluable
    print(p_method)




    # eval() # use this to evaluate???
    res_df = None  # result is a dataframe with the evaluated results
    return res_df  # a list of masses and thir data

def suchthat2df(suchthat):
    return evaluate(str(suchthat))


if __name__ == '__main__':
    suchthat = Evaluable(p_method='AND', p_values=(Evaluable(p_method='AND', p_values=(Evaluable(p_method='isOdd',
                                                                                                 p_values=[Obj(
                                                                                                     p_rule='p_withAttr_accessItem_',
                                                                                                     p_values=['pr',
                                                                                                               '.',
                                                                                                               'chemsc',
                                                                                                               '[', 'H',
                                                                                                               ']'])]),
                                                                                       Evaluable(p_method='isOdd',
                                                                                                 p_values=[Evaluable(
                                                                                                     p_method='*',
                                                                                                     p_values=(Obj(
                                                                                                         p_rule='p_withAttr_accessItem_',
                                                                                                         p_values=['pr',
                                                                                                                   '.',
                                                                                                                   'chemsc',
                                                                                                                   '[',
                                                                                                                   'db',
                                                                                                                   ']']),
                                                                                                               2))]))),
                                                   Evaluable(p_method='==', p_values=(Evaluable(p_method='+', p_values=(
                                                   Evaluable(p_method='+', p_values=(
                                                   Obj(p_rule='p_withAttr_id', p_values=['FA1', '.', 'chemsc']),
                                                   Obj(p_rule='p_withAttr_id', p_values=['FA2', '.', 'chemsc']))),
                                                   ElementSeq(txt='C9 H19 N1 O6 P1'))), Obj(p_rule='p_withAttr_id',
                                                                                            p_values=['pr', '.',
                                                                                                      'chemsc'])))))
    res = suchthat2df(suchthat)
    print(res)
