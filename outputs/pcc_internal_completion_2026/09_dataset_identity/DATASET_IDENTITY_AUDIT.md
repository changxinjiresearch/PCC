# MU-Glioma-Post dataset identity audit

- Kaggle owner/slug: `stacyvangepuram/mu-glioma-post`.
- Kaggle dataset ID: `9841271`.
- Kaggle title: `MU-Glioma-Post`.
- Dataset version: not exposed by the downloaded Kaggle metadata; therefore recorded as `UNAVAILABLE`, not inferred.
- Locked cohort: 40 longitudinal pairs from 40 unique patients.
- Locked folds: five patient-level folds; each fold contains 32 train and 8 held-out test cases.
- Case manifest SHA-256: `e5ad65359280e002d9bcc4c89211f48840d535b602821ad22db863b88e4656f8`.
- Fold manifest SHA-256: `880bd3b2c87c571d5df10342357a8b67c7d6069a2b68a99df0f5dccb783154ec`.
- File map: 120 source files (current T1c, current mask, future mask for every case), with stable path, size, shape, spacing, and SHA-256 in `LOCKED_CASE_FILE_MAP.csv`.
- File-map SHA-256: `65523b12cea69b499d7cfd65746aa2c4b86f3281e77603f6fcd90275da1fc6fd`.

The locked case and fold manifests were read only. No case, pairing, patient assignment, or source path was modified. The P0 boundary remains current T1c/current mask only; future masks are used after P0 freezing for target construction, retrospective correction, and evaluation.

The optional future-image difference control separately verified all 40 future T1c files for exact shape, affine (absolute tolerance `1e-5`), orientation, and spacing compatibility before execution. That compatibility does not convert the retrospective control into a deployment method.
