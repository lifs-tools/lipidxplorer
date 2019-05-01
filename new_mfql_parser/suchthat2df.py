from data_structs import Evaluable, Obj, ElementSeq


def suchthat2df(suchthat):
    return suchthat


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
