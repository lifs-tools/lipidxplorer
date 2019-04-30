from data_structs import Var, ElementSeq


def var2df(var):
    return str()


if __name__ == '__main__':
    vars = [Var(id='pr', object=ElementSeq(str='C[30..80] H[40..300] O[10] N[1] P[1]'),
                Options={'dbr': (2.5, 14.5), 'chg': -1}),
            Var(id='FA1', object=ElementSeq(str='C[10..40] H[20..100] O[2]'), Options={'dbr': (1.5, 7.5), 'chg': -1}),
            Var(id='FA2', object=ElementSeq(str='C[10..40] H[20..100] O[2]'), Options={'dbr': (1.5, 7.5), 'chg': -1})]

    vars = [var2df(var) for var in vars]
    print(vars)
