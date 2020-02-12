import warnings
from collections import namedtuple
from data_structs import Obj, ElementSeq, Evaluable, Func, ReportItem, ReportCol
from chemParser import txt2dict
from targets import Targets_util
import pandas as pd


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
            elif evaluable.p_values[2] == 'mass':
                res = f'{evaluable.p_values[0]}_m'
            elif evaluable.p_values[2] == 'isobaric':
                res = f'{evaluable.p_values[0]}_target'
                warnings.warn(f' *** how to deal with isobaric ***')
            elif evaluable.p_values[2] == 'errppm':
                res = f'{evaluable.p_values[0]}_ppm'
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
        elif type(reportItem.p_values) in [int,float, str]: # just a string
            col = ReportCol(name, None , reportItem.p_values)
        else:
            col = ReportCol(name, '%s', txt(reportItem.p_values))
        res.append(col)
    return res

def reportCols2DF(reportCols, df):
    rep_df = pd.DataFrame(index = df.index)
    for reportCol in reportCols:
        print(reportCol)
        if reportCol.col_fortmat is None:
            rep_df[reportCol.col_name] = reportCol.col_eval_txt
            print(f'1: {reportCol.col_eval_txt}')
        else:
            eval_res = df.eval(reportCol.col_eval_txt)
            col_format = reportCol.col_fortmat
            print(f'2: {type(eval_res)} {col_format}')
            if type(eval_res) == list:
                eval_res = zip(*eval_res)
            rep_df[reportCol.col_name] = [col_format % tup for tup in eval_res]
        
    return rep_df

if __name__ == '__main__':

    filename = 'test_resources\\small_test\\170213_CE_pos_MSMS.mfql'
    from mfql_Parser import fromFile 
    mfql_dict = fromFile(filename)

    res = suchthat2txt(mfql_dict['suchthat'])
    print('\n'.join([str(r) for r in res]))
    print('*******************************8')
    res = report2exec_txt(mfql_dict['report'])
    print('\n'.join([str(r) for r in res]))
    





