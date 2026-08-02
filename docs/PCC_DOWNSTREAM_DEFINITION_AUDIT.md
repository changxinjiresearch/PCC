# PCC downstream definition audit

Audit scope: downstream experiments that consume the immutable
`PCC_LEAKAGE_FREE_RERUN_2026` Kaggle version 8 P0 maps and clean targets.

Evidence priority was: executable historical notebook; matching saved
artifacts; migrated implementation/tests; formal config/manifest; report;
inference. No method was promoted because its historical result was favorable.

## Locked common inputs

- Exactly 40 version-8 `P0_float32.npy` held-out maps.
- Their matching version-8 clean target arrays.
- Locked case and fold manifests.
- Canonical PCC operation order in `src/models/pcc.py`.
- Main metric mode: top-k Dice/IoU against the explicitly stated evaluation
  target; fixed-0.5 metrics remain secondary.
- No predictor retraining.

## Definition decisions

| Experiment | Scientific question | Historical evidence | Operation and parameter evidence | Guidance / evaluation target | Status | Reason |
|---|---|---|---|---|---|---|
| Full PCC | Reference retrospective correction | Notebook cell 110; migrated PCC tests; v8 P1–P10 | canonical rounds=10, eta=0.30, radius=26, sigma=2.0 | clean / clean | `RECOVERED_AND_LOCKED` | Executed and frozen in v8 |
| One-round PCC | Does iteration beyond one update matter? | Expanded report Table 33I; saved v8 P1 | use saved P1; all update terms unchanged | clean / clean | `RECOVERED_AND_LOCKED` | No recomputation needed |
| No target reinforcement | Contribution of target residual term | Table 33I | label says remove reinforcement, but no surviving executable variant specifies whether residual, smoothed target signal, or both are removed | clean / clean | `PARTIALLY_RECOVERED` | Formula not uniquely recoverable |
| No outside/background suppression | Contribution of outside-support suppression | Table 33I | named term is visible in canonical code, but the exact historical ablation code and persistence dtype are absent | clean / clean | `PARTIALLY_RECOVERED` | Report wording alone is insufficient implementation authority |
| No region constraint | Role of pathology-constrained support | Table 33I | “apply target-comparison globally” is reported; interaction with outside-support suppression is not uniquely specified | clean / clean | `PARTIALLY_RECOVERED` | Removing support can implicitly remove a second mechanism |
| No smoothing | Role of residual smoothing | User-specified family; canonical code has Gaussian residual smoothing | no formal historical ablation row, grid, or output contract found | clean / clean | `NOT_RECOVERABLE` | Would be a new experiment rather than recovered historical ablation |
| Shuffled target | Dependence on correct case guidance | Base report Tables 26–27 | historical aggregate exists, but exact seed, permutation and donor mapping are absent | donor / recipient clean | `PARTIALLY_RECOVERED` | Cannot guarantee deterministic patient-disjoint mapping |
| Mismatched target | Dependence on correct target identity | No distinct locked formal definition found | unavailable | donor / recipient clean | `NOT_RECOVERABLE` | Not separable from shuffled-target evidence |
| Spatially displaced target | Dependence on spatial correspondence | Imperfect report contains Shift-3 summary | axis/direction/boundary rule are not reported | shifted / clean | `PARTIALLY_RECOVERED` | Shift magnitude alone is insufficient |
| Difference-map control | Whether generic discrepancy-map access explains gain | Base integrated report mentions the family | exact equation and parameters absent from migrated code and formal cells | unresolved / clean | `NOT_RECOVERABLE` | No executable authority |
| No-target control | Whether target-free iteration explains gain | v8 Naive already provides a target-free iterative comparator | exact PCC-with-target-term-removed variant unresolved | none / clean | `PARTIALLY_RECOVERED` | Naive remains available; a new named PCC variant is not inferred |
| Imperfect Clean | Reference guidance | Imperfect-target report | clean target identity is exact | clean / clean | `RECOVERED_AND_LOCKED` | Equal to frozen v8 retrospective guidance; no rerun needed |
| Partial-50 | Incomplete guidance robustness | Imperfect report Tables 7–11 | retained fraction summary only; sampling/morphology/seed continuation absent | degraded / clean | `PARTIALLY_RECOVERED` | Generator cannot be reproduced |
| Partial-25 | Severe incomplete guidance | same | same | degraded / clean | `PARTIALLY_RECOVERED` | Generator cannot be reproduced |
| FP-25 | False-positive contamination | same | amount summarized; placement distribution/support/seed absent | degraded / clean | `PARTIALLY_RECOVERED` | Generator cannot be reproduced |
| Shift-3 | Spatial displacement | same | magnitude 3 reported; axis/direction/padding absent | degraded / clean | `PARTIALLY_RECOVERED` | Generator cannot be reproduced |
| Mixed noise | Joint degradation | same | component composition/order/seed absent | degraded / clean | `PARTIALLY_RECOVERED` | Generator cannot be reproduced |
| Target A original | Dependence on target construction | Expanded report Table 33AB | `future_mask AND NOT current_mask` | A / A | `RECOVERED_AND_LOCKED` | Equal to v8 clean target; frozen result reused |
| Target B eroded current | Boundary definition sensitivity | Table 33AB | erosion iterations=2 | B / B | `PARTIALLY_RECOVERED` | structuring element/connectivity absent |
| Target C boundary tolerant | Boundary tolerance | Table 33AB | dilate original, iterations=2 | C / C | `PARTIALLY_RECOVERED` | structuring element/connectivity absent |
| Target D large-change-only | Fragment sensitivity | Table 33AB | components with min 100 voxels and at least 10% of largest | D / D | `PARTIALLY_RECOVERED` | component connectivity absent |
| Sensitivity rounds=5/15 | Round-count stability | Base report Table 30 | canonical other settings; rounds in {5,15} | clean / clean | `RECOVERED_AND_LOCKED` | Exact grid maps to canonical argument |
| Sensitivity eta=0.20/0.40 | Update-strength stability | Table 30 | canonical other settings; eta in {0.20,0.40} | clean / clean | `RECOVERED_AND_LOCKED` | Exact grid maps to canonical argument |
| Sensitivity radius=18/34 | correction-support stability | Table 30 | canonical other settings; radius in {18,34} | clean / clean | `RECOVERED_AND_LOCKED` | Exact grid maps to canonical argument |
| Sensitivity sigma=1.0/3.0 | residual-smoothing stability | Table 30 | canonical other settings; sigma in {1.0,3.0} | clean / clean | `RECOVERED_AND_LOCKED` | Exact grid maps to canonical argument |
| update sigma | Separate update smoothing | no independent canonical parameter exists | unavailable | clean / clean | `NOT_RECOVERABLE` | Cannot split one historical sigma into a new parameter |
| reinforcement strength | Independent reinforcement coefficient | no independent canonical parameter exists | unavailable | clean / clean | `NOT_RECOVERABLE` | Canonical eta jointly scales residual update |
| suppression strength | Independent suppression coefficient | no independent canonical parameter exists | unavailable | clean / clean | `NOT_RECOVERABLE` | Canonical eta jointly scales suppression |

## Exact commands

- Frozen one-round analysis:
  `python3 reproductions/pcc_leakage_free_v8/analyze_version8.py --input <verified-v8-small-files> --output outputs/pcc_leakage_free_rerun_2026_v8/18_integrated_statistics --freeze validation_reference/frozen_refs/pcc_leakage_free_rerun_2026_v8`
- Locked sensitivity execution (Kaggle, frozen-output dependency):
  `python experiments/run_pcc_downstream.py --family sensitivity --frozen-root <mounted-v8-artifact-root> --output-root /kaggle/working/pcc_downstream_v8`

Only entries marked `RECOVERED_AND_LOCKED` are eligible for execution. A
reported historical aggregate is not itself an executable definition.
