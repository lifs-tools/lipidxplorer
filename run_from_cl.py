from lx.project import Project
from lx.spectraImport import getAMasterScan, doImport
from lx.mfql.runtimeExecution import TypeMFQL
from lx.mfql.mfqlParser import startParsing
import glob
import generateOptions

proy = r'test_res\test_res-project.lxp'
proy_xml = r'test_res\test_res-project_xml.lxp'
root_mfql_dir = r'test_res'
input_files_dir = r'test_res'

def getInputFiles(options):
    importDir = options['importDir']
    extension = options['spectraFormat']
    files = glob.glob(importDir+r'\*.'+extension)
    return files


def direct(project_path):
    #lximport
    project = Project()
    project.load(project_path)
    project.testOptions()
    project.formatOptions()
    options_og = project.getOptions()
    options = generateOptions.fromFullOptions(options_og)
    # options = generateOptions.setOptions2likelyDefault(options)
    options = generateOptions.setOptions_fromImputPaths( input_files_dir, root_mfql_dir)

    #lxmain
    scan = doImport( #note lpdxImportDEF_new is used when with gui
        spectraFormat = options['dataType'],
        scan = getAMasterScan(options),
        listFiles=getInputFiles(options),
        alignmentMS=options['alignmentMethodMS'],#linear, hierarchical, heuristic o, only for mzXML
        alignmentMSMS=options['alignmentMethodMSMS'],
        scanAvg=options['scanAveragingMethod'],#linear, heuristic
        importMSMS=options['importMSMS']) # Ii think oits always True?

    #lrRun
    mfqlFiles = generateOptions.getMfqlFiles(root_mfql_dir)

    # fronm lxmain startMFQL(options=options, queries=dictMFQL)
    mfqlObj = TypeMFQL(masterScan=scan)
    mfqlObj.options = options
    mfqlObj.outputSeperator = ','

    # parse input file k and save the result in mfqlObj.result
    startParsing(mfqlFiles,
                mfqlObj,
                isotopicCorrectionMS=options['isotopicCorrectionMS'],
                isotopicCorrectionMSMS=options['isotopicCorrectionMSMS'],
                complementSC=options['complementMasterScan'],
                generateStatistics=options['statistics'],
                )
    scan.dump(options_og['dumpMasterScanFile'])
    makeResultsFile(mfqlObj, options)# this makes the -out files

def makeResultsFile(mfqlObj, options):
    result = mfqlObj.result
    #as in lxmain
    if result.mfqlOutput:
        strHead = ''
        if not options['noHead']:
            for key in result.listHead:
                if key != result.listHead[-1]:
                    strHead += key + '%s' % mfqlObj.outputSeperator
                else:
                    strHead += key

            # generate whole string
            strResult = "%s\n" % strHead
        else:
            strResult = ''

        for k in result.dictQuery.values():
            strResult += "\n###,%s\n" % k.name
            strResult += k.strOutput
            strResult += '\n'

        # free 'k' because otherwise Python keeps all
        # the SurveyEntries. Don't ask me why...
        del k

        # put out
        f = open(options['resultFile'], 'w')
        f.write(strResult)
        f.close()

if __name__ == '__main__':
    import timeit
    r = timeit.timeit('direct(proy)', setup="from __main__ import *", number=1)
    print(r)

    # Seconds from generate options
    # 9 options['timerange'] = (0.0, float("inf"))
    # 34  options['timerange'] = (0.0, float("inf")
    # 211 options['MSmassrange'] = (0.0, float("inf")); options['MSMSmassrange'] = (0.0, float("inf"))
    # print(r)
    # direct(proy)
    # direct(proy_xml)
