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
import logging
import json

# numba logs the full intermediate code of every function it compiles
# (calcsf_cached.calcsf: "label 0: args = arg(0, name=args) ...
# $6unpack_sequence ...") as logging.DEBUG messages, from
# numba.core.interpreter and numba.core.transforms. They reach the batch log
# whenever the root logger is at DEBUG level in a worker. Capping numba's own
# logger at WARNING drops exactly these messages; numba warnings and errors
# still get through. This module is imported by every spawned worker before
# it runs a sample, so the cap applies there too.
logging.getLogger("numba").setLevel(logging.WARNING)

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

        original_print = builtins.print

        def worker_print(*args, sep=" ", end="\n", file=None, flush=False):
            # print(..., file=<something else>) must still go to that file.
            # The old version wrote every print() into the log and ignored
            # file=, so text code meant for a file or a StringIO -- e.g.
            # numba's dump_to_string(), which prints the IR line by line
            # ("label 0:", "args = arg(0, name=args) ...") into a StringIO --
            # landed in the batch log instead.
            if file is not None and file is not sink and file is not sys.stdout \
                    and file is not sys.stderr:
                original_print(*args, sep=sep, end=end, file=file, flush=flush)
                return
            sep = " " if sep is None else sep
            end = "\n" if end is None else end
            sink.write(sep.join(str(a) for a in args) + end)

        builtins.print = worker_print

    return sink


def _debug_settings_line():
    """One log line with the settings that make numba print its IR.

    Written once per sample in verbose mode, after the MFQL run, so a log
    that shows numba IR ("label 0: args = arg(0, name=args) ...") also shows
    why: a numba debug setting (env var, .numba_config.yaml) prints it with
    an "IR DUMP" header; a root logger at DEBUG prints it without one.
    """
    def level(name):
        lg = logging.getLogger(name)
        return "%s(effective %s, handlers %d)" % (
            logging.getLevelName(lg.level),
            logging.getLevelName(lg.getEffectiveLevel()),
            len(lg.handlers))

    parts = ["root logger " + level(""), "numba logger " + level("numba")]
    env = {k: v for k, v in os.environ.items() if k.upper().startswith("NUMBA_")}
    parts.append("NUMBA_* env %s" % (env or "none"))
    cfg = sys.modules.get("numba.core.config")
    if cfg is not None:
        flags = {k: getattr(cfg, k, None) for k in
                 ("DEBUG", "DUMP_IR", "DUMP_SSA", "DEBUG_FRONTEND")}
        parts.append("numba config %s" % flags)
    if os.path.exists(".numba_config.yaml"):
        parts.append(".numba_config.yaml in %s" % os.getcwd())
    return "Debug settings: " + "; ".join(parts)



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


def _layout_path(csv_path):
    """<sample>.csv -> <sample>.layout.json (written next to the CSV)."""
    p = Path(csv_path)
    return p.with_name(p.stem + ".layout.json")


def _report_value(value):
    """One REPORT value as text, the way generateReport() writes it ("%s").

    None (e.g. an intensity of a variable that was not found) becomes NaN,
    i.e. an empty cell, instead of the text "None".
    """
    if value is None:
        return np.nan
    return "%s" % (value,)


def _query_result_to_frame(qres, header):
    """The result rows of one query as a DataFrame.

    Built from the row dicts (qres.listReportOut: {REPORT column: value}),
    NOT by parsing qres.strOutput.

    Why not strOutput
    -----------------
    When several queries run in one startParsing() call, generateReport()
    writes every query's rows against ONE shared column list (result.listHead,
    the union of all queries' REPORT columns, in the order the queries first
    used them). It leaves out the separator after the last column of the
    query's own REPORT. If that column is not also the last of the query's
    columns in the shared list - i.e. the query orders its REPORT columns
    differently from a query before it, e.g. FragmentAERRppm after the
    intensities instead of before - the row ends with an extra separator and
    has one field too many. pandas.read_csv(names=header) then turns the first
    field (LipidSpecies) into the row index, every column moves one to the
    left, LipidSpecies holds the LipidClass ("DG"), and the merge collapses
    the whole class into one row. A query run alone is never affected,
    because then the shared list is its own column order.

    Columns are taken in the order of `header` and only if the query
    reported them, so a query no longer gets "None" columns of other queries.
    Columns a row has but `header` does not list are left out, exactly as
    generateReport() leaves them out of strOutput.
    """
    rows = getattr(qres, "listReportOut", None) or []
    if not rows:
        return pd.DataFrame()

    if header:
        present = set()
        for rpt in rows:
            present.update(rpt.keys())
        columns = [c for c in header if c in present]
    else:
        columns = []
        for rpt in rows:
            columns.extend(c for c in rpt.keys() if c not in columns)

    data = [{c: _report_value(rpt[c]) for c in columns if c in rpt} for rpt in rows]
    # Kept as text, exactly as generateReport() formats it (e.g. "780.70",
    # not 780.7), so the merged file shows the same values as normal mode.
    return pd.DataFrame(data, columns=columns)


def _query_layout(scan, result, header):
    """Column layout of one sample's result, for the normal-mode writer.

    Normal mode writes one header: the REPORT columns of all queries, joined
    in query order (generateReport() -> result.listHead), where a sample
    column such as "Intensity:<sample>" is repeated for every sample in place.
    A batch sample knows only its own sample, so this records each query's
    columns with the sample columns reduced to their base name; the merge
    expands them again for all samples.

    Returns
        {"samples":       [sample names of this MasterScan],
         "query_order":   [QUERYNAME, ...] in run order (= MFQL order),
         "query_columns": {QUERYNAME: [[column, is_sample_column], ...]}}

    Only columns that are in `header` are listed, as only those are written.
    A query without rows has an empty column list.
    """
    samples = [str(s) for s in getattr(scan, "listSamples", [])]
    in_header = set(header)
    query_order, query_columns = [], {}
    for qres in result.dictQuery.values():
        query_order.append(qres.name)
        cols, seen = [], set()
        for rpt in getattr(qres, "listReportOut", None) or []:
            for key in rpt.keys():
                if key not in in_header:
                    continue
                base, is_sample = key, False
                for smp in samples:
                    suffix = ":" + smp
                    if key.endswith(suffix) and len(key) > len(suffix):
                        base, is_sample = key[:-len(suffix)], True
                        break
                if (base, is_sample) not in seen:
                    seen.add((base, is_sample))
                    cols.append([base, is_sample])
        query_columns[qres.name] = cols
    return {"samples": samples, "query_order": query_order,
            "query_columns": query_columns}


def run_mfql_on_scan(scan, queries, options, layout=None):
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

    layout: optional dict. If given, it is filled with what the merge needs
        to write the batch result in the normal-mode layout (see
        _query_layout()): the sample names of this MasterScan, the queries
        in run order and each query's REPORT columns in REPORT order.

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

    header = list(result.listHead) if getattr(result, "listHead", None) else []

    if layout is not None:
        layout.update(_query_layout(scan, result, header))

    dfs = []
    for qres in result.dictQuery.values():
        df_block = _query_result_to_frame(qres, header)
        if df_block.empty:
            continue

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
        layout = {}
        df = run_mfql_on_scan(scan, queries, options, layout=layout)
        if options.get("verboseWorkerLog", False):
            # After the run, when every setting the MFQL code makes is in
            # effect (see _debug_settings_line).
            log(_debug_settings_line())

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
            # Column layout for the normal-mode merge (see _query_layout).
            with open(_layout_path(out_path), "w", encoding="utf-8") as f:
                json.dump(layout, f)
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
# Ion mode of a batch (for the per-sample folder and the log name)
# ============================================================
#
# Positive and negative runs on the same import folder used to share
# "per_sample_results" and "batch_log.txt", so the second run overwrote the
# first one's per-sample CSVs (same sample names) and log. The ion mode is
# read from the selected MFQLs ("IN MS1+" / "IN MS2-" ...) before the run, so
# the folder and the log can be named from the start. batch_results_*.csv
# keeps its name from the ScanPolarity column, as before.

# "IN MS1+" / "in ms2 -" in an MFQL; comments ("# ...") are removed first
_MFQL_SCOPE_RE = re.compile(r"\bIN\s+MS[12]\s*([+-])", re.IGNORECASE)
_MFQL_COMMENT_RE = re.compile(r"#[^\r\n]*")


def batch_ion_mode(queries) -> str:
    """Ion mode of a batch, read from its MFQL files.

    queries: list of {"name": ..., "path": ...} as passed to run_batch().

    Returns "positive", "negative", "mixed" (both + and - scopes among the
    selected MFQLs) or "" when no scope could be read (unreadable files, no
    "IN MS1+/-" at all). "" keeps the old names without a suffix.
    """
    signs = set()
    for q in queries:
        try:
            text = Path(q["path"]).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        signs.update(_MFQL_SCOPE_RE.findall(_MFQL_COMMENT_RE.sub("", text)))
    if signs == {"+"}:
        return "positive"
    if signs == {"-"}:
        return "negative"
    if signs:
        return "mixed"
    return ""


def ion_mode_suffix(ion_mode: str) -> str:
    """'_positive' / '_negative' / '_mixed', or '' if the mode is unknown."""
    return "_" + ion_mode if ion_mode else ""


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

    # Ion mode from the MFQLs: per_sample_results_positive / _negative /
    # _mixed, so a positive and a negative run never write into the same
    # folder. A folder of the same mode from an earlier run is replaced, so
    # no CSV of that run can end up next to (or in the merge of) this one.
    ion_mode = batch_ion_mode(queries)
    log(f"Ion mode (from the MFQLs): {ion_mode or 'unknown'}")

    # Directory where workers will store per-sample CSVs
    per_sample_dir = import_dir / f"per_sample_results{ion_mode_suffix(ion_mode)}"
    if per_sample_dir.exists():
        log(f"Replacing per-sample results of an earlier run in {per_sample_dir}")
        shutil.rmtree(per_sample_dir, ignore_errors=True)
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

    try:
        merged, polarity = merge_lipid_results(
            sample_csv_paths,
            mzml_files=merge_reference_files,
            occurrence_threshold=occurrence_threshold
        )
    finally:
        # The <sample>.layout.json files are only for the merge; remove them
        # so the per-sample folder holds just the CSVs (also if the merge
        # failed).
        for csv_path in sample_csv_paths:
            try:
                _layout_path(csv_path).unlink()
            except OSError:
                pass



    # Output path for the final batch results. The name comes from the
    # ScanPolarity column, as before, with two fixes:
    #   - no MFQL reports ScanPolarity: polarity is empty and polarity[0]
    #     raised IndexError -> fall back to the ion mode from the MFQLs;
    #   - both positive and negative rows: polarity[0] was whichever came
    #     first, so a mixed run overwrote batch_results_positive.csv (or
    #     _negative) -> "mixed".
    if len(polarity) > 1:
        polarity_name = "mixed"
    elif len(polarity) == 1:
        polarity_name = str(polarity[0])
    else:
        polarity_name = ion_mode or "unknown"
    batch_result_path = import_dir / f"batch_results_{polarity_name}.csv"
    # Same layout and separator as the normal-mode output file.
    output_sep = "\t" if options.get("tabLimited") else ","
    merged.write(batch_result_path, sep=output_sep)
    log(f"Saved merged results to {batch_result_path} ({merged.n_rows} rows)")

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
        "polarity": polarity_name,
        "ion_mode": ion_mode,
        "per_sample_dir": str(per_sample_dir) if save_per_sample else None,
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
#
# Output layout: the same as normal mode (lxMain.startMFQL)
# ---------------------------------------------------------
#   - one header line: the REPORT columns of all queries, joined in MFQL
#     order exactly as generateReport() joins them (result.listHead); a
#     sample column such as "Intensity:<sample>" is repeated for every sample
#     at the place where the query reports it;
#   - then one block per query, in MFQL order: an empty line, a line
#     "###<sep><QUERYNAME>", the rows, an empty line; a query without rows
#     still gets its "###" line, as in normal mode;
#   - a cell the row's query does not report is "None", as in normal mode.
# Two batch-only additions are kept:
#   - the blocks of queries that found internal standards (LipidSpecies
#     starting with "IS") come first, and inside a block the internal
#     standards come first; every query still appears exactly once (see
#     the block rules in merge_lipid_results);
#   - the occurrence filter.
# What cannot be the same as normal mode are the values: batch mode builds
# one MasterScan per sample instead of one aligned MasterScan, so which
# species are found, their intensities and their Mass can differ.

# Internal standards: LipidSpecies starting with this prefix.
IS_PREFIX = "IS"

# Columns run_mfql_on_scan()/process_sample() add for the merge; they are not
# REPORT columns and are not written.
_BOOKKEEPING_COLUMNS = ("query_name", "mfql_file", "sample_id")

# Old per-sample CSVs (without a layout file) may have bare intensity columns
# that belong to their only sample.
_BARE_SAMPLE_COLUMN_RE = re.compile(r"^(Intensity|PrecursorIntensity|Fragment[A-Z]Intensity)$")


class MergedResult:
    """The merged batch result in the normal-mode layout.

    header: list of column names
    blocks: list of (title, rows); each row is a list of strings, one per
            header column
    """

    def __init__(self, header, blocks):
        self.header = header
        self.blocks = blocks

    @property
    def n_rows(self):
        return sum(len(rows) for _, rows in self.blocks)

    def to_text(self, sep=","):
        """The file content, line by line as lxMain.startMFQL writes it."""
        out = [sep.join(self.header) + "\n"]
        for title, rows in self.blocks:
            out.append("\n###%s%s\n" % (sep, title))
            for row in rows:
                out.append(sep.join(row) + "\n")
            out.append("\n")
        return "".join(out)

    def write(self, path, sep=","):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_text(sep))


def _detect_delimiter(path):
    with open(path, "rb") as f:
        sample = f.read(4096)

    text = sample.decode("utf-8-sig", errors="replace")

    # A fixed-size read almost always stops mid-line, and the short line
    # that leaves behind has a different field count from the rest, which
    # is exactly what Sniffer's consistency check rejects. Feed the sniffer
    # whole lines only.
    lines = text.splitlines(keepends=True)
    if len(lines) > 1 and not lines[-1].endswith("\n"):
        text = "".join(lines[:-1])

    try:
        return csv.Sniffer().sniff(text, delimiters=",;\t|").delimiter
    except Exception:
        warnings.warn(
            f"Could not detect delimiter for {path}. Falling back to comma.",
            UserWarning
        )
        return ","


def _guess_samples(df, path):
    """Sample names of an old per-sample CSV that has no layout file."""
    stem = Path(path).stem
    for candidate in (f"{stem}.mzML", stem):
        if any(c.endswith(":" + candidate) for c in df.columns):
            return [candidate]
    suffixes = [c.rsplit(":", 1)[1] for c in df.columns if ":" in c]
    if suffixes:
        return [max(set(suffixes), key=suffixes.count)]
    return [f"{stem}.mzML"]


def _split_sample_column(column, samples):
    """'Intensity:<sample>' -> ('Intensity', '<sample>'), else None."""
    for smp in samples:
        suffix = ":" + smp
        if column.endswith(suffix) and len(column) > len(suffix):
            return column[:-len(suffix)], smp
    if _BARE_SAMPLE_COLUMN_RE.match(column) and samples:
        return column, samples[0]
    return None


def _join_columns(lists):
    """Join column lists in order, like lx.tools.connectLists (no mutation)."""
    out, seen = [], set()
    for cols in lists:
        for c in cols:
            if c not in seen:
                seen.add(c)
                out.append(c)
    return out


def _to_float(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def merge_lipid_results(sample_files, mzml_files=None, occurrence_threshold=None):
    """
    Merge the per-sample result CSVs into one batch result in the layout of
    the normal-mode output (see the comment block above).

    A row is one species of one query: the key is (QUERYNAME, LipidSpecies).
    So the same species found by two queries appears in both blocks, as in
    normal mode. Within one sample a key is kept once (first row).

    Values that are not per sample (Mass, errors, formulas, ...) come from
    the first sample, in sample order, that has the row; per-sample columns
    (Intensity:<sample>, ...) come from each sample, 0 where the sample did
    not find the species.

    Parameters
    ----------
    sample_files : paths of the per-sample CSVs (each may have a
        <sample>.layout.json next to it, written by process_sample).
    mzml_files : optional; if given, the CSVs are put into the order of these
        file names.
    occurrence_threshold : optional fraction 0..1. A row whose query reports
        an "Intensity" column is kept only if Intensity > 0 in at least
        ceil(n_samples * threshold) samples. Rows of queries without an
        "Intensity" column are not filtered.

    Returns
    -------
    (MergedResult, polarity) ; polarity = unique non-empty ScanPolarity values
    """

    sample_files = list(sample_files)
    if not sample_files:
        raise ValueError("No sample files were provided.")

    if mzml_files is not None:
        csv_by_stem = {Path(p).stem: p for p in sample_files}
        sample_files = [csv_by_stem[Path(p).stem] for p in mzml_files
                        if Path(p).stem in csv_by_stem]
        if not sample_files:
            raise ValueError(
                "mzml_files was provided, but none of the mzML stems matched "
                "the CSV file stems."
            )

    records = {}             # (query, species) -> record (insertion-ordered)
    query_order = []         # QUERYNAMEs in MFQL order
    query_columns = {}       # QUERYNAME -> [(column or base, is_sample), ...]
    all_samples = []         # sample names in sample order

    for path in sample_files:
        delimiter = _detect_delimiter(path)
        try:
            # Everything as text, so values are written back exactly as the
            # sample wrote them; "" is an empty cell.
            df = pd.read_csv(path, sep=delimiter, encoding="utf-8-sig",
                             dtype=str, keep_default_na=False)
        except Exception:
            raise ValueError(f"Failed reading {path} with delimiter {repr(delimiter)}")

        if "LipidSpecies" not in df.columns:
            raise ValueError(f"{path} is missing the required column LipidSpecies.")

        if "query_name" not in df.columns:
            # Older per-sample CSV: name the block after the MFQL file or
            # the lipid class instead.
            if "mfql_file" in df.columns:
                df["query_name"] = df["mfql_file"]
            elif "LipidClass" in df.columns:
                df["query_name"] = df["LipidClass"]
            else:
                df["query_name"] = "Unknown"

        layout = None
        layout_file = _layout_path(path)
        if layout_file.exists():
            try:
                with open(layout_file, encoding="utf-8") as f:
                    layout = json.load(f)
            except Exception:
                warnings.warn(f"Could not read {layout_file}; using the CSV columns.", UserWarning)

        samples = list(layout["samples"]) if layout and layout.get("samples") else _guess_samples(df, path)
        for smp in samples:
            if smp not in all_samples:
                all_samples.append(smp)

        column_kind = {}     # CSV column -> (base, sample) or None
        for c in df.columns:
            column_kind[c] = _split_sample_column(c, samples)

        # Query order and each query's columns: from the layout file (exact
        # REPORT order); otherwise from the CSV column order, taking the
        # columns the query's rows fill.
        if layout:
            for q in layout.get("query_order", []):
                if q not in query_order:
                    query_order.append(q)
            for q, cols in layout.get("query_columns", {}).items():
                if cols and q not in query_columns:
                    query_columns[q] = [(c[0], bool(c[1])) for c in cols]
        for q in pd.unique(df["query_name"]):
            if q not in query_order:
                query_order.append(q)
            if q not in query_columns:
                rows_q = df[df["query_name"] == q]
                cols = []
                for c in df.columns:
                    if c in _BOOKKEEPING_COLUMNS or not (rows_q[c] != "").any():
                        continue
                    kind = column_kind[c]
                    entry = (kind[0], True) if kind else (c, False)
                    if entry not in cols:
                        cols.append(entry)
                query_columns[q] = cols

        df = df.drop_duplicates(subset=["query_name", "LipidSpecies"], keep="first")

        for row in df.to_dict("records"):
            key = (row["query_name"], row["LipidSpecies"])
            rec = records.get(key)
            if rec is None:
                rec = {"meta": {}, "per_sample": {}}
                records[key] = rec
            for c, v in row.items():
                if c in _BOOKKEEPING_COLUMNS or c == "LipidSpecies" or v == "":
                    continue
                kind = column_kind[c]
                if kind:
                    rec["per_sample"].setdefault(kind, v)
                elif c not in rec["meta"]:
                    rec["meta"][c] = v

    # ------------------------------------------------------------
    # Header: the queries' columns joined in MFQL order, sample columns
    # expanded for all samples (normal mode: result.listHead)
    # ------------------------------------------------------------
    entries = _join_columns(query_columns.get(q, []) for q in query_order)
    if ("LipidSpecies", False) not in entries:
        entries.insert(0, ("LipidSpecies", False))

    header, header_cells = [], []        # header_cells: (base, is_sample, sample)
    for base, is_sample in entries:
        if is_sample:
            for smp in all_samples:
                header.append(f"{base}:{smp}")
                header_cells.append((base, True, smp))
        else:
            header.append(base)
            header_cells.append((base, False, None))

    # ------------------------------------------------------------
    # Occurrence filter on the main Intensity columns
    # ------------------------------------------------------------
    if occurrence_threshold is not None:
        if not 0 <= occurrence_threshold <= 1:
            raise ValueError("occurrence_threshold must be between 0 and 1.")

        queries_with_intensity = {
            q for q in query_order if ("Intensity", True) in query_columns.get(q, [])
        }
        if queries_with_intensity:
            min_required = int(np.ceil(len(sample_files) * occurrence_threshold))
            before = len(records)
            for key in list(records.keys()):
                if key[0] not in queries_with_intensity:
                    continue
                per_sample = records[key]["per_sample"]
                n_positive = sum(
                    1 for smp in all_samples
                    if (_to_float(per_sample.get(("Intensity", smp))) or 0) > 0
                )
                if n_positive < min_required:
                    del records[key]
            print(
                f"Occurrence filter removed {before - len(records)} lipids "
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
    # Rows
    # ------------------------------------------------------------
    def make_row(key, rec):
        q, species = key
        reported = set(query_columns.get(q, []))
        row = []
        lead = ""
        for base, is_sample, smp in header_cells:
            absent = False
            if base == "LipidSpecies" and not is_sample:
                value = species
            elif (base, is_sample) not in reported:
                value = "None"
                absent = True
            elif is_sample:
                # 0 where this sample did not find the species
                value = rec["per_sample"].get((base, smp), "0")
            else:
                value = rec["meta"].get(base, "None")
            row.append(lead + value)
            # generateReport() writes a column the query does not report as
            # "None" + separator + " ", so the next cell starts with a space
            # (" None"). Copied, so the file reads exactly like normal mode.
            lead = " " if absent else ""
        return row

    def is_internal_standard(species):
        return str(species).strip().upper().startswith(IS_PREFIX)

    def mass_sort_key(item):
        position, (key, rec) = item
        mass = _to_float(rec["meta"].get("Mass"))
        return (mass is None, mass if mass is not None else 0.0, position)

    items = list(enumerate(records.items()))

    blocks = []

    # Rules:
    #   - Every query gets exactly one block, titled exactly as normal mode
    #     does: "###<sep>QUERYNAME". No query name appears twice.
    #   - Blocks of queries that found internal standards come first, then
    #     all other queries; both groups in MFQL order. So the internal
    #     standards are together at the top.
    #   - Inside a block: internal standard rows first, then the other rows,
    #     each sorted by Mass (normal mode: precursor mass).
    #   - A query without rows gets an empty block, as in normal mode.
    def rows_of(q, want_is):
        q_items = [it for it in items
                   if it[1][0][0] == q and is_internal_standard(it[1][0][1]) == want_is]
        q_items.sort(key=mass_sort_key)
        return [make_row(k, r) for _, (k, r) in q_items]

    with_is, without_is = [], []
    for q in query_order:
        is_rows = rows_of(q, True)
        block = (q, is_rows + rows_of(q, False))
        (with_is if is_rows else without_is).append(block)
    blocks = with_is + without_is

    # ------------------------------------------------------------
    # Polarity
    # ------------------------------------------------------------
    # Unique values in first-seen order. (A plain dict: lx.tools.odict
    # takes no arguments.)
    polarity = np.array(list(dict.fromkeys(
        r["meta"]["ScanPolarity"] for r in records.values()
        if r["meta"].get("ScanPolarity")
    )))
    if not any(base == "ScanPolarity" for base, _ in entries):
        warnings.warn("ScanPolarity column missing. Returning empty polarity array.", UserWarning)
    elif len(polarity) > 1:
        warnings.warn(f"Multiple ScanPolarity values found: {polarity}", UserWarning)

    return MergedResult(header, blocks), polarity
