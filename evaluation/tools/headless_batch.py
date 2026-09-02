"""Run LipidXplorer batch mode headlessly, using the GUI's own option-building code.

Usage: headless_batch.py <import_dir> <out_tag> [n_cores]

Reuses LpdxFrame.collectSettings / readOptions_batch via a stub so the options
are built exactly as the GUI builds them, rather than reimplemented here.
"""
import configparser, os, sys, json, glob

sys.path.insert(0, os.environ.get("LX_ROOT", "/Users/nilshoffmann/Projects/github.com/lifs-tools/lipidxplorer"))

BENCH = "/Users/nilshoffmann/Downloads/1.5-benchmark-data"
INI = os.path.join(BENCH, "lpdxImportSettings_LIFS_Course.ini")
SECTION = "240821_mice_lung_neg"
MFQL_DIRS = [os.path.join(BENCH, "MFQL", "negative_standards"),
             os.path.join(BENCH, "MFQL", "negative_lipids")]

import_dir = sys.argv[1]
tag = sys.argv[2]
n_cores = int(sys.argv[3]) if len(sys.argv) > 3 else 4

import lx.gui.lpdxGUI as G
from lx.project import Project
from lx.batch_processor import run_batch



def main():
    class _Ctrl:
        def __init__(self, v): self._v = v
        def GetValue(self): return self._v


    class Stub:
        """Carries just the attributes collectSettings/readOptions_batch touch."""
        def __init__(self):
            self.confParse = configparser.ConfigParser()
            self.confParse.read(INI)
            self.currentConfiguration = SECTION
            self.text_ctrl_ImportDataSection = _Ctrl(import_dir)
            self.combo_ctrl_ImportDataSection = _Ctrl("mzML")
            self.text_ctrl_OutputMasterScanSection = _Ctrl(INI)


    stub = Stub()
    assert stub.confParse.has_section(SECTION), f"section {SECTION} not in {INI}"
    G.LpdxFrame.collectSettings(stub, SECTION)
    project = G.LpdxFrame.readOptions_batch(stub)

    options = project.options
    options["batch_mode"] = True
    options["importMSMS"] = True
    options["spectraFormat"] = "mzML"
    options["masterScanImport"] = INI
    options["resultFile"] = INI
    options["savePerSample"] = True

    project.testOptions()
    project.formatOptions()
    options = project.getOptions()

    queries = []
    for d in MFQL_DIRS:
        for p in sorted(glob.glob(os.path.join(d, "*.mfql"))):
            queries.append({"name": os.path.basename(p), "path": p})
    if os.environ.get("QORDER") == "reversed":
        queries.reverse()

    print(f"### run tag={tag} cores={n_cores} queries={len(queries)} dir={import_dir}",
          file=sys.stderr)

    summary = run_batch(
        options, queries,
        n_cores=n_cores,
        occurrence_threshold=0.25,
        log_file=os.path.join(import_dir, f"batch_log_{tag}.txt"),
    )
    print("### summary:", json.dumps(summary, default=str), file=sys.stderr)

    # Preserve this run's outputs under the tag so repeat runs do not clobber.
    for src in glob.glob(os.path.join(import_dir, "batch_results_*.csv")):
        if f"_{tag}" in src:
            continue
        dst = src.replace(".csv", f"__{tag}.csv")
        os.replace(src, dst)
        print("### kept", dst, file=sys.stderr)
    psr = os.path.join(import_dir, "per_sample_results")
    if os.path.isdir(psr):
        os.replace(psr, psr + f"__{tag}")


if __name__ == "__main__":
    main()
