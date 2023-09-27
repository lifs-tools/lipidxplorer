#!/bin/env python2.7
# encoding: utf-8
"""
Created on 29.03.2017
PeakStrainer is a tool to reduce the size of an MS spectra,
usage: peakStrainer spectra_file.raw
@author: mirandaa
"""
import sys
import os
import time
import logging
import csv
from tools.peakStrainer.utils.peakStrainer_util import write2templateMzXML
import itertools
import math
import re
from _collections import defaultdict
import collections

log = logging.getLogger(os.path.basename(__file__))
from tools.peakStrainer.lib import MSFileReader
from collections import namedtuple
import numpy as np
import glob, os
from pyteomics import mzxml, mzml
import argparse


__version__ = "17.12.15.0"


def main(folder, technial_replicates=True, rcf_a=5408000.0, rcf_b=0.5):
    log.setLevel(logging.DEBUG)
    if log.level == logging.DEBUG:
        log.addHandler(logging.StreamHandler())  # log to console
    if log.level == logging.DEBUG:
        logging.basicConfig(filename="peakStrainer.log", filemode="w")

    log.debug("Start %f", time.perf_counter())
    #     if len(sys.argv) == 1:
    #         print("A filename must be provided")
    #         raise SystemExit

    #     filename = " ".join(sys.argv[1:])
    #     extension = os.path.splitext(filename)[1]
    #     if extension.lower() == '.raw':
    #         scans = ThermoRawfile2Scans(filename)
    #     elif extension.lower() == '.mzxml':
    scans = mzXML2Scans(folder, technial_replicates=technial_replicates)
    #     elif extension.lower() == '.mzml':
    #         scans = mzML2Scans(filename)

    if log.level == logging.DEBUG:
        ThermoRawfile2Scans_csv(scans)

    filename = " ".join(sys.argv[1:])
    scans = ThermoRawfile2Scans(filename)
    if log.level == logging.DEBUG:
        ThermoRawfile2Scans_csv(scans)

    """ filtering by scan
    scans = filterScanBy_retentionTime(scans)
    scans = filterScanBy_filterline(scans)
    scans = filterScanBy_samples(scans, step_size = 3)
    """
    scans = removeLockFromHeader(scans)
    # Note: mergePeaksOnFilterline_withRandom to generate testing data
    scans = roundCollisionEnergy(scans)
    filterLines = mergePeaksOnFilterline(scans)
    if log.level == logging.DEBUG:
        filterlinePeaks_csv(filterLines, "mergePeaksOnFilterline.csv")

    preFiltered_filterlines = {
        k: preliminaryFilter(v) for k, v in list(filterLines.items())
    }
    # preFiltered_filterlines = {k: preliminaryReductionFilter(v) for k, v in filterLines.items()}
    if log.level == logging.DEBUG:
        filterlinePeaks_csv(preFiltered_filterlines, "preliminaryFilter.csv")

    """ create bins for peaks
    filterlines_withBins = {k: generateBins_decimalPlaces(v) for k, v in filterLines.items()}
    filterlines_withBins = {k: generateBins_resolution(v) for k, v in filterLines.items()}
    filterlines_withBins = {k: generateBins_theoreticalResolution(v) for k, v in preFiltered_filterlines.items()}
    filterlines_withBins = {k: generateBins_resolutionPowerFunc(v,a,b) for k, v in preFiltered_filterlines.items()} # 5408000.0, 2096000.0
    """
    filterlines_withBins = {
        k: generateBins_resolutionPowerFunc(v, rcf_a, rcf_b)
        for k, v in list(filterLines.items())
    }
    if log.level == logging.DEBUG:
        filterlinePeaks_csv(filterlines_withBins, "generateBins.csv")

    #     filterlines_withBins_ms = {k: generateBins_resolutionPowerFunc(v, 5408000.0, 0.5 ) for k, v in filterLines.items() if ' ms ' in k }
    #     filterlines_withBins_msms = {k: generateBins_resolutionPowerFunc(v, 5408000.0, 0.5 ) for k, v in filterLines.items() if ' ms ' not in k}
    #     filterlines_withBins = filterlines_withBins_ms.update(filterlines_withBins_msms)
    #     for different function for ms and for msms

    filterlines_withBins = {
        k: alterBins_mergeOverlap(v)
        for k, v in list(filterlines_withBins.items())
    }
    if log.level == logging.DEBUG:
        filterlinePeaks_csv(filterlines_withBins, "mergeBins.csv")

    """ put each mass in a bin
    filterlines_inBins = {k: sortMassIn_sortWindow(v) for k, v in filterlines_withBins.items()}
    filterlines_inBins = {k: sortMassIn_FirstBin(v) for k, v in filterlines_withBins.items()}
    filterlines_inBins = {k: sortMassIn_NarrowestBin(v) for k, v in filterlines_withBins.items()}
    """
    filterlines_inBins = {
        k: sortMassIn_FirstBin(v)
        for k, v in list(filterlines_withBins.items())
    }
    if log.level == logging.DEBUG:
        filterlinePeaks_csv(filterlines_inBins, "sortMassIn.csv")

    filterlines_binData = {
        k: aggregateBinData(v) for k, v in list(filterlines_inBins.items())
    }
    if log.level == logging.DEBUG:
        filterlineBins_csv(filterlines_binData, "aggregateBinData.csv")

    filterlines_filtered = {
        k: filterBins(v) for k, v in list(filterlines_binData.items())
    }
    if log.level == logging.DEBUG:
        filterlineBins_csv(filterlines_filtered, "filteredBins.csv")

    filtered_peaks = {
        k: bins2Peaks(v, filterlines_inBins[k])
        for k, v in list(filterlines_filtered.items())
    }
    if log.level == logging.DEBUG:
        filterlinePeaks_csv(filtered_peaks, "mzXMLdata.csv")

    # can't use filtered bins in mzxml because it is not readable by seems
    #     filtered_bins = {k: formatPeaks(v) for k, v in filterlines_filtered.items()}# this makes an average of the bin
    perFiles = make_perFile(filtered_peaks)

    for perfile in perFiles:
        filtered_bins = perFiles[perfile]
        filtered_bins = reorder4lipidxplorer(filtered_bins)
        newfilename = perfile[:-4] + ".mzXML"
        log.info("Writing results to %s", newfilename)
        write2templateMzXML(newfilename, filtered_bins)
    #     order = [' ms ', '.33-', ' ms ']
    #     filtered_bins = reorderScans(filtered_bins, order)

    log.debug("finish %f", time.process_time())


def make_perFile(filtered_peaks):
    log.info("split the fltered peaks into files from scans")
    # get the files
    outfiles = defaultdict(dict)
    for filterline in filtered_peaks:
        masses, intens, files = filtered_peaks[filterline]
        uniqFiles = set(files)
        for file in uniqFiles:
            filterlines_of_file = outfiles[file]
            fmass = [m for m, i, f in zip(masses, intens, files) if f == file]
            fintens = [
                i for m, i, f in zip(masses, intens, files) if f == file
            ]
            filterlines_of_file[filterline] = (fmass, fintens)
    return outfiles


def isElbowIIT(rawfile, end, scanNum, filterLine):
    nextScan = min(scanNum + 1, end)
    nextNextScan = min(scanNum + 2, end)
    next_filterLine = rawfile.GetFilterForScanNum(nextScan)
    nextNext_filterLine = rawfile.GetFilterForScanNum(nextNextScan)
    if filterLine != next_filterLine or nextScan == end:  # there is no elbow
        return False
    ion_injection_time = rawfile.GetTrailerExtraForScanNum(scanNum)[
        "Ion Injection Time (ms)"
    ]
    next_ion_injection_time = rawfile.GetTrailerExtraForScanNum(nextScan)[
        "Ion Injection Time (ms)"
    ]

    if (
        next_filterLine != nextNext_filterLine
    ):  # can't average so use estimation
        return ion_injection_time > next_ion_injection_time + (
            math.sqrt(next_ion_injection_time) * 3
        )

    nextNext_ion_injection_time = rawfile.GetTrailerExtraForScanNum(
        nextNextScan
    )["Ion Injection Time (ms)"]
    average = (next_ion_injection_time + nextNext_ion_injection_time) / 2
    stdev = math.sqrt(
        (next_ion_injection_time - average) ** 2
        + (nextNext_ion_injection_time - average) ** 2
    )

    # TODO use pandas dataframe and getdo groupby and average to get these numbers
    return ion_injection_time > average + max(
        (stdev * 3), (math.sqrt(next_ion_injection_time) * 3)
    )  # max used because sometimes the deviation is too small


def ThermoRawfile2Scans(file_path, dropElbowIIT=False):
    if True:
        return ThermoRawfile2Scans_local(file_path)
    # NOTE: for testing use ThermoRawfile2Scans_sample instead
    log.info("raw file: %s", file_path)
    rawfile = MSFileReader.ThermoRawfile(file_path)

    start = rawfile.FirstSpectrumNumber
    end = rawfile.GetLastSpectrumNumber()

    MSrawscans = []
    for scanNum in range(start, end + 1):
        peak_datas = rawfile.GetLabelData(scanNum)[0]
        filterLine = rawfile.GetFilterForScanNum(scanNum)
        retTime = rawfile.RTFromScanNum(scanNum) * 60
        row = (scanNum, filterLine, peak_datas, retTime, file_path)

        isElbow = isElbowIIT(rawfile, end, scanNum, filterLine)
        if dropElbowIIT and isElbow:
            log.info(
                " Scan Number {} is removed, it has increased Ion Injection Time, is probably invalid".format(
                    scanNum
                )
            )
            continue

        MSrawscans.append(row)

    log.info("Scan Count is %d", len(MSrawscans))
    # Note: to reshape into lists use
    # scanNum, filterLine, peak_datas, retTime = list(zip(*MSrawscans)

    # Note: to get list of mass use
    # peak_data = peak_datas[0]
    # peak_data.mass

    return MSrawscans


import numpy as np
import ctypes
import clr, System
from System import Array, Int32
from System.Runtime.InteropServices import GCHandle, GCHandleType

_MAP_NET_NP = {
    "Single": np.dtype("float32"),
    "Double": np.dtype("float64"),
    "SByte": np.dtype("int8"),
    "Int16": np.dtype("int16"),
    "Int32": np.dtype("int32"),
    "Int64": np.dtype("int64"),
    "Byte": np.dtype("uint8"),
    "UInt16": np.dtype("uint16"),
    "UInt32": np.dtype("uint32"),
    "UInt64": np.dtype("uint64"),
    "Boolean": np.dtype("bool"),
}


def asNumpyArray(netArray):
    """
    Given a CLR `System.Array` returns a `numpy.ndarray`.  See _MAP_NET_NP for
    the mapping of CLR types to Numpy dtypes.
    """
    dims = np.empty(netArray.Rank, dtype=int)
    for I in range(netArray.Rank):
        dims[I] = netArray.GetLength(I)
    netType = netArray.GetType().GetElementType().Name

    try:
        npArray = np.empty(dims, order="C", dtype=_MAP_NET_NP[netType])
    except KeyError:
        raise NotImplementedError(
            "asNumpyArray does not yet support System type {}".format(netType)
        )

    try:  # Memmove
        sourceHandle = GCHandle.Alloc(netArray, GCHandleType.Pinned)
        sourcePtr = sourceHandle.AddrOfPinnedObject().ToInt64()
        destPtr = npArray.__array_interface__["data"][0]
        ctypes.memmove(destPtr, sourcePtr, npArray.nbytes)
    finally:
        if sourceHandle.IsAllocated:
            sourceHandle.Free()
    return npArray


def ThermoRawfile2Scans_local(file_path):
    # NOTE: for testing use ThermoRawfile2Scans_sample instead
    log.info("raw file: %s", file_path)
    rawfile = MSFileReader.ThermoRawfile(file_path)
    source = rawfile._source

    start = rawfile.FirstSpectrumNumber()
    end = rawfile.LastSpectrumNumber()

    Labels = namedtuple(
        "Labels", "mass intensity resolution baseline noise charge"
    )

    def get_out(raw, scan):
        data = raw.GetCentroidStream(scan, False)

        return Labels(
            tuple(asNumpyArray(data.Masses)),
            tuple(asNumpyArray(data.Intensities)),
            tuple(asNumpyArray(data.Resolutions)),
            tuple(asNumpyArray(data.Baselines)),
            tuple(asNumpyArray(data.Noises)),
            tuple(asNumpyArray(data.Charges)),
        )

    MSrawscans = []
    for scanNum in range(start, end + 1):
        data = source.GetCentroidStream(scanNum, False)
        if data.Length == 0:
            log.debug(
                f"scan {scanNum} {source.GetScanEventForScanNumber(scanNum).ToString()} has no masses"
            )
            continue
        peak_datas = get_out(source, scanNum)
        filterLine = source.GetScanEventForScanNumber(scanNum).ToString()
        retTime = source.RetentionTimeFromScanNumber(scanNum) * 60
        row = (scanNum, filterLine, peak_datas, retTime, file_path)
        MSrawscans.append(row)

    log.info("Scan Count is %d", len(MSrawscans))
    # Note: to reshape into lists use
    # scanNum, filterLine, peak_datas, retTime = list(zip(*MSrawscans)
    # retTime, file_name   #Note: to get list of mass use
    # peak_data = peak_datas[0]
    # peak_data.mass

    return MSrawscans


def removeLockFromHeader(scans):
    log.info("removeLockFromHeader")
    newScans = []
    for scan in scans:
        scanList = list(scan)
        header = scanList[1]
        scanList[1] = header.replace("lock ", "")
        newScans.append(scanList)
    return newScans


def mzXML2Scans(file_path, add_file_name=False, technial_replicates=False):
    if technial_replicates:
        return mzXML2Scans_technical_replacates(file_path)

    log.info("mzXML file: %s", file_path)

    MSrawscans = []
    with mzxml.read(file_path) as reader:
        for spectrum in reader:
            # (zmass, abunds, resols, baseline , noise, charge) = peakData
            scanNum = spectrum["num"]
            count = len(spectrum["m/z array"])
            peak_datas = (
                spectrum["m/z array"],
                spectrum["intensity array"],
                [None] * count,
                [None] * count,
                [None] * count,
                [None] * count,
            )
            filterLine = spectrum["filterLine"]
            retTime = spectrum["retentionTime"]
            if add_file_name:
                row = (scanNum, filterLine, peak_datas, retTime, file_path)
            else:
                row = (scanNum, filterLine, peak_datas, retTime)
            MSrawscans.append(row)

    log.info("Scan Count is %d", len(MSrawscans))
    return MSrawscans


def mzXML2Scans_technical_replacates(file_path):
    log.info("techical replicates mzXML files at: %s", file_path)
    files = glob.glob(file_path + "/*.mzxml")
    log.info("processing {} files".format(len(files)))

    MSrawscans_fromReplicates = []
    for file in files:
        MSrawscans = mzXML2Scans(file, add_file_name=True)
        MSrawscans_fromReplicates.extend(MSrawscans)

    return MSrawscans_fromReplicates


def mzML2Scans(file_path):
    log.info("mzML file: %s", file_path)
    MSrawscans = []
    with mzml.read(file_path) as reader:
        for spectrum in reader:
            # (zmass, abunds, resols, baseline , noise, charge) = peakData
            id = spectrum["id"]
            m = re.match(r".* scan=(\d)", id)
            scanNum = int(m.groups()[0])

            if len(spectrum["scanList"]["scan"]) > 1:
                log.error(
                    "scanList for single scan is more than 1 for: {}".format(
                        id
                    )
                )

            count = len(spectrum["m/z array"])
            peak_datas = (
                spectrum["m/z array"],
                spectrum["intensity array"],
                [None] * count,
                [None] * count,
                [None] * count,
                [None] * count,
            )
            filterLine = spectrum["scanList"]["scan"][0]["filter string"]
            retTime = spectrum["scanList"]["scan"][0]["scan start time"] * 60
            row = (scanNum, filterLine, peak_datas, retTime, file_path)
            MSrawscans.append(row)

    log.info("Scan Count is %d", len(MSrawscans))
    return MSrawscans


def ThermoRawfile2Scans_csv(scans, filename="ThermoRawfile2Scans.csv"):
    with open(filename, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=",")
        writer.writerow(("scanNum", "filterLine", "retTime", "row"))
        for scan in scans:
            (scanNum, filterLine, peak_datas, retTime, file_name) = scan
            for row in zip(*peak_datas):
                line = (scanNum, filterLine, retTime, file_name) + row
                writer.writerow(line)


"""
Filter on scans
"""


def filterScanBy_first(scans, n=1):
    log.info("filterScanBy_first %d scans", n)

    return scans[n:]


def roundCollisionEnergy(scans, decimal_places=6):
    log.info(
        "roundCollisionEnergy in header to merge scans to %d decimal places",
        decimal_places,
    )
    result = []
    for row in scans:
        scanNum, filterLine, peak_datas, retTime, file_name = row
        if " ms2 " in filterLine:
            m = re.match(r"(.*) (\d+\.\d*)@(.*)", filterLine)
            colisionEnergy = float(m.groups()[1])
            new_colisionEnergy = round(colisionEnergy, decimal_places)
            new_filterLine = (
                m.groups()[0]
                + " "
                + str(new_colisionEnergy)
                + "@"
                + m.groups()[2]
            )
            row = scanNum, new_filterLine, peak_datas, retTime, file_name
        result.append(row)

    return result


def filterScanBy_retentionTime(
    scans, lowSeconds=0.5, highSeconds=float("inf")
):
    log.info("filterScanBy_retentionTime %f to %f", lowSeconds, highSeconds)
    result = []
    for row in scans:
        scanNum, filterLine, peak_datas, retTime, file_name = row
        if retTime >= lowSeconds and retTime <= highSeconds:
            result.append(row)
    return result


def filterScanBy_filterline(scans, subtext=" ms ", keep=False):
    log.info("filterScanBy_filterline %s filter keep: %s", subtext, keep)
    result = []
    for row in scans:
        scanNum, filterLine, peak_datas, retTime, file_name = row
        if keep:
            if subtext in filterLine:
                result.append(row)
        else:  # not keep
            if subtext not in filterLine:
                result.append(row)
    return result


def filterScanBy_samples(scans, step_size=10):
    log.info("filterScanBy_samples step_size %d", step_size)
    result = []
    for idx, row in enumerate(scans):
        if idx % step_size == 0:
            result.append(row)
    return result


"""
merge peaks and coarse grained filtering
"""


def mergePeaksOnFilterline(scans):
    log.info("Merging %d scans", len(scans))

    filterLines = set(
        [
            filterLine
            for scanNo, filterLine, peakData, retTime, file_name in scans
        ]
    )
    log.info("found %d uniqe filterlines", len(filterLines))

    # create dict
    mergedPeaks = {}
    for filterLine in filterLines:
        mergedPeaks[filterLine] = ([], [], [], [], [], [], [])

    #     populate dict
    for scanNo, filterLine, peakData, retTime, file_name in scans:
        (zmass, abunds, resols, baseline, noise, charge) = peakData
        mergedPeaks[filterLine][0].extend(zmass)
        mergedPeaks[filterLine][1].extend(abunds)
        mergedPeaks[filterLine][2].extend(resols)
        mergedPeaks[filterLine][3].extend(baseline)
        mergedPeaks[filterLine][4].extend(noise)
        mergedPeaks[filterLine][5].extend(charge)
        mergedPeaks[filterLine][6].extend([file_name] * len(zmass))

    return mergedPeaks


def filterlinePeaks_csv(mergedPeaks, filename="filterlinePeaks.csv"):
    with open(filename, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=",")
        writer.writerow(("Scan", "Row data"))
        for scan in mergedPeaks:
            peak_data = mergedPeaks[scan]
            for row in zip(*peak_data):
                line = (scan,) + row
                writer.writerow(line)


def preliminaryFilter(
    peakData, decimal_places=2, minCount=2, minRepetitionRate=0.0
):
    log.debug(
        "preliminaryFilter rounding to decimal_places %d, minCount = %d, minRepetitionRate %f",
        decimal_places,
        minCount,
        minRepetitionRate,
    )
    masses = peakData[0]
    log.debug("initial peak count %d", len(masses))

    halfdec = (10**-decimal_places) / 2

    # bins plus round up and round down to catch the edge cases of close to top or close to bottom of bin
    # eg  123.104 round = 123.10 up=123.11 down= 123.10
    #     123.106 round = 123.11 up=123.11 down= 123.10
    #     by counting the bins from round up and down we get a bin count
    #     123.10 : 3 and 123.11 : 3
    # for peaks with no adjacent bins the peak count is 2

    rounddown = [round(mass - halfdec, decimal_places) for mass in masses]
    roundeds = [round(mass, decimal_places) for mass in masses]
    roundup = [round(mass + halfdec, decimal_places) for mass in masses]

    bins = dict()
    for rounded in roundeds:
        bins[rounded] = bins.get(rounded, 0) + 1

    for rounded in roundup:
        bins[rounded] = bins.get(rounded, 0) + 1

    for rounded in rounddown:
        bins[rounded] = bins.get(rounded, 0) + 1

    log.debug("Prelimianry groups count %d", len(bins))
    minCount_bin = {
        bin: (count / 3) + 1
        for bin, count in list(bins.items())
        if (count / 3) + 1 >= minCount
    }
    log.debug("groups with minCount %d: %d", minCount, len(minCount_bin))
    minCount_bin_max = (
        float(max(minCount_bin.values())) if len(minCount_bin) != 0 else 0
    )
    minRepetitionRate_bin = {
        bin: count
        for bin, count in list(minCount_bin.items())
        if (count / minCount_bin_max) > minRepetitionRate
    }
    log.debug(
        "groups with minRepetitionRate %f: %d",
        minRepetitionRate,
        len(minRepetitionRate_bin),
    )

    preFilterPass = [
        rounded in list(minRepetitionRate_bin.keys()) for rounded in roundeds
    ]
    compressedPeakData = list(
        itertools.compress(list(zip(*peakData)), preFilterPass)
    )
    compressedPeakData = list(zip(*compressedPeakData))
    log.debug("final peak count %d", preFilterPass.count(True))
    return compressedPeakData


def preliminaryReductionFilter(peakData, reduction=0.10, minPeaks=10):
    peak_count = len(peakData[0])
    goal = int(peak_count * reduction)
    log.debug(
        "preliminaryReductionFilter will reduce peak count to max %d and min %d",
        goal,
        minPeaks,
    )

    decimal_places = 2
    minCount = 2
    minRepetitionRate = 0.5
    toggle = False
    while peak_count > goal:
        if toggle:
            decimal_places += 1
        else:
            minRepetitionRate += 0.1
        peakData = preliminaryFilter(
            peakData, decimal_places, minCount, minRepetitionRate
        )
        peak_count = len(peakData[0])

    return peakData


"""
generate bins
"""


def generateBins_decimalPlaces(peakData, decimal_places=4):
    log.debug("generateBins_decimalPlaces, decimal_places %d", decimal_places)
    masses = peakData[0]
    abunds = peakData[1]
    resols = peakData[2]
    log.debug("generateBins_decimalPlaces, peak count %d", len(masses))

    halfWidth = (10**-decimal_places) / 2
    bins_low = [round(mass - halfWidth, decimal_places) for mass in masses]
    bins_high = [round(mass + halfWidth, decimal_places) for mass in masses]

    peakData += (bins_low, bins_high)
    return peakData


def generateBins_resolution(peakData, decimal_places=4):
    log.debug("generateBins_resolution, decimal_places %d", decimal_places)
    masses = peakData[0]
    abunds = peakData[1]
    resols = peakData[2]
    log.debug("generateBins_resolution, peak count %d", len(masses))

    bins_high = [
        mass + ((mass / resol) / 2) for mass, resol in zip(masses, resols)
    ]
    bins_low = [
        mass - ((mass / resol) / 2) for mass, resol in zip(masses, resols)
    ]
    # rounding to make bins larger
    halfWidth = (10**-decimal_places) / 2
    bins_low = [round(mass - halfWidth, decimal_places) for mass in bins_low]
    bins_high = [round(mass + halfWidth, decimal_places) for mass in bins_high]

    peakData += (bins_low, bins_high)
    return peakData


def peakWidth_at_hight(abunds, highth=0.95):
    """Note:
    for future implementation
    assuming that the peak has a gausian curve,
    and that the resols is full width at half maximum, fwhm
    and given the equation in wikipedia for fwhm

    the formula for the full width at an abritary height between [0,1]

    is width = 2 * sqrt(abund**2 * log(hight) / (-4*log(2)))

    """

    def widthAtHight(fwhm, normHight):
        return 2 * math.sqrt(
            fwhm**2 * math.log(normHight) / (-4 * math.log(2))
        )

    return [widthAtHight(abund, highth) for abund in abunds]


def generateBins_theoreticalResolution(peakData, decimal_places=4):
    log.debug(
        "generateBins_theoreticalResolution, decimal_places %d", decimal_places
    )
    masses = peakData[0]
    abunds = peakData[1]
    resols = peakData[2]
    log.debug("generateBins_theoreticalResolution, peak count %d", len(masses))

    log.info("curve fitting to generate theoreticalResolution")
    from scipy.optimize import curve_fit

    def func(x, a, b):
        return a * (x**-b)

    sort_mass = sorted(zip(abunds, masses, resols))  # filter on intensity
    # 5408000.0, 2096000.0
    select_abunds, select_masses, select_resols = list(zip(*sort_mass))
    log.debug("Selecting only 90% highest intensity, as per Kai S.")
    side_len = len(select_masses) / 10
    popt, pconv = curve_fit(
        func, select_masses[side_len:], select_resols[side_len:]
    )

    log.info("function a*(x**-b) uses values: mass, %f, %f ", popt[0], popt[1])

    theoResols = [func(mass, *popt) for mass in masses]

    bins_high = [
        mass + ((mass / resol) / 2) for mass, resol in zip(masses, theoResols)
    ]
    bins_low = [
        mass - ((mass / resol) / 2) for mass, resol in zip(masses, theoResols)
    ]
    # rounding to make bins larger
    halfWidth = (10**-decimal_places) / 2
    bins_low = [round(mass - halfWidth, decimal_places) for mass in bins_low]
    bins_high = [round(mass + halfWidth, decimal_places) for mass in bins_high]

    peakData += (bins_low, bins_high)
    return peakData


def generateBins_resolutionPowerFunc(
    peakData, a=1.0, minus_b=1.0, decimal_places=4
):
    log.debug(
        "generateBins_resolutionPowerFunc, mass +- res_func, res_func = a*(mass**-b), a= %f, b = %f",
        a,
        minus_b,
    )
    masses = peakData[0]
    log.debug("generateBins_resolutionPowerFunc, peak count %d", len(masses))

    def func(x, a, b):
        return a * (x**-b)

    popt = (a, minus_b)

    log.info("function a*(x**-b) uses values: mass, %f, %f ", popt[0], popt[1])

    theoResols = [func(mass, *popt) for mass in masses]

    bins_high = [
        mass + ((mass / resol) / 2) for mass, resol in zip(masses, theoResols)
    ]
    bins_low = [
        mass - ((mass / resol) / 2) for mass, resol in zip(masses, theoResols)
    ]
    # rounding to make bins larger
    halfWidth = (10**-decimal_places) / 2
    bins_low = [round(mass - halfWidth, decimal_places) for mass in bins_low]
    bins_high = [round(mass + halfWidth, decimal_places) for mass in bins_high]

    peakData += (bins_low, bins_high)
    return peakData


def generateBins_theoreticalIntensity(peakData, decimal_places=4):
    log.debug(
        "generateBins_theoreticalIntensity, decimal_places %d", decimal_places
    )
    masses = peakData[0]
    abunds = peakData[1]
    resols = peakData[2]
    log.debug("generateBins_theoreticalResolution, peak count %d", len(masses))

    log.info("curve fitting to generate theoreticalResolution")
    from scipy.optimize import curve_fit

    def func(x, a, b):
        return a * (x**-b)

    sort_mass = sorted(zip(masses, abunds))

    select_masses, select_resols = list(zip(*sort_mass))
    log.debug("Selecting only middle of distribution, as per Kai S.")
    side_len = len(select_masses) / 15
    popt, pconv = curve_fit(
        func,
        select_masses[side_len:-side_len],
        select_resols[side_len:-side_len],
    )

    log.info("function a*(x**-b) uses values: mass, %f, %f ", popt[0], popt[1])

    theoResols = [func(mass, *popt) for mass in masses]

    bins_high = [
        mass + ((mass / resol) / 2) for mass, resol in zip(masses, theoResols)
    ]
    bins_low = [
        mass - ((mass / resol) / 2) for mass, resol in zip(masses, theoResols)
    ]
    # rounding to make bins larger
    halfWidth = (10**-decimal_places) / 2
    bins_low = [round(mass - halfWidth, decimal_places) for mass in bins_low]
    bins_high = [round(mass + halfWidth, decimal_places) for mass in bins_high]

    peakData += (bins_low, bins_high)
    return peakData


def alterBins_mergeOverlap(peakData):
    log.debug("alterBins_mergeOverlap")

    sortedPeakData = list(zip(*sorted(zip(*peakData))))
    masses = list(sortedPeakData[0])
    abunds = list(sortedPeakData[1])
    resols = list(sortedPeakData[2])
    bins_low = list(sortedPeakData[-2])
    bins_high = list(sortedPeakData[-1])

    while True:  # bubble check
        changeCount = 0
        for idx, _ in enumerate(bins_high):
            if idx >= len(bins_high) - 1:
                continue
            low = bins_low[idx]
            high = bins_high[idx]
            nextLow = bins_low[idx + 1]
            nexthigh = bins_high[idx + 1]

            if low == nextLow and high == nexthigh:
                continue  # already updated

            if high > nextLow:
                newHigh = max(nexthigh, high)
                newLow = min(nextLow, low)

                bins_high[idx] = newHigh
                bins_high[idx + 1] = newHigh
                bins_low[idx] = newLow
                bins_low[idx + 1] = newLow

                changeCount += 1
        log.debug("merged %d pairs of bins", changeCount)
        if changeCount == 0:
            break

    peakData = tuple(sortedPeakData[:-2]) + (bins_low, bins_high)
    return peakData


"""
sort each mass in a bin
"""


def sortMassIn_FirstBin(peakData):
    log.debug(
        "sortMassIn_FirstBin, no sorting , just the first bins that matches"
    )
    masses = peakData[0]
    abunds = peakData[1]
    resols = peakData[2]
    bins_low = peakData[-2]
    bins_high = peakData[-1]

    uniqBins = set(zip(bins_low, bins_high))
    log.debug("Mass count %d, available bins %d", len(masses), len(uniqBins))
    if len(masses) * len(uniqBins) > 1000000:
        log.debug(
            "this operation may take a long time, use sortMassIn_sortWindow instead"
        )
        return sortMassIn_sortWindow(peakData, int(len(uniqBins) / 100))
    bins = []
    for mass in masses:
        inbin = False
        for bin_low, bin_high in uniqBins:
            if mass >= bin_low and mass <= bin_high:
                bins.append((bin_low, bin_high))
                inbin = True
                break
        if not inbin:
            print("error")

    if len(bins) != len(masses):
        log.error(
            "There was a problem setting masses in bins, please verify bins where created correctly"
        )
        raise RuntimeError(
            "There was a problem setting masses in bins, please verify bins where created correctly"
        )

    peakData += (bins,)
    return peakData


def sortPeaksByBinWidth(peakData):
    bin_width = [
        bin_high - bin_low
        for bin_low, bin_high in zip(peakData[-2], peakData[-1])
    ]
    sorted_peakdata_plus = list(zip(*sorted(zip(bin_width, *peakData))))
    sorted_peakdata = sorted_peakdata_plus[1:]
    return sorted_peakdata


def sortMassIn_NarrowestBin(peakData):
    log.debug("sortMassIn_NarrowestBin")
    masses = peakData[0]
    abunds = peakData[1]
    resols = peakData[2]
    bins_low = peakData[-2]
    bins_high = peakData[-1]

    uniqBins = set(zip(bins_low, bins_high))
    log.debug("Mass count %d, available bins %d", len(masses), len(uniqBins))
    if len(masses) * len(uniqBins) > 1000000:
        log.debug(
            "this operation may take a long time, use sortMassIn_sortNarrowWindow instead"
        )
        return sortMassIn_sortNarrowWindow(peakData, len(uniqBins) / 100)

    sorted_peakdata = sortPeaksByBinWidth(peakData)

    masses = sorted_peakdata[0]
    abunds = sorted_peakdata[1]
    resols = sorted_peakdata[2]
    bins_low = sorted_peakdata[-2]
    bins_high = sorted_peakdata[-1]

    bins = []
    for mass in masses:
        for bin_low, bin_high in uniqBins:
            if mass >= bin_low and mass <= bin_high:
                bins.append((bin_low, bin_high))
                break

    if len(bins) != len(masses):
        log.error(
            "There was a problem setting masses in bins, please verify bins where created correctly"
        )

    peakData += (bins,)
    return peakData


def sortMassIn_sortWindow(peakData, window=200):
    if window > 200:
        window = 200
    log.debug("sortMassIn_sortWindow, window size %d", window)

    peakData_sorted = list(zip(*sorted(zip(*peakData))))

    masses = peakData_sorted[0]
    abunds = peakData_sorted[1]
    resols = peakData_sorted[2]
    bins_low = peakData_sorted[-2]
    bins_high = peakData_sorted[-1]

    tryAgain = True

    while tryAgain:
        tryAgain = False
        bins = []
        for idx, mass in enumerate(masses):
            found = False
            lowidx = 0 if idx < (window / 2) else idx - (window / 2)
            lowidx = int(lowidx)
            highidx = window + lowidx
            if idx % window == 0:
                log.debug("at %d of %d", idx, len(masses))
            for bin_low, bin_high in zip(
                bins_low[lowidx:highidx], bins_high[lowidx:highidx]
            ):
                if mass >= bin_low and mass <= bin_high:
                    found = True
                    bins.append((bin_low, bin_high))
                    break
            if not found:
                log.error(
                    "the mass at index %d did not find a bin, window size %d",
                    idx,
                    window,
                )
                window = window * 2
                log.error("change window size to %d", window)
                tryAgain = True
                break

    if len(bins) != len(masses):
        log.error(
            "There was a problem setting masses in bins, please verify bins where created correctly, and window size"
        )

    peakData += (bins,)
    return peakData


def sortMassIn_sortNarrowWindow(peakData, window=200):
    log.debug("sortMassIn_sortNarrowWindow, window size %d", window)

    peakData_sorted = list(zip(*sorted(zip(*peakData))))

    masses = peakData_sorted[0]
    abunds = peakData_sorted[1]
    resols = peakData_sorted[2]
    bins_low = peakData_sorted[-2]
    bins_high = peakData_sorted[-1]

    bins = []
    for idx, mass in enumerate(masses):
        found = False
        lowidx = 0 if idx < (window / 2) else idx - (window / 2)
        highidx = window + lowidx

        # --
        bin_width = [
            bin_high - bin_low
            for bin_low, bin_high in zip(
                peakData_sorted[-2][lowidx:highidx],
                peakData_sorted[-1][lowidx:highidx],
            )
        ]
        sorted_peakdata_plus = list(
            zip(
                *sorted(
                    zip(
                        bin_width,
                        peakData_sorted[0][lowidx:highidx],
                        peakData_sorted[1][lowidx:highidx],
                        peakData_sorted[2][lowidx:highidx],
                        peakData_sorted[3][lowidx:highidx],
                        peakData_sorted[4][lowidx:highidx],
                        peakData_sorted[5][lowidx:highidx],
                        peakData_sorted[6][lowidx:highidx],
                        peakData_sorted[7][lowidx:highidx],
                        peakData_sorted[8][lowidx:highidx],
                    )
                )
            )
        )
        sorted_peakdata = sorted_peakdata_plus[1:]
        # --

        if idx % window == 0:
            log.debug("at %d of %d", idx, len(masses))
        for bin_low, bin_high in zip(sorted_peakdata[-2], sorted_peakdata[-1]):
            if mass >= bin_low and mass <= bin_high:
                found = True
                bins.append((bin_low, bin_high))
                break
        if not found:
            log.error("the mass at index %d did not find a bin", idx)

    if len(bins) != len(masses):
        log.error(
            "There was a problem setting masses in bins, please verify bins where created correctly"
        )

    peakData = peakData_sorted + (bins,)
    return peakData


"""
aggregate bins
"""


def aggregateBinData(peakData, max_count=None):
    log.debug(
        "aggregateBinData count %d, count, sumZmass, sumAbund, sum_Sig2Noise",
        len(peakData),
    )
    masses = peakData[0]
    abunds = peakData[1]
    resols = peakData[2]
    bins_low = peakData[-3]
    bins_high = peakData[-2]
    bins = peakData[-1]
    binsData = dict()

    newRow = 0, 0.0, 0.0, 0.0  #  count, sumZmass, sumAbund, sumNoise
    for (
        mass,
        abund,
        resol,
        baseline,
        noise,
        charge,
        file_name,
        bin_low,
        bin_high,
        bin,
    ) in zip(*peakData):
        count, sumZmass, sumAbund, sum_Sig2Noise = binsData.get(bin, newRow)
        count += 1
        sumZmass += mass
        sumAbund += abund
        if noise is not None:
            sig2noise = abund / noise
        else:
            sig2noise = 0
        sum_Sig2Noise += sig2noise
        if max_count and count > max_count:
            log.info(f"set upper bount to count {max_count}")
            count = max_count

        binsData[bin] = count, sumZmass, sumAbund, sum_Sig2Noise

    log.debug("bin count %d ", len(binsData))
    return binsData


def filterlineBins_csv(filterlineBins, filename="filterlineBins.csv"):
    with open(filename, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=",")
        writer.writerow(("filterline", "binLow", "binH", "row data"))
        for filterline in filterlineBins:
            binsdata = filterlineBins[filterline]
            for bin in binsdata:
                row = binsdata[bin]
                line = (filterline,) + bin + row
                writer.writerow(line)


def getMaxCount(binData, disregardBottom=0.10):
    maxCount = 0
    maxAbunds = 0
    for bin in binData:
        count, sumZmass, sumAbund, sumNoise = binData[bin]
        if maxAbunds < (sumAbund / count):
            maxAbunds = sumAbund / count

    abundsCutoff = maxAbunds * disregardBottom
    log.debug(
        "bins with average intensity lower than %f are not evaluated to establish min repetition rate",
        abundsCutoff,
    )
    for bin in binData:
        count, sumZmass, sumAbund, sumNoise = binData[bin]
        if (sumAbund / count) < abundsCutoff:
            continue  # dont consider the
        if maxCount < count:
            maxCount = count

    log.debug(
        "Max peak count is %d, for bins with average abundance above %f ",
        maxCount,
        abundsCutoff,
    )
    return maxCount


def filterBins(
    binData,
    minRepetitionRate=0.70,
    minSignal2Noise=1.0,
    decimal_places=4,
    disregardBottom=0.10,
):
    decimal = 10**-decimal_places
    log.debug(
        "filterBins count %d ,minRepetitionRate %f, decimal places %d, %f, desrigarding bottom %f percent",
        len(binData),
        minRepetitionRate,
        decimal_places,
        decimal,
        disregardBottom,
    )
    if disregardBottom >= 1:
        raise RuntimeError("disregardBottom can not be more than 1")
    maxCount = getMaxCount(binData, disregardBottom)

    bintable = [(k + binData[k]) for k in binData]
    sortedBintable = sorted(bintable)
    # TODO this code is fishy , refactor
    binData_filtered = {}
    #     for bin in binData:
    for idx, row in enumerate(sortedBintable):
        bin = row[0:2]
        (count, sumZmass, sumAbund, sum_sig2Noise) = row[2:]
        minSignal2Noise = (
            0 if sum_sig2Noise == 0 else minSignal2Noise
        )  # in casse there is no signal to noise
        if (
            count >= (maxCount * minRepetitionRate)
            and (sum_sig2Noise / count) >= minSignal2Noise
        ):
            binData_filtered[bin] = (count, sumZmass, sumAbund, sum_sig2Noise)

        if idx + 1 >= len(sortedBintable):
            continue

        nextrow = sortedBintable[idx + 1]
        # test edge cases
        if (
            abs(nextrow[0] - row[1]) < decimal
        ):  # row highbin is adjecent nextrow lowbin
            count2 = row[2] + nextrow[2]
            sum_sig2Noise2 = row[5] + nextrow[5]
            if (
                count2 >= (maxCount * minRepetitionRate)
                and (sum_sig2Noise2 / count2) >= minSignal2Noise
            ):
                binData_filtered[bin] = (
                    count,
                    sumZmass,
                    sumAbund,
                    sum_sig2Noise,
                )
                binData_filtered[nextrow[0:2]] = nextrow[2:]

    log.debug("Filter rate %f", len(binData_filtered) / len(binData))

    return binData_filtered


def formatPeaks(binData):
    log.debug("formatPeaks into simple list pair, mass and intentisty")
    masses = []
    intens = []
    for bin in binData:
        (count, sumZmass, sumAbund, sumNoise) = binData[bin]
        masses.append(sumZmass / count)
        intens.append(sumAbund / count)

    return (masses, intens)


def bins2Peaks(binsData, peakData):
    log.debug(
        "bins2Peaks get all the peaks with given bin, into simple list pair, mass and intentisty"
    )
    bins_filtered = list(binsData.keys())
    masses = peakData[0]
    abunds = peakData[1]
    resols = peakData[2]
    bins_low = peakData[-3]
    bins_high = peakData[-2]
    bins = peakData[-1]

    filteredRowdata = [
        (row[0], row[1], row[6])
        for row in zip(*peakData)
        if row[9] in bins_filtered
    ]
    result = list(zip(*filteredRowdata))
    return result


def reorder4lipidxplorer(filtered_bins):
    log.debug("reorder4lipidxplorer so it goes ms+, msms+,ms-, msms-")
    filtered_bins1 = collections.OrderedDict(
        sorted(list(filtered_bins.items()), key=lambda t: t[0])
    )
    return filtered_bins1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", help="folder with technical replicates")
    parser.add_argument(
        "--rcf_a",
        help="select the resolution curve finction value a",
        type=float,
        default=5408000.0,
    )
    parser.add_argument(
        "--rcf_b",
        help="select the resolution curve finction value b",
        type=float,
        default=0.5,
    )

    args = parser.parse_args()

    main(
        args.folder,
        technial_replicates=True,
        rcf_a=args.rcf_a,
        rcf_b=args.rcf_b,
    )
