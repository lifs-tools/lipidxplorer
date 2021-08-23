import pytest
from lx.project import Project

expected_str = r"""{'setting': 1.0, 'selectionWindow': 0.4, 'MStolerance': 2.00 ppm, 'MSMStolerance': 2.00 ppm, 'MSresolution': 5.00 ppm, 'MSMSresolution': 11.11 ppm, 'MSresolutionDelta': -100.0, 'MSMSresolutionDelta': -90.0, 'MSthreshold': 0.0001, 'MSMSthreshold': 0.0001, 'MSminOccupation': 0.5, 'MSMSminOccupation': 0.5, 'precursorMassShift': 0.0, 'precursorMassShiftOrbi': 0.0, 'optionalMStolerance': 5.00 ppm, 'optionalMSMStolerance': 5.00 ppm, 'MSfilter': 0.6, 'MSMSfilter': 0.6, 'loopNr': 3, 'importMSMS': True, 'pisSpectra': False, 'isotopicCorrection_MSMS': False, 'removeIsotopes': True, 'isotopesInMasterScan': False, 'monoisotopicCorrection': False, 'relativeIntensity': False, 'logMemory': False, 'intensityCorrection': False, 'masterScanInSQL': False, 'sumFattyAcids': False, 'isotopicCorrectionMS': True, 'isotopicCorrectionMSMS': True, 'complementMasterScan': False, 'noHead': False, 'compress': False, 'tabLimited': False, 'dumpMasterScan': True, 'statistics': False, 'noPermutations': True, 'settingsPrefix': False, 'timerange': (33.0, 1080.0), 'MScalibration': [680.4802], 'MSmassrange': (360.0, 1000.0), 'MSMSmassrange': (150.0, 1000.0), 'MStoleranceType': 'ppm', 'MSMStoleranceType': 'ppm', 'optionalMStoleranceType': 'ppm', 'optionalMSMStoleranceType': 'ppm', 'alignmentMethodMS': 'linear', 'alignmentMethodMSMS': 'linear', 'scanAveragingMethod': 'linear', 'masterScanFileImport': 'D:\\fork\\isas_lipidxplorer\\test_resources\\small_test\\small_test.sc', 'masterScanFileRun': 'D:\\fork\\isas_lipidxplorer\\test_resources\\small_test\\small_test.sc', 'dumpMasterScanFile': 'D:\\fork\\isas_lipidxplorer\\test_resources\\small_test\\small_test-dump.csv', 'complementMasterScanFile': 'D:\\fork\\isas_lipidxplorer\\test_resources\\small_test\\small_test-complement.csv', 'importDir': 'D:\\fork\\isas_lipidxplorer\\test_resources\\small_test', 'masterScanRun': 'D:\\fork\\isas_lipidxplorer\\test_resources\\small_test\\small_test.sc', 'masterScanImport': 'D:\\fork\\isas_lipidxplorer\\test_resources\\small_test\\small_test.sc', 'dataType': 'mzML', 'ini': 'D:\\fork\\isas_lipidxplorer\\test_resources\\small_test\\lpdxImportSettings_benchmark.ini', 'MSMScalibration': '', 'MSthresholdType': 'absolute', 'MSMSthresholdType': 'absolute', 'intensityCorrectionPrecursor': '', 'intensityCorrectionFragment': '', 'resultFile': 'D:\\fork\\isas_lipidxplorer\\test_resources\\small_test\\small_test-out.csv', 'optionalMSthreshold': 'None', 'optionalMSMSthreshold': 'None', 'optionalMSthresholdType': 'None', 'optionalMSMSthresholdType': 'None', 'mzXML': 'None', 'spectraFormat': 'mzML'}"""

def read_options(project_path):
    project = Project()
    project.load(project_path)
    project.testOptions()
    project.formatOptions()
    options = project.getOptions()
    return options

def test_read_project():
    proy = r'test_resources\small_test\small_test-project.lxp'
    options = read_options(proy)

    assert expected_str == str(options)