# Layer 1 Formal v1 / v1.1 protocol audit

## Observation

Both completed 2026 reruns use the same 40-case cohort, the same `matched_5fold_splits_seed42.csv` fold source, current T1c as the only image input, current tumour mask as the target, patient-level held-out evaluation, AdamW (`lr=1e-3`, weight decay `1e-5`), batch size 64, seed 42, all training slices, and thresholds selected only on training predictions. The corrector in both protocols is a separately trained residual segmenter receiving current T1c plus the baseline probability; this Layer 1 corrector is not the Layer 2 probability-map refinement loop.

The material prespecified difference is training duration: Formal v1 uses 10 baseline and 10 corrector epochs; Formal v1.1 uses 15 and 15 epochs. Both save the final epoch rather than selecting a checkpoint on held-out cases. No result-dependent protocol change was identified.

## Verification

- Formal v1 authority: archived notebook cells 73–75; execution commit `7f2a7fd`; Kaggle kernel `jeechangxin/pcc-layer1-formal-v1-rerun-2026`, version 1.
- Formal v1.1 authority: archived notebook cells 77–78; execution commit `7d5c482`; Kaggle kernel `jeechangxin/pcc-layer1-formal-v1-1-rerun-2026`, version 1.
- Both completion contracts report 5 folds, 40 unique held-out cases, 5 baseline checkpoints, 5 corrector checkpoints, and zero failed cases.

## Decision boundary

Protocol authority must not be selected from the higher Dice. Formal v1 has the clearer designation as the original formal protocol; Formal v1.1 was explicitly introduced as a longer-training sensitivity analysis. A manuscript may therefore present v1 as primary and v1.1 as sensitivity, but the final designation remains a human authorship decision.
