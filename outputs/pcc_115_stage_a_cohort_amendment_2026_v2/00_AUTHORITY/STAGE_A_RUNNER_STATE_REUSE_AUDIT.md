# Stage A Runner State-Reuse Audit

## Scope and authority

- Audited Kaggle kernel: `jeechangxin/pcc-115-holdout-stage-a-p0-freeze-2026`, current submission version 3.
- The pulled current notebook checks out repository commit `66269681e4417dccabc68ecaa792d76e19aa5856` and calls `execute_stage_a_all_shards`.
- `ACTUAL_KAGGLE_V3_RUNNER_SNAPSHOT.py` is the runner taken from that exact commit. Its SHA-256 is `15ca3edd60fb984d0b3bc35bdeaaaf70edf32c246fe006b44fd2d3f0f451a98c`, identical to the present repository copy.
- This audit read only current T1c, current mask, frozen checkpoints, runner source, execution log, P0/access records and completion markers. It did not read a future image, future mask or target and did not compute performance.

## Case-loop findings

| Check | Evidence in actual runner | Result |
|---|---|---|
| Each case reads its own current T1c and mask | Lines 142–143 obtain both paths from the current `record` and call `nib.load` inside the patient loop. The two access JSON files name the correct patient-specific files. | PASS |
| Input tensor rebuilt per case | Line 146 calls current-only preprocessing and creates `batch` inside the loop. | PASS |
| Five-fold prediction accumulator reset | Line 146 assigns `predictions=[]` inside the loop. | PASS |
| Per-fold slice accumulator reset | Line 149 assigns `slices=[]` inside the fold loop. | PASS |
| Ensemble rebuilt per case | Line 152 constructs `p0` from that case's newly populated `predictions`. | PASS |
| Output path is case-unique | Line 154 uses `record["output_p0_path"]`. The locked manifest gives different paths for 0113 and 0132. | PASS |
| Atomic rename source can cross cases | Lines 36–45 create a unique `NamedTemporaryFile` in the destination directory, validate that exact temporary file, and replace only the current case path. No shared fixed temporary name exists. | NO |
| Completion marker records correct case | Line 156 derives both marker filename and JSON `case_id` from the current record. The two persisted markers contain their respective case IDs and shard 2. | PASS |
| Prior-case array/cache reused | Case-local `t1c`, `mask`, `prepared`, `batch`, `predictions`, `slices`, `p0`, `output`, and `digest` are all rebound in the loop. Only the five immutable eval-mode model objects are intentionally shared. | NO EVIDENCE |
| Same-shard file copy | Runner imports no copy operation and contains no `copy`, `copyfile`, hard link or shard-to-shard copy path. | NO |

## Shard 2 focus

- 0113 is manifest row index 34 and 0132 is row index 42 (zero-based); they are separated by seven other patient records in the all-shards execution order.
- Both records carry `stage_a_shard=2`, but execution is patient-by-patient over the 115-row manifest. There is no persistent shard-level prediction accumulator.
- Their access logs identify different current file paths and the correct case IDs.
- Their completion markers identify the correct case IDs and both bind the recorded P0 digest `64c63ef2a43237ff28afb2922e48a2e9a1e08223e55e3f21667e092fef12afcf`.

## Independent reproduction evidence

The two current-only inputs were forwarded independently on CPU with the exact five locked checkpoint files (all checkpoint SHA-256 values matched), the same model, float32 inference and equal 0.2 weights. Every corresponding fold output was byte-identical between 0113 and 0132, and the two newly produced ensembles were byte-identical. This is the expected consequence of the separately established byte-identical two-channel inputs.

The CPU ensembles are not byte-identical to the original P100 ensembles (`max_abs_diff=7.796287536621094e-05`, `mean_abs_diff=4.452454405168282e-09` for both cases). The equality and identical difference profile across both cases, together with the different CPU/GPU execution backends, do not provide evidence of a patient-state write error.

## Conclusion

No result reuse, accumulator leakage, stale ensemble, wrong atomic-rename source, incorrect marker identity, cache pollution or same-shard file-copy mechanism was found. The duplicate P0 is explained by duplicate current-only source data and duplicate preprocessed model input, not by runner state reuse.

This conclusion does not convert Stage A to PASS. The required disposition is `DATASET_DUPLICATE_INPUT_REQUIRES_HUMAN_DECISION` pending the 155-patient current-only duplicate audit and a human cohort-lock decision.
