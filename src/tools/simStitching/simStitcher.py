"""
Created on 24.05.2017

@author: mirandaa
"""
import sys, os
import logging
import re
from base64 import b64decode
from array import array
from collections import namedtuple
from math import sqrt
import warnings

log = logging.getLogger(os.path.basename(__file__))
from tools.peakStrainer.utils.peakStrainer_util import (
    getMZXMLEncondedScans,
    decode_mzXML_Peaks,
    write2templateMzXML,
    encodePeaks,
)
from itertools import compress
import numpy as np
import xml.etree.ElementTree as ET
import copy


class Scan(object):
    class FilterLine(object):
        MODE_POS = " + "
        MODE_NEG = " - "

        def __init__(self, filterline):
            self.filterline = filterline
            self.match = re.match(r"(.*)\[(\d+\.\d*)-(\d+\.\d*)\]", filterline)
            if not self.match:
                raise ValueError("Can not process: {filterline}")

        def __str__(self):
            return self.filterline

        def __repr__(self):
            return self.filterline

        def _head(self):
            return self.match.group(1)

        def _low(self):
            return float(self.match.group(2))

        def _high(self):
            return float(self.match.group(3))

        def _center(self):
            return (
                float(self.match.group(2)) + float(self.match.group(3))
            ) / 2

        def asTuple(self):
            return (self._head(), self._low(), self._high())

        def mode(self):
            if self.MODE_POS in self._head():
                return self.MODE_POS
            elif self.MODE_NEG in self._head():
                return self.MODE_NEG
            else:
                return None

    def __init__(self, scanNo, filterLine, encodedPeaks, retTime=None):
        self.scanNo = scanNo
        self.filterLine = self.FilterLine(filterLine)
        self.encodedPeaks = encodedPeaks
        self.retTime = retTime
        self.masses, self.intens = decode_mzXML_Peaks(self.encodedPeaks)
        self.previous = None
        self.next = None
        self.centreCorrectionFactor = (
            None  # correction factor for the center peak
        )

    def __str__(self):
        return "Scan Num {}, {}, peak Count = {}, low ={}, high = {}".format(
            self.scanNo,
            self.filterLine,
            len(self.masses),
            self.overlapLow(),
            self.overlapHigh(),
        )

    def __repr__(self):
        return "{}; {}; {}; {};".format(
            self.scanNo, self.filterLine, self.retTime, self.encodedPeaks
        )

    def decode_mzXML_Peaks(self, encodedPeaks):
        decoded = b64decode(encodedPeaks)
        peaks = array("f", decoded)

        if sys.byteorder != "big":
            peaks.byteswap()

        masses = peaks[::2]
        intens = peaks[1::2]
        return masses, intens

    def allPeaks(self):
        return self.decode_mzXML_Peaks(self.encodedPeaks)

    def nonOverlapPeaks(self):
        return self.nonOverlap_andNoEdgePeaks(daltons=0)

    def cutEdgePeaks(self, daltons=5):
        masses, intens = self.allPeaks()
        isEdge = [
            mass >= self.filterLine._low() + daltons
            and mass < self.filterLine._high() - daltons
            for mass in masses
        ]

        return list(compress(masses, isEdge)), list(compress(intens, isEdge))

    def nonOverlap_andNoEdgePeaks(self, daltons=5):
        """
        remove edge of sim if still available after overlap

        :param daltons: how many daltons to remove from the edge of the SIM
        """
        masses, intens = self.allPeaks()
        isNonOverlap = [
            mass >= self.overlapLow() + daltons
            and mass < self.overlapHigh() - daltons
            for mass in masses
        ]

        return list(compress(masses, isNonOverlap)), list(
            compress(intens, isNonOverlap)
        )

    def _getHighOverlap(
        self,
    ):  # 3 cases either last one, or there is an overlap or there isn't
        if (
            self.next is None
            or self.filterLine._head() != self.next.filterLine._head()
        ):
            return 0

        if self.filterLine._high() > self.next.filterLine._low():
            return (self.filterLine._high() - self.next.filterLine._low()) / 2
        else:
            return 0

    def _getLowOverlap(
        self,
    ):  # 3 cases either first one, or there is an overlap or there isn't
        if (
            self.previous is None
            or self.filterLine._head() != self.previous.filterLine._head()
        ):
            return 0

        if self.previous.filterLine._high() > self.filterLine._low():
            return (
                self.previous.filterLine._high() - self.filterLine._low()
            ) / 2
        else:
            return 0

    def overlapLow(self):
        if (
            self.previous is None
            or self.filterLine._head() != self.previous.filterLine._head()
        ):  # use the difference in high
            return self.filterLine._low() + self._getHighOverlap()
        else:
            return self.filterLine._low() + self._getLowOverlap()

    def overlapHigh(self):
        if (
            self.next is None
            or self.filterLine._head() != self.next.filterLine._head()
        ):  # use the difference in low
            return self.filterLine._high() - self._getLowOverlap()
        else:
            return self.filterLine._high() - self._getHighOverlap()

    def totalIonCount(self):
        mass, intens = self.allPeaks()
        return sum(intens)


def getSampleSimPeak(scans, relintens=0.05, mzGap=0.5):
    def hasGap(mass, masses, mzGap):
        idx = masses.index(mass)
        prev = masses[idx - 1] if idx > 0 else mass - mzGap
        next = masses[idx + 1] if idx < len(masses) - 1 else mass + mzGap

        if mass - prev >= mzGap and next - mass >= mzGap:
            return True
        else:
            log.debug("no gap of {} for mass {}".format(mzGap, mass))
            return False

    SimSample = namedtuple("SimSample", "mass intens filterLine totalIonCount")
    results = []
    for scan in scans:
        target = (scan.filterLine._high() + scan.filterLine._low()) / 2
        masses, intens = scan.nonOverlapPeaks()
        intensLimit = max(intens) * relintens

        hasIntens = [inten >= intensLimit for inten in intens]

        validMasses = list(compress(masses, hasIntens))
        validIntens = list(compress(intens, hasIntens))

        hasMassesGap = [
            hasGap(mass, validMasses, mzGap) for mass in validMasses
        ]

        gapMasses = list(compress(validMasses, hasMassesGap))
        gapIntens = list(compress(validIntens, hasMassesGap))

        sortedMasses = sorted(gapMasses, key=lambda mass: abs(mass - target))

        if not sortedMasses:
            log.error("no sample found for {}".format(scan.filterLine))
        else:
            for mass in sortedMasses:
                idx = gapMasses.index(mass)
                simSample = SimSample(
                    gapMasses[idx],
                    gapIntens[idx],
                    scan.filterLine,
                    scan.totalIonCount(),
                )
                results.append(simSample)

    return results


def getMatchingMS(sampleSimPeaks, scans_ms):
    results = []
    for sample in sampleSimPeaks:
        probalemMSfilterline = sample.filterLine._head().replace(
            "SIM", "Full"
        )  # dirty hack
        scan_ms = [
            scan
            for scan in scans_ms
            if scan.filterLine._head() == probalemMSfilterline
        ]
        if not scan_ms:
            log.error("no MS found for sample : {}".format(sample))
            continue

        masses, intenses = scan_ms[0].allPeaks()
        target = sample.mass

        sortedMasses = sorted(masses, key=lambda mass: abs(mass - target))
        if abs(sortedMasses[0] - target) < 0.01:
            idx = masses.index(sortedMasses[0])
            results.append(
                sample + (masses[idx], intenses[idx], probalemMSfilterline)
            )
    return results


def toCSVFile(fileBaseName, dictOrList):
    with open(fileBaseName + ".csv", "w") as outfile:
        if type(dictOrList) is list:
            string = "\n".join(map(str, dictOrList))
            string = string.replace("(", "")
            string = string.replace(")", "")

        elif type(dictOrList) is dict:
            string = "\n".join(map(str, list(dictOrList.items())))
            string = string.replace(":", ":\n")
            string = string.replace("(", "\n")
            string = string.replace(")", "\n")
            string = string.replace("[", "\n")
            string = string.replace("[", "\n")

        outfile.write(string)


def func(mass, totIonCount, C):
    X = mass
    Y = totIonCount
    return (
        C[4] * X**2.0
        + C[5] * Y**2.0
        + C[3] * X * Y
        + C[1] * X
        + C[2] * Y
        + C[0]
    )


def fun(C, mass, totIonCount, deviationFactor):
    X = np.array(mass)
    Y = np.array(totIonCount)
    offset = np.array(deviationFactor)
    return (
        C[4] * np.power(X, 2.0)
        + C[5] * np.power(Y, 2.0)
        + C[3] * X * Y
        + C[1] * X
        + C[2] * Y
        + C[0]
    ) - offset


def updateFunc(
    C, centerfactor, startOffset, mass, deviationFactor=0, onlyScale=False
):
    """

    :param C: values for regression training
    :param centerfactor: scaling for mass at center of sim to match ms
    :param startOffset: how far from sim center is the mass
    :param mass: the mass
    :param deviationFactor: scaling for current mass to corresponding ms mass
    :param onlyScale: no function, only scale to centre mass, this is good approximation
    """

    if onlyScale:
        return centerfactor

    cf = np.array(centerfactor)
    so = np.array(startOffset)
    m = np.array(mass)
    df = np.array(deviationFactor)

    return (cf + (C[0] * np.exp(C[1] * so)) * (C[2] * m) + C[3]) - df


def getCenterFactors(simMasses, deviationFactors, simHeads):
    import pandas as pd

    centers = [simHead._center() for simHead in simHeads]
    dfcf = pd.DataFrame(
        {
            "simMasses": simMasses,
            "deviationFactors": deviationFactors,
            "simHeads": simHeads,
            "centers": centers,
        }
    )
    dfcf["distances"] = abs(dfcf.simMasses - dfcf.centers)
    dfcf["mini"] = dfcf.groupby("simHeads")["distances"].transform("min")

    selectDF = dfcf[dfcf.distances == dfcf.mini]
    result = (selectDF.simHeads.tolist(), selectDF.deviationFactors.tolist())
    dictRes = dict(list(zip(*result)))
    return dictRes


def getDeviationTrend(matchingSim, C=None):
    log.info("curve fitting to generate projection")
    log.info("given C:{}".format(C))
    result = {}
    centreFactors = {}
    uniqMSHeads = set([line[6] for line in matchingSim])
    # from scipy.optimize import  curve_fit use for linear regresion
    # import scipy.linalg # used for surface
    import scipy.optimize

    for mode in [Scan.FilterLine.MODE_POS, Scan.FilterLine.MODE_NEG]:
        #         if C is not None:
        #             result[uniqMShead] = C
        #             continue
        matchingSimSelection = [
            line for line in matchingSim if mode in line[6]
        ]
        #         minMSInten = max([line[4] for line in matchingSimSelection]) * 0.01 # only sample peaks with a minimum intensity for function, performs worse!!!!, dont do it
        #         validSimSelection = [line for line in matchingSimSelection if line[4] > minMSInten]
        (
            simMasses,
            simIntens,
            simHeads,
            simTotalIonCount,
            msMasses,
            msIntens,
            msHeads,
        ) = list(zip(*matchingSimSelection))

        #         sumSimIntens = sum(simIntens) # to normalize
        #         simMsIntens = sum(msIntens)
        #         simIntens_norm = [simInten / sumSimIntens for simInten in simIntens]
        #         msIntens_norm = [msInten / simMsIntens for msInten in msIntens]
        deviationFactors = [
            msIntens[idx] / simIntens[idx] for idx, _ in enumerate(msIntens)
        ]
        centerfactorsDict = getCenterFactors(
            simMasses, deviationFactors, simHeads
        )
        centerfactorsList = [
            centerfactorsDict[simHead] for simHead in simHeads
        ]
        startOffsets = [
            simMass - simhead._low()
            for simMass, simhead in zip(simMasses, simHeads)
        ]
        try:
            #    popt, pconv = curve_fit(func, msMasses, deviationFactors)
            # as per https://gist.github.com/amroamroamro/1db8d69b4b65e8bc66a6
            #             data = np.array([simMasses, simTotalIonCount, deviationFactors])
            #             data= data.T
            #
            #             A = np.c_[np.ones(data.shape[0]), data[:,:2], np.prod(data[:,:2], axis=1), data[:,:2]**2] # C[0] + C[1]*X+C[2]*Y + C[3]*X*Y + C[4]*X**2.+C[5]*Y**2.
            # C,_,_,_ = scipy.linalg.lstsq(A, data[:,2]) returns negatives
            # C,_ = scipy.optimize.nnls(A, data[:,2]) #linear

            # from http://scipy-cookbook.readthedocs.io/items/robust_regression.html
            x0 = np.ones(4)
            C = scipy.optimize.least_squares(
                updateFunc,
                x0,
                args=(
                    centerfactorsList,
                    startOffsets,
                    simMasses,
                    deviationFactors,
                ),
            )

            # evaluate it on a grid
            # Z = np.dot(np.c_[np.ones(XX.shape), XX, YY, XX*YY, XX**2, YY**2], C).reshape(X.shape)
            # Z = C[4]*X**2. + C[5]*Y**2. + C[3]*X*Y + C[1]*X + C[2]*Y + C[0]
        except:
            log.error("ERROR: Values do not fit a surface")
            popt = (0, 0, 0, 0, 0, 0)
        log.info(
            "function least_squares uses values: projection, %s for %s",
            str(C.x),
            mode,
        )
        result[mode] = C.x
        centreFactors.update(centerfactorsDict)
    return result, centreFactors


def project_ms2sim(matchingSims, popts, centerFactors, onlyScale=True):
    (
        simMasses,
        simIntens,
        simHeads,
        simTotalIonCounts,
        msMasses,
        msIntens,
        msHeads,
    ) = list(zip(*matchingSims))
    startOffsets = [
        simMass - simhead._low()
        for simMass, simhead in zip(simMasses, simHeads)
    ]
    #     modes = [Scan.FilterLine.MODE_POS if Scan.FilterLine.MODE_POS in msHead \
    #              else Scan.FilterLine.MODE_NEG for msHead in msHeads]
    correctionFactors = [
        updateFunc(
            popts[simHead.mode()],
            centerFactors[simHead],
            startOffset,
            simMass,
            deviationFactor=0,
            onlyScale=onlyScale,
        )
        for simHead, startOffset, simMass in zip(
            simHeads, startOffsets, simMasses
        )
    ]

    simIntens_Corrected = [
        matchingSim[1] * correctionFactors[idx]
        for idx, matchingSim in enumerate(matchingSims)
    ]
    sqError = [
        (matchingSim[1] - simIntens_Corrected[idx]) ** 2
        for idx, matchingSim in enumerate(matchingSims)
    ]
    sumSqError = sum(sqError)

    l2norm = sqrt(sumSqError)

    log.info(
        " l2 norm {} from max {}, count = {}".format(
            l2norm,
            max(
                [
                    msInten
                    for simMass, simInten, simHead, simTotIonCount, msMass, msInten, msHead in matchingSims
                ]
            ),
            len(sqError),
        )
    )

    return [
        matchingSim + (simIntens_Corrected[idx], correctionFactors[idx])
        for idx, matchingSim in enumerate(matchingSims)
    ]


def tr_loglevel(loglevel):
    tr = {
        0: logging.ERROR,
        1: logging.INFO,
        2: logging.DEBUG,
        3: logging.DEBUG,
    }
    return tr[loglevel]


def getCSVPath(csvPath, filePath):
    dir, file = os.path.split(filePath)

    baseName = file[:-6]

    return getCSVPath1(csvPath, filePath) + baseName + "-"


def getCSVPath1(csvPath, filePath):
    dir, file = os.path.split(filePath)
    if csvPath == None:
        csvPath = dir
    if not csvPath.endswith("\\"):
        csvPath = csvPath + "\\"
    csvPath = csvPath + "logfiles\\"
    if not os.path.exists(csvPath):
        os.makedirs(csvPath)

    return csvPath


def getSelectedMatchingSim(matchingSim):
    """
    will return one scan per sim, the one closes to the centre of the sim
    :param matchingSim: all matching peaks between sim scans and ms
    """
    #     simMass, simInten, simHead, simTotalIonCount, msMass,msInten, msHead = zip(*matchingSim)

    sortedMatchingSim = sorted(
        matchingSim, key=lambda e: abs(e[0] - e[2]._center())
    )

    first = set()
    selected = []

    for e in sortedMatchingSim:
        if e[2].filterline in first:
            continue
        first.add(e[2].filterline)
        selected.append(e)

    return selected


def replaceScansinXML(original, destination, remove, include):
    namespaces = {
        "xmlns": "http://sashimi.sourceforge.net/schema_revision/mzXML_3.0"
    }
    ET.register_namespace(
        "", "http://sashimi.sourceforge.net/schema_revision/mzXML_3.0"
    )
    tree = ET.parse(original)

    msRunElement = tree.find(".//xmlns:msRun", namespaces)
    scanElements = msRunElement.findall(".//xmlns:scan", namespaces)

    # remove
    for scan in scanElements:
        scanLine = scan.attrib["filterLine"]
        for r_prefix in remove:
            if r_prefix in scanLine:
                msRunElement.remove(scan)

    # include
    scanTemplete = scanElements[0]
    print(ET.tostring(scanTemplete).decode())

    idx = int(scanElements[-1].attrib["num"])
    for scan in include:
        idx += 1
        (masses, intens) = include[scan][:2]
        newScan = copy.deepcopy(scanTemplete)
        newScan.attrib["filterLine"] = scan
        newScan.attrib["peaksCount"] = str(len(masses))
        newScan.attrib["num"] = str(idx + 1)
        newScan.attrib["msLevel"] = "1" if " ms " in scan else "2"
        newScan.attrib["polarity"] = "-" if " - " in scan else "+"
        newScan.attrib["retentionTime"] = "PT{}S".format(0.0 + idx)

        encodedPeaks = encodePeaks(masses, intens)
        newScan.find(".//xmlns:peaks", namespaces).text = encodedPeaks
        msRunElement.append(newScan)

    tree.write(destination, encoding="ISO-8859-1", xml_declaration=True)


def simStitcher(
    filePath,
    scaleToCenterMass=True,
    adaptByRegresion=False,
    daltons=5,
    csvPath1=None,
    loglevel=3,
    doCompare=True,
    callback=None,
):
    """
    stitch the sim scans together
    :param filePath: thermo raw file to process
    :param scaleToCenterMass: scale SIM to match MS, based on center SIM mass
    :param adaptByRegresion: try to adapt the complete SIM to match MS, overrides scaleToCenterMass, performance is beta
    :param daltons: daltons to remove from sim edge, default:5
    :param csvPath1: csvoutput path
    :param loglevel: from 0 low to 3 high
    """

    log.setLevel(tr_loglevel(loglevel))
    log.addHandler(logging.StreamHandler())  # log to console
    if loglevel > 0:
        csvPath = getCSVPath(csvPath1, filePath)
    if loglevel > 0:
        logging.basicConfig(
            filename=getCSVPath1(csvPath1, filePath) + "simSitcher.log",
            filemode="w",
        )

    log.info("getMZXMLEncondedScans from" + filePath)
    scans_mzxml = getMZXMLEncondedScanRows(filePath)
    log.debug("\n".join(map(str, scans_mzxml)))

    log.info("drop first scan because invalid")
    #     scans_mzxml = scans_mzxml[1:]

    log.info("get Sim scans")
    scans_mzxml_sim = [
        scan for scan in scans_mzxml if " sim " in scan[1].lower()
    ]
    log.info("avoid  msx scans")
    scans_mzxml_sim = [
        scan for scan in scans_mzxml_sim if " msx " not in scan[1].lower()
    ]
    log.debug("\n".join(map(str, scans_mzxml_sim)))
    if loglevel > 2:
        toCSVFile(csvPath + "scans_mzxml_sim", scans_mzxml_sim)

    scans = [Scan(*scan_xml) for scan_xml in scans_mzxml_sim]

    log.info(
        "get sorted filterlines"
    )  # where low is a number instead of a text
    scans.sort(key=lambda scan: scan.filterLine.asTuple())

    log.debug("\n".join(map(str, scans)))
    if loglevel > 2:
        toCSVFile(csvPath + "ordered_scans", scans)

    # link scans together
    scans[0].next = scans[1]  # previous is None
    for idx, scan in enumerate(scans):
        if idx == 0 or idx >= len(scans) - 1:
            continue
        scans[idx].previous = scans[idx - 1]
        scans[idx].next = scans[idx + 1]
    scans[-1].previous = scans[-2]  # next is None

    # -- build stitched scans
    scans_stitched = {}
    for scan in scans:
        head = scan.filterLine._head()
        masses, intens = scan.cutEdgePeaks(daltons)
        totIonCounts = [scan.totalIonCount()] * len(masses)
        heads = [scan.filterLine] * len(masses)
        scans_stitched.setdefault(head, ([], [], [], []))[0].extend(masses)
        scans_stitched.setdefault(head, ([], [], [], []))[1].extend(intens)
        scans_stitched.setdefault(head, ([], [], [], []))[2].extend(
            totIonCounts
        )
        scans_stitched.setdefault(head, ([], [], [], []))[3].extend(heads)

    log.info("stitched scans:")
    log.info("\n".join(list(scans_stitched.keys())))
    log.debug("\n".join(map(str, list(scans_stitched.items()))))
    if loglevel > 2:
        toCSVFile(csvPath + "scans_stitched", scans_stitched)

    log.info("check if stitched scans have gaps and fill if its lock")
    maxGap = scans[0].filterLine._high() - scans[0].filterLine._low()

    lock_stitched_scans = [
        s for s in scans_stitched.keys() if " lock " in s.lower()
    ]
    for key in lock_stitched_scans:
        masses, *_ = scans_stitched[key]
        nonLock_key = key.replace(" lock ", " ")
        nonLock_peaks = []

        for next, mass in zip(masses[1:], masses[:-1]):
            if next - mass > maxGap:
                log.info(
                    "***gap between two sims is larger than sim,  {} between  mz: {} and {} ***".format(
                        key, next, mass
                    )
                )
                if nonLock_key in scans_stitched.keys():
                    log.info(
                        "***gap will be filled with peaks from {}  ***".format(
                            nonLock_key
                        )
                    )
                    these_noLockPeaks = [
                        t
                        for t in zip(*scans_stitched[nonLock_key])
                        if t[0] < next and t[0] > mass
                    ]
                    nonLock_peaks.extend(these_noLockPeaks)
                if callback:
                    callback(
                        "***gap between two sims is larger than sim,  {}  ***".format(
                            key
                        )
                    )
        if nonLock_peaks:
            # add the originals
            lists = zip(*nonLock_peaks)
            for i, l in enumerate(lists):
                scans_stitched[key][i].extend(l)

    names = list(scans_stitched.keys())
    # -- rename
    for stitched_Head in names:
        min_head = min(
            [
                scan.filterLine._low()
                for scan in scans
                if scan.filterLine._head() == stitched_Head
            ]
        )
        max_head = max(
            [
                scan.filterLine._high()
                for scan in scans
                if scan.filterLine._head() == stitched_Head
            ]
        )
        rename = (
            stitched_Head + "[" + str(min_head) + "-" + str(max_head) + "]"
        )
        scans_stitched[rename] = scans_stitched[stitched_Head]
        del scans_stitched[stitched_Head]

    log.info("renamed stitched scans:")
    log.info("\n".join(list(scans_stitched.keys())))

    if not scaleToCenterMass:
        log.info("writing to :" + outputStitchedFile(filePath))
        # ---
        # get scans that where stitched --> names
        # remove from mzxml
        # add stiched to mzXML
        remove = names
        include = scans_stitched
        destination = outputStitchedFile(filePath)
        replaceScansinXML(filePath, destination, remove, include)

        #         write2templateMzXML(outputStitchedFile(filePath), scans_stitched)
        log.info("finish stitching")
        return  # ALL DONE!

    log.info("start scaling")

    scans_mzxml_ms = [
        scan
        for scan in scans_mzxml
        if " ms " in scan[1].lower() and " full " in scan[1].lower()
    ]
    log.debug("\n".join(map(str, scans_mzxml_ms)))
    if loglevel > 2:
        toCSVFile(csvPath + "scans_mzxml_ms", scans_mzxml_ms)

    scans_ms = [Scan(*scan_xml) for scan_xml in scans_mzxml_ms]

    log.info("get Valid sim samples")
    sampleSimPeaks = getSampleSimPeak(scans)
    log.debug("\n".join(map(str, sampleSimPeaks)))
    if loglevel > 2:
        toCSVFile(csvPath + "sampleSimPeaks", sampleSimPeaks)

    log.info("get matching ms peak")
    matchingSim = getMatchingMS(sampleSimPeaks, scans_ms)

    #     tightSelection = getSelectedMatchingSim(matchingSim)

    log.info("get deviation trend")
    popts, centerFactors = getDeviationTrend(matchingSim)
    onlyScale = scaleToCenterMass and not adaptByRegresion
    log.debug(
        "is only scale {}, scaleToCenterMass:{} and adaptByRegresion: {}".format(
            onlyScale, scaleToCenterMass, adaptByRegresion
        )
    )
    projected = project_ms2sim(matchingSim, popts, centerFactors, onlyScale)
    log.debug(
        "simMass     simInten     simHead     simTotalIonCount     msMass     msInten     msHead    correctedIntens    correctionFactor"
    )
    log.debug("\n".join(map(str, projected)))
    if loglevel > 0:
        toCSVFile(
            csvPath + "matchingSim", projected
        )  # simMass     simInten     simHead     simTotalIonCount     msMass     msInten     msHead    correctedIntens    correctionFactor

    log.info("finished comparing")

    log.info("start sim intens update")

    scans_adjusted = {}

    #     popts, centerFactors
    for idx, scan in enumerate(scans_stitched):
        (masses, intens, totIonCount, heads) = scans_stitched[scan]
        startOffsets = [
            mass - head._low() for mass, head in zip(masses, heads)
        ]
        centreFactorsList = []
        for head in heads:
            if head in list(centerFactors.keys()):
                centreFactorsList.append(centerFactors[head])
            else:
                log.info(
                    "No centrefactor found for {} , using 1 instead".format(
                        head
                    )
                )
                centreFactorsList.append(1.0)
        #             correctionFactors = [update(mass, totIonCount, popts[maybeMSfilterline]) for mass,totIonCount  in zip(masses, totIonCount)]
        correctionFactors = [
            updateFunc(
                popts[head.mode()],
                cf,
                startOffset,
                mass,
                deviationFactor=0,
                onlyScale=onlyScale,
            )
            for head, cf, startOffset, mass in zip(
                heads, centreFactorsList, startOffsets, masses
            )
        ]

        intensAdjusted = [
            intens[idx] * correctionFactors[idx]
            for idx, _ in enumerate(intens)
        ]
        scans_adjusted[scan] = (masses, intensAdjusted)

    log.debug("\n".join(map(str, list(scans_adjusted.items()))))
    if loglevel > 2:
        toCSVFile(csvPath + "scans_adjusted", scans_adjusted)

    log.info("writing to :" + outputAdjustedFile(filePath))
    write2templateMzXML(outputAdjustedFile(filePath), scans_adjusted)

    log.info("finish adjustment")


def outputStitchedFile(fileName):
    dir, file = os.path.split(fileName)
    if not os.path.exists(dir + "\\stitched"):
        os.makedirs(dir + "\\stitched")
    newfilename = dir + "\\stitched\\" + file[:-6] + "-s" + file[-6:]
    return newfilename


def outputAdjustedFile(fileName):
    dir, file = os.path.split(fileName)
    if not os.path.exists(dir + "\\adjusted"):
        os.makedirs(dir + "\\adjusted")
    newfilename = dir + "\\adjusted\\" + file[:-6] + "-as" + file[-6:]
    return newfilename


def getMZXMLEncondedScanRows(filePath):
    return list(zip(*getMZXMLEncondedScans(filePath)))


if __name__ == "__main__":
    if len(sys.argv) > 0:
        simStitcher(sys.argv[1])
    else:
        simStitcher()
