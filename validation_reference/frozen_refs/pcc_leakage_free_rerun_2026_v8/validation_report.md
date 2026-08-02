# Frozen reference validation

Reference: `PCC_LEAKAGE_FREE_RERUN_2026`, Kaggle version 8.

- Run status: `COMPLETE`.
- Run commit: `936a239d913a61533025c02918eeaf8b961d467f`.
- Launch commit: `b8dcc379c5cb38c4c16eb1c62f70e8553c8a68be`.
- GPU was mandatory (`gpu_required: true`).
- Completed folds/P0/retrospective cases: 5/40/40.
- Failed cases: 0.
- Method rows: 280 (40 × 7).
- PCC trajectory rows: 400 (40 × 10).
- Case and fold manifest hashes match `FULL_RUN_STATUS.json`.
- Frozen files were copied without transformation and verified by SHA-256.
- A read-only Kaggle-side audit (`pcc-version-8-frozen-hash-audit`, version 1)
  recorded the relative path, byte size, and SHA-256 of all 40 held-out P0
  maps and all five fold checkpoints without downloading them locally.
- `FROZEN_ARTIFACT_HASHES.csv` contains 51 records: 40 P0 maps, five fold
  checkpoints, three identity files, the main metrics CSV, the trajectory CSV,
  and the failed-case CSV.
- Frozen main-results SHA-256:
  `65db1d0056b510f778e085c5cc8b5150c8db1e5488b7e3d62fb0a745f6cbd2b5`.
- Frozen trajectory SHA-256:
  `c8cd3a730cb8350426ab0bcdd2dae48ab99d7ee684e6ca5a0ed27a015295ebec`.
- Large maps and checkpoints remain in Kaggle; this frozen reference contains
  only the authoritative small aggregate evidence and provenance.

This reference is immutable. Downstream analyses must consume these frozen
copies or verify identical hashes before use. Historical Word values remain a
separate experiment variant and are not incorporated into these files.
