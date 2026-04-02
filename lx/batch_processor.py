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


# ===========================================================================
# --- ADDED FOR UNIFIED LOGGING (Workers + Batch Controller)
# ===========================================================================
from lx.logger import TeeLogger
import builtins
LOGGER = None   # Will be set by run_batch()
# ===========================================================================



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
        log_file:  (kept for compatibility, not used here)

    Returns:
        dict with fields:
            - sample_id
            - status: "OK" or "ERROR"
            - path: path to per-sample CSV (or None)
            - error: error message (if any)
    """

    sample_path, sample_id, sample_entry_name, options, queries, out_dir, log_file = args

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
        return {
            "sample_id": sample_id,
            "status": "OK",
            "path": str(out_path) if out_path else None
        }

    except Exception as e:
        print(f"[PID {pid}] FATAL ERROR in sample '{sample_id}': {e}", flush=True)
        traceback.print_exc()
        return {
            "sample_id": sample_id,
            "status": "ERROR",
            "path": None,
            "error": str(e)
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
    n_ok = 0
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

            if status == "OK" and path:
                sample_csv_paths.append(path)
                n_ok += 1
                log(f"[MAIN] OK sample='{sid}' path='{path}' (total OK={n_ok})")
            else:
                n_err += 1
                log(f"[MAIN] ERROR/EMPTY sample='{sid}' status='{status}' (total ERR/EMPTY={n_err})")

    duration = time.time() - start
    log(f"All samples processed in {duration:.2f}s")

    if not sample_csv_paths:
        log("No valid per-sample results found.")
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

    final_df = merge_lipid_results(
        sample_csv_paths,
        mzml_files=merge_reference_files,
        occurrence_threshold=occurrence_threshold
    )

    # Output path for the final batch results
    batch_result_path = import_dir / "batch_results.csv"
    final_df.to_csv(batch_result_path, index=False, encoding="utf-8")
    log(f"Saved merged results to {batch_result_path} ({len(final_df)} rows)")

    # -----------------------------------------------------------
    # Build summary
    # -----------------------------------------------------------
    summary = {
        "processed": len(listFiles),
        "ok": n_ok,
        "errors": len(listFiles) - n_ok,
        "duration_sec": round(duration, 2),
        "cores_used": n_cores,
        "output_file": str(batch_result_path),
    }

    # -----------------------------------------------------------
    # Cleanup per-sample CSVs if user does NOT want to keep them
    # -----------------------------------------------------------
    if save_per_sample:
        log(f"Saved {len(sample_csv_paths)} per-sample CSVs in {per_sample_dir}.")
    else:
        log("User does not want to keep per-sample results. Deleting temporary CSVs...")
        for tmp in sample_csv_paths:
            try:
                os.remove(tmp)
            except Exception:
                pass

    gc.collect()

    log(f"Summary: {summary}")
    return summary





# The merge_lipid_results()
# -------------------------------------------------------------------

def merge_lipid_results(sample_files, mzml_files=None, occurrence_threshold=None):
    """
    Merge multiple per-sample lipidomics result CSVs into a single clean batch table.

    Workflow summary:
    -----------------
    1. Detect delimiter for each CSV and load dynamically.
    2. Deduplicate rows by LipidSpecies within each file.
    3. Add sample-specific suffixes to intensity columns.
    4. Concatenate all samples side-by-side on LipidSpecies.
    5. Coalesce duplicate metadata columns (first non-null).
    6. Fill numeric intensity columns with 0.
    7. Reorder columns dynamically by logical groups.
    8. Sort rows so that:
         - All LipidSpecies starting with "IS" (internal standards) are together at the top.
         - Other rows are sorted by LipidClass → Mass (ascending).
    9. Add one blank (NaN) row between each LipidClass block (including IS).
    10. Return the final merged DataFrame.

    Returns
    -------
    pandas.DataFrame
        The merged and cleaned lipidomics table.
    """

    # Silence future downcasting warnings (optional)
    try:
        pd.options.future.no_silent_downcasting = True
    except Exception:
        pass

    # Detect delimiter for each CSV (comma, semicolon, tab, etc.) ===
    def detect_delimiter(path):
        with open(path, "rb") as f:
            sample = f.read(4096)

        # try decode safely; utf-8-sig handles BOM
        text = sample.decode("utf-8-sig", errors="replace")

        try:
            return csv.Sniffer().sniff(text, delimiters=[",", ";", "\t", "|"]).delimiter
        except Exception:
            return ","  # default fallback

    # Read and prepare each file ===
    sample_files = list(sample_files)

    if mzml_files is not None:
        mzml_stems = [Path(p).stem for p in mzml_files]   # desired order
        csv_by_stem = {Path(p).stem: p for p in sample_files}
        # keep only those that exist, in mzML order
        sample_files = [csv_by_stem[s] for s in mzml_stems if s in csv_by_stem]

    dfs = []
    for p in sample_files:
        delim = detect_delimiter(p)
        try:
            df = pd.read_csv(p, sep=delim, encoding="utf-8-sig")
        except Exception as e:
            print(f"FAILED reading {p} with delim={repr(delim)}")
            raise

        if "LipidSpecies" not in df.columns:
            raise ValueError(f"LipidSpecies missing in {p}")

        # Remove duplicate species (keep first occurrence)
        df = df.drop_duplicates(subset=["LipidSpecies"], keep="first")

        # Extract sample identifier from filename
        sample_id = Path(p).stem  # e.g. 250324_VW_Plasmaextrakte_51363_a

        # Identify columns containing intensity data
        sample_cols = [c for c in df.columns if re.match(r"^(Intensity|PrecursorIntensity|Fragment.*Intensity)", c)]
        meta_cols = [c for c in df.columns if c not in sample_cols and c != "LipidSpecies"]

        # Keep LipidSpecies, metadata, and intensity columns
        keep_cols = ["LipidSpecies"] + meta_cols + sample_cols
        df = df[keep_cols]

        # Rename intensity columns to include sample ID (avoid name clashes)
        rename_map = {c: (f"{c}:{sample_id}.mzML" if ":" not in c else c) for c in sample_cols}
        df = df.rename(columns=rename_map)

        # Use LipidSpecies as index for joining
        df = df.set_index("LipidSpecies")
        dfs.append(df)

    # Concatenate all datasets ===
    wide = pd.concat(dfs, axis=1, join="outer")

    # Coalesce duplicate columns (same metadata repeated across files) ===
    coalesced = pd.DataFrame(index=wide.index)
    for col_name in wide.columns.unique():
        block = wide.loc[:, wide.columns == col_name]
        if block.shape[1] == 1:
            coalesced[col_name] = block.iloc[:, 0]
        else:
            # Take first non-null from left (bfill fills from right to left)
            filled = block.bfill(axis=1).infer_objects(copy=False)
            coalesced[col_name] = filled.iloc[:, 0]

    # Drop irrelevant columns if present ===
    coalesced = coalesced.drop(columns=["query_name", "sample_id"], errors="ignore")

    # Reorder columns by logical metadata → intensity → identifiers ===
    head_meta = [
        "LipidClass","Mass","IsobaricClass","ChemicalFormula","DerivatizedForm",
        "AdductIon","LipidCategory","ScanPolarity"
    ]
    head_meta = [c for c in head_meta if c in coalesced.columns]

    # Helper to collect sample-specific columns by prefix
    def sample_block(base):
        cols = []
        for f in sample_files:
            sid = Path(f).stem
            col = f"{base}:{sid}.mzML"
            if col in coalesced.columns:
                cols.append(col)
        return cols

    intensity_block = sample_block("Intensity")
    mid_meta = [c for c in ["IdentificationLevel","QuantificationIon"] if c in coalesced.columns]
    identifier_block = [c for c in ["PrecursorIdentifier","FragmentAIdentifier",
                                    "FragmentBIdentifier","FragmentCIdentifier"] if c in coalesced.columns]
    precursor_intensity_block = sample_block("PrecursorIntensity")

    # Fragment intensity groups
    fragment_bases = sorted({
        re.match(r"^(Fragment[A-Z]Intensity)\b", c).group(1)
        for c in coalesced.columns if re.match(r"^Fragment[A-Z]Intensity\b", c)
    })
    fragment_blocks = []
    for base in fragment_bases:
        fragment_blocks.extend(sample_block(base))

    tail_meta = [c for c in [
        "PrecursorERRppm","FragmentAERRppm","FragmentBERRppm","FragmentCERRppm",
        "FragmentAMass","FragmentBMass","FragmentCMass",
        "FragmentAAdductIon","FragmentBAdductIon","FragmentCAdductIon",
        "FragmentAChemicalFormula","FragmentBChemicalFormula","FragmentCChemicalFormula",
        "NeutralChemicalFormula"
    ] if c in coalesced.columns]

    ordered_blocks = (
        head_meta
        + intensity_block
        + mid_meta
        + identifier_block
        + precursor_intensity_block
        + fragment_blocks
        + tail_meta
    )
    remaining = [c for c in coalesced.columns if c not in ordered_blocks]
    final_cols = [c for c in ordered_blocks + remaining if c in coalesced.columns]
    coalesced = coalesced[final_cols]

    # Sort rows, group IS, fill intensities, and add blank separators ===
    df = coalesced.copy()
    if "LipidSpecies" not in df.columns:
        df.index.name = "LipidSpecies"
        df = df.reset_index()

    # Preserve original order for IS block
    df["__orig_pos__"] = np.arange(len(df))

    # Convert intensity-like columns to numeric and fill NaN with 0
    intensity_pattern = re.compile(r"^(Intensity|PrecursorIntensity|Fragment[A-Z]Intensity):")
    intensity_cols = [c for c in df.columns if intensity_pattern.match(c)]
    for c in intensity_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # -----------------------------------------------------------
    # Apply occupation threshold to Intensity block only
    # -----------------------------------------------------------
    occupation_threshold = occurrence_threshold

    if intensity_block and occupation_threshold is not None:
        n_positive = (df[intensity_block] > 0).sum(axis=1)
        min_required = int(np.ceil(len(intensity_block) * occupation_threshold))

        before = len(df)
        df = df[n_positive >= min_required].copy()
        after = len(df)

        print(f"Occupation filter removed {before - after} lipids "
              f"(threshold={occupation_threshold})")

    # Identify IS rows (LipidSpecies starts with "IS")
    is_mask = df["LipidSpecies"].astype(str).str.strip().str.upper().str.startswith("IS")

    # Split and sort
    is_df = df[is_mask].copy().sort_values("__orig_pos__", kind="mergesort")
    non_is_df = df[~is_mask].copy()

    # Sort non-IS rows by LipidClass then Mass (ascending)
    if "Mass" in non_is_df.columns:
        non_is_df["Mass"] = pd.to_numeric(non_is_df["Mass"], errors="coerce")
        non_is_df = non_is_df.sort_values(
            ["LipidClass", "Mass", "__orig_pos__"],
            ascending=[True, True, True],
            kind="mergesort"
        )
    else:
        non_is_df = non_is_df.sort_values(
            ["LipidClass", "__orig_pos__"],
            ascending=[True, True],
            kind="mergesort"
        )

    # Combine IS block first, then all other sorted classes
    ordered = pd.concat([is_df, non_is_df], ignore_index=True)
    ordered = ordered.drop(columns=["__orig_pos__"], errors="ignore")

    # Synthetic grouping column (ensures all IS rows form one group)
    ordered["__grp__"] = np.where(
        ordered["LipidSpecies"].astype(str).str.strip().str.upper().str.startswith("IS"),
        "__IS__",
        ordered["LipidClass"].astype(str)
    )

    # Build final DataFrame with one blank row after each group
    groups_out = []

    # IS block first (if present)
    if (ordered["__grp__"] == "__IS__").any():
        g = ordered[ordered["__grp__"] == "__IS__"]
        groups_out.append(g)
        groups_out.append(pd.DataFrame([[np.nan] * len(ordered.columns)], columns=ordered.columns))

    # Then each LipidClass alphabetically
    for cls in sorted(x for x in ordered["__grp__"].unique() if x != "__IS__"):
        g = ordered[ordered["__grp__"] == cls]
        groups_out.append(g)
        groups_out.append(pd.DataFrame([[np.nan] * len(ordered.columns)], columns=ordered.columns))

    final_df = pd.concat(groups_out, ignore_index=True)
    final_df = final_df.drop(columns=["__grp__"], errors="ignore")

    # Ensure LipidSpecies is the first column
    cols = final_df.columns.tolist()
    if "LipidSpecies" in cols:
        cols = ["LipidSpecies"] + [c for c in cols if c != "LipidSpecies"]
        final_df = final_df[cols]

    # === Return final merged DataFrame ===
    return final_df