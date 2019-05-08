import pandas as pd

from data_structs import Var, ElementSeq
from from_m_lipidx.calcsf_cached import calcsf
from from_m_lipidx.chemParser import parseElemSeq

elems = 'C,H,O,N,P,S,Na,D,Ci,Cl,Li,Ni,F,I,Ag,Al,W,Ti'
elems = elems.split(',')

def makeArgs(es):
    res = []
    for elem in elems:
        if elem in es._seq:
            res.append(es._seq.get(elem).get_range()[0])
            res.append(es._seq.get(elem).get_range()[-1])
        else:
            res.append(0)
            res.append(0)
    return res


def var2df(var):
    # TODO remimplement this because its super inefficient
    txt = var.object.txt
    es = parseElemSeq(txt.strip('\''))

    charge = var.Options['chg']
    dbLowerBound = var.Options['dbr'][0]
    dbUpperBound = var.Options['dbr'][1]
    tolerance = float("inf")
    mass = 0

    argsTuple = tuple(makeArgs(es))
    args = argsTuple + (mass, tolerance, dbLowerBound, dbUpperBound, charge)
    df = make_DF(args)
    return df


def make_DF(args):
    mass_list, dbr_list, listOutSeq = calcsf(args)
    df = pd.DataFrame({'m': mass_list, 'db': dbr_list, 'sequence': listOutSeq})
    # as in https://mikulskibartosz.name/how-to-split-a-list-inside-a-dataframe-cell-into-rows-in-pandas-9849d8ff2401
    df_elems = df['sequence'].apply(pd.Series)
    df_elems.columns = elems
    df = df.join(df_elems)
    return df


def elementSeqTxt2df(txt):  # for processing suchthat
    es = parseElemSeq(txt.strip('\''))
    argsTuple = tuple(makeArgs(es))
    args = argsTuple + (0, float("inf"), 0, float("inf"), 0)  # (mass, tolerance, dbLowerBound, dbUpperBound, charge)
    df = make_DF(args)
    return df.m



if __name__ == '__main__':
    vars = [Var(id='pr', object=ElementSeq(txt='C[30..80] H[40..300] O[10] N[1] P[1]'),
                Options={'dbr': (2.5, 14.5), 'chg': -1}),
            Var(id='FA1', object=ElementSeq(txt='C[10..40] H[20..100] O[2]'), Options={'dbr': (1.5, 7.5), 'chg': -1}),
            Var(id='FA2', object=ElementSeq(txt='C[10..40] H[20..100] O[2]'), Options={'dbr': (1.5, 7.5), 'chg': -1})]

    vars = [var2df(var) for var in vars]
    print(vars[0].head())
