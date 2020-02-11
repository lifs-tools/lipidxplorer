import warnings
from collections import namedtuple
from data_structs import Obj, ElementSeq, Evaluable, Func, ReportItem, ReportCol
from chemParser import txt2dict
from targets import Targets_util


def ElementSeq2m(elementSeq):
    txt = elementSeq.txt
    tmp = txt2dict(txt)
    target = Targets_util(tmp)
    target._makeRanges()
    target._makeDF()
    target._cal_M()
    return target._df['m'][0]


def txt(evaluable):
    res = None
    if type(evaluable) in [int,float, str]:
        res = str(evaluable)
    elif isinstance(evaluable, list):
        if len(evaluable) == 1 :
            res = txt(evaluable[0])
    elif isinstance(evaluable, Evaluable):
        res = f'{txt(evaluable.term_1)} {evaluable.operation.lower()} {txt(evaluable.term_2)}'
    elif isinstance(evaluable, Func):
        if evaluable.func == 'isOdd':
            res = f'{txt(evaluable.on)} % 2 == 0'
        if evaluable.func == 'avg':
            res = f'{txt(evaluable.on)}' # do nothing
    elif isinstance(evaluable, Obj):
        if evaluable.p_rule == 'p_withAttr_accessItem_':
            if evaluable.p_values[2] == 'chemsc':
                item = evaluable.p_values[-2]
                if item == 'db': item = 'dbr' # refa: rename db to dbr
                res = f'{evaluable.p_values[0]}_{item}'
        elif evaluable.p_rule == 'p_withAttr_id':
            if evaluable.p_values[2] == 'chemsc':
                res = f'{evaluable.p_values[0]}_target'
            elif evaluable.p_values[2] == 'intensity':
                res = f'{evaluable.p_values[0]}_i'
        elif evaluable.p_rule == 'p_expression_attribute':
            if type(evaluable.p_values[0]) == Obj and \
                evaluable.p_values[0].p_rule == 'p_withAttr_id' and \
                evaluable.p_values[0].p_values[2] == 'chemsc':
                    item = evaluable.p_values[1]
                    if item == 'db': item = 'dbr' # refa: rename db to dbr
                    res = f'{evaluable.p_values[0].p_values[0]}_{item}'
    elif isinstance(evaluable, ElementSeq):
        res = f'{ElementSeq2m(evaluable)}'
    else:
        warnings.warn(f'could not evaluate {evaluable}')
        res = str(evaluable)
    
    if res == None:
         warnings.warn(f'did not evaluate {evaluable}')
    return res

def suchthat2txt(suchthat):
    return txt(suchthat)

def report2exec_txt(report):
    res = []
    for reportItem in report:
        name = reportItem.id
        if reportItem.is_PCT_format:
            pct_format = reportItem.p_values[0]
            col_tuple = reportItem.p_values[3]
            tuple_txt = [txt(t) for t in col_tuple]
            exec_txt = ', '.join(tuple_txt)
            col = ReportCol(name, pct_format, exec_txt)
        elif type(reportItem.p_values)  == str: # just a string
            col = ReportCol(name, None , reportItem.p_values[0])
        else:
            col = ReportCol(name, '%', txt(reportItem.p_values[0]))
        res.append(col)
    return res

if __name__ == '__main__':
    # suchthat = Evaluable(operation='AND', term_1=Evaluable(operation='AND', term_1=Func(func='isOdd', on=[
    #     Obj(p_rule='p_withAttr_accessItem_', p_values=['pr', '.', 'chemsc', '[', 'H', ']'])]), term_2=Func(func='isOdd',
    #                                                                                                        on=[
    #                                                                                                            Evaluable(
    #                                                                                                                operation='*',
    #                                                                                                                term_1=Obj(
    #                                                                                                                    p_rule='p_withAttr_accessItem_',
    #                                                                                                                    p_values=[
    #                                                                                                                        'pr',
    #                                                                                                                        '.',
    #                                                                                                                        'chemsc',
    #                                                                                                                        '[',
    #                                                                                                                        'db',
    #                                                                                                                        ']']),
    #                                                                                                                term_2=2)])),
    #                      term_2=Evaluable(operation='==', term_1=Evaluable(operation='+',
    #                                                                        term_1=Evaluable(operation='+', term_1=Obj(
    #                                                                            p_rule='p_withAttr_id',
    #                                                                            p_values=['FA1', '.', 'chemsc']),
    #                                                                                         term_2=Obj(
    #                                                                                             p_rule='p_withAttr_id',
    #                                                                                             p_values=['FA2', '.',
    #                                                                                                       'chemsc'])),
    #                                                                        term_2=ElementSeq(txt='C9 H19 N1 O6 P1')),
    #                                       term_2=Obj(p_rule='p_withAttr_id', p_values=['pr', '.', 'chemsc'])))
    # res = suchthat2txt(suchthat)
    # print(res)

    # report =[ReportItem(id='SPECIE', p_values=['"CE %d:%d"', '%', '"(', [Evaluable(operation='-', term_1=Obj(p_rule='p_expression_attribute', p_values=(Obj(p_rule='p_withAttr_id', p_values=['PR', '.', 'chemsc']), 'C')), term_2=27), Evaluable(operation='-', term_1=Obj(p_rule='p_expression_attribute', p_values=(Obj(p_rule='p_withAttr_id', p_values=['PR', '.', 'chemsc']), 'db')), term_2=4.5)], ')"'], is_PCT_format=True),
    #     ReportItem(id='CLASS', p_values=['CE'], is_PCT_format=False),
    #     ReportItem(id='MASS', p_values=[Obj(p_rule='p_withAttr_id', p_values=['PR', '.', 'mass'])], is_PCT_format=False),
    #     ReportItem(id='IDMSLEVEL', p_values=[2], is_PCT_format=False),
    #     ReportItem(id='QUANTMSLEVEL', p_values=[2], is_PCT_format=False),
    #     ReportItem(id='ISOBARIC', p_values=[Obj(p_rule='p_withAttr_id', p_values=['PR', '.', 'isobaric'])], is_PCT_format=False),
    #     ReportItem(id='CHEMSC', p_values=[Obj(p_rule='p_withAttr_id', p_values=['PR', '.', 'chemsc'])], is_PCT_format=False),
    #     ReportItem(id='ERRppm', p_values=['"%2.2f"', '%', '"(', [Obj(p_rule='p_withAttr_id', p_values=['PR', '.', 'errppm'])], ')"'], is_PCT_format=True),
    #     ReportItem(id='FRERRppm', p_values=['"%2.2f"', '%', '"(', [Obj(p_rule='p_withAttr_id', p_values=['FR', '.', 'errppm'])], ')"'], is_PCT_format=True),
    #     ReportItem(id='INT', p_values=[Obj(p_rule='p_withAttr_id', p_values=['FR', '.', 'intensity'])], is_PCT_format=False),
    #     ReportItem(id='QUALA', p_values=[Obj(p_rule='p_withAttr_id', p_values=['PR', '.', 'intensity'])], is_PCT_format=False),
    #     ReportItem(id='QUALB', p_values=[Obj(p_rule='p_withAttr_id', p_values=['PR', '.', 'intensity'])], is_PCT_format=False),
    #     ReportItem(id='QUALC', p_values=[Obj(p_rule='p_withAttr_id', p_values=['PR', '.', 'intensity'])], is_PCT_format=False)]
    filename = 'test_resources\\small_test\\170213_CE_pos_MSMS.mfql'
    from mfql_Parser import fromFile 
    mfql_dict = fromFile(filename)

    res = report2exec_txt(mfql_dict['report'])
    print('\n'.join(res))
    pass





