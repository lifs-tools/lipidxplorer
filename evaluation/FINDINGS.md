# Batch mode: cross-platform quantification differences

Investigation, 2 September 2026. Data, comparison harnesses and conclusions
are preserved here so the next person does not have to repeat the dead ends.

**Status: one real bug identified and characterised, cause NOT found. No fix
in this branch — the one fix attempted was measured, found to be a
regression, and reverted.**

## The question

Running LipidXplorer 1.5 in batch mode on Linux, Windows and macOS, from the
same commit, with the same spectra, settings and MFQL files, produces
different `batch_results_negative.csv`. Are the results essentially the same?

Answer: **identifications yes, intensities no.**

## Conclusions

### Established

| Finding | Evidence |
|---|---|
| Identical inputs on one machine give byte-identical output | `mac` vs `mac2`: **0** differing cells across all 86 columns, 702/702 rows |
| Different platforms give different numbers | `mac` vs `Linux`: 14,608 differing cells |
| Identifications agree across platforms | 686 species common to all three; **0** mismatches across all 16 annotation columns; identical column sets; 15 lipid classes each |
| Intensities do not | p50 0.54–1.70%, p90 46.8–58.7%; 9–12% of detected cells differ by >50% |
| No platform is systematically high or low | median log-ratio **+0.0000** for all three pairs; detection disagreements symmetric |
| The merge does not misassign sample columns | permutation test: "same values but permuted" is *exactly equal* to "identical in place" (159/159, 170/170, 232/232) |
| MFQL query order changes the numbers | `mac` vs `mac3_reversed_mfqldirs`, same machine, only MFQL directory order reversed: **2982** differing cells, 133/700 rows with different intensities, species count 702 → 701 |
| Query order is filesystem-dependent | `collect_mfql_from_listbox` walks with `os.walk` and **never sorts**. APFS gives creation order, ext4 hash order, NTFS roughly alphabetical. Stable per machine — which is why `mac` ≡ `mac2` |
| Identification is *correct* | single sample, existing batch code vs non-batch: 665 species, **jaccard 1.000**, in *both* query orders |
| Quantification is *not* | same comparison, intensities: only **20.5%** identical, p50 **4.33%**, max 99.4%. Batch sorted vs reversed: **18.9%** identical |

Builds were confirmed to be from the same commit, so none of this is a
build or dependency-version difference.

### The open bug

**Batch identification matches non-batch exactly and is order-independent.
Batch quantification differs from non-batch by ~4.3% median and shifts when
MFQL query order changes.**

Cause unknown. The next step is instrumenting where intensities diverge
between the batch and non-batch paths for a single sample — not another
mechanism hypothesis. Three were tried and all three were wrong (below).

### Refuted hypotheses

Recorded so they are not re-tried.

1. **Run-to-run nondeterminism.** Refuted by `mac` ≡ `mac2` (0 differing
   cells). Batch mode is fully reproducible on a given machine. The
   symmetric, zero-bias scatter that suggested noise is equally consistent
   with three deterministic-but-different results.

2. **Column misassignment in `merge_lipid_results`.** Refuted by the
   permutation test above. Values are not shuffled between sample columns.

3. **Hash-order dependence.** Dict iteration is insertion-ordered in Python
   3.7+ and the import path uses essentially no sets.

4. **Cumulative isotopic correction.** The code asymmetry is real —
   `process_sample` calls `startParsing` once *per query* against one shared
   MasterScan, while `lx.lxMain.startMFQL` calls it *once with all queries*;
   and `isotopicCorrectionMS`/`MSMS`/`correctMonoisotopicPeaks` do mutate
   `mfqlObj.sc.listSurveyEntry[...].dictIntensity` in place (34 write sites).
   But the inference that this *compounds* was wrong: `isotopicCorrectionMS`
   marks corrected entries with `dictIntensity[k] = -1`, so a second pass
   over an already-marked entry just re-sets `-1`, and the `-= difference`
   subtractions only touch entries that query identified. The repeats are
   largely idempotent.

   Measured directly — see "rejected fix" below.

### The rejected fix

Changing `process_sample` to collect all queries and call `startParsing`
once (mirroring `lxMain`), plus recording `self.filename` on `TypeQuery` to
map results back to files:

| | species | vs non-batch |
|---|---|---|
| NONBATCH (ground truth) | 665 | — |
| existing code, sorted | 665 | **1.000** |
| existing code, reversed | 665 | **1.000** |
| one-call fix, sorted | 665 | 0.852 — 53 wrong |
| one-call fix, reversed | 665 | 0.785 — 80 wrong |

It reduced order sensitivity sharply (median 7.86% → 0.000% at merged
scale) but **broke identification**, which the existing code already gets
exactly right. Reverted. Do not re-apply without solving that.

## Incidental bugs found

Unrelated to the above, worth their own issues:

- **`lximport.py` cannot run.** `from LipidXplorer import APP_VERSION` pulls
  in the GUI, which imports `lx.lxMain`, giving
  `ImportError: cannot import name 'startMFQL' from partially initialized
  module 'lx.lxMain' (most likely due to a circular import)`.
- **`startMFQL` raises after writing its results** — `lx/lxMain.py:210`
  reads `options['masterScanFileRun']`, which is not always set. The result
  CSV is complete; the trailing `writeReport` call dies.
- **Negative intensities in output.** Linux 715, Win11 1181, mac 887 cells,
  range `-3.0` to `-0.5`, ~10 distinct values. An intensity cannot be
  negative; these come from the `-1` correction markers and subsequent
  arithmetic.
- **`collect_mfql_from_listbox` does not sort.** Sorting would at least make
  the three platforms agree with each other. It does *not* fix the
  quantification bug — they would agree on the same wrong numbers — but it
  removes one uncontrolled variable.

## Data

Merged results, 12 samples, `240821_mice_lung_neg`, occurrence threshold
0.25, MFQL from `negative_standards` + `negative_lipids`:

| File | Run |
|---|---|
| `batch_results_negative_Linux.csv` | Linux, CI build |
| `batch_results_negative_Win11.csv` | Windows 11, CI build |
| `batch_results_negative_mac.csv` | macOS, local build, same commit |
| `batch_results_negative_mac2.csv` | macOS, repeat of the above — byte-identical |
| `batch_results_negative_mac3_reversed_mfqldirs.csv` | macOS, MFQL directory order reversed |

## Tools

In `evaluation/tools/`. All expect the benchmark data at
`/Users/nilshoffmann/Downloads/1.5-benchmark-data` — adjust `BENCH` at the
top of each.

- **`batch_doctor.py`** — environment diagnostic. Walks the boundaries
  `run_batch` crosses (spawn pool, worker-side `lx` imports, numba,
  resource-dir writability, `getInputFiles` discovery, output writability)
  and reports which one breaks.
  `uv run python batch_doctor.py <import_dir> mzML`

- **`headless_batch.py`** — runs batch mode without the GUI, driving the
  GUI's own `collectSettings`/`readOptions_batch` through a stub so options
  are built exactly as the GUI builds them. `QORDER=reversed` reverses the
  query list; `LX_ROOT` selects which checkout to import `lx` from, for
  comparing two versions.
  `QORDER=sorted uv run python headless_batch.py <import_dir> <tag> <cores>`

- **`order_test.py`** — builds one MasterScan, then runs the same queries
  three ways on independent deep copies: sorted per-query, reversed
  per-query, and all-in-one-call. Isolates query-order effects from
  everything else. `QSET=standards|lipids|all`, `NQ=<n>`.

- **`nonbatch_run.py`** — ground truth. Builds a single-sample MasterScan,
  saves it, and runs it through `lx.lxMain.startMFQL` — the non-batch path —
  with all queries. Its output is the reference batch mode should match.
  Note its result CSV is multi-block, with `###,QueryName` separator lines
  and one header at the top; parse accordingly.

## Reproducing the key measurement

```sh
cd evaluation/tools
# ground truth for one sample
uv run python nonbatch_run.py <dir-with-one-mzML> /tmp/truth.csv
# batch, same sample
QORDER=sorted uv run python headless_batch.py <same-dir> runA 4
# then compare species sets and the Intensity: column
```

A useful test for any future fix: batch per-sample output must keep
**jaccard 1.000** against non-batch on species identity, and should move
intensity agreement above the current 20.5%.
