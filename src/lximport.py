# important
#!/usr/bin/python

import os
import sys
import re
from optparse import OptionParser
import configparser

from lx.lxMain import startImport

from lx.exceptions import LipidXException
from lx.project import Project
from lx.options import Options, optionsDict

# import logging

### logging levels ###
# DEBUG - debug
# INFO - info for user
# WARNING - warning for user
# ERROR - error, when exception araise
# CRITICAL - when program exits

# logging.basicConfig(level=logging.DEBUG,
#                    format='%(asctime)s %(levelname)s %(funcName)s(): %(message)s',
# 					datefmt = '%H:%M:%S',
#                    filename='lpdxlog.txt',
#                    filemode='a')

# log = logging.getLogger("lpdxUITypes.py")

# define a Handler which writes INFO messages or higher to the sys.stderr
# console = logging.StreamHandler()
# console.setLevel(logging.INFO)
# set a format which is simpler for console use
# formatter = logging.Formatter('(log) %(name)-12s: %(message)s')
# tell the handler to use this format
# console.setFormatter(formatter)
# add the handler to the root logger
# log.addHandler(console)


def lpdxImportCLI(projpath=None):

    ######################################################
    ###              collect the options               ###

    confParse = configparser.ConfigParser()

    optParser = OptionParser(usage="\nlpdxCLI.py [options] [experiment/] [output.sc]\n")

    # import part
    optParser.add_option(
        "-p", "--prj", dest="prj", help="path of the project file", metavar="FILE"
    )
    # optParser.add_option("-i", "--ini", dest="ini",
    # 				 help="path of the *.ini FILE if different from './lpdxImportSettings.ini'", metavar = "FILE")
    optParser.add_option(
        "-s", "--setting", dest="setting", help="section of a setting from *.ini file"
    )

    optParser.add_option(
        "-m",
        "--masterscan",
        dest="masterScan",
        help="The name of the masterscan which should be output.",
    )

    optParser.add_option(
        "-i",
        "--importdir",
        dest="importDir",
        help="the directory with the samples which should be imported.",
    )

    optParser.add_option(
        "--pis",
        dest="pisSpectra",
        action="store_true",
        default=False,
        help="switches to precursor ion scan (PIS) mode.",
    )
    # optParser.add_option("-g", "--groups", dest="groups", default = "",
    # 				 help="select a group file. Without, no groups will be defined.")

    # import settings
    optParser.add_option(
        "-t",
        "--timerange",
        dest="timerange",
        type="string",
        help="overwrites/specifies the timerange of retention time \
						in sec with '(start, end)'",
        metavar="ARG",
    )
    optParser.add_option(
        "--MSmassrange",
        dest="MSmassrange",
        type="string",
        help="overwrites/specifies the range of masses with '(start, end)'",
        metavar="ARG",
    )

    optParser.add_option(
        "--MSMSmassrange",
        dest="MSMSmassrange",
        type="string",
        help="overwrites/specifies the range of masses with '(start, end)'",
        metavar="ARG",
    )
    optParser.add_option(
        "--MSresolutionDelta",
        dest="MSresolutionDelta",
        type="string",
        help="overwrites/specifies the change of resolution per 1da in MS",
        metavar="ARG",
    )

    optParser.add_option(
        "--MSMSresolutionDelta",
        dest="MSMSresolutionDelta",
        type="string",
        help="overwrites/specifies the change of resolution per 1da in MS/MS",
        metavar="ARG",
    )

    optParser.add_option(
        "--MSminOccupation",
        dest="MSminOccupation",
        type="string",
        help="defines the percentage MS occupation of masses through all samples ",
        metavar="ARG",
    )

    optParser.add_option(
        "--MSMSminOccupation",
        dest="MSMSminOccupation",
        type="string",
        help="defines the percentage MS occupation of masses through all samples ",
        metavar="ARG",
    )

    optParser.add_option(
        "--MStolerance",
        dest="MStolerance",
        help="overwrites/specifies 'MStolerance' of the *.ini file",
        metavar="ARG",
    )

    optParser.add_option(
        "--MSMStolerance",
        dest="MSMStolerance",
        help="overwrites/specifies 'MSMStolerance' of the *.ini file",
        metavar="ARG",
    )

    optParser.add_option(
        "--MStoleranceType",
        dest="MStoleranceType",
        help="overwrites/specifies 'MStoleranceType' of the *.ini file",
        metavar="ARG",
    )

    optParser.add_option(
        "--MSMStoleranceType",
        dest="MSMStoleranceType",
        help="overwrites/specifies 'MSMStoleranceType' of the *.ini file",
        metavar="ARG",
    )

    optParser.add_option(
        "--MSresolution",
        dest="MSresolution",
        help="overwrites/specifies 'MSresolution' of the *.ini file",
        metavar="ARG",
    )

    optParser.add_option(
        "--MSMSresolution",
        dest="MSMSresolution",
        help="overwrites/specifies 'MSMSresolution' of the *.ini file",
        metavar="ARG",
    )

    optParser.add_option(
        "--MSthreshold",
        dest="MSthreshold",
        help="overwrites/specifies 'MSthreshold' of the *.ini file",
        metavar="ARG",
    )

    optParser.add_option(
        "--MSMSthreshold",
        dest="MSMSthreshold",
        help="overwrites/specifies 'MSMSthreshold' of the *.ini file",
        metavar="ARG",
    )

    optParser.add_option(
        "--MSthresholdType",
        dest="MSthresholdType",
        help="overwrites/specifies 'MSthresholdType' of the *.ini file",
        metavar="ARG",
    )

    optParser.add_option(
        "--MSMSthresholdType",
        dest="MSMSthresholdType",
        help="overwrites/specifies 'MSMSthreshold' of the *.ini file",
        metavar="ARG",
    )

    optParser.add_option(
        "--selectionWindow",
        dest="selectionWindow",
        help="overwrites/specifies 'selectionWindow' of the *.ini file",
        metavar="ARG",
    )

    optParser.add_option(
        "--MScalibration",
        dest="MScalibration",
        help="overwrites/specifies 'MScalibration' of the *.ini file",
        metavar="ARG",
    )

    optParser.add_option(
        "--MSMScalibration",
        dest="MSMScalibration",
        help="overwrites/specifies 'MSMScalibration' of the *.ini file",
        metavar="ARG",
    )

    optParser.add_option(
        "--precursorMassShift",
        dest="precursorMassShift",
        help="overwrites/specifies 'precursorMassShift' of the *.ini file",
        metavar="ARG",
    )

    optParser.add_option(
        "--PMO",
        dest="precursorMassShiftOrbi",
        help="overwrites/specifies 'precursorMassShiftOrbi' of the *.ini file",
        metavar="ARG",
    )

    optParser.add_option(
        "--alignmentMethodMS",
        dest="alignmentMethodMS",
        default="linear",
        help="linear (default) or heuristic",
        metavar="ARG",
    )

    optParser.add_option(
        "--alignmentMethodMSMS",
        dest="alignmentMethodMSMS",
        default="linear",
        help="linear (default) or heuristic",
        metavar="ARG",
    )

    optParser.add_option(
        "--fileType",
        dest="spectraFormat",
        type="string",
        help="Choose the spectra file type",
    )

    optParser.add_option(
        "--prefix",
        dest="settingsPrefix",
        action="store_true",
        default=False,
        help="have the settings as a prefix",
    )

    (cliOptions, args) = optParser.parse_args()

    if cliOptions.prj is None and projpath is None:
        if len(args) < 2:
            raise LipidXException("Wrong number of arguments")

    options = optionsDict()
    # the order of the following if-statements integrates prioraties

    project = Project()

    # if the settings are comming from the project file
    if projpath is not None:
        project.load(projpath)
        project.testOptions()
    elif not cliOptions.prj is None:
        # project = Project()
        project.load(cliOptions.prj)
        project.testOptions()
        # options = project.getOptions()
        # project.options['importDir'] = args[0]
        # project.options['masterScan'] = args[1]

    else:
        project.options["setting"] = "command line"
        project.options["loopNr"] = 3
        project.options["alignmentMethodMS"] = "linear"
        project.options["alignmentMethodMSMS"] = "linear"
        project.options["scanAveragingMethod"] = "linear"

        project.options["importDir"] = args[0]
        project.options["masterScan"] = args[1]
        project.options["dumpMasterScanFileImport"] = (
            os.path.splitext(args[1])[0] + "-dump.csv"
        )
        project.options["importMSMS"] = True
        project.options["mzXML"] = True

    # if the settings are used from the *.ini file
    # if not cliOptions.ini is None:
    # 	opts = Options()
    # 	opts.initialize("%s" % cliOptions.ini)
    # 	opts.setCurrentConfiguration(cliOptions.setting)
    # 	opts.readConfiguration()
    # 	for opt in opts.options.keys():
    # 		project.options[opt] = opts.options[opt]
    # else:
    project.options["ini"] = "None"

    # the settings come only from the command line (they overwrite existing options)
    if projpath is not None:
        project.options["masterScan"] = project.options["masterScanImport"]
    elif cliOptions.masterScan is None:
        try:
            project.options["masterScan"] = args[1]  # cliOptions.masterScanFile
        except IndexError:
            print("ERROR: The masterscan file was not specified. Use the ", end=" ")
            print("option -m")

    if projpath is not None:
        pass
    else:  # use command line options
        for opt in list(cliOptions.__dict__.keys()):
            if not cliOptions.__dict__[opt] is None:
                project.options[opt] = cliOptions.__dict__[opt]

    project.formatOptions()

    ###              collect the options               ###
    ######################################################

    options = project.getOptions()
    # print the options
    for k in options:
        try:
            print("{0:24} : {1:12}".format(k, str(options[k])))
        except:
            print("{0:24} : None".format(k))
    if projpath is not None:
        pass
    elif "masterScan" in list(cliOptions.__dict__.keys()):
        options["masterScan"] = cliOptions.__dict__["masterScan"]

    ### start import ###
    startImport(options=options, lipidxplorer=True)


if __name__ == "__main__":
    lpdxImportCLI()
    # (options, scan, importDir, output) = lpdxImportCLI()
