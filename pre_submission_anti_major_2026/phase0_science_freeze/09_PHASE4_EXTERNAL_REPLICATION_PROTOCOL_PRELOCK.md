# Phase 4 external replication — protocol skeleton

Phase 0 does not run external validation. LUMIERE is not automatically outcome-naive. Historical exposure audit must precede feasibility and determines wording.

Feasibility: longitudinal timepoints, current T1c/mask, future segmentation, no overlap, provenance, interpretable geometry without result-dependent repair, predeclared mask ontology, and sufficient cases after pre-outcome technical eligibility. No-go cannot be based on poor Dice/P0/PCC improvement; once outcomes are read, the dataset cannot be silently abandoned.

If a genuinely acceptable new cohort is locked before new outcome-performance access, Stage A uses the same frozen five checkpoints without training/calibration/TTA; P0 is float32 geometry-checked and hash-frozen. Stage B then runs Fixed, Full PCC, and No-smoothing. Skeleton confirmatory family: Full PCC vs Fixed and No-smoothing vs Full PCC, Dice@0.5, paired two-sided Wilcoxon, Holm exactly 2, 10,000 paired bootstrap and effect sizes. This remains a skeleton pending feasibility.
