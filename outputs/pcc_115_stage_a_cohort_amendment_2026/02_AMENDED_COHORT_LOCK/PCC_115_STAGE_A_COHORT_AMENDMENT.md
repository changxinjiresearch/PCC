# PCC 115 Stage A Cohort Amendment

The original independent internal holdout cohort contained 115 patients. After Stage A future-blind P0 generation, a pre-outcome identity audit found that PatientID_0113 and PatientID_0132 had identical current T1c, current mask and future T1c files/arrays, but different future tumor-mask files/arrays.

The two cases therefore cannot be treated as two independently and uniquely attributable patient-level confirmatory observations. Neither case is selected by label or future performance; both are excluded. The anomaly is recorded only as `DATA_IDENTITY_OR_LABEL_ASSIGNMENT_ANOMALY`, without asserting a more specific cause.

The exclusion occurred before target construction, PCC execution, performance calculation and any outcome unblinding. The original 115-person manifest and all 115 frozen P0 files remain permanently retained for audit. The amended primary confirmatory cohort is fixed at 113 patients. Future Stage B confirmatory work, if separately authorized, may read only `LOCKED_113_CONFIRMATORY_CASE_MANIFEST.csv`.

PatientID_0113 and PatientID_0132 must not enter primary or secondary patient-level statistics. They may be disclosed only as a data-quality anomaly in supplementary material.
