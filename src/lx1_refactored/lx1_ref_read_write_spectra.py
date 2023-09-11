"""converting a spectra file *.mzML into a dataframe
and write dataframe to *.mzML
and selecting th data in the spectra
ie limiting the scope of scans, mass, intensity or time


"""
import logging
import pickle
import sys
import warnings
from datetime import datetime
from enum import Flag, auto
from pathlib import Path

import numpy as np
import pandas as pd
from ms_deisotope import MSFileLoader
from ms_deisotope.data_source.memory import make_scan
from ms_deisotope.data_source.metadata import file_information
from ms_deisotope.data_source.metadata.scan_traits import (
    ScanAcquisitionInformation, ScanEventInformation)
from ms_deisotope.data_source.scan.base import RawDataArrays
from ms_deisotope.output.mzml import MzMLSerializer
from pyteomics.xml import unitfloat

from .lx1_ref_masterscan import build_masterscan, df2listSurveyEntry

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="[%(asctime)s] {%(name)s:%(lineno)d} %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(Path(__file__).stem)

def get_settings(options):
    """convert options into a dict called settings, to limit the scope of scans that are read

    Returns:
        dict: settings needed for reading
    """
    # print(options)
    res = {}
    time_range = options["timerange"]
    res["time_start"] = 0 if not time_range else time_range[0]
    res["time_end"] = float("inf") if not time_range else time_range[1]
    ms1_mass_range = options["MSmassrange"]
    res["ms1_start"] = 0 if not ms1_mass_range else ms1_mass_range[0]
    res["ms1_end"] = float("inf") if not ms1_mass_range else ms1_mass_range[1]
    ms2_mass_range = options["MSMSmassrange"]
    res["ms2_start"] = 0 if not ms2_mass_range else ms2_mass_range[0]
    res["ms2_end"] = float("inf") if not ms2_mass_range else ms2_mass_range[1]
    res["polarity"] = -1 if options["polarity"] == "-" else 1 # None means use both
    return res

def scan_to_DF(scan, path, mz_start, mz_end):
    """convert a single scan from a spectra into a dataframe

    Args:
        scan (_type_): _description_
        path (_type_): _description_
        mz_start (_type_): _description_
        mz_end (_type_): _description_

    Returns:
        dataframe: the relevant scan information as columns
    """
    _categorical_cols = [
        "stem",
        "scan_id",
        "filter_string",
        "precursor_id",
        "precursor_mz",
        "polarity",
    ]
    a = scan.arrays
    df = pd.DataFrame(
        {
            "mz": a.mz.astype("float32"),
            "inty": a.intensity.astype("float32"),
            "stem": path.stem,
            "scan_id": scan.scan_id,
            "filter_string": scan.annotations["filter string"]
            if scan.annotations
            else scan._data["filterLine"],
            "precursor_id": scan.precursor_information.precursor.scan_id
            if scan.precursor_information
            else np.NaN,
            "precursor_mz": scan.precursor_information.mz
            if scan.precursor_information
            else 0,
            "polarity": scan.polarity,
        }
    )
    df = df[df.mz.between(mz_start, mz_end) & df.inty > 0]
    for col in _categorical_cols:
        df[col] = df[col].astype("category")
    return df

class MS_level(Flag):
    ms1 = auto()
    ms2 = auto()
    sim = auto()

def _get_ms_level(ms_level_ish):
    """converts a string or int into an MS_level,
    so users can input anything

    Args:
        ms_level_ish (str or int): comma sperated str or int or
    """
    # TODO use match case
    res = None
    ms_level_ish = str(ms_level_ish).lower()

    if '1' in ms_level_ish:
        res = MS_level.ms1 if res is None else res | MS_level.ms1
    if '2' in ms_level_ish:
        res = MS_level.ms2 if res is None else res | MS_level.ms2
    if 'sim' in ms_level_ish:
        res = MS_level.sim if res is None else res | MS_level.sim
    
    if res is None:
        raise ValueError(ms_level_ish, "Value must be a comma seperated string with 1, 2 or sim") 
    
    return res



def spectra_as_df(
    path,
    ms_level='1',
    time_start=0,
    time_end=float("inf"),
    ms1_start=0,
    ms1_end=float("inf"),
    ms2_start=0,
    ms2_end=float("inf"),
    polarity=1,
):
    """read a spectra into a dataframe with contstraints,
     ms_level is string like: "1" or "ms1,ms2" or "sim"
    poarity can be: 0 for both +1 positive and -1 negative

    Args:
        path (_type_): _description_
        ms_level (str, optional): the ms level that should be read, comma seperated string. Defaults to '1'.
        time_start (int, optional): seconds, read start time . Defaults to 0.
        time_end (_type_, optional): seconds, read end time. Defaults to float("inf").
        ms1_start (int, optional): da, lowest mass to include. Defaults to 0.
        ms1_end (_type_, optional): da, highest mass to include. Defaults to float("inf").
        ms2_start (int, optional): da, lowest mass to include, for ms2 scans. Defaults to 0.
        ms2_end (_type_, optional): da, lowest mass to include, for ms2 scans. Defaults to float("inf").
        polarity (int, optional): -1, +1 or 0 for both. Defaults to 1.

    Returns:
        _type_: _description_
    """
    path = Path(path)
    assert polarity in [-1,+1,0], 'polarity must be -1, +1 or 0'
    ms_level = _get_ms_level(ms_level)
    
    dfs = []
    with MSFileLoader(str(path)) as r:
        r.get_scan_by_time(time_start / 60)
        r.start_from_scan(r.get_scan_by_time(time_start / 60).id)

        for b in r:
            if not (time_start / 60 < b.precursor.scan_time < time_end / 60):
                continue
            if b.precursor.polarity != polarity:
                warnings.warn(
                    f"polarity {polarity} not found in spectra {path}"
                )
                continue

            # check if its a sim scan
            scan = b.precursor
            filter_string = (
                scan.annotations["filter string"]
                if scan.annotations
                else scan._data["filterLine"]
            )

            if MS_level.ms1 in ms_level:
                df = scan_to_DF(b.precursor, path, ms1_start, ms1_end)
                dfs.append(df)
            if MS_level.sim in ms_level and " sim " in filter_string.lower():
                df = scan_to_DF(b.precursor, path, ms1_start, ms1_end)
                dfs.append(df)

            # read the ms2 scans
            if MS_level.ms2 in ms_level:
                for p in b.products:
                    if not (time_start / 60 < p.scan_time < time_end / 60):
                        continue
                    if not (ms1_start < p.precursor_information.mz < ms1_end):
                        continue
                    df = scan_to_DF(p, path, ms2_start, ms2_end)
                    dfs.append(df)

    df = pd.concat(dfs)
    log.info(f"spectra {path.stem}, size: {df.shape}")
    return df

########## filter some scan before averaging

def drop_fuzzy(df):
    """drop the first few scans that have a low total ion count"""
    raise NotImplementedError()
    # fraction_of_average_intensity = 0.1
    # spectras_sum_inty = (
    #     spectra_df.loc[spectra_df.precursor_id.isna()]
    #     .groupby("scan_id")["inty"]
    #     .sum()
    # )
    # sum_inty_mean = spectras_sum_inty.mean()
    # spectras_sum_inty = spectras_sum_inty.to_dict()

    # to_drop = []
    # for (
    #     scan_id
    # ) in spectra_df.scan_id.drop_duplicates():  # this maintains order
    #     if (
    #         spectras_sum_inty[scan_id]
    #         < sum_inty_mean * fraction_of_average_intensity
    #     ):  # one order
    #         to_drop.append(scan_id)
    #     else:
    #         break

    # return spectra_df.loc[~spectra_df.scan_id.isin(to_drop)]

def dataframe2mzml(df, source, destination=None):
    """write a dataframe into a mzml file

    Args:
        df (dataframe): contains masses and intensities and scans (mz,inty, filter_string)
        source (str: filepath): the basis for this file, some metadata is copied
        destination (str: filepath, optional): name of the file that shouild be generated or defaults to adding the date to the source file name. Defaults to None.

    Returns:
        str: the name of the file that was destination
    """
    # NOTE https://github.com/mobiusklein/ms_deisotope/blob/master/src/ms_deisotope/data_source/text.py
    # https://github.com/mobiusklein/ms_deisotope/blob/master/examples/csv_to_mzml.py
    # see https://git.mpi-cbg.de/labShevchenko/simtrim/-/blob/master/simtrim/simtrim.py#L35
    # or https://mobiusklein.github.io/ms_deisotope/docs/_build/html/output/mzml.html
    source_reader = MSFileLoader(source)
    scan1 = next(source_reader)
    scan1 = scan1.precursor
    scan1.pick_peaks()
    source = Path(source)

    if destination is None:
        # Get the current date and time
        current_datetime = datetime.now()

        # Format the date and time as a string in a tight format
        tight_datetime_string = current_datetime.strftime("%Y%m%d%H%M%S")
        destination = Path(
            str(source.with_suffix("")) + tight_datetime_string + ".mzml"
        )

    with MzMLSerializer(
        open(destination, "wb"),
        1,
        deconvoluted=False,
        sample_name=destination.stem,
        build_extra_index=False,
    ) as writer:
        # writer.copy_metadata_from(source) #NOTE not sure if is needed
        writer.add_file_contents(file_information.MS_MSn_Spectrum.name)
        writer.add_data_processing(writer.build_processing_method())

        writer.save(scan1)
        index = 0
        for filter_string, gdf in df.groupby("filter_string"):
            signal = RawDataArrays(gdf["mz"].values, gdf["inty"].values)
            scanEventInformation = ScanEventInformation(
                unitfloat(0, "minute"),
                [],
                traits={"filter string": filter_string},
            )
            acquisition_information = ScanAcquisitionInformation(
                "no combination", [scanEventInformation,],
            )
            # Create a new spectrum
            index += 1
            scan = make_scan(
                signal,
                1,
                f"index={index}",
                0,
                0,
                is_profile=False,
                polarity=gdf.iloc[0].at["polarity"],
                acquisition_information=acquisition_information,
                precursor_information=None,
            )
            scan.pick_peaks()

            # Write the spectrum to the MzML file
            writer.save(scan)

    return destination
