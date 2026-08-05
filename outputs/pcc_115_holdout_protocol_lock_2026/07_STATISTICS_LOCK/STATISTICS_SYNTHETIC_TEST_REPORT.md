# Statistics synthetic test report

Scope: synthetic patient-level difference vectors only. Tests cover all-zero Wilcoxon handling, two-sided `zero_method=wilcox`, average ranks for ties, rank-biserial direction, Cohen's dz with zero SD, exactly-two Holm adjustment, percentile paired bootstrap, wins/ties/losses and finite-input rejection. No 115-patient result was read.

Result: PASS. Verified by saved pytest output; relevant checks protocol tests 29–31 and the holdout-statistics unit tests pass.
