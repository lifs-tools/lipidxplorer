import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt


def estimate(file, bins=50):
    df = pd.read_csv(file)
    df.columns = ["scanNum", "filterLine", "retTime", "m", "i", "r", "x", "y", "z"]
    # category instead? df['filterLine'] = df['filterLine'].asType('category')
    # this works better with all th data instead of a seperate one for ms2+

    # as in https://stackoverflow.com/questions/42006058/binning-data-in-a-pandas-dataframe-into-intervals
    # aslo try and use https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Interval.html
    # and cummax
    # bins may be root of number of samples
    df["m_bin"] = pd.cut(df.m, bins)
    idxmax = df.groupby("m_bin")["r"].idxmin()

    # df.iloc[idxmax.values].plot.scatter(x='m', y='r')
    # this works for known r
    # z = np.polyfit(df.iloc[idxmax.values].m,df.iloc[idxmax.values].r,2)
    # f = np.poly1d(z)
    # plt.scatter(x, f(x))

    df["m_diff"] = df.groupby("scanNum")["m"].diff()
    # as in https://en.wikipedia.org/wiki/Resolution_(mass_spectrometry)
    # https://en.wikipedia.org/wiki/Full_width_at_half_maximum in sigmas 2.355/3
    # because peak to peak is 3 sigma, so m_diff/3 =1 sigma
    df["est_r"] = df["m"].min() / (df["m_diff"] * 2.355 / 3)  # test
    idxmax1 = df.groupby("m_bin")["est_r"].idxmax()
    # df.iloc[idxmax1.values].plot.scatter(x='m', y='est_r')

    # https://stackoverflow.com/questions/23199796/detect-and-exclude-outliers-in-pandas-data-frame
    q95 = df.iloc[idxmax1.values].est_r.quantile(0.95)  # to remove outliers
    # TODO try moving average
    q95df = df.iloc[idxmax1.values].where(
        df.est_r.lt(q95)
    )  # this is dirty need to improve
    z1 = np.polyfit(q95df.dropna().m, q95df.dropna().est_r, 2)
    f1 = np.poly1d(z1)
    return f1


if __name__ == "__main__":
    file = r"resolution_estimation/20140310_PCbheart_22-5p_01.csv"
    f = estimate(file)
    m = 500
    r = f(m)
    print(r)
