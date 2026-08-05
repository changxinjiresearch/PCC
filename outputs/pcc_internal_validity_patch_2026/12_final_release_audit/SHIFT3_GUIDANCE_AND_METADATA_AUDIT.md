# SHIFT-3 Guidance and Metadata Audit

## Audited files

- Full PCC source: `outputs/pcc_internal_validity_patch_2026/10_raw_statistical_inputs/imperfect_guidance/IMPERFECT_GUIDANCE_REPEAT_METRICS.csv`; SHA-256 `a5f56a2c43cb3d45cc8ef59970181c45214348caba45bbbd4dc95a0e3a84a4a4`.
- No-smoothing source: `outputs/pcc_internal_validity_patch_2026/03_no_smoothing_robustness/NO_SMOOTHING_REPEAT_METRICS.csv`; SHA-256 `8c6ff547a69d84695d464e599b1ed253182ab82c13680cae5de6d2849f880ebe`.
- Derived metadata correction: `03_no_smoothing_robustness/NO_SMOOTHING_REPEAT_METRICS_METADATA_CORRECTED.csv`; original retained unchanged.
- Execution code: `10_raw_statistical_inputs/execution_code/run_internal_completion_2026.py` (Full PCC imperfect-guidance writer, SHIFT-3 construction at lines 184--185); `10_raw_statistical_inputs/execution_code/run_internal_validity_patch.py` (No-smoothing reader/construction at lines 46--47 and guidance-count assertion at line 80); Kaggle launch notebooks are archived alongside them.

## Key matching

- Full PCC SHIFT-3 rows: **240**.
- No-smoothing SHIFT-3 rows: **240**.
- Key: `case_id + condition + repeat`; repeat is the six signed shift directions and is also the displacement field.
- Key missing: **0**.
- Key extra: **0**.
- Duplicate keys: Full PCC **0** rows; No-smoothing **0** rows.
- Guidance voxel-count mismatches: **0**.
- Shift-direction mismatches: **0**.
- Seed mismatches: **0** (both sources record SHIFT-3 seed as null).

## Guidance logic

Both execution paths use the same deterministic `shift_no_wrap(clean, direction)` construction for each locked case and each of `+x`, `+y`, `+z`, `-x`, `-y`, `-z`. The No-smoothing path matches each source PCC row by case, condition, and repeat and asserts the reconstructed guidance voxel count equals the source count before applying the predictor. The comparison contains one matched row for every key, with zero voxel-count, direction, or seed mismatches. This is sufficient evidence that the actual SHIFT-3 guidance input was identical; the later No-smoothing prediction is a distinct smoothing variant and was not rerun here.

## Metadata discrepancy and correction

The two discrepant fields are `retained_true_target_fraction` and `added_false_positive_volume`. Full PCC writes the realized values from the shifted guidance (`(guide & clean).sum()/clean.sum()` and `(guide & ~clean).sum()`), whereas the No-smoothing writer emits fixed descriptive defaults `1.0` and `0`. The No-smoothing execution code uses the guidance array itself for the PCC update; these fields are not used as predictor inputs. Therefore the discrepancy is a **metadata-only recording error**, not a change to guidance, probability maps, Dice, IoU, or any other scientific result.

- Corrected rows/field changes: **480**.
- Scientific result cell changes: **0**.
- Authorized metadata cell changes: **480**.
- Correction log: `12_final_release_audit/SHIFT3_METADATA_CORRECTION_LOG.csv`.

## Final determination

**PASS** — actual guidance identity is supported by archived execution code, the guidance-count assertion, and zero-mismatch key comparison. The original No-smoothing CSV is preserved byte-for-byte; only the independent metadata-corrected derivative changes the two authorized descriptive fields.
