import os
from x_options import read_options
from lx.spectraContainer import MasterScan
from lx.spectraImport import doImport, lpdxImportDEF_new
from lx.spectraTools import loadSC


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


if __name__ == "__main__":
    # proy = r'test_resources\small_test\small_test-project.lxp'
    # options = read_options(proy)
    # masterscan = make_masterscan(options)
    # masterscan.dump(options['dumpMasterScanFile'])

    reference1 = loadSC(
        r"d:\ownCloud\LX 2.0\kai_compare_lx1_12_13\LX1-2_PC_test_MS1\LX1-2_PC_test_MS1.sc"
    )
    # reference1.dump(r'd:\ownCloud\LX 2.0\kai_compare_lx1_12_13\LX1-2_PC_test_MS1\LX1-2_PC_test_MS1-dump.csv')
    interesting1 = [
        e
        for e in reference1.listSurveyEntry
        if e.peakMean > 508.26 and e.peakMean < 508.269
    ]
    del reference1
    for e in interesting1:
        print(e)
    print("****")
    reference2 = loadSC(
        r"d:\ownCloud\LX 2.0\kai_compare_lx1_12_13\LX2_PC_test_MS1\LX2_PC_test_MS1.sc"
    )
    # reference2.dump(r'd:\ownCloud\LX 2.0\kai_compare_lx1_12_13\LX2_PC_test_MS1\LX2_PC_test_MS1-dump.csv')
    interesting2 = [
        e
        for e in reference2.listSurveyEntry
        if e.peakMean > 508.0 and e.peakMean < 508.9
    ]
    del reference2
    for e in interesting2:
        print(e)
    # same = compareMasterScans(masterscan, reference)
    print(f"are same ")
# interesting2[3] has the two peaks , in lx1 there is only one peak
# /-/ . 508.2625 |           0        13031            0            0            0            0            0        31119            0            0            0            0            0            0            0            0   QP: 0.0032 Mean: 508.2625 Median: 508.2625 V(X): 0.0000 E(X): 0.0016 []
# /-/ . 508.2643 |           0            0            0            0            0            0            0        31119            0            0            0            0            0            0            0            0   QP: 0.0000 Mean: 508.2643 Median: 508.2643 V(X): 0.0000 E(X): 0.0000 []
