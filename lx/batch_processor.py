# lx/batch_processor.py ######### Ballal #########
import os
import time
import traceback
from pathlib import Path
import multiprocessing as mp
from typing import Dict, List, Any
import pandas as pd
import gc  # For manual memory cleanup
import copy
import io
import re
import csv
import numpy as np

    

from lx.spectraImport import doImport
from lx.spectraImport import lpdxImportDEF_new
from lx.exceptions import LipidXException
from lx.options import Options, optionsDict

from lx.mfql.runtimeExecution import TypeMFQL
from lx.mfql.mfqlParser import startParsing
from lx.tools import odict

# ============================================================
# Real LipidXplorer implementations (Batch-safe)
# ============================================================
def build_master_scan(file_path: str, options: dict):
    """
    Create a MasterScan in memory for one sample using LipidXplorer's
    normal import pipeline, but skip directory scanning and saving.

    Parameters
    ----------
    file_path : str
        Path to the sample file (.mzML or .dta/csv)
    options : dict
        Import options (same structure as in the GUI)

    Returns
    -------
    scan : MasterScan
        The in-memory MasterScan object, ready for MFQL queries
    """

    #print(f"[build_master_scan] Building MasterScan for {file_path}", flush=True)

    # Prepare import setup — equivalent to startImport() in normal mode
    # options['importMSMS'] = True
    # options['batch_mode'] = True  # prevent saveSC

    # lpdxImportDEF_new() returns tuple (options, scan, importDir, output, parent, listFiles, isTaken, isGroup)
    listIntermission = lpdxImportDEF_new(
        parent=None,
        options=options
    )

    # Patch the file list so we only import one sample
    listIntermission = (
        listIntermission[0],
        listIntermission[1],
        listIntermission[2],
        listIntermission[3],
        listIntermission[4],
        [[file_path, os.path.dirname(file_path)]],  # <-- listFiles
        True,
        False,
    )

    # Run the actual import process to fill the MasterScan
    doImport(
        listIntermission[0],  # options
        listIntermission[1],  # scan
        listIntermission[2],  # importDir
        listIntermission[3],  # output
        listIntermission[4],  # parent
        listIntermission[5],  # listFiles
        listIntermission[6],  # isTaken
        listIntermission[7],  # isGroup
        options['alignmentMethodMS'],
        options['alignmentMethodMSMS'],
        options['scanAveragingMethod'],
        options['importMSMS']
    )

    print("[build_master_scan] MasterScan built successfully.", flush=True)
    # print("listIntermission[0] (optionsDict)................")
    # ops = listIntermission[0]

    # for k, v in ops._data.items():
    #     print(f"  {k}: {v}")
        

    return listIntermission[1]  # return the scan object



def run_mfql_on_scan(scan, query_path, options):
    """
    Run ONE MFQL file against a given MasterScan and return a DataFrame
    that matches the output of a normal single-run (startMFQL).

    Steps:
      1. Build MFQL input dict {query_name: query_text}.
      2. Create TypeMFQL bound to the current MasterScan.
      3. Merge import-related options from the scan.
      4. Call startParsing() to execute the MFQL logic.
      5. Extract header (listHead) and query results (strOutput).
      6. Build a pandas DataFrame with proper columns.
      7. Clean up large objects to keep memory low.

    Returns:
        pd.DataFrame: MFQL hit table for this sample.
    """

    # ---------------------------------------------------------
    # 1. Read MFQL query text and create mapping {filename: text}
    # ---------------------------------------------------------
    q_name = Path(query_path).name
    with open(query_path, "r", encoding="utf-8") as f:
        q_text = f.read()
        
    mfqlFiles = odict()
    mfqlFiles[q_name] = q_text

    # ---------------------------------------------------------
    # 2. Initialize MFQL object linked to the MasterScan
    # ---------------------------------------------------------
    mfqlObj = TypeMFQL(masterScan=scan)

    # Assign user-defined import options (already optionsDict type)
    mfqlObj.options = options

    # ---------------------------------------------------------
    # 3. Merge runtime import-related options from MasterScan
    #    (mirrors startMFQL behavior)
    # ---------------------------------------------------------
    for key in list(mfqlObj.sc.options.keys()):
        if key in Options.importOptions:
            try:
                # copy value only if non-empty on the scan side
                if not mfqlObj.sc.options.isEmpty(key):
                    mfqlObj.options[key] = mfqlObj.sc.options[key]
            except Exception:
                # some keys may intentionally be empty, e.g. MSMScalibration=""
                continue

    # ---------------------------------------------------------
    # 4. Choose correct separator: comma or tab
    # ---------------------------------------------------------
    mfqlObj.outputSeperator = '\t' if options.get('tabLimited') else ','

    # ---------------------------------------------------------
    # 5. Run the full MFQL pipeline (identification + report)
    # ---------------------------------------------------------
    startParsing(
        mfqlFiles,
        mfqlObj,
        scan,
        isotopicCorrectionMS   = options.get('isotopicCorrectionMS', True),
        isotopicCorrectionMSMS = options.get('isotopicCorrectionMSMS', True),
        complementSC           = options.get('complementMasterScan', False),
        parent                 = None,
        progressCount          = 0,
        generateStatistics     = options.get('statistics', False)
    )

    # ---------------------------------------------------------
    # 6. Extract results from the MFQL object
    # ---------------------------------------------------------
    result = mfqlObj.result

    # If no output generated, return empty DataFrame
    if not getattr(result, "mfqlOutput", False):
        try:
            del mfqlObj
        except Exception:
            pass
        return pd.DataFrame()

    # Header row — same as the single-run CSV header
    header = list(result.listHead) if hasattr(result, "listHead") else None

    # Collect all query result blocks (string CSV fragments)
    dfs = []
    for qres in result.dictQuery.values():
        output_text = qres.strOutput.strip()
        if not output_text:
            continue

        # Convert the raw text block into a DataFrame
        buf = io.StringIO(output_text)
        if header:
            # use header from listHead (no header row inside the data)
            df_block = pd.read_csv(buf, sep=mfqlObj.outputSeperator, names=header, header=None)
        else:
            df_block = pd.read_csv(buf, sep=mfqlObj.outputSeperator)

        # Tag the query name (for downstream merging)
        df_block["query_name"] = qres.name
        dfs.append(df_block)

    # Merge all query blocks into one DataFrame for this sample
    df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    #print(f"[run_mfql_on_scan] Query {q_name} returned {len(df)} hits.",list(df.columns.values), flush=True)
    # ---------------------------------------------------------
    # 7. Cleanup large objects to free memory in worker process
    # ---------------------------------------------------------
    try:
        if hasattr(result, "dictQuery"):
            del result.dictQuery
        del result
        del mfqlObj
    except Exception:
        pass

    return df




# ============================================================
# Worker: executes per-sample file (one process per sample)
# ============================================================

def process_sample(args: tuple) -> Dict[str, Any]:
    """
    Worker function — executed in a separate process for each sample.

    Workflow:
      1. Build an in-memory MasterScan from the sample  file.
      2. Run all MFQL queries against that MasterScan (via run_mfql_on_scan).
      3. Combine all query results into a single DataFrame.
      4. Return metadata and results to the main process.

    Args:
        args (tuple): (file_path, sample_id, options, queries)
            - file_path : str  →  file path for this sample
            - sample_id : str  → short sample name (filename stem)
            - options   : optionsDict (or dict) → import settings
            - queries   : list[dict] → MFQL query descriptors [{name, path}, ...]

    Returns:
        dict: {
            "sample_id": str,
            "table": pd.DataFrame,
            "status": "OK" or "ERROR",
            "error": str (optional)
        }
    """
    # ---------------------------------------------------------------
    # 0. Unpack arguments and basic setup
    # ---------------------------------------------------------------
    file_path, sample_id, options, queries = args
    pid = os.getpid()      # for logging clarity
    t0 = time.time()       # for performance timing

    print(f"[PID {pid}] Starting sample '{sample_id}' ({len(queries)} queries)", flush=True)

    try:
        # -----------------------------------------------------------
        # 1. Build MasterScan for this sample
        # -----------------------------------------------------------
        # The MasterScan is created *in-memory only* (not saved to disk).
        # It contains aligned spectra and peak data ready for MFQL.
        scan = build_master_scan(file_path, options)

        # -----------------------------------------------------------
        # 2. Run all MFQL queries for this sample
        # -----------------------------------------------------------
        all_hits = []  # will collect all query DataFrames

        for i, q in enumerate(queries, 1):
            q_name, q_path = q["name"], q["path"]
            try:
                print(f"    [PID {pid}] ({i}/{len(queries)}) Running {q_name}", flush=True)

                # Execute the MFQL query using the shared helper
                hits = run_mfql_on_scan(scan, q_path, options)

                # If no results were found, skip
                if hits is None or hits.empty:
                    print(f"    [PID {pid}] No hits for {q_name}", flush=True)
                    continue

                # Annotate each row with the sample + query name
                hits["sample_id"] = sample_id
                hits["query_name"] = q_name

                # Append for merging later
                all_hits.append(hits)

            except Exception as e:
                # Catch and log query-specific errors
                print(f"    [PID {pid}] Error in {q_name}: {e}", flush=True)
                traceback.print_exc()
                continue

        # -----------------------------------------------------------
        # 3. Merge all query results for this sample
        # -----------------------------------------------------------
        if all_hits:
            df = pd.concat(all_hits, ignore_index=True)
        else:
            df = pd.DataFrame()  # no hits at all

        duration = time.time() - t0
        print(f"[PID {pid}] Finished '{sample_id}' in {duration:.2f}s ({len(df)} hits)", flush=True)

        # -----------------------------------------------------------
        # 4. Clean up to free memory
        # -----------------------------------------------------------
        del scan, all_hits
        gc.collect()

        # Return sample summary + results to parent
        return {"sample_id": sample_id, "table": df, "status": "OK"}

    except Exception as e:
        # Catch any top-level errors so one sample doesn’t crash the batch
        print(f"[PID {pid}] Fatal error in '{sample_id}': {e}", flush=True)
        traceback.print_exc()
        return {"sample_id": sample_id, "status": "ERROR", "error": str(e)}



# ============================================================
# Controller: manages pool + collects + merges results
# ============================================================

def run_batch(options: dict, queries: list, n_cores: int = None):
    """
    Batch controller:
      1) Find mzML files
      2) Process in parallel
      3) Collect valid per-sample tables
      4) (Optionally) save per-sample CSVs
      5) Merge via merge_lipid_results()
      6) Save <resultFile>_batch.csv
    """


    import_dir = Path(options.get("importDir", "")).resolve()
    mzml_files = sorted(import_dir.glob("*.mzML"))  ####### change it Ballal #########
    if not mzml_files:
        print(f"No mzML files found in {import_dir}", flush=True)
        return {}

    print(f"Found {len(mzml_files)} mzML files for batch processing.", flush=True)

    tasks = [(str(f), f.stem, copy.deepcopy(options), queries) for f in mzml_files]

    n_cores = n_cores or min(mp.cpu_count(), 8)
    print(f"Using {n_cores} cores (CPU count = {mp.cpu_count()})", flush=True)

    start = time.time()
    
    with mp.Pool(processes=n_cores) as pool:
        results = pool.map(process_sample, tasks)
        
    duration = time.time() - start
    print(f"\nAll samples processed in {duration:.2f}s\n", flush=True)

    print("Collecting valid per-sample results...", flush=True)
    valid_results = [r for r in results if r.get("status") == "OK" and not r["table"].empty]
    if not valid_results:
        print("No valid per-sample results found.", flush=True)
        return {}

    # optionally save per-sample CSVs
    import_dir = Path(import_dir)

    # Create subfolder inside import_dir
    per_sample_dir = import_dir / "per_sample_results"
    per_sample_dir.mkdir(parents=True, exist_ok=True)

    save_per_sample = bool(options.get("savePerSample", False))
    sample_csv_paths = []

    if save_per_sample:
        print("Saving individual per-sample CSVs...", flush=True)

    for r in valid_results:
        df = r["table"]
        sample_name = r.get("sample_id") or r.get("name") or "sample"

        # Save inside the new folder
        p = per_sample_dir / f"{sample_name}.csv"

        df.to_csv(p, index=False)
        sample_csv_paths.append(str(p))

    if save_per_sample:
        print(f"Saved {len(sample_csv_paths)} per-sample CSVs in {per_sample_dir}.", flush=True)

    # If user doesn't want per-sample files, we still need paths.
    # We already wrote temporary CSVs above to avoid in-memory to-file conversion during merge;
  
    if not save_per_sample:
        # We'll delete them after final save
        pass

    #print("Merging all per-sample results...", flush=True)
    final_df = merge_lipid_results(sample_csv_paths)

    # Output path
    # normal_result_path = options.get("resultFile")
    # if normal_result_path:
    #     normal_result_path = Path(normal_result_path)
    #     batch_result_path = normal_result_path.with_name(
    #         normal_result_path.stem + "_batch" + normal_result_path.suffix
    #     )
    # else:
    batch_result_path = import_dir / "batch_results.csv"


    final_df.to_csv(batch_result_path, index=False, encoding="utf-8")
    #print(f"Saved merged results to {batch_result_path} ({len(final_df)} rows)", flush=True)

    # Build summary BEFORE cleanup so valid_results is still in scope
    summary = {
        "processed": len(mzml_files),
        "ok": len(valid_results),
        "errors": len(mzml_files) - len(valid_results),
        #"rows": len(final_df),
        "duration_sec": round(duration, 2),
        "cores_used": n_cores,
        "output_file": str(batch_result_path),
    }

    # Cleanup temp per-sample CSVs if not saving
    if not save_per_sample:
        for tmp in sample_csv_paths:
            try: os.remove(tmp)
            except Exception: pass

    del results, valid_results
    gc.collect()

    print(f"Summary: {summary}", flush=True)
    return summary

def merge_lipid_results(sample_files):
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

    # === 1. Detect delimiter for each CSV (comma, semicolon, tab, etc.) ===
    def detect_delimiter(path):
        with open(path, "r", newline="") as f:
            sample = f.read(4096)
            sniffer = csv.Sniffer()
            try:
                return sniffer.sniff(sample).delimiter
            except Exception:
                return ","  # default fallback

    # === 2. Read and prepare each file ===
    dfs = []
    for p in sample_files:
        delim = detect_delimiter(p)
        df = pd.read_csv(p, delimiter=delim)

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
        #print(f"Loaded {p} ({df.shape[0]} rows, {df.shape[1]} cols)")

    # === 3. Concatenate all datasets ===
    wide = pd.concat(dfs, axis=1, join="outer")
    #print(f"Concatenated shape: {wide.shape}")

    # === 4. Coalesce duplicate columns (same metadata repeated across files) ===
    coalesced = pd.DataFrame(index=wide.index)
    for col_name in wide.columns.unique():
        block = wide.loc[:, wide.columns == col_name]
        if block.shape[1] == 1:
            coalesced[col_name] = block.iloc[:, 0]
        else:
            # Take first non-null from left (bfill fills from right to left)
            filled = block.bfill(axis=1).infer_objects(copy=False)
            coalesced[col_name] = filled.iloc[:, 0]
    #print(f"Coalesced to {coalesced.shape[1]} unique columns")

    # === 5. Drop irrelevant columns if present ===
    coalesced = coalesced.drop(columns=["query_name", "sample_id"], errors="ignore")

    # === 6. Reorder columns by logical metadata → intensity → identifiers ===
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

    # === 7. Sort rows, group IS, fill intensities, and add blank separators ===
    #print("Sorting rows, grouping IS, and cleaning intensities...")

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
        non_is_df = non_is_df.sort_values(["LipidClass", "__orig_pos__"],
                                          ascending=[True, True], kind="mergesort")

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

