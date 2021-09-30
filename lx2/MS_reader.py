"""
tool to handle the spectra
"""
import pandas as pd
import numpy as np
from collections import namedtuple
import logging, os

log = logging.getLogger(os.path.basename(__file__))
from pyteomics import mzml, auxiliary


def mzML2DataFrames(filename, test_sample=False):  # this is with pytheomics
    scans = []
    peaks_dfs = []

    with mzml.read(filename) as reader:
        for item in reader:
            id = item["id"]
            idx = item["index"]
            fs = item["scanList"]["scan"][0]["filter string"]
            if item["scanList"]["count"] != 1:
                raise NotImplementedError(
                    "we dont read more than one scan per entry .... yet "
                )
            time = item["scanList"]["scan"][0][
                "scan start time"
            ]  # * 1 the dataframe makes a unitfloat into a float
            msLevel = item["ms level"]
            positive_scan = True if "positive scan" in item else False
            if not positive_scan:
                item["negative scan"]  # raise exceltion if not positive or negative
            p_data = item.get("precursorList", None)  # helper
            if p_data and p_data["count"] != 1:
                raise NotImplementedError(
                    "we dont read more than one scan per entry .... yet "
                )
            precursor_id = (
                p_data["precursor"][0]["spectrumRef"] if p_data else None
            )  # check if more than one
            target_mz = (
                p_data["precursor"][0]["isolationWindow"]["isolation window target m/z"]
                if p_data
                else None
            )
            max_i = item["base peak intensity"]
            tic = item["total ion current"]

            # collect the scans data
            row = (
                id,
                idx,
                fs,
                time,
                msLevel,
                positive_scan,
                precursor_id,
                max_i,
                tic,
                target_mz,
            )
            scans.append(row)

            # collect the peaks data
            i = item["intensity array"]
            m = item["m/z array"]
            cols = {"m": m, "i": i}
            df = pd.DataFrame(cols)
            df["id"] = id
            df.set_index("id", inplace=True)
            peaks_dfs.append(df)

            # for testing
            if test_sample and len(scans) > 100:  # TODO remove this
                break

        scansDF = pd.DataFrame(
            scans,
            columns=[
                "id",
                "idx",
                "filter_string",
                "time",
                "msLevel",
                "positive_scan",
                "precursor_id",
                "max_i",
                "tic",
                "target_mz",
            ],
        )
        scansDF.set_index("id", inplace=True)
        peaksDF = pd.concat(peaks_dfs)

    return scansDF, peaksDF


class SpectraUtil:
    "Util to handle spectra"

    def __init__(self, scansDF, peaksDF, filename=None):
        self._original_scansDF = scansDF
        self._original__peaksDF = peaksDF
        self.scansDF = self._original_scansDF
        self.peaksDF = self._original__peaksDF
        self._filename = filename

    @staticmethod
    def fromFile(filename, test_sample=False):
        return SpectraUtil(*mzML2DataFrames(filename, test_sample), filename)

    # note to help debug maybe use
    # @property
    # def scansDF(self):
    #     return self.scansDF

    def reset(self):
        print(f"reseting to original")
        self.scansDF = self._original_scansDF
        self.peaksDF = self._original__peaksDF

    def get_reset_copy(self):
        print(f"a copy of the original with nothing set... sorry no undo")
        return SpectraUtil(
            self._original_scansDF, self._original__peaksDF, self._filename
        )

    def get_current_copy(self):
        print(f"a copy of the current set... just in case")
        return SpectraUtil(self.scansDF, self.peaksDF, self._filename)

    def set_timerange(self, t0, t1):
        print(f"time range in seconds: {t0} to {t1}")
        self.scansDF = self.scansDF.loc[self.scansDF.time.multiply(60).between(t0, t1)]

    def set_mode(self, positive_mode=True):
        print(f"set mode to positive : {positive_mode}, (false means negative) ")
        self.scansDF = self.scansDF.loc[self.scansDF.positive_scan == positive_mode]

    def set_ms_level(self, level=1):
        print(f"set ms level to  : {level}")
        self.scansDF = self.scansDF.loc[self.scansDF.msLevel == level]

    def set_mass_range(self, m0, m1):
        print(f"time mass range from: {m0} to {m1}")
        self.peaksDF = self.peaksDF.loc[self.peaksDF.m.between(m0, m1)]

    def make_rel_i(self):
        print(f"calculate the relative intensities as: rel_i")
        # left_ and right_ index to keep the index
        spectraDF = self.peaksDF.merge(
            self.scansDF.max_i, left_index=True, right_index=True
        )
        self.peaksDF["rel_i"] = spectraDF.i / spectraDF.max_i

    def set_min_i(self, min_i=0):
        print(f"set the minimum intensity to {min_i}")
        self.peaksDF = self.peaksDF.loc[self.peaksDF.i > min_i]

    def round_m(self, decimals=4):
        print(f"set the precision of m/z to {decimals} decimal places")
        self.peaksDF["m"] = self.peaksDF.m.round(decimals)

    def get_fragment_scans(self, scan_index):
        print(f"scans triggered by the {scan_index}")
        return self._original_scansDF.loc[
            self._original_scansDF.precursor_id == scan_index
        ]

    def get_fragment_peaks(self, scan_index):
        print(f"Peaks triggered by the {scan_index} ")
        # for scantuple in spectraUtil.scansDF.itertuples():
        #   dosomething(spectraUtil.get_fragment_peaks(scantuple.Index))
        return self._original__peaksDF.loc[
            self._original__peaksDF.index.isin(
                self.get_fragment_scans(scan_index).index
            )
        ]

    def get_nearest(self, targetsDF, peaksDF=None, on="m", tol=0.01):
        print(f"find the nearest Peaks to the target_peaks with a tolerance of {tol}")
        if peaksDF == None:
            peaksDF = self.peaksDF

        s_peaksDF = peaksDF.reset_index().sort_values(on)
        s_targetDF = targetsDF.reset_index().sort_values(on)

        tmp_type = peaksDF[on].dtype
        s_targetDF[on] = s_targetDF[on].astype(tmp_type)
        s_targetDF["target"] = s_targetDF[on]

        return pd.merge_asof(
            s_peaksDF,
            s_targetDF,
            left_on=on,
            right_on=on,
            tolerance=tol,
            direction="nearest",
        ).dropna()
