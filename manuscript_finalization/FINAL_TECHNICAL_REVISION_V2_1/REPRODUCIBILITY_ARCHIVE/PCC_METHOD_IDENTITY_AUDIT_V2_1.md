# PCC method identity audit V2.1

- Formal name: Prediction-Comparison-Correction.
- Canonical equation: editable equation (1), logit(P_(r+1)) = logit(P_r) + eta S_r - eta O_r.
- Full PCC: 10 rounds; eta=0.30; radius=26 voxels; sigma=2.0 voxels; epsilon=1e-5; float32; P10 formal.
- Outside-support probability is suppressed, not preserved.
- No-smoothing sole scientific difference: S_r=D_r.
- Development P0: patient-disjoint out-of-fold single held-out checkpoint.
- Internal 113 and RHUH 39: five frozen checkpoints, equal weight 0.2; evaluated cases absent from training.

PCC_METHOD_IDENTITY_MISMATCHES = 0
TARGET_ACCESS_OVERCLAIMS = 0
