"""
Created on 29.03.2017
peakStrainer_util contains functions that are useful but not used
@author: mirandaa
"""
from base64 import b64decode, b64encode
from array import array
import sys
import os
import logging
import random
import xml.etree.ElementTree as ET
import re
import copy
from collections import OrderedDict

log = logging.getLogger(os.path.basename(__file__))
from tools.peakStrainer.lib import MSFileReader


def encodePeaks(masses, intens):
    peak_list = []
    for mass, intens in sorted(zip(masses, intens)):
        peak_list.append(mass)
        peak_list.append(intens)

    peaks = array("f", peak_list)
    if sys.byteorder != "big":
        peaks.byteswap()

    encoded = b64encode(peaks).decode()
    return encoded


def decode_mzXML_Peaks(encodedPeaks):
    """
    Note zmass and intensity are together

    """
    if isinstance(encodedPeaks, tuple):  # assume its mzml
        return decode_mz_ML_Peaks(encodedPeaks[0], encodedPeaks[1])

    decoded = b64decode(encodedPeaks)
    peaks = array("f", decoded)

    if sys.byteorder != "big":
        peaks.byteswap()

    mass = peaks[::2]
    intens = peaks[1::2]
    return mass, intens


def decode_mz_ML_Peaks(mass_encoded, inty_encoded):

    mass_decoded = b64decode(mass_encoded)
    inty_decoded = b64decode(inty_encoded)

    mass_peaks = array("f", mass_decoded)
    inty_peaks = array("f", inty_decoded)

    if sys.byteorder != "big":
        mass_peaks.byteswap()
        inty_peaks.byteswap()

    return mass_peaks, inty_peaks


def ThermoRawfile2Scans_sample(file_path):
    log.info("file: %s", file_path)
    rawfile = MSFileReader.ThermoRawfile(file_path)

    start = rawfile.FirstSpectrumNumber
    end = rawfile.GetLastSpectrumNumber()

    MSrawscans = []
    for scanNum in range(start, end + 1):
        if scanNum % 10 == 0:
            continue  # just take a sample
        rawPeaks = rawfile.GetLabelData(scanNum)[0]
        filterLine = rawfile.GetFilterForScanNum(scanNum)
        if "ms2" not in filterLine:
            continue  # to discard the MS1 this is the largest
        retTime = rawfile.RTFromScanNum(scanNum) * 60
        object = (scanNum, filterLine, rawPeaks, retTime)
        MSrawscans.append(object)

    logging.info("Scan Count is {}".format(len(MSrawscans)))
    return MSrawscans


def mergePeaksOnFilterline_withRandom(scans):
    log.info("Merging %d scans", len(scans))

    filterLines = set(
        [filterLine for scanNo, filterLine, peakData, retTime in scans]
    )
    log.info("found %d uniqe filterlines", len(filterLines))

    # create dict
    mergedPeaks = {}
    for filterLine in filterLines:
        mergedPeaks[filterLine] = ([], [], [])

    #     populate dict
    for scanNo, filterLine, peakData, retTime in scans:
        (zmass, abunds, resols, baseline, noise, charge) = peakData

        logging.warn("Altering content for testing:")
        logging.warn("masses with an odd M/Z will be have random resolution")

        for idx, val in enumerate(zmass):
            massInt = int(val)
            if massInt % 2 == 1:
                zmass[idx] = massInt + random.random()

        mergedPeaks[filterLine][0].extend(zmass)
        mergedPeaks[filterLine][1].extend(abunds)
        mergedPeaks[filterLine][2].extend(resols)

    return mergedPeaks


def setLogger(LOG_FILENAME="log.log"):
    # log to file
    logging.basicConfig(
        format="%(message)s",
        filename=LOG_FILENAME,
        filemode="w",
        level=logging.DEBUG,
    )
    # log to console
    logging.getLogger().addHandler(logging.StreamHandler())


def namespace(element):
    m = re.match("\{.*\}", element.tag)
    return m.group(0) if m else ""


def getMZXMLEncondedScans(filePath):
    #     TODO:handle different namespaces of mzxml
    namespaces = {
        "xmlns": "http://sashimi.sourceforge.net/schema_revision/mzXML_3.0"
    }
    ET.register_namespace(
        "", "http://sashimi.sourceforge.net/schema_revision/mzXML_3.0"
    )
    tree = ET.parse(filePath)

    scanElems = tree.findall(".//xmlns:scan", namespaces)

    rawscans = []
    for scan in scanElems:
        encodedPeaks = scan.find(".//xmlns:peaks", namespaces).text
        scanNo = int(scan.attrib["num"])
        filterLine = scan.attrib["filterLine"]
        retTime = scan.attrib["retentionTime"]
        object = (scanNo, filterLine, encodedPeaks, retTime)
        rawscans.append(object)

    return list(zip(*rawscans))


def getMZ_MLEncondedScans(filePath):
    #     TODO:handle different namespaces of mzxml
    ns = {
        "mzml": "http://psi.hupo.org/ms/mzml",
        "ms": "http://psi.hupo.org/ms/mzml",
    }

    tree = ET.parse(filePath)
    root = tree.getroot()

    spectrums = root.findall(".//mzml:spectrum", namespaces=ns)

    rawscans = []
    for spectrum in spectrums:
        mz_array_elem = spectrum.find(
            './/ms:cvParam[@name="m/z array"]/../ms:binaryDataArray',
            namespaces=ns,
        )
        intensity_array_elem = spectrum.find(
            './/ms:cvParam[@name="intensity array"]/../ms:binaryDataArray',
            namespaces=ns,
        )
        encodedPeaks = (mz_array_elem, intensity_array_elem)
        scanNo = int(spectrum.get("id").split("=")[-1])
        filterLine = spectrum.find(
            './/ms:cvParam[@name="filter string"]', namespaces=ns
        ).get("value")
        retTime = spectrum.find(
            './/ms:cvParam[@name="scan start time"]', namespaces=ns
        ).get("value")
        object = (scanNo, filterLine, encodedPeaks, retTime)
        rawscans.append(object)

    return list(zip(*rawscans))


def write2templateMzXML(newfilename, scanPeaks):
    namespaces = {
        "xmlns": "http://sashimi.sourceforge.net/schema_revision/mzXML_3.0"
    }
    ET.register_namespace(
        "", "http://sashimi.sourceforge.net/schema_revision/mzXML_3.0"
    )
    scriptPath = os.path.dirname(os.path.realpath(__file__))
    tree = ET.parse(scriptPath + "//template.mzXML")

    msRunElement = tree.find(".//xmlns:msRun", namespaces)
    scanTemplete = msRunElement.find(".//xmlns:scan", namespaces)

    for idx, scan in enumerate(scanPeaks):
        (masses, intens) = scanPeaks[scan][:2]
        newScan = copy.deepcopy(scanTemplete)
        newScan.attrib["filterLine"] = scan
        newScan.attrib["peaksCount"] = str(len(masses))
        newScan.attrib["num"] = str(idx + 1)
        newScan.attrib["scanType"] = scan.split()[4]

        msLevel = 1 if " ms " in scan else 2
        if msLevel == 1:
            newScan.remove(newScan.find(".//xmlns:precursorMz", namespaces))
        else:
            precursorMz = newScan.find(".//xmlns:precursorMz", namespaces)
            match = re.match(r".* (.*)@(...)", scan, re.M | re.I)
            precursorMz.attrib["activationMethod"] = match.group(2)
            precursorMz.text = match.group(1)

        newScan.attrib["msLevel"] = str(msLevel)
        newScan.attrib["polarity"] = "-" if " - " in scan else "+"
        newScan.attrib["retentionTime"] = "PT{}S".format(0.0 + idx)

        encodedPeaks = encodePeaks(masses, intens)
        newScan.find(".//xmlns:peaks", namespaces).text = encodedPeaks
        msRunElement.append(newScan)

    msRunElement.remove(scanTemplete)

    tree.write(newfilename, encoding="ISO-8859-1", xml_declaration=True)


def reorderScans(filtered_bins, order=None):
    if order == None:
        return filtered_bins

    newfiltered_bins = OrderedDict()
    for idxOrder, selectionText in enumerate(order):
        for scan in filtered_bins:
            if selectionText in scan:
                newfiltered_bins[scan + ", " + str(idxOrder)] = filtered_bins[
                    scan
                ]

    return newfiltered_bins
