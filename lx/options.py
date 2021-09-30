import os
import re
import traceback
from lx.exceptions import LipidXException
from lx.mfql.runtimeStatic import TypeTolerance
from lx.tools import odict
from collections import MutableMapping as DictMixin


class optionsDict(DictMixin):
    """A special type of dictionary which handels its own exceptions."""

    def __init__(self):
        self._data = {}

    def __setitem__(self, key, value):
        self._data[key] = value

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        for i in self._data:
            yield i

    def __getitem__(self, key):
        if self._isEmpty(self._data[key]):
            for line in traceback.format_stack()[:-1]:
                print(line.strip())
            raise LipidXException("The key '%s' is not given" % key)
        return self._data[key]

    def __delitem__(self, key):
        del self._data[key]

    def __repr__(self):
        result = []
        for key in list(self._data.keys()):
            result.append("%s: %s" % (repr(key), repr(self._data[key])))
        return "".join(["{", ", ".join(result), "}"])

    def _isEmpty(self, option):
        return (option is None) or (option == "")

    def isEmpty(self, option):
        return (
            (self._data[option] is None)
            or (self._data[option] == "")
            or (self._data[option] == [])
        )

    def keys(self):
        return list(self._data.keys())

    def has_key(self, key):
        return key in self._data

    def copy(self):
        copyDict = optionsDict()
        copyDict._data = self._data.copy()
        return copyDict

    def sort(self, *args, **kwargs):
        self._data.keys.sort(*args, **kwargs)

    def getOrdinary(self):
        ordinary = {}
        for key in list(self._data.keys()):
            ordinary[key] = self._data[key]
        return ordinary


class Options:
    """The option class handels all nesseccary LX values."""

    # specify the options which are only used for the import
    importOptions = [
        "selectionWindow",
        "timerange",
        "MScalibration",
        "MSMScalibration",
        "MSmassrange",
        "MSMSmassrange",
        "MSresolution",
        "MSMSresolution",
        "MSthreshold",
        "MSMSthreshold",
        "MSthresholdType",
        "MSMSthresholdType",
        "MStolerance",
        "MSMStolerance",
        "MStoleranceType",
        "MSMStoleranceType",
        "MSresolutionDelta",
        "MSMSresolutionDelta",
        "MSminOccupation",
        "MSMSminOccupation",
        "precursorMassShift",
        "precursorMassShiftOrbi",
    ]

    def __init__(self, options=None):
        """All options are defined here. There are two dictionaries:
        options and options_formatted. The options dictionary stores the
        orginal string values while the options_formatted dictionary
        stores the values in the needed format."""

        # these are the two sections of a project file
        self.sectionP = "project"
        self.sectionQ = "mfql"

        self.projectFilePath = None
        self.setting = ""
        self.options = odict()
        self.mfql = odict()
        self.options["importDir"] = None
        self.options["masterScanRun"] = None
        self.options["masterScanImport"] = None
        self.options["importMSMS"] = None
        self.options["pisSpectra"] = None
        self.options["dataType"] = None
        self.options["ini"] = None
        self.options["setting"] = None
        self.options["selectionWindow"] = None
        self.options["timerange"] = None
        self.options["MScalibration"] = None
        self.options["MSMScalibration"] = None
        self.options["MSmassrange"] = None
        self.options["MSMSmassrange"] = None
        self.options["MStolerance"] = None
        self.options["MSMStolerance"] = None
        self.options["MStoleranceType"] = None
        self.options["MSMStoleranceType"] = None
        self.options["MSresolution"] = None
        self.options["MSMSresolution"] = None
        self.options["MSresolutionDelta"] = None
        self.options["MSMSresolutionDelta"] = None
        self.options["MSthreshold"] = None
        self.options["MSMSthreshold"] = None
        self.options["MSthresholdType"] = None
        self.options["MSMSthresholdType"] = None
        self.options["MSminOccupation"] = None
        self.options["MSMSminOccupation"] = None
        self.options["precursorMassShift"] = None
        self.options["precursorMassShiftOrbi"] = None  # aka PMO
        self.options["alignmentMethodMS"] = None
        self.options["alignmentMethodMSMS"] = None
        self.options["scanAveragingMethod"] = None
        self.options["scanAveragingMethod"] = None
        self.options[
            "isotopicCorrection_MSMS"
        ] = None  # here starts the Set debugging Options from the Debug menu
        self.options["removeIsotopes"] = None
        self.options["isotopesInMasterScan"] = None
        self.options["monoisotopicCorrection"] = None
        self.options["relativeIntensity"] = None
        self.options["logMemory"] = None
        self.options[
            "intensityCorrection"
        ] = None  # here starts the output options menu
        self.options["intensityCorrectionPrecursor"] = None
        self.options["intensityCorrectionFragment"] = None
        self.options["masterScanInSQL"] = None
        self.options["sumFattyAcids"] = None
        self.options["resultFile"] = None
        self.options["optionalMStolerance"] = None
        self.options["optionalMSMStolerance"] = None
        self.options["optionalMStoleranceType"] = None
        self.options["optionalMSMStoleranceType"] = None
        self.options["optionalMSthreshold"] = None
        self.options["optionalMSMSthreshold"] = None
        self.options["optionalMSthresholdType"] = None
        self.options["optionalMSMSthresholdType"] = None
        self.options["isotopicCorrectionMS"] = None
        self.options["isotopicCorrectionMSMS"] = None
        self.options["complementMasterScan"] = None
        self.options["complementMasterScanFile"] = None
        self.options["noHead"] = None
        self.options["compress"] = None
        self.options["tabLimited"] = None
        self.options["dumpMasterScan"] = None
        self.options["dumpMasterScanFile"] = None
        self.options["statistics"] = None
        self.options["noPermutations"] = None
        self.options[
            "mzXML"
        ] = None  # option key used in lpdxImport.py, substituted by 'dataType'
        self.options[
            "spectraFormat"
        ] = None  # option key used in lpdxImport.py, substituted by 'dataType'
        self.options[
            "settingsPrefix"
        ] = None  # option key used in lpdxImport.py, substituted by 'dataType'
        # self.options['vendorsAveraging'] = None # True/False for switching to Thermo's averaging
        self.options[
            "MSfilter"
        ] = None  # minimum filter threshold for repeated ions in MS1, between 0 and 1
        self.options[
            "MSMSfilter"
        ] = None  # minimum filter threshold for repeated ions in MS2, between 0 and 1

        # for this setting exists no possibility to change it ...
        # however...
        self.options["loopNr"] = 3

        # the "formatted options" contain the options in the correct data format
        # the method 'readOptions' fills this dictionary
        self.options_formatted = optionsDict()

        # fill 'self.options' if 'options' is given
        if not options is None:
            for key in list(self.options.keys()):
                self.options[key] = options[key]

    def __repr__(self):

        str = "\n"
        for key in sorted(self.options.keys()):
            str += "{0:24s} : {1:10s}\n".format(key, repr(self.options[key]))

        return str

    def isEmpty(self, option):

        if isinstance(option, type("")):
            if option in list(self.options.keys()):
                option = self.options[option]

        if isinstance(option, type([])):
            if len(option) == 0:
                return True
            else:
                for e in option:
                    if not ((option is None) or (option == "")):
                        return False
                return True

        return (
            (option is None) or (option == "") or (option == "()") or (option == "(,)")
        )

    def allImportSettingsSet(self):

        l = []
        for s in self.importOptions:
            if self.options[s] == "" or self.options[s] == "0" or not self.options[s]:
                l.append(s)
        return l

    def testOptionsRun(self):

        if not self.isEmpty("optionalMStolerance"):
            m = re.match(
                "(\d+|\d+\.\d+)(\s)*(ppm|Da)", self.options["optionalMStolerance"]
            )
            if m is None:
                if (
                    not self.options["optionalMStoleranceType"] is None
                    and not self.options["optionalMStoleranceType"] == ""
                ):
                    m = re.match("(\d+|\d+\.\d+)", self.options["optionalMStolerance"])
                    if not m is None:
                        if float(m.group(1)) < 0.0:
                            raise LipidXException(
                                "The tolerance value for MS should be >= 0"
                            )
                    else:
                        raise LipidXException(
                            "The entry for the MS tolerance is corrupt."
                        )
                else:
                    raise LipidXException(
                        "The entry for the MS tolerance is corrupt or the type is missing."
                    )
            else:
                if float(m.group(1)) < 0.0:
                    raise LipidXException("The tolerance value for MS should be >= 0")

        if not self.isEmpty("optionalMSMStolerance"):
            m = re.match(
                "(\d+|\d+\.\d+)(\s)*(ppm|Da)", self.options["optionalMSMStolerance"]
            )
            if m is None:
                if (
                    not self.options["optionalMSMStoleranceType"] is None
                    and not self.options["optionalMSMStoleranceType"] == ""
                ):
                    m = re.match(
                        "(\d+|\d+\.\d+)", self.options["optionalMSMStolerance"]
                    )
                    if not m is None:
                        if float(m.group(1)) < 0.0:
                            raise LipidXException(
                                "The tolerance value for MS/MS should be >= 0"
                            )
                    else:
                        raise LipidXException(
                            "The entry for the MS/MS tolerance is corrupt."
                        )
                else:
                    raise LipidXException(
                        "The entry for the MS/MS tolerance is corrupt or the type is missing."
                    )
            else:
                if float(m.group(1)) < 0.0:
                    raise LipidXException(
                        "The tolerance value for MS/MS should be >= 0"
                    )

        self.testOptions()

    def testOptions(self):
        """Test the settings of the current configuration for correctness."""

        if not self.isEmpty("selectionWindow"):
            pass

        if not self.isEmpty("timerange"):
            timerange = (
                float(self.options["timerange"].split(",")[0].strip("() ")),
                float(self.options["timerange"].split(",")[1].strip("() ")),
            )
            if timerange[0] < 0 or timerange[1] < 0:
                raise LipidXException("Time range should be >= 0")
            if not timerange[0] <= timerange[1]:
                raise LipidXException(
                    "Second value of the time range is smaller then the first, which makes no sense ..."
                )

        if not self.isEmpty("MScalibration"):
            for mass in self.options["MScalibration"].split(","):
                if float(mass) < 0:
                    raise LipidXException(
                        "The m/z value %s in the MS calibriation list is negative."
                        % mass
                    )
        if not self.isEmpty("MSMScalibration"):
            for mass in self.options["MSMScalibration"].split(","):
                if float(mass) < 0:
                    raise LipidXException(
                        "The m/z value %s in the MS/MS calibriation list is negative."
                        % mass
                    )

        if not self.isEmpty("MSmassrange"):
            MSmassrange = (
                float(self.options["MSmassrange"].split(",")[0].strip("() ")),
                float(self.options["MSmassrange"].split(",")[1].strip("() ")),
            )
            if MSmassrange[0] < 0 or MSmassrange[1] < 0:
                raise LipidXException("M/Z range for MS should be >= 0")
            if not MSmassrange[0] <= MSmassrange[1]:
                raise LipidXException(
                    "Second value of the m/z range for MS is smaller then the first, which makes no sense ..."
                )

        if not self.isEmpty("MSMSmassrange"):
            MSMSmassrange = (
                float(self.options["MSMSmassrange"].split(",")[0].strip("() ")),
                float(self.options["MSMSmassrange"].split(",")[1].strip("() ")),
            )
            if MSMSmassrange[0] < 0 or MSMSmassrange[1] < 0:
                raise LipidXException("M/Z range for MS/MS should be >= 0")
            if not MSmassrange[0] <= MSmassrange[1]:
                raise LipidXException(
                    "Second value of the m/z range for MS/MS is smaller then first, which makes no sense ..."
                )

        # actually, there should not be a MSaccuracy setting any more
        # if not self.options['MSaccuracy'] >= 0:
        # 	raise LipidXException("The accuracy setting for MS should be >= 0")
        # if not self.options['MSMSaccuracy'] >= 0:
        # 	raise LipidXException("The accuracy setting for MS/MS should be >= 0")

        if not self.isEmpty("MStolerance"):
            m = re.match("(\d+|\d+\.\d+)(\s)*(ppm|Da)", self.options["MStolerance"])
            if m is None:
                if (
                    not self.options["MStoleranceType"] is None
                    and not self.options["MStoleranceType"] == ""
                ):
                    m = re.match("(\d+|\d+\.\d+)", self.options["MStolerance"])
                    if not m is None:
                        if float(m.group(1)) < 0.0:
                            raise LipidXException(
                                "The tolerance value for MS should be >= 0"
                            )
                    else:
                        raise LipidXException(
                            "The entry for the MS tolerance is corrupt."
                        )
                else:
                    raise LipidXException(
                        "The entry for the MS tolerance is corrupt or 'MStoleranceType' is missing."
                    )
            else:
                if float(m.group(1)) < 0.0:
                    raise LipidXException("The tolerance value for MS should be >= 0")

        if not self.isEmpty("MSMStolerance"):
            m = re.match("(\d+|\d+\.\d+)(\s)*(ppm|Da)", self.options["MSMStolerance"])
            if m is None:
                if (
                    not self.options["MSMStoleranceType"] is None
                    and not self.options["MSMStoleranceType"] == ""
                ):
                    m = re.match("(\d+|\d+\.\d+)", self.options["MSMStolerance"])
                    if not m is None:
                        if float(m.group(1)) < 0.0:
                            raise LipidXException(
                                "The tolerance value for MS/MS should be >= 0"
                            )
                    else:
                        raise LipidXException(
                            "The entry for the MS/MS tolerance is corrupt."
                        )
                else:
                    raise LipidXException(
                        "The entry for the MS/MS tolerance is corrupt or 'MStoleranceType' is missing."
                    )
            else:
                if float(m.group(1)) < 0.0:
                    raise LipidXException(
                        "The tolerance value for MS/MS should be >= 0"
                    )

        if not self.isEmpty("MSthreshold"):
            if not float(self.options["MSthreshold"]) >= 0:
                raise LipidXException("The threshold setting for MS should be >= 0")
        if not self.isEmpty("MSMSthreshold"):
            if not float(self.options["MSMSthreshold"]) >= 0:
                raise LipidXException("The threshold setting for MS/MS should be >= 0")

        if not self.isEmpty("MSminOccupation"):
            if (
                not float(self.options["MSminOccupation"]) >= 0
                and not float(self.options["MSminOccupation"]) <= 1
            ):
                raise LipidXException("Min occupation setting for MS should be 0 >= 1.")
        if not self.isEmpty("MSMSminOccupation"):
            if (
                not float(self.options["MSMSminOccupation"]) >= 0
                and not float(self.options["MSMSminOccupation"]) <= 1
            ):
                raise LipidXException(
                    "Min occupation setting for MS/MS should be 0 >= 1."
                )

        if not self.isEmpty("MSresolutionDelta"):
            if (
                not float(self.options["MSresolutionDelta"]) >= 0
                and not float(self.options["MSresolutionDelta"]) <= 1
            ):
                raise LipidXException(
                    "The resolution gradian setting for MS should be 0 >= 1."
                )
        if not self.isEmpty("MSMSresolutionDelta"):
            if (
                not float(self.options["MSMSresolutionDelta"]) >= 0
                and not float(self.options["MSMSminOccupation"]) <= 1
            ):
                raise LipidXException(
                    "Min occupation setting for MS/MS should be 0 >= 1."
                )

        if not self.isEmpty("alignmentMethodMS"):
            if not self.options["alignmentMethodMS"] in ["linear", "calctol"]:
                raise LipidXException("The alignment method for MS is not set properly")
        if not self.isEmpty("alignmentMethodMSMS"):
            if not self.options["alignmentMethodMSMS"] in ["linear", "calctol"]:
                raise LipidXException(
                    "The alignment method for MS/MS is not set properly"
                )
        if (
            not self.options["scanAveragingMethod"] is None
            and not self.options["scanAveragingMethod"] == ""
        ):
            if not self.options["scanAveragingMethod"] in ["linear", "calctol"]:
                raise LipidXException(
                    "The alignment method for the scan averaging is not set properly"
                )

        if not self.isEmpty("MSresolution"):
            if (
                self.options["MSresolution"]
                != "auto"  # auto will set optoins to use calctol
                and not int(self.options["MSresolution"]) >= 0
            ):  # auto will set optoins to use calctol
                raise LipidXException(
                    "The MS resolution must be > 0 or auto, 0 will call auto resolution"
                )
        if not self.isEmpty("MSMSresolution"):
            if not int(self.options["MSMSresolution"]) > 0:
                raise LipidXException("The MS/MS resolution must not be < 0")

        if not self.isEmpty("importMSMS"):
            if not self.options["importMSMS"] in ["True", "False", True, False]:
                raise LipidXException("The 'importMSMS' option has no proper values")

        if not self.isEmpty("MSthresholdType"):
            pass
        if not self.isEmpty("MSMSthresholdType"):
            pass

        if not self.isEmpty("precursorMassShift"):
            pass

        if not self.isEmpty("precursorMassShiftOrbi"):
            pass

        return True

    def formatOptions(self):
        """Reads and formats the settings of the current configuration for correctness."""

        floating_point_m = re.compile("[+-]?[0-9]*\.?[0-9]+")

        o = self.options

        for option in list(o.keys()):
            if not option in ["MScalibration", "MSMScalibration"]:
                try:
                    if floating_point_m.match(o[option]):
                        self.options_formatted[option] = float(o[option])
                except:
                    pass

        # convert Boolean values
        for option in list(o.keys()):
            if o[option] == "True":
                self.options_formatted[option] = True
            if o[option] == "False":
                self.options_formatted[option] = False

        if not self.isEmpty("timerange"):
            self.options_formatted["timerange"] = (
                float(o["timerange"].split(",")[0].strip("() ")),
                float(o["timerange"].split(",")[1].strip("() ")),
            )

        if not self.isEmpty("MScalibration") and len(o["MScalibration"]) > 0:
            self.options_formatted["MScalibration"] = [
                float(x) for x in o["MScalibration"].split(",")
            ]
        if not self.isEmpty("MSMScalibration") and len(o["MSMScalibration"]) > 0:
            self.options_formatted["MSMScalibration"] = [
                float(x) for x in o["MSMScalibration"].split(",")
            ]

        if not self.isEmpty("MSresolutionDelta"):
            self.options_formatted["MSresolutionDelta"] = float(o["MSresolutionDelta"])
        if not self.isEmpty("MSMSresolutionDelta"):
            self.options_formatted["MSMSresolutionDelta"] = float(
                o["MSMSresolutionDelta"]
            )

        if not self.isEmpty("MSthreshold"):
            self.options_formatted["MSthreshold"] = float(o["MSthreshold"])
        if not self.isEmpty("MSMSthreshold"):
            self.options_formatted["MSMSthreshold"] = float(o["MSMSthreshold"])

        # if occupation threshold is not given, we set a standard of 0.0
        if not self.isEmpty("MSminOccupation"):
            self.options_formatted["MSminOccupation"] = float(o["MSminOccupation"])
        else:
            self.options_formatted["MSminOccupation"] = 0.0
        if not self.isEmpty("MSMSminOccupation"):
            self.options_formatted["MSMSminOccupation"] = float(o["MSMSminOccupation"])
        else:
            self.options_formatted["MSMSminOccupation"] = 0.0

        if not self.isEmpty("MSmassrange"):
            self.options_formatted["MSmassrange"] = (
                float(o["MSmassrange"].split(",")[0].strip("() ")),
                float(o["MSmassrange"].split(",")[1].strip("() ")),
            )
        if not self.isEmpty("MSMSmassrange"):
            self.options_formatted["MSMSmassrange"] = (
                float(o["MSMSmassrange"].split(",")[0].strip("() ")),
                float(o["MSMSmassrange"].split(",")[1].strip("() ")),
            )

        if not self.isEmpty("MSresolution"):
            if self.options["MSresolution"] == "auto":
                tol = TypeTolerance("res", 20000.0)
            else:
                tol = TypeTolerance("res", float(o["MSresolution"]))
            self.options_formatted["MSresolution"] = tol
        if not self.isEmpty("MSMSresolution"):
            self.options_formatted["MSMSresolution"] = TypeTolerance(
                "res", float(o["MSMSresolution"])
            )

        if not self.isEmpty("MStolerance"):
            m = re.match("(\d+|\d+\.\d+)(\s)*(ppm|Da)", self.options["MStolerance"])
            if m is None:
                if not o["MStoleranceType"] is None and not o["MStoleranceType"] == "":
                    m = re.match("(\d+|\d+\.\d+)", o["MStolerance"])
                    if not m is None:
                        try:
                            self.options_formatted["MStolerance"] = TypeTolerance(
                                o["MStoleranceType"], float(o["MStolerance"])
                            )
                        except ZeroDivisionError:
                            raise LipidXException(
                                "No tolerance value given. Please input a value greater than zero."
                            )
            else:
                self.options_formatted["MStolerance"] = TypeTolerance(
                    m.group(3), float(o["MStolerance"])
                )
        if not self.isEmpty("MSMStolerance"):
            m = re.match("(\d+|\d+\.\d+)(\s)*(ppm|Da)", self.options["MSMStolerance"])
            if m is None:
                if (
                    not o["MSMStoleranceType"] is None
                    and not o["MSMStoleranceType"] == ""
                ):
                    m = re.match("(\d+|\d+\.\d+)", o["MSMStolerance"])
                    if not m is None:
                        self.options_formatted["MSMStolerance"] = TypeTolerance(
                            o["MSMStoleranceType"], float(o["MSMStolerance"])
                        )
            else:
                self.options_formatted["MSMStolerance"] = TypeTolerance(
                    m.group(3), float(o["MSMStolerance"])
                )

        if not self.isEmpty("MStoleranceType"):
            self.options_formatted["MStoleranceType"] = o["MStoleranceType"]
        if not self.isEmpty("MSMStoleranceType"):
            self.options_formatted["MSMStoleranceType"] = o["MSMStoleranceType"]

        if not self.isEmpty("optionalMStolerance"):
            m = re.match(
                "(\d+|\d+\.\d+)(\s)*(ppm|Da)", self.options["optionalMStolerance"]
            )
            if m is None:
                if (
                    not o["optionalMStoleranceType"] is None
                    and not o["optionalMStoleranceType"] == ""
                ):
                    m = re.match("(\d+|\d+\.\d+)", o["optionalMStolerance"])
                    if not m is None:
                        self.options_formatted["optionalMStolerance"] = TypeTolerance(
                            o["optionalMStoleranceType"],
                            float(o["optionalMStolerance"]),
                        )
            else:
                self.options_formatted["optionalMStolerance"] = TypeTolerance(
                    m.group(3), float(o["optionalMStolerance"])
                )
        if not self.isEmpty("optionalMSMStolerance"):
            m = re.match(
                "(\d+|\d+\.\d+)(\s)*(ppm|Da)", self.options["optionalMSMStolerance"]
            )
            if m is None:
                if (
                    not o["optionalMSMStoleranceType"] is None
                    and not o["optionalMSMStoleranceType"] == ""
                ):
                    m = re.match("(\d+|\d+\.\d+)", o["optionalMSMStolerance"])
                    if not m is None:
                        self.options_formatted["optionalMSMStolerance"] = TypeTolerance(
                            o["optionalMSMStoleranceType"],
                            float(o["optionalMSMStolerance"]),
                        )
            else:
                self.options_formatted["optionalMSMStolerance"] = TypeTolerance(
                    m.group(3), float(o["optionalMSMStolerance"])
                )

        if not self.isEmpty("optionalMStoleranceType"):
            self.options_formatted["optionalMStoleranceType"] = o[
                "optionalMStoleranceType"
            ]
        if not self.isEmpty("optionalMSMStoleranceType"):
            self.options_formatted["optionalMSMStoleranceType"] = o["MSMStoleranceType"]

        if not self.isEmpty("alignmentMethodMS"):
            self.options_formatted["alignmentMethodMS"] = o["alignmentMethodMS"]
        if not self.isEmpty("alignmentMethodMSMS"):
            self.options_formatted["alignmentMethodMSMS"] = o["alignmentMethodMSMS"]
        if not self.isEmpty("scanAveragingMethod"):
            self.options_formatted["scanAveragingMethod"] = o["scanAveragingMethod"]

        # this option is not editable
        self.options_formatted["loopNr"] = 3

        # the file paths
        if not self.isEmpty("masterScan"):
            self.options_formatted["masterScanFileImport"] = o["masterScanImport"]
            self.options_formatted["masterScanFileRun"] = o["masterScanRun"]
        if not self.isEmpty("dumpMasterScan"):
            self.options_formatted["dumpMasterScanFile"] = (
                os.path.splitext(o["masterScanRun"])[0] + "-dump.csv"
            )
        if not self.isEmpty("complementMasterScan"):
            self.options_formatted["complementMasterScanFile"] = (
                os.path.splitext(o["masterScanRun"])[0] + "-complement.csv"
            )

        # copy the rest of the string based options to the internal options
        for opt in list(self.options.keys()):
            if not opt in list(self.options_formatted.keys()):
                self.options_formatted[opt] = self.options[opt]

        self.options_formatted = self.try2apply_calctol(o, self.options_formatted)

    def try2apply_calctol(self, o, options_formatted):
        if o["MSresolution"] == "auto" or o["MSresolution"] == 0:
            options_formatted["optionalMStolerance"] = TypeTolerance("ppm", 20.0)
            options_formatted["optionalMSMStolerance"] = TypeTolerance("ppm", 20.0)
            options_formatted["optionalMStoleranceType"] = "ppm"
            options_formatted["optionalMSMStoleranceType"] = "ppm"

            options_formatted["alignmentMethodMS"] = "calctol"
            options_formatted["alignmentMethodMSMS"] = "calctol"
            options_formatted["scanAveragingMethod"] = "calctol"
        return options_formatted

    def formatOptionsRun(self):
        """Reads and formats the settings of the current configuration for correctness."""

        floating_point_m = re.compile("[+-]?[0-9]*\.?[0-9]+")

        o = self.options

        for option in list(o.keys()):
            if not option in ["MScalibration", "MSMScalibration"]:
                try:
                    if floating_point_m.match(o[option]):
                        self.options_formatted[option] = float(o[option])
                except:
                    pass

        # convert Boolean values
        for option in list(o.keys()):
            if o[option] == "True":
                self.options_formatted[option] = True
            if o[option] == "False":
                self.options_formatted[option] = False

        if not self.options["optionalMStolerance"] is None:
            m = re.match(
                "(\d+|\d+\.\d+)(\s)*(ppm|Da)", self.options["optionalMStolerance"]
            )
            if m is None:
                if (
                    not o["optionalMStoleranceType"] is None
                    and not o["optionalMStoleranceType"] == ""
                ):
                    m = re.match("(\d+|\d+\.\d+)", o["optionalMStolerance"])
                    if not m is None:
                        self.options_formatted["optionalMStolerance"] = TypeTolerance(
                            o["optionalMStoleranceType"],
                            float(o["optionalMStolerance"]),
                        )
            else:
                self.options_formatted["optionalMStolerance"] = TypeTolerance(
                    m.group(3), float(o["optionalMStolerance"])
                )
        if not self.options["optionalMSMStolerance"] is None:
            m = re.match(
                "(\d+|\d+\.\d+)(\s)*(ppm|Da)", self.options["optionalMSMStolerance"]
            )
            if m is None:
                if (
                    not o["optionalMSMStoleranceType"] is None
                    and not o["optionalMSMStoleranceType"] == ""
                ):
                    m = re.match("(\d+|\d+\.\d+)", o["optionalMSMStolerance"])
                    if not m is None:
                        self.options_formatted["optionalMSMStolerance"] = TypeTolerance(
                            o["optionalMSMStoleranceType"],
                            float(o["optionalMSMStolerance"]),
                        )
            else:
                self.options_formatted["optionalMSMStolerance"] = TypeTolerance(
                    m.group(3), float(o["optionalMSMStolerance"])
                )

        if not o["optionalMSthresholdType"] is None:
            self.options_formatted["optionalMSthresholdType"] = o[
                "optionalMSthresholdType"
            ]
        if not o["optionalMSMSthresholdType"] is None:
            self.options_formatted["optionalMSMSthresholdType"] = o[
                "optionalMSMSthresholdType"
            ]

        # this option is not editable
        self.options_formatted["loopNr"] = 3

        # copy the rest of the string based options to the internal options
        for opt in list(self.options.keys()):
            if not opt in list(self.options_formatted.keys()):
                self.options_formatted[opt] = self.options[opt]

    def getOptions(self):
        return self.options_formatted

    def getPrintOptions(self):
        return self.options
