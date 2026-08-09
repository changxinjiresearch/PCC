
# Locked RHUH external statistical analysis plan

Inference is patient-level. The confirmatory family contains exactly Full PCC vs Fixed and No-smoothing PCC vs Full PCC on Dice@0.5. Use paired two-sided Wilcoxon signed-rank (`zero_method=wilcox`), Holm over exactly two hypotheses, alpha 0.05, and report n, paired mean/median differences, wins/ties/losses, raw and adjusted p, Cohen dz, rank-biserial, and paired bootstrap 95% CI.

Bootstrap uses exactly 10,000 patient-pair replicates and seed **20260810**, locked before results. Result-driven comparisons or seed changes are forbidden.
