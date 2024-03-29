import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import namedtuple
from chemParser import txt2dict


class Targets_util:

    mass_of = {
        "C": 12,
        "H": 1.0078250321,
        "N": 14.0030740052,
        "P": 30.97376151,
        "O": 15.9949146221,
        "S": 31.97207069,
    }

    def __init__(self, elements):
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
            self._ranges[name] = np.arange(bounds[0], bounds[1] + 1)

    def _makeDF(self):
        index = pd.MultiIndex.from_product(
            self._ranges.values(), names=self._ranges.keys()
        )
        self._df = pd.DataFrame(index=index).reset_index()

    def _cal_M(self):
        self._df["m"] = 0
        for colName in self._df.columns.intersection(self.mass_of.keys()):
            self._df["m"] += self._df[colName] * self.mass_of[colName]

    def _cal_dbr(self):
        x = (
            self._df.get("Cl", 0)
            + self._df.get("Br", 0)
            + self._df.get("I", 0)
            + self._df.get("F", 0)
        )
        self._df["dbr"] = (
            self._df.get("C", 0)
            + 1
            - self._df.get("H", 0) / 2
            - x / 2
            + self._df.get("N", 0) / 2
        )

    def _cal_chem(self):
        # https://stackoverflow.com/questions/52673285/performance-of-pandas-apply-vs-np-vectorize-to-create-new-column-from-existing-c
        self._df["chem"] = ""
        for colName in self._df.columns.intersection(self.mass_of.keys()):
            self._df["chem"] += colName + self._df[colName].apply(str) + " "
        self._df["chem"] = self._df["chem"].str[:-1]

    def set_dbr(self, dbr_u, dbr_l):
        self._df = self._df.loc[self._df.dbr.between(dbr_u, dbr_l)]

    @staticmethod
    def set_max_daltons(matchesDF, max_daltons=0.01):
        matchesDF["err"] = matchesDF["m"] - matchesDF["target"]
        matchesDF["err"] = matchesDF["err"].abs()
        matchesDF["min_err"] = matchesDF.groupby(["id", "chem"])["err"].transform("min")
        matchesDF = matchesDF.loc[matchesDF["err"] == matchesDF["min_err"]]
        matchesDF.drop("min_err", axis=1, inplace=True)

        matchesDF["ppm"] = matchesDF["err"] / matchesDF["target"] * 1_000_000
        matchesDF = matchesDF.loc[matchesDF["err"] <= max_daltons]
        # matchesDF.drop('err', axis = 1, inplace=True)
        return matchesDF

    @staticmethod
    def makeAllCombo(pr_df, fr_df):
        pr_df = pr_df.add_prefix("PR_")
        fr_df = fr_df.add_prefix("FR_")
        pr_df.loc[:, "key"] = 0
        fr_df.loc[:, "key"] = 0
        in_df = pr_df.merge(fr_df, on="key")

        pr_df.drop("key", 1, inplace=True)
        fr_df.drop("key", 1, inplace=True)
        in_df.drop("key", 1, inplace=True)

        return in_df

    @staticmethod
    def devideAllCombo(all_df):
        # TODO try https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.filter.html
        # df filter
        all_df.sort_values(["PR_ppm", "FR_ppm"], inplace=True)
        cols = all_df.columns
        pr_cols = [col for col in cols if col.startswith("PR_")]
        fr_cols = [col for col in cols if col.startswith("FR_")]

        pr_df = all_df.loc[:, pr_cols]
        fr_df = all_df.loc[:, fr_cols]
        pr_df.sort_values("PR_ppm", inplace=True)
        pr_df.drop_duplicates(inplace=True)
        fr_df.drop_duplicates(inplace=True)
        return pr_df, fr_df

    @staticmethod
    def suchThat(df, query):
        return df.query(query)

    @staticmethod
    def summaryDF(df, prefix="PR_", quantile=0.25):
        # TODO try https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.filter.html
        groups = df.groupby([prefix + "chem"])
        columns = ["C_dbr", "ppm_mean", "i_mean", "i_rsd", "count"]
        columns = [prefix + col for col in columns]
        tups = []
        for e, g_df in groups:
            tup = (
                e,
                g_df[prefix + "ppm"].mean(),
                g_df[prefix + "i"].mean(),
                g_df[prefix + "i"].std() / g_df[prefix + "i"].mean() * 100,
                g_df[prefix + "m"].count(),
            )
            tups.append(tup)
        df_summary = pd.DataFrame(tups, columns=columns)

        sort_col = columns[1]
        df_summary.sort_values(sort_col, ascending=True, inplace=True)
        sort_smallest = df_summary[sort_col] <= df_summary[sort_col].quantile(quantile)
        return df_summary.loc[sort_smallest]

    @staticmethod
    def lx1_DF(df):
        """makes the result as similar as lx1 as possible, ie averaged

        Arguments:
            df {dataframe} -- that contins all the data as from 'suchthat'

        Returns:
            dataframe -- with the averaged values
        """
        columns = df.columns
        tups = []
        for pr_chem, pr_df in df.groupby("PR_chem"):
            for fr_chem, fr_df in pr_df.groupby("FR_chem"):
                tup = ()
                fv_idx = fr_df.first_valid_index()
                for col in columns:
                    if col[3:] in ["m", "i"]:
                        tup += (fr_df[col].mean(),)
                    else:
                        tup += (fr_df[col][fv_idx],)
                tups.append(tup)
        df_summary = pd.DataFrame(tups, columns=columns)

        return df_summary

    @staticmethod
    def lollipop_plot(m, i):
        # https://python-graph-gallery.com/180-basic-lollipop-plot/
        # https://stackoverflow.com/questions/1358977/how-to-make-several-plots-on-a-single-page-using-matplotlib
        (markerline, stemlines, baseline) = plt.stem(m, i)  # , markerfmt=' ')
        plt.setp(baseline, visible=False)
        return plt

    @staticmethod
    def showAll_lollipop(df, prefix="PR_", sample=False):
        groups = df.groupby([prefix + "C", prefix + "dbr"])
        for e, g_df in groups:
            plt = Targets_util.lollipop_plot(g_df[prefix + "m"], g_df[prefix + "i"])
            plt.title(e)
            plt.xlim([g_df[prefix + "m"].min(), g_df[prefix + "m"].max()])
            plt.show()
            if sample:
                break  # ony show one

    @staticmethod
    def var2Target(var):
        elements = txt2dict(var.object.txt)
        target = Targets_util(elements)
        dbrs = var.Options.get("dbr", (None, None))
        target.set_dbr(*dbrs)
        return target

    @staticmethod
    def vars2targets(vars):
        return [Targets_util.var2Target(var) for var in vars]
