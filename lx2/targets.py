import pandas as pd
import numpy as np
from collections import namedtuple

class MFQL_util():

    mass_of = {
        'C' : 12,
        'H' : 1.0078250321,
        'N' : 14.0030740052,
        'P' : 30.97376151,
        'O' : 15.9949146221,
        'S' : 31.97207069
        }
    
    def __init__(self,elements):
        self.elements = elements
        self._ranges = {}
        self._df = None
        self._build()
    
    def _build(self):
        self._makeRanges()
        self._makeDF()
        self._cal_M()
        self._cal_dbr()
        self._cal_chem()

    def _makeRanges(self):
        for name, bounds in self.elements.items():
            self._ranges[name] = np.arange(bounds[0],bounds[1]+1)
    
    def _makeDF(self):
        index  = pd.MultiIndex.from_product(self._ranges.values(), names = self._ranges.keys())
        self._df = pd.DataFrame(index = index).reset_index()
    
    def _cal_M(self):
        self._df['m'] = 0
        for colName in self._df.columns.intersection(self.mass_of.keys()):
            self._df['m'] += self._df[colName] * self.mass_of[colName]

    def _cal_dbr(self):
        x = self._df.get('Cl',0) + self._df.get('Br', 0) + self._df.get('I',0) + self._df.get('F',0)
        self._df['dbr'] = self._df.get('C', 0) + 1 - self._df.get('H', 0)/2 - x/2 + self._df.get('N', 0)/2

    def _cal_chem(self):
        #https://stackoverflow.com/questions/52673285/performance-of-pandas-apply-vs-np-vectorize-to-create-new-column-from-existing-c
        self._df['chem'] = ''
        for colName in self._df.columns.intersection(self.mass_of.keys()):
            self._df['chem'] += colName + self._df[colName].apply(str) + ' '

    def set_dbr(self, dbr_u, dbr_l):
        self._df = self._df.loc[self._df.dbr.between(dbr_u, dbr_l)]

    @staticmethod
    def keepMinErrorPeaks(matchesDF):
        matchesDF['err'] = matchesDF['m'] - matchesDF['target']
        matchesDF['err'] = matchesDF['err'].abs()
        matchesDF['min_err'] = matchesDF.groupby(['id','chem'])['err'].transform('min')
        matchesDF = matchesDF.loc[matchesDF['err'] == matchesDF['min_err']]
        matchesDF.drop('min_err', axis = 1, inplace=True)
        return matchesDF
    
    @staticmethod
    def makeAllCombo(pr_df, fr_df):
        pr_df.loc[:, 'key']=0
        fr_df.loc[:, 'key']=0
        pr_df.add_prefix('PR_')
        fr_df.add_prefix('FR_')
        in_df = pr_df.merge(fr_df, on='key')
        
        pr_df.drop('key', 1, inplace=True)
        fr_df.drop('key', 1, inplace=True)
        in_df.drop('key',1, inplace = True)

        return in_df 
    
    @staticmethod
    def suchThat(df, query):
        return df.query(query)
