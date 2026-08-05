# Cohort Selection Audit

Direct read-only scanning of the mounted MU-Glioma-Post dataset found 203 patient directories and 596 timepoint directories. There were 155 patients with at least two timepoints containing exactly one current T1c and one tumour mask. Across usable timepoints, 391 adjacent-in-usable-order candidate pairs can be described, but the executed discovery code considered only each patient's earliest two usable timepoints for selection.

The authoritative manifest contains the first 40 eligible patients in sorted order and exactly matches the 40 reconstructed selections. All 40 locked triplets of current T1c, current mask, and future mask have compatible shape, affine (tolerance `1e-5`), and orientation. All locked current masks, future masks, and future-change targets are non-empty.

The dataset scan was performed after the frozen run and is an audit, not a new selection. Git history shows that deterministic discovery and non-overwriting manifest creation preceded the completed experiment. No model result enters the selection function.
