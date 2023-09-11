"""functions to process SIM scans"""
import logging
import sys
import warnings
from pathlib import Path
from enum import Flag, auto

import numpy as np
import pandas as pd
from ms_deisotope import MSFileLoader
from pyteomics.xml import unitfloat
from ms_deisotope.data_source.memory import make_scan
from ms_deisotope.data_source.metadata import file_information
from ms_deisotope.data_source.metadata.scan_traits import (
    ScanAcquisitionInformation,
    ScanEventInformation,
)
import pickle
from ms_deisotope.data_source.scan.base import RawDataArrays
from ms_deisotope.output.mzml import MzMLSerializer

from .lx1_ref_masterscan import build_masterscan, df2listSurveyEntry
from .lx1_ref_read_write_spectra import get_settings, spectra_as_df


logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="[%(asctime)s] {%(name)s:%(lineno)d} %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(Path(__file__).stem)

def parse_filter_string(df, trim_overlap=None):
    pat = r"(.*)\[(\d+\.\d*)-(\d+\.\d*)\]"
    filter_strings = pd.Series(df["filter_string"].unique())
    filter_string_df = filter_strings.str.extract(pat)
    filter_string_df.columns = ["_prefix", "_from_mz", "_to_mz"]
    filter_string_df["_prefix"] = filter_string_df["_prefix"].astype(
        "category"
    )
    filter_string_df["_from_mz"] = filter_string_df["_from_mz"].astype(
        "float32"
    )
    filter_string_df["_to_mz"] = filter_string_df["_to_mz"].astype("float32")
    filter_string_df["filter_string"] = filter_strings
    filter_string_df["_is_lock"] = filter_string_df["_prefix"].str.contains(
        "lock"
    )

    assert (
        filter_string_df["_from_mz"] < filter_string_df["_to_mz"]
    ).all(), "filterstring is not in oreder"
    filter_string_df["_overlaps_next"] = (
        filter_string_df["_from_mz"] <= filter_string_df["_from_mz"].shift(-1)
    ) & (filter_string_df["_to_mz"] <= filter_string_df["_to_mz"].shift(-1))

    if trim_overlap is None:
        filter_string_df["_trim_overlap"] = filter_string_df[
            "_to_mz"
        ] - filter_string_df["_from_mz"].shift(-1)
        filter_string_df["_trim_overlap"] = (
            filter_string_df["_trim_overlap"] / 2
        )
    else:
        filter_string_df["_trim_overlap"] = trim_overlap

    return filter_string_df


def stitch_sim_scans(df, filter_string_df, replace_filter_string=False):
    merge = df.merge(filter_string_df, on="filter_string")
    mask = merge["mz"].between(
        merge["_from_mz"] + merge["_trim_overlap"],
        merge["_to_mz"] - merge["_trim_overlap"],
    )
    if replace_filter_string:
        new_names = filter_string_replacements(filter_string_df)
        df["filter_string"] = df["filter_string"].replace(new_names)

    return df[mask]


def filter_string_replacements(filter_string_df):
    filter_string_df["_group"] = (
        ~filter_string_df["_overlaps_next"]
    ).cumsum() + 1
    filter_string_df["_group"] = filter_string_df["_group"].shift()
    filter_string_df.iloc[0].at["_group"] = (
        1 if filter_string_df.at[0, "_overlaps_next"] else 0
    )
    filter_string_df["_from_mz"] = filter_string_df.groupby("_group")[
        "_from_mz"
    ].transform("min")
    filter_string_df["_to_mz"] = filter_string_df.groupby("_group")[
        "_to_mz"
    ].transform("max")
    filter_string_df["new_filter_string"] = filter_string_df.apply(
        lambda row: f'{row["_prefix"]}[{row["_from_mz"]}-{row["_to_mz"]}]',
        axis=1,
    )
    new_names = filter_string_df.set_index("filter_string")[
        "new_filter_string"
    ].to_dict()
    return new_names


def sim_trim(path, da=None):
    """trim the sim on the file, and create an mzml from the trimmed sims at location of original file

    Args:
        file (str): filepath to the spectra with sim in it
        da (float, optional): daltos to trim from each edge of sim. Defaults to None.
    """

    # NOTE https://git.mpi-cbg.de/labShevchenko/simtrim/-/blob/master/simtrim/simtrim.py
    # https://github.com/mobiusklein/ms_deisotope/issues/10#issuecomment-477393829
    # https://github.com/mobiusklein/ms_deisotope/issues/13#issuecomment-515017479

    source_reader = MSFileLoader(path)

    p = Path(path)
    dest = str(p.with_suffix("")) + "-trim.mzML"

    # calculate da
    if da is None or da <= 0:
        scan_window1, scan_window2 = None, None
        for bunch in (
            b
            for b in source_reader
            if "SIM" in b.precursor.annotations["filter string"]
        ):
            scan_window1 = scan_window2
            scan_window2 = bunch.precursor.acquisition_information[0][0]
            if scan_window1 and scan_window2:  # get only two entries then stop
                source_reader.reset()
                break
        delta = scan_window1.upper - scan_window2.lower
        if delta <= 0:
            raise ValueError(
                "The first two sims do not provide a valid `da` value"
            )
        da = delta / 2

    # write the file
    with open(dest, "wb") as fh:
        writer = MzMLSerializer(
            fh, n_spectra=len(source_reader.index), deconvoluted=False
        )
        description = source_reader.file_description()
        writer.add_file_information(description)
        writer.add_file_contents("profile spectrum")
        writer.add_file_contents("centroid spectrum")
        writer.remove_file_contents("profile spectrum")

        instrument_configs = source_reader.instrument_configuration()
        for config in instrument_configs:
            writer.add_instrument_configuration(config)

        software_list = source_reader.software_list()
        for software in software_list:
            writer.add_software(software)

        data_processing_list = source_reader.data_processing()
        for dp in data_processing_list:
            writer.add_data_processing(dp)

        processing = writer.build_processing_method()
        writer.add_data_processing(processing)

        for bunch in (
            b
            for b in source_reader
            if "SIM" in b.precursor.annotations["filter string"]
        ):
            if da is None:
                print("fix this")
            scan_window = bunch.precursor.acquisition_information[0][0]
            bunch.precursor.pick_peaks()
            bunch.precursor.peak_set = bunch.precursor.peak_set.between(
                scan_window.lower + da, scan_window.upper - da
            )
            writer.save(bunch)

        writer.complete()
        writer.format()

    return dest