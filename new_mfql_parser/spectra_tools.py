import warnings
from collections import defaultdict

import pandas as pd


def specta_df_fromCSV(csv):
    df = pd.read_csv(csv)
    df.columns = 'scanNum,filterLine,retTime,mz,i,r,n,z,charge'.split(',')
    return df


def get_triggerScan(scan_df, tol=0.01):
    # get only the scans not the peaks
    unique_scan_df = scan_df[['scanNum', 'filterLine']].drop_duplicates()

    # todo make this Dry
    unique_scan_df.loc[unique_scan_df.filterLine.str.contains(' ms '), 'msLevel'] = 1
    unique_scan_df.loc[unique_scan_df.filterLine.str.contains(' ms2 '), 'msLevel'] = 2
    unique_scan_df['msLevel'] = unique_scan_df['msLevel'].astype('category')
    unique_scan_df.loc[unique_scan_df.filterLine.str.contains(' - '), 'mode'] = 'neg'
    unique_scan_df.loc[unique_scan_df.filterLine.str.contains(' + '), 'mode'] = 'pos'
    unique_scan_df['mode'] = unique_scan_df['mode'].astype('category')

    unique_scan_df['precursor'] = unique_scan_df['filterLine'].str.extract('(\d*\.\d*)@', expand=True)

    # get the probabale ms1 scan and veryify its there
    # todo make this better
    # scan_df.where() datframe where returns from one dataframe if true and from abother if false
    triggerScan = {}
    triggeredScans = defaultdict(list)
    prev1, prev2 = None, None
    for tup in unique_scan_df.itertuples():
        if tup.msLevel == 1:
            # triggerScan.append()
            prev1 = tup.scanNum
            prev2 = prev1
            continue
        target_peak = float(tup.precursor)
        nearnes = scan_df[scan_df.scanNum == prev1].mz.apply(
            lambda x: abs(x - target_peak)).min()  # TODO make this more efficient
        if nearnes < tol:
            triggerScan[tup.scanNum] = prev1
            triggeredScans[prev1].append(tup.scanNum)
        elif scan_df[scan_df.scanNum == prev2].mz.apply(
                lambda x: abs(x - target_peak)).min():  # check the alternative if not found
            # triggerScan.append(prev2)
            triggerScan[tup.scanNum] = prev2
            triggeredScans[prev2].append(tup.scanNum)
        else:
            # triggerScan.append(None)  # none was found
            warnings.warn('no ms1 trigger peak found for scan {}'.format(tup.scanNum))

    # unique_scan_df['triggerScan'] = triggerScan
    # unique_scan_df.index = unique_scan_df.scanNum
    return triggerScan, triggeredScans
