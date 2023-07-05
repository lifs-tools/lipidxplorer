#!/usr/bin/env python
# coding: utf-8

# # Estimate the resolution based on mass and intensity
#
# because the open source formats do not have it and we use it in lipidxplorer and peakstrainer
#

# In[1]:


import pandas as pd


# In[2]:


# this is our sample file
fileName = "20140310_PCbheart_22-5p_01.csv"
df = pd.read_csv(fileName)
df.columns = ["scanNum", "filterLine", "retTime", "m", "i", "r", "x", "y", "z"]


# In[3]:


df.head()


# In[4]:


get_ipython().run_line_magic("matplotlib", "notebook")
import matplotlib.pyplot as plt


# Resolution is a function of the mass, lets see that
plt.scatter(df["m"], df["r"])
plt.show()
# In[6]:


# using the mean we can smooth out some of the outliers
df["round_m"] = df["m"].astype(int)
df["mean_r"] = df.groupby("round_m")["r"].transform("mean")
df.plot.scatter(x="m", y="mean_r")


# There are some outliers... because:
# * centroided peaks are based on multiple profile peaks
# * resolution is based on multiple profile peaks
# * if there are very few profile peaks (i.e. 2) then the resolution is super high... how to distinguish them?

# all the high resolution have a low intensity, see the graph below

# In[7]:


plt.scatter(df["r"], df["i"])
plt.show()


# lets count the number of peaks by intensity...
# we expet so see a continous distribution

# In[7]:


plt.hist(df["r"], 100)  # maybe see it as a rug plot
plt.show()


# we see that it most of the peaks are between 0 and 250000

# In[8]:


q99 = df["r"].quantile(0.99)
upper = 1.1 * q99  # 1.1 to include the first few outliers
upper


# In[9]:


r_ser = df.loc[df["r"] < upper]["r"]
plt.hist(r_ser, 100)
plt.show()


# we expect the resoltion to be a continous curve and so we want to cut off the roght side that is genearted by the resolutiuon artifacts

# ## Calulated relative intensity

# get the relative intensity of the peaks and remove all the low intensity,
# __the reolution should be mass dependant not resolution dependandt__,
# and we only need a few samples to make the curve so, lets get rid of some low intensity peaks
#
#

# In[12]:


# calculate the relative intensity
df["max_i"] = df.groupby("scanNum")["i"].transform("max")


# In[13]:


df["rel_i"] = df["i"] / df["max_i"]
df["rel_i"].describe()


# In[14]:


plt.scatter(df.loc[df.rel_i > 0.05]["m"], df.loc[df.rel_i > 0.05]["r"])
plt.show()


# In[30]:


plt.scatter(df.loc[df.rel_i > 0.05]["m"], df.loc[df.rel_i > 0.05]["mean_r"])
plt.show()


# cleaner resolution curve by removing the low intensity peeks, thats where would find the resolution outliers, because they have very fuew datapoints to generate the resolutuon and intensity values...
# but there are still some outliers at m=740, we can still see the curve underneath,
# thats what we want to replicate

# # generate the calculated resolution

# In[15]:


df.sort_values(["scanNum", "m"], inplace=True)


# In[16]:


df["delta_m1"] = df.m - df.m.shift(1)
df["delta_m2"] = df.m.shift(-1) - df.m
df["in_scan1"] = df.scanNum == df.scanNum.shift(1)
df["in_scan2"] = df.scanNum == df.scanNum.shift(-1)


# In[17]:


nan = df.delta_m1[0]
df.head()


# In[18]:


# replacing all the edge cases with nan,
# now in the description there should be no negative delta_m
df.loc[df["in_scan1"] == False, "delta_m1"] = nan
df.loc[df["in_scan2"] == False, "delta_m2"] = nan
df["delta_m"] = df[["delta_m1", "delta_m2"]].min(axis=1)
df["delta_m"].describe()  # should be no less than 0


# In[19]:


del df["in_scan1"]
del df["in_scan2"]
del df["max_i"]
del df["delta_m1"]
del df["delta_m2"]
# we dont need them anymore


# In[20]:


df.describe()


# In[21]:


# as in https://en.wikipedia.org/wiki/Resolution_(mass_spectrometry)
df["calc_r"] = df["m"] / df["delta_m"]


# we would expect to see a correlation between r and calc_r, a diagonal
# with some noise in the r because of not enough datapoints and in calc_r because no peak close enough

# In[22]:


# here we want to see a diagonal line
df.plot.scatter(x="mean_r", y="calc_r")


# In[23]:


small_df = df.loc[(df.rel_i > 0.01) & (df.calc_r > 10000)].plot.scatter(
    x="mean_r", y="calc_r"
)


# I would make a rounded calc_r but there are too many invalid values, so we need to select the valid calc_r
# (https://pbpython.com/pandas_transform.html)

# In[24]:


df["max_calc_r"] = df.groupby("round_m")["calc_r"].transform("max")


# to smooth out some of the outliers we run the average on the top 95 %

# In[25]:


df["rel_calc_r"] = df["calc_r"] / df["max_calc_r"]
df.loc[(df.rel_i > 0.01) & (df.rel_calc_r > 0.95)].plot.scatter(
    x="mean_r", y="max_calc_r"
)


# there are still some outliers but much less so lets try the mean again
# *ps it was #sel_df = df.loc[ (df.rel_i > 0.01) & (df.i < 5000) & (df.rel_calc_r > 0.95) & (df.rel_calc_r < 1) ]
# not sure why high intense peaks give noise... because high intense can have a high reolution that is not the base performance of the machine

# In[27]:


sel_df = df.loc[
    (df.rel_i > 0.01) & (df.i < 5.125122e04) & (df.rel_calc_r > 0.95)
]  # df.i is because q[50]
# sel_df['mean_max_calc_r'] = df.groupby('round_m')['max_calc_r'].transform('mean')
# sel_df.plot.scatter(x='mean_r', y='mean_max_calc_r' )
plt.scatter(
    x=sel_df["mean_r"],
    y=sel_df["max_calc_r"],
    c=sel_df["m"] / 10,
    s=sel_df["i"] / 100,
)
# plt.scatter(x=sel_df['m']*100, y=sel_df['r'])
# plt.scatter(x=sel_df['r'], y=sel_df['i']*10)


# In[55]:


sel_df.loc[(sel_df.mean_r < 72000) & (sel_df.max_calc_r < 31000)].sort_values(
    "i", ascending=False
)


# In[28]:


sel_df.plot.scatter(x="mean_r", y="max_calc_r")


# now we have less datapoints but much cleaner

# In[ ]:


sel_df.plot.scatter(x="m", y="max_calc_r")
sel_df.plot.scatter(x="m", y="mean_r")


# now we have a similar shape curve but lower... that might be because we use the valley definition and the raw file has the FWHM definition
# so based on https://en.wikipedia.org/wiki/Full_width_at_half_maximum
# we can adjust by 2.355 sigma, assuming peaks have a normal distribuiton

# # lets get the average of the max_calc_r

# In[31]:


x = sel_df["m"]
y = sel_df["max_calc_r"].rolling(1).max()
plt.scatter(x, y)


# In[ ]:


# https://stackoverflow.com/questions/19165259/python-numpy-scipy-curve-fitting
import numpy as np

x = sel_df.sort_values(by=["m"]).m.values
y = sel_df.sort_values(by=["m"]).mean_r.values
y_calc = sel_df.sort_values(by=["m"]).max_calc_r.values
z = np.polyfit(x, y_calc, 2)
f = np.poly1d(z)

# calculate new x's and y's
x_new = np.linspace(x[0], x[-1], 1200)
y_new = f(x_new)

plt.plot(x, y_calc, "o", x_new, y_new)
plt.xlim([x[0] - 1, x[-1] + 1])
plt.show()


# In[ ]:


# http://scipy-lectures.org/intro/scipy/auto_examples/plot_curve_fit.html
from scipy.optimize import curve_fit
import numpy as np


def func(x, a, b, c):
    return a * np.exp(-b * x) + c


popt_calc, pcov_calc = curve_fit(
    func, sel_df.m, sel_df.max_calc_r, bounds=(0, [1.0, 1.0, 1.0])
)
popt, pcov = curve_fit(
    func, sel_df.m, sel_df.mean_r, bounds=(0, [1.0, 1.0, 1.0])
)


# In[ ]:


popt_calc


# In[ ]:


popt


# In[ ]:


# http://scipy-lectures.org/intro/scipy/auto_examples/plot_curve_fit.html?
# https://docs.scipy.org/doc/scipy-1.0.0/reference/generated/scipy.optimize.curve_fit.html
plt.scatter(sel_df.m, sel_df.mean_r, label="Data")
plt.plot(
    sel_df.m,
    func(sel_df.m, *popt),
    "g--",
    label="fit: a=%5.3f, b=%5.3f, c=%5.3f" % tuple(popt),
)
plt.legend()
plt.show()


# so this did not work... lets try
# * moving average
# * loes
# * savitzky_golay
# * interp1d

# In[ ]:


# https://docs.scipy.org/doc/scipy/reference/tutorial/interpolate.html
from scipy.interpolate import interp1d

points = zip(x, y)
points = sorted(points, key=lambda point: point[0])
x, y = zip(*points)
x = np.array(x)
y = np.array(y)
f = interp1d(x, y)
f2 = interp1d(x, y, kind="cubic")
xnew = np.linspace(x.min(), x.max(), num=50, endpoint=True)
plt.plot(x, y, "o", xnew, f(xnew), "-", xnew, f2(xnew), "--")
plt.legend(["data", "linear", "cubic"], loc="best")
plt.show()


# In[ ]:


np.any(x[1:] <= x[:-1])


# In[ ]:


from scipy.signal import savgol_filter

sf = savgol_filter(y, 51, 2)
plt.plot(x, y, "+")
plt.plot(x, sf)
plt.show()


# In[ ]:


# In[ ]:


# https://stackoverflow.com/questions/31104565/confidence-interval-for-lowess-in-python
import statsmodels.api as sm


# In[ ]:


x = sel_df.sort_values(by=["m"]).m.values
y = sel_df.sort_values(by=["m"]).mean_r.values
y_calc = sel_df.sort_values(by=["m"]).max_calc_r.values


# In[ ]:


lowess = sm.nonparametric.lowess(y, x, frac=0.5)
plt.plot(x, y, "+")
plt.plot(lowess[:, 0], lowess[:, 1])
plt.show()


# In[ ]:


lowess = sm.nonparametric.lowess(y_calc, x, frac=0.5)
plt.plot(x, y_calc, "+")
plt.plot(lowess[:, 0], lowess[:, 1])
plt.show()


# In[ ]:


fig, ax = plt.subplots()
sel_df.sort_values("m", inplace=True)
sel_df.plot(x="m", y="mean_r", ax=ax)

model = sm.formula.ols(formula="mean_r ~ m", data=sel_df)
res = model.fit()
sel_df.assign(fit=res.fittedvalues).plot(x="m", y="mean_r", ax=ax)


# # final test to get the regresion curve
#

# In[ ]:


#  m vs mean_r and max_calc_r
sel_df
plt.plot(sel_df.m, sel_df.mean_r, "+")
plt.plot(sel_df.m, sel_df.max_calc_r, "o")
plt.legend()
plt.show()


# In[ ]:


# http://scipy-lectures.org/intro/scipy/auto_examples/plot_curve_fit.html
from scipy.optimize import curve_fit
import numpy as np


def func(x, a, b, c):
    return a * (x ** -b) + c  # this does not work a*np.exp(-b*x)+c


x = sel_df.m
y = sel_df.mean_r / 1000  # because the scale is too large
y_calc = sel_df.max_calc_r / 1000
popt, pcov = curve_fit(func, x, y)
popt_calc, pcov_calc = curve_fit(func, x, y_calc, bounds=(0, [1e6, 1.0, 1e3]))
print(popt)
print(popt_calc)


# In[ ]:


plt.scatter(x, y, label="Data")
plt.scatter(x, y_calc, label="Data_calc")
plt.plot(
    x,
    func(x, *popt),
    "g--",
    label="fit: a=%5.3f, b=%5.3f, c=%5.3f" % tuple(popt),
)
plt.plot(
    x,
    func(x, *popt_calc),
    "b",
    label="fit_calc: a=%5.3f, b=%5.3f, c=%5.3f" % tuple(popt_calc),
)
plt.legend()
plt.show()


# # https://stackoverflow.com/questions/3938042/fitting-exponential-decay-with-no-initial-guessing
#

# In[ ]:


def model_func(t, A, K, C):
    return A * np.exp(K * t) + C


def fit_exp_linear(t, y, C=0):
    y = y - C
    y = np.log(y)
    K, A_log = np.polyfit(t, y, 1)
    A = np.exp(A_log)
    return A, K


def fit_exp_nonlinear(t, y):
    opt_parms, parm_cov = curve_fit(model_func, t, y, maxfev=1000)
    A, K, C = opt_parms
    return A, K, C


def plot(ax, t, y, noisy_y, fit_y, orig_parms, fit_parms):
    A0, K0, C0 = orig_parms
    A, K, C = fit_parms

    ax.plot(
        t,
        y,
        "k--",
        label="Actual Function:\n $y = %0.2f e^{%0.2f t} + %0.2f$"
        % (A0, K0, C0),
    )
    ax.plot(
        t,
        fit_y,
        "b-",
        label="Fitted Function:\n $y = %0.2f e^{%0.2f t} + %0.2f$" % (A, K, C),
    )
    ax.plot(t, noisy_y, "ro")
    ax.legend(bbox_to_anchor=(1.05, 1.1), fancybox=True, shadow=True)


# In[ ]:


#     # Actual parameters
A0, K0, C0 = 1, 1, 1  # 2.5, -4.0, 2.0

#     # Generate some data based on these
#     tmin, tmax = 0, 0.5
#     num = 20
#     t = np.linspace(tmin, tmax, num)
#     y = model_func(t, A0, K0, C0)

#     # Add noise
#     noisy_y = y + 0.5 * (np.random.random(num) - 0.5)
t = sel_df.m.values
noisy_y = sel_df.mean_r

fig = plt.figure()
ax1 = fig.add_subplot(2, 1, 1)
ax2 = fig.add_subplot(2, 1, 2)

# # Non-linear Fit
# A, K, C = fit_exp_nonlinear(t, noisy_y)
# fit_y = model_func(t, A, K, C)
# plot(ax1, t, y, noisy_y, fit_y, (A0, K0, C0), (A, K, C0))
# ax1.set_title('Non-linear Fit')

# Linear Fit (Note that we have to provide the y-offset ("C") value!!
A, K = fit_exp_linear(t, y, C0)
fit_y = model_func(t, A, K, C0)
plot(ax2, t, y, noisy_y, fit_y, (A0, K0, C0), (A, K, 0))
ax2.set_title("Linear Fit")

plt.show()


# https://stackoverflow.com/questions/15624070/why-does-scipy-optimize-curve-fit-not-fit-to-the-data

# # todo
# make the 3d graph between r m and i
# seperate ms and msms
# ckean up to share with anton or yuri
# and veryfy gets same results on peakstrainer or lipidxolorere
