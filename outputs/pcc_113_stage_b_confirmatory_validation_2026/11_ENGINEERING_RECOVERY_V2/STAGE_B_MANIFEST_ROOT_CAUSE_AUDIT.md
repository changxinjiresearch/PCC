# Stage B manifest root-cause audit

## Scope

This is a pre-outcome engineering audit. It does not read future masks, construct a target, calculate performance, or execute a Stage B method.

## Findings

1. **Expected runtime locations in attempts 1–3.** The runner's `locate()` searched `/kaggle/input/<basename>`, `/kaggle/working/<basename>`, the relative working directory, and recursive descendants of `/kaggle/input` and `/kaggle/working`. The required basenames were `LOCKED_113_STAGE_B_CORRECTION_SHARD_MANIFEST.csv`, `LOCKED_113_CONFIRMATORY_CASE_MANIFEST.csv`, and `LOCKED_113_P0_SHA256.csv`.
2. **Local locations.** The three CSVs were present under each local kernel source directory `kaggle/pcc_113_stage_b_cpu_shard_{0,1,2,3}/`. Authoritative copies were also present under `outputs/pcc_113_stage_b_confirmatory_validation_2026/00_STAGE_B_AUTHORITY/` and the Stage A amendment archive. These local source files were not an input dataset mount.
3. **Kernel source contents.** The metadata declared `code_file=run.py`, one Stage A `kernel_sources` output, and the `stacyvangepuram/mu-glioma-post` dataset. The local directories contained adjacent CSVs, but no metadata entry made them a mounted `/kaggle/input` source. Runtime logs show the submitted script at `/kaggle/src/script.py` and no resolvable locked CSVs.
4. **Mounted sources.** Each old shard metadata file mounted `dataset_sources=[stacyvangepuram/mu-glioma-post]` and `kernel_sources=[jeechangxin/pcc-115-holdout-stage-a-p0-freeze-2026]`. No Stage B input-bundle dataset was mounted.
5. **Why the manifest was unavailable.** The CSVs were treated as adjacent kernel-source files, while the runner only resolved mounted input/working paths. Kaggle's runtime did not expose those adjacent files at a path searched by the runner. The logs explicitly report `FileNotFoundError: LOCKED_113_STAGE_B_CORRECTION_SHARD_MANIFEST.csv` before case access.

## Attempt-specific evidence

- Attempt 1: source package failure (`ModuleNotFoundError: No module named 'src'`), before scientific data access.
- Attempt 2: source bundle failure (`src.analysis.internal_statistics` absent), before scientific data access.
- Attempt 3: source dependency was bundled, but all submitted shard logs still failed on the missing manifest CSV, before scientific data access.

## Classification

- Git source omission: **no** for the three tracked local shard CSVs.
- Kernel source omission: **runtime packaging/visibility failure**, yes; adjacent source files were not available through the runner's searched runtime roots.
- Dataset source omission: **yes**; no dedicated Stage B input-bundle dataset was attached.
- Relative-path error: **yes**, in the sense that local source-relative placement was not a valid runtime input path for this runner.
- Working-directory error: **contributing**, because `/kaggle/src` was not searched.
- `.gitignore` exclusion: **no** for the local shard CSVs; `outputs/*` is ignored, but the canonical output copies were not used as a Kaggle mount.
- Other: old attempts also had independent source-package dependency failures.

## Root cause decision

The primary root cause is **Stage B manifest availability/path engineering failure: manifests were stored beside the local kernel script without a mounted input-bundle source, while the runner resolved only `/kaggle/input` and `/kaggle/working`**. Recovery must therefore use one immutable input-bundle source and a smoke test that records resolved runtime paths before any scientific execution.

Previous attempts 1–3, their logs, BLOCKED state, and commits remain unchanged.

Scientific data read: false. Future mask read: false. Target constructed: false. Performance computed: false. Stage B methods executed: false. LUMIERE started: false.
