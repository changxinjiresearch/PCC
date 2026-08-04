# PCC Internal Validity Patch Protocol 2026

## Status and scope

This protocol prospectively locks `PCC_INTERNAL_VALIDITY_PATCH_2026` before any new patch result is calculated or interpreted. The work is classified as `posthoc_internal_validity_audit_and_prospectively_locked_followup`. It is not a redesign of PCC, a rerun of frozen experiments, a historical reproduction, or external validation.

## Frozen authority

The authority is Kaggle `jeechangxin/pcc-leakage-free-rerun-2026`, version 8, as frozen locally under `validation_reference/frozen_refs/pcc_leakage_free_rerun_2026_v8`. The case manifest SHA-256 is `e5ad65359280e002d9bcc4c89211f48840d535b602821ad22db863b88e4656f8`; the fold manifest SHA-256 is `880bd3b2c87c571d5df10342357a8b67c7d6069a2b68a99df0f5dccb783154ec`; the canonical configuration SHA-256 is `29111a4d9cb16a2981eec5cbaa193346f9715630a6e81aaf9734805f789a14b6`.

No predictor training, P0 generation, case/fold change, canonical configuration change, frozen result overwrite, LUMIERE execution, or manuscript Word modification is permitted.

## Evaluations

The existing target-volume-matched top-k metrics are retained and labelled oracle-assisted retrospective localization metrics. New target-independent evaluations use saved probability maps directly: threshold 0.5 confusion metrics, soft Dice, Brier score, average precision, and target/outside probability mass. A cross-fitted threshold is allowed only when each held-out fold's threshold can be selected exclusively from the other four folds' out-of-fold cases over the locked grid 0.01–0.99; ties select the smallest threshold.

The no-smoothing follow-up is discovery-triggered but prospectively locked here. It reuses the existing imperfect-guidance definitions, repeat identifiers, seeds, directions, P0, clean targets, region, outside suppression, eta, clipping, and ten-round state propagation. Its sole mathematical difference is `S_r = D_r`, with Gaussian smoothing omitted. Repeats are aggregated within case before inference.

Layer 1 and Layer 3 models are not rerun. Their frozen case-level tables are subjected to new two-sided, case-level statistical audits. Layer 1 Formal v1 remains a provenance-based primary-protocol candidate and v1.1 a 15-epoch sensitivity analysis; final selection remains `HUMAN_DECISION_REQUIRED`. Layer 3 claims are limited to spatial reliance and correction localization.

## Statistics

All inference uses cases as the sampling unit, 10,000 bootstrap resamples with seed `20260803`, two-sided Wilcoxon tests, paired Cohen's dz, deterministic Holm correction within the families enumerated in the YAML, finite-value checks, and explicit missingness. Repeats, folds, and voxels are never treated as independent cases.

## Cohort and identity audit

The audit will report only cohort-flow quantities supported by raw discovery records, manifests, notebook code, logs, and Git history. Unrecoverable historical stages will be labelled `UNKNOWN / NOT RECOVERABLE`; no exclusion process will be inferred backward from the final 40 cases.

## Completion

Completion requires authoritative artifact recovery or documented absence, target-independent evaluations, the no-smoothing robustness follow-up, Layer 1 and Layer 3 statistical reaudits, cohort/identity audits, finite case-level outputs, explicit failures, tests, compile checks, `git diff --check`, hashing, commit, and push. External validation is explicitly outside this protocol.
