#!/usr/bin/env python
# coding: utf-8

# In[1]:


get_ipython().run_line_magic("ls", "")


# In[2]:


file = "20140310_PCbheart_22-5p_01.csv"


# In[3]:


import pandas as pd
import numpy as np
from scipy.optimize import curve_fit

# %matplotlib notebook
import matplotlib.pyplot as plt


# In[4]:


df = pd.read_csv(file)


# In[5]:


df.columns = ["scanNum", "filterLine", "retTime", "m", "i", "r", "x", "y", "z"]
# category instead? df['filterLine'] = df['filterLine'].asType('category')


# In[6]:


# outliers? q99 = df['r'].quantile(.99)
# df = df.loc[df.filterLine.str.contains(' ms ')]
# df_ms2 = df.loc[df.filterLine.str.contains(' ms2 ')]
df.reset_index(inplace=True)


# In[7]:


df.plot.scatter(x="m", y="r")


# In[8]:


# as in https://stackoverflow.com/questions/42006058/binning-data-in-a-pandas-dataframe-into-intervals
# aslo try and use https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Interval.html
# and cummax
df["m_bin"] = pd.cut(df.m, 50)
idxmax = df.groupby("m_bin")["r"].idxmin()


# In[9]:


df.iloc[idxmax.values].plot.scatter(x="m", y="r")


# In[10]:


z = np.polyfit(df.iloc[idxmax.values].m, df.iloc[idxmax.values].r, 2)
f = np.poly1d(z)


# In[11]:


x = df.iloc[idxmax.values]["m"]
plt.scatter(x, f(x))
plt.scatter(x, df.iloc[idxmax.values].r)


# In[23]:


f1(200)


# # do it with intensity

# In[12]:


df["m_diff"] = df.groupby("scanNum")["m"].diff()


# In[26]:


# as in https://en.wikipedia.org/wiki/Resolution_(mass_spectrometry)
# https://en.wikipedia.org/wiki/Full_width_at_half_maximum 2.63
# df['est_r'] = df['m']/df['m_diff']
df["est_r"] = df["m"].min() / df["m_diff"]  # not sure why its one magnitude lower


# In[27]:


idxmax1 = df.groupby("m_bin")["est_r"].idxmax()


# In[28]:


df.iloc[idxmax1.values].plot.scatter(x="m", y="est_r")


# In[73]:


# maybe def reject_outliers(data, m=2):
#     return data[abs(data - np.mean(data)) < m * np.std(data)]
# https://stackoverflow.com/questions/23199796/detect-and-exclude-outliers-in-pandas-data-frame
q95 = df.iloc[idxmax1.values].est_r.quantile(0.95)  # to remove outliers
# try moving average


# In[74]:


q95df = df.iloc[idxmax1.values].where(df.est_r.lt(q95))  # this is dirty need to improve


# In[75]:


q95df.dropna().shape


# In[76]:


z1 = np.polyfit(q95df.dropna().m, q95df.dropna().est_r, 2)
f1 = np.poly1d(z1)


# In[77]:


x = df.iloc[idxmax.values]["m"]
plt.scatter(x, f1(x), label="estimated")
plt.scatter(x, f(x), label="from r")
plt.scatter(x, df.iloc[idxmax.values].r, label="true")
plt.legend()


# # try with more robust curve fitting

# In[86]:


test_df = df.iloc[idxmax1.values]


# In[131]:


from scipy.optimize import least_squares

t_train = test_df.m
y_train = test_df.est_r

# function for computing residuals, necessary for `least_squares` as the
# `least_squares` method minimizes residuals


def fun(x, t, y):
    return x[0] + x[1] * np.exp(x[2] * t) - y


def generate_data(t, A, sigma, omega):
    y = A * np.exp(-sigma * t) * np.sin(omega * t)
    return y


x0 = np.array([1.0, 1.0, 0.0])

res_soft_l1 = least_squares(
    fun, x0, loss="cauchy", f_scale=0.1, args=(t_train, y_train)
)


# In[132]:


x = df.iloc[idxmax.values]["m"]
plt.scatter(x, f1(x), label="estimated")
plt.scatter(x, f(x), label="from r")
plt.scatter(x, generate_data(x, *res_soft_l1.x), label="robust")
plt.scatter(x, df.iloc[idxmax.values].r, label="true")
plt.legend()


# ## maybe lowes
#

# In[143]:


import statsmodels.api as sm

lowess = sm.nonparametric.lowess
z = lowess(y_train, t_train, poly_degree=2)


# In[141]:


plt.scatter(z[:, 0], z[:, 1])


# In[ ]:
