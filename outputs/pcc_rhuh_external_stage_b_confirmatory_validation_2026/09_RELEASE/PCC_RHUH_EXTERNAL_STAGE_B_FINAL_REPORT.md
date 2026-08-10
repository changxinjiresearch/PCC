# PCC RHUH External Stage B final report

This is an independent cross-dataset external technical validation. Fixed/P0 is the frozen future-blind external prediction. Full PCC and No-smoothing PCC use the realized recurrence-change target and therefore represent retrospective target-conditioned correction, not prospective recurrence forecasting, deployment-time future prediction, or clinical validation.

RHUH segmentation > 0 is the prelocked closest available pathological-region mapping and is not perfect ontology equivalence with the internal MU mask.

- confirmatory patients: 39
- case-method rows: 273
- Full PCC trajectory rows: 390
- failed patients: 0
- Fixed mean Dice@0.5: 0.189500178907
- Full PCC mean Dice@0.5: 0.365426900711
- No-smoothing PCC mean Dice@0.5: 0.451227277145
- Full PCC P1 mean Dice@0.5: 0.20126560836
- Full PCC P10 mean Dice@0.5: 0.365426900711
- late-degradation cases: 0; P10 retained for every case
- model training/fine-tuning/P0 regeneration: none
- post-outcome scientific config changes: 0
- LUMIERE: false

## Full PCC vs Fixed

- n: 39
- mean_difference: 0.17592672180407568
- median_difference: 0.1853165072216912
- wins: 39
- ties: 0
- losses: 0
- wilcoxon_p_two_sided: 3.637978807091713e-12
- holm_adjusted_p: 7.275957614183426e-12
- bootstrap_95ci_low: 0.15085505697494797
- bootstrap_95ci_high: 0.19916239291277402
- cohens_dz: 2.236074987445618
- rank_biserial: 1.0
- confirmatory_success: True

## No-smoothing PCC vs Full PCC

- n: 39
- mean_difference: 0.08580037643316532
- median_difference: 0.08833724180671815
- wins: 38
- ties: 0
- losses: 1
- wilcoxon_p_two_sided: 7.275957614183426e-12
- holm_adjusted_p: 7.275957614183426e-12
- bootstrap_95ci_low: 0.07161981698837586
- bootstrap_95ci_high: 0.1005533622159637
- cohens_dz: 1.8073467410504533
- rank_biserial: 0.9974358974358974
- confirmatory_success: True
