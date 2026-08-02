# PCC unresolved ambiguities and blockers

1. **P0 authority:** the completed Formal EIA rebuild uses the evaluated future-change target to train and select its case-specific baseline. The new contract forbids this. It is unresolved whether the intended full rerun should adopt one particular historical independent five-fold Model A/B2 implementation or define a new cross-case predictor.
2. **Future-image normalization leakage:** formal preprocessing derives the current-image normalization support from nonzero voxels in both current and future T1c. This also violates a strict current-only P0 pipeline even before supervised target fitting. No change is authorized without selecting the intended leakage-free preprocessing authority.
3. **Cross-case artifacts:** fold assignments, complete checkpoint set, P0 maps, and referenced `direct_target_case_metrics.csv` are unavailable locally.
4. **Dataset:** MU-Glioma-Post and LUMIERE volumes are not mounted locally. The configured paths are Kaggle-only.
5. **Trajectory contract:** notebook PCC computes per-round metrics, but the migrated return object does not retain all round maps. Adding trajectory capture is an engineering extension and must preserve the final-map operation sequence.
6. **Ablation definitions:** reports name ablations, but complete migrated named runners/configs are absent. They must not be reconstructed from labels alone.
7. **Imperfect-guidance noise generation:** exact seed/operation authority and complete artifacts are not locally executable.
8. **Layer 1 versions:** FORMAL v1 and v1.1 are distinct and their checkpoints must not be interchanged.

These are scientific/data blockers, not invitations to optimize toward Word-report values.
