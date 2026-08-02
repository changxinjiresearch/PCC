# PCC leakage-free Kaggle smoke status

Kernel: `jeechangxin/pcc-leakage-free-rerun-2026`

## Attempts

- Version 1: failed at the first CUDA Conv2d with `cudaErrorNoKernelImageForDevice`. Case and fold manifests were nevertheless generated before training.
- Version 2: completed using the bounded smoke-only CPU fallback; Kaggle output indexing did not expose the sibling artifact directory.
- Version 3: completed, but duplicating all large maps for export exceeded the practical output packaging boundary and produced an incomplete copied P0.
- Version 4: completed with in-place array validation and compact evidence export.

## Version 4 validated contract

- `LOCKED_CASE_MANIFEST.csv`: 40 case rows; SHA-256 `e5ad65359280e002d9bcc4c89211f48840d535b602821ad22db863b88e4656f8`.
- `LOCKED_FOLD_MANIFEST.csv`: 200 fold/split rows; SHA-256 `880bd3b2c87c571d5df10342357a8b67c7d6069a2b68a99df0f5dccb783154ec`.
- One held-out P0 completion states `future_information_used: false`.
- Seven method rows in canonical order: Fixed, Naive, EIA-linear, EIA-blend090, EIA-blend075, EIA-morph, PCC.
- Ten ordered trajectory rows, rounds 1 through 10.
- Retrospective completion states `shared_p0: true` and `shared_clean_target: true`.
- Notebook in-place assertions require all P0/P1–P10/final arrays to share shape, be float32 and finite, and require exact `P10 == pcc_correction`; the kernel could not complete if an assertion failed.

The Kaggle output API omitted the separately written compact summary JSON, so its per-array hashes are not claimed as locally downloaded evidence. The CSVs and completion records were downloaded and parsed locally.

## Full-run decision

The assigned Kaggle worker's PyTorch/CUDA combination cannot execute Conv2d on its GPU. The full entry deliberately forbids CPU fallback. A full five-fold run was therefore not launched. This is an external GPU-availability/compatibility blocker, not a scientific or code mismatch. The next safe action is to rerun the pinned kernel when Kaggle supplies a compatible GPU image/device; no configuration or fold assignment may change.
