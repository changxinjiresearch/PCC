# P0 generation by cohort audit

The development and confirmatory pathways are not interchangeable. Each development patient appears as test in exactly one of five 32-train/8-test folds. Its frozen P0 was generated only by that fold's checkpoint; it was not a five-checkpoint ensemble. Training patients contributed their own future-added targets as supervised labels, which is ordinary supervised learning. The evaluated development patient's future image, future mask and target were absent from the fold that generated its held-out P0.

The 113 independent internal patients and 39 RHUH patients were absent from every predictor-training partition. For each of these patients, all five frozen development checkpoints produced current-input-only maps, combined by equal arithmetic weights of 0.2. RHUH additionally used a physically isolated current-only dataset. No evaluated-case future data entered P0 preprocessing, model selection or inference; no retraining, fine-tuning, calibration or test-time adaptation occurred.

P0_PATHWAY_AMBIGUITIES = 0
