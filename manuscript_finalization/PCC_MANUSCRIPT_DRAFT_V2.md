# Target-conditioned refinement of future-blind longitudinal glioma change maps replicates across independent cohorts

[AUTHOR_LIST_REQUIRED]

[AFFILIATIONS_REQUIRED]

*Correspondence: [CORRESPONDING_AUTHOR_EMAIL_REQUIRED]*

## Abstract

Longitudinal glioma change is difficult to localize on post-treatment MRI, and retrospective correction can be misinterpreted as prospective prediction. We separated these tasks. A five-fold model generated a future-blind initial probability map (P0) from current contrast-enhanced T1 MRI and current masks. After the realized change target became available, probability correction and calibration (PCC) applied a fixed ten-round target-conditioned update. In a prelocked 113-patient internal cohort, mean Dice at threshold 0.5 increased from 0.239 for P0 to 0.444 for canonical PCC (mean paired difference 0.205, 95% bootstrap CI 0.191–0.218; Holm-adjusted P=5.61e-20). A no-smoothing variant, discovered during development and subsequently locked, reached 0.637. In an independent 39-patient RHUH cohort, physically isolated future-blind P0 achieved mean Dice 0.190; canonical PCC and no-smoothing reached 0.365 and 0.451, respectively, with both prelocked comparisons significant after Holm correction. These findings show reproducible retrospective target-conditioned refinement across datasets, not prospective recurrence forecasting or clinical validation.

**Keywords:** glioma; longitudinal MRI; segmentation; external testing; probability-map refinement; domain shift

## Introduction

Magnetic resonance imaging is central to longitudinal assessment after glioma treatment, but postoperative anatomy, treatment effects and evolving enhancing and non-enhancing abnormalities complicate spatial comparison. Contemporary response criteria emphasize standardized timepoint selection and caution in interpreting apparent progression, particularly when treatment-related change can mimic tumour progression [1,14]. Automated segmentation may make longitudinal measurements more reproducible, yet a map evaluated against a later image is not necessarily a map that could have been generated before that image existed.

Post-treatment longitudinal mapping poses a stricter problem than single-timepoint segmentation. Surgical cavities alter normal anatomy; enhancing signal can reflect residual tumour, recurrence, treatment effect or blood products; and non-enhancing abnormality can change in extent and meaning over time. A numerical overlap score consequently combines at least three sources of variation: the initial model, the definition of the reference mask and the spatial relationship between timepoints. The present work does not attempt to resolve the clinical diagnosis of progression. It instead studies a binary change-localization task on dataset-provided masks, with eligibility and geometry defined before outcome evaluation.

Probability maps preserve graded uncertainty that a binary mask discards. A fixed threshold supplies a prespecified decision rule, whereas soft overlap, Brier score and average precision describe complementary probability behaviour [10,11,15]. Target-volume-matched top-k scores can answer a retrospective localization question but use the target volume and are therefore oracle-assisted. Treating these quantities as interchangeable would make an apparently strong map difficult to interpret. We consequently retained all locked metrics but assigned each a specific role.

This distinction is especially important for machine-learning studies. External testing often exposes performance attenuation when acquisition, population or annotation distributions differ from development data [5,6]. It is also easy to blur a future-blind prediction with a retrospective analysis that uses the realized outcome. CLAIM 2024 therefore emphasizes transparent data partitions, reference standards, external testing and availability [7]. In this study, the two operations are separated both conceptually and operationally: a frozen predictor first generates a probability map from current-only information, whereas subsequent correction is evaluated only after the realized future-change target is available.

The separation changes the appropriate scientific question. A prospective predictor should be judged by the future-blind P0 map alone. Once the future target is supplied, the question becomes whether a fixed correction operator has stable, interpretable and reproducible behaviour—not whether it has forecast the future. Shuffled guidance, term removal, imperfect guidance and external replication can inform that narrower question. They cannot make target conditioning disappear or establish deployment utility.

We studied probability correction and calibration (PCC), an iterative error-guided probability-map refinement rule. PCC starts from a future-blind probability map, preserves probabilities outside a target-centred support region and updates logits within that region using discrepancy between the current map and the realized target. Its canonical form smooths discrepancy before each update. A no-smoothing variant, which retains voxelwise discrepancy, emerged as a post-hoc candidate in the development cohort; it was not retrospectively redefined as canonical PCC. The candidate was then specified before evaluation in independent internal and external cohorts.

The study had three evidence levels. A 40-patient development cohort supported mechanistic ablation, target-shuffling, imperfect-guidance and trajectory analyses. A separate internal cohort was locked at 113 patients after a pre-outcome identity audit excluded two non-independent records while retaining all frozen P0 evidence. Finally, the RHUH-GBM dataset supplied an independent cross-dataset test [3]. Its P0 maps were generated in a physically isolated current-only stage before recurrence mask arrays became accessible. One of 40 RHUH patients was excluded before P0 generation because current and recurrence images did not share a valid physical voxel grid, leaving 39 patients. We asked whether canonical PCC improved the prelocked patient-level Dice endpoint over future-blind P0, whether the no-smoothing candidate subsequently improved over canonical PCC, and whether both findings replicated externally without changing methods, thresholds, patients or statistics.

The design was confirmatory only for four paired statements: two comparisons in the independent internal cohort and the same two comparisons in RHUH. Other metrics and development analyses remain descriptive, robustness-oriented or exploratory. This hierarchy was fixed in the manuscript authority registry before writing, preventing older leakage-prone experiments, superseded metrics and historical LUMIERE results from entering the current evidence chain.

## Results

### Cohorts and future-access separation

The development cohort comprised 40 patients, each held out in exactly one of five patient-level folds. The initial independent internal holdout contained 115 patients; an identity audit performed before target construction or performance evaluation found two records with identical current images and discordant future labels. Both were excluded under a prelocked rule, yielding 113 confirmatory patients. All 115 frozen P0 maps and the original manifest were retained. RHUH-GBM contained 40 patients with preoperative, early-postoperative and recurrence examinations [3]. RHUH-0008 was excluded before external P0 generation because lossless orientation checks could not place current and recurrence scans on one physical voxel grid. The external denominator was therefore 39. No patient was excluded using P0, target size or performance.

For both confirmatory cohorts, Stage A read current T1 contrast-enhanced MRI and current masks only. In RHUH, the Stage A execution dataset contained no recurrence image or segmentation. All 39 P0 files were frozen by SHA-256 before Stage B first accessed a recurrence segmentation. Stage B then constructed the realized change target as future mask minus current-mask voxels. Figure 1 shows this boundary. Fixed denotes the unchanged P0 and is the future-blind performance estimate. All PCC and EIA outputs are retrospective target-conditioned results.

### Development analyses define behaviour and limits

At the deployment-style fixed threshold of 0.5 in the 40-patient development audit, mean Dice was 0.229 for Fixed, 0.276 for canonical PCC and 0.326 for no-smoothing. Mean soft Dice was 0.270 for canonical PCC and 0.309 for no-smoothing; average precision was 0.373 and 0.523, respectively. EIA-blend-0.75 achieved higher average precision (0.612) than canonical PCC, illustrating why oracle-style controls cannot be summarized as uniformly inferior.

Separate locked development ablations used the historical formal development metric and are reported as mechanism/robustness evidence rather than substituted into confirmatory fixed-threshold results. Removing the error-guided term reduced mean Dice from 0.388 to 0.288, while removing outside-support suppression reduced it to 0.361. Shuffling targets across patients reduced mean Dice to 0.284 and the correct target was better in 39 of 40 patients. These results show dependence on case-specific spatial guidance, not biological causality. Under imperfect guidance, canonical PCC mean Dice was 0.349 for 50% target retention, 0.324 for 25% retention, 0.384 with 25% false-positive guidance, 0.368 after a three-voxel shift and 0.333 under mixed perturbation, compared with 0.388 for clean guidance. The no-smoothing advantage was largest with clean guidance and attenuated under more severe perturbations, consistent with a precision–robustness trade-off (Fig. 5; Supplementary Tables S4–S6).

### Independent internal confirmation

All 113 internal patients completed all eight locked methods, producing 904 case-method rows without failure. Mean Dice@0.5 was 0.239 for Fixed, 0.444 for canonical PCC and 0.637 for no-smoothing (Fig. 2). Canonical PCC exceeded Fixed in 113/113 patients (mean paired difference 0.205; median 0.212; 95% paired bootstrap CI 0.191–0.218; two-sided Wilcoxon P=2.803e-20; Holm-adjusted P=5.606e-20; Cohen's dz=2.75; rank-biserial=1.00).

No-smoothing exceeded canonical PCC in 113/113 patients (mean paired difference 0.193; median 0.189; 95% CI 0.174–0.213; two-sided Wilcoxon P=2.803e-20; Holm-adjusted P=5.606e-20; dz=1.80; rank-biserial=1.00). This independent confirmation followed, rather than preceded, the development observation. Mean soft Dice/average precision were 0.185/0.227 for Fixed, 0.267/0.414 for canonical PCC and 0.320/0.647 for no-smoothing. Full secondary distributions and 10,000-resample confidence intervals appear in Supplementary Table S2.

### Fixed ten-round trajectory

Canonical PCC propagated state through ten pre-specified rounds, and P10 was the formal output for every patient. The 1,130-row internal trajectory contained 113 patients × 10 rounds. P10 was best or tied-best by fixed-threshold Dice in 112 patients. One patient (PatientID_0242) declined from P9 to P10, but P10 was retained; no patient-specific round selection was performed. Figure 3 reports the cohort mean trajectories rather than implying monotonic improvement for every patient.

### RHUH future-blind transfer and external retrospective confirmation

RHUH Stage A transferred the unchanged five-checkpoint predictor without training, fine-tuning, calibration or dataset-specific normalization. Frozen P0/Fixed achieved mean Dice@0.5 0.190, soft Dice 0.151, Brier score 0.0093 and average precision 0.153. These are the cross-dataset future-blind transfer estimates. The lower Fixed Dice than in the 113-patient internal cohort is consistent with domain shift, although the cohorts differ in timepoint structure and mask ontology and were not subjected to a formal between-cohort hypothesis test.

After P0 freeze, all 39 RHUH patients completed seven methods and ten canonical PCC rounds, producing 273 case-method and 390 trajectory rows without failure. Mean Dice@0.5 reached 0.365 for canonical PCC and 0.451 for no-smoothing (Fig. 4). Canonical PCC exceeded Fixed in 39/39 patients (mean paired difference 0.176; median 0.185; 95% CI 0.151–0.199; two-sided Wilcoxon P=3.638e-12; Holm-adjusted P=7.276e-12; dz=2.24; rank-biserial=1.00).

No-smoothing exceeded canonical PCC in 38 patients and was lower in one (mean paired difference 0.086; median 0.088; 95% CI 0.072–0.101; two-sided and Holm-adjusted P=7.276e-12; dz=1.81; rank-biserial=0.997). Mean soft Dice/average precision were 0.238/0.309 for canonical PCC and 0.270/0.404 for no-smoothing. No late P10 degradation occurred in RHUH. Oracle-assisted target-volume-matched top-k Dice was 0.207, 0.361 and 0.426, respectively; these values describe retrospective localization and are not deployment metrics.

## Discussion

The main finding is narrow but reproducible: after a future-blind initial probability map was frozen, a fixed retrospective target-conditioned update improved localization in a prelocked internal cohort and in a separately locked RHUH cohort. The corresponding Fixed/P0 results quantify what the predictor could do without future information; the PCC results quantify what an error-guided correction rule did after the realized change target became available. Keeping these estimates separate is essential. The study does not show that PCC can prospectively forecast recurrence, and the corrected maps cannot be interpreted as deployment-time predictions.

The internal and external cohorts address different sources of credibility. The 113-patient cohort tests whether development findings survive patient-level separation and prelocked inference within the same broad data source. RHUH tests transfer of the frozen P0 predictor across institution, acquisition and annotation context, followed by replication of the already specified correction rule. Agreement in the direction of paired effects across these levels is stronger evidence of algorithmic reproducibility than a single random split, but it does not establish clinical generalizability beyond the analysed datasets.

The answer-conditioning objection therefore sets the interpretation rather than invalidating it. PCC is not offered as a way to infer an unknown target from current MRI. Instead, it provides a controlled retrospective framework for interrogating how spatial discrepancy, outside-support suppression and iterative probability updates alter a frozen map. Target shuffling reduced performance, removal of the error-guided term largely removed the gain, and imperfect guidance attenuated performance. These controls show that the observed refinement depends on spatially appropriate guidance and specified update terms. They do not prove a biological mechanism or clinical utility.

Canonical Gaussian smoothing was not optimal under clean guidance. One plausible computational interpretation is that smoothing attenuates sparse discrepancies, dilutes boundary information and spreads correction beyond exact target voxels; retaining D_r may preserve voxelwise error magnitude. That interpretation remains a hypothesis, not a demonstrated biological mechanism. The chronology also matters. Full PCC was the canonical method. No-smoothing was discovered during development, then treated as a candidate and locked before the 113-patient and RHUH analyses. Its advantage was confirmed in both, but development perturbations indicate that the advantage contracts as guidance becomes incomplete or displaced. No-smoothing should therefore be described as a candidate simplification with a possible robustness trade-off, not as a universally superior replacement.

The negative and mixed controls are scientifically important. EIA blends could exceed PCC on average precision, even when PCC was the focus of the prelocked Dice comparison. A global-discrepancy ablation modestly exceeded canonical PCC in the historical development metric, and one internally confirmed patient declined between P9 and P10. Retaining these findings prevents an overly tidy narrative. They also show why P10, threshold 0.5 and the two-comparison Holm family had to remain fixed rather than being reselected from observed trajectories or secondary endpoints.

External attenuation of future-blind Fixed performance is unsurprising in medical imaging [5,6]. RHUH differs in institution, acquisition, postoperative timing and segmentation ontology. Yet the external study preserved the frozen predictor and normalization, physically withheld recurrence voxels from Stage A, and used a pre-outcome geometry exclusion. The external results consequently provide an independent technical test of predictor transfer and, separately, target-conditioned correction reproducibility. They are not clinical validation. RHUH's all-nonbackground mask—necrosis, peritumoral/non-enhancing abnormality and enhancing tumour—is the closest available pathological-region mapping to the internal all-nonbackground mask, not perfect ontology equivalence.

Several limitations are fundamental. First, PCC requires the true future-change target; its corrected output is retrospective and oracle-conditioned. Second, the development cohort was selected deterministically from an historical dataset and surviving early-screening records were incomplete. Third, the internal 113-patient amendment excluded two non-independent records after Stage A but before outcome access; the original 115 manifest and P0 were retained, and neither record entered analysis. Fourth, RHUH included only 39 analysable patients after one pre-outcome geometry exclusion and represents a single external institution. Fifth, source masks were automated/derived and expert-review processes differed between datasets. Sixth, oracle-assisted top-k and EIA controls use target information and are not deployable comparators. Seventh, spatial Layer analyses are exploratory evidence of reliance/localization, not causal tumour biology. Finally, no prospective workflow, reader study, clinical decision analysis or patient-outcome evaluation was performed.

The principal endpoint also has known constraints. Dice is sensitive to lesion size and does not alone characterize calibration, ranking or clinically meaningful boundary error [10,15]. We therefore report soft overlap, Brier score and average precision, but none resolves uncertainty in the dataset reference masks. Confidence intervals quantify patient-sampling variability under the locked analysis; they do not account for uncertainty from alternative ontologies, annotation pipelines or hospitals. Exact P values demonstrate incompatibility with the paired null under the specified test, not clinical importance.

These boundaries suggest the next step: prospective work should evaluate a genuinely future-blind model and predefine how any deployable guidance could be obtained without outcome access. Within the present evidence, PCC is best understood as a reproducible retrospective methodological analysis that separates initial prediction from target-conditioned refinement.

## Methods

### Study design and data sources

The project used secondary analyses of MU-Glioma-Post and RHUH-GBM. MU-Glioma-Post contains longitudinal, skull-stripped, coregistered and resampled postoperative MR images and four-class segmentations (non-enhancing tumour core, surrounding non-enhancing FLAIR hyperintensity, enhancing tissue and resection cavity) [2]. RHUH-GBM contains 40 patients with preoperative, early-postoperative (<72 h) and recurrence MRI and expert-corrected segmentations [3]. The internal task used the union of non-background MU labels. RHUH used segmentation >0 (necrosis, peritumoral/non-enhancing abnormality and enhancing tumour), prelocked as the closest available mapping.

The development cohort comprised the first 40 eligible patients in lexical patient order; within a patient, usable timepoints were sorted numerically and the first two usable timepoints were paired. Each patient was held out in exactly one of five folds. Of the remaining 115 internal patients, PatientID_0113 and PatientID_0132 were excluded before target construction and performance analysis because current T1c and masks were identical, future T1c was identical, and future masks differed. The amended confirmatory cohort contained 113 unique patients and cases. RHUH used early postoperative as current and recurrence as future. RHUH-0008 was excluded before P0 generation because lossless orientation operations could not establish one physical voxel grid; 39 patients remained. No target- or performance-based exclusion occurred.

### Future-blind predictor and P0 freeze

The initial predictor was a 2D slice-wise CrossCaseSmallUNet with two input channels, one output channel and 16 base channels, trained in five patient-isolated folds. Channel 0 was current T1c normalized from positive-voxel p1/p99 and clipped to [0,1]; channel 1 was the binary current mask. Each checkpoint produced logits converted by sigmoid. P0 was the float32 arithmetic mean of five probability maps with weights 0.2 each. Checkpoint and code SHA-256 values were locked. No RHUH training, fine-tuning, calibration, checkpoint selection, test-time adaptation or dataset-specific normalization was used.

The recovered canonical training configuration used deterministic patient-group splitting with seed 42, 20 epochs, batch size 8, Adam with learning rate 0.001, and an equal mixture of weighted binary cross-entropy with logits and soft-Dice loss; the positive-class weight was capped at 50. Training slices contained current tumour or future change. The checkpoint criterion was minimum mean training loss by epoch; the historical cells did not use a separate tuning partition. This limitation is retained rather than retrospectively introducing one.

Internal and external Stage A generated P0 without reading future mask arrays. RHUH used a private current-only execution dataset containing only 39 current T1c files, 39 current segmentations, a manifest and provenance; it contained no recurrence files. P0 arrays were checked for shape, float32 dtype, finite values and [0,1] range, then frozen by SHA-256. Stage B could not begin until every required P0 had passed.

### Target and methods

After P0 freeze, the boolean target was T=(future mask>0) AND NOT(current mask>0). No registration, resampling, interpolation, morphology or target-size filtering was applied. Fixed returned P0. Naive and EIA variants used their frozen implementations; EIA-linear and EIA-blend controls are oracle-style retrospective controls.

Canonical PCC initialized P_0=safe_clip_prob(P0). For rounds r=1,...,10, a radius-26-voxel support R was formed around T, discrepancy was D_r=(T-P_r)R, and the canonical signal was S_r=GaussianSmooth(D_r, sigma=2.0 voxels). Outside-support probability O_r=P_r(1-R) was preserved, and the locked logit-space update used eta=0.30, epsilon=10^-5, float32 and propagated state. P10 was always formal. No-smoothing differed only in S_r=D_r. It was a post-hoc development finding that was prelocked for both confirmatory cohorts.

### Development analyses

Development evidence included term ablations, a 2×2 identity factorial, patient-level target shuffling, imperfect-guidance perturbations, target-construction sensitivity and spatial reliance/localization audits. Stochastic repeats were aggregated within patient before inference. Layer 1 used the provenance-supported formal v1 protocol; Layer 3 claims were restricted to endpoints surviving their predeclared Holm families. These analyses were supporting/exploratory and did not alter confirmatory configurations.

### Outcomes and statistics

The primary endpoint was patient-level Dice at probability>=0.5. Secondary metrics were IoU, precision, recall, soft Dice, Brier score, average precision/area under the precision–recall curve, predicted-positive volume and target-to-predicted-volume ratio. Target-volume-matched top-k Dice/IoU were labelled ORACLE_ASSISTED_RETROSPECTIVE_LOCALIZATION and interpreted separately. Complementary segmentation metrics were retained because overlap and probability scores capture different behaviour [10,11,15].

Each confirmatory family contained exactly two comparisons: canonical Full PCC versus Fixed and no-smoothing PCC versus Full PCC. The patient was the statistical unit. Sample sizes were the complete locked eligible cohorts available before outcome evaluation; no prospective power calculation or outcome-driven enlargement was performed. We used paired two-sided Wilcoxon signed-rank tests (zero_method=wilcox), alpha=0.05 and Holm adjustment over exactly two hypotheses [12]. We report n, paired mean and median differences, wins/ties/losses, raw and adjusted P, Cohen's dz, rank-biserial effect size and percentile 95% confidence intervals from 10,000 paired patient-level bootstrap resamples [13]. Seeds were 20260803 internally and 20260810 externally, as locked before outcome evaluation. Secondary summaries used 10,000 patient-level bootstrap resamples without new pairwise P values. Failures remained in the fixed denominators (113 and 39); complete paired cases formed primary inference, with a neutral zero-benefit sensitivity policy if failures occurred. No failure occurred.

### Reproducibility, ethics and AI assistance

Protocol manifests, code/configuration hashes, P0 hashes, completion markers, outcome-access records and immutable releases were preserved. The internal and RHUH analyses were committed before outcome access and no post-outcome scientific configuration change was permitted. Generation of this manuscript read only frozen CSVs and reports and did not execute scientific methods.

This was a secondary analysis of existing de-identified datasets. The MU-Glioma-Post source study reports University of Missouri IRB approval (IRB #2096253 MU) and waiver of informed consent for retrospective collection and sharing of de-identified data [2]. RHUH was used under TCIA's applicable conditions and its original ethics are reported by the dataset authors [3]. [AUTHOR CONFIRMATION REQUIRED: add the present institution's secondary-use determination.]

OpenAI Codex assisted author-supervised software engineering, deterministic document assembly, drafting/editing and consistency checks. It was not an author, did not define or modify the protocol or results, and did not assume scientific responsibility. Human authors reviewed all evidence, code, numbers, citations and text and retain full responsibility. [AUTHOR APPROVAL REQUIRED.]

## Data availability

MU-Glioma-Post is available through The Cancer Imaging Archive (TCIA) collection MU-Glioma-Post under its stated licence and access conditions [2]. RHUH-GBM is available through TCIA under DOI 10.7937/4545-c905 and applicable restricted-use terms [3]. The authors do not own or relicense source MRI. De-identified derived numeric tables, cohort-flow records, protocol locks and figure source data will be deposited at [PROCESSED_DATA_REPOSITORY_DOI_REQUIRED] before submission. Large MRI, segmentation and P0 arrays are not redistributed in the manuscript repository; access follows source-dataset terms and the availability plan.

## Code availability

Custom code for preprocessing, the frozen predictor, PCC/EIA methods, deterministic summaries, statistical validation and figure generation will be archived from the submission commit at [CODE_REPOSITORY_URL_REQUIRED], with an immutable release tag and environment/configuration manifests. Reviewer access will be supplied if the repository cannot be public at first submission.

## References

1. Wen, P. Y. et al. RANO 2.0: Update to the Response Assessment in Neuro-Oncology criteria for high- and low-grade gliomas in adults. J. Clin. Oncol. **41**, 5187–5199 (2023). https://doi.org/10.1200/JCO.23.01059
2. Mahmoud, E. et al. MU-Glioma Post: A comprehensive dataset of automated MR multi-sequence segmentation and clinical features. Sci. Data **12**, 1847 (2025). https://doi.org/10.1038/s41597-025-06011-7
3. Cepeda, S. et al. The Río Hortega University Hospital Glioblastoma dataset: A comprehensive collection of preoperative, early postoperative and recurrence MRI scans (RHUH-GBM). Data Brief **50**, 109617 (2023). https://doi.org/10.1016/j.dib.2023.109617
4. Ronneberger, O., Fischer, P. & Brox, T. U-Net: Convolutional networks for biomedical image segmentation. Lect. Notes Comput. Sci. **9351**, 234–241 (2015). https://doi.org/10.1007/978-3-319-24574-4_28
5. Yu, A. C., Mohajer, B. & Eng, J. External validation of deep learning algorithms for radiologic diagnosis: A systematic review. Radiol. Artif. Intell. **4**, e210064 (2022). https://doi.org/10.1148/ryai.210064
6. Guan, H. & Liu, M. Domain adaptation for medical image analysis: A survey. IEEE Trans. Biomed. Eng. **69**, 1173–1185 (2022). https://doi.org/10.1109/TBME.2021.3117407
7. Tejani, A. S. et al. Checklist for Artificial Intelligence in Medical Imaging (CLAIM): 2024 update. Radiol. Artif. Intell. **6**, e240300 (2024). https://doi.org/10.1148/ryai.240300
8. Collins, G. S. et al. TRIPOD+AI statement: Updated guidance for reporting clinical prediction models that use regression or machine learning methods. BMJ **385**, e078378 (2024). https://doi.org/10.1136/bmj-2023-078378
9. Moons, K. G. M. et al. PROBAST+AI: An updated quality, risk of bias, and applicability assessment tool for prediction models using regression or artificial intelligence methods. BMJ **388**, e082505 (2025). https://doi.org/10.1136/bmj-2024-082505
10. Müller, D., Soto-Rey, I. & Kramer, F. Towards a guideline for evaluation metrics in medical image segmentation. BMC Res. Notes **15**, 210 (2022). https://doi.org/10.1186/s13104-022-06096-y
11. Brier, G. W. Verification of forecasts expressed in terms of probability. Mon. Weather Rev. **78**, 1–3 (1950). https://doi.org/10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2
12. Holm, S. A simple sequentially rejective multiple test procedure. Scand. J. Stat. **6**, 65–70 (1979). https://doi.org/10.2307/4615733
13. Efron, B. Bootstrap methods: Another look at the jackknife. Ann. Stat. **7**, 1–26 (1979). https://doi.org/10.1214/aos/1176344552
14. Johnson, D. R. et al. Congress of Neurological Surgeons systematic review and evidence-based guidelines update on the role of imaging in the management of progressive glioblastoma in adults. J. Neurooncol. **158**, 225–247 (2022). https://doi.org/10.1007/s11060-021-03896-9
15. Taha, A. A. & Hanbury, A. Metrics for evaluating 3D medical image segmentation: Analysis, selection, and tool. BMC Med. Imaging **15**, 29 (2015). https://doi.org/10.1186/s12880-015-0068-x

## Acknowledgements

[ACKNOWLEDGEMENTS_REQUIRED]

## Author contributions

[AUTHOR_CONTRIBUTIONS_REQUIRED]

## Funding

[FUNDING_INFORMATION_REQUIRED]

## Competing interests

[COMPETING_INTERESTS_DECLARATION_REQUIRED]

## Figure legends

**Figure 1. Study design and future-access boundary.** The initial map was generated from current-only inputs and frozen before future voxel outcomes became accessible. PCC and EIA analyses occurred only after target construction and are retrospective.

**Figure 2. Independent internal patient-level Dice at threshold 0.5.** Lines connect each of 113 patients across Fixed, canonical Full PCC and no-smoothing PCC. Thick horizontal segments show means.

**Figure 3. Canonical Full PCC mean round trajectories.** Means are shown for the 113-patient internal and 39-patient RHUH cohorts. P10 was pre-specified and retained for every patient; curves do not imply monotonicity in every case.

**Figure 4. RHUH external patient-level Dice at threshold 0.5.** Lines connect each of 39 patients. Fixed is the future-blind P0; corrected maps are retrospective target-conditioned outputs.

**Figure 5. Development ablation and guidance dependence.** Values use the locked development metric and support mechanism/robustness interpretation only; they are not substituted for confirmatory fixed-threshold endpoints.

## Tables

**Table 1. Evidence levels and cohort flow.**

| Evidence level | Source patients | Pre-outcome exclusions | Analysed patients | Role |
|---|---:|---:|---:|---|
| Development | 40 | 0 | 40 | Method development, ablation, robustness |
| Independent internal | 115 | 2 identity/label anomaly | 113 | Prelocked confirmation |
| RHUH external | 40 | 1 geometry incompatibility | 39 | Cross-dataset technical testing |

**Table 2. Prelocked confirmatory comparisons on patient-level Dice@0.5.**

| Cohort/comparison | n | Mean difference | Median difference | Wins/ties/losses | 95% bootstrap CI | Raw P | Holm P |
|---|---:|---:|---:|---:|---:|---:|---:|
| Internal: Full PCC vs Fixed | 113 | 0.205 | 0.212 | 113/0/0 | 0.191–0.218 | 2.803e-20 | 5.606e-20 |
| Internal: No-smoothing vs Full PCC | 113 | 0.193 | 0.189 | 113/0/0 | 0.174–0.213 | 2.803e-20 | 5.606e-20 |
| RHUH: Full PCC vs Fixed | 39 | 0.176 | 0.185 | 39/0/0 | 0.151–0.199 | 3.638e-12 | 7.276e-12 |
| RHUH: No-smoothing vs Full PCC | 39 | 0.086 | 0.088 | 38/0/1 | 0.072–0.101 | 7.276e-12 | 7.276e-12 |
