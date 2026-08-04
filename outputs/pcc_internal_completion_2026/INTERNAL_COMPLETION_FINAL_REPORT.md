# PCC Internal Completion 2026 — Final Report

## Status

All prespecified, executable internal analyses are complete. The protocol was locked before result generation at Git commit `3ed97f2`; its canonical YAML SHA-256 is `7a36fe0689abae5552395da84b69260e081764c13bd540a2454b2e74494697c4`.

The analyses reused the frozen `PCC_LEAKAGE_FREE_RERUN_2026` version 8 held-out P0 maps and clean targets. The predictor was not retrained and no P0 was regenerated. No LUMIERE or other external-data experiment was started.

## Completion

| Family | Cases | Status | Primary output |
|---|---:|---|---|
| Mechanism ablation and 2×2 term factorial | 40 | COMPLETE | `01_mechanism_ablation/MECHANISM_CASE_METRICS.csv` |
| Patient-level shuffled-target counterfactual | 40 | COMPLETE | `02_shuffled_target/SHUFFLED_TARGET_CASE_METRICS.csv` |
| Imperfect guidance | 40 | COMPLETE | `03_imperfect_guidance/IMPERFECT_GUIDANCE_CASE_AGGREGATED.csv` |
| Target construction robustness | 40 | COMPLETE | `04_target_construction/TARGET_CONSTRUCTION_CASE_METRICS.csv` |
| Future-image difference control | 40 | COMPLETE | `05_difference_map_control/DIFFERENCE_MAP_CASE_METRICS.csv` |
| Failure and boundary analysis | 40 | COMPLETE | `06_failure_analysis/INTERNAL_FAILURE_BOUNDARY_CASES.csv` |
| Prespecified qualitative panels | 8 selections | COMPLETE | `07_qualitative_panels/` |
| Layer 1 v1/v1.1 protocol audit | two protocols | COMPLETE; HUMAN_DECISION_REQUIRED | `08_layer1_protocol_audit/` |
| Dataset identity | 40 cases / 40 patients | COMPLETE | `09_dataset_identity/` |

All experiment failure tables are empty. The merged imperfect-guidance result has 5,160 repeat-level rows and 40 unique cases. Random repeats were aggregated within case before inference.

## Principal internal results

The frozen Full PCC mean Dice was `0.388421`; Fixed P0 was `0.276207`. These values are reused references, not regenerated results.

Mechanism findings were not selected by performance. Removing the error-guided term reduced mean Dice to `0.288075`; removing outside suppression reduced it to `0.361249`. Contrary to a simple necessity interpretation, removing Gaussian smoothing increased mean Dice to `0.500140` (paired difference versus Full PCC `+0.111719`, 40/0/0 wins/ties/losses). Global discrepancy also modestly exceeded Full PCC (`0.393227`, paired difference `+0.004806`, 32/8/0). These prespecified negative findings must be retained.

The factorial identity control reproduced Fixed P0 when both terms were off, and the both-on condition reproduced frozen Full PCC case-wise.

Shuffled-target PCC mean Dice was `0.283648`, below correct-target Full PCC by `0.104773`; correct-target Full PCC was higher in 39 cases and lower in one. This supports dependence on case-specific spatial guidance, while the exceptional case remains in the boundary analysis.

For PCC, mean Dice under imperfect guidance was: Partial-50 `0.349182`, Partial-25 `0.323722`, FP-25 `0.384170`, Shift-3 `0.368439`, and Mixed `0.332755`, versus clean PCC `0.388421`. All stochastic or directional repeats were averaged within each case before paired tests.

Target-construction results are reported in two explicitly separate evaluation modes. Against the original clean target, boundary-tolerant correction yielded mean Dice `0.350328`, eroded-current `0.413138`, and large-change-only `0.388355`, versus Original `0.388421`. Same-definition evaluation values must not be mixed with these original-clean evaluations.

The gated retrospective future-image difference control passed all 40 spatial-compatibility checks. Its mean Dice was `0.047453`; it is a retrospective control, not a deployable baseline.

## Interpretation boundaries

- PCC is retrospective target-conditioned, error-guided probability-map refinement. It does not update predictor parameters.
- These analyses do not reproduce unrecoverable historical experiments; they are new prespecified 2026 analyses.
- EIA blend remains an oracle-like retrospective control.
- The smoothing ablation result weakens any claim that canonical Gaussian smoothing is necessary or optimal.
- Layer 3 evidence remains spatial reliance/localization evidence, not causal or molecular pathology evidence.
- Layer 1 v1 versus v1.1 primary-protocol selection remains a human decision; no recommendation was made from Dice magnitude.

## Verification

The output contract validator passed: mechanism 480 rows, shuffled 40, imperfect repeats 5,160, target construction 320, difference control 40, 40 unique cases, all case-level values finite, and no predictor/P0 regeneration. Full isolated tests, compile checks, format validation, artifact hashing, and final Git checks are recorded under `11_tests/` and `14_reproducibility/`.
