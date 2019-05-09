import pandas as pd


def specta_df_fromCSV(csv):
    df = pd.read_csv(csv)
    df.columns = 'scanNum,filterLine,retTime,mz,i,r,n,z,charge'.split(',')
    return df


def add_pr_fa_link(scan_df):
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

    return scan_df
