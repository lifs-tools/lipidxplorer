import os, re
import configparser
from lx.options import Options
from lx.exceptions import LipidXException
from lx.mfql.runtimeStatic import TypeTolerance
from copy import copy, deepcopy


class Project(Options):
    """The project class handels LX project values, i.e. all
	values which are set in the GUI. They are stored in an *.ini
	file with ConfigParser."""

    def __init__(self, options=None):
        """ All options are defined here. There are two dictionaries:
		options and options_formatted. The options dictionary stores the
		orginal string values while the options_formatted dictionary
		stores the values in the needed format."""

        Options.__init__(self, options=options)

        # config Parser for reading/writing *.ini files
        self.confParse = None

        # fill 'self.options' if 'options' is given
        if not options is None:
            for key in list(self.options.keys()):
                self.options[key] = options[key]

    def initialize(self, projectFilePath):
        """Initialize the ini file."""

        if not os.path.exists(projectFilePath):
            raise LipidXException("File %s does not exist." % projectFilePath)
            return None

        self.projectFilePath = projectFilePath
        self.confParse = configparser.ConfigParser()
        self.confParse.read(self.projectFilePath)

    def load(self, path):
        """load and open a project file"""

        ### check version and downward compatibility ###

        if not os.path.exists(path):
            raise LipidXException("File %s does not exist." % path)
            return None
        self.confParse = configparser.ConfigParser()
        self.confParse.read(path)

        # the new MasterScan option (>1.2.4)
        if self.confParse.has_option(self.sectionP, "masterScan"):
            ms = self.confParse.get(self.sectionP, "masterScan")
            self.confParse.remove_option(self.sectionP, "masterScan")
            self.confParse.set(self.sectionP, "masterScanImport", ms)
            self.confParse.set(self.sectionP, "masterScanRun", ms)

        self.confParse.write(open(path, "w+"))

        ### load and init the *.ini file ###

        self.initialize(path)

        ### the options ###

        # fill the option dictionary
        for opt in list(self.options.keys()):
            try:
                self.options[opt] = self.confParse.get(self.sectionP, opt)
            except configparser.NoOptionError:
                print("Option '%s' is not contained in the project file" % opt)

        # method from the Options superclass
        self.importSettingsSet = self.allImportSettingsSet()

        # check and read the options from self.options
        self.formatOptions()

        # add the master scan file path
        self.options["dumpMasterScanFile"] = (
            os.path.splitext(self.options["masterScanRun"])[0] + "-dump.csv"
        )
        self.options_formatted["dumpMasterScanFile"] = (
            os.path.splitext(self.options["masterScanRun"])[0] + "-dump.csv"
        )

        ### the query section ###

        # fill the mfql files with (key, value) pairs
        mfql = self.confParse.items(self.sectionQ)

        # tranform (key, value) pairs in dictionary
        dictMfql = {}
        for key, value in mfql:
            if key in dictMfql:
                dictMfql.append(value)
            else:
                dictMfql[key] = value

        # read the mfql scripts with the right names
        for m in list(dictMfql.keys()):
            r = re.match("(.*)-name", m)
            if r:
                self.mfql[dictMfql[m]] = dictMfql[r.group(1)]
                del dictMfql[m]
                del dictMfql[r.group(1)]

        for m in list(dictMfql.keys()):
            self.mfql[m] = dictMfql[m]

    def writeOptionsToIni(self):

        self.testConfiguration()

        # write all settings
        self.confParse.set(configuration, "selectionWindow", o["selectionWindow"])
        self.confParse.set(
            configuration,
            "timerange",
            "(%f,%f)" % (o["timerange"][0], o["timerange"][1]),
        )
        self.confParse.set(configuration, "selectionWindow", o["selectionWindow"])
        str = ""
        for m in o["MScalibration"]:
            str += "%.4f," % m
        self.confParse.set(configuration, "MScalibration", str)
        str = ""
        for m in o["MSMScalibration"]:
            str += "%.4f," % m
        self.confParse.set(configuration, "MSMScalibration", str)
        self.confParse.set(
            configuration,
            "MSmassrange",
            "(%f,%f)" % (o["MSmassrange"][0], o["MSmassrange"][1]),
        )
        self.confParse.set(
            configuration,
            "MSMSmassrange",
            "(%f,%f)" % (o["MSMSmassrange"][0], o["MSMSmassrange"][1]),
        )
        self.confParse.set(configuration, "MSresolution", o["MSresolution"].tolerance)
        self.confParse.set(
            configuration, "MSMSresolution", o["MSMSresolution"].tolerance
        )
        self.confParse.set(configuration, "MStolerance", o["MStolerance"])
        self.confParse.set(configuration, "MSMStolerance", o["MSMStolerance"])
        self.confParse.set(configuration, "MSthreshold", str(o["MSthreshold"]))
        self.confParse.set(configuration, "MSMSthreshold", str(o["MSMSthreshold"]))
        self.confParse.set(
            configuration, "MSresolutionDelta", str(o["MSresolutionDelta"])
        )
        self.confParse.set(
            configuration, "MSMSresolutionDelta", str(o["MSMSresolutionDelta"])
        )
        self.confParse.set(configuration, "MSminOccupation", o["MSminOccupation"])
        self.confParse.set(configuration, "MSMSminOccupation", o["MSMSminOccupation"])
        self.confParse.set(configuration, "precursorMassShift", o["precursorMassShift"])
        self.confParse.set(
            configuration, "precursorMassShiftOrbi", o["precursorMassShiftOrbi"]
        )
        self.confParse.set(configuration, "alignmentMethodMS", o["alignmentMethodMS"])
        self.confParse.set(
            configuration, "alignmentMethodMSMS", o["alignmentMethodMSMS"]
        )
        self.confParse.set(
            configuration, "scanAveragingMethod", o["scanAveragingMethod"]
        )
        self.confParse.set(configuration, "importMSMS", o["importMSMS"])

        self.confParse.write(open(self.projectFilePath, "w+"))


class GUIProject(Project):
    """Load the project file into the GUI"""

    def formatOptions(self):
        """Formats the some settings of the current configuration to fit in the GUI."""

        o = self.options

        # convert Boolean values
        for option in list(o.keys()):
            if o[option] == "True":
                self.options_formatted[option] = True
            if o[option] == "False":
                self.options_formatted[option] = False

        if not o["timerange"] is None:
            self.options_formatted["timerange"] = (
                o["timerange"].split(",")[0].strip("() "),
                o["timerange"].split(",")[1].strip("() "),
            )

        if len(o["MScalibration"]) > 0:
            self.options_formatted["MScalibration"] = o["MScalibration"].split(",")
        if len(o["MSMScalibration"]) > 0:
            self.options_formatted["MSMScalibration"] = o["MSMScalibration"].split(",")

        if not o["MSmassrange"] is None:
            self.options_formatted["MSmassrange"] = (
                (o["MSmassrange"].split(",")[0].strip("() ")),
                (o["MSmassrange"].split(",")[1].strip("() ")),
            )
        if not o["MSMSmassrange"] is None:
            self.options_formatted["MSMSmassrange"] = (
                (o["MSMSmassrange"].split(",")[0].strip("() ")),
                (o["MSMSmassrange"].split(",")[1].strip("() ")),
            )

        if not o["MSresolution"] is None:
            self.options_formatted["MSresolution"] = o["MSresolution"]
        if not o["MSMSresolution"] is None:
            self.options_formatted["MSMSresolution"] = o["MSMSresolution"]

        if not self.options["MStolerance"] is None:
            m = re.match("(\d+|\d+\.\d+)(\s)*(ppm|Da)", self.options["MStolerance"])
            if m is None:
                if not o["MStoleranceType"] is None and not o["MStoleranceType"] == "":
                    m = re.match("(\d+|\d+\.\d+)", o["MStolerance"])
                    if not m is None:
                        self.options_formatted["MStolerance"] = o["MStolerance"]
            else:
                self.options_formatted["MStolerance"] = o["MStolerance"]
        if not self.options["MSMStolerance"] is None:
            m = re.match("(\d+|\d+\.\d+)(\s)*(ppm|Da)", self.options["MSMStolerance"])
            if m is None:
                if (
                    not o["MSMStoleranceType"] is None
                    and not o["MSMStoleranceType"] == ""
                ):
                    m = re.match("(\d+|\d+\.\d+)", o["MSMStolerance"])
                    if not m is None:
                        self.options_formatted["MSMStolerance"] = o["MSMStolerance"]
            else:
                self.options_formatted["MSMStolerance"] = o["MSMStolerance"]

        # this option is not editable
        self.options_formatted["loopNr"] = 3

        # copy the rest of the string based options to the internal options
        for opt in list(self.options.keys()):
            if not opt in list(self.options_formatted.keys()):
                self.options_formatted[opt] = self.options[opt]
