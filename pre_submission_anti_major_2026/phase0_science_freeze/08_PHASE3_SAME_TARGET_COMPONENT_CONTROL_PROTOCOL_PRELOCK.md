# Phase 3 same-target component controls — protocol skeleton

Role: `POST_PRIMARY_PRESPECIFIED_ROBUSTNESS`, cohorts Internal 113 and RHUH 39. All variants use the same frozen P0, target T, region R, eta, clipping, float32, ten rounds, and P10 formal output.

Variants: FULL_PCC; NO_ERROR_GUIDED_TERM (remove +eta*S, retain outside suppression); NO_OUTSIDE_SUPPRESSION (retain +eta*S, remove outside suppression); NEITHER_TERM (remove both, label unchanged-P0 structural negative control); NO_SMOOTHING (S=D, all other canonical terms unchanged). P1 may be descriptive only; formal endpoint remains P10.

Shuffled-target negative control: patient-level deterministic derangement separately within Internal 113 and RHUH 39; no self-donor; fixed seed and donor mapping persisted/hashed before interpretation; donor target guides correction while recipient clean target evaluates it. All results are descriptive/supporting. No automatic 5–10-test Wilcoxon family or new Holm family.
