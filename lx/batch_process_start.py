# lx/batch_process_start.py ###### Ballal ######
"""
Entry point for batch processing launched from the GUI.
This script runs in a separate Python process (spawned by On_button_RUN_batch).

Responsibilities:
- Read JSON payload (options + queries) from stdin.
- Initialize multiprocessing safely (freeze_support + spawn).
- Call lx.batch_processor.run_batch() to perform actual work.
- Print progress / results to stdout for the GUI to display.
"""

import sys
import json
import traceback
from multiprocessing import freeze_support, set_start_method

# IMPORTANT:
# lx.batch_processor MUST NOT import wx or any GUI code,
# because it will be imported in worker processes on Windows.

from lx.batch_processor import run_batch
from lx.options import Options, optionsDict
from lx.project import Project
import pickle

def read_payload_from_stdin() -> dict:
    """Read the pickled payload sent by the GUI over stdin."""
    try:
        data = pickle.load(sys.stdin.buffer)
        return data
    except Exception as e:
        print(f"Error loading pickle payload: {e}", file=sys.stderr, flush=True)
        sys.exit(1)




def main():
    """
    Entry point for batch execution.
    Called when launched via: 		cmd = [sys.executable, "-u", "-m", "lx.batch_process_start"]
		try:
			proc = subprocess.Popen(
				cmd,
				stdin=subprocess.PIPE,     # binary input for pickle
				stdout=subprocess.PIPE,    # binary output for live reading
				stderr=subprocess.STDOUT,  # merge stderr into stdout
				bufsize=0                  # unbuffered binary I/O
			)
    """
    
    # -----------------------------------------------------------------
    # Multiprocessing initialization (MUST be first on Windows)
    # -----------------------------------------------------------------
    # Prevents issues when creating new processes with "spawn" start method.
    freeze_support()

    # Force 'spawn' everywhere for consistency (safe cross-platform)
    try:
        set_start_method("spawn")
    except RuntimeError:
        # Already set by the parent process or environment
        pass

    # -----------------------------------------------------------------
    # Read payload (from GUI stdin)
    # -----------------------------------------------------------------
    data = read_payload_from_stdin()

    options = data.get("options", {})
    queries = data.get("queries", [])
    #print("options received:",options, flush=True)
    if not options or not queries:
        #print("Invalid payload: missing 'options' or 'queries'", file=sys.stderr, flush=True)
        sys.exit(1)

    #print("Payload received. Starting batch processing...", flush=True)

    # -----------------------------------------------------------------
    # Run the actual batch work (multiprocessing)
    # -----------------------------------------------------------------
    try:
        summary = run_batch(options, queries)

        print("Batch processing completed.", flush=True)
        #if summary is not None:
            # Print a short summary for the GUI log
            #print(f"Summary: {summary}", flush=True)

        sys.exit(0)

    except Exception as e:
        # Print full traceback for debugging
        print("Error during batch processing:", file=sys.stderr, flush=True)
        traceback.print_exc()
        sys.exit(1)


# ---------------------------------------------------------------------
# Guarded entry point
# ---------------------------------------------------------------------
# This is CRITICAL on Windows: prevents child worker processes
# from re-running the main() logic when using 'spawn' mode.
# ---------------------------------------------------------------------
if __name__ == "__main__":
    main()
