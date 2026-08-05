# PCC internal validity patch 2026 — final report

Status: **INTERNAL VALIDITY PATCH ARCHIVE RELEASE AUDITED**

## Identity and immutability

The frozen authority is PCC_LEAKAGE_FREE_RERUN_2026 Kaggle version 8. No predictor was retrained, no P0 was regenerated, no case/fold/config was changed, and no frozen case-level result was edited. Protocol commit: `bbcdd52`. Protocol config SHA-256: `d49043609de3507ec334dcca42f878b1c621300eca17790287e9504bf7313752`.

The v8 authoritative 280-row method table, 400-row trajectory table, 40-row case manifest and 200-row fold manifest were recovered directly from Kaggle. The case and fold manifest hashes match the locked expected hashes. Failed cases were zero.

## Target-independent evaluation

All eight evaluated methods (seven frozen methods plus the locked No-smoothing variant) have 40-case fixed-0.5, probability-score, and strict out-of-fold cross-fitted-threshold results. Full PCC mean fixed-0.5 Dice was 0.275815 and No-smoothing was 0.326306. Full PCC mean soft Dice was 0.269865 and No-smoothing was 0.309452. Mean PR-AUC was 0.373095 for Full PCC and 0.523144 for No-smoothing. Aggressive EIA blends remain oracle-like retrospective controls and were not generally inferior to PCC. Historical top-k remains an oracle-assisted target-volume-matched localization metric, not deployment-style Dice.

## No-smoothing follow-up

The 1,720 locked repeat results completed without failed cases and were aggregated within each of 40 cases. No-smoothing did not perform significantly worse than Full PCC under any tested guidance condition; it was significantly better under Clean, Partial-50, FP-25 and Shift-3, with no significant difference under Partial-25 and Mixed. The magnitude of the clean-guidance advantage was substantially attenuated under partial, shifted, and mixed guidance. It had lower outside-target mass, so increased outside mass was not the explanation. It remains a posthoc candidate for pre-locked external testing, not a replacement canonical method. The SHIFT-3 metadata audit is PASS; the original repeat-level CSV is unchanged and the metadata-corrected file is an independent derivative.

## Release evidence

The current formal suite recorded 208 passed, 1 skipped, 0 failed, 0 errors and 27 subtests; the focused validity-patch suite recorded 15 passed and exit code 0. Compileall, `git diff --check`, data-format parsing, finite critical-value checks, duplicate checks and identity checks passed. The complete evidence is in `11_tests/` and `12_final_release_audit/`.

## Layer 1

No model was rerun. Formal v1 primary-threshold Dice gain was 0.063309 (bootstrap 95% CI 0.044122–0.084622; two-sided p=1.58e-08; dz=0.950862; 35/0/5 wins/ties/losses). Formal v1 remains the provenance-based primary-protocol candidate; v1.1 remains a 15-epoch sensitivity analysis. Final manuscript protocol selection is **HUMAN_DECISION_REQUIRED**.

## Layer 3

Layer 3A absolute core PRI remained supported after Holm; boundary and peritumour PRI did not. Relative PRI results did not survive Holm. Layer 3B peritumour minus control absolute correction was supported; boundary was nominal only and core was unsupported. FP-useful and error-region-useful dominance survived Holm, while FN and boundary-FN dominance were nominal only. These are spatial-reliance and correction-localization findings, not molecular, cellular, pathological-causal, or clinical-causal proof.

## Cohort and identity

The mounted dataset contained 203 patient directories and 596 timepoint directories. Recorded discovery logic identified 155 patients with at least two usable timepoints and selected the first 40 deterministically before modeling. The remaining 115 eligible patients were excluded by that locked limit and 48 had fewer than two usable timepoints. All 40 locked pairs passed recorded compatibility/nonempty checks. Earlier historical discovery-stage counts and rationales not preserved in evidence remain UNKNOWN/NOT RECOVERABLE rather than inferred.

Manifests and Layer 1/2/3 results contain the same 40 unique patients; every patient is test-held-out in exactly one fold. No duplicate patient, timepoint mismatch, or source-path drift was found.

## Documented blockers and boundaries

- Historical pre-2026 cohort-screening stages cannot be fully reconstructed.
- Repository-root pytest collection is obstructed by same-named archival test copies; the authoritative `tests/` suite passes.
- Layer 1 final primary-protocol choice requires human manuscript governance.
- LUMIERE was not started, by explicit scope.
