# PCC method implementation audit

Audit basis: Git `a31ee5e05ad20cd26def91ba5b9e74c36c9050a5`, dirty worktree, authoritative notebook cells 109–110, migration manifest, migrated source, tests, saved Patient 0003 package, and Stage A/B provenance.

## Trace answers

| Question | Code evidence and finding |
|---|---|
| P0 producer | `FormalTrainingProvider` calls `train_case_baseline`; `MiniUNet` receives normalized current T1c and current mask. Checkpoint and saved-map providers are alternate sources. |
| Does P0 avoid future truth? | **No for the historical case-specific formal rebuild.** `SliceDataset(..., target)` supplies T to the loss and `eval_prob_map(..., target)` selects the best epoch. This is parameter leakage even though the forward input has two current-only channels. |
| T definition | `preprocess_longitudinal_arrays`: masks `>0`, then `future & ~current`. Current normalization support uses the union of nonzero current and future T1c, which is an additional future-image preprocessing dependency. |
| Compare | `apply_pcc`: `(target_bool.astype(float32) - p) * correction_region`. It is a soft signed probability discrepancy, not a thresholded FN/FP mask or distance-transform error. |
| Correct | Gaussian-smoothed residual is added to logits; `p` outside the target-derived region is subtracted with the same eta. |
| Updated object | Probability map/logits representation only. Predictor and corrector parameters are unchanged during PCC rounds. |
| Backprop/optimizer | Present only in case-specific baseline training; absent from PCC and EIA correction. |
| Forward per PCC round | No. The baseline model runs before correction; PCC iterates directly on maps. |
| State propagation | `pcc` is assigned the clipped sigmoid result and used as `p` in the next loop iteration. |
| Reinforcement | Signed residual inside `R(T)`, including positive reinforcement where T exceeds P. |
| FP suppression | `(~R).astype(float32) * p` is subtracted in logit space. |
| Region constraint | `distance_transform_edt(~T) <= 26`. |
| Smoothing | `gaussian_filter(residual, sigma=2.0)` each round. |
| Copying risk | No direct assignment or final replacement by T. EIA blends are explicitly oracle-like. PCC nevertheless depends on exact T and must remain retrospective. |

## Canonical decision

For reproducing the **historical Formal EIA rebuild**, notebook cells 109–110 and their literal migrated modules are canonical. Tests transcribe their operation order and constants. The Patient 0003 saved package validates the artifact contract but cannot prove pixel/checkpoint equivalence.

For the **new leakage-free longitudinal specification**, the user has authorized `PCC_LEAKAGE_FREE_RERUN_2026`. Its predictor architecture, training loss, optimizer, epochs, batch size, learning rate, training-loss checkpoint criterion, preprocessing, and top-k evaluation were migrated from notebook cells 14–17. The original fold CSV is absent; a new deterministic patient-group split is locked before training and is explicitly a new run.

## Alignment classification

| Component | Classification | Reason |
|---|---|---|
| Target construction | READY for historical formal variant | Literal cell 110 migration and unit tests. |
| PCC map refinement | READY for historical formal variant | Literal cell 110 migration and unit tests; saved-artifact replay available. |
| Fixed/Naive/EIA evaluation | READY for historical formal variant | Implemented and tested, subject to an externally supplied P0. |
| Case-specific formal baseline | METHOD_DEFINITION_DIFFERENCE | Faithful historical migration, but violates leakage-free P0 contract. |
| Cross-case leakage-free P0 | PARTIALLY_MIGRATED / artifacts missing | Notebook implementations exist; no complete registered executable path or local data. |
| Round trajectories | FOUND_BUT_BROKEN for persisted contract | Notebook calculates per-round metrics but migrated `PCCResult` returns only final map, region, and signal. Scientific math is present; trajectory persistence is not. |
| Full cohort execution | HARD_DATA_BLOCKER | Required MU-Glioma-Post paths and locked case CSV are unavailable locally; pandas/scipy/nibabel/matplotlib/torch are also absent in this environment. |

No scientific source was changed. No implementation mismatch was proven that would justify changing the canonical historical algorithm.
