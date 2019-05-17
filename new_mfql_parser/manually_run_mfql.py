from mfql_Parser import parser
from spectra_tools import get_triggerScan, specta_df_fromCSV, getMS1Negpeaks
from var2df import var2df

if __name__ == '__main__':
    print('get mfql data')
    with open('sample.mfql', 'rU') as f:
        mfql = f.read()
    mfql = parser.parse(mfql)

    print('get spectra')
    df = specta_df_fromCSV('spectra.csv')
    print('get pr-fa link')
    triggerScan, triggeredScans = get_triggerScan(df)

    print('do define part')
    '''QUERYNAME = PCFAS;
	DEFINE pr = 'C[30..80] H[40..300] O[10] N[1] P[1]' WITH DBR = (2.5,14.5), CHG = -1;
	DEFINE FA1 = 'C[10..40] H[20..100] O[2]' WITH DBR = (1.5,7.5), CHG = -1;
	DEFINE FA2 ='C[10..40] H[20..100] O[2]' WITH DBR = (1.5,7.5), CHG = -1;'''
    variables = mfql['variables']
    var_dfs = {var.id: var2df(var) for var in variables}

    print('do identification part')
    '''IDENTIFY
	pr IN MS1- AND
	FA1 IN MS2- AND
	FA2 IN MS2-'''
    print('pr in ms1-')
    MS1Neg_ser = getMS1Negpeaks(df)

    print('do such that part')
    print('do report part')
