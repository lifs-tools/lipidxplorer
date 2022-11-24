from pathlib import Path
import pickle
import pandas as pd

from lx.project import Project

from lx.spectraImport import doImport, lpdxImportDEF_new

from lx.mfql.runtimeExecution import TypeMFQL
from lx.mfql.mfqlParser import startParsing


proy_path = r"test_resources/small_test/small_test-project.lxp"

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
        if str(c) != str(a):
            same = False
            break
            # TODO does this work and check the listMSMS ?

    return same

def compareResults(created, reference):
    # col_headers = reference.listHead
    same = True
    for k in reference.dictQuery:
        created_q = created.dictQuery[k]
        reference_q = reference.dictQuery[k]

        for col_header in reference_q.dataMatrix:
            for idx,val in enumerate(reference_q.dataMatrix[col_header]):
                if created_q.dataMatrix[col_header][idx] != val:
                    same =False
                    break
    return same



# ================= mfql


def getMfqlFiles(root_mfql_dir):
    p = Path(root_mfql_dir)
    mfqls = p.glob("*.mfql")
    return {mfql.name: mfql.read_text() for mfql in mfqls}


def makeResultsString(result, options)->str:
    # result = mfqlObj.result
    outputSeperator = ","
    # as in lxmain
    strResult = ''
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


def make_MFQL_result(masterscan, mfqlFiles, options, log_steps = False):
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
        log_steps=log_steps,
    )

    return mfqlObj.result


def masterscan_2_df(masterscan, add_ids = False, add_og_intensity = False):
    def se_2_dict(se):
        res = dict(se.dictIntensity)
        res['precurmass'] = se.precurmass
        res['massWindow'] = se.massWindow
        if add_ids:
            res['listMark'] = str(se.listMark)
        if add_og_intensity:
            og_intensity = dict(se.dictBeforeIsocoIntensity)
            og_intensity = {f"og_{k}":v for k,v in og_intensity.items()}
            res.update(og_intensity)
        
        return res
    return pd.DataFrame((se_2_dict(se) for se in masterscan.listSurveyEntry))
    

