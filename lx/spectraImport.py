#!/usr/bin/python
import csv
import os, sys, re
from collections import namedtuple
from optparse import OptionParser

import time

sysPath = ".." + os.sep + "lib"
sys.path.append(sysPath)

from lx.tools import reportout, unique
from lx.mfql.runtimeStatic import TypeTolerance
from lx.exceptions import LipidXException
from lx.spectraContainer import MasterScan, SurveyEntry
from lx.spectraTools import recalibrateMS, recalibrateMSMS, saveSC
from lx.readSpectra import add_Sample, add_mzXMLSample, add_DTASample
from lx.alignment import (
    alignPIS,
    mkSurveyLinear,
    mkSurveyHierarchical,
    mkSurveyHeuristic,
    mkMSMSEntriesLinear_new,
    mkMSMSEntriesHeuristic_new,
    specEntry,
    linearAlignment,
)

from lx.debugger import Debug

from lx.readSpectra_refactor import add_Sample as add_Sample_ref


# for debugging
# from guppy import hpy


def lpdxImportDEF_new(parent, options=None):
    """This version of importDEF does not process the options, since
    it assumes that they are already processed by lx.options.py"""

    # generate MasterScan object
    scan = MasterScan(options)

    scan.importSettingsFile = options["ini"]
    # scan.setting = options['setting']
    if not parent is None:
        scan.setting = parent.currentConfiguration
    else:
        scan.setting = options["setting"]
    scan.importDir = options["importDir"]

    # check if last char is a '/':
    if scan.importDir[-1] == os.sep:
        scan.importDir = scan.importDir[:-1]

    # load occupation threshold settings
    if os.path.exists("%s\\groups.txt" % scan.importDir):
        with open("%s\\groups.txt" % scan.importDir) as f:
            s = f.readlines()
            if not s == []:
                for i in s:
                    # scan.sampleOccThr['MS'].append((float(i.split(':')[0]), [x.strip() for x in i.split(':')[1].split(',')]))
                    # scan.sampleOccThr['MSMS'].append((float(i.split(':')[0]), [x.strip() for x in i.split(':')[1].split(',')]))
                    scan.sampleOccThr["MS"].append(
                        (options["MSminOccupation"], [x.strip() for x in i.split(",")])
                    )
                    scan.sampleOccThr["MSMS"].append(
                        (
                            options["MSMSminOccupation"],
                            [x.strip() for x in i.split(",")],
                        )
                    )
            else:
                scan.sampleOccThr["MS"] = [(options["MSminOccupation"], [])]
                scan.sampleOccThr["MSMS"] = [(options["MSMSminOccupation"], [])]
    else:
        scan.sampleOccThr["MS"] = [(options["MSminOccupation"], [])]
        scan.sampleOccThr["MSMS"] = [(options["MSMSminOccupation"], [])]

    (listFiles, isTaken, isGroup) = getInputFiles(scan.importDir, options)

    scan.listFiles = listFiles

    return (
        options,
        scan,
        scan.importDir,
        options["masterScanImport"],
        parent,
        listFiles,
        isTaken,
        isGroup,
    )


def lpdxImportDEF(
    parent=None,
    forcesinglecharge=None,
    timerange=None,
    selectionWindow=None,
    MSresolution=None,
    MSMSresolution=None,
    MStolerance=None,
    MStoleranceType=None,
    MSMStolerance=None,
    MSMStoleranceType=None,
    MSmassrange=None,
    MSMSmassrange=None,
    MSthreshold=None,
    MSMSthreshold=None,
    MSthresholdType=None,
    MSMSthresholdType=None,
    MSminOccupation=None,
    MSMSminOccupation=None,
    MSresolutionDelta=None,
    MSMSresolutionDelta=None,
    MScalibration=None,
    MSMScalibration=None,
    precursorMassShift=None,
    precursorMassShiftOrbi=None,
    mzXML=None,
    importData=None,
    masterScan=None,
    importDir=None,
    output=None,
    configuration=None,
    iniFile=None,
):

    options = {}

    if forcesinglecharge and forcesinglecharge != "0":
        options["forcesinglecharge"] = int(forcesinglecharge)
    else:
        options["forcesinglecharge"] = None

    if selectionWindow and selectionWindow != "0":
        options["selectionWindow"] = float(selectionWindow)
    else:
        options["selectionWindow"] = None

    if timerange and timerange != "0":
        options["timerange"] = (
            float(timerange.split(",")[0].strip("() ")),
            float(timerange.split(",")[1].strip("() ")),
        )
        if not options["timerange"][0] <= options["timerange"][1]:
            raise LipidXException(
                "second value in timerange is smaller then first, which makes no sense ..."
            )
    else:
        options["timerange"] = None

    if MScalibration and MScalibration != "0":
        tmp = MScalibration.split(",")
        options["MScalibration"] = []
        for i in tmp:
            try:
                options["MScalibration"].append(float(i))
            except:
                raise LipidXException(
                    "The format of the MS calibration mass list is wrong."
                )
    else:
        options["MScalibration"] = None

    if MSMScalibration and MSMScalibration != "0":
        tmp = MSMScalibration.split(",")
        options["MSMScalibration"] = []
        for i in tmp:
            try:
                options["MSMScalibration"].append(float(i))
            except:
                raise LipidXException(
                    "The format of the MS/MS calibration mass list is wrong."
                )
    else:
        options["MSMScalibration"] = None

    if MSmassrange and MSmassrange != "0":
        options["MSmassrange"] = (
            float(MSmassrange.split(",")[0].strip("() ")),
            float(MSmassrange.split(",")[1].strip("() ")),
        )
        if not options["MSmassrange"][0] <= options["MSmassrange"][1]:
            raise LipidXException(
                "second value in MSmassrange is smaller then first, which makes no sense ..."
            )
    else:
        options["MSmassrange"] = None

    if MSMSmassrange and MSMSmassrange != "0":
        options["MSMSmassrange"] = (
            float(MSMSmassrange.split(",")[0].strip("() ")),
            float(MSMSmassrange.split(",")[1].strip("() ")),
        )
        if not options["MSMSmassrange"] <= options["MSMSmassrange"]:
            raise LipidXException(
                "second value in MSMSmassrange is smaller then first, which makes no sense ..."
            )
    else:
        options["MSMSmassrange"] = None

    if MSresolution and MSresolution != "0":
        options["MSresolution"] = TypeTolerance(
            "res",
            float(MSresolution),
            smallestMass=options["MSmassrange"][0],
            delta=float(MSresolutionDelta),
        )
    else:
        options["MSresolution"] = None

    if MSMSresolution and MSMSresolution != "0":
        options["MSMSresolution"] = TypeTolerance(
            "res",
            float(MSMSresolution),
            smallestMass=options["MSMSmassrange"][0],
            delta=float(MSMSresolutionDelta),
        )
    else:
        options["MSMSresolution"] = None

    if MStolerance and MStolerance != "0":
        if MStoleranceType and MStoleranceType != "":
            options["MStolerance"] = TypeTolerance(MStoleranceType, float(MStolerance))
            options["MStoleranceType"] = MStoleranceType
        else:
            options["MStolerance"] = TypeTolerance("ppm", float(MStolerance))
    else:
        options["MStolerance"] = None

    if MSMStolerance and MSMStolerance != "0":
        if MSMStoleranceType and MSMStoleranceType != "":
            options["MSMStolerance"] = TypeTolerance(
                MSMStoleranceType, float(MSMStolerance)
            )
            options["MSMStoleranceType"] = MSMStoleranceType
        else:
            options["MSMStolerance"] = TypeTolerance("ppm", float(MSMStolerance))
    else:
        options["MSMStolerance"] = None

    if MSthreshold and MSthreshold != "0":
        options["MSthreshold"] = float(MSthreshold)
        if not 0.0 <= options["MSthreshold"]:
            # log.critical("MSthreshold has to a positve value")
            raise LipidXException("MSthreshold has to a positve value")
    else:
        options["MSthreshold"] = None

    if MSMSthreshold and MSMSthreshold != "0":
        options["MSMSthreshold"] = float(MSMSthreshold)
        if not 0.0 <= options["MSMSthreshold"]:
            # log.critical("MSMSthreshold has to a positve value")
            raise LipidXException("MSMSthreshold has to a positve value")
    else:
        options["MSMSthreshold"] = None

    if MSthresholdType and MSthresholdType != "0":
        options["MSthresholdType"] = MSthresholdType
    else:
        options["MSthresholdType"] = None

    if MSMSthresholdType and MSMSthresholdType != "0":
        options["MSMSthresholdType"] = MSMSthresholdType
    else:
        options["MSMSthresholdType"] = None

    if MSminOccupation and MSminOccupation != "0":
        options["MSminOccupation"] = float(MSminOccupation)
        if (0.0 > options["MSminOccupation"]) or (1.0 < options["MSminOccupation"]):
            # log.critical("MSminOccupation should be a value between 0 and 1")
            raise LipidXException("MSminOccupation should be a value between 0 and 1")
    else:
        options["MSminOccupation"] = 0.0

    if MSMSminOccupation and MSMSminOccupation != "0":
        options["MSMSminOccupation"] = float(MSMSminOccupation)
        if (0.0 > options["MSMSminOccupation"]) or (1.0 < options["MSMSminOccupation"]):
            # log.critical("MSMSminOccupation should be a value between 0 and 1")
            raise LipidXException("MSMSminOccupation should be a value between 0 and 1")
    else:
        options["MSMSminOccupation"] = 0.0

    if MSresolutionDelta:
        options["MSresolutionDelta"] = float(MSresolutionDelta)

    if MSMSresolutionDelta and MSMSresolutionDelta != "0":
        options["MSMSresolutionDelta"] = float(MSMSresolutionDelta)
    else:
        options["MSMSresolutionDelta"] = None

    if precursorMassShift and precursorMassShift != "0":
        options["precursorMassShift"] = precursorMassShift
    else:
        options["precursorMassShift"] = 0

    if precursorMassShiftOrbi and precursorMassShiftOrbi != "0":
        options["precursorMassShiftOrbi"] = precursorMassShiftOrbi
    else:
        options["precursorMassShiftOrbi"] = 0

    options["mzXML"] = mzXML
    options["loopNr"] = 3  # three is default ;)

    #### set standard values

    # if options['forcesinglecharge'] == None:
    # 	options['forcesinglecharge'] = 0
    ##timerange = None
    # if options['selectionWindow'] == None:
    # 	options['selectionWindow'] = 0.5
    # if options['MSresolution'] == None:
    # 	raise LipidXException("MS resolution has to be set")
    # if options['MSMSresolution'] == None:
    # 	raise LipidXException("MS/MS resolution has to be set")
    ##MSmassrange = None,
    ##MSMSmassrange = None,
    # if options['MSthreshold'] == None:
    # 	options['MSthreshold'] = 0.0001
    # if options['MSMSthreshold'] == None:
    # 	options['MSMSthreshold'] = 0.0001
    # MSminOccupation = None,
    # MSMSminOccupation = None,
    # MSresolutionDelta = None,
    # MSMSresolutionDelta = None,
    # MScalibration = None,
    # MSMScalibration = None,
    # precursorMassShift = None,
    # precursorMassShiftOrbi = None,
    # mzXML = None,
    # importData = None,
    # masterScan = None,
    # importDir = None,
    # output = None,

    # generate MasterScan object
    scan = MasterScan(options)

    # check if last char is a '/':
    if importDir[-1] == os.sep:
        importDir = importDir[:-1]

    scan.importSettingsFile = iniFile
    scan.setting = configuration
    scan.importDir = importDir

    # load occupation threshold settings
    if os.path.exists("%s\\groups.txt" % importDir):
        with open("%s\\groups.txt" % importDir) as f:
            s = f.readlines()
            if not s == []:
                for i in s:
                    # scan.sampleOccThr['MS'].append((float(i.split(':')[0]), [x.strip() for x in i.split(':')[1].split(',')]))
                    # scan.sampleOccThr['MSMS'].append((float(i.split(':')[0]), [x.strip() for x in i.split(':')[1].split(',')]))
                    scan.sampleOccThr["MS"].append(
                        (options["MSminOccupation"], [x.strip() for x in i.split(",")])
                    )
                    scan.sampleOccThr["MSMS"].append(
                        (
                            options["MSMSminOccupation"],
                            [x.strip() for x in i.split(",")],
                        )
                    )
            else:
                scan.sampleOccThr["MS"] = [(options["MSminOccupation"], [])]
                scan.sampleOccThr["MSMS"] = [(options["MSMSminOccupation"], [])]
    else:
        scan.sampleOccThr["MS"] = [(options["MSminOccupation"], [])]
        scan.sampleOccThr["MSMS"] = [(options["MSMSminOccupation"], [])]

    (listFiles, isTaken, isGroup) = getInputFiles(importDir, options)

    scan.listFiles = listFiles

    return (options, scan, importDir, output, parent, listFiles, isTaken, isGroup)


def getInputFiles(importDir, options):

    if not os.path.exists(importDir):
        raise LipidXException("Sample data '%s' folder not found." % importDir)

    if not os.path.isdir(importDir):
        raise LipidXException("Sample data '%s' is not a folder." % importDir)

    listFiles = []
    isGroup = False
    groupedSamples = False
    isTaken = False

    for root, dirs, files in os.walk(importDir):

        # import XML without having groups
        if not (re.match("(^\.\w+).*|.*\.svn.*", root)) and options[
            "spectraFormat"
        ] in ["mzML", "mzXML", "raw", "rawA"]:

            if options["spectraFormat"] == "rawA":
                ext = "raw"
            else:
                ext = options["spectraFormat"]

            isTaken = True
            if not re.match("(^\.\w+).*|.*\.svn.*", root):
                for f in files:
                    if re.match("(.*\.%s$)|(.*\.xml)" % ext, f, re.IGNORECASE):
                        listFiles.append([root + os.sep + f, root])

                # it is empty when folders for sample groups are given, because
                # this is the first point where os.walk() will be
                if listFiles == []:
                    groupedSamples = True

                if groupedSamples and listFiles != []:
                    samplegroupName = listFiles[0][1].split(os.sep)[-1]

        # import *.dta without having groups
        elif (
            not (re.match("(^\.\w+).*|.*\.svn.*", root))
            and options["spectraFormat"] == "dta/csv"
        ):
            isTaken = True
            for i in dirs:
                if not re.match("(^\.\w+).*|.*\.svn.*", i):
                    listFiles.append([root + os.sep + i, i])

        elif re.match("(^\.\w+).*|.*\.svn.*", root):
            pass

        else:
            raise LipidXException(
                "Problems with the data format %s in %s"
                % (options["spectraFormat"], root)
            )

    if listFiles == []:
        raise LipidXException(
            "No spectra files with the format *.%s found." % options["spectraFormat"]
        )

    return (listFiles, isTaken, isGroup)


def doImport(
    options,
    scan,
    importDir,
    output,
    parent,
    listFiles,
    isTaken,
    isGroup,
    alignmentMS,
    alignmentMSMS,
    scanAvg,
    importMSMS=True,
    saveScan=True,
):

    # some statistics
    nb_ms_scans = []
    nb_ms_peaks = []
    nb_msms_scans = []
    nb_msms_peaks = []

    # go recursively through the directory
    listPolarity = []
    dictBasePeakIntensity = {}
    progressCount = 0

    # the scan.dictSample variable is filled with
    # MSmass and MSMS classes. This means, the raw *.dta
    # and *.csv data is loaded into scan.dictSample.
    # After loading the cleaning algorithm is applied.

    # the scan.dictSample variable is filled with
    # MSmass and MSMS classes taken from mzXML files.
    # After loading the cleaning algorithm is applied.
    if listFiles != []:
        listFiles.sort()

        for i in listFiles:

            if (
                options["spectraFormat"] == "mzXML"
            ):  # old mzXML import. I don't wanna touch this
                ret = add_mzXMLSample(
                    scan,
                    i[0],
                    i[1],
                    timerange=scan.options["timerange"],
                    MSmassrange=scan.options["MSmassrange"],
                    MSMSmassrange=scan.options["MSMSmassrange"],
                    scanAveraging=scanAvg,
                    isGroup=isGroup,
                    importMSMS=importMSMS,
                    MSthresholdType=scan.options["MSthresholdType"],
                    MSMSthresholdType=scan.options["MSMSthresholdType"],
                )

            elif options["spectraFormat"] == "mzML":  # the new import routine, :-)

                ret = add_Sample(
                    scan,
                    i[0],
                    i[1],
                    options=scan.options,
                    timerange=scan.options["timerange"],
                    MSmassrange=scan.options["MSmassrange"],
                    MSMSmassrange=scan.options["MSMSmassrange"],
                    scanAveraging=scanAvg,
                    isGroup=isGroup,
                    importMSMS=importMSMS,
                    MSthresholdType=scan.options["MSthresholdType"],
                    MSMSthresholdType=scan.options["MSMSthresholdType"],
                    fileformat="mzML",
                )

            dictBasePeakIntensity[ret[0]] = ret[1]

            if len(ret) > 2:
                nb_ms_scans.append(ret[2])
                nb_ms_peaks.append(ret[3])
                nb_msms_scans.append(ret[4])
                nb_msms_peaks.append(ret[5])

            if ret[6] == 0:
                raise ValueError(f" File {i[0]} contains 0 peaks after alignment")

            if nb_ms_peaks[-1] == 0:
                raise ValueError(f" File {i[0]} contains 0 MS1 peaks after alignment")
            elif nb_msms_peaks[-1] == 0:
                raise ValueError(f" File {i[0]} contains 0 MS2 peaks after alignment")

    if (not scan.options.isEmpty("precursorMassShift")) and scan.options[
        "precursorMassShift"
    ]:
        if scan.options["precursorMassShift"] != 0:
            print("Applying precursor mass shift")
            scan.shiftPrecursors(scan.options["precursorMassShift"])

    if (not scan.options.isEmpty("precursorMassShiftOrbi")) and scan.options[
        "precursorMassShiftOrbi"
    ]:
        if scan.options["precursorMassShiftOrbi"] != 0:
            print("Applying precursor mass shift for Scanline error on Orbitrap data.")
            scan.shiftPrecursorsInRawFilterLine(scan.options["precursorMassShiftOrbi"])

    scan.listSamples.sort()

    if listPolarity == []:
        listPolarity = [-1, 1]
    else:
        listPolarity = unique(listPolarity)

    # recalibrate MS spectra
    if not scan.options.isEmpty("MScalibration"):
        ms1_recal_table = recalibrateMS(
            scan,
            scan.options["MScalibration"],
            scan.options["alignmentMethodMS"] == "calctol",
        )
    if not scan.options.isEmpty("MSMScalibration") and (
        scan.options["MSMScalibration"]
    ):
        recalibrateMSMS(
            scan,
            scan.options["MSMScalibration"],
            isCalctol=scan.options["alignmentMethodMS"] == "calctol",
        )
    elif not scan.options.isEmpty("MScalibration") and scan.options.isEmpty(
        "MSMScalibration"
    ):
        print("recalibrating msms with ms calibration")  # as requested by KS
        recalibrateMSMS(
            scan,
            scan.options["MScalibration"],
            isCalctol=scan.options["alignmentMethodMS"] == "calctol",
            ms1_recal_table=ms1_recal_table,
        )

    # align MS spectra
    print("Aligning MS spectra", alignmentMS)

    ### align the spectra for the MasterScan ###

    if alignmentMS in ["linear", "calctol"]:
        mkSurveyLinear(
            scan,
            [-1, 1],
            numLoops=options["loopNr"],
            deltaRes=scan.options["MSresolutionDelta"],
            minocc=scan.options["MSminOccupation"],
            bin_res=scan.options["alignmentMethodMS"] == "calctol",
            collapse=scan.options["alignmentMethodMS"] == "calctol",
        )

    ### aling the fragment spectra ###

    # Preparation of MSMS experiments is:
    # 1) clustering of the dta's precursor masses according
    # 	 to MS accuracy -> every cluster contains all MSMS
    #    experiments for precursor mass m where thier dta-precursor
    # 	 mass p is in [m - MSaccuracy, m + MSaccuracy]
    # 2) The MSMS experiments of one cluster c are then
    # 	 merged with the known merging algorithm
    # 3) Every cluster c is associated to a precursor mass M
    # 	 from the SurveyEntry list. This takes the
    # 	 given selectionWindow into account.
    if importMSMS:
        reportout("Aligning MS/MS spectra %s\n" % alignmentMSMS)
        if alignmentMSMS in ["linear", "calctol"]:
            mkMSMSEntriesLinear_new(
                scan,
                listPolarity,
                numLoops=options["loopNr"],
                isPIS=options["pisSpectra"],
                bin_res=options["alignmentMethodMSMS"] == "calctol",
                collapse=scan.options["alignmentMethodMSMS"] == "calctol",
            )

    # blanks = potential_blanks(scan.listSurveyEntry, 25) # be careguk not to confiuse blanks with internal standards
    # blanks are singnals that are in all the samples? and low intens?
    # istd are signals that are on all except blanks and high intens

    for sample in scan.listSamples:
        if sample in scan.dictSamples:
            del scan.dictSamples[sample]
    del scan.dictSamples

    scan.sortAndIndedice()
    for se in scan.listSurveyEntry:
        se.sortAndIndedice()

    ranking = alignment_ranking(scan.listSurveyEntry)
    ac = ranked_entries(scan.listSurveyEntry, ranking, 25)
    print()
    print("Top 25 suggested calibration masses")
    for s in ac:
        print(s)
    print()

    if options["settingsPrefix"]:
        splitext = os.path.splitext(output)
        output = splitext[0] + "-" + scan.setting + splitext[1]

    if saveScan:
        print("Save output to %s." % output)
        saveSC(scan, output)

    return scan


def get_sum_i(listSurveyEntry):
    sum_i = {}
    for se in listSurveyEntry:
        for k, i in se.dictIntensity.items():
            sum_i[k] = sum_i.get(k, 0) + i

    # m = max(sum_i.values())
    # print(sum_i)
    return sum_i


def alignment_ranking(listSurveyEntry, count=10):
    sum_i = get_sum_i(listSurveyEntry)
    suspected_blank = min(sum_i, key=lambda key: sum_i[key])  # suspected blank
    idx = []
    scan_ratio = []
    non0_avg_rel_i = []
    non0_avg_abs_i = []
    for e in listSurveyEntry:
        rel_i = []
        abs_i = []
        if e.dictIntensity[suspected_blank] > 0:
            continue  # ignore all the signals that where in the suspected blank
        for k, v in e.dictBasePeakIntensity.items():
            if e.dictIntensity[k] == 0:
                continue  # ignore zero
            rel_i.append(e.dictIntensity[k] / v)
            abs_i.append(e.dictIntensity[k])
        non0_avg_rel_i.append(sum(rel_i) / len(rel_i))
        non0_avg_abs_i.append(sum(abs_i) / len(rel_i))
        idx.append(e.index)
        scan_ratio.append(len(abs_i) / len(e.dictBasePeakIntensity))
    vals = (idx, scan_ratio, non0_avg_rel_i, non0_avg_abs_i)
    vals = list(zip(*vals))
    vals = sorted(vals, key=lambda x: x[1] + x[2], reverse=True)
    nt = namedtuple("rank_data", "idx scan_ratio non0_avg_rel_i non0_avg_abs_i")
    vals = [nt(*v) for v in vals]
    return vals


def ranked_entries(listSurveyEntry, vals, count=10):
    res = []
    for e in vals[:count]:
        res.append(listSurveyEntry[e.idx])

    return res


def doImport_alt(
    options,
    scan_original,
    importDir,
    output,
    parent,
    listFiles,
    isTaken,
    isGroup,
    alignmentMS,
    alignmentMSMS,
    scanAvg,
    importMSMS=True,
):
    """Alternative import which splits the spectra into chunks
    to save memory."""

    ### set standard values

    assert isinstance(importMSMS, type(True))

    if Debug("logMemory"):
        from guppy import hpy
        import memory_logging

    # time
    starttime = time.clock()

    # go recursively through the directory
    listPolarity = []
    dictBasePeakIntensity = {}
    progressCount = 0

    # set the chunk size
    chunk_size = 10

    # the list of the survey Entries
    listSurveyEntries = []

    # the scan.dictSample variable is filled with
    # MSmass and MSMS classes. This means, the raw *.dta
    # and *.csv data is loaded into scan.dictSample.
    # After loading the cleaning algorithm is applied.
    if options["spectraFormat"] == "dta/csv" and isTaken:
        pass
    # 	if listFiles != []:
    # 		listFiles.sort()
    #
    # 			for i in listFiles:
    ##				ret = add_DTASample(scan, i[0], i[1],
    # 					MSmassrange = scan.options['MSmassrange'],
    # 					MSMSmassrange = scan.options['MSMSmassrange'],
    # 					importMSMS = importMSMS,
    # 					thresholdType = scan.options['MSthresholdType'])
    #
    # 				listPolarity.append(ret[0])
    # 				dictBasePeakIntensity[ret[2]] = ret[1]

    # progressCount += 1
    # if parent:
    # 	(cont, skip) = parent.debug.progressDialog.Update(progressCount)
    # 	if not cont:
    # 		print "Stopped by user."
    # 		parent.debug.progressDialog.Destroy()
    # 		return parent.CONST_THREAD_USER_ABORT

    # the scan.dictSample variable is filled with
    # MSmass and MSMS classes taken from mzXML files.
    # After loading the cleaning algorithm is applied.
    elif listFiles != []:
        listFiles.sort()

        listOfListFiles = []
        index = 0
        while index < len(listFiles):
            listOfListFiles.append([])
            for j in range(chunk_size):
                if index < len(listFiles):
                    listOfListFiles[-1].append(listFiles[index])
                    index += 1

        for chunk in listOfListFiles:

            scan = MasterScan(scan_original.options)
            scan.options = scan_original.options
            # listSamples = []
            # dictSamples = {}

            for i in chunk:

                if (
                    options["spectraFormat"] == "mzXML"
                ):  # old mzXML import. I don't wanna touch this
                    ret = add_mzXMLSample(
                        scan,
                        i[0],
                        i[1],
                        timerange=scan.options["timerange"],
                        MSmassrange=scan.options["MSmassrange"],
                        MSMSmassrange=scan.options["MSMSmassrange"],
                        scanAveraging=scanAvg,
                        isGroup=isGroup,
                        importMSMS=importMSMS,
                        MSthresholdType=scan.options["MSthresholdType"],
                        MSMSthresholdType=scan.options["MSMSthresholdType"],
                    )

                elif options["spectraFormat"] in [
                    "mzML",
                    "raw",
                ]:  # the new import routine, :-)
                    ret = add_Sample(
                        scan,
                        i[0],
                        i[1],
                        options=scan.options,
                        timerange=scan.options["timerange"],
                        MSmassrange=scan.options["MSmassrange"],
                        MSMSmassrange=scan.options["MSMSmassrange"],
                        scanAveraging=scanAvg,
                        isGroup=isGroup,
                        importMSMS=importMSMS,
                        MSthresholdType=scan.options["MSthresholdType"],
                        MSMSthresholdType=scan.options["MSMSthresholdType"],
                    )

                dictBasePeakIntensity[ret[0]] = ret[1]
                # listSamples.append(ret[2])
                # dictSamples[ret[2]] = ret[3]

            if not len(list(dictBasePeakIntensity.keys())) > 0:
                raise LipidXException(
                    "Something wrong with the calculation of the base peaks"
                )

            loadingtime = time.clock() - starttime
            reportout("%.2f sec. for reading the spectra" % loadingtime)

            # if Debug("logMemory"):
            # 	print "ML> spectra for one chunk loaded:", memory_logging.pythonMemory()
            # 	print "MLh> ", hpy().heap()

            if (not scan.options.isEmpty("precursorMassShift")) and scan.options[
                "precursorMassShift"
            ]:
                if scan.options["precursorMassShift"] != 0:
                    print("Applying precursor mass shift")
                    scan.shiftPrecursors(scan.options["precursorMassShift"])

            if (not scan.options.isEmpty("precursorMassShiftOrbi")) and scan.options[
                "precursorMassShiftOrbi"
            ]:
                if scan.options["precursorMassShiftOrbi"] != 0:
                    print(
                        "Applying precursor mass shift for Scanline error on Orbitrap data."
                    )
                    scan.shiftPrecursorsInRawFilterLine(
                        scan.options["precursorMassShiftOrbi"]
                    )

            scan.listSamples.sort()

            if listPolarity == []:
                listPolarity = [-1, 1]
            else:
                listPolarity = unique(listPolarity)

            # recalibrate MS spectra
            if not scan.options.isEmpty("MScalibration"):
                lRecalTable = recalibrateMS(scan, scan.options["MScalibration"])
            if not scan.options.isEmpty("MSMScalibration") and (
                scan.options["MSMScalibration"]
            ):
                lRecalTable = recalibrateMSMS(scan, scan.options["MSMScalibration"])

            calibrationtime = time.clock() - starttime - loadingtime
            reportout("%.2f sec. for calibrating the spectra" % calibrationtime)

            # if Debug("logMemory"):
            # 	print "ML> before alignment:", memory_logging.pythonMemory()
            # 	print "MLh> ", hpy().heap()

            # align MS spectra
            print("Aligning MS spectra", alignmentMS)

            # for PIS
            if options["pisSpectra"]:
                alignPIS(
                    scan,
                    [-1, 1],
                    numLoops=options["loopNr"],
                    deltaRes=scan.options["MSMSresolutionDelta"],
                    minocc=scan.options["MSMSminOccupation"],
                    alignmentMS=alignmentMS,
                )

            if alignmentMS == "linear":
                mkSurveyLinear(
                    scan,
                    [-1, 1],
                    numLoops=options["loopNr"],
                    deltaRes=scan.options["MSresolutionDelta"],
                    minocc=scan.options["MSminOccupation"],
                    checkoccupation=False,
                )

            elif alignmentMS == "hierarchical":
                # experimental
                mkSurveyHierarchical(
                    scan,
                    "",
                    numLoops=options["loopNr"],
                    deltaRes=scan.options["MSresolutionDelta"],
                    minocc=scan.options["MSminOccupation"],
                    checkoccupation=False,
                )

            elif alignmentMS == "heuristic":
                mkSurveyHeuristic(
                    scan,
                    "",
                    numLoops=options["loopNr"],
                    deltaRes=scan.options["MSresolutionDelta"],
                    minocc=scan.options["MSminOccupation"],
                    checkoccupation=False,
                )

            reportout(
                "> {0:.<30s}{1:>11d}\n".format(
                    "Nb. of MS peaks (after alg.)", len(scan.listSurveyEntry)
                )
            )

            # collect the survey entries from the chunk
            listSurveyEntries.append(scan.listSurveyEntry)

            scan_original.listSamples += scan.listSamples
            for sample in scan.dictSamples:
                scan_original.dictSamples[sample] = scan.dictSamples[sample]

            # if Debug("logMemory"):
            # 	print "ML> after alignment:", memory_logging.pythonMemory()
            # 	print "MLh> after alignment", hpy().heap()

    ### align the chunks ###

    if Debug("logMemory"):
        print("ML> before alignment of the chunks:", memory_logging.pythonMemory())
        print("MLh> before alignment of the chunks:", hpy().heap())

    # generate a list of specEntry elements for the alignment of the SurveyEntries
    dictSpecEntry = {}
    for i in range(len(listSurveyEntries)):
        dictSpecEntry[repr(i)] = []
        for entry in listSurveyEntries[i]:
            dictSpecEntry[repr(i)].append(
                specEntry(
                    mass=entry.precurmass,
                    content={"sample": repr(i), "surveyEntry": entry},
                )
            )

    listClusters = linearAlignment(
        list(dictSpecEntry.keys()), dictSpecEntry, scan.options["MSresolution"]
    )

    #### check again with this debugging output!
    # for sample in dictSpecEntry.keys():#cl.keys():
    # 	print sample,
    # print ''
    # for cl in listClusters:
    # 	str = ''
    # 	for sample in dictSpecEntry.keys():#cl.keys():
    # 		if cl.has_key(sample):
    # 			if cl[sample].content:
    # 				str +=  "  %.4f  " % cl[sample].mass
    # 			else:
    # 				try:
    # 					str +=  " /%.4f/ " % cl[sample].mass
    # 				except TypeError:
    # 					print "TypeError:", cl[sample].mass
    # 		else:
    # 			str += " / empty  / "
    # 	print str
    ### end of the debugging output

    # mk the new SurveyEntries
    listSurveyEntry = []
    for cl in listClusters:

        # collect the base peaks
        dictBasePeakIntensity = {}

        # collect the scans
        dictScans = {}

        # collect the individual peaks
        peaks = []

        # collect intensities
        dictIntensity = {}

        # calc the average mass
        avgMass = 0
        count = 0
        polarity = 0
        for chunk in list(dictSpecEntry.keys()):  # cl.keys():
            if chunk in cl:
                if cl[chunk].content:
                    polarity = cl[chunk].content["surveyEntry"].polarity
                    for key in list(
                        cl[chunk].content["surveyEntry"].dictIntensity.keys()
                    ):
                        if key not in dictIntensity:
                            dictIntensity[key] = (
                                cl[chunk].content["surveyEntry"].dictIntensity[key]
                            )
                            dictScans[key] = (
                                cl[chunk].content["surveyEntry"].dictScans[key]
                            )
                            dictBasePeakIntensity[key] = (
                                cl[chunk]
                                .content["surveyEntry"]
                                .dictBasePeakIntensity[key]
                            )
                            peaks += cl[chunk].content["surveyEntry"].peaks

                        else:
                            raise LipidXException("Something wrong: samples overlap")
                    count += 1
                    avgMass += cl[chunk].mass
        avgMass /= count

        for sample in scan_original.listSamples:
            if not sample in list(dictIntensity.keys()):
                dictIntensity[sample] = 0.0
            if not sample in list(dictScans.keys()):
                dictScans[sample] = 1  # 1 - because we take the sqrt
            if not sample in list(dictBasePeakIntensity.keys()):
                dictBasePeakIntensity[sample] = 0

        # check occupation threshold
        if scan_original.checkOccupation(
            dictIntensity,
            dictScans,
            occThr=scan_original.options["MSminOccupation"],
            mode="MS",
            dictBasePeakIntensity=dictBasePeakIntensity,
            threshold=scan_original.options["MSthreshold"],
            threshold_type=scan_original.options["MSthresholdType"],
        ):

            listSurveyEntry.append(
                SurveyEntry(
                    msmass=avgMass,
                    smpl=dictIntensity,
                    peaks=peaks,
                    charge=None,
                    polarity=polarity,
                    dictScans=dictScans,
                    dictBasePeakIntensity=dictBasePeakIntensity,
                )
            )

    scan_original.listSurveyEntry = listSurveyEntry

    # if Debug("logMemory"):
    # 	print "ML> after alignment of the chunks (MS):", memory_logging.pythonMemory()
    # 	print "MLh> after alignment of the chunks (MS):", hpy().heap()

    # if not keepGoing:
    # 	print "Stopped by user."
    # 	parent.isRunning = False
    # 	return None

    # Preparation of MSMS experiments is:
    # 1) clustering of the dta's precursor masses according
    # 	 to MS accuracy -> every cluster contains all MSMS
    #    experiments for precursor mass m where thier dta-precursor
    # 	 mass p is in [m - MSaccuracy, m + MSaccuracy]
    # 2) The MSMS experiments of one cluster c are then
    # 	 merged with the known merging algorithm
    # 3) Every cluster c is associated to a precursor mass M
    # 	 from the SurveyEntry list. This takes the
    # 	 given selectionWindow into account.
    if importMSMS:
        reportout("Aligning MS/MS spectra %s\n" % alignmentMSMS)
        if alignmentMSMS == "linear":
            mkMSMSEntriesLinear_new(
                scan_original,
                listPolarity,
                numLoops=options["loopNr"],
                isPIS=options["pisSpectra"],
            )
        elif alignmentMSMS == "heuristic":
            mkMSMSEntriesHeuristic_new(
                scan_original,
                listPolarity,
                numLoops=options["loopNr"],
                isPIS=options["pisSpectra"],
            )

    alignmenttime = time.clock() - starttime - loadingtime - calibrationtime
    reportout("%.2f sec. for aligning the spectra\n" % alignmenttime)

    # free space in the MasterScan
    for sample in scan_original.listSamples:
        if sample in scan_original.dictSamples:
            del scan_original.dictSamples[sample]
    del scan_original.dictSamples

    scan_original.sortAndIndedice()
    for se in scan_original.listSurveyEntry:
        se.sortAndIndedice()

    # if Debug("logMemory"):
    # 	print "ML> after alignment of MS/MS:", memory_logging.pythonMemory()
    # 	print "MLh> ", hpy().heap()

    print("Save output to %s." % output)
    saveSC(scan_original, output)

    reportout("%.2f sec. for the whole import process" % (time.clock() - starttime))
    reportout("\n")

    if parent:
        # parent.debug.progressDialog.Destroy()
        return parent.CONST_THREAD_SUCCESSFUL


if __name__ == "__main__":
    pass
    # (options, scan, importDir, output) = lpdxImportCLI()
