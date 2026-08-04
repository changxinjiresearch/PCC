# Internal Paper Readiness Report

## Main-text ready

- Frozen leakage-free Layer 2 main experiment (version 8).
- Correct-target versus shuffled-target counterfactual.
- Prespecified mechanism ablations, including the adverse-to-hypothesis smoothing result.
- Case-level failure/boundary analysis.
- Automatically rank-selected qualitative panels with source maps.

## Supplementary-material ready

- Complete 2×2 term factorial.
- Imperfect-guidance robustness with within-case aggregation of five FP seeds, six shifts, and 30 mixed repeats.
- Target-construction robustness with separate same-definition and original-clean evaluations.
- Retrospective future-image difference control, explicitly labelled non-deployable.
- Dataset identity, donor mapping, statistical family definitions, and deterministic generator tests.

## Human decision required

Layer 1 Formal v1 is provisionally favored by provenance, prespecification, leakage control, reproducibility, and methodological clarity. The final manuscript primary-protocol choice between v1 and v1.1 remains `HUMAN_DECISION_REQUIRED`; performance magnitude was not used to decide.

## Not ready / excluded from this phase

- No LUMIERE or other external validation was run.
- Unrecoverable historical downstream definitions are not represented as historical reproductions.
- The new results must not be merged with old Word-report numerical values.

## Claims requiring restraint

- Do not call PCC deployment-level future prediction.
- Do not claim predictor parameter learning during PCC correction.
- Do not claim PCC is superior to aggressive EIA blends.
- Do not claim Gaussian smoothing is beneficial: the locked no-smoothing ablation performed better on this cohort.
- Do not claim absence of failure modes merely because frozen PCC beat Fixed in 40/40 main cases.

Subject to the Layer 1 human protocol decision and later external-validation phase, the internal result package is ready for manuscript drafting and supplementary reporting.
