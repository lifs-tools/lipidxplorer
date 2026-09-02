"""Does MFQL query order change batch results, and does the one-call fix help?

Builds ONE MasterScan, then runs the same queries three ways on independent
deep copies of it:

  A  queries in sorted order,   one startParsing() per query  (batch today)
  B  queries in reversed order, one startParsing() per query  (batch today)
  C  all queries in a single startParsing() call              (non-batch, lxMain)

A vs B  -> is the result order-dependent?
A vs C  -> does batch differ from the non-batch semantics?
"""
import configparser, copy, glob, io, os, sys, json

sys.path.insert(0, "/Users/nilshoffmann/Projects/github.com/lifs-tools/lipidxplorer")

BENCH = "/Users/nilshoffmann/Downloads/1.5-benchmark-data"
INI = os.path.join(BENCH, "lpdxImportSettings_LIFS_Course.ini")
SECTION = "240821_mice_lung_neg"
NQ = int(os.environ.get("NQ", "8"))


def build_options(import_dir):
    import lx.gui.lpdxGUI as G

    class _Ctrl:
        def __init__(s, v): s._v = v
        def GetValue(s): return s._v

    class Stub: pass
    stub = Stub()
    stub.confParse = configparser.ConfigParser(); stub.confParse.read(INI)
    stub.currentConfiguration = SECTION
    stub.text_ctrl_ImportDataSection = _Ctrl(import_dir)
    stub.combo_ctrl_ImportDataSection = _Ctrl("mzML")
    stub.text_ctrl_OutputMasterScanSection = _Ctrl(INI)

    G.LpdxFrame.collectSettings(stub, SECTION)
    project = G.LpdxFrame.readOptions_batch(stub)
    o = project.options
    o["batch_mode"] = True; o["importMSMS"] = True
    o["spectraFormat"] = "mzML"; o["masterScanImport"] = INI; o["resultFile"] = INI
    o["savePerSample"] = False
    project.testOptions(); project.formatOptions()
    return project.getOptions()


def run_queries(scan, qpaths, options, single_call):
    """Return {query_name: DataFrame}. single_call mirrors lxMain."""
    import pandas as pd
    from lx.tools import odict
    from lx.mfql.runtimeExecution import TypeMFQL
    from lx.mfql.mfqlParser import startParsing
    
    if not single_call:
        # the FIXED batch path: one call for all queries, order as given
        from lx.batch_processor import run_mfql_queries_on_scan
        qs = [{"name": os.path.basename(p), "path": p} for p in qpaths]
        return run_mfql_queries_on_scan(scan, qs, options)

    mfqlFiles = odict()
    for p in qpaths:
        mfqlFiles[os.path.basename(p)] = open(p, encoding="utf-8").read()
    mfqlObj = TypeMFQL(masterScan=scan)
    mfqlObj.options = options
    mfqlObj.outputSeperator = "," 
    startParsing(mfqlFiles, mfqlObj, scan,
                 isotopicCorrectionMS=options.get("isotopicCorrectionMS", True),
                 isotopicCorrectionMSMS=options.get("isotopicCorrectionMSMS", True),
                 complementSC=options.get("complementMasterScan", False),
                 parent=None, progressCount=0,
                 generateStatistics=options.get("statistics", False))
    res = mfqlObj.result
    out = {}
    if getattr(res, "mfqlOutput", False):
        header = list(res.listHead) if hasattr(res, "listHead") else None
        for qres in res.dictQuery.values():
            t = qres.strOutput.strip()
            if not t: continue
            out[qres.name] = pd.read_csv(io.StringIO(t), sep=",", names=header, header=None)
    return out


def fingerprint(res):
    """Stable summary of a result set: rows + summed intensity per query."""
    import pandas as pd
    fp = {}
    for name, df in sorted(res.items()):
        if df is None or df.empty:
            fp[name] = (0, 0.0); continue
        icols = [c for c in df.columns if isinstance(c, str) and c.startswith("Intensity")]
        if icols:
            vals = df[icols].apply(pd.to_numeric, errors="coerce")
            total = float(vals.to_numpy(float).sum())
        else:
            total = 0.0
        fp[name] = (len(df), round(total, 3))
    return fp


if __name__ == "__main__":
    work = sys.argv[1]
    options = build_options(work)

    from lx.spectraImport import getInputFiles
    from lx.batch_processor import build_master_scan

    listFiles, _, _ = getInputFiles(work, options)
    sample_path, entry_name = str(listFiles[0][0]), listFiles[0][1]
    print(f"### sample: {os.path.basename(sample_path)}", flush=True)

    qset = os.environ.get("QSET", "all")
    std = sorted(glob.glob(os.path.join(BENCH, "MFQL", "negative_standards", "*.mfql")))
    lip = sorted(glob.glob(os.path.join(BENCH, "MFQL", "negative_lipids", "*.mfql")))
    qpaths = {"standards": std, "lipids": lip, "all": std + lip}[qset][:NQ]
    print(f"### {len(qpaths)} queries", flush=True)

    base = build_master_scan(sample_path, entry_name, options)
    print("### MasterScan built", flush=True)

    results = {}
    for tag, qs, single in (("A_sorted", qpaths, False),
                            ("B_reversed", list(reversed(qpaths)), False),
                            ("C_onecall", qpaths, True)):
        scan = copy.deepcopy(base)
        results[tag] = fingerprint(run_queries(scan, qs, options, single))
        print(f"### {tag} done", flush=True)

    print("\n### value multisets (rows,total) -- naming differs between modes:")
    for tag, fp in results.items():
        vals = sorted(tuple(v) for v in fp.values())
        print(f"###   {tag}: {vals}", flush=True)

    with open(os.path.join(work, "order_test.json"), "w") as fh:
        json.dump({k: {n: list(v) for n, v in fp.items()} for k, fp in results.items()}, fh, indent=1)
    print("### wrote order_test.json", flush=True)
