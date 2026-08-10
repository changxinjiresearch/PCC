# Target-conditioned refinement of future-blind longitudinal glioma segmentation-change maps across independent cohorts

[AUTHOR_LIST_REQUIRED]

[AFFILIATIONS_REQUIRED]

Corresponding author: [CORRESPONDING_AUTHOR_AND_EMAIL_REQUIRED]

## Abstract

Longitudinal glioma segmentation-change localization requires separating prediction from analyses that use the realized outcome. We generated an initial probability map (P0) from current contrast-enhanced T1 MRI and an available current-timepoint segmentation, without the evaluated case's future image, future segmentation or future-added target. After P0 was frozen, Prediction-Comparison-Correction (PCC) retrospectively compared it with a one-sided future-added composite segmentation target and applied ten fixed logit-space updates. In 113 prelocked independent internal patients, mean Dice at threshold 0.5 was 0.239 for P0 and 0.444 for canonical PCC (paired difference 0.205, 95% bootstrap CI 0.191–0.218; Holm-adjusted P=5.61e-20). A no-smoothing candidate identified during development and prelocked before confirmation reached 0.637. In 39 RHUH patients, a physically isolated five-checkpoint P0 ensemble yielded mean Dice 0.190; canonical PCC and prelocked no-smoothing reached 0.365 and 0.451. Matched-information controls showed that results depended substantially on target access and update rule. PCC therefore provides reproducible retrospective target-conditioned refinement, not prospective recurrence forecasting or clinical validation.

Keywords: glioma; longitudinal MRI; segmentation change; external technical validation; target conditioning; reproducibility

## Introduction

Post-treatment glioma MRI is interpreted across changing anatomical and treatment contexts. Surgery, chemoradiation, resection cavities and treatment-related effects complicate comparison between timepoints, while response frameworks depend on explicit imaging baselines and longitudinal criteria [1,14]. Automated segmentation can support reproducible spatial summaries, but a binary foreground derived from a dataset annotation is not equivalent to viable tumour, histological progression or the complete biological course of disease [2,3]. These distinctions are especially important when an analysis uses a follow-up segmentation.

Two methodological tasks are often conflated. A future-blind prediction task estimates a future event from information available at the current timepoint. Cepeda and colleagues, for example, used multiparametric postoperative MRI features to train classifiers that localized later glioblastoma recurrence regions without supplying the evaluated follow-up label at inference [16]. By contrast, a retrospective target-conditioned analysis asks what a fixed transformation does after the realized target is known. The latter can examine error structure and update behaviour, but cannot be presented as prospective forecasting.

We designed the present study around this separation. A cross-case model first produced P0 from current contrast-enhanced T1 MRI and an available current binary segmentation. “Future-blind” therefore means blind to the evaluated case's future image, future segmentation and future-added target; it does not mean raw-MRI-only inference or independence from a current segmentation. P0 was frozen before future outcome access. Prediction-Comparison-Correction (PCC) then used the realized one-sided segmentation-change target to reinforce target-aligned discrepancy within a target-derived support region while explicitly suppressing unsupported probability outside that region. In the name Prediction-Comparison-Correction, “Prediction” denotes the pre-existing P0 supplied to the framework; the correction stage is not itself a prospective forecasting procedure.

This access asymmetry creates an unavoidable answer-conditioning concern. Comparing PCC only with Fixed P0 cannot isolate algorithmic structure because Fixed receives no target. We therefore retain Fixed as the future-blind baseline while also describing locked target-access controls: EIA-linear, direct EIA blends and, internally, EIA-morph. These are not deployable competitors; they contextualize whether a structured iterative rule behaves differently from simpler uses of the same retrospective information. No new inferential family was introduced.

The evidence was organized hierarchically. A 40-patient development cohort supported ablation, guidance perturbation and the post-hoc identification of a no-smoothing candidate. Two later protocols independently locked the canonical and candidate methods: an internal 113-patient cohort with future-blind P0 generation, and a 39-patient RHUH cohort testing cross-dataset P0 transfer followed by retrospective correction. We asked whether the fixed PCC behaviour replicated across these cohorts, while preserving negative controls, domain-shift attenuation and the distinction between prediction and target-conditioned refinement.

## Results

### Cohorts, segmentation target and future-access boundary

The development cohort contained 40 patients, the amended independent internal cohort 113, and the RHUH external cohort 39 (Table 1). Two internal records were excluded after P0 generation but before target construction or outcome evaluation because of a pre-outcome identity/label-assignment anomaly; all original P0 evidence was retained. RHUH-0008 was excluded before external P0 generation because lossless orientation operations could not establish a shared physical voxel grid. No patient was excluded by target size or performance.

Official clinical metadata matched every locked patient ID. Development patients had median age 57.5 years (IQR 53.0–65.0), 17/40 were female, and all 40 were recorded as grade-4 GBM. Internal confirmatory patients had median age 60.0 years (IQR 43.0–69.0), 47/113 were female and diagnoses included GBM (74), astrocytoma (23), diffuse glioma (9), oligodendroglioma (4), pilocytic astrocytoma (2) and glioma with GBM features (1). RHUH patients had median age 64.0 years (IQR 55.0–69.5), 12/39 were female, all had grade-4 glioblastoma, 35 were IDH wild type and four IDH mutant. Clinical variables were not harmonized or tested between cohorts.

For both datasets, binary masks were composite foreground definitions. MU used the union of non-background labels, including non-enhancing tumour core, surrounding non-enhancing FLAIR abnormality, enhancing foreground and resection cavity. RHUH used segmentation>0: necrosis, peritumoral/non-enhancing abnormality and enhancing tumour. The prelocked mapping was the closest available pathological-region mapping, not perfect ontology equivalence. The target was the one-sided, segmentation-derived future-added composite foreground, T=M_future AND NOT M_current. It omitted foreground that disappeared at follow-up and was neither a symmetric change map nor histological recurrence.

### Development analyses characterized update behaviour

Each development patient's P0 was a patient-disjoint out-of-fold prediction from the single checkpoint for its held-out fold. Development comparisons used the locked oracle-assisted target-volume-matched top-k Dice unless otherwise stated. Under that retrospective localization metric, canonical Full PCC reached 0.388, no-smoothing reached 0.500, removal of error guidance yielded 0.288 and removal of outside suppression yielded 0.361 (Figure 5). These values are not Dice@0.5 and do not measure deployment performance. Shuffling patient targets reduced the locked development score, and partial or displaced guidance attenuated correction. The spatial analyses were exploratory and were not interpreted as causal biology.

No-smoothing emerged post hoc in development. Full PCC remained canonical. The candidate was subsequently specified before both independent analyses, so its later evidence is confirmatory of a predeclared candidate rather than proof that it was the original method.

### Independent internal confirmation

All 113 internal patients were absent from every predictor-training partition. Their P0 maps were equal-weight arithmetic means of the five frozen fold checkpoints, each receiving only current T1c and current segmentation. Mean Dice@0.5 was 0.239 for Fixed P0, 0.444 for canonical Full PCC and 0.637 for no-smoothing (Figure 2). Full PCC minus Fixed had mean paired difference 0.205 and median difference 0.212; all 113 differences were positive. The two-sided Wilcoxon P value was 2.803e-20, Holm-adjusted P was 5.606e-20, and the 10,000-resample paired bootstrap interval was 0.191–0.218 (Table 2).

No-smoothing minus Full PCC had mean difference 0.193, median difference 0.189, and 113/0/0 wins/ties/losses. Its two-sided Wilcoxon P value was 2.803e-20, Holm-adjusted P 5.606e-20, and bootstrap interval 0.174–0.213. These were the only two confirmatory comparisons.

### Matched-information controls contextualized target access

Table 3 reports descriptive results for seven locked methods. Internally, EIA-linear, EIA-blend-0.90 and EIA-blend-0.75 had Dice@0.5 means 0.296, 0.259 and 0.317. EIA-blend-0.75 achieved AP 0.478, exceeding canonical PCC AP 0.414. Thus PCC did not dominate every target-access control or metric. Fixed versus PCC measures the combined consequence of target access and algorithmic update; matched-information controls help distinguish structured update behaviour from simple target access alone, but cannot remove the oracle nature of the target. No comparator P values were added (`NOT_PRELOCKED_NOT_RUN`).

### Fixed ten-round trajectory

Canonical PCC propagated state for exactly ten rounds, and P10 remained formal for every patient (Figure 3). Mean Dice increased across the cohort-level internal trajectory, but the rule was not replaced by per-case best-round selection. One internal patient had a late P9-to-P10 decline. This retained negative observation prevents a claim of universal patient-level monotonicity.

### RHUH future-blind transfer and retrospective replication

The RHUH Stage A execution mounted only early-postoperative T1ce, early-postoperative segmentation and the five frozen checkpoints. All 39 patients were external to training, and no RHUH training, fine-tuning, calibration or test-time adaptation occurred. The five checkpoint maps were averaged at 0.2 each. Before recurrence voxel access, all 39 P0 maps were frozen and hash-verified. Fixed P0 mean Dice@0.5 was 0.190, lower than the internal estimate and consistent with domain shift rather than evidence of correction failure [5,6].

After the outcome-access lock, canonical PCC reached mean Dice 0.365 and no-smoothing 0.451 (Figure 4). Full PCC minus Fixed had n=39, mean paired difference 0.176, median 0.185, 39/0/0 wins/ties/losses, two-sided P=3.638e-12, Holm P=7.276e-12 and bootstrap interval 0.151–0.199. No-smoothing minus Full PCC had mean difference 0.086, median 0.088, 38/0/1 wins/ties/losses, two-sided P=7.276e-12, Holm P=7.276e-12 and interval 0.072–0.101. RHUH matched-information controls again showed mixed metric rankings (Table 3), precluding universal superiority claims.

## Discussion

The principal finding is deliberately narrow. A current-image-and-current-segmentation model produced a frozen P0 without access to the evaluated case's future outcome. Once a one-sided future-added composite segmentation target became available, the fixed canonical PCC rule improved Dice@0.5 in independent internal and RHUH cohorts. This is evidence for reproducible retrospective target-conditioned map refinement. It is not evidence that PCC prospectively predicts recurrence.

The two stages answer different questions. P0 estimates future segmentation change conditionally on current T1c and an available current segmentation. PCC then compares that pre-existing map with the realized target. The word “Prediction” in Prediction-Comparison-Correction refers to P0, not to the correction stage. The current-mask dependency is material: this study did not evaluate manual versus automatic production of that mask, propagation of current-segmentation errors, or an end-to-end raw-MRI deployment pipeline.

Answer conditioning remains the central interpretation constraint. Full PCC versus Fixed does not isolate algorithmic structure because only PCC receives T. Accordingly, the improvement over Fixed cannot be claimed as a novel predictive advantage of target access. The target-access EIA controls supply a more appropriate descriptive context. They showed that simple direct use of the target-derived signal could equal or exceed PCC on selected probability metrics, while fixed-threshold rankings differed. The study therefore asks a narrower question: given explicit retrospective target access, how do fixed update rules behave, and does the specified PCC behaviour reproduce across cohorts? The controls help separate structured updates from access alone; they do not “solve” the oracle problem.

Replication across the 113-patient internal cohort and RHUH strengthens technical reproducibility. The internal cohort isolated patients from all predictor training; RHUH additionally changed institution, acquisition and annotation context. The attenuation of Fixed P0 performance externally is expected under medical-imaging domain shift [5,6]. PCC's external correction remained directional, but its target-conditioned score must not be substituted for the future-blind transfer estimate.

No-smoothing also requires chronological restraint. It was not canonical PCC. It emerged from development analyses and was then prelocked as a candidate before the internal and RHUH outcomes. One computational hypothesis is that Gaussian smoothing attenuates sparse discrepancy, dilutes boundaries or spreads corrections beyond exact error voxels, whereas S_r=D_r retains voxelwise discrepancy. This is not a demonstrated biological mechanism, and imperfect-guidance analyses suggest a possible robustness trade-off.

The study occupies a different methodological niche from genuine recurrence prediction. Cepeda et al. trained postoperative MRI radiomic classifiers to localize subsequent glioblastoma recurrence without supplying the evaluated future label at inference [16]. Such work evaluates future-blind predictive information. Our P0 stage is conceptually aligned with that access boundary, although it uses different data and a current segmentation. PCC Stage B instead evaluates a retrospective transformation after the outcome is known. Direct comparison of their performance values would be inappropriate.

Limitations are substantial. PCC requires the true future-added target and has no deployment-time route to obtain it in this study. P0 assumes an available current segmentation. T is one-sided: it includes future foreground absent from current foreground but omits disappearing foreground, symmetric lesion change, volumetric response and histological recurrence. Dataset foregrounds are composites with imperfectly matched ontologies; the MU definition includes resection-cavity-related foreground whereas RHUH has no equivalent label. RHUH contributed 39 analysable patients from one institution. Source masks used dataset-specific automated and expert-refinement processes. The training checkpoints were selected by minimum training loss without a separate tuning partition because the historical canonical implementation did not include one; we retained that frozen policy rather than reconstructing a validation scheme retrospectively. No reader study, clinical decision analysis, prospective deployment test or patient-outcome utility analysis was performed.

Future work should evaluate a fully specified source for current segmentation, test genuinely future-blind models prospectively, and predefine any non-outcome guidance available at deployment. Within the present evidence, PCC is best treated as a reproducible retrospective method for studying target-conditioned probability-map updates, with Fixed P0 reported separately as the future-blind cross-case prediction component.

## Methods

### Study design and datasets

This retrospective secondary analysis used MU-Glioma-Post and RHUH-GBM [2,3]. MU contains postoperative longitudinal MRI, clinical metadata and composite segmentations. RHUH contains preoperative, early-postoperative and recurrence MRI from 40 patients with grade-4 glioblastoma. Cohort construction and exclusions were locked before outcome evaluation. Metadata in Table 1 were deterministically linked by exact patient ID from official source files; no missing value was imputed and no between-cohort test was performed.

The development set used 40 patient-level pairs and five 32-train/8-test folds. The independent internal source set contained 115 patients; PatientID_0113 and PatientID_0132 were excluded before target construction or performance access under the prelocked identity-anomaly rule, leaving 113. RHUH used early-postoperative current and recurrence future timepoints. RHUH-0008 was excluded before P0 generation for physical-grid incompatibility, leaving 39.

### Foreground definitions and one-sided target

MU current and future masks were the union of all non-background dataset labels: non-enhancing tumour core, surrounding non-enhancing FLAIR abnormality, enhancing foreground and resection cavity. RHUH masks were segmentation>0, combining necrosis (label 1), peritumoral/non-enhancing abnormality (label 2) and enhancing tumour (label 3). These were prelocked as the closest available mapping, not perfect ontology equivalence.

After P0 freeze, the target was T=(M_future>0) AND NOT(M_current>0). T is therefore a one-sided, segmentation-derived future-added composite foreground target. No registration, resampling, interpolation, morphology, target-size filtering or manual correction was performed during target construction.

### Predictor inputs, training labels and cohort-specific P0 generation

The slice-wise CrossCaseSmallUNet used a compact U-Net-derived encoder-decoder [4] with two input channels, one output channel and base width 16. Channel 0 was current T1c normalized using its positive-voxel 1st and 99th percentiles and clipped to [0,1]. Channel 1 was the binary current foreground segmentation. Sigmoid converted logits to probabilities. Thus inference was future-blind with respect to the evaluated case's future data, but conditional on both current MRI and current segmentation.

Training was ordinary supervised learning. Training patients contributed their own T masks as labels; slices were retained when current foreground or training-label foreground was present. The five patient-level folds used seed 42, 20 epochs, batch size 8, Adam learning rate 0.001, and 0.5 weighted binary cross-entropy plus 0.5 soft-Dice loss, with positive weight capped at 50. Checkpoints minimized mean training loss. No separate validation partition existed in the canonical historical implementation, so none was retrospectively introduced.

P0 pathways differed by cohort. For development, each patient's formal P0 came only from the checkpoint trained in the fold where that patient was held out; the evaluated patient's future mask and T were absent from that fold. For the independent 113, every patient was unseen by all five training partitions, so five frozen checkpoint maps were averaged with equal weights 0.2. RHUH used the same five-checkpoint equal-weight ensemble on a physically isolated dataset containing only early-postoperative T1ce and segmentation. It used no RHUH training, fine-tuning, calibration, checkpoint selection, test-time adaptation or recurrence voxel data. All P0 files were float32, checked for geometry, finiteness and [0,1] range, then frozen by SHA-256 before outcome access.

### Prediction-Comparison-Correction

Let P_r be the current float32 probability map, T the realized one-sided future-added target and R the support region defined by Euclidean distance at most 26 voxels from T. Each round formed signed within-support discrepancy D_r=(T-P_r)R, Gaussian-smoothed discrepancy S_r=GaussianSmooth(D_r, sigma=2.0 voxels), and outside-support probability O_r=P_r(1-R). The canonical update was

logit(P_{r+1}) = logit(P_r) + eta S_r - eta O_r,

followed by sigmoid, non-finite handling, clipping to [0,1] and state propagation. Probability-to-logit clipping used epsilon=1e-5; logits were clipped to [-30,30]. Eta was 0.30, dtype float32 and rounds=10. P10 was always formal. Outside-support probability was therefore explicitly suppressed in logit space, not preserved.

No-smoothing retained the same R, O_r, eta, clipping, dtype, state propagation and ten rounds. Its sole scientific difference was S_r=D_r. It was a post-hoc development candidate prelocked before both confirmatory analyses.

### Comparator methods

Fixed returned clipped P0. Naive was a target-free one-step transformation sigmoid(2.5 logit(P0)). For EIA methods, R was the same radius-26 support and G=normalize01(GaussianSmooth(T,2.0)). EIA-linear returned clip[P0+0.30G(1-P0)-0.30(1-R)P0]. EIA-blend-0.90 returned clip(0.90P0+0.10G), and EIA-blend-0.75 returned clip(0.75P0+0.25G). Internal EIA-morph thresholded P0 at 0.5, intersected it with R, applied one binary closing and hole filling, and retained components of at least 20 voxels. EIA methods accessed the target and were oracle-style retrospective controls; they were not evaluated as deployable models.

### Outcomes and statistics

The primary endpoint was patient-level Dice at probability>=0.5. Secondary metrics were IoU, precision, recall, soft Dice, Brier score, average precision, predicted-positive volume and target-to-predicted-volume ratio [10,11,15]. Target-volume-matched top-k Dice/IoU were labelled ORACLE_ASSISTED_RETROSPECTIVE_LOCALIZATION.

Each confirmatory family contained exactly Full PCC versus Fixed and no-smoothing versus Full PCC. The patient was the unit. Paired two-sided `scipy.stats.wilcoxon` used `zero_method='wilcox'`, `alternative='two-sided'` and the library default `method='auto'`; because no method argument was passed, results are reported as P values, not claimed to be exact. Holm adjustment covered exactly two hypotheses [12]. We report paired mean and median differences, wins/ties/losses, P values, Holm P, Cohen dz, rank-biserial effect size and percentile intervals from 10,000 paired patient bootstrap resamples [13]. Seeds were 20260803 internally and 20260810 externally. No EIA pairwise P values were added.

### Reproducibility, ethics and AI assistance

Protocol locks, case manifests, fold manifests, checkpoint and P0 hashes, outcome-access records, code hashes and frozen result releases were retained. Reporting was audited against CLAIM 2024 [7]; TRIPOD+AI was applied only to the future-blind prediction component where relevant [8], and PROBAST+AI informed an internal risk-of-bias review rather than a claim of full applicability to target-conditioned correction [9]. Manuscript V2 generation read only CSV/report authorities and official clinical metadata; it did not execute scientific methods.

The MU source study reports University of Missouri IRB approval (IRB #2096253 MU) and waiver of informed consent for retrospective de-identified data sharing [2]. The RHUH source study reports written consent and approvals from the Río Hortega Institutional Review Board and CEIm of the West Valladolid Health Area (Ref. 22PI-208) [3]. [AUTHOR CONFIRMATION REQUIRED: present-institution secondary-use determination.]

OpenAI Codex assisted author-supervised engineering, deterministic document assembly, drafting/editing and consistency checks. It was not an author and did not alter protocols or scientific results. [AUTHOR FINAL VERIFICATION REQUIRED: authors must verify all evidence, code, numbers, citations and text and retain responsibility.]

## Data availability

MU-Glioma-Post is available from TCIA under the source collection's conditions [2]. RHUH-GBM is available from TCIA under DOI 10.7937/4545-c905 and applicable access terms [3]. Derived numeric tables, protocol summaries and figure source data will be deposited at [PROCESSED_DATA_REPOSITORY_DOI_REQUIRED]. Source MRI, segmentations and large P0 arrays are not redistributed here.

## Code availability

Custom code, configs, hashes and deterministic manuscript scripts will be archived at [CODE_REPOSITORY_URL_REQUIRED] with an immutable release tag. Reviewer access will be supplied if public release is not available at initial submission.

## References

1. Wen, P. Y. et al. RANO 2.0: Update to the Response Assessment in Neuro-Oncology criteria for high- and low-grade gliomas in adults. J. Clin. Oncol. 41, 5187–5199 (2023). https://doi.org/10.1200/JCO.23.01059
2. Mahmoud, E. et al. MU-Glioma Post: A comprehensive dataset of automated MR multi-sequence segmentation and clinical features. Sci. Data 12, 1847 (2025). https://doi.org/10.1038/s41597-025-06011-7
3. Cepeda, S. et al. The Río Hortega University Hospital Glioblastoma dataset: A comprehensive collection of preoperative, early postoperative and recurrence MRI scans (RHUH-GBM). Data Brief 50, 109617 (2023). https://doi.org/10.1016/j.dib.2023.109617
4. Ronneberger, O., Fischer, P. & Brox, T. U-Net: Convolutional networks for biomedical image segmentation. Lect. Notes Comput. Sci. 9351, 234–241 (2015). https://doi.org/10.1007/978-3-319-24574-4_28
5. Yu, A. C., Mohajer, B. & Eng, J. External validation of deep learning algorithms for radiologic diagnosis: A systematic review. Radiol. Artif. Intell. 4, e210064 (2022). https://doi.org/10.1148/ryai.210064
6. Guan, H. & Liu, M. Domain adaptation for medical image analysis: A survey. IEEE Trans. Biomed. Eng. 69, 1173–1185 (2022). https://doi.org/10.1109/TBME.2021.3117407
7. Tejani, A. S. et al. Checklist for Artificial Intelligence in Medical Imaging (CLAIM): 2024 update. Radiol. Artif. Intell. 6, e240300 (2024). https://doi.org/10.1148/ryai.240300
8. Collins, G. S. et al. TRIPOD+AI statement: Updated guidance for reporting clinical prediction models that use regression or machine learning methods. BMJ 385, e078378 (2024). https://doi.org/10.1136/bmj-2023-078378
9. Moons, K. G. M. et al. PROBAST+AI: An updated quality, risk of bias, and applicability assessment tool for prediction models using regression or artificial intelligence methods. BMJ 388, e082505 (2025). https://doi.org/10.1136/bmj-2024-082505
10. Müller, D., Soto-Rey, I. & Kramer, F. Towards a guideline for evaluation metrics in medical image segmentation. BMC Res. Notes 15, 210 (2022). https://doi.org/10.1186/s13104-022-06096-y
11. Brier, G. W. Verification of forecasts expressed in terms of probability. Mon. Weather Rev. 78, 1–3 (1950). https://doi.org/10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2
12. Holm, S. A simple sequentially rejective multiple test procedure. Scand. J. Stat. 6, 65–70 (1979). https://doi.org/10.2307/4615733
13. Efron, B. Bootstrap methods: Another look at the jackknife. Ann. Stat. 7, 1–26 (1979). https://doi.org/10.1214/aos/1176344552
14. Johnson, D. R. et al. Congress of Neurological Surgeons systematic review and evidence-based guidelines update on the role of imaging in the management of progressive glioblastoma in adults. J. Neurooncol. 158, 225–247 (2022). https://doi.org/10.1007/s11060-021-03896-9
15. Taha, A. A. & Hanbury, A. Metrics for evaluating 3D medical image segmentation: Analysis, selection, and tool. BMC Med. Imaging 15, 29 (2015). https://doi.org/10.1186/s12880-015-0068-x
16. Cepeda, S. et al. Predicting Regions of Local Recurrence in Glioblastomas Using Voxel-Based Radiomic Features of Multiparametric Postoperative MRI. Cancers (Basel) 15, 1894 (2023). https://doi.org/10.3390/cancers15061894

## Acknowledgements

[ACKNOWLEDGEMENTS_REQUIRED]

## Author contributions

[AUTHOR_CONTRIBUTIONS_REQUIRED]

## Funding

[FUNDING_INFORMATION_REQUIRED]

## Competing interests

[COMPETING_INTERESTS_DECLARATION_REQUIRED]

## Figure legends

**Figure 1. Study design and future-access boundary.** P0 used current T1c plus current segmentation and was future-blind with respect to the evaluated case's future data. Training-patient future-added labels were ordinary supervision and did not create evaluated-case leakage. PCC began only after P0 freeze and target access.

**Figure 2. Independent internal prelocked comparisons.** Patient-level Dice@0.5 for Fixed, canonical Full PCC and prelocked no-smoothing in 113 patients. Displayed methods correspond to the confirmatory family; descriptive matched-information controls appear in Table 3.

**Figure 3. Canonical Full PCC trajectory.** Cohort means across the fixed P1–P10 sequence. P10 was retained for every patient; no best-round selection was performed.

**Figure 4. RHUH external prelocked comparisons.** Patient-level Dice@0.5 in 39 patients. Fixed is the future-blind P0 estimate; corrected maps are retrospective target-conditioned outputs. Matched-information controls appear in Table 3.

**Figure 5. Development-only oracle-assisted target-volume-matched localization.** The metric is target-volume-matched top-k Dice, requires target information, is not the fixed-threshold confirmatory endpoint and is not a deployment metric.

## Tables

**Table 1. Cohort characteristics and analysis flow.** Clinical metadata were linked from official source files by locked patient ID. Values are median (IQR) or counts. Source definitions differ; no between-cohort inference was performed. MU interval missingness was 1/40 development and 2/113 internal; RHUH exact scan interval was not consistently available.

**Table 2. Prelocked confirmatory comparisons for patient-level Dice@0.5.** P values are two-sided Wilcoxon signed-rank values with Holm adjustment over exactly two tests per cohort.

**Table 3. Descriptive performance of locked methods under different information-access conditions.** EIA and PCC methods access T; Fixed and Naive do not. Values are descriptive means. Pairwise EIA inference was not prelocked and was not run.
