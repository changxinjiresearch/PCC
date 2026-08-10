# Supplementary Information

## Target-conditioned refinement of future-blind longitudinal glioma segmentation-change maps across independent cohorts

[AUTHOR_LIST_REQUIRED]

## Supplementary Methods

### Authority and P0 pathways

V1 was frozen before revision. Table S1 records its files. Development P0 was fold-specific out-of-fold inference, whereas the independent internal and RHUH P0 maps were equal-weight ensembles of five frozen checkpoints. Table S2 provides the exact clinical-metadata linkage and missingness without imputation.

### Comparator definitions

Fixed, Naive, EIA and PCC definitions follow `LOCKED_COMPARATOR_METHOD_DEFINITIONS.md`. EIA and target-volume top-k analyses require the target and are retrospective oracle-style controls. No secondary pairwise inferential tests were introduced.

### Development and robustness analyses

Development mechanism summaries (Table S5), imperfect-guidance analyses (Table S6) and no-smoothing robustness (Table S7) use the frozen development authorities. Development top-k outcomes are target-volume-matched oracle-assisted localization metrics, not Dice@0.5.

## Supplementary Results

Internal and RHUH secondary metrics are reported in Tables S3 and S4. Oracle-assisted controls appear separately in Tables S8 and S9. Table S10 accounts for all scientific denominators and failures. Spatial analyses remain exploratory and are not used for biological or causal claims.

## Supplementary table captions

**Table S1. Authority and frozen V1 provenance.** Path, size and SHA-256 for every frozen V1 package file.

**Table S2. Extended locked-cohort clinical metadata.** Exact patient-ID linkage to official MU-Glioma-Post and RHUH clinical metadata; missing and invalid intervals are retained without imputation.

**Table S3. Internal secondary metrics.** Descriptive patient-level summaries and locked bootstrap intervals; no new P values.

**Table S4. RHUH secondary metrics.** Descriptive patient-level summaries and locked bootstrap intervals; no new P values.

**Table S5. Development mechanism and method summaries.** Development-only results; target-volume-matched metrics are oracle-assisted.

**Table S6. Imperfect-guidance robustness.** Frozen perturbation summaries.

**Table S7. No-smoothing robustness.** Frozen condition-by-method summaries.

**Table S8. Internal oracle-assisted controls.** Target-volume-matched top-k summaries.

**Table S9. RHUH oracle-assisted controls.** Target-volume-matched top-k summaries.

**Table S10. Failure accounting.** Fixed denominators and scientific failures.
