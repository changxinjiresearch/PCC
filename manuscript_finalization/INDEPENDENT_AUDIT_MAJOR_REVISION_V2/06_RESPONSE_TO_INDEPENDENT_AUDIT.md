# Response to independent audit

We thank the independent reviewers. We accepted each manuscript-level concern and revised without changing scientific results.

## MAJOR-01 — PCC outside-support probability was incorrectly described as preserved.

**Response.** We agree. Replace prose and provide the complete logit update; audit all preserve/outside-support wording.

**Change made.** Introduction paragraph 3; Methods, Prediction-Comparison-Correction; PCC_ALGORITHM_TEXT_IDENTITY_AUDIT.md

**Evidence.** src/models/pcc.py; locked method definitions. Scientific result changed: NO.

## MAJOR-02 — V1 expanded PCC as probability correction and calibration.

**Response.** We agree. Restore Prediction-Comparison-Correction and define Prediction as the supplied P0.

**Change made.** Abstract; Introduction paragraph 3; Methods, Prediction-Comparison-Correction; PCC_TERMINOLOGY_AUDIT.md

**Evidence.** historical protocol terminology and project authority. Scientific result changed: NO.

## MAJOR-03 — P0 generation pathways were incorrectly unified across cohorts.

**Response.** We agree. Report development held-out single-fold inference separately from five-checkpoint holdout/external ensembles.

**Change made.** Results, Development analyses and Independent internal confirmation; Methods, Predictor inputs, training labels and cohort-specific P0 generation; Figure 1; P0_GENERATION_BY_COHORT_AUDIT.md

**Evidence.** fold manifest; Stage A checkpoint/runtime manifests. Scientific result changed: NO.

## MAJOR-04 — Future-blind wording did not adequately disclose current-mask input.

**Response.** We agree. Define future-blind relative to evaluated-case future data and disclose two-channel input and deployment limitation.

**Change made.** Abstract; Introduction paragraph 3; Methods, Predictor inputs; Discussion paragraphs 1–2 and Limitations; Figure 1

**Evidence.** current-only preprocessing and runtime manifests. Scientific result changed: NO.

## MAJOR-05 — Training-label text could be misconstrued as test-case future leakage.

**Response.** We agree. Describe training-patient future-added labels and evaluated-patient isolation explicitly.

**Change made.** Methods, Predictor inputs, training labels and cohort-specific P0 generation; Figure 1 legend; P0_GENERATION_BY_COHORT_AUDIT.md

**Evidence.** src/pipelines/leakage_free_p0.py. Scientific result changed: NO.

## MAJOR-06 — Target wording overreached beyond a one-sided composite segmentation target.

**Response.** We agree. Use one-sided, segmentation-derived future-added composite foreground terminology and audit biological wording.

**Change made.** Title; Abstract; Results, Cohorts, segmentation target and future-access boundary; Methods, Foreground definitions and one-sided target; Discussion, Limitations; TARGET_SEMANTICS_LANGUAGE_AUDIT.csv

**Evidence.** target construction code and dataset label authority. Scientific result changed: NO.

## MAJOR-07 — Matched-information comparators were not adequately visible in the main manuscript.

**Response.** We agree. Add descriptive Table 3 and balanced answer-conditioning interpretation without new P values.

**Change made.** Results, Matched-information controls contextualized target access; Discussion paragraph 3; Table 3

**Evidence.** locked 113 and RHUH case-method CSVs. Scientific result changed: NO.

## MAJOR-08 — Naive and EIA comparator definitions were insufficient for reproduction.

**Response.** We agree. Provide formulas, parameters, information access and code hashes.

**Change made.** Methods, Comparator methods; LOCKED_COMPARATOR_METHOD_DEFINITIONS.md; LOCKED_COMPARATOR_CODE_HASHES.csv

**Evidence.** src/models/naive_self_tightening.py; src/models/eia.py. Scientific result changed: NO.

## MAJOR-09 — Table 1 lacked clinical cohort characteristics.

**Response.** We agree. Add age, sex, diagnosis, grade, interval and RHUH variables with explicit missingness and no significance tests.

**Change made.** Results, Cohorts, segmentation target and future-access boundary; Methods, Study design and datasets; Table 1; Table S2

**Evidence.** official MU and RHUH clinical metadata linked to locked IDs. Scientific result changed: NO.

## MODERATE-01 — Discussion called Wilcoxon P values exact without implementation support.

**Response.** We agree. Remove exact wording; report scipy.stats.wilcoxon defaults plus explicit zero_method and alternative.

**Change made.** Methods, Outcomes and statistics; Table 2; STATISTICAL_IMPLEMENTATION_REPORTING_AUDIT.md

**Evidence.** src/analysis/holdout_statistics.py; Stage B runner. Scientific result changed: NO.

## MODERATE-02 — Direct future-blind postoperative recurrence-localization prior art was missing.

**Response.** We agree. Add accurate contrast between future-blind prediction and retrospective target-conditioned refinement.

**Change made.** Introduction paragraph 2; Discussion paragraph 7; Reference 16

**Evidence.** Cepeda et al., Cancers 2023; DOI/PMID verified. Scientific result changed: NO.

## MODERATE-03 — Development target-volume-matched metrics could be mistaken for Dice@0.5.

**Response.** We agree. Label every development top-k result as oracle-assisted target-volume-matched localization.

**Change made.** Results, Development analyses characterized update behaviour; Figure 5 and legend; Tables S5–S7

**Evidence.** development metric authorities. Scientific result changed: NO.

## MODERATE-04 — Supplement numbering and wide-table layout were inconsistent.

**Response.** We agree. Rebuild registry, cross-references, landscape tables and readable typography.

**Change made.** Supplementary Information Tables S1–S10; SUPPLEMENT_TABLE_FIGURE_REGISTRY.csv; SUPPLEMENT_CROSS_REFERENCE_AUDIT.csv

**Evidence.** V1 supplement. Scientific result changed: NO.

## MODERATE-05 — Title and high-level claims could imply biological progression forecasting.

**Response.** We agree. Use segmentation-change terminology and scan prediction/forecast/clinical claims.

**Change made.** Title; Abstract; Introduction; Discussion; TARGET_SEMANTICS_LANGUAGE_AUDIT.csv

**Evidence.** target semantics authority. Scientific result changed: NO.
