## lx/batch_processor.py ######### Ballal #########

import os
import time
import traceback
from pathlib import Path

from typing import Any, Dict, List, Optional
import pandas as pd
import gc  # For manual memory cleanup
import copy
import io
import re
import csv
import numpy as np
import subprocess
import pickle
import sys
import multiprocessing as mp
from lx.spectraImport import doImport
from lx.spectraImport import lpdxImportDEF_new
from lx.spectraImport import getInputFiles
from lx.exceptions import LipidXException
from lx.options import Options, optionsDict

from lx.mfql.runtimeExecution import TypeMFQL
from lx.mfql.mfqlParser import startParsing
from lx.tools import odict

import shutil
import warnings

# ===========================================================================
# --- ADDED FOR UNIFIED LOGGING (Workers + Batch Controller)
# ===========================================================================
from lx.logger import TeeLogger
import builtins
LOGGER = None   # Will be set by run_batch()
# ===========================================================================


class _WorkerLog:
    """Line-buffered sink that appends a worker's output to the batch log.

    Partial writes are buffered until a newline arrives so that a line
    assembled from several stdout fragments is timestamped once, in the same
    format TeeLogger uses, rather than once per fragment.

    The handle is opened once and held. It used to be opened and closed per
    line, which was affordable only as long as the log stayed small -- and
    in verbose mode it does not, since sys.stdout and sys.stderr are routed
    here as well and it then carries everything doImport, readSpectra and
    the MFQL interpreter print (~750 lines per sample). Reopening a file
    every worker is appending to costs ~70us on APFS, and more on Windows,
    where an on-access scanner runs on each open. An isolated benchmark (11
    processes, 8250 lines) puts the per-line open at 0.57s against 0.17s for
    a held handle; no end-to-end speedup is claimed.

    Each line is written and flushed in one call, so it still lands whole:
    on both POSIX and Windows an O_APPEND write this small is atomic, which
    is what keeps several workers from interleaving mid-line.
    """

    def __init__(self, log_file, context=""):
        self._log_file = log_file
        self._context = context
        self._buffer = ""
        self._handle = None

    def _open(self):
        """Return the shared log handle, opening it on first use.

        Returns None if the log cannot be opened at all -- a worker has to
        finish its sample either way.
        """
        if self._handle is None:
            try:
                self._handle = open(self._log_file, "a", encoding="utf-8")
            except Exception:
                return None
        return self._handle

    def write(self, data):
        if not data:
            return
        self._buffer += data
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            self._emit(line)

    def _emit(self, line):
        if not line.strip():
            return
        handle = self._open()
        if handle is None:
            return
        stamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
        prefix = f"{stamp} {self._context}" if self._context else stamp
        try:
            handle.write(f"{prefix} {line}\n")
            handle.flush()
        except Exception:
            # A worker must finish its sample even if the log has gone away.
            # Drop the handle so a later line can try to reopen it.
            self._handle = None

    def flush(self):
        if self._buffer:
            line, self._buffer = self._buffer, ""
            self._emit(line)

    def close(self):
        """Flush and release the handle; a later write reopens it."""
        self.flush()
        if self._handle is not None:
            try:
                self._handle.close()
            except Exception:
                pass
            self._handle = None


def _worker_context(sample_id):
    """Build the diagnostic context stamped onto this worker's log lines.

    Pool workers are reused across samples, so the label names both the
    worker -- stable for the life of the process -- and the sample it is
    working on right now. multiprocessing already names its pool children
    'SpawnPoolWorker-3'; shorten that to 'W3' to keep the prefix narrow.
    """
    name = mp.current_process().name
    match = re.search(r"(\d+)$", name)
    worker = f"W{match.group(1)}" if match else name
    return f"[{worker} {sample_id}]"


def _install_worker_logging(log_file, context="", verbose=False):
    """Give this worker process a sink that appends to the shared batch log.

    Workers are started with the 'spawn' method, so they get a fresh
    interpreter: they do not inherit the TeeLogger that the GUI installs over
    builtins.print, and in a windowed PyInstaller bundle their stdout and
    stderr go to a null sink. Without a sink here, every progress line and
    every traceback raised inside a worker is discarded, and the GUI shows
    nothing between "Using N worker process(es)" and the first completed
    sample.

    `context` is prepended to every line, so lines from several workers
    interleaved in one log stay attributable.

    `verbose` additionally redirects builtins.print, sys.stdout and
    sys.stderr into the sink, which catches output from the deeper code path
    -- doImport, readSpectra, the MFQL interpreter -- none of which knows a
    batch is running. Measured at ~750 lines per sample against ~35 for the
    worker's own progress -- 8742 lines against 486 over a 12-sample run --
    so it is off unless asked for. That is for readability: back to back on
    an idle machine the two modes timed 118.29s and 120.15s, i.e. the same.

    Returns the sink, or None when no log file was configured (running
    head-less from a script, say).
    """
    if not log_file:
        return None

    sink = _WorkerLog(log_file, context=context)

    if verbose:
        sys.stdout = sink
        sys.stderr = sink

        def worker_print(*args, **kwargs):
            sink.write(" ".join(str(a) for a in args) + "\n")

        builtins.print = worker_print

    return sink



# ============================================================
# Real LipidXplorer implementations (Batch-safe)
# ============================================================
def build_master_scan(sample_path: str, sample_entry_name: str, options: dict):
    """
    Create a MasterScan in memory for one sample using LipidXplorer's
    normal import pipeline, but skip directory scanning and saving.

    sample_path:
        - mzML mode   -> full file path
        - dta/csv mode -> full sample directory path

    sample_entry_name:
        The second value returned by getInputFiles(), preserved exactly
        so doImport() gets the same structure as normal import mode.
    """
    print(f"[build_master_scan] Building MasterScan for {sample_path}", flush=True)

    listIntermission = lpdxImportDEF_new(
        parent=None,
        options=options
    )

    # Patch the file list so we only import one sample
    # Keep exactly the same [path, name] shape as normal getInputFiles() output
    listIntermission = (
        listIntermission[0],
        listIntermission[1],
        listIntermission[2],
        listIntermission[3],
        listIntermission[4],
        [[sample_path, sample_entry_name]],
        True,
        False,
    )

    doImport(
        listIntermission[0],
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
        options['importMSMS']
    )

    print("[build_master_scan] MasterScan built successfully.", flush=True)
    return listIntermission[1]



# "QUERYNAME = <name>;" at the start of a line of an MFQL file (lines starting
# with '#' are comments and cannot match). Used to tell which MFQL file a
# result row came from (see run_mfql_on_scan). The name pattern is the one
# the MFQL lexer accepts for an ID (t_ID in mfqlParser.py).
_QUERYNAME_RE = re.compile(r"^[ \t]*QUERYNAME\s*=\s*([A-Za-z$][A-Za-z$0-9]*)",
                           re.IGNORECASE | re.MULTILINE)


def run_mfql_on_scan(scan, queries, options):
    """
    Run ALL MFQL queries against one MasterScan in a single startParsing()
    call -- the same way normal mode (lxMain.startMFQL) runs them.

    Why one call and not one call per query
    ---------------------------------------
    startParsing() first identifies the lipids of every query it is given,
    then applies the isotopic corrections ONCE to the MasterScan, then writes
    the reports. Calling it once per query on the same MasterScan (as batch
    mode used to) repeats the isotopic corrections for every query, and each
    query sees the intensities already modified by the queries before it.
    The result then depended on how many queries ran and in which order.
    One call per sample removes that and matches normal mode's MFQL
    semantics. (Batch and normal mode still differ in one way by design:
    batch mode builds one MasterScan per sample, normal mode one MasterScan
    with all samples aligned together.)

    Args:
        scan:    the MasterScan of one sample
        queries: list of {"name": <MFQL file name>, "path": <full path>},
                 already in the fixed order set by run_batch()
        options: options dict

    Returns:
        DataFrame with all result rows of all queries, plus two columns:
          - query_name: the QUERYNAME declared inside the MFQL
          - mfql_file:  the MFQL file name the row came from; the merge uses
                        it to keep sub-classes of one LipidClass (e.g. PC and
                        PC O-) in separate blocks.

    A syntax or runtime error in any MFQL raises and fails the whole sample
    (as in normal mode). There is deliberately no per-query fallback: it
    would silently bring back the order-dependent results described above.
    """

    # Read all MFQL texts. The odict keeps the order of `queries`, so the
    # queries are parsed and identified in that fixed order. The key is the
    # file name; startParsing() uses it as mfqlObj.filename in its error
    # messages, so an error names the offending file.
    mfqlFiles = odict()
    queryname_to_file = {}
    for q in queries:
        with open(q["path"], "r", encoding="utf-8") as f:
            q_text = f.read()
        mfqlFiles[q["name"]] = q_text

        # MFQL allows exactly one query per file, so QUERYNAME -> file name
        # is a 1:1 map. It is needed because the result object is keyed by
        # QUERYNAME, not by file name.
        m = _QUERYNAME_RE.search(q_text)
        if m:
            queryname_to_file[m.group(1)] = q["name"]

    mfqlObj = TypeMFQL(masterScan=scan)
    mfqlObj.options = options

    for key in list(mfqlObj.sc.options.keys()):
        if key in Options.importOptions:
            try:
                if not mfqlObj.sc.options.isEmpty(key):
                    mfqlObj.options[key] = mfqlObj.sc.options[key]
            except Exception:
                continue

    mfqlObj.outputSeperator = '\t' if options.get('tabLimited') else ','

    startParsing(
        mfqlFiles,
        mfqlObj,
        scan,
        isotopicCorrectionMS=options.get('isotopicCorrectionMS', True),
        isotopicCorrectionMSMS=options.get('isotopicCorrectionMSMS', True),
        complementSC=options.get('complementMasterScan', False),
        parent=None,
        progressCount=0,
        generateStatistics=options.get('statistics', False)
    )

    result = mfqlObj.result
    if not getattr(result, "mfqlOutput", False):
        del mfqlObj
        return pd.DataFrame()

    header = list(result.listHead) if hasattr(result, "listHead") else None

    dfs = []
    for qres in result.dictQuery.values():
        text = qres.strOutput.strip()
        if not text:
            continue

        buf = io.StringIO(text)
        if header:
            df_block = pd.read_csv(buf, sep=mfqlObj.outputSeperator, names=header, header=None)
        else:
            df_block = pd.read_csv(buf, sep=mfqlObj.outputSeperator)

        df_block["query_name"] = qres.name
        # Map the QUERYNAME back to its MFQL file; fall back to the
        # QUERYNAME itself if the file could not be identified.
        df_block["mfql_file"] = queryname_to_file.get(qres.name, qres.name)
        dfs.append(df_block)

    df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

    try:
        del result.dictQuery
        del result
        del mfqlObj
    except:
        pass

    return df




##################### for testing #######################
# def process_sample(args):
#     sample_path, sample_id, sample_entry_name, options, queries, out_dir = args
#     print(f"[PID] test build scan {sample_id}", flush=True)
#     scan = build_master_scan(sample_path, sample_entry_name, options)
#     del scan
#     return {"sample_id": sample_id, "status": "OK", "path": None}

#################################


# ============================================================
# Worker: executes per-sample file
# ============================================================
def process_sample(args: tuple) -> Dict[str, Any]:
    """
    Worker function for one sample.

    Args (tuple):
        sample_path: input path for one sample
                     - mzML mode   -> mzML file path
                     - dta/csv mode -> sample directory path
        sample_id: sample name used for output CSV naming
        sample_entry_name: second value from getInputFiles()
        options:   options dict (will be deep-copied in worker)
        queries:   list of {"name": ..., "path": ...} MFQL queries
        out_dir:   directory where per-sample CSVs are written
        log_file:  shared batch log this worker appends its progress to

    Returns:
        dict with fields:
            - sample_id
            - status: "OK" or "ERROR"
            - path: path to per-sample CSV (or None)
            - error: error message (if any)
    """

    sample_path, sample_id, sample_entry_name, options, queries, out_dir, log_file = args

    # Must come first: everything below reports through log(), which is
    # otherwise discarded in a spawned worker (see _install_worker_logging).
    # The context makes every line attributable to this worker and sample.
    # verboseWorkerLog additionally captures the library chatter from
    # doImport and the MFQL interpreter; it is off by default because that
    # is ~750 lines per sample against the six this function writes.
    sink = _install_worker_logging(
        log_file,
        _worker_context(sample_id),
        verbose=bool(options.get("verboseWorkerLog", False)),
    )

    def log(message):
        """This worker's own progress -- always logged, verbose or not."""
        if sink:
            sink.write(str(message) + "\n")
        else:
            print(message, flush=True)

    # Per-worker deep copy so processes don't share mutable state
    import copy as _copy
    options = _copy.deepcopy(options)

    pid = os.getpid()
    t0 = time.time()
    # The pid is recorded once here rather than on every line: the context
    # prefix already identifies the worker, and this is enough to tie it to
    # a process in `ps` when someone needs that.
    log(f"START pid={pid} file='{sample_path}' ({len(queries)} queries)")

    try:
        # -----------------------------------------------------------
        # Build MasterScan
        # -----------------------------------------------------------
        log(f"Building MasterScan for '{sample_id}'")
        scan = build_master_scan(sample_path, sample_entry_name, options)
        log(f"MasterScan READY for '{sample_id}'")

        # -----------------------------------------------------------
        # Run all MFQL queries on this scan -- in ONE startParsing() call,
        # as normal mode does (see run_mfql_on_scan for why).
        # An error in any MFQL propagates to the outer except below and
        # fails this sample with the full traceback; the message names the
        # MFQL file. It is not caught per query on purpose.
        # -----------------------------------------------------------
        log(f"Running {len(queries)} MFQL(s) on '{sample_id}': "
            + ", ".join(q["name"] for q in queries))
        df = run_mfql_on_scan(scan, queries, options)

        if df is None or df.empty:
            df = pd.DataFrame()
        else:
            df["sample_id"] = sample_id
            # One line per MFQL with its row count, so the log still shows
            # which queries produced hits.
            counts = df["mfql_file"].value_counts()
            for q in queries:
                n_rows = int(counts.get(q["name"], 0))
                if n_rows:
                    log(f"MFQL '{q['name']}': {n_rows} row(s)")
                else:
                    log(f"No hits for MFQL '{q['name']}' on '{sample_id}'")
        all_hits = None  # kept so the cleanup below stays unchanged

        duration = time.time() - t0
        log(f"FINISHED MFQL for '{sample_id}' in {duration:.2f}s ({len(df)} rows)")

        # -----------------------------------------------------------
        # Write per-sample CSV (only if there are hits)
        # -----------------------------------------------------------
        if df.empty:
            out_path = None
            log(f"No hits for '{sample_id}', no CSV written.")
        else:
            out_dir_path = Path(out_dir)
            out_dir_path.mkdir(parents=True, exist_ok=True)
            out_path = out_dir_path / f"{sample_id}.csv"
            df.to_csv(out_path, index=False)
            log(f"Wrote per-sample CSV '{out_path}'")

        # Cleanup big objects
        try:
            del scan, all_hits, df
        except Exception:
            pass
        gc.collect()

        log(f"DONE sample='{sample_id}'")
        if sink:
            sink.close()
        return {
            "sample_id": sample_id,
            "status": "OK",
            "path": str(out_path) if out_path else None
        }

    except Exception as e:
        log(f"FATAL ERROR in sample '{sample_id}': {e}")
        log(traceback.format_exc())
        if sink:
            sink.close()
        return {
            "sample_id": sample_id,
            "status": "ERROR",
            "path": None,
            # Carried back to the controller so the GUI can show why this
            # sample failed instead of a bare "ERROR".
            "error": traceback.format_exc()
        }


# ============================================================
# Deterministic ordering of samples and MFQL queries
# ============================================================
#
# Why this exists
# ---------------
# Both input lists used to arrive in whatever order the filesystem returned:
#   - samples come from getInputFiles(), which uses os.walk() unsorted;
#   - MFQL queries come from the GUI / lxrun.py, which also use os.walk().
# NTFS returns directory entries alphabetically, ext4 and APFS do not, so
# the same data and the same MFQL folder were processed in a different
# order on Windows, Linux and macOS. That order is not cosmetic:
#   - merge_lipid_results() takes Mass, PrecursorERRppm, FragmentAERRppm and
#     the other non-intensity columns from the FIRST sample (in sample
#     order) that contains the lipid;
#   - every MFQL query of one sample runs against the same MasterScan
#     object, and the queries mutate it (marks, isotope corrections), and the
#     per-sample de-duplication in the merge keeps the FIRST row of a
#     species, i.e. the one from the query that ran first.
# Sorting both lists here, in the one place every batch run goes through,
# makes the result independent of OS and filesystem.
#
# The rule is plain alphabetical order by file name (Python string order,
# i.e. by code point). It is identical on every OS as long as the file
# names are identical, which is all that is needed. Note that it is
# case-sensitive, so it can differ slightly from what Windows Explorer
# shows; that is fine -- it only has to be the same everywhere.

# A sample whose file name contains this word (in any capitalisation) is
# treated as a blank and moved behind all other samples. Blanks carry little
# or no signal, so they should never be the "first sample" the merge takes
# Mass and the error columns from. If the word is not in the file name,
# a blank cannot be recognised and is sorted like any other sample.
_BLANK_MARKER = "blank"


def _is_blank_sample(file_name: str) -> bool:
    """Return True if the sample file name marks it as a blank.

    The check is case-insensitive ('Blank', 'BLANK', 'blank' all match) and
    looks for the word anywhere in the name, e.g. '240506_Blank_49932_a'.
    """
    return _BLANK_MARKER in file_name.casefold()


def _sample_sort_key(sample_path: str):
    """Sort key for one sample path (an mzML file, or a sample directory
    in dta/csv mode).

    Order of the tuple elements, most significant first:
      1. blanks last  -- False sorts before True;
      2. the file/directory name, alphabetically;
      3. the remaining path components as a tie-break, for the rare case of
         two samples with the same name in different sub-folders. Path.parts
         is used instead of the path string so that '\\' on Windows and '/'
         elsewhere cannot change the order.
    """
    p = Path(sample_path)
    return (_is_blank_sample(p.name), p.name, p.parts)


def _query_sort_key(query: Dict[str, str]):
    """Sort key for one MFQL query entry {"name": ..., "path": ...}.

    Sorted alphabetically by the query (file) name; the path components
    break ties, should two entries ever share a name.
    """
    return (query["name"], Path(query["path"]).parts)


# ============================================================
# Controller: manages pool + collects + merges
# ============================================================
def run_batch(
    options: dict,
    queries: list,
    n_cores: Optional[int] = None,
    occurrence_threshold: Optional[float] = None,
    log_file: Optional[str] = None,
):
    """
    Batch controller:
      1) Find input samples using getInputFiles().
      2) Process in parallel using a multiprocessing Pool.
      3) Each worker writes its per-sample CSV to disk and returns only
         small metadata (sample_id, status, path).
      4) The parent streams results with imap_unordered so it never
         holds all worker outputs in memory at once.
      5) Collect paths of CSVs with hits.
      6) Merge via merge_lipid_results().
      7) Save final batch_results.csv.
      8) Optionally keep or delete per-sample CSVs depending on
         options["savePerSample"].

    Samples and MFQL queries are processed in a fixed alphabetical order
    (blanks last), independent of the OS -- see _sample_sort_key() and
    _query_sort_key().
    """

    # Simple log helper. If the GUI installs a TeeLogger as print(),
    # these messages will go to the GUI + file automatically.
    def log(*a):
        print(" ".join(str(x) for x in a), flush=True)

    import_dir = Path(options.get("importDir", "")).resolve()
    spectra_format = options.get("spectraFormat", "")

    # -----------------------------------------------------------
    # Fix the MFQL query order (alphabetical by name).
    # The callers build this list from os.walk(), whose order depends on the
    # filesystem; every worker runs the queries in exactly this list order.
    # sorted() returns a new list, so the caller's list is not modified.
    # -----------------------------------------------------------
    queries = sorted(queries, key=_query_sort_key)

    # -----------------------------------------------------------
    # Find all samples using normal import discovery logic
    # -----------------------------------------------------------
    listFiles, isTaken, isGroup = getInputFiles(str(import_dir), options)

    if not listFiles:
        log(f"No input samples found in {import_dir} for format '{spectra_format}'")
        return {}

    # Fix the sample order (alphabetical by name, blanks last).
    # getInputFiles() returns the os.walk() order, which differs between
    # NTFS, ext4 and APFS. The task list, and with it the column order and
    # the "first sample" used by merge_lipid_results(), follow this order.
    listFiles = sorted(listFiles, key=lambda entry: _sample_sort_key(str(entry[0])))

    log(f"Found {len(listFiles)} input sample(s) for batch processing (format={spectra_format}).")

    # Record the resolved orders once, so any run can be checked from its
    # log alone against a run on another machine.
    log("Sample order: " + ", ".join(Path(str(e[0])).name for e in listFiles))
    log("MFQL order: " + ", ".join(q["name"] for q in queries))

    # Directory where workers will store per-sample CSVs
    per_sample_dir = import_dir / "per_sample_results"
    per_sample_dir.mkdir(parents=True, exist_ok=True)

    save_per_sample = bool(options.get("savePerSample", False))

    # -----------------------------------------------------------
    # Build tasks (one sample per worker call)
    # -----------------------------------------------------------
    tasks = []

    for entry in listFiles:
        sample_path = str(entry[0])
        sample_entry_name = entry[1]

        # Keep old mzML naming behavior for output CSVs and merge order
        if spectra_format == "dta/csv":
            sample_id = Path(sample_path).name
        else:
            sample_id = Path(sample_path).stem

        tasks.append(
            (sample_path, sample_id, sample_entry_name, options, queries, str(per_sample_dir), log_file)
        )

    log(f"Using {n_cores} worker process(es)")

    sample_csv_paths: List[str] = []
    n_total = len(tasks)
    n_done = 0
    n_ok = 0
    n_empty = 0
    n_err = 0

    start = time.time()

    # -----------------------------------------------------------
    # Run multiprocessing Pool with 'spawn' context
    # -----------------------------------------------------------
    ctx = mp.get_context("spawn")

    with ctx.Pool(processes=n_cores) as pool:
        for r in pool.imap_unordered(process_sample, tasks, chunksize=1):
            status = r.get("status")
            path = r.get("path")
            sid = r.get("sample_id")
            n_done += 1

            # "no hits" and "the worker raised" used to be reported by the same
            # line, which made a broken sample indistinguishable from an empty
            # one. Keep them apart, and print the error when there is one.
            if status == "OK" and path:
                sample_csv_paths.append(path)
                n_ok += 1
                log(f"({n_done}/{n_total}) OK sample='{sid}' path='{path}'")
            elif status == "OK":
                n_empty += 1
                log(f"({n_done}/{n_total}) no hits for sample='{sid}'")
            else:
                n_err += 1
                log(f"({n_done}/{n_total}) FAILED sample='{sid}':\n"
                    f"{r.get('error') or 'no error detail returned'}")

    duration = time.time() - start
    log(f"All samples processed in {duration:.2f}s "
        f"({n_ok} with hits, {n_empty} without hits, {n_err} failed)")

    if not sample_csv_paths:
        log("No valid per-sample results found.")
        # Nothing was written, so the directory created above is empty. Leaving
        # it behind contradicts the unticked "Save per sample result" box.
        if not save_per_sample:
            shutil.rmtree(per_sample_dir, ignore_errors=True)
        return {}

    # -----------------------------------------------------------
    # imap_unordered() returns results in completion order, which depends on
    # timing. Put the per-sample CSVs back into task (= sorted sample) order
    # so the merge never sees a timing-dependent order. For mzML the merge
    # reorders by mzml_files anyway; for dta/csv (mzml_files=None) this is
    # the only thing that fixes the order.
    # -----------------------------------------------------------
    task_index = {t[1]: i for i, t in enumerate(tasks)}  # sample_id -> position
    sample_csv_paths.sort(key=lambda p: task_index.get(Path(p).stem, len(task_index)))

    # -----------------------------------------------------------
    # Merge per-sample CSVs into one final table
    # Keep old merge behavior for mzML ordering compatibility.
    # For dta/csv, there is no mzML file list, so pass None.
    # -----------------------------------------------------------
    log("Merging per-sample results...")

    if spectra_format == "dta/csv":
        merge_reference_files = None
    else:
        merge_reference_files = [Path(t[0]) for t in tasks]

    final_df, polarity = merge_lipid_results(
        sample_csv_paths,
        mzml_files=merge_reference_files,
        occurrence_threshold=occurrence_threshold
    )



    # Output path for the final batch results
    batch_result_path = import_dir / f"batch_results_{polarity[0]}.csv"
    final_df.to_csv(batch_result_path, index=False, encoding="utf-8")
    log(f"Saved merged results to {batch_result_path} ({len(final_df)} rows)")

    # -----------------------------------------------------------
    # Build summary
    # -----------------------------------------------------------
    summary = {
        "processed": len(listFiles),
        "ok": n_ok,
        "errors": len(listFiles) - n_ok,
        # "errors" above lumps empty samples in with failed ones and is kept
        # for callers that already read it; these two report what happened.
        "no_hits": n_empty,
        "failed": n_err,
        "duration_sec": round(duration, 2),
        "cores_used": n_cores,
        "output_file": str(batch_result_path),
        "polarity": polarity[0]
    }

    # -----------------------------------------------------------
    # Cleanup per-sample CSVs if user does NOT want to keep them
    # -----------------------------------------------------------
    if save_per_sample:
        log(f"Saved {len(sample_csv_paths)} per-sample CSVs in {per_sample_dir}.")
    else:
        log("User does not want to keep per-sample results. Deleting temporary CSVs...")
        shutil.rmtree(per_sample_dir, ignore_errors=True)
        # The per-sample paths logged above pointed into that directory, so say
        # so rather than leaving a log full of files that no longer exist.
        log(f"Removed {per_sample_dir}; the per-sample CSV paths logged above "
            f"no longer exist. Merged results are in {batch_result_path}.")

    gc.collect()

    log(f"Summary: {summary}")
    return summary





# The merge_lipid_results()
# -------------------------------------------------------------------

def merge_lipid_results(sample_files, mzml_files=None, occurrence_threshold=None):
    """
    Merge multiple per-sample lipidomics result CSV files into one batch table.

    Required input columns per CSV
    ------------------------------
    Required:
        - LipidSpecies

    Strongly recommended:
        - LipidClass
        - Mass
        - ScanPolarity
        - Intensity

    Parameters
    ----------
    sample_files : list-like
        Paths to per-sample lipidomics CSV result files.

    mzml_files : list-like, optional
        Paths to mzML files. If given, CSV files are ordered according to the
        mzML file stem names.

    occurrence_threshold : float, optional
        Fraction of samples in which a lipid must have Intensity > 0.
        Example:
            0.5 means lipid must appear in at least 50% of samples.

    Returns
    -------
    final_df : pandas.DataFrame
        Merged lipidomics result table.

    polarity : numpy.ndarray
        Unique non-null ScanPolarity values, if available.
    """

    # Optional pandas setting to avoid future silent downcasting behavior
    try:
        pd.options.future.no_silent_downcasting = True
    except Exception:
        pass

    # ------------------------------------------------------------
    # Helper: detect CSV delimiter
    # ------------------------------------------------------------
    def detect_delimiter(path):
        with open(path, "rb") as f:
            sample = f.read(4096)

        text = sample.decode("utf-8-sig", errors="replace")

        # A fixed-size read almost always stops mid-line, and the short line
        # that leaves behind has a different field count from the rest, which
        # is exactly what Sniffer's consistency check rejects. Rows here run
        # to several hundred characters, so this failed for *every* file and
        # warned on each one. Feed the sniffer whole lines only.
        lines = text.splitlines(keepends=True)
        if len(lines) > 1 and not lines[-1].endswith("\n"):
            text = "".join(lines[:-1])

        try:
            # csv.Sniffer wants the candidates as one string of characters.
            # The list this used to pass happens to work -- the parameter is
            # only ever used in `char in delimiters` tests -- but it violates
            # the documented signature and type checkers flag it.
            return csv.Sniffer().sniff(
                text,
                delimiters=",;\t|"
            ).delimiter
        except Exception:
            warnings.warn(
                f"Could not detect delimiter for {path}. Falling back to comma.",
                UserWarning
            )
            return ","

    # ------------------------------------------------------------
    # Helper: validate required and recommended columns
    # ------------------------------------------------------------
    def validate_columns(df, path):
        required_cols = ["LipidSpecies"]

        recommended_cols = [
            "LipidClass",
            "Mass",
            "ScanPolarity",
            "Intensity"
        ]

        missing_required = [c for c in required_cols if c not in df.columns]
        missing_recommended = [c for c in recommended_cols if c not in df.columns]

        if missing_required:
            raise ValueError(
                f"{path} is missing required columns: {missing_required}. "
                f"Required minimum column: {required_cols}"
            )

        if missing_recommended:
            warnings.warn(
                f"{path} is missing recommended columns: {missing_recommended}. "
                "The merge will continue, but sorting, polarity reporting, or "
                "occurrence filtering may be incomplete.",
                UserWarning
            )

    # ------------------------------------------------------------
    # Prepare file order
    # ------------------------------------------------------------
    sample_files = list(sample_files)

    if not sample_files:
        raise ValueError("No sample files were provided.")

    if mzml_files is not None:
        mzml_stems = [Path(p).stem for p in mzml_files]
        csv_by_stem = {Path(p).stem: p for p in sample_files}

        sample_files = [
            csv_by_stem[stem]
            for stem in mzml_stems
            if stem in csv_by_stem
        ]

        if not sample_files:
            raise ValueError(
                "mzml_files was provided, but none of the mzML stems matched "
                "the CSV file stems."
            )

    # ------------------------------------------------------------
    # Read, validate, deduplicate, and rename sample intensity columns
    # ------------------------------------------------------------
    dfs = []

    for path in sample_files:
        delimiter = detect_delimiter(path)

        try:
            df = pd.read_csv(path, sep=delimiter, encoding="utf-8-sig")
        except Exception:
            raise ValueError(
                f"Failed reading {path} with delimiter {repr(delimiter)}"
            )

        validate_columns(df, path)

        # Remove duplicate lipid species inside each file
        df = df.drop_duplicates(subset=["LipidSpecies"], keep="first")

        # Use file stem as sample ID
        sample_id = Path(path).stem

        # Identify intensity-like columns
        sample_cols = [
            c for c in df.columns
            if re.match(
                r"^(Intensity|PrecursorIntensity|Fragment[A-Z]Intensity)",
                c
            )
        ]

        # Metadata columns are everything else except LipidSpecies
        meta_cols = [
            c for c in df.columns
            if c not in sample_cols and c != "LipidSpecies"
        ]

        # Keep only relevant columns
        keep_cols = ["LipidSpecies"] + meta_cols + sample_cols
        df = df[keep_cols]

        # Add sample-specific suffix to intensity columns
        rename_map = {
            c: f"{c}:{sample_id}.mzML"
            for c in sample_cols
            if ":" not in c
        }

        df = df.rename(columns=rename_map)

        # Use LipidSpecies as join key
        df = df.set_index("LipidSpecies")

        dfs.append(df)

    # ------------------------------------------------------------
    # Merge all samples side-by-side
    # ------------------------------------------------------------
    wide = pd.concat(dfs, axis=1, join="outer")

    # ------------------------------------------------------------
    # Coalesce duplicate metadata columns
    # Example: LipidClass appears once per file; keep first non-null value
    # ------------------------------------------------------------
    coalesced = pd.DataFrame(index=wide.index)

    for col_name in wide.columns.unique():
        block = wide.loc[:, wide.columns == col_name]

        if block.shape[1] == 1:
            coalesced[col_name] = block.iloc[:, 0]
        else:
            filled = block.bfill(axis=1).infer_objects(copy=False)
            coalesced[col_name] = filled.iloc[:, 0]

    # Drop unwanted columns if present
    coalesced = coalesced.drop(
        columns=["query_name", "sample_id"],
        errors="ignore"
    )

    # ------------------------------------------------------------
    # Build logical column order
    # ------------------------------------------------------------
    head_meta = [
        "LipidClass",
        "Mass",
        "IsobaricClass",
        "ChemicalFormula",
        "DerivatizedForm",
        "AdductIon",
        "LipidCategory",
        "ScanPolarity"
    ]

    head_meta = [c for c in head_meta if c in coalesced.columns]

    def sample_block(base):
        cols = []

        for file_path in sample_files:
            sample_id = Path(file_path).stem
            col = f"{base}:{sample_id}.mzML"

            if col in coalesced.columns:
                cols.append(col)

        return cols

    intensity_block = sample_block("Intensity")

    mid_meta = [
        c for c in ["IdentificationLevel", "QuantificationIon"]
        if c in coalesced.columns
    ]

    identifier_block = [
        c for c in [
            "PrecursorIdentifier",
            "FragmentAIdentifier",
            "FragmentBIdentifier",
            "FragmentCIdentifier"
        ]
        if c in coalesced.columns
    ]

    precursor_intensity_block = sample_block("PrecursorIntensity")

    # Fragment intensity columns such as FragmentAIntensity, FragmentBIntensity
    fragment_bases = sorted({
        re.match(r"^(Fragment[A-Z]Intensity)\b", c).group(1)
        for c in coalesced.columns
        if re.match(r"^Fragment[A-Z]Intensity\b", c)
    })

    fragment_blocks = []

    for base in fragment_bases:
        fragment_blocks.extend(sample_block(base))

    tail_meta = [
        c for c in [
            "PrecursorERRppm",
            "FragmentAERRppm",
            "FragmentBERRppm",
            "FragmentCERRppm",
            "FragmentAMass",
            "FragmentBMass",
            "FragmentCMass",
            "FragmentAAdductIon",
            "FragmentBAdductIon",
            "FragmentCAdductIon",
            "FragmentAChemicalFormula",
            "FragmentBChemicalFormula",
            "FragmentCChemicalFormula",
            "NeutralChemicalFormula"
        ]
        if c in coalesced.columns
    ]

    ordered_blocks = (
        head_meta
        + intensity_block
        + mid_meta
        + identifier_block
        + precursor_intensity_block
        + fragment_blocks
        + tail_meta
    )

    remaining = [
        c for c in coalesced.columns
        if c not in ordered_blocks
    ]

    final_cols = [
        c for c in ordered_blocks + remaining
        if c in coalesced.columns
    ]

    coalesced = coalesced[final_cols]

    # ------------------------------------------------------------
    # Restore LipidSpecies as a normal column
    # ------------------------------------------------------------
    df = coalesced.copy()

    df.index.name = "LipidSpecies"
    df = df.reset_index()

    # Preserve original order for internal standards
    df["__orig_pos__"] = np.arange(len(df))

    # ------------------------------------------------------------
    # Convert intensity columns to numeric and fill missing values with 0
    # ------------------------------------------------------------
    intensity_pattern = re.compile(
        r"^(Intensity|PrecursorIntensity|Fragment[A-Z]Intensity):"
    )

    intensity_cols = [
        c for c in df.columns
        if intensity_pattern.match(c)
    ]

    for col in intensity_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ------------------------------------------------------------
    # Apply occurrence filter only to main Intensity columns
    # ------------------------------------------------------------
    if occurrence_threshold is not None:
        if not 0 <= occurrence_threshold <= 1:
            raise ValueError(
                "occurrence_threshold must be between 0 and 1."
            )

        if intensity_block:
            n_positive = (df[intensity_block] > 0).sum(axis=1)
            min_required = int(
                np.ceil(len(intensity_block) * occurrence_threshold)
            )

            before = len(df)
            df = df[n_positive >= min_required].copy()
            after = len(df)

            print(
                f"Occurrence filter removed {before - after} lipids "
                f"(threshold={occurrence_threshold}, "
                f"minimum positive samples={min_required})"
            )
        else:
            warnings.warn(
                "occurrence_threshold was provided, but no Intensity columns "
                "were found. Occurrence filtering was skipped.",
                UserWarning
            )

    # ------------------------------------------------------------
    # Identify internal standards
    # Rows where LipidSpecies starts with IS
    # ------------------------------------------------------------
    is_mask = (
        df["LipidSpecies"]
        .astype(str)
        .str.strip()
        .str.upper()
        .str.startswith("IS")
    )

    is_df = (
        df[is_mask]
        .copy()
        .sort_values("__orig_pos__", kind="mergesort")
    )

    non_is_df = df[~is_mask].copy()

    # ------------------------------------------------------------
    # Sort non-IS lipids
    # Preferred: LipidClass, then the MFQL file, then Mass
    # Fallbacks are used if columns are missing
    #
    # The MFQL file is the sub-class key: PC and PC O- (and any other
    # sub-classes) report the same LipidClass but come from different MFQL
    # files. Sorting by LipidClass and Mass alone interleaved their rows;
    # with the MFQL file in between, each sub-class forms its own block.
    # Within one LipidClass the blocks follow the MFQL file names
    # alphabetically.
    # ------------------------------------------------------------
    sort_cols = []
    ascending = []

    if "LipidClass" in non_is_df.columns:
        sort_cols.append("LipidClass")
        ascending.append(True)

    if "mfql_file" in non_is_df.columns:
        # Rows without a file (per-sample CSVs from an older version) sort
        # together as one sub-class instead of breaking the sort.
        non_is_df["mfql_file"] = non_is_df["mfql_file"].fillna("").astype(str)
        sort_cols.append("mfql_file")
        ascending.append(True)

    if "Mass" in non_is_df.columns:
        non_is_df["Mass"] = pd.to_numeric(
            non_is_df["Mass"],
            errors="coerce"
        )
        sort_cols.append("Mass")
        ascending.append(True)

    sort_cols.append("__orig_pos__")
    ascending.append(True)

    non_is_df = non_is_df.sort_values(
        sort_cols,
        ascending=ascending,
        kind="mergesort"
    )

    # ------------------------------------------------------------
    # Combine IS block first, then sorted lipid classes
    # ------------------------------------------------------------
    ordered = pd.concat(
        [is_df, non_is_df],
        ignore_index=True
    )

    ordered = ordered.drop(columns=["__orig_pos__"], errors="ignore")

    # ------------------------------------------------------------
    # Create grouping column for blank-row separation
    # IS gets its own group at the top
    # ------------------------------------------------------------
    if "LipidClass" in ordered.columns:
        lipid_class_group = ordered["LipidClass"].astype(str)
    else:
        lipid_class_group = pd.Series("Unknown", index=ordered.index)

    # One block per LipidClass AND MFQL file, so sub-classes of one class
    # (PC / PC O-) get their own block. "\x00" cannot occur in a class or
    # file name, so the combined key cannot collide.
    if "mfql_file" in ordered.columns:
        lipid_class_group = (
            lipid_class_group
            + "\x00"
            + ordered["mfql_file"].fillna("").astype(str)
        )

    ordered["__grp__"] = np.where(
        ordered["LipidSpecies"]
        .astype(str)
        .str.strip()
        .str.upper()
        .str.startswith("IS"),
        "__IS__",
        lipid_class_group
    )

    # ------------------------------------------------------------
    # Add one blank row after each group
    # ------------------------------------------------------------
    groups_out = []

    if (ordered["__grp__"] == "__IS__").any():
        g = ordered[ordered["__grp__"] == "__IS__"]
        groups_out.append(g)
        groups_out.append(
            pd.DataFrame(
                [[np.nan] * len(ordered.columns)],
                columns=ordered.columns
            )
        )

    # Blocks in the order the rows were sorted above (LipidClass, MFQL file),
    # i.e. order of first appearance -- not re-sorted as strings, so the
    # block order always matches the row sort.
    class_groups = [
        x for x in pd.unique(ordered["__grp__"].dropna())
        if x != "__IS__"
    ]

    for lipid_class in class_groups:
        g = ordered[ordered["__grp__"] == lipid_class]
        groups_out.append(g)
        groups_out.append(
            pd.DataFrame(
                [[np.nan] * len(ordered.columns)],
                columns=ordered.columns
            )
        )

    if groups_out:
        final_df = pd.concat(groups_out, ignore_index=True)
    else:
        final_df = ordered.copy()

    # mfql_file was only needed to sort and block the rows; it is not part of
    # the result table (query_name and sample_id are dropped earlier for the
    # same reason).
    final_df = final_df.drop(columns=["__grp__", "mfql_file"], errors="ignore")

    # ------------------------------------------------------------
    # Ensure LipidSpecies is first column
    # ------------------------------------------------------------
    cols = final_df.columns.tolist()

    if "LipidSpecies" in cols:
        cols = ["LipidSpecies"] + [
            c for c in cols
            if c != "LipidSpecies"
        ]
        final_df = final_df[cols]

    # ------------------------------------------------------------
    # Extract polarity safely
    # ------------------------------------------------------------
    if "ScanPolarity" in final_df.columns:
        polarity = final_df["ScanPolarity"].dropna().unique()

        if len(polarity) > 1:
            warnings.warn(
                f"Multiple ScanPolarity values found: {polarity}",
                UserWarning
            )
    else:
        polarity = np.array([])
        warnings.warn(
            "ScanPolarity column missing. Returning empty polarity array.",
            UserWarning
        )

    return final_df, polarity
