# PCC 115 Stage A Duplicate-P0 Final Audit

Date: 2026-08-06

## Result

- Actual frozen P0 files: 115
- Distinct P0 SHA-256 values: 114
- Duplicate P0 groups: 1
- Duplicate group: `PatientID_0113_T1_to_T2_t1c`, `PatientID_0132_T1_to_T2_t1c`
- Duplicate P0 SHA-256: `64c63ef2a43237ff28afb2922e48a2e9a1e08223e55e3f21667e092fef12afcf`
- Distinct final current-only model inputs across 155 patients: 154
- Final disposition: `DATASET_DUPLICATE_INPUT_REQUIRES_HUMAN_DECISION`

The two affected patients have identical current T1c and current mask files, identical current-only preprocessing, and identical final two-channel tensors. Five-fold independent CPU reproductions were identical to each other for every fold and for the ensemble. Runner review found no result-reuse or cross-case write mechanism.

## Limited longitudinal identity check

For both patients and both current channels, the two approved local views had identical inode, file SHA-256, float32 array SHA-256, shape, affine, orientation and spacing. No later-timepoint or target file was read.

## Amendment

Rule A amendment: retain both patients, do not alter the cohort lock or frozen P0, and wait for human cohort adjudication. Stage B and LUMIERE remain forbidden.

## Test repair

`test_21_no_stage_b_outputs` now detects actual Stage B result directories and Stage B result/metric/trajectory/performance files. It no longer treats the required `PCC_115_STAGE_A_READINESS_FOR_STAGE_B.md` filename as Stage B output.

Test result: `30 passed`, `0 deselected`, `0 failed`, exit code `0`.

## Version and safety gates

The P0-producing Kaggle submission is kernel version 3. No model was rerun, no P0 was regenerated, no performance was computed, and Stage B/LUMIERE were not executed. The original P0, manifest and completion markers remained unchanged (231/231 post-audit records unchanged).
