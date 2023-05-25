import os
import re
import math
from lx.mfql.runtimeStatic import TypeTolerance
from lx.mfql.chemsc import SCConstraint
from lx.mfql.chemParser import parseElemSeq
from pyteomics import mzml  # TODO port to python 3 and use pymzML
import numpy as np
from collections import namedtuple


def fromFullOptions(options_og):
    """returns only the optoins that are needed not all of them"""
    options = dict()
    options["dataType"] = options_og["dataType"]
    options["MStolerance"] = options_og["MStolerance"]
    options["MSMStolerance"] = options_og["MSMStolerance"]
    options["importDir"] = options_og["importDir"]
    options["MSminOccupation"] = options_og["MSminOccupation"]
    options["MSMSminOccupation"] = options_og["MSMSminOccupation"]
    options["masterScanImport"] = options_og["masterScanImport"]
    options["spectraFormat"] = options_og["spectraFormat"]
    options["alignmentMethodMS"] = options_og["alignmentMethodMS"]
    options["alignmentMethodMSMS"] = options_og["alignmentMethodMSMS"]
    options["scanAveragingMethod"] = options_og["scanAveragingMethod"]
    options["importMSMS"] = options_og["importMSMS"]
    options["timerange"] = options_og["timerange"]
    options["MSmassrange"] = options_og["MSmassrange"]
    options["MSMSmassrange"] = options_og["MSMSmassrange"]
    options["MSthresholdType"] = options_og["MSthresholdType"]
    options["MSMSthresholdType"] = options_og["MSMSthresholdType"]
    options["pisSpectra"] = options_og["pisSpectra"]
    # after the import
    options["MSresolution"] = options_og["MSresolution"]
    options["MSresolutionDelta"] = options_og["MSresolutionDelta"]
    options["MSthreshold"] = options_og["MSthreshold"]
    options["MSMSthreshold"] = options_og["MSMSthreshold"]
    options["precursorMassShift"] = options_og["precursorMassShift"]
    options["precursorMassShiftOrbi"] = options_og["precursorMassShiftOrbi"]
    options["MScalibration"] = options_og["MScalibration"]
    options["MSMScalibration"] = options_og._data.get(
        "MSMScalibration", None
    )  # this is SHit because there is no get in this custom dict!!!
    options["selectionWindow"] = options_og["selectionWindow"]
    options["MSMSresolution"] = options_og["MSMSresolution"]
    options["MSMSresolutionDelta"] = options_og["MSMSresolutionDelta"]
    options["isotopicCorrectionMS"] = options_og["isotopicCorrectionMS"]
    options["isotopicCorrectionMSMS"] = options_og["isotopicCorrectionMSMS"]
    options["complementMasterScan"] = options_og["complementMasterScan"]
    options["statistics"] = options_og["statistics"]
    options["optionalMStolerance"] = options_og["optionalMStolerance"]
    options["optionalMSMStolerance"] = options_og["optionalMSMStolerance"]
    options["noPermutations"] = options_og["noPermutations"]
    options["intensityCorrection"] = options_og["intensityCorrection"]
    # options['dumpMasterScanFile'] = options_og['dumpMasterScanFile']
    options["noHead"] = options_og["noHead"]
    options["resultFile"] = options_og["resultFile"]
    return options


def setOptions2likelyDefault(options_og):
    """replaces options values with some likely defaults"""
    options = options_og
    options["dataType"] = options_og["spectraFormat"]  # TODO why is this duplicated?
    # options['MStolerance'] = options_og['MStolerance']
    # options['MSMStolerance'] = options_og['MSMStolerance']
    # options['importDir'] = options_og['importDir']
    # options['MSminOccupation'] = options_og['MSminOccupation']
    # options['MSMSminOccupation'] = options_og['MSMSminOccupation']
    options["masterScanImport"] = None  # not used anymore
    # options['spectraFormat'] = options_og['spectraFormat']
    options["alignmentMethodMS"] = "linear"
    options["alignmentMethodMSMS"] = "linear"
    options["scanAveragingMethod"] = "linear"
    options["importMSMS"] = True  # TODO check in mfql
    # options['timerange'] = options_og['timerange']
    # options['MSmassrange'] = options_og['MSmassrange']
    # options['MSMSmassrange'] = options_og['MSMSmassrange']
    # options['MSthresholdType'] = options_og['MSthresholdType'] #TODO replace this with jaco filter?
    # options['MSMSthresholdType'] = options_og['MSMSthresholdType']
    options["pisSpectra"] = False
    # after the import
    # options['MSresolution'] = options_og['MSresolution']
    # options['MSresolutionDelta'] = options_og['MSresolutionDelta']
    # options['MSthreshold'] = options_og['MSthreshold']
    # options['MSMSthreshold'] = options_og['MSMSthreshold']
    options["precursorMassShift"] = 0.0
    options["precursorMassShiftOrbi"] = None
    # options['MScalibration'] = options_og['MScalibration'] #todo find most intense peak and use that
    options["MSMScalibration"] = None
    # options['selectionWindow'] = options_og['selectionWindow']
    # options['MSMSresolution'] = options_og['MSMSresolution']
    # options['MSMSresolutionDelta'] = options_og['MSMSresolutionDelta']
    options["isotopicCorrectionMS"] = True
    options["isotopicCorrectionMSMS"] = True
    options["complementMasterScan"] = False
    options["statistics"] = False
    # options['optionalMStolerance'] = options_og['optionalMStolerance']
    # options['optionalMSMStolerance'] = options_og['optionalMSMStolerance']
    # options['noPermutations'] = options_og['noPermutations']
    options["intensityCorrection"] = False
    # options['dumpMasterScanFile'] = options_og['dumpMasterScanFile']
    options["noHead"] = False
    # options['resultFile'] = options_og['resultFile']
    return options


def inputFileType(input_files_dir):
    """prefer mzXML iov ever mzxml"""
    inputFileType = None
    for f in os.listdir(input_files_dir):
        if f.lower().endswith("mzml"):
            inputFileType = "mzML"
            break
        elif f.lower().endswith("mzxml"):
            inputFileType = "mzXML"
            break
    return inputFileType


def getMfqlFiles(root_mfql_dir):
    matches = {}
    for root, dirnames, filenames in os.walk(root_mfql_dir):
        for filename in filenames:
            if filename.lower().endswith(".mfql"):
                matches[filename] = os.path.join(root, filename)
    return {k: open(v, "r").read() for k, v in matches.iteritems()}


def resultFileName(input_files_dir, replace=True):
    extrension = ".csv"
    suffix = "-out"
    basename = os.path.basename(input_files_dir)
    if not replace:
        raise NotImplementedError
    fileName = basename + suffix + extrension
    return os.path.join(input_files_dir, fileName)


def getTolerance(ppm=5.0):
    """for now default is 5 ppm"""
    res = TypeTolerance("ppm", ppm)  # TODO replace this
    return res


def getMinMaxMFQLMass(root_mfql_dir, forMS2=False):
    "returns the minnimum and maximum mass to be found in the mfqla"
    mfqlFiles = getMfqlFiles(root_mfql_dir)
    defs = (
        set()
    )  # TODO should be on ordered set to avoid duplicates but convention is first is the precursor
    for file in mfqlFiles.values():
        regex = r"\sDEFINE.*?=.*?\'(.*?)\'"
        m = re.findall(regex, file)
        if not forMS2:  # we assume that the first deifinition in an MFQL is for the MS1
            defs.update([m[0]])
        else:
            defs.update(m[1:])

    def getDefMinMax(definition):
        elemSeq = parseElemSeq(definition)
        elemSeq.set_charge(1)  # TODO read the charge from mfql
        if not isinstance(elemSeq, SCConstraint):
            return (
                elemSeq.getWeight(),
                elemSeq.getWeight(),
            )  # its a elemnet sequence ...ie no range
        return elemSeq.getMassRange()

    minMass = float("inf")
    maxMass = 0
    for definition in defs:
        defMin, defMax = getDefMinMax(definition)  # TODO maybe use numpy arange
        defMin = math.floor(defMin)
        defMax = math.ceil(defMax)  # some premature optimization :)

        minMass = defMin if defMin < minMass else minMass
        maxMass = defMax if defMax > maxMass else maxMass

    return minMass - 1, maxMass + 1  # +1 just to be on the safe side


def getResolutionDeltas(input_files_dir):
    first_file = None
    for root, dirnames, filenames in os.walk(input_files_dir):
        for filename in filenames:
            if filename.lower().endswith(".mzml"):
                first_file = os.path.join(root, filename)
                break
        if first_file:
            break

    def getDelta(m):
        top10 = m.max() - ((m.max() - m.min()) / 10)
        topM = m[m > top10]
        topMin = np.min(np.diff(topM))
        bot10 = m.min() + ((m.max() - m.min()) / 10)
        botM = m[m < bot10]
        botMin = np.min(np.diff(botM))
        dist = top10 - bot10
        delta = botMin / topMin * dist

        DD = namedtuple("DD", "delta dist")
        return DD(delta, dist)

    ms1Delta = None
    ms2Delta = None
    ms2Masses = None
    with mzml.read(first_file) as reader:
        for item in reader:
            # idx = item['index'] + 1
            msX = item["ms level"]
            # fs = item['scanList']['scan'][0]['filter string']
            # i = item['intensity array']
            if msX == 1 and ms1Delta is None:
                m = item["m/z array"]
                ms1Delta = getDelta(m)
            elif msX == 2 and ms2Delta is None:
                m = item["m/z array"]
                if ms2Masses is None:  # initialize
                    ms2Masses = m
                    continue
                if (
                    m.min() > ms2Masses.max() or m.max() < ms2Masses.min()
                ):  # it complements
                    ms2Masses = np.concatenate((ms2Masses, m))
                elif (
                    m.max() - m.min() > ms2Masses.max() - ms2Masses.min()
                ):  # its a greater range
                    ms2Masses = m
                if (
                    ms2Masses.max() - ms2Masses.min() > ms1Delta.dist
                ):  # we have a range similar to the ms1
                    ms2Delta = getDelta(ms2Masses)
            if ms1Delta and ms2Delta:
                break
        if ms2Delta is None:
            ms2Delta = getDelta(ms2Masses)
    MS_X = namedtuple("MS_X", "ms1 ms2")
    return MS_X(-ms1Delta.delta, -ms2Delta.delta)


def setOptions_fromImputPaths(input_files_dir, root_mfql_dir):
    """replaces options values with some likely defaults, and calculated paths"""
    """see https://wiki.mpi-cbg.de/lipidx/LipidXplorer_Reference"""
    resolutionDeltas = getResolutionDeltas(input_files_dir)
    options = {}
    options["dataType"] = inputFileType(input_files_dir)  # TODO why is this duplicated?
    options["spectraFormat"] = inputFileType(input_files_dir)
    options["MStolerance"] = getTolerance()
    options["MSMStolerance"] = getTolerance()
    options["importDir"] = input_files_dir
    options["MSminOccupation"] = 0  # TODO why does this not change the results
    options["MSMSminOccupation"] = 0
    options["alignmentMethodMS"] = "linear"
    options["alignmentMethodMSMS"] = "linear"
    options["scanAveragingMethod"] = "linear"
    options["importMSMS"] = True  # TODO check in mfql
    options["timerange"] = (0.0, float("inf"))  # TODO perfoirmance
    options["MSmassrange"] = getMinMaxMFQLMass(root_mfql_dir)
    options["MSMSmassrange"] = (
        0,
        getMinMaxMFQLMass(root_mfql_dir)[1],
    )  # TODO handle neutral loss neutral charege takes a fragement
    options["MSthresholdType"] = "relative"  # TODO replace this with jaco filter?
    options["MSMSthresholdType"] = "relative"
    options["pisSpectra"] = False
    # after the import
    options["MSresolution"] = getTolerance()
    options["MSresolutionDelta"] = resolutionDeltas.ms1
    options[
        "MSthreshold"
    ] = 0.00001  # intensity threshold shooul be addressed by jaco filter
    options["MSMSthreshold"] = 0.00001
    options["precursorMassShift"] = 0.0
    options["precursorMassShiftOrbi"] = None
    options[
        "MScalibration"
    ] = ""  # options_og['MScalibration'] #todo find most intense peak and use that?... should actually use a standard
    options["MSMScalibration"] = None
    options["selectionWindow"] = 0.5  # TODO why does this affect the results so much
    options["MSMSresolution"] = getTolerance(
        11.11
    )  # todo why this malkes different results
    options["MSMSresolutionDelta"] = resolutionDeltas.ms2
    options["isotopicCorrectionMS"] = True
    options["isotopicCorrectionMSMS"] = True
    options["complementMasterScan"] = False
    options["statistics"] = False
    options["optionalMStolerance"] = getTolerance(
        2.0
    )  # todo why this gets differrent results
    options["optionalMSMStolerance"] = getTolerance(2.0)
    options[
        "noPermutations"
    ] = False  # we keep permutations, why remove them? maybe only not report them
    options["intensityCorrection"] = False
    options["noHead"] = False
    options["resultFile"] = resultFileName(input_files_dir)
    return options
