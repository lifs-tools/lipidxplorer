from lx.project import Project

from lx.spectraImport import doImport, lpdxImportDEF_new
from lx.spectraTools import loadSC


proy_path = r'test_resources\small_test\small_test-project.lxp'
expected_options_str = r"""{'setting': 1.0, 'selectionWindow': 0.4, 'MStolerance': 2.00 ppm, 'MSMStolerance': 2.00 ppm, 'MSresolution': 5.00 ppm, 'MSMSresolution': 11.11 ppm, 'MSresolutionDelta': -100.0, 'MSMSresolutionDelta': -90.0, 'MSthreshold': 0.0001, 'MSMSthreshold': 0.0001, 'MSminOccupation': 0.5, 'MSMSminOccupation': 0.5, 'precursorMassShift': 0.0, 'precursorMassShiftOrbi': 0.0, 'optionalMStolerance': 5.00 ppm, 'optionalMSMStolerance': 5.00 ppm, 'MSfilter': 0.6, 'MSMSfilter': 0.6, 'loopNr': 3, 'importMSMS': True, 'pisSpectra': False, 'isotopicCorrection_MSMS': False, 'removeIsotopes': True, 'isotopesInMasterScan': False, 'monoisotopicCorrection': False, 'relativeIntensity': False, 'logMemory': False, 'intensityCorrection': False, 'masterScanInSQL': False, 'sumFattyAcids': False, 'isotopicCorrectionMS': True, 'isotopicCorrectionMSMS': True, 'complementMasterScan': False, 'noHead': False, 'compress': False, 'tabLimited': False, 'dumpMasterScan': True, 'statistics': False, 'noPermutations': True, 'settingsPrefix': False, 'timerange': (33.0, 1080.0), 'MScalibration': [680.4802], 'MSmassrange': (360.0, 1000.0), 'MSMSmassrange': (150.0, 1000.0), 'MStoleranceType': 'ppm', 'MSMStoleranceType': 'ppm', 'optionalMStoleranceType': 'ppm', 'optionalMSMStoleranceType': 'ppm', 'alignmentMethodMS': 'linear', 'alignmentMethodMSMS': 'linear', 'scanAveragingMethod': 'linear', 'masterScanFileImport': 'D:\\fork\\isas_lipidxplorer\\test_resources\\small_test\\small_test.sc', 'masterScanFileRun': 'D:\\fork\\isas_lipidxplorer\\test_resources\\small_test\\small_test.sc', 'dumpMasterScanFile': 'D:\\fork\\isas_lipidxplorer\\test_resources\\small_test\\small_test-dump.csv', 'complementMasterScanFile': 'D:\\fork\\isas_lipidxplorer\\test_resources\\small_test\\small_test-complement.csv', 'importDir': 'D:\\fork\\isas_lipidxplorer\\test_resources\\small_test', 'masterScanRun': 'D:\\fork\\isas_lipidxplorer\\test_resources\\small_test\\small_test.sc', 'masterScanImport': 'D:\\fork\\isas_lipidxplorer\\test_resources\\small_test\\small_test.sc', 'dataType': 'mzML', 'ini': 'D:\\fork\\isas_lipidxplorer\\test_resources\\small_test\\lpdxImportSettings_benchmark.ini', 'MSMScalibration': '', 'MSthresholdType': 'absolute', 'MSMSthresholdType': 'absolute', 'intensityCorrectionPrecursor': '', 'intensityCorrectionFragment': '', 'resultFile': 'D:\\fork\\isas_lipidxplorer\\test_resources\\small_test\\small_test-out.csv', 'optionalMSthreshold': 'None', 'optionalMSMSthreshold': 'None', 'optionalMSthresholdType': 'None', 'optionalMSMSthresholdType': 'None', 'mzXML': 'None', 'spectraFormat': 'mzML'}"""

expected_ms_path = r'test_resources\small_test\small_test_LX12.sc' 

def read_options(project_path):
    project = Project()
    project.load(project_path)
    project.testOptions()
    project.formatOptions()
    options = project.getOptions()
    return options

def make_masterscan(options):
    listIntermission = lpdxImportDEF_new(
			options = options,
			parent = None)

    scan = doImport(listIntermission[0],
			listIntermission[1],
			listIntermission[2],
			listIntermission[3],
			listIntermission[4],
			listIntermission[5],
			listIntermission[6],
			listIntermission[7],
			options['alignmentMethodMS'],
			options['alignmentMethodMSMS'],
			options['scanAveragingMethod'],
			options['importMSMS'])
    return scan


def  compareMasterScans(created, reference):
    c_ls = created.listSurveyEntry
    a_ls = reference.listSurveyEntry

    same =True
    for c,a in zip(c_ls, a_ls):
        if c != a:
            same = False
            break
    return same
