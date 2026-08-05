# No-smoothing robustness follow-up

This is a **posthoc discovery-driven, prospectively locked robustness follow-up**. It does not redefine canonical PCC and is not an original prespecified main analysis.

Both Kaggle shards completed: 20 cases and 860 repeat rows each, zero failed cases. The merged table contains 1,720 unique case–condition–repeat rows for 40 cases. Random repeats were averaged within case before all inference.

## Findings

No-smoothing was higher than Full PCC under clean guidance (top-k Dice 0.500140 versus 0.388421; fixed-0.5 Dice 0.326306 versus 0.275815). Across the tested conditions, No-smoothing was not significantly worse than Full PCC: it was significantly better under Clean, Partial-50, FP-25 and Shift-3, with no significant difference under Partial-25 and Mixed. The magnitude of the clean-guidance advantage was substantially attenuated under partial, shifted, and mixed guidance, although No-smoothing did not perform significantly worse than Full PCC in any tested condition.

- PARTIAL_50 top-k robustness difference-in-differences: -0.072309 (95% bootstrap CI -0.085454 to -0.060149; Holm p=9.09e-12).
- PARTIAL_25: -0.103200 (-0.123477 to -0.084504; Holm p=9.09e-12).
- SHIFT_3: -0.100156 (-0.124535 to -0.077976; Holm p=9.09e-12).
- MIXED: -0.109777 (-0.136265 to -0.085682; Holm p=9.09e-12).
- FP_25 alone did not show worse top-k retention: +0.001873 (0.000163 to 0.003863; Holm p=0.3682). Its fixed-0.5 difference-in-differences was +0.001961 and Holm-significant.

No-smoothing had *lower*, not higher, mean outside-clean-target probability mass than Full PCC in CLEAN and every degraded condition. Therefore its poorer robustness to partial/shifted guidance is not explained by greater total outside-target mass in this audit.

## Decision boundary

No-smoothing is not automatically promoted to the primary method. Full PCC remains the prespecified canonical method; No-smoothing remains a posthoc candidate variant for a separately pre-locked 115-person and external validation protocol. The SHIFT-3 metadata audit found 240/240 key matches and zero guidance-count, direction or seed mismatches; the apparent `retained_true_target_fraction=1.0` and `added_false_positive_volume=0.0` values were writer defaults only. The original repeat-level CSV is preserved, and the metadata-corrected derivative changes only those two descriptive fields.
