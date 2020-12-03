from pathlib import Path
from x_options  import read_options
from x_masterscan import make_masterscan
from lx.mfql.runtimeExecution import TypeMFQL
from lx.mfql.mfqlParser import startParsing

def getMfqlFiles(root_mfql_dir):
    p = Path(root_mfql_dir)
    mfqls = p.glob('*.mfql')
    return {mfql.name:mfql.read_text() for mfql in mfqls }

def makeResultsString(result, options):
    # result = mfqlObj.result
    outputSeperator = ','
    #as in lxmain
    if result.mfqlOutput:
        strHead = ''
        if not options['noHead']:
            for key in result.listHead:
                if key != result.listHead[-1]:
                    strHead += key + '%s' % outputSeperator
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

    return strResult

def make_MFQL_result(masterscan, mfqlFiles):
    mfqlObj = TypeMFQL(masterScan=masterscan)
    mfqlObj.options = options
    mfqlObj.outputSeperator = ','

    (progressCount, returnValue) = startParsing(mfqlFiles,
            mfqlObj,
            masterscan,
            isotopicCorrectionMS = options['isotopicCorrectionMS'],
            isotopicCorrectionMSMS = options['isotopicCorrectionMSMS'],
            complementSC = options['complementMasterScan'],
            parent = None,
            progressCount = 0,
            generateStatistics = options['statistics'],
            )

    return mfqlObj.result

if __name__ == "__main__":
    proy = r'test_resources\small_test\small_test-project.lxp'
    options = read_options(proy)
    masterscan = make_masterscan(options)
    mfqlFiles = getMfqlFiles(r'test_resources\small_test')
    result = make_MFQL_result(masterscan, mfqlFiles)
    resultStr = makeResultsString(result, options)
    reference = Path(r'test_resources\small_test\small_test-out.csv').read_text()
    print(f'are same {resultStr == reference}')
