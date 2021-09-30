import sys
import pandas as pd
import numpy as np


def lxquant(input_file, istd_file):
    InternalStandard = "InternalStandard"
    SPECIE = "SPECIE"

    df1 = pd.read_csv(input_file)
    df_istd = pd.read_csv(istd_file)

    df1_istd = df1.merge(df_istd, left_on=SPECIE, right_on=InternalStandard)
    df1_istd_tmp = df1_istd.select_dtypes(include=np.number)
    # maybe use vectorization at some time... just discovered it when looking for this
    # https://stackoverflow.com/questions/3379301/using-numpy-vectorize-on-functions-that-return-vectors
    df1_istd_ratio = df1_istd_tmp.apply(
        lambda x: x[-1] / x[1:], axis=1, result_type="expand"
    )  # started at 1 to drop mass
    df1_istd_ratio["LipidClass"] = df1_istd["LipidClass"]

    dfs = []
    for i in range(len(df1_istd_ratio)):
        an_istd = df1_istd_ratio.iloc[i]  # just one df1_istd_ratio
        df1_sub = df1[
            df1["CLASS"] == an_istd["LipidClass"]
        ]  # the identifiactions for that standard
        # select columns
        del an_istd["LipidClass"]  # this cant be multiplied
        cols = set(df1_sub.columns).intersection(
            set(an_istd.index)
        )  # the colmuns in common
        difCols = set(df1_sub.columns).difference(set(an_istd.index))
        # make a result dataframe
        res_df1_sub = df1_sub[difCols]  # make the temlate for the reuslts
        for col in cols:
            res_df1_sub[col] = df1_sub[col] * an_istd[col]
        dfs.append(res_df1_sub)
    result_df = pd.concat(dfs)
    return result_df


if __name__ == "__main__":
    input_file = sys.argv[1]
    istd_file = sys.argv[2]
    result_df = lxquant(input_file, istd_file)
    result_df.to_csv(input_file + ".quant.csv")
