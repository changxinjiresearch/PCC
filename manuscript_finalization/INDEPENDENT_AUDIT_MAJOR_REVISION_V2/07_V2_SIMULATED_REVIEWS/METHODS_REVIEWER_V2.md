# Medical imaging AI methodological reviewer

**Leakage and task identity.** Development P0 is now correctly identified as single-checkpoint patient-disjoint out-of-fold inference; independent internal and RHUH P0 are distinct five-checkpoint ensembles. Training-patient future-added labels are disclosed as supervised labels, while evaluated-case future images, masks and targets are excluded from P0 inference. Current segmentation is explicitly the second model channel.

**Answer conditioning.** PCC remains an oracle-conditioned retrospective method. V2 does not claim that matched-information controls remove this limitation; Table 3 instead shows that direct target-access controls can equal or exceed PCC on selected secondary metrics. The complete PCC update, outside suppression, No-smoothing sole difference and comparator formulas are reproducible. No new experiment or result-driven inference was introduced.

**Residual risk.** A prospective or raw-MRI end-to-end use case would require new experiments, as would current-mask error propagation. These are transparently framed as future work rather than current claims.

UNRESOLVED_FATAL = 0
UNRESOLVED_MAJOR_FIXABLE_WITH_EXISTING_EVIDENCE = 0
