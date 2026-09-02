"""Ground truth: run ONE sample through the real non-batch MFQL path.

Builds a single-sample MasterScan (identical to what batch mode builds),
saves it, then calls lx.lxMain.startMFQL -- the long-standing non-batch
entry point -- with all 28 queries. Its species set is the reference the
batch variants should be judged against.
"""
import configparser, glob, os, sys

sys.path.insert(0, os.environ.get("LX_ROOT",
    "/Users/nilshoffmann/Projects/github.com/lifs-tools/lipidxplorer"))

BENCH = "/Users/nilshoffmann/Downloads/1.5-benchmark-data"
INI = os.path.join(BENCH, "lpdxImportSettings_LIFS_Course.ini")
SECTION = "240821_mice_lung_neg"


def main():
    work = sys.argv[1]
    out_csv = sys.argv[2]

    import lx.gui.lpdxGUI as G
    from lx.spectraImport import getInputFiles
    from lx.spectraTools import saveSC
    from lx.batch_processor import build_master_scan
    from lx.lxMain import startMFQL

    class _Ctrl:
        def __init__(s, v): s._v = v
        def GetValue(s): return s._v
    class Stub: pass

    stub = Stub()
    stub.confParse = configparser.ConfigParser(); stub.confParse.read(INI)
    stub.currentConfiguration = SECTION
    stub.text_ctrl_ImportDataSection = _Ctrl(work)
    stub.combo_ctrl_ImportDataSection = _Ctrl("mzML")
    stub.text_ctrl_OutputMasterScanSection = _Ctrl(INI)
    G.LpdxFrame.collectSettings(stub, SECTION)
    project = G.LpdxFrame.readOptions_batch(stub)
    o = project.options
    o["batch_mode"] = True; o["importMSMS"] = True
    o["spectraFormat"] = "mzML"; o["masterScanImport"] = INI; o["resultFile"] = INI
    project.testOptions(); project.formatOptions()
    options = project.getOptions()

    listFiles, _, _ = getInputFiles(work, options)
    sp, name = str(listFiles[0][0]), listFiles[0][1]
    print(f"### sample {os.path.basename(sp)}", flush=True)

    scan = build_master_scan(sp, name, options)
    sc_path = os.path.join(work, "single.sc")
    saveSC(scan, sc_path)
    print(f"### MasterScan saved {sc_path}", flush=True)

    qpaths = sorted(glob.glob(os.path.join(BENCH, "MFQL", "negative_standards", "*.mfql")))
    qpaths += sorted(glob.glob(os.path.join(BENCH, "MFQL", "negative_lipids", "*.mfql")))
    queries = {os.path.basename(p): p for p in qpaths}

    # non-batch expects to LOAD the masterscan and write a result file
    options["masterScanRun"] = sc_path
    options["resultFile"] = out_csv
    options["batch_mode"] = False
    print(f"### running startMFQL with {len(queries)} queries", flush=True)
    startMFQL(options=options, queries=queries, parent=None)
    print(f"### wrote {out_csv}", flush=True)


if __name__ == "__main__":
    main()
