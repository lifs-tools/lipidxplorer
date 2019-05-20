import numpy as np


def nearest(ser1, ser2):
    '''find the neareest value in series 2 for each element in series1'''
    # from https://stackoverflow.com/questions/2566412/find-nearest-value-in-numpy-array
    # TODO try https://stackoverflow.com/questions/9706041/finding-index-of-an-item-closest-to-the-value-in-a-list-thats-not-entirely-sort
    res = []
    array = np.asarray(ser2)
    for value in ser1:
        idx = (np.abs(array - value)).argmin()
        res.append(idx)
    return res

    # as https://stackoverflow.com/questions/48074180/replace-a-pandas-series-with-the-closest-values-from-another-series?noredirect=1&lq=1
    # nearest = pd.Series(sel_df.mz, sel_df.mz).reindex(var_df.m, method='nearest', tolerance=100)
