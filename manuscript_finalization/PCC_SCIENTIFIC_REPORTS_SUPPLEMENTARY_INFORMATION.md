# Supplementary Information

## Target-conditioned refinement of future-blind longitudinal glioma change maps replicates across independent cohorts

[AUTHOR_LIST_REQUIRED]

## Supplementary Methods

This supplement expands reproducibility, cohort-flow, ablation, robustness, secondary metric and reporting details. All values are deterministic summaries of frozen releases; no model or correction method was rerun.

### Evidence provenance

Development authority was PCC_LEAKAGE_FREE_RERUN_2026 Kaggle version 8 plus the 2026 internal completion and validity patch. Internal confirmation used the Stage B V2 authority, whose V1 scientific CSVs were proven unchanged. RHUH used the pre-outcome protocol lock, physically isolated Stage A P0 freeze and Stage B release. SHA-256 values are listed in Supplementary Table S1 and the authority registry.

### Cohort amendments

The 113-patient cohort amendment excluded PatientID_0113 and PatientID_0132 before target construction or performance access because current T1c/current masks and future T1c were identical while future masks differed. Both were excluded rather than selecting by labels or results. All original P0 evidence was retained. RHUH-0008 was excluded before external P0 generation because lossless orientation operations did not establish a shared physical grid. No registration, interpolation or case-specific header repair was allowed.

### Development controls

Removing error guidance, removing outside suppression, no smoothing, global discrepancy, shuffled targets and imperfect guidance were evaluated without changing the frozen P0. Shuffled donors were patient-level. Imperfect-guidance repeats were aggregated within patient. No-smoothing was not the original canonical method and its development observation was explicitly treated as post-hoc.

### Spatial analyses

Layer 1 v1 was selected on provenance, not performance magnitude; v1.1 is sensitivity evidence. Layer 3 used two-sided tests and prespecified Holm families. Absolute core PRI and peritumour-control localization survived their respective corrections; several boundary and relative effects were nominal or unsupported. The manuscript therefore treats these analyses as exploratory spatial reliance/localization, not causal biology.

## Supplementary Results

### Supplementary Table S1. Authority packages

See `PCC_MANUSCRIPT_AUTHORITATIVE_EVIDENCE_REGISTRY.csv` for path, size and SHA-256 of every authority.

### Supplementary Table S2. Internal secondary metrics

The complete 64-row V2 summary reports n, mean, SD, median, Q1, Q3, IQR and 10,000-resample patient bootstrap confidence intervals for eight methods and eight locked secondary metrics. Seed was 20260803. No secondary pairwise P values were added.

### Supplementary Table S3. RHUH secondary metrics

All seven methods were summarized using n=39 and seed 20260810. Fixed future-blind means were Dice 0.190, soft Dice 0.151, Brier 0.0093 and AP 0.153. Canonical PCC means were 0.365, 0.238, 0.0065 and 0.309. No-smoothing means were 0.451, 0.270, 0.0058 and 0.404.

### Supplementary Tables S4–S6. Development robustness

Canonical PCC mean Dice was 0.388 under clean guidance; 0.349 under Partial-50, 0.324 under Partial-25, 0.384 under FP-25, 0.368 under Shift-3 and 0.333 under Mixed guidance. Correct-target PCC exceeded shuffled-target PCC by 0.105 on average, with 39 wins and one loss. No-smoothing's clean advantage attenuated under perturbation and was not significantly worse under any tested condition in the locked robustness family.

### Supplementary Table S7. Oracle-assisted controls

Target-volume-matched top-k and EIA blends use target information. Internal top-k Dice means were 0.268, 0.440 and 0.631; RHUH values were 0.207, 0.361 and 0.426. These are retrospective localization summaries.

### Supplementary Table S8. Failure accounting

Development, internal confirmatory and RHUH Stage B scientific failure tables contained zero failed patients. Denominators remained 40, 113 and 39. Engineering failures before scientific access are preserved separately and were not counted as scientific failures.

## Reporting checklists

The completed CLAIM 2024 matrix accompanies this supplement. TRIPOD+AI was applied only to the future-blind predictor component; PROBAST+AI informed an internal risk audit. Public URLs and final author metadata remain submission actions.


## Supplementary data tables

### Supplementary Table S2. Internal secondary summary

| Method | Metric | n | Mean | SD | Median | Q1 | Q3 | CI low | CI high |
|---|---|---|---|---|---|---|---|---|---|
| Fixed | IoU_0.5 | 113 | 0.1428 | 0.09134 | 0.1363 | 0.08025 | 0.1872 | 0.1265 | 0.1601 |
| Fixed | precision_0.5 | 113 | 0.2647 | 0.2096 | 0.2053 | 0.105 | 0.3947 | 0.2269 | 0.3036 |
| Fixed | recall_0.5 | 113 | 0.4287 | 0.2542 | 0.3867 | 0.223 | 0.59 | 0.3814 | 0.4749 |
| Fixed | soft_Dice | 113 | 0.1852 | 0.112 | 0.1837 | 0.103 | 0.2431 | 0.165 | 0.2062 |
| Fixed | Brier | 113 | 0.004523 | 0.004734 | 0.003303 | 0.001627 | 0.005121 | 0.003719 | 0.00544 |
| Fixed | average_precision | 113 | 0.2272 | 0.1624 | 0.188 | 0.09859 | 0.3366 | 0.1977 | 0.2581 |
| Fixed | predicted_positive_volume | 113 | 3.181e+04 | 2.191e+04 | 2.517e+04 | 1.541e+04 | 4.355e+04 | 2.784e+04 | 3.585e+04 |
| Fixed | target_to_predicted_volume_ratio | 113 | 1.25 | 1.837 | 0.5285 | 0.195 | 1.23 | 0.9356 | 1.606 |
| Naive | IoU_0.5 | 113 | 0.1428 | 0.09134 | 0.1363 | 0.08025 | 0.1872 | 0.1264 | 0.1602 |
| Naive | precision_0.5 | 113 | 0.2647 | 0.2096 | 0.2053 | 0.105 | 0.3947 | 0.2275 | 0.3034 |
| Naive | recall_0.5 | 113 | 0.4287 | 0.2542 | 0.3867 | 0.223 | 0.59 | 0.3818 | 0.4759 |
| Naive | soft_Dice | 113 | 0.2244 | 0.1269 | 0.2243 | 0.1395 | 0.2905 | 0.2013 | 0.2482 |
| Naive | Brier | 113 | 0.00478 | 0.004989 | 0.003434 | 0.00163 | 0.005516 | 0.00392 | 0.005746 |
| Naive | average_precision | 113 | 0.2267 | 0.1625 | 0.1878 | 0.09874 | 0.3366 | 0.1975 | 0.2573 |
| Naive | predicted_positive_volume | 113 | 3.181e+04 | 2.191e+04 | 2.517e+04 | 1.541e+04 | 4.355e+04 | 2.791e+04 | 3.593e+04 |
| Naive | target_to_predicted_volume_ratio | 113 | 1.25 | 1.837 | 0.5285 | 0.195 | 1.23 | 0.9292 | 1.613 |
| EIA-linear | IoU_0.5 | 113 | 0.1834 | 0.1103 | 0.1764 | 0.1088 | 0.2388 | 0.1637 | 0.2037 |
| EIA-linear | precision_0.5 | 113 | 0.3132 | 0.2349 | 0.2503 | 0.1274 | 0.4548 | 0.2706 | 0.3565 |
| EIA-linear | recall_0.5 | 113 | 0.508 | 0.2561 | 0.4872 | 0.3042 | 0.6902 | 0.46 | 0.5541 |
| EIA-linear | soft_Dice | 113 | 0.2602 | 0.1492 | 0.2606 | 0.1485 | 0.385 | 0.2329 | 0.2883 |
| EIA-linear | Brier | 113 | 0.003341 | 0.002776 | 0.002608 | 0.001387 | 0.004138 | 0.002857 | 0.003871 |
| EIA-linear | average_precision | 113 | 0.3611 | 0.2364 | 0.3232 | 0.1654 | 0.5269 | 0.3181 | 0.405 |
| EIA-linear | predicted_positive_volume | 113 | 3.223e+04 | 2.276e+04 | 2.592e+04 | 1.464e+04 | 4.6e+04 | 2.825e+04 | 3.651e+04 |
| EIA-linear | target_to_predicted_volume_ratio | 113 | 1.145 | 1.686 | 0.5302 | 0.2063 | 1.19 | 0.8602 | 1.471 |
| EIA-blend-0.90 | IoU_0.5 | 113 | 0.1568 | 0.09854 | 0.1464 | 0.09721 | 0.2065 | 0.1392 | 0.1756 |
| EIA-blend-0.90 | precision_0.5 | 113 | 0.294 | 0.224 | 0.2377 | 0.1182 | 0.435 | 0.253 | 0.3365 |
| EIA-blend-0.90 | recall_0.5 | 113 | 0.4342 | 0.2537 | 0.3848 | 0.2277 | 0.5965 | 0.3878 | 0.4808 |
| EIA-blend-0.90 | soft_Dice | 113 | 0.2123 | 0.1212 | 0.2088 | 0.1241 | 0.2862 | 0.1901 | 0.2343 |
| EIA-blend-0.90 | Brier | 113 | 0.003808 | 0.003966 | 0.002786 | 0.001385 | 0.004373 | 0.003123 | 0.004585 |
| EIA-blend-0.90 | average_precision | 113 | 0.3588 | 0.1943 | 0.3191 | 0.2157 | 0.5073 | 0.3237 | 0.3949 |
| EIA-blend-0.90 | predicted_positive_volume | 113 | 2.892e+04 | 2.039e+04 | 2.255e+04 | 1.345e+04 | 4.069e+04 | 2.528e+04 | 3.273e+04 |
| EIA-blend-0.90 | target_to_predicted_volume_ratio | 113 | 1.338 | 1.921 | 0.5724 | 0.2242 | 1.389 | 1.012 | 1.709 |
| EIA-blend-0.75 | IoU_0.5 | 113 | 0.1991 | 0.1174 | 0.1869 | 0.1311 | 0.263 | 0.1773 | 0.2204 |
| EIA-blend-0.75 | precision_0.5 | 113 | 0.3793 | 0.257 | 0.3351 | 0.1741 | 0.5898 | 0.3327 | 0.4267 |
| EIA-blend-0.75 | recall_0.5 | 113 | 0.4491 | 0.2492 | 0.4115 | 0.235 | 0.6172 | 0.4037 | 0.4956 |
| EIA-blend-0.75 | soft_Dice | 113 | 0.2532 | 0.1413 | 0.2459 | 0.1475 | 0.3632 | 0.2274 | 0.2793 |
| EIA-blend-0.75 | Brier | 113 | 0.002876 | 0.002962 | 0.002036 | 0.0009949 | 0.003301 | 0.002359 | 0.003443 |
| EIA-blend-0.75 | average_precision | 113 | 0.4779 | 0.2157 | 0.4498 | 0.3277 | 0.6499 | 0.438 | 0.5179 |
| EIA-blend-0.75 | predicted_positive_volume | 113 | 2.305e+04 | 1.731e+04 | 1.924e+04 | 9285 | 3.193e+04 | 1.996e+04 | 2.637e+04 |
| EIA-blend-0.75 | target_to_predicted_volume_ratio | 113 | 1.58 | 2.251 | 0.7209 | 0.295 | 1.957 | 1.195 | 2.017 |
| EIA-morph | IoU_0.5 | 113 | 0.1511 | 0.09465 | 0.1358 | 0.09493 | 0.1974 | 0.1343 | 0.1688 |
| EIA-morph | precision_0.5 | 113 | 0.2821 | 0.2184 | 0.2141 | 0.1117 | 0.4273 | 0.2432 | 0.3233 |
| EIA-morph | recall_0.5 | 113 | 0.4297 | 0.2557 | 0.3844 | 0.2227 | 0.6041 | 0.3835 | 0.4769 |
| EIA-morph | soft_Dice | 113 | 0.2514 | 0.1372 | 0.2391 | 0.1734 | 0.3297 | 0.2259 | 0.2765 |
| EIA-morph | Brier | 113 | 0.005195 | 0.005021 | 0.003417 | 0.001792 | 0.006601 | 0.004324 | 0.006143 |
| EIA-morph | average_precision | 113 | 0.1059 | 0.08344 | 0.08012 | 0.04958 | 0.1501 | 0.09089 | 0.1211 |
| EIA-morph | predicted_positive_volume | 113 | 2.937e+04 | 2.184e+04 | 2.359e+04 | 1.28e+04 | 3.983e+04 | 2.544e+04 | 3.348e+04 |
| EIA-morph | target_to_predicted_volume_ratio | 113 | 3.795 | 26.86 | 0.5334 | 0.2071 | 1.328 | 1.024 | 9.061 |
| Full PCC | IoU_0.5 | 113 | 0.3027 | 0.1498 | 0.3067 | 0.2104 | 0.3918 | 0.2753 | 0.3302 |
| Full PCC | precision_0.5 | 113 | 0.499 | 0.2743 | 0.4785 | 0.2805 | 0.7087 | 0.4483 | 0.5492 |
| Full PCC | recall_0.5 | 113 | 0.5404 | 0.215 | 0.5486 | 0.3767 | 0.7067 | 0.5006 | 0.5803 |
| Full PCC | soft_Dice | 113 | 0.2667 | 0.1496 | 0.2635 | 0.1626 | 0.3671 | 0.2396 | 0.2943 |
| Full PCC | Brier | 113 | 0.003102 | 0.004117 | 0.00172 | 0.0008422 | 0.003231 | 0.002414 | 0.003921 |
| Full PCC | average_precision | 113 | 0.4142 | 0.2117 | 0.4166 | 0.2552 | 0.5815 | 0.3757 | 0.4536 |
| Full PCC | predicted_positive_volume | 113 | 2.233e+04 | 1.85e+04 | 1.853e+04 | 8041 | 3.158e+04 | 1.904e+04 | 2.574e+04 |
| Full PCC | target_to_predicted_volume_ratio | 113 | 1.44 | 2.322 | 0.8266 | 0.4321 | 1.62 | 1.072 | 1.904 |
| No-smoothing PCC | IoU_0.5 | 113 | 0.4958 | 0.2014 | 0.5164 | 0.363 | 0.629 | 0.4589 | 0.533 |
| No-smoothing PCC | precision_0.5 | 113 | 0.7088 | 0.2561 | 0.7618 | 0.5467 | 0.9502 | 0.6607 | 0.754 |
| No-smoothing PCC | recall_0.5 | 113 | 0.7034 | 0.244 | 0.7441 | 0.5275 | 0.9294 | 0.6575 | 0.7463 |
| No-smoothing PCC | soft_Dice | 113 | 0.3204 | 0.1647 | 0.3259 | 0.2144 | 0.4415 | 0.2905 | 0.3506 |
| No-smoothing PCC | Brier | 113 | 0.002583 | 0.004011 | 0.001206 | 0.0005939 | 0.002499 | 0.001913 | 0.003388 |
| No-smoothing PCC | average_precision | 113 | 0.6473 | 0.1988 | 0.6639 | 0.5326 | 0.8112 | 0.6107 | 0.6825 |
| No-smoothing PCC | predicted_positive_volume | 113 | 2.03e+04 | 1.91e+04 | 1.492e+04 | 6355 | 2.606e+04 | 1.7e+04 | 2.382e+04 |
| No-smoothing PCC | target_to_predicted_volume_ratio | 113 | 1.514 | 2.212 | 1.034 | 0.7034 | 1.604 | 1.17 | 1.964 |

### Supplementary Table S3. RHUH secondary summary

| Method | Metric | n | Mean | SD | Median | Q1 | Q3 | CI low | CI high |
|---|---|---|---|---|---|---|---|---|---|
| Fixed | Dice_0.5 | 39 | 0.1895 | 0.1318 | 0.1811 | 0.08101 | 0.2697 | 0.149 | 0.2306 |
| Fixed | IoU_0.5 | 39 | 0.1105 | 0.08301 | 0.09956 | 0.04222 | 0.1559 | 0.08506 | 0.1365 |
| Fixed | precision_0.5 | 39 | 0.2422 | 0.1968 | 0.2022 | 0.064 | 0.3866 | 0.1816 | 0.3029 |
| Fixed | recall_0.5 | 39 | 0.2147 | 0.152 | 0.1606 | 0.1199 | 0.3086 | 0.1687 | 0.264 |
| Fixed | soft_Dice | 39 | 0.1512 | 0.1064 | 0.1456 | 0.06035 | 0.2269 | 0.1182 | 0.1838 |
| Fixed | Brier | 39 | 0.009284 | 0.004699 | 0.007635 | 0.005454 | 0.01239 | 0.007854 | 0.01076 |
| Fixed | average_precision | 39 | 0.1531 | 0.1213 | 0.1417 | 0.04085 | 0.2387 | 0.1162 | 0.191 |
| Fixed | predicted_positive_volume | 39 | 5.279e+04 | 2.36e+04 | 5.117e+04 | 3.662e+04 | 6.931e+04 | 4.571e+04 | 6.026e+04 |
| Fixed | target_to_predicted_volume_ratio | 39 | 1.494 | 1.55 | 0.933 | 0.6321 | 2.082 | 1.066 | 2.015 |
| Naive | Dice_0.5 | 39 | 0.1895 | 0.1318 | 0.1811 | 0.08101 | 0.2697 | 0.149 | 0.2306 |
| Naive | IoU_0.5 | 39 | 0.1105 | 0.08301 | 0.09956 | 0.04222 | 0.1559 | 0.08506 | 0.1365 |
| Naive | precision_0.5 | 39 | 0.2422 | 0.1968 | 0.2022 | 0.064 | 0.3866 | 0.1816 | 0.3029 |
| Naive | recall_0.5 | 39 | 0.2147 | 0.152 | 0.1606 | 0.1199 | 0.3086 | 0.1687 | 0.264 |
| Naive | soft_Dice | 39 | 0.179 | 0.1247 | 0.1616 | 0.07547 | 0.25 | 0.1405 | 0.2176 |
| Naive | Brier | 39 | 0.009386 | 0.005005 | 0.007521 | 0.005225 | 0.01299 | 0.00786 | 0.01096 |
| Naive | average_precision | 39 | 0.1528 | 0.1212 | 0.1396 | 0.04003 | 0.2387 | 0.116 | 0.1908 |
| Naive | predicted_positive_volume | 39 | 5.279e+04 | 2.36e+04 | 5.117e+04 | 3.662e+04 | 6.931e+04 | 4.571e+04 | 6.026e+04 |
| Naive | target_to_predicted_volume_ratio | 39 | 1.494 | 1.55 | 0.933 | 0.6321 | 2.082 | 1.066 | 2.015 |
| EIA-linear | Dice_0.5 | 39 | 0.2461 | 0.153 | 0.2291 | 0.1285 | 0.3463 | 0.1983 | 0.2932 |
| EIA-linear | IoU_0.5 | 39 | 0.1489 | 0.1014 | 0.1293 | 0.06864 | 0.2094 | 0.1175 | 0.1804 |
| EIA-linear | precision_0.5 | 39 | 0.3248 | 0.2462 | 0.2727 | 0.1358 | 0.5009 | 0.2492 | 0.4024 |
| EIA-linear | recall_0.5 | 39 | 0.2612 | 0.1682 | 0.2373 | 0.1646 | 0.3857 | 0.2102 | 0.315 |
| EIA-linear | soft_Dice | 39 | 0.2761 | 0.1357 | 0.2434 | 0.1891 | 0.4028 | 0.2337 | 0.317 |
| EIA-linear | Brier | 39 | 0.006255 | 0.002851 | 0.005547 | 0.003857 | 0.008322 | 0.005375 | 0.007154 |
| EIA-linear | average_precision | 39 | 0.3541 | 0.2166 | 0.2854 | 0.1898 | 0.5348 | 0.2868 | 0.4218 |
| EIA-linear | predicted_positive_volume | 39 | 4.744e+04 | 2.609e+04 | 4.014e+04 | 2.888e+04 | 6.252e+04 | 3.965e+04 | 5.563e+04 |
| EIA-linear | target_to_predicted_volume_ratio | 39 | 1.716 | 1.755 | 1.007 | 0.7257 | 2.216 | 1.224 | 2.295 |
| EIA-blend-0.90 | Dice_0.5 | 39 | 0.2059 | 0.1393 | 0.2099 | 0.09195 | 0.2979 | 0.1628 | 0.2494 |
| EIA-blend-0.90 | IoU_0.5 | 39 | 0.1215 | 0.08907 | 0.1172 | 0.0482 | 0.175 | 0.09425 | 0.1493 |
| EIA-blend-0.90 | precision_0.5 | 39 | 0.2761 | 0.219 | 0.2347 | 0.07691 | 0.4485 | 0.2087 | 0.3442 |
| EIA-blend-0.90 | recall_0.5 | 39 | 0.2211 | 0.1542 | 0.1721 | 0.1267 | 0.3218 | 0.1744 | 0.2709 |
| EIA-blend-0.90 | soft_Dice | 39 | 0.1945 | 0.1145 | 0.1991 | 0.1066 | 0.2801 | 0.1593 | 0.2292 |
| EIA-blend-0.90 | Brier | 39 | 0.007768 | 0.003957 | 0.006328 | 0.00455 | 0.01038 | 0.006563 | 0.009014 |
| EIA-blend-0.90 | average_precision | 39 | 0.2722 | 0.1595 | 0.2916 | 0.1095 | 0.4156 | 0.2226 | 0.3215 |
| EIA-blend-0.90 | predicted_positive_volume | 39 | 4.735e+04 | 2.248e+04 | 4.414e+04 | 3.199e+04 | 6.195e+04 | 4.065e+04 | 5.448e+04 |
| EIA-blend-0.90 | target_to_predicted_volume_ratio | 39 | 1.667 | 1.697 | 1.056 | 0.7412 | 2.428 | 1.197 | 2.236 |
| EIA-blend-0.75 | Dice_0.5 | 39 | 0.2482 | 0.1566 | 0.2459 | 0.1243 | 0.3646 | 0.1995 | 0.2969 |
| EIA-blend-0.75 | IoU_0.5 | 39 | 0.1507 | 0.1039 | 0.1402 | 0.06627 | 0.2229 | 0.1187 | 0.1829 |
| EIA-blend-0.75 | precision_0.5 | 39 | 0.3631 | 0.2632 | 0.3176 | 0.138 | 0.6226 | 0.282 | 0.4447 |
| EIA-blend-0.75 | recall_0.5 | 39 | 0.2394 | 0.1592 | 0.2103 | 0.1392 | 0.3574 | 0.191 | 0.2905 |
| EIA-blend-0.75 | soft_Dice | 39 | 0.2614 | 0.1309 | 0.238 | 0.1709 | 0.3832 | 0.2204 | 0.3007 |
| EIA-blend-0.75 | Brier | 39 | 0.005783 | 0.002987 | 0.004744 | 0.003362 | 0.00774 | 0.004878 | 0.006726 |
| EIA-blend-0.75 | average_precision | 39 | 0.4066 | 0.2094 | 0.4108 | 0.238 | 0.5872 | 0.3412 | 0.4701 |
| EIA-blend-0.75 | predicted_positive_volume | 39 | 3.82e+04 | 2.093e+04 | 3.481e+04 | 2.26e+04 | 4.934e+04 | 3.194e+04 | 4.483e+04 |
| EIA-blend-0.75 | target_to_predicted_volume_ratio | 39 | 2.095 | 2.031 | 1.305 | 0.9592 | 2.498 | 1.52 | 2.758 |
| Full PCC | Dice_0.5 | 39 | 0.3654 | 0.1877 | 0.3913 | 0.2291 | 0.5175 | 0.3064 | 0.4214 |
| Full PCC | IoU_0.5 | 39 | 0.2389 | 0.1379 | 0.2433 | 0.1295 | 0.3491 | 0.1959 | 0.2805 |
| Full PCC | precision_0.5 | 39 | 0.5292 | 0.2845 | 0.5293 | 0.3425 | 0.7772 | 0.4403 | 0.6149 |
| Full PCC | recall_0.5 | 39 | 0.3248 | 0.1759 | 0.3144 | 0.2341 | 0.4436 | 0.2713 | 0.3802 |
| Full PCC | soft_Dice | 39 | 0.2382 | 0.1445 | 0.2284 | 0.134 | 0.3585 | 0.1935 | 0.2817 |
| Full PCC | Brier | 39 | 0.006457 | 0.004132 | 0.005062 | 0.003083 | 0.008279 | 0.00523 | 0.007775 |
| Full PCC | average_precision | 39 | 0.3093 | 0.1903 | 0.3213 | 0.1503 | 0.4898 | 0.2502 | 0.3676 |
| Full PCC | predicted_positive_volume | 39 | 3.556e+04 | 2.366e+04 | 2.786e+04 | 1.898e+04 | 4.964e+04 | 2.839e+04 | 4.294e+04 |
| Full PCC | target_to_predicted_volume_ratio | 39 | 2.345 | 2.445 | 1.58 | 1.142 | 2.597 | 1.687 | 3.175 |
| No-smoothing PCC | Dice_0.5 | 39 | 0.4512 | 0.2103 | 0.4658 | 0.3502 | 0.6201 | 0.3853 | 0.5142 |
| No-smoothing PCC | IoU_0.5 | 39 | 0.3136 | 0.1698 | 0.3036 | 0.2125 | 0.4494 | 0.2614 | 0.3653 |
| No-smoothing PCC | precision_0.5 | 39 | 0.6633 | 0.2889 | 0.7185 | 0.5209 | 0.8969 | 0.5707 | 0.748 |
| No-smoothing PCC | recall_0.5 | 39 | 0.3898 | 0.2012 | 0.4051 | 0.2868 | 0.5306 | 0.3286 | 0.4524 |
| No-smoothing PCC | soft_Dice | 39 | 0.2696 | 0.1557 | 0.2777 | 0.1653 | 0.4003 | 0.2215 | 0.3165 |
| No-smoothing PCC | Brier | 39 | 0.005765 | 0.003959 | 0.004686 | 0.002675 | 0.007503 | 0.004597 | 0.007045 |
| No-smoothing PCC | average_precision | 39 | 0.4044 | 0.2091 | 0.4197 | 0.2725 | 0.5755 | 0.3396 | 0.4687 |
| No-smoothing PCC | predicted_positive_volume | 39 | 3.36e+04 | 2.391e+04 | 2.775e+04 | 1.596e+04 | 4.568e+04 | 2.63e+04 | 4.108e+04 |
| No-smoothing PCC | target_to_predicted_volume_ratio | 39 | 2.559 | 2.713 | 1.679 | 1.281 | 2.71 | 1.835 | 3.492 |

### Supplementary Table S4. No-smoothing robustness summary

| Condition | Method | Metric | n | Mean | SD | Median | CI low | CI high |
|---|---|---|---|---|---|---|---|---|
| CLEAN | FULL_PCC | dice_topk | 40 | 0.3884 | 0.1735 | 0.3775 | 0.3366 | 0.4419 |
| CLEAN | FULL_PCC | iou_topk | 40 | 0.2566 | 0.1501 | 0.2326 | 0.2133 | 0.3047 |
| CLEAN | FULL_PCC | dice_fixed05 | 40 | 0.2758 | 0.164 | 0.2688 | 0.2279 | 0.3278 |
| CLEAN | FULL_PCC | iou_fixed05 | 40 | 0.1714 | 0.1244 | 0.1553 | 0.1357 | 0.211 |
| CLEAN | FULL_PCC | target_mass | 40 | 1.368e+04 | 1.464e+04 | 8322 | 9554 | 1.835e+04 |
| CLEAN | FULL_PCC | false_guidance_mass | 40 | 0 | 0 | 0 | 0 | 0 |
| CLEAN | FULL_PCC | outside_clean_target_mass | 40 | 3.904e+04 | 2.388e+04 | 3.363e+04 | 3.197e+04 | 4.659e+04 |
| CLEAN | FULL_PCC | predicted_positive_voxels | 40 | 4.977e+04 | 3.051e+04 | 4.272e+04 | 4.064e+04 | 5.935e+04 |
| CLEAN | NO_SMOOTHING_PCC | dice_topk | 40 | 0.5001 | 0.1764 | 0.5134 | 0.4463 | 0.5555 |
| CLEAN | NO_SMOOTHING_PCC | iou_topk | 40 | 0.3529 | 0.1718 | 0.3453 | 0.3018 | 0.4077 |
| CLEAN | NO_SMOOTHING_PCC | dice_fixed05 | 40 | 0.3263 | 0.1798 | 0.311 | 0.2731 | 0.3829 |
| CLEAN | NO_SMOOTHING_PCC | iou_fixed05 | 40 | 0.2097 | 0.1428 | 0.1841 | 0.1683 | 0.2559 |
| CLEAN | NO_SMOOTHING_PCC | target_mass | 40 | 1.488e+04 | 1.524e+04 | 9762 | 1.058e+04 | 1.968e+04 |
| CLEAN | NO_SMOOTHING_PCC | false_guidance_mass | 40 | 0 | 0 | 0 | 0 | 0 |
| CLEAN | NO_SMOOTHING_PCC | outside_clean_target_mass | 40 | 3.481e+04 | 2.202e+04 | 3.027e+04 | 2.809e+04 | 4.18e+04 |
| CLEAN | NO_SMOOTHING_PCC | predicted_positive_voxels | 40 | 4.548e+04 | 2.808e+04 | 3.832e+04 | 3.699e+04 | 5.415e+04 |
| FP_25 | FULL_PCC | dice_topk | 40 | 0.3842 | 0.1739 | 0.3754 | 0.3323 | 0.4386 |
| FP_25 | FULL_PCC | iou_topk | 40 | 0.2533 | 0.1496 | 0.2311 | 0.2106 | 0.3011 |
| FP_25 | FULL_PCC | dice_fixed05 | 40 | 0.2728 | 0.1632 | 0.265 | 0.2251 | 0.3241 |
| FP_25 | FULL_PCC | iou_fixed05 | 40 | 0.1692 | 0.1233 | 0.1528 | 0.134 | 0.208 |
| FP_25 | FULL_PCC | target_mass | 40 | 1.368e+04 | 1.464e+04 | 8322 | 9487 | 1.842e+04 |
| FP_25 | FULL_PCC | false_guidance_mass | 40 | 240.2 | 206.5 | 201.6 | 178.3 | 305.7 |
| FP_25 | FULL_PCC | outside_clean_target_mass | 40 | 3.972e+04 | 2.423e+04 | 3.392e+04 | 3.265e+04 | 4.724e+04 |
| FP_25 | FULL_PCC | predicted_positive_voxels | 40 | 5.07e+04 | 3.094e+04 | 4.331e+04 | 4.167e+04 | 6.023e+04 |
| FP_25 | NO_SMOOTHING_PCC | dice_topk | 40 | 0.4978 | 0.1759 | 0.511 | 0.4452 | 0.5527 |
| FP_25 | NO_SMOOTHING_PCC | iou_topk | 40 | 0.3506 | 0.1711 | 0.3432 | 0.3008 | 0.406 |
| FP_25 | NO_SMOOTHING_PCC | dice_fixed05 | 40 | 0.3252 | 0.1792 | 0.3104 | 0.272 | 0.3818 |
| FP_25 | NO_SMOOTHING_PCC | iou_fixed05 | 40 | 0.2089 | 0.1421 | 0.1838 | 0.1678 | 0.2541 |
| FP_25 | NO_SMOOTHING_PCC | target_mass | 40 | 1.488e+04 | 1.524e+04 | 9762 | 1.052e+04 | 1.972e+04 |
| FP_25 | NO_SMOOTHING_PCC | false_guidance_mass | 40 | 489.2 | 391.7 | 382.4 | 375.7 | 612.2 |
| FP_25 | NO_SMOOTHING_PCC | outside_clean_target_mass | 40 | 3.509e+04 | 2.207e+04 | 3.048e+04 | 2.851e+04 | 4.2e+04 |
| FP_25 | NO_SMOOTHING_PCC | predicted_positive_voxels | 40 | 4.573e+04 | 2.818e+04 | 3.873e+04 | 3.718e+04 | 5.465e+04 |
| MIXED | FULL_PCC | dice_topk | 40 | 0.3328 | 0.1674 | 0.3337 | 0.2829 | 0.3849 |
| MIXED | FULL_PCC | iou_topk | 40 | 0.2128 | 0.1361 | 0.2003 | 0.1744 | 0.2562 |
| MIXED | FULL_PCC | dice_fixed05 | 40 | 0.2541 | 0.1592 | 0.2333 | 0.2074 | 0.3053 |
| MIXED | FULL_PCC | iou_fixed05 | 40 | 0.1561 | 0.1201 | 0.1321 | 0.1217 | 0.1965 |
| MIXED | FULL_PCC | target_mass | 40 | 1.236e+04 | 1.37e+04 | 7228 | 8570 | 1.673e+04 |
| MIXED | FULL_PCC | false_guidance_mass | 40 | 815 | 756.9 | 479 | 601.9 | 1058 |
| MIXED | FULL_PCC | outside_clean_target_mass | 40 | 3.928e+04 | 2.414e+04 | 3.384e+04 | 3.2e+04 | 4.695e+04 |
| MIXED | FULL_PCC | predicted_positive_voxels | 40 | 4.928e+04 | 3.073e+04 | 4.181e+04 | 4.032e+04 | 5.884e+04 |
| MIXED | NO_SMOOTHING_PCC | dice_topk | 40 | 0.3347 | 0.1703 | 0.3299 | 0.2846 | 0.3882 |
| MIXED | NO_SMOOTHING_PCC | iou_topk | 40 | 0.2146 | 0.1365 | 0.1977 | 0.1747 | 0.2583 |
| MIXED | NO_SMOOTHING_PCC | dice_fixed05 | 40 | 0.2616 | 0.1646 | 0.2303 | 0.2133 | 0.3152 |
| MIXED | NO_SMOOTHING_PCC | iou_fixed05 | 40 | 0.1621 | 0.1265 | 0.1303 | 0.1256 | 0.2029 |
| MIXED | NO_SMOOTHING_PCC | target_mass | 40 | 1.174e+04 | 1.314e+04 | 6844 | 8095 | 1.604e+04 |
| MIXED | NO_SMOOTHING_PCC | false_guidance_mass | 40 | 1269 | 1075 | 807.5 | 957.7 | 1615 |
| MIXED | NO_SMOOTHING_PCC | outside_clean_target_mass | 40 | 3.543e+04 | 2.214e+04 | 3.056e+04 | 2.897e+04 | 4.233e+04 |
| MIXED | NO_SMOOTHING_PCC | predicted_positive_voxels | 40 | 4.321e+04 | 2.824e+04 | 3.645e+04 | 3.487e+04 | 5.218e+04 |
| PARTIAL_25 | FULL_PCC | dice_topk | 40 | 0.3237 | 0.1641 | 0.315 | 0.2765 | 0.376 |
| PARTIAL_25 | FULL_PCC | iou_topk | 40 | 0.2057 | 0.1331 | 0.1869 | 0.1674 | 0.2491 |
| PARTIAL_25 | FULL_PCC | dice_fixed05 | 40 | 0.2505 | 0.1592 | 0.2199 | 0.2051 | 0.3008 |
| PARTIAL_25 | FULL_PCC | iou_fixed05 | 40 | 0.1538 | 0.121 | 0.1235 | 0.1195 | 0.1931 |
| PARTIAL_25 | FULL_PCC | target_mass | 40 | 1.18e+04 | 1.327e+04 | 6934 | 8091 | 1.603e+04 |
| PARTIAL_25 | FULL_PCC | false_guidance_mass | 40 | 0 | 0 | 0 | 0 | 0 |
| PARTIAL_25 | FULL_PCC | outside_clean_target_mass | 40 | 3.822e+04 | 2.371e+04 | 3.321e+04 | 3.115e+04 | 4.571e+04 |
| PARTIAL_25 | FULL_PCC | predicted_positive_voxels | 40 | 4.754e+04 | 3.012e+04 | 4.042e+04 | 3.867e+04 | 5.717e+04 |
| PARTIAL_25 | NO_SMOOTHING_PCC | dice_topk | 40 | 0.3322 | 0.1591 | 0.3267 | 0.2851 | 0.3822 |
| PARTIAL_25 | NO_SMOOTHING_PCC | iou_topk | 40 | 0.211 | 0.1277 | 0.1953 | 0.1734 | 0.2526 |
| PARTIAL_25 | NO_SMOOTHING_PCC | dice_fixed05 | 40 | 0.251 | 0.1627 | 0.2192 | 0.2036 | 0.3032 |
| PARTIAL_25 | NO_SMOOTHING_PCC | iou_fixed05 | 40 | 0.1548 | 0.1252 | 0.1231 | 0.1188 | 0.1965 |
| PARTIAL_25 | NO_SMOOTHING_PCC | target_mass | 40 | 1.099e+04 | 1.252e+04 | 6490 | 7522 | 1.508e+04 |
| PARTIAL_25 | NO_SMOOTHING_PCC | false_guidance_mass | 40 | 0 | 0 | 0 | 0 | 0 |
| PARTIAL_25 | NO_SMOOTHING_PCC | outside_clean_target_mass | 40 | 3.481e+04 | 2.202e+04 | 3.027e+04 | 2.834e+04 | 4.175e+04 |
| PARTIAL_25 | NO_SMOOTHING_PCC | predicted_positive_voxels | 40 | 4.194e+04 | 2.799e+04 | 3.52e+04 | 3.375e+04 | 5.079e+04 |
| PARTIAL_50 | FULL_PCC | dice_topk | 40 | 0.3492 | 0.1705 | 0.343 | 0.2976 | 0.402 |
| PARTIAL_50 | FULL_PCC | iou_topk | 40 | 0.2256 | 0.1417 | 0.207 | 0.1838 | 0.271 |
| PARTIAL_50 | FULL_PCC | dice_fixed05 | 40 | 0.2604 | 0.1612 | 0.2419 | 0.2128 | 0.3112 |
| PARTIAL_50 | FULL_PCC | iou_fixed05 | 40 | 0.1606 | 0.1226 | 0.1376 | 0.1258 | 0.2015 |
| PARTIAL_50 | FULL_PCC | target_mass | 40 | 1.255e+04 | 1.383e+04 | 7327 | 8604 | 1.704e+04 |
| PARTIAL_50 | FULL_PCC | false_guidance_mass | 40 | 0 | 0 | 0 | 0 | 0 |
| PARTIAL_50 | FULL_PCC | outside_clean_target_mass | 40 | 3.845e+04 | 2.377e+04 | 3.333e+04 | 3.142e+04 | 4.594e+04 |
| PARTIAL_50 | FULL_PCC | predicted_positive_voxels | 40 | 4.836e+04 | 3.024e+04 | 4.118e+04 | 3.944e+04 | 5.761e+04 |
| PARTIAL_50 | NO_SMOOTHING_PCC | dice_topk | 40 | 0.3886 | 0.1595 | 0.3741 | 0.3425 | 0.4395 |
| PARTIAL_50 | NO_SMOOTHING_PCC | iou_topk | 40 | 0.2541 | 0.1352 | 0.2301 | 0.2152 | 0.2982 |
| PARTIAL_50 | NO_SMOOTHING_PCC | dice_fixed05 | 40 | 0.2758 | 0.1662 | 0.2561 | 0.2279 | 0.3298 |
| PARTIAL_50 | NO_SMOOTHING_PCC | iou_fixed05 | 40 | 0.172 | 0.1289 | 0.1469 | 0.135 | 0.2142 |
| PARTIAL_50 | NO_SMOOTHING_PCC | target_mass | 40 | 1.224e+04 | 1.333e+04 | 7200 | 8536 | 1.668e+04 |
| PARTIAL_50 | NO_SMOOTHING_PCC | false_guidance_mass | 40 | 0 | 0 | 0 | 0 | 0 |
| PARTIAL_50 | NO_SMOOTHING_PCC | outside_clean_target_mass | 40 | 3.481e+04 | 2.202e+04 | 3.027e+04 | 2.836e+04 | 4.17e+04 |
| PARTIAL_50 | NO_SMOOTHING_PCC | predicted_positive_voxels | 40 | 4.306e+04 | 2.792e+04 | 3.636e+04 | 3.479e+04 | 5.185e+04 |
| SHIFT_3 | FULL_PCC | dice_topk | 40 | 0.3684 | 0.1713 | 0.363 | 0.3167 | 0.4213 |
| SHIFT_3 | FULL_PCC | iou_topk | 40 | 0.2405 | 0.1442 | 0.2218 | 0.1989 | 0.2879 |
| SHIFT_3 | FULL_PCC | dice_fixed05 | 40 | 0.2699 | 0.1623 | 0.2635 | 0.2227 | 0.3203 |
| SHIFT_3 | FULL_PCC | iou_fixed05 | 40 | 0.1672 | 0.1228 | 0.1518 | 0.1321 | 0.2067 |
| SHIFT_3 | FULL_PCC | target_mass | 40 | 1.334e+04 | 1.442e+04 | 7956 | 9265 | 1.795e+04 |
| SHIFT_3 | FULL_PCC | false_guidance_mass | 40 | 1693 | 1761 | 962.3 | 1197 | 2268 |
| SHIFT_3 | FULL_PCC | outside_clean_target_mass | 40 | 3.917e+04 | 2.39e+04 | 3.363e+04 | 3.208e+04 | 4.676e+04 |
| SHIFT_3 | FULL_PCC | predicted_positive_voxels | 40 | 4.962e+04 | 3.057e+04 | 4.254e+04 | 4.039e+04 | 5.907e+04 |
| SHIFT_3 | NO_SMOOTHING_PCC | dice_topk | 40 | 0.38 | 0.1725 | 0.3639 | 0.3283 | 0.4346 |
| SHIFT_3 | NO_SMOOTHING_PCC | iou_topk | 40 | 0.2498 | 0.145 | 0.2225 | 0.207 | 0.2954 |
| SHIFT_3 | NO_SMOOTHING_PCC | dice_fixed05 | 40 | 0.2854 | 0.1691 | 0.2809 | 0.2353 | 0.3387 |
| SHIFT_3 | NO_SMOOTHING_PCC | iou_fixed05 | 40 | 0.1789 | 0.1303 | 0.1634 | 0.1411 | 0.2201 |
| SHIFT_3 | NO_SMOOTHING_PCC | target_mass | 40 | 1.311e+04 | 1.418e+04 | 7843 | 9081 | 1.776e+04 |
| SHIFT_3 | NO_SMOOTHING_PCC | false_guidance_mass | 40 | 2123 | 2087 | 1258 | 1525 | 2808 |
| SHIFT_3 | NO_SMOOTHING_PCC | outside_clean_target_mass | 40 | 3.575e+04 | 2.215e+04 | 3.062e+04 | 2.926e+04 | 4.279e+04 |
| SHIFT_3 | NO_SMOOTHING_PCC | predicted_positive_voxels | 40 | 4.479e+04 | 2.848e+04 | 3.759e+04 | 3.631e+04 | 5.399e+04 |

### Supplementary Table S7a. Internal oracle-assisted summary

| Method | Metric | n | Mean | SD | Median | Oracle assisted |
|---|---|---|---|---|---|---|
| Fixed | topk_Dice | 113 | 0.2683 | 0.1577 | 0.2641 | True |
| Fixed | topk_IoU | 113 | 0.1648 | 0.1103 | 0.1522 | True |
| Naive | topk_Dice | 113 | 0.2686 | 0.1574 | 0.2641 | True |
| Naive | topk_IoU | 113 | 0.165 | 0.1101 | 0.1522 | True |
| EIA-linear | topk_Dice | 113 | 0.3701 | 0.2284 | 0.3387 | True |
| EIA-linear | topk_IoU | 113 | 0.2536 | 0.1929 | 0.2039 | True |
| EIA-blend-0.90 | topk_Dice | 113 | 0.3388 | 0.1771 | 0.3198 | True |
| EIA-blend-0.90 | topk_IoU | 113 | 0.2181 | 0.1344 | 0.1903 | True |
| EIA-blend-0.75 | topk_Dice | 113 | 0.4438 | 0.2051 | 0.4128 | True |
| EIA-blend-0.75 | topk_IoU | 113 | 0.3084 | 0.1797 | 0.2601 | True |
| EIA-morph | topk_Dice | 113 | 0.1907 | 0.1233 | 0.1777 | True |
| EIA-morph | topk_IoU | 113 | 0.1109 | 0.08102 | 0.09752 | True |
| Full PCC | topk_Dice | 113 | 0.4398 | 0.1937 | 0.4573 | True |
| Full PCC | topk_IoU | 113 | 0.3013 | 0.1591 | 0.2965 | True |
| No-smoothing PCC | topk_Dice | 113 | 0.6308 | 0.1958 | 0.6539 | True |
| No-smoothing PCC | topk_IoU | 113 | 0.4893 | 0.2046 | 0.4858 | True |

### Supplementary Table S7b. RHUH oracle-assisted summary

| Method | Metric | n | Mean | SD | Median | CI low | CI high |
|---|---|---|---|---|---|---|---|
| Fixed | topk_Dice | 39 | 0.2066 | 0.1351 | 0.2084 | 0.1651 | 0.2484 |
| Fixed | topk_IoU | 39 | 0.1215 | 0.08608 | 0.1163 | 0.09516 | 0.1484 |
| Naive | topk_Dice | 39 | 0.2066 | 0.1351 | 0.2084 | 0.1651 | 0.2484 |
| Naive | topk_IoU | 39 | 0.1215 | 0.08608 | 0.1163 | 0.09516 | 0.1484 |
| EIA-linear | topk_Dice | 39 | 0.3435 | 0.2245 | 0.2918 | 0.2741 | 0.4134 |
| EIA-linear | topk_IoU | 39 | 0.2306 | 0.1778 | 0.1708 | 0.1764 | 0.2873 |
| EIA-blend-0.90 | topk_Dice | 39 | 0.2408 | 0.1446 | 0.2619 | 0.1963 | 0.2851 |
| EIA-blend-0.90 | topk_IoU | 39 | 0.1444 | 0.09449 | 0.1507 | 0.1154 | 0.1737 |
| EIA-blend-0.75 | topk_Dice | 39 | 0.346 | 0.213 | 0.353 | 0.2799 | 0.4121 |
| EIA-blend-0.75 | topk_IoU | 39 | 0.2294 | 0.1627 | 0.2143 | 0.1794 | 0.2806 |
| Full PCC | topk_Dice | 39 | 0.3612 | 0.1787 | 0.3843 | 0.3056 | 0.414 |
| Full PCC | topk_IoU | 39 | 0.2342 | 0.1309 | 0.2379 | 0.194 | 0.2734 |
| No-smoothing PCC | topk_Dice | 39 | 0.4263 | 0.1967 | 0.4292 | 0.3651 | 0.4844 |
| No-smoothing PCC | topk_IoU | 39 | 0.2896 | 0.1553 | 0.2733 | 0.2421 | 0.3364 |
