## lx/batch_processor.py ######### Ballal #########

import os
import time
import traceback
from pathlib import Path

from typing import Dict, List, Any
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

    The file is opened and closed per line. That is slower than holding a
    handle open, but progress lines are infrequent and it keeps writes from
    several worker processes from interleaving mid-line: on both POSIX and
    Windows an O_APPEND write this small lands atomically.
    """

    def __init__(self, log_file):
        self._log_file = log_file
        self._buffer = ""

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
        stamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
        try:
            with open(self._log_file, "a", encoding="utf-8") as handle:
                handle.write(f"{stamp} {line}\n")
        except Exception:
            # A worker must finish its sample even if the log has gone away.
            pass

    def flush(self):
        if self._buffer:
            line, self._buffer = self._buffer, ""
            self._emit(line)


def _install_worker_logging(log_file):
    """Route this worker process's output into the shared batch log.

    Workers are started with the 'spawn' method, so they get a fresh
    interpreter: they do not inherit the TeeLogger that the GUI installs over
    builtins.print, and in a windowed PyInstaller bundle their stdout and
    stderr go to a null sink. Without this, every progress line and every
    traceback raised inside a worker is discarded, and the GUI shows nothing
    between "Using N worker process(es)" and the first completed sample.

    Returns the sink so the caller can flush it, or None when no log file was
    configured (running head-less from a script, say).
    """
    if not log_file:
        return None

    sink = _WorkerLog(log_file)
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



def run_mfql_on_scan(scan, query_path, options):
    """
    Run one MFQL file against a MasterScan.
    """

    q_name = Path(query_path).name
    with open(query_path, "r", encoding="utf-8") as f:
        q_text = f.read()

    mfqlFiles = odict()
    mfqlFiles[q_name] = q_text

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

    # Must come first: everything below reports through print(), which is
    # otherwise discarded in a spawned worker (see _install_worker_logging).
    sink = _install_worker_logging(log_file)

    # Per-worker deep copy so processes don't share mutable state
    import copy as _copy
    options = _copy.deepcopy(options)

    pid = os.getpid()
    t0 = time.time()
    print(f"[PID {pid}] START sample='{sample_id}' file='{sample_path}' ({len(queries)} queries)", flush=True)

    try:
        # -----------------------------------------------------------
        # Build MasterScan
        # -----------------------------------------------------------
        print(f"[PID {pid}] Building MasterScan for '{sample_id}'", flush=True)
        scan = build_master_scan(sample_path, sample_entry_name, options)
        print(f"[PID {pid}] MasterScan READY for '{sample_id}'", flush=True)

        # -----------------------------------------------------------
        # Run all MFQL queries on this scan
        # -----------------------------------------------------------
        all_hits = []
        for i, q in enumerate(queries, 1):
            q_name, q_path = q["name"], q["path"]
            print(f"[PID {pid}] ({i}/{len(queries)}) Running MFQL '{q_name}' on '{sample_id}'", flush=True)
            try:
                hits = run_mfql_on_scan(scan, q_path, options)
            except Exception as e_q:
                print(f"[PID {pid}] ERROR in MFQL '{q_name}' on '{sample_id}': {e_q}", flush=True)
                traceback.print_exc()
                continue

            if hits is None or hits.empty:
                print(f"[PID {pid}] No hits for MFQL '{q_name}' on '{sample_id}'", flush=True)
                continue

            hits["sample_id"] = sample_id
            hits["query_name"] = q_name
            all_hits.append(hits)

        if all_hits:
            df = pd.concat(all_hits, ignore_index=True)
        else:
            df = pd.DataFrame()

        duration = time.time() - t0
        print(f"[PID {pid}] FINISHED MFQL for '{sample_id}' in {duration:.2f}s ({len(df)} rows)", flush=True)

        # -----------------------------------------------------------
        # Write per-sample CSV (only if there are hits)
        # -----------------------------------------------------------
        if df.empty:
            out_path = None
            print(f"[PID {pid}] No hits for '{sample_id}', no CSV written.", flush=True)
        else:
            out_dir_path = Path(out_dir)
            out_dir_path.mkdir(parents=True, exist_ok=True)
            out_path = out_dir_path / f"{sample_id}.csv"
            df.to_csv(out_path, index=False)
            print(f"[PID {pid}] Wrote per-sample CSV '{out_path}'", flush=True)

        # Cleanup big objects
        try:
            del scan, all_hits, df
        except Exception:
            pass
        gc.collect()

        print(f"[PID {pid}] DONE sample='{sample_id}'", flush=True)
        if sink:
            sink.flush()
        return {
            "sample_id": sample_id,
            "status": "OK",
            "path": str(out_path) if out_path else None
        }

    except Exception as e:
        print(f"[PID {pid}] FATAL ERROR in sample '{sample_id}': {e}", flush=True)
        traceback.print_exc()
        if sink:
            sink.flush()
        return {
            "sample_id": sample_id,
            "status": "ERROR",
            "path": None,
            # Carried back to the controller so the GUI can show why this
            # sample failed instead of a bare "ERROR".
            "error": traceback.format_exc()
        }


# ============================================================
# Controller: manages pool + collects + merges
# ============================================================
def run_batch(options: dict, queries: list, n_cores: int = None, occurrence_threshold: float = None, log_file=None):
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
    """

    # Simple log helper. If the GUI installs a TeeLogger as print(),
    # these messages will go to the GUI + file automatically.
    def log(*a):
        print(" ".join(str(x) for x in a), flush=True)

    import_dir = Path(options.get("importDir", "")).resolve()
    spectra_format = options.get("spectraFormat", "")

    # -----------------------------------------------------------
    # Find all samples using normal import discovery logic
    # -----------------------------------------------------------
    listFiles, isTaken, isGroup = getInputFiles(str(import_dir), options)

    if not listFiles:
        log(f"No input samples found in {import_dir} for format '{spectra_format}'")
        return {}

    log(f"Found {len(listFiles)} input sample(s) for batch processing (format={spectra_format}).")

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
                log(f"[MAIN] ({n_done}/{n_total}) OK sample='{sid}' path='{path}'")
            elif status == "OK":
                n_empty += 1
                log(f"[MAIN] ({n_done}/{n_total}) no hits for sample='{sid}'")
            else:
                n_err += 1
                log(f"[MAIN] ({n_done}/{n_total}) FAILED sample='{sid}':\n"
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

        try:
            return csv.Sniffer().sniff(
                text,
                delimiters=[",", ";", "\t", "|"]
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
    # Preferred: LipidClass then Mass
    # Fallbacks are used if columns are missing
    # ------------------------------------------------------------
    sort_cols = []
    ascending = []

    if "LipidClass" in non_is_df.columns:
        sort_cols.append("LipidClass")
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
        lipid_class_group = "Unknown"

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

    class_groups = sorted(
        x for x in ordered["__grp__"].dropna().unique()
        if x != "__IS__"
    )

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

    final_df = final_df.drop(columns=["__grp__"], errors="ignore")

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