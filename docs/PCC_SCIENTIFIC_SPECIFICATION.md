# PCC scientific specification locked for the full rerun

## Scope and terminology

The longitudinal scientific question is retrospective, target-conditioned correction of an independently produced future-change prediction. The deployable prediction stage and the retrospective correction stage must remain distinct.

The required states are:

1. `P0 = F(X_current, M_current)`, produced without the evaluated case's future image, future mask, or future-change target;
2. `T = M_future AND NOT M_current`, unless a separately named target-construction variant is selected;
3. `E_r = (T - P_r) * R(T)` in the currently migrated formal Layer2R correction;
4. `P_(r+1)` is obtained by the canonical logit-space update and becomes the next round's state.

Fixed evaluates unchanged P0. Naive may transform P0 but must not receive T. PCC receives T retrospectively and must be described as iterative target-conditioned error-guided probability-map refinement, not parameter learning. EIA controls receive the same P0 and T and are oracle-like retrospective controls, not deployment models.

## Code-evidenced formal Layer2R definition

- Target: strict-positive masks followed by `future_mask & ~current_mask`; no registration tolerance, resampling, erosion, component filter, or boundary exclusion is implemented in the formal preprocessing path.
- Correction region: 3-D Euclidean distance to T, radius 26 voxels.
- Target signal: 3-D Gaussian smoothing with sigma 2.0 followed by whole-volume min-max normalization.
- PCC: 10 rounds, eta 0.30. Each round clips P, computes the soft signed residual inside the target-derived region, Gaussian-smooths it, suppresses P outside that region, updates logits, applies sigmoid, clips, and propagates the new P.
- The PCC correction function contains no `loss.backward()`, optimizer, model forward pass, pseudo-label, or learned correction parameters.
- Direct target copying is not present, but target conditioning is strong and explicit. The final map is not assigned to T.

## Non-conformance discovered before execution

The historical Formal EIA rebuild's so-called case-specific baseline is trained on every slice of the evaluated case using T as its supervised label, and T is also used for best-epoch selection. Its network inputs are only current T1c and current mask, but its fitted parameters are future-target-conditioned. Consequently that map is not a leakage-free P0 under this rerun specification.

This conflict must not be repaired by relabeling or tuning. The newly authorized canonical main route is `PCC_LEAKAGE_FREE_RERUN_2026`: a patient-group five-fold held-out predictor faithfully based on notebook cells 14–17, followed by immutable-P0 retrospective correction. Historical fold files did not survive locally, so the run will create a new deterministic group split and will not claim original-fold reproduction. Dataset/GPU execution remains external.

## Reporting boundary

Historical Formal EIA outputs remain valid evidence about the historical target-trained case-specific variant. They must not be reported as prospective future prediction. Layer 1, cross-case P0, imperfect guidance, target variants, Layer 3 audits, and LUMIERE are distinct families and cannot be pooled.
