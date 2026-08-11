# Outcome-access policy

## Future-blind Stage A

May access current MRI, current segmentation, geometry, eligibility metadata, and frozen checkpoints. It may not access evaluated-case future voxel data, future segmentation/target, performance, future-derived sampling, or future-derived checkpoint selection. Pre-outcome geometry audits may inspect headers/shape/affine/orientation only.

## Retrospective Stage B

Only after P0 freeze, SHA freeze, and eligibility lock may future segmentation/target be accessed for PCC, No-smoothing, target-access controls, and evaluation. Current-mask robustness must use a clean frozen target; perturbation never changes the ground-truth definition.
