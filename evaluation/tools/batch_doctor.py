"""Batch-mode diagnostic. Run on the machine where batch mode fails.

    uv run python batch_doctor.py /path/to/import/dir mzML

Walks the same boundaries lx.batch_processor.run_batch crosses and reports
which one breaks, instead of letting the GUI logger swallow the error.
"""
import os, sys, time, traceback, multiprocessing as mp

def hdr(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70, flush=True)

def _probe(_):
    """Runs in a spawned worker: the imports process_sample actually needs."""
    import os
    r = {"pid": os.getpid(), "frozen": getattr(sys, "frozen", False)}
    try:
        from lx.spectraImport import doImport, lpdxImportDEF_new, getInputFiles
        from lx.mfql.runtimeExecution import TypeMFQL
        from lx.mfql.mfqlParser import startParsing
        import lx.batch_processor
        r["imports"] = "OK"
    except Exception:
        r["imports"] = traceback.format_exc()
    try:
        from lx.mfql.calcsf_cached import __dict__ as _
        import numba  # noqa
        r["numba"] = "OK"
    except Exception:
        r["numba"] = traceback.format_exc()
    return r

def main():
    hdr("ENVIRONMENT")
    print("platform      :", sys.platform)
    print("executable    :", sys.executable)
    print("frozen        :", getattr(sys, "frozen", False))
    print("_MEIPASS      :", getattr(sys, "_MEIPASS", None))
    print("cwd           :", os.getcwd())
    print("__main__.file :", getattr(sys.modules["__main__"], "__file__", None))
    print("start method  :", mp.get_start_method(allow_none=True))
    print("cpu_count     :", mp.cpu_count())

    hdr("RESOURCE DIR WRITABILITY  (lpdxGUI writes lpdxopts.ini here at startup)")
    try:
        from lx.gui.lpdxGUI import get_resource_dir, get_runtime_dir
        rd = get_resource_dir()
        print("resource_dir  :", rd)
        print("runtime_dir   :", get_runtime_dir())
        print("writable      :", os.access(rd, os.W_OK))
        for f in ("lpdxopts.ini", "lpdxImportSettings_benchmark.ini"):
            p = rd / f
            print(f"  {f}: exists={p.exists()} writable={os.access(p, os.W_OK) if p.exists() else 'n/a'}")
    except Exception:
        traceback.print_exc()

    hdr("SPAWN POOL + WORKER IMPORTS")
    try:
        t0 = time.time()
        ctx = mp.get_context("spawn")
        with ctx.Pool(processes=2) as pool:
            for r in pool.imap_unordered(_probe, range(2)):
                print(f"worker pid={r['pid']} frozen={r['frozen']}")
                print("  lx imports:", r["imports"] if r["imports"] == "OK" else "\n" + r["imports"])
                print("  numba     :", r["numba"] if r["numba"] == "OK" else "\n" + r["numba"])
        print("POOL OK in %.1fs" % (time.time() - t0))
    except Exception:
        print("POOL FAILED:")
        traceback.print_exc()

    if len(sys.argv) > 2:
        import_dir, fmt = sys.argv[1], sys.argv[2]
        hdr(f"SAMPLE DISCOVERY  getInputFiles({import_dir!r}, {fmt!r})")
        try:
            from lx.spectraImport import getInputFiles
            listFiles, isTaken, isGroup = getInputFiles(import_dir, {"spectraFormat": fmt})
            print(f"found {len(listFiles)} sample(s); isTaken={isTaken} isGroup={isGroup}")
            for e in listFiles[:10]:
                print("   ", e)
        except Exception:
            traceback.print_exc()

        hdr("OUTPUT DIR WRITABILITY")
        from pathlib import Path
        d = Path(import_dir).resolve() / "per_sample_results"
        try:
            d.mkdir(parents=True, exist_ok=True)
            (d / ".probe").write_text("x"); (d / ".probe").unlink()
            print("writable:", d)
        except Exception:
            traceback.print_exc()
    else:
        print("\n(pass an import dir + format to also test sample discovery)")

if __name__ == "__main__":
    mp.freeze_support()
    main()
