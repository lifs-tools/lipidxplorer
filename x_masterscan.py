import os
from x_options  import read_options
from lx.spectraContainer import MasterScan
from lx.spectraImport import doImport, lpdxImportDEF_new
from lx.spectraTools import loadSC


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

if __name__ == "__main__":
    proy = r'test_resources\small_test\small_test-project.lxp'
    options = read_options(proy)
    masterscan = make_masterscan(options)
    masterscan.dump(options['dumpMasterScanFile'])
    reference  = loadSC(r'test_resources\small_test\small_test_LX12.sc')
    same = compareMasterScans(masterscan, reference)
    print(f'are same {same}')
