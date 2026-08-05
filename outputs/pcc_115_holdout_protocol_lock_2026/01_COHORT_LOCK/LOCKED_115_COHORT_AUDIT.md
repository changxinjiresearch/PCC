# 115-patient cohort audit

Status: PASS for the protocol-lock preflight. The completed CPU-only Kaggle kernel found 203 source patient directories, 155 patients with the required earliest-two usable timepoints, 40 locked patients, and exactly 115 remaining patients. The locked 115 manifest has one row per patient and zero overlap with the locked 40.

Pair rule: sort patient IDs ascending; within each patient sort `Timepoint_N` numerically; retain timepoints containing exactly one `*_brain_t1c.nii` and one `*_tumorMask.nii`; select the earliest two usable timepoints. Geometry and nonempty-target checks are read-only eligibility checks. No predictor, PCC, method result, or performance value is used.

The prompt's descriptive 846-pair number is not used: the authoritative local discovery code and preflight report the patient-level eligibility count and the deterministic first-pair rule.
