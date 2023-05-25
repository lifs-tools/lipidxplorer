import logging
from re import L
import sys
from pathlib import Path
import pickle
from collections import namedtuple

import numpy as np
import pandas as pd

from ms_deisotope import MSFileLoader

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="[%(asctime)s] {%(name)s:%(lineno)d} %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(Path(__file__).stem)


Peak_arrays = namedtuple("Peak_arrays", "mz inty")


class lx2_data_files:
    # Options
    # spectraset
    # mfqlset
    pass


class lx2_spectra:
    def __init__(self, spectra_path, options) -> None:
        self.spectra_path = spectra_path
        self.options = options

        self.ms1_scans = []
        self.ms1_peaks = []
        self.ms2_scans = []
        self.ms2_peaks = []

        # https://mobiusklein.github.io/ms_deisotope/docs/_build/html/Quickstart.html
        # one standard entry point for multiple file types
        self._spectra_reader = self._get_reader()
        self.populate_scans_peaks()
        self._spectra_reader.close()

        self.ms1_delta_res = self.get_ms1_delta_res()
        self.average_ms1_scans = self.averaged_ms1_scans()
        self.average_ms1_peaks = self.averaged_ms1_scans()
        # self.recalibration_peaks_ms1 = self.get_recalibration_peaks_ms1()

        # self.average_ms1_scan = self.get_average_ms1_scan()
        # self.average_ms1_peaks = self.get_average_ms1_peaks()

        # self.precursor_grouping = self.get_precursor_grouping()

        # self.ms2_delta_res = self.get_ms2_delta_res()
        # self.averaged_ms2_scans = self.averaged_ms2_scans()
        # self.averaged_ms2_peaks = self.averaged_ms2_peaks()
        # self.recalibration_peaks_ms2 = self.get_recalibration_peaks_ms2()

        # self.average_ms2_scan = self.get_average_ms2_scan()
        # self.average_ms2_peaks = self.get_average_ms2_peaks()

    @property
    def stem(self):
        return Path(self.spectra_path).stem
    
    def dump(self, pkl_path):
        with open(pkl_path, 'wb') as handle:
            pickle.dump(self,handle)

    def _get_reader(self):
        reader = MSFileLoader(self.spectra_path)
        reader.make_iterator(grouped=False)
        reader.initialize_scan_cache()

        return reader

    def populate_scans_peaks(self):
        time_range = self.options["timerange"]
        time_start = 0 if not time_range else time_range[0]
        time_end = float("inf") if not time_range else time_range[1]
        ms1_mass_range = self.options["MSmassrange"]
        ms1_start = 0 if not ms1_mass_range else ms1_mass_range[0]
        ms1_end = float("inf") if not ms1_mass_range else ms1_mass_range[1]
        ms2_mass_range = self.options["MSMSmassrange"]
        ms2_start = 0 if not ms2_mass_range else ms2_mass_range[0]
        ms2_end = float("inf") if not ms2_mass_range else ms2_mass_range[1]

        polarity_guard = None

        for scan in self._get_reader():
            if polarity_guard is None:
                polarity_guard = scan.polarity
            if polarity_guard != scan.polarity:
                raise ValueError("Mixed polarity is not supported")
            if not (time_start / 60 < scan.scan_time < time_end / 60):
                continue

            if scan.ms_level == 1:
                self.ms1_scans.append(scan)
                mz_mask = (scan.arrays.mz > ms1_start) & (scan.arrays.mz < ms1_end)
                inty_mask = scan.arrays.intensity > 0
                mask = mz_mask & inty_mask
                self.ms1_peaks.append(
                    Peak_arrays(scan.arrays.mz[mask], scan.arrays.intensity[mask])
                )
            else:
                self.ms2_scans.append(scan)
                mz_mask = (scan.arrays.mz > ms2_start) & (scan.arrays.mz < ms2_end)
                inty_mask = scan.arrays.intensity > 0
                mask = mz_mask & inty_mask
                self.ms2_peaks.append(
                    Peak_arrays(scan.arrays.mz[mask], scan.arrays.intensity[mask])
                )

        return None

    def get_ms1_delta_res(self, minimum_delta=0.0001):
        scan_count = len(self.ms1_peaks)
        if scan_count < 2:
            log.error("not enough scans for delta resolution calculatinos")
            raise ValueError("not enough scans for delta resolution calculatinos")
        mz_array = np.concatenate([peak_arrays.mz for peak_arrays in self.ms1_peaks])
        df = pd.DataFrame({"mz": mz_array})
        df["mz_diff"] = df["mz"].diff()
        df = df.sort_values("mz", ascending=False)
        df["window_diff"] = (
            df["mz_diff"]
            .where(df["mz_diff"] > minimum_delta, np.nan)
            .rolling(scan_count, min_periods=2)
            .mean()
        )
        df["delta_res"] = df["window_diff"].cummin()

        # below for reference in as a reminders
        # df['scan_id_f'] = df['scan_id'].factorize()[0]
        # df['scan_cnt'] = df.scan_id_f.rolling(scan_count).apply(lambda s: len(set(s)))
        # df['mean_mz_diff']  = df.mz_diff.rolling(window = 31, center=True, win_type ='cosine' ).mean() # note win_type =should be tukey

        return df.groupby("delta_res")["mz"].first().reset_index()

    def averaged_ms1_scans(self):
        result = set()
        for scan in self.ms1_scans:
            filter_string = (
                scan.annotations["filter string"]
                if scan.annotations
                else scan._data["filterLine"]
            )
            result.update(filter_string.split())
        return " ".join(result)

    def averaged_ms1_peaks(self):
        # add log to dump steps
        # group within scan as lx1
        # group within scan as lx2
        # group within scan as lx2 delta_res
        # merge within scan as lx1
        # merge within scan as lx2

        # group within spectra
        # filter repetition
        # merge within spectra
        # recalibrate
        pass


def test_readfile():
    spectra_path = (
        r"test_resources\benchmark128\spectra\190321_Serum_Lipidextract_368723_01.mzML"
    )
    options = {  # NOTE to initialize Masterscan(options) a dictionalry is not enough
        "timerange": (33.0, 1080.0),
        "MSmassrange": (360.0, 1000.0),
        "MSMSmassrange": (150.0, 1000.0),
        "MScalibration": [680.4802],
        "MSMScalibration": None,
    }
    scan = lx2_spectra(spectra_path, options)
    assert scan is not None


test_readfile()
