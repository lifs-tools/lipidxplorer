import logging, os
log = logging.getLogger(os.path.basename(__file__))
import pandas as pd
from pyteomics import mzml, auxiliary

def add_Sample(
		sc = None,
		specFile = None,
		specDir = None,
		options = {},
		**kwargs
		):

	make_a_masterscan(specFile)

	specName = specFile
	lpdxSample_base_peak_ms1 = None
	nb_ms_scans = 0
	nb_ms_peaks = 0
	nb_msms_scans = 0 
	nb_msms_peaks = 0
	return (specFile, lpdxSample_base_peak_ms1, nb_ms_scans, nb_ms_peaks, nb_msms_scans, nb_msms_peaks)

def make_a_masterscan(mzml_file):
	scansDF, peaksDF = mzML2DataFrames(mzml_file)
    

def mzML2DataFrames(filename): #TODO move this to input2dataframe
    scans = []
    peaks_dfs = []
    
    with mzml.read(filename) as reader:
        for item in reader:
            id  = item['id']
            idx = item['index'] + 1
            fs  = item['scanList']['scan'][0]['filter string']
            time = item['scanList']['scan'][0]['scan start time'] # * 1 to make a unitfloat into a float
            msLevel = item['ms level']
            positive_scan = item['positive scan']
            p_data = item.get('precursorList',None) #helper
            precursor_id = p_data['precursor'][0]['spectrumRef'] if p_data else None
            
            #collect the scans data
            row = (id,idx,fs,time,msLevel,positive_scan,precursor_id)
            scans.append(row)
            
            #collect the peaks data
            i   = item['intensity array']
            m   = item['m/z array']
            cols = {'m':m, 'i':i}
            df = pd.DataFrame(cols)
            df['id']=id
            df.set_index('id', inplace = True)
            peaks_dfs.append(df)
        
        scansDF = pd.DataFrame(scans, columns=['id','idx','filter_string','time','msLevel','positive_scan','precursor_id'])
        scansDF.set_index('id', inplace = True)
        peaksDF = pd.concat(peaks_dfs)

    return scansDF, peaksDF