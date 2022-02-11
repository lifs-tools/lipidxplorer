from pathlib import Path

from lx.project import Project

from lx.spectraImport import doImport, lpdxImportDEF_new

from lx.mfql.runtimeExecution import TypeMFQL
from lx.mfql.mfqlParser import startParsing


proy_path = r"test_resources/small_test/small_test-project.lxp"
expected_options_str = r"""{'setting': 1.0, 'selectionWindow': 0.4, 'MStolerance': 2.00 ppm, 'MSMStolerance': 2.00 ppm, 'MSresolution': 5.00 ppm, 'MSMSresolution': 11.11 ppm, 'MSresolutionDelta': -100.0, 'MSMSresolutionDelta': -90.0, 'MSthreshold': 0.0001, 'MSMSthreshold': 0.0001, 'MSminOccupation': 0.5, 'MSMSminOccupation': 0.5, 'precursorMassShift': 0.0, 'precursorMassShiftOrbi': 0.0, 'optionalMStolerance': 5.00 ppm, 'optionalMSMStolerance': 5.00 ppm, 'MSfilter': 0.6, 'MSMSfilter': 0.6, 'loopNr': 3, 'importMSMS': True, 'pisSpectra': False, 'isotopicCorrection_MSMS': False, 'removeIsotopes': True, 'isotopesInMasterScan': False, 'monoisotopicCorrection': False, 'relativeIntensity': False, 'logMemory': False, 'intensityCorrection': False, 'masterScanInSQL': False, 'sumFattyAcids': False, 'isotopicCorrectionMS': True, 'isotopicCorrectionMSMS': True, 'complementMasterScan': False, 'noHead': False, 'compress': False, 'tabLimited': False, 'dumpMasterScan': False, 'statistics': False, 'noPermutations': True, 'settingsPrefix': False, 'timerange': (33.0, 1080.0), 'MScalibration': [680.4802], 'MSmassrange': (360.0, 1000.0), 'MSMSmassrange': (150.0, 1000.0), 'MStoleranceType': 'ppm', 'MSMStoleranceType': 'ppm', 'optionalMStoleranceType': 'ppm', 'optionalMSMStoleranceType': 'ppm', 'alignmentMethodMS': 'linear', 'alignmentMethodMSMS': 'linear', 'scanAveragingMethod': 'linear', 'masterScanFileImport': 'test_resources/small_test/small_test.sc', 'masterScanFileRun': 'test_resources/small_test/small_test.sc', 'dumpMasterScanFile': 'test_resources/small_test/small_test-dump.csv', 'complementMasterScanFile': 'test_resources/small_test/small_test-complement.csv', 'importDir': 'test_resources/small_test', 'masterScanRun': 'test_resources/small_test/small_test.sc', 'masterScanImport': 'test_resources/small_test/small_test.sc', 'dataType': 'mzML', 'ini': 'test_resources/small_test/lpdxImportSettings_benchmark.ini', 'MSMScalibration': '', 'MSthresholdType': 'absolute', 'MSMSthresholdType': 'absolute', 'intensityCorrectionPrecursor': '', 'intensityCorrectionFragment': '', 'resultFile': 'test_resources/small_test/small_test-out.csv', 'optionalMSthreshold': 'None', 'optionalMSMSthreshold': 'None', 'optionalMSthresholdType': 'None', 'optionalMSMSthresholdType': 'None', 'mzXML': 'None', 'spectraFormat': 'mzML'}"""

expected_ms_path = r"test_resources/small_test/small_test_LX12.sc"
expected_lx2ms_path = r"test_resources/small_test/small_test_LX2.sc"


def read_options(project_path, make_msresolution_auto=False):

    project = Project()
    project.load(project_path)
    if make_msresolution_auto:
        project.options["MSresolution"] = "auto"
    project.testOptions()
    project.formatOptions()
    options = project.getOptions()
    return options


# ==========masterscan
def make_masterscan(options):
    listIntermission = lpdxImportDEF_new(options=options, parent=None)

    scan = doImport(
        listIntermission[0],
        listIntermission[1],
        listIntermission[2],
        listIntermission[3],
        listIntermission[4],
        listIntermission[5],
        listIntermission[6],
        listIntermission[7],
        options["alignmentMethodMS"],
        options["alignmentMethodMSMS"],
        options["scanAveragingMethod"],
        options["importMSMS"],
    )
    return scan


def compareMasterScans(created, reference):
    c_ls = created.listSurveyEntry
    a_ls = reference.listSurveyEntry

    same = True
    for c, a in zip(c_ls, a_ls):
        if c != a:
            same = False
            break
    return same


# ================= mfql

out_reference = """SPECIE,CLASS,MASS,IDMSLEVEL,QUANTMSLEVEL,ISOBARIC,CHEMSC,ERRppm,FRERRppm,INT:190321_Serum_Lipidextract_368723_01.mzML,INT:190321_Serum_Lipidextract_368723_02.mzML,QUALA:190321_Serum_Lipidextract_368723_01.mzML,QUALA:190321_Serum_Lipidextract_368723_02.mzML,QUALB:190321_Serum_Lipidextract_368723_01.mzML,QUALB:190321_Serum_Lipidextract_368723_02.mzML,QUALC:190321_Serum_Lipidextract_368723_01.mzML,QUALC:190321_Serum_Lipidextract_368723_02.mzML

###,CESplash
CE-IS,CE,675.6788022582082,2.0,2.0,,C45 H75 D7 O2 N1 ,1.27,0.09,1011400.7,846662.2,4012456.0,3392868.9,4012456.0,3392868.9,4012456.0,3392868.9


###,CholesterolMSMS
CE 14:0,CE,614.5880457819642,2.0,2.0,,C41 H76 O2 N1 ,1.61,0.32,59798.3,42923.3,307966.6,252668.8,307966.6,252668.8,307966.6,252668.8
CE 15:0,CE,628.6035929460234,2.0,2.0,,C42 H78 O2 N1 ,1.41,0.19,17515.2,17286.7,63084.5,61244.9,63084.5,61244.9,63084.5,61244.9
CE 16:1,CE,640.6037300477551,2.0,2.0,,C43 H78 O2 N1 ,1.60,0.07,630592.9,462945.5,2134711.5,1889786.5,2134711.5,1889786.5,2134711.5,1889786.5
CE 16:0,CE,642.619326247301,2.0,2.0,,C43 H80 O2 N1 ,1.51,0.02,2235270.8,1634640.0,8177329.7,6865548.5,8177329.7,6865548.5,8177329.7,6865548.5
CE 17:1,CE,654.6194415630919,2.0,2.0,,C44 H80 O2 N1 ,1.66,0.21,52677.5,51634.8,220209.9,185837.9,220209.9,185837.9,220209.9,185837.9
CE 17:0,CE,656.6350071147785,2.0,2.0,,C44 H82 O2 N1 ,1.52,0.19,35043.4,0.0,142027.7,126431.7,142027.7,126431.7,142027.7,126431.7
CE 18:3,CE,664.6036841469262,2.0,2.0,,C45 H78 O2 N1 ,1.47,0.22,445004.6,388951.7,1923426.7,1602003.1,1923426.7,1602003.1,1923426.7,1602003.1
CE 18:2,CE,666.6191890107873,2.0,2.0,,C45 H80 O2 N1 ,1.25,0.13,17516418.5,15554329.2,74716168.2,64112907.3,74716168.2,64112907.3,74716168.2,64112907.3
CE 18:1,CE,668.6347530334406,2.0,2.0,,C45 H82 O2 N1 ,1.12,0.20,3767341.3,2989491.2,15702181.8,13315926.2,15702181.8,13315926.2,15702181.8,13315926.2
CE 18:0,CE,670.6505131216841,2.0,2.0,,C45 H84 O2 N1 ,1.28,0.27,117367.7,95704.8,532378.2,461442.1,532378.2,461442.1,532378.2,461442.1
CE 19:5,CE,674.5847600354955,2.0,2.0,,C46 H76 O2 N1 ,-3.40,0.32,70376.8,64550.9,100682.1,94081.4,100682.1,94081.4,100682.1,94081.4
CE 19:3,CE,678.6193589580417,2.0,2.0,,C46 H80 O2 N1 ,1.48,0.26,9081.7,16919.7,40789.9,53197.8,40789.9,53197.8,40789.9,53197.8
CE 20:5,CE,688.6034452430658,2.0,2.0,,C47 H78 O2 N1 ,1.07,0.25,207631.7,159652.9,619124.1,530655.6,619124.1,530655.6,619124.1,530655.6
CE 20:4,CE,690.6191954984191,2.0,2.0,,C47 H80 O2 N1 ,1.22,0.10,3816827.1,2976938.0,12244934.7,10541829.3,12244934.7,10541829.3,12244934.7,10541829.3
CE 20:3,CE,692.634805351091,2.0,2.0,,C47 H82 O2 N1 ,1.15,0.30,212456.0,210489.8,868080.7,713602.8,868080.7,713602.8,868080.7,713602.8
CE 22:6,CE,714.6192762222361,2.0,2.0,,C49 H80 O2 N1 ,1.29,0.32,191528.7,195760.5,622205.4,522206.7,622205.4,522206.7,622205.4,522206.7
CE 22:5,CE,716.6347799842056,2.0,2.0,,C49 H82 O2 N1 ,1.08,0.48,32964.7,34786.1,61850.1,48246.2,61850.1,48246.2,61850.1,48246.2
"""


def getMfqlFiles(root_mfql_dir):
    p = Path(root_mfql_dir)
    mfqls = p.glob("*.mfql")
    return {mfql.name: mfql.read_text() for mfql in mfqls}


def makeResultsString(result, options):
    # result = mfqlObj.result
    outputSeperator = ","
    # as in lxmain
    if result.mfqlOutput:
        strHead = ""
        if not options["noHead"]:
            for key in result.listHead:
                if key != result.listHead[-1]:
                    strHead += key + "%s" % outputSeperator
                else:
                    strHead += key

            # generate whole string
            strResult = "%s\n" % strHead
        else:
            strResult = ""

        for k in result.dictQuery.values():
            strResult += "\n###,%s\n" % k.name
            strResult += k.strOutput
            strResult += "\n"

    return strResult


def make_MFQL_result(masterscan, mfqlFiles, options):
    mfqlObj = TypeMFQL(masterScan=masterscan)
    mfqlObj.options = options
    mfqlObj.outputSeperator = ","

    (progressCount, returnValue) = startParsing(
        mfqlFiles,
        mfqlObj,
        masterscan,
        isotopicCorrectionMS=options["isotopicCorrectionMS"],
        isotopicCorrectionMSMS=options["isotopicCorrectionMSMS"],
        complementSC=options["complementMasterScan"],
        parent=None,
        progressCount=0,
        generateStatistics=options["statistics"],
    )

    return mfqlObj.result
