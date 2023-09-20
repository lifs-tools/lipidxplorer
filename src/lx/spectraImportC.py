#!/usr/bin/python

import os, sys, re

import time

sysPath = ".." + os.sep + "lib"
sys.path.append(sysPath)

from lx.tools import reportout, unique
from lx.mfql.runtimeStatic import TypeTolerance
from lx.exceptions import LipidXException
from lx.spectraContainer import MasterScan, SurveyEntry, MSMSEntry
from lx.spectraTools import recalibrateMS, recalibrateMSMS, saveSC
from lx.readSpectraC import add_Sample, add_mzXMLSample, add_DTASample
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

import platform

if platform.machine() == "i686":
    from lx.fileReader.readspectra26_32.ReadSpectra import ProcessSpectra
elif platform.machine() == "x86":
    from lx.fileReader.readspectra26_32.ReadSpectra import ProcessSpectra
elif platform.machine() == "AMD64":
    from lx.fileReader.readspectra27_64.ReadSpectra import ProcessSpectra

from ImportSpectra import ImportSpectra

# for debugging
# from guppy import hpy


def vDict(d, keys, standard_value):
    for key in keys:
        if not key in list(d.keys()):
            d[key] = standard_value
    return d


def dictPathToFile(d):
    new = {}
    for key in list(d.keys()):
        new[key.split(os.sep)[-1]] = d[key]
    return new


def lpdxImportDEF_new(parent, options=None):
    """This version of importDEF does not process the options, since
    it assumes that they are already processed by lx.options.py"""

    # generate MasterScan object
    scan = MasterScan(options)

    scan.importSettingsFile = options["ini"]
    scan.setting = options["setting"]
    scan.importDir = options["importDir"]

    # check if last char is a '/':
    if scan.importDir[-1] == os.sep:
        scan.importDir = scan.importDir[:-1]

    # load occupation threshold settings
    if os.path.exists("%s\\groups.txt" % scan.importDir):
        f = open("%s\\groups.txt" % scan.importDir)
        s = f.readlines()
        if not s == []:
            for i in s:
                # scan.sampleOccThr['MS'].append((float(i.split(':')[0]), [x.strip() for x in i.split(':')[1].split(',')]))
                # scan.sampleOccThr['MSMS'].append((float(i.split(':')[0]), [x.strip() for x in i.split(':')[1].split(',')]))
                scan.sampleOccThr["MS"].append(
                    (
                        options["MSminOccupation"],
                        [x.strip() for x in i.split(",")],
                    )
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
        options["masterScan"],
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
            options["MStolerance"] = TypeTolerance(
                MStoleranceType, float(MStolerance)
            )
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
            options["MSMStolerance"] = TypeTolerance(
                "ppm", float(MSMStolerance)
            )
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
        if (0.0 > options["MSminOccupation"]) or (
            1.0 < options["MSminOccupation"]
        ):
            # log.critical("MSminOccupation should be a value between 0 and 1")
            raise LipidXException(
                "MSminOccupation should be a value between 0 and 1"
            )
    else:
        options["MSminOccupation"] = 0.0

    if MSMSminOccupation and MSMSminOccupation != "0":
        options["MSMSminOccupation"] = float(MSMSminOccupation)
        if (0.0 > options["MSMSminOccupation"]) or (
            1.0 < options["MSMSminOccupation"]
        ):
            # log.critical("MSMSminOccupation should be a value between 0 and 1")
            raise LipidXException(
                "MSMSminOccupation should be a value between 0 and 1"
            )
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
        f = open("%s\\groups.txt" % importDir)
        s = f.readlines()
        if not s == []:
            for i in s:
                # scan.sampleOccThr['MS'].append((float(i.split(':')[0]), [x.strip() for x in i.split(':')[1].split(',')]))
                # scan.sampleOccThr['MSMS'].append((float(i.split(':')[0]), [x.strip() for x in i.split(':')[1].split(',')]))
                scan.sampleOccThr["MS"].append(
                    (
                        options["MSminOccupation"],
                        [x.strip() for x in i.split(",")],
                    )
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

    return (
        options,
        scan,
        importDir,
        output,
        parent,
        listFiles,
        isTaken,
        isGroup,
    )


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
            "No spectra files with the format *.%s found."
            % options["spectraFormat"]
        )

    return (listFiles, isTaken, isGroup)


def doImport_new(
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
):
    if not options["spectraFormat"] == "raw":
        raise LipidXException("This version works only with raw files")

    # only absolute threshold allowed right now
    if (
        not options["MSthresholdType"] == "absolute"
        or not options["MSMSthresholdType"] == "absolute"
    ):
        raise LipidXException("Only absolute threshold type is allowed")

    # mk options dict for ImportSpectra
    is_options = {}
    is_options["lowRT"] = float(options["timerange"][0]) / 60
    is_options["highRT"] = float(options["timerange"][1]) / 60
    is_options["resolution_ms"] = 0  # int(options['MSresolution'].getTinR())
    is_options[
        "resolution_msms"
    ] = 0  # int(options['MSMSresolution'].getTinR())
    is_options[
        "resolution_delta_ms"
    ] = 0.0  # float(options['MSresolutionDelta'])
    is_options[
        "resolution_delta_msms"
    ] = 0.0  # float(options['MSMSresolutionDelta'])
    is_options["threshold_ms"] = 0.0  # float(options['MSthreshold'])
    is_options["threshold_msms"] = 0.0  # float(options['MSMSthreshold'])
    is_options["occupation_threshold_ms"] = float(options["MSminOccupation"])
    is_options["occupation_threshold_msms"] = float(
        options["MSMSminOccupation"]
    )
    is_options["min_mz"] = float(options["MSmassrange"][0])
    is_options["max_mz"] = float(options["MSmassrange"][1])
    is_options["min_mz_msms"] = float(options["MSMSmassrange"][0])
    is_options["max_mz_msms"] = float(options["MSMSmassrange"][1])
    is_options["selection_window"] = float(options["selectionWindow"])
    is_options["ms_only"] = not options["importMSMS"]

    ### start importing the raw files by calling the C import module ###
    lf = [str(x[0]) for x in listFiles]
    importedSpectra = ImportSpectra(lf, is_options)

    # mk file path -> file name (samples)
    samples = []
    for f in lf:  # lf - listFiles
        samples.append(f.split(os.sep)[-1])
    scan.listSamples = samples

    ### retrieve the imported peak entries ###
    # ret = importedSpectra.getPeakEntries()
    ms_header = importedSpectra.getMasterScanHeader()

    scan.dictScans = dictPathToFile(vDict(ms_header["scan_nb_ms"], samples, 1))
    scan.dictBasePeakIntensity = dictPathToFile(
        vDict(ms_header["base_peak_intensity_ms"], samples, 0.0)
    )

    nb_of_peak_entries = importedSpectra.getNumberOfPeakEntries()

    print("Store the spectra in the MasterScan spectra data base")

    # show some progress
    nb_progress_steps = 20
    print("")
    print("                   |                    | <- finished")

    for index in range(nb_of_peak_entries):
        if index % (nb_of_peak_entries / nb_progress_steps) == 0:
            print(".", end=" ")

        entry = importedSpectra.getPeakEntry(index)
        scan.listSurveyEntry.append(
            SurveyEntry(
                msmass=entry["mz"],
                smpl=vDict(dictPathToFile(entry["intensity"]), samples, 0.0),
                peaks=[],
                charge=None,
                # polarity = entry['polarity'],
                polarity=ms_header["polarity"],
                dictScans={},
                msms=None,
                dictBasePeakIntensity={},
            )
        )
        scan.listSurveyEntry[-1].dictScans = scan.dictScans
        scan.listSurveyEntry[
            -1
        ].dictBasePeakIntensity = scan.dictBasePeakIntensity

        assert scan.listSurveyEntry[-1].polarity != 0

        if entry["MSMS"] != []:
            for msms_entry in entry["MSMS"]:
                scan.listSurveyEntry[-1].listMSMS.append(
                    MSMSEntry(
                        mass=msms_entry["mz"],
                        dictIntensity=vDict(
                            dictPathToFile(msms_entry["intensity"]),
                            samples,
                            0.0,
                        ),
                        peaks=[],
                        # polarity = msms_entry['polarity'],
                        polarity=ms_header["polarity"],
                        charge=None,
                        se=None,
                        samples=samples,
                        dictScanCount={},
                        dictBasePeakIntensity={},
                    )
                )
                scan.listSurveyEntry[-1].listMSMS[
                    -1
                ].dictScanCount = dictPathToFile(
                    vDict(entry["scan_nb_msms"], samples, 1)
                )
                scan.listSurveyEntry[-1].listMSMS[
                    -1
                ].dictBasePeakIntensity = dictPathToFile(
                    vDict(entry["base_peak_intensity_msms"], samples, 0.0)
                )

                assert scan.listSurveyEntry[-1].listMSMS[-1].polarity != 0

    print("")
    print("Save output to %s." % output)
    saveSC(scan, output)

    # put "success" to the GUI
    if parent:
        # parent.debug.progressDialog.Destroy()
        return parent.CONST_THREAD_SUCCESSFUL


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
):
    ### set standard values

    assert isinstance(importMSMS, type(True))

    # if Debug("logMemory"):
    # 	from guppy import hpy
    # 	import memory_logging

    # TODO put in processSpectra

    ps = ProcessSpectra(
        str(importDir),
        [str(x[0]) for x in listFiles],
        [str(x[0].split(os.sep)[-1]) for x in listFiles],
    )

    # some statistics
    nb_ms_scans = []
    nb_ms_peaks = []
    nb_msms_scans = []
    nb_msms_peaks = []

    # time
    starttime = time.perf_counter()

    # go recursively through the directory
    listPolarity = []
    dictBasePeakIntensity = {}
    progressCount = 0

    # the scan.dictSample variable is filled with
    # MSmass and MSMS classes. This means, the raw *.dta
    # and *.csv data is loaded into scan.dictSample.
    # After loading the cleaning algorithm is applied.
    if options["spectraFormat"] == "dta/csv" and isTaken:
        if listFiles != []:
            listFiles.sort()

            for i in listFiles:
                ret = add_DTASample(
                    scan,
                    i[0],
                    i[1],
                    MSmassrange=scan.options["MSmassrange"],
                    MSMSmassrange=scan.options["MSMSmassrange"],
                    importMSMS=importMSMS,
                    thresholdType=scan.options["MSthresholdType"],
                )

                listPolarity.append(ret[0])
                dictBasePeakIntensity[ret[2]] = ret[1]

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

        for i in listFiles:
            # progressCount += 1
            # if parent:
            # 	(cont, skip) = parent.debug.progressDialog.Update(progressCount)
            # 	if not cont:
            # 		print "Stopped by user."
            # 		parent.debug.progressDialog.Destroy()
            # 		return parent.CONST_THREAD_USER_ABORT

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

            elif (
                options["spectraFormat"] == "mzML"
            ):  # the new import routine, :-)
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
                    processSpectra=ps,
                )

            elif (
                options["spectraFormat"] == "raw"
            ):  # the new import routine, :-)
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
                    fileformat="raw",
                    processSpectra=ps,
                )

            dictBasePeakIntensity[ret[0]] = ret[1]

            if len(ret) > 2:
                nb_ms_scans.append(ret[2])
                nb_ms_peaks.append(ret[3])
                nb_msms_scans.append(ret[4])
                nb_msms_peaks.append(ret[5])

        if not len(list(dictBasePeakIntensity.keys())) > 0:
            raise LipidXException(
                "Something wrong with the calculation of the base peaks"
            )

    else:
        raise LipidXException("No valid option given.")

    # align the spectra with ProcessSpectra
    if not ps is None:
        ps.alignMSSpectra(
            options["MSresolution"].tolerance,
            options["MSresolutionDelta"],
            options["MSmassrange"][0],
        )

        ps.alignMSMS(options["selectionWindow"])
        # ps.mkSurveyEntries()

    reportout(
        "> {0:.<30s}{1:>11d}".format(
            "Avg. Nb. of MS scans", sum(nb_ms_scans) / len(nb_ms_scans)
        )
    )
    reportout(
        "> {0:.<30s}{1:>11d}".format(
            "Avg. Nb. of MS peaks", sum(nb_ms_peaks) / len(nb_ms_peaks)
        )
    )
    reportout(
        "> {0:.<30s}{1:>11d}".format(
            "Avg. Nb. of MS/MS scans", sum(nb_msms_scans) / len(nb_msms_scans)
        )
    )
    reportout(
        "> {0:.<30s}{1:>11d}".format(
            "Avg. Nb. of MS/MS peaks", sum(nb_msms_peaks) / len(nb_msms_peaks)
        )
    )

    loadingtime = time.perf_counter() - starttime
    reportout("%.2f sec. for reading the spectra" % loadingtime)

    # if Debug("logMemory"):
    # 	print "ML> spectra loaded and averaged:", memory_logging.pythonMemory()
    # 	print "MLh> spectra loaded and averaged: ", hpy().heap()

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

    # if parent:
    # 	if not parent.isRunning:
    # 		print "Stopped by user."
    # 		parent.debug.progressDialog.Destroy()
    # 		return parent.CONST_THREAD_USER_ABORT

    scan.listSamples.sort()

    if listPolarity == []:
        listPolarity = [-1, 1]
    else:
        listPolarity = unique(listPolarity)

    # recalibrate MS spectra
    if not scan.options.isEmpty("MScalibration"):
        recalibrateMS(scan, scan.options["MScalibration"])
    if not scan.options.isEmpty("MSMScalibration") and (
        scan.options["MSMScalibration"]
    ):
        recalibrateMSMS(scan, scan.options["MSMScalibration"])

    calibrationtime = time.perf_counter() - starttime - loadingtime
    reportout("%.2f sec. for calibrating the spectra" % calibrationtime)

    # align MS spectra
    print("Aligning MS spectra", alignmentMS)

    # if Debug("logMemory"):
    # 	print "ML> before alignment (MS):", memory_logging.pythonMemory()
    # 	print "MLh> before alignment (MS)", hpy().heap()

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
        )

    elif alignmentMS == "hierarchical":
        # experimental
        mkSurveyHierarchical(
            scan,
            "",
            numLoops=options["loopNr"],
            deltaRes=scan.options["MSresolutionDelta"],
            minocc=scan.options["MSminOccupation"],
        )

    elif alignmentMS == "heuristic":
        mkSurveyHeuristic(
            scan,
            "",
            numLoops=options["loopNr"],
            deltaRes=scan.options["MSresolutionDelta"],
            minocc=scan.options["MSminOccupation"],
        )

    progressCount += 1
    # if parent:
    # 	(cont, skip) = parent.debug.progressDialog.Update(progressCount)
    # 	if not cont:
    # 		print "Stopped by user."
    # 		parent.debug.progressDialog.Destroy()
    # 		return parent.CONST_THREAD_USER_ABORT

    reportout(
        "> {0:.<30s}{1:>11d}\n".format(
            "Nb. of MS peaks (after alg.)", len(scan.listSurveyEntry)
        )
    )

    # if Debug("logMemory"):
    # 	print "ML> after alignment (MS):", memory_logging.pythonMemory()
    # 	print "MLh> after alignment (MS):", hpy().heap()

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
                scan,
                listPolarity,
                numLoops=options["loopNr"],
                isPIS=options["pisSpectra"],
            )
        elif alignmentMSMS == "heuristic":
            mkMSMSEntriesHeuristic_new(
                scan,
                listPolarity,
                numLoops=options["loopNr"],
                isPIS=options["pisSpectra"],
            )

    alignmenttime = (
        time.perf_counter() - starttime - loadingtime - calibrationtime
    )
    reportout("%.2f sec. for aligning the spectra\n" % alignmenttime)

    for sample in scan.listSamples:
        if sample in scan.dictSamples:
            del scan.dictSamples[sample]
    del scan.dictSamples

    # if Debug("logMemory"):
    # 	print "ML> after alignment of MS/MS:", memory_logging.pythonMemory()
    # 	print "MLh> ", hpy().heap()

    progressCount += 1
    # if parent:
    # 	(cont, skip) = parent.debug.progressDialog.Update(progressCount)
    # 	if not cont:
    # 		print "Stopped by user."
    # 		parent.debug.progressDialog.Destroy()
    # 		return parent.CONST_THREAD_USER_ABORT

    # if not keepGoing:
    # 	print "Stopped by user."
    # 	parent.isRunning = False
    # 	return None

    scan.sortAndIndedice()
    for se in scan.listSurveyEntry:
        se.sortAndIndedice()

    print("Save output to %s." % output)
    saveSC(scan, output)

    reportout(
        "%.2f sec. for the whole import process"
        % (time.perf_counter() - starttime)
    )
    reportout("\n")

    if parent:
        # parent.debug.progressDialog.Destroy()
        return parent.CONST_THREAD_SUCCESSFUL


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

    # if Debug("logMemory"):
    # 	from guppy import hpy
    # 	import memory_logging

    # time
    starttime = time.perf_counter()

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
                        fileformat=options["spectraFormat"],
                    )

                dictBasePeakIntensity[ret[0]] = ret[1]
                # listSamples.append(ret[2])
                # dictSamples[ret[2]] = ret[3]

            if not len(list(dictBasePeakIntensity.keys())) > 0:
                raise LipidXException(
                    "Something wrong with the calculation of the base peaks"
                )

            loadingtime = time.perf_counter() - starttime
            reportout("%.2f sec. for reading the spectra" % loadingtime)

            # if Debug("logMemory"):
            # 	print "ML> spectra for one chunk loaded:", memory_logging.pythonMemory()
            # 	print "MLh> ", hpy().heap()

            if (
                not scan.options.isEmpty("precursorMassShift")
            ) and scan.options["precursorMassShift"]:
                if scan.options["precursorMassShift"] != 0:
                    print("Applying precursor mass shift")
                    scan.shiftPrecursors(scan.options["precursorMassShift"])

            if (
                not scan.options.isEmpty("precursorMassShiftOrbi")
            ) and scan.options["precursorMassShiftOrbi"]:
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
                lRecalTable = recalibrateMS(
                    scan, scan.options["MScalibration"]
                )
            if not scan.options.isEmpty("MSMScalibration") and (
                scan.options["MSMScalibration"]
            ):
                lRecalTable = recalibrateMSMS(
                    scan, scan.options["MSMScalibration"]
                )

            calibrationtime = time.perf_counter() - starttime - loadingtime
            reportout(
                "%.2f sec. for calibrating the spectra" % calibrationtime
            )

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
        print(
            "ML> before alignment of the chunks:",
            memory_logging.pythonMemory(),
        )
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
                                cl[chunk]
                                .content["surveyEntry"]
                                .dictIntensity[key]
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
                            raise LipidXException(
                                "Something wrong: samples overlap"
                            )
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

    alignmenttime = (
        time.perf_counter() - starttime - loadingtime - calibrationtime
    )
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

    reportout(
        "%.2f sec. for the whole import process"
        % (time.perf_counter() - starttime)
    )
    reportout("\n")

    if parent:
        # parent.debug.progressDialog.Destroy()
        return parent.CONST_THREAD_SUCCESSFUL


if __name__ == "__main__":
    pass
    # (options, scan, importDir, output) = lpdxImportCLI()
