# Stage B launch test report

The focused synthetic/static regression suite was executed with the isolated test environment. Exit code: `0`. Result: `72 passed, 2 warnings, 21 subtests passed`.

Pre-outcome authority checks: PASS — protocol ZIP hash; amendment ZIP hash; 113 patients; 113 unique patients; 113 unique cases; excluded IDs absent; zero overlap with locked 40; 113 P0 rows; 113/113 P0 hash matches; no P0 regeneration; original 115 shard assignment retained; shard counts 29/27/29/28; locked method hashes exact; evaluation hashes exact; statistics hash exact.

Synthetic method/evaluation/statistics checks: PASS — Fixed; Naive; EIA-linear; EIA-blend-0.90; EIA-blend-0.75; EIA-morph; Full PCC; No-smoothing sole smoothing difference; ten Full PCC rounds; P10 final state; threshold 0.5; Dice@0.5; target-volume top-k; Wilcoxon two-sided with `zero_method=wilcox`; exactly-two Holm; 10,000 bootstrap replicates; seed 20260803; failure-neutralization contract.

Boundary checks: PASS — no model training; no predictor forward; no P0 modification; no future mask array read; no result-dependent configuration; no LUMIERE execution.

Raw pytest stdout, stderr, and exit code are retained beside this report.
