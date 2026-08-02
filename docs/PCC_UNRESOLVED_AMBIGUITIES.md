# PCC unresolved ambiguities and blockers

1. **Historical P0 authority resolved for the new run:** the completed Formal EIA rebuild remains target-trained and excluded. `PCC_LEAKAGE_FREE_RERUN_2026` is now authorized from notebook cells 14–17 and is intentionally distinct from historical B2.
2. **Future-image normalization leakage:** formal preprocessing derives the current-image normalization support from nonzero voxels in both current and future T1c. This also violates a strict current-only P0 pipeline even before supervised target fitting. No change is authorized without selecting the intended leakage-free preprocessing authority.
3. **Historical cross-case artifacts:** original fold assignments, checkpoints, P0 maps, and referenced `direct_target_case_metrics.csv` remain unavailable. New folds will therefore be generated and locked without an original-fold claim.
4. **Dataset:** MU-Glioma-Post and LUMIERE volumes are not mounted locally. The configured paths are Kaggle-only.
5. **Trajectory contract:** notebook PCC computes per-round metrics, but the migrated return object does not retain all round maps. Adding trajectory capture is an engineering extension and must preserve the final-map operation sequence.
6. **Ablation definitions:** reports name ablations, but complete migrated named runners/configs are absent. They must not be reconstructed from labels alone.
7. **Imperfect-guidance noise generation:** exact seed/operation authority and complete artifacts are not locally executable.
8. **Layer 1 versions:** FORMAL v1 and v1.1 are distinct and their checkpoints must not be interchanged.

These are scientific/data blockers, not invitations to optimize toward Word-report values.
