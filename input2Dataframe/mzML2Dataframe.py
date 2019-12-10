import logging, os
import numpy as np
import pandas as pd
log = logging.getLogger(os.path.basename(__file__))
from pyteomics import mzml, auxiliary
import pymzml

import pymzml

def mzML2DataFrames_faster(filename): #this is with pytheomics
    idx_list = [] #TODO this should be a np.array
    fs_list = []
    i_list = []
    m_list = []
    msrun = pymzml.run.Reader(file_path)
    for spectrum in msrun:
        idx = spectrum['id']
        fs  = spectrum['MS:1000512']
        i   = spectrum.mz
        m   =  spectrum.i

            #Append to content
            count = len(i)
            idx_list.extend([idx]*count)
            fs_list.extend([fs]*count)
            i_list.extend(i)
            m_list.extend(m)
    return pd.DataFrame({'scanNum':idx_list, 'filterLine':fs_list, 'intensity':i_list, 'mass':m_list})


def mzML2DataFrames(filename): #this is with pytheomics
    idx_list = [] #TODO this should be a np.array
    fs_list = []
    i_list = []
    m_list = []
    with mzml.read(filename) as reader:
        for item in reader:
            idx = item['index'] + 1
            fs = item['scanList']['scan'][0]['filter string']
            i = item['intensity array']
            m = item['m/z array']

            #Append to content
            count = len(i)
            idx_list.extend([idx]*count)
            fs_list.extend([fs]*count)
            i_list.extend(i)
            m_list.extend(m)

    return pd.DataFrame({'scanNum':idx_list, 'filterLine':fs_list, 'intensity':i_list, 'mass':m_list})


def main(filename): # TODO should return two seperate dataframe to avoid data repetition
    log.info('convert raw file {} to dataframe'.format(filename))
    MSrawscansDF, MSPeakDatasDF = mzML2DataFrames(filename)
    name = os.path.split(filename)[-1]
    MSrawscansDF.to_pickle(name[:-4]+'_Scans.pkl')
    MSPeakDatasDF.to_pickle(name[:-4]+'_Peaks.pkl')

if __name__ == '__main__':
    filename = ' '.join(sys.argv[1:])
    main(filename)