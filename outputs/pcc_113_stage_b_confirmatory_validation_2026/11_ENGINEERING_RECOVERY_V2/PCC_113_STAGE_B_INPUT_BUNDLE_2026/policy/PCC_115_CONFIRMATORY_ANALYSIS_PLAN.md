# Confirmatory patient-level analysis

The confirmatory Holm family has exactly two two-sided paired Wilcoxon signed-rank tests: Full PCC versus Fixed at Dice 0.5, and No-smoothing versus Full PCC at Dice 0.5. `zero_method='wilcox'`; zeros are removed before ranking and equal nonzero absolute differences receive average ranks. An all-zero vector returns p=1 with status `ALL_ZERO`.

Report paired mean and median differences, 10,000 patient-pair percentile bootstrap replicates with seed 20260803, Cohen's dz, rank-biserial `(W+−W−)/(W++W−)`, and wins/ties/losses. A zero difference SD makes dz unavailable with `SD_ZERO`; it is never coerced to zero. Bootstrap failure blocks that inferential output. Primary success requires mean paired difference >0 and Holm-adjusted p<0.05. No-smoothing replication uses the same criterion but does not determine the Full-PCC primary result. No one-sided tests are permitted.

Locked empty targets are protocol failures; they and all other failures remain in the 115 denominator. Non-finite metrics are failures, not filtered observations. Other methods, endpoints and comparisons form a separate secondary Holm family.
