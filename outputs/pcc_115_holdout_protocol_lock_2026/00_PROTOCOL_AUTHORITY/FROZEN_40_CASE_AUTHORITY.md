# Frozen 40-case authority

ZIP: `PCC_INTERNAL_VALIDITY_PATCH_2026_COMPLETE.zip`
Expected SHA-256: `f76969a789e1d7e30d8bc32a9c79bdabf2471a92ea305a1d8b23fe40a7120d99`
Git baseline: `38181335557214d53147591e29ac4e1a8e132df5`

The historical notebook under `archive/` is read-only. Cohort selection is authoritative from `experiments/audit_cohort_selection.py` and the saved 40-case cohort audit: patient directories and timepoints are sorted deterministically; a usable timepoint has exactly one brain T1c and one tumor mask; each patient contributes the earliest two usable timepoints; the first 40 eligible patients are locked in sorted patient-ID order.

The current CPU preflight verified the five checkpoint hashes in the Kaggle source and created no model output.
