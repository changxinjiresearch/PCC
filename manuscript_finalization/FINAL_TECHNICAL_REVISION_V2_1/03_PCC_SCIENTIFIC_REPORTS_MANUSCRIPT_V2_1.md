# Target-conditioned refinement of future-blind longitudinal glioma segmentation-change maps across independent cohorts

[AUTHOR_LIST_REQUIRED]

[AFFILIATIONS_REQUIRED]

Corresponding author: [CORRESPONDING_AUTHOR_AND_EMAIL_REQUIRED]

## Abstract

Longitudinal glioma segmentation-change localization requires separating prediction from analyses that use a realized outcome. We generated a starting probability map (P0) from current contrast-enhanced T1 MRI and an available current segmentation, without the evaluated case's future image, segmentation or future-added target. After P0 freeze, Prediction-Comparison-Correction (PCC) retrospectively used the one-sided future-added composite segmentation target in ten fixed logit-space updates. In 113 prelocked independent internal patients, mean Dice at threshold 0.5 was 0.239 for P0 and 0.444 for canonical PCC (paired difference 0.205, 95% bootstrap CI 0.191–0.218; Holm-adjusted P=5.61e-20). A no-smoothing candidate identified during development and prelocked before confirmation reached 0.637. In 39 RHUH patients, a physically isolated five-checkpoint P0 ensemble yielded mean Dice 0.190; canonical PCC and prelocked no-smoothing reached 0.365 and 0.451. Descriptive target-access comparators showed that target-derived information and update structure both shaped results. PCC therefore provides reproducible retrospective target-conditioned refinement, not prospective recurrence forecasting or clinical validation.

Keywords: glioma; longitudinal MRI; segmentation change; external technical validation; target conditioning; reproducibility

## Introduction

Longitudinal imaging is central to the assessment of glioma after surgery and adjuvant treatment, yet spatial comparison across timepoints is intrinsically difficult. Resection changes anatomy; cavities, blood products and treatment-related signal can alter the postoperative baseline; and enhancing and non-enhancing abnormalities need not evolve together. Scan timing and treatment history further affect what a foreground label represents at a given visit. Contemporary response criteria therefore define explicit baselines and longitudinal rules rather than treating every new imaging abnormality as equivalent evidence of progression [1,14]. Segmentation adds a spatial representation to that assessment, but a dataset-derived binary foreground is not itself viable tumour, histological progression or the complete biological state of a lesion. This distinction matters for both model inputs and reference standards, particularly when masks combine enhancing foreground, non-enhancing abnormality, necrosis or resection-cavity-related labels [2,3]. Our task is consequently described as localization of segmentation change rather than prediction of biological tumour growth or clinical progression.

Single-timepoint segmentation and future localization are also different computational problems. A segmentation model delineates a structure visible in the input image. A future-localization model must estimate where a later annotation will differ from the current annotation while the evaluated future outcome remains unavailable. Such evaluation is especially vulnerable to leakage because follow-up images, masks, target-derived sampling, checkpoint selection or post hoc case filtering can all transfer outcome information into the apparent prediction pathway. A current-timepoint segmentation can legitimately be used as a conditional input if it would be available at that time, but this does not make the system an autonomous raw-MRI predictor. We therefore use “future-blind” only with respect to the evaluated case's future image, future segmentation and future-added target. In this study P0 is conditioned on current contrast-enhanced T1 MRI (T1c) and an available current binary segmentation.

Genuinely future-blind recurrence-localization studies provide an important reference point. Cepeda and colleagues used voxel-based radiomic features from multiparametric postoperative MRI to localize later glioblastoma recurrence without supplying the evaluated recurrence label at inference [16]. That design addresses predictive information available before the future event. More broadly, medical-imaging models often lose performance when transferred across institutions, scanners and annotation practices, making frozen external evaluation important [5,6]. The present work includes a future-blind component with the same outcome-access boundary, but its principal correction stage addresses a different question. It does not replace or compete directly with prospective recurrence forecasting, and performance after outcome-conditioned correction cannot be interpreted as deployment-time prediction.

The methodological gap arises once a realized follow-up target is legitimately available for retrospective analysis. A frozen prediction can then be compared with that target to study how a predetermined update rule redistributes probability. The key distinction is between the information supplied by the target and the behaviour imposed by the update rule. A comparison between a target-conditioned method and unchanged P0 necessarily combines both effects. We therefore used target shuffling, component ablations, imperfect-guidance perturbations and retrospective target-access comparators to examine whether spatially appropriate guidance and specific algorithmic terms mattered. These comparators receive target-derived information, but not in identical representations or through identical transformations; they contextualize rather than eliminate answer conditioning. Independent protocol locks were then required to determine whether the observed update behaviour reproduced beyond development.

Multiple metrics were retained because thresholded overlap and probability-map quality answer different questions. Dice and intersection-over-union at a fixed threshold of 0.5 quantify binary localization under the predeclared decision rule. Soft Dice summarizes continuous overlap, Brier score evaluates voxelwise probabilistic error, and average precision summarizes ranking under class imbalance [10,11,15]. Target-volume-matched top-k overlap was used only as an oracle-assisted retrospective localization measure: it fixes the predicted positive volume using the target and is therefore neither a deployment metric nor interchangeable with Dice@0.5. Keeping these metric systems separate prevents a target-dependent development score from being mistaken for confirmatory future-blind performance.

We evaluated this framework across three evidence levels. A 40-patient development cohort supported algorithmic ablation, imperfect-guidance analysis and the post hoc identification of a no-smoothing candidate. A later 113-patient independent internal cohort used prelocked, future-blind P0 maps and two prespecified confirmatory comparisons. Finally, 39 patients from the independent RHUH-GBM collection tested transfer of the unchanged five-checkpoint predictor before a separately locked retrospective correction stage [3]. The canonical method remained Prediction-Comparison-Correction (PCC); “Prediction” denotes the pre-existing P0 supplied to the framework, not prospective forecasting by the correction stage. We asked whether fixed target-conditioned update behaviour reproduced internally and across datasets, whether a prelocked no-smoothing simplification replicated after its developmental discovery, and how target-access controls qualified the interpretation of any improvement.

## Results

### Cohorts, target semantics and future-access boundary

The evidence hierarchy comprised 40 development patients, 113 independent internal patients and 39 RHUH external patients (Table 1). The internal source manifest initially contained 115 patients. PatientID_0113 and PatientID_0132 were excluded together after Stage A P0 generation but before target construction or performance access because a pre-outcome identity/label-assignment anomaly prevented treating them as independent patients; their original P0 files and the 115-patient manifest remained in the audit chain. The RHUH source contained 40 patients. RHUH-0008 was excluded before external P0 generation because lossless axis permutation and flipping could not place its current and recurrence data on a common physical voxel grid. No patient was excluded according to target size, P0 appearance or performance, and end-to-end scientific failures were zero in both confirmatory cohorts.

The binary foregrounds were dataset-specific composites. MU used all non-background labels, including non-enhancing tumour core, surrounding non-enhancing FLAIR abnormality, enhancing foreground and resection cavity. RHUH used segmentation>0, combining necrosis, peritumoral/non-enhancing abnormality and enhancing tumour. Their prelocked correspondence was the closest available pathological-region mapping, not perfect ontology equivalence. For each retained pair, the reference was T=M_future AND NOT M_current: a one-sided, segmentation-derived future-added composite foreground target. It excludes foreground that disappears by follow-up and is not a symmetric lesion-change map, a measure of total response, histologically confirmed recurrence or pure viable tumour growth. In every pathway, P0 was generated and frozen before the evaluated case's future segmentation was accessed.

### Development analyses characterized PCC behaviour

Each development P0 was produced by the single checkpoint for the patient's patient-disjoint held-out fold. At the deployment-style threshold of 0.5, mean Dice was 0.216 for Fixed, 0.326 for canonical Full PCC and 0.385 for no-smoothing; corresponding soft-Dice means were 0.222, 0.270 and 0.309, average precision means were 0.229, 0.373 and 0.523, and Brier scores were 0.00630, 0.00470 and 0.00385. These descriptive development estimates use a different data role from the later confirmatory cohorts and were not promoted into the confirmatory family.

Mechanistic development experiments used the separately locked oracle-assisted target-volume-matched top-k metric (Figure 5 and Supplementary Table S5). Under that target-dependent metric, Fixed P0 achieved mean Dice 0.276, canonical Full PCC 0.388 and no-smoothing 0.500. Turning off error guidance while retaining outside suppression reduced the score to 0.288; retaining error guidance but removing outside suppression yielded 0.361. With both terms off, the score returned to 0.276. A global-discrepancy variant reached 0.393, showing that not every deviation from the canonical support reduced the development score. Shuffled target assignment attenuated performance, supporting dependence on spatially appropriate guidance rather than an arbitrary target-derived mass, but it did not remove the oracle nature of the clean target.

Guidance perturbations further qualified the clean-target result (Supplementary Tables S6 and S7). For Full PCC, oracle-assisted top-k Dice was 0.388 with clean guidance, 0.349 with 50% partial guidance, 0.324 with 25% partial guidance, 0.384 after addition of 25% false-positive guidance, 0.368 after a three-voxel shift and 0.333 under mixed perturbation. Thus incomplete or displaced guidance generally attenuated correction, although the false-positive condition was close to the clean result. No-smoothing was stronger under clean guidance but its advantage narrowed under imperfect guidance, motivating a possible precision–robustness trade-off rather than a universal superiority claim. Spatial analyses remained exploratory and were not interpreted as causal or biological evidence.

### Independent internal confirmation

All 113 independent internal patients were absent from every predictor-training partition. Their P0 maps were equal-weight arithmetic ensembles of the five frozen fold checkpoints, with each checkpoint receiving only current T1c and current segmentation. Mean Dice@0.5 was 0.239 for Fixed P0, 0.444 for canonical Full PCC and 0.637 for no-smoothing (Figure 2). Full PCC minus Fixed had a mean paired difference of 0.205, median difference of 0.212 and 113/0/0 wins/ties/losses. The paired two-sided Wilcoxon P value was 2.803e-20, the Holm-adjusted P value was 5.606e-20, the 10,000-resample paired bootstrap 95% interval was 0.191–0.218, Cohen dz was 2.746 and rank-biserial effect size was 1.000 (Table 2).

No-smoothing minus Full PCC had mean difference 0.193, median difference 0.189 and 113/0/0 wins/ties/losses. Its two-sided P value was 2.803e-20, Holm-adjusted P was 5.606e-20, bootstrap interval was 0.174–0.213, Cohen dz was 1.797 and rank-biserial effect size was 1.000. These were the only two internal confirmatory hypotheses. Supporting probability metrics moved in the same general direction: Fixed, Full PCC and no-smoothing had mean IoU@0.5 of 0.143, 0.303 and 0.496; soft Dice of 0.185, 0.267 and 0.320; Brier score of 0.00452, 0.00310 and 0.00258; and average precision of 0.227, 0.414 and 0.647, respectively. The pattern therefore was not confined to one thresholded-overlap summary.

### Retrospective target-access comparator context

Table 3 places the confirmatory methods beside frozen descriptive controls without adding inferential hypotheses. Internally, EIA-linear and EIA-blend-0.75 achieved mean Dice@0.5 of 0.296 and 0.317, compared with 0.444 for canonical PCC and 0.637 for no-smoothing. Their probability-metric rankings were not identical: EIA-blend-0.75 had mean soft Dice 0.253 and average precision 0.478, whereas canonical PCC had 0.267 and 0.414. EIA-morph, evaluated only in the internal confirmatory analysis, is reported in Supplementary Table S8. In RHUH, EIA-linear and EIA-blend-0.75 reached Dice@0.5 of 0.246 and 0.248, compared with 0.365 and 0.451 for canonical and no-smoothing PCC. EIA-linear had external soft Dice 0.276, exceeding canonical PCC at 0.238, and EIA-blend-0.75 average precision was 0.407 compared with 0.309 for canonical PCC and 0.404 for no-smoothing. These mixed rankings are retained as negative context. The methods shared access to target-derived information but did not receive an identical representation or transformation, so no universal superiority or causal decomposition is claimed. Pairwise comparator inference was not prelocked and was not run.

### Fixed ten-round trajectory

Canonical PCC propagated its probability state for exactly ten rounds, and P10 was formal for every patient (Figure 3). Internal cohort mean Dice@0.5 increased from P1 to P10, but the protocol did not select a per-patient best round. P10 was best or tied-best for 112 of 113 internal cases. PatientID_0242_T1_to_T3_t1c declined from P9 to P10 and nevertheless retained P10, providing a concrete counterexample to universal patient-level monotonicity. The RHUH cohort also improved across the fixed P1-to-P10 sequence, and no RHUH patient showed late P10 degradation. These trajectories describe the locked update path; they were not used to revise the round count or identify an outcome-dependent stopping rule.

### RHUH future-blind predictor transfer

RHUH Stage A assessed cross-dataset transfer of the predictor before any correction. The execution environment contained the 39 early-postoperative T1ce images, their current segmentations and the five hash-matched frozen checkpoints, but no recurrence image or segmentation array. The same p1/p99 current-volume normalization and equal 0.2 checkpoint weights were used; there was no RHUH training, fine-tuning, recalibration, checkpoint selection or test-time adaptation. All 39 float32 P0 maps passed geometry, finiteness and range checks and were frozen by SHA-256 before outcome access.

These Fixed results are the external future-blind transfer estimates. Mean Dice@0.5 was 0.190, IoU@0.5 0.111, soft Dice 0.151, Brier score 0.00928 and average precision 0.153. Each was lower than the corresponding independent internal estimate, a descriptive pattern consistent with domain shift in institution, acquisition, postoperative context and annotation practice [5,6]. No between-cohort significance test was prespecified or performed. Importantly, the later target-conditioned maps do not replace these numbers when describing the performance of the future-blind predictor.

### RHUH retrospective external confirmation

After the outcome-access lock, canonical Full PCC achieved mean Dice@0.5 of 0.365 and no-smoothing 0.451 (Figure 4). Full PCC minus Fixed had n=39, mean difference 0.176, median difference 0.185 and 39/0/0 wins/ties/losses. The two-sided Wilcoxon P value was 3.638e-12, Holm-adjusted P was 7.276e-12, the paired bootstrap interval was 0.151–0.199, Cohen dz was 2.236 and rank-biserial effect size was 1.000. No-smoothing minus Full PCC had mean difference 0.086, median 0.088, 38/0/1 wins/ties/losses, P=7.276e-12, Holm P=7.276e-12, interval 0.072–0.101, Cohen dz 1.807 and rank-biserial 0.997 (Table 2).

Supporting metrics again showed substantial but non-identical changes. Full PCC and no-smoothing had mean IoU@0.5 of 0.239 and 0.314, soft Dice of 0.238 and 0.270, Brier scores of 0.00646 and 0.00576, and average precision of 0.309 and 0.404. The target-access comparators provided the mixed contextual rankings described above (Table 3). Oracle-assisted target-volume-matched top-k results are reported separately in Supplementary Table S9 and are not deployment estimates. All 39 patients completed every method, no result-driven exclusion occurred, and the fixed P10 endpoint was retained.

## Discussion

This study separates two forms of evidence that are easily conflated. A predictor first generated P0 from current T1c and a current segmentation while remaining blind to the evaluated case's future outcome. After P0 freeze, canonical PCC used the realized one-sided future-added target in a fixed retrospective update. Canonical PCC improved the prelocked Dice@0.5 endpoint in both the 113-patient independent internal cohort and the 39-patient RHUH cohort, and a no-smoothing candidate discovered post hoc in development but prelocked before both confirmations again improved the canonical output. The direction reproduced despite attenuation of both future-blind P0 performance and correction effects externally. Descriptive target-access controls further showed that quantitative behaviour depended on the update rule, while also preserving strong secondary results from some EIA controls.

The answer-conditioning issue is therefore not a peripheral limitation; it defines the scope of the correction stage. PCC receives the realized target, and Fixed does not. Full PCC versus Fixed consequently combines the informational effect of target access with the structural effect of PCC's discrepancy, support, smoothing and outside-suppression terms. The large paired improvement cannot be interpreted as an increase in prospective recurrence-forecasting accuracy or proof that target access is unimportant. Fixed P0 is the estimate relevant to future-blind transfer. PCC is a retrospective transformation whose output can be evaluated only after the reference outcome is known. Stating this boundary prevents the corrected Dice from being substituted for a deployment-time prediction result.

The retrospective experiments nevertheless answer a bounded methodological question: given explicit target-derived information, do predetermined update rules exhibit different and reproducible behaviour? Target shuffling showed that clean performance depended on spatially appropriate guidance rather than merely introducing arbitrary target-derived signal. Factorial ablations showed contributions from both error guidance and outside-support suppression. The ten-round trajectories demonstrated the behaviour of a fixed state-propagating rule rather than a single post hoc overwrite. Independent protocol locks then tested whether the same definitions reproduced beyond development. None of these analyses proves that oracle conditioning has been removed; together they characterize how a frozen probability map responds to specified retrospective guidance.

The EIA controls sharpen, but do not complete, this interpretation. EIA and PCC share access to target-derived information, yet they are not strictly information-equivalent: the target can be smoothed, blended, restricted by a support region or repeatedly propagated, and each transformation changes the representation delivered to the output. Table 3 should therefore be read as descriptive context rather than a causal decomposition of target access and algorithmic structure. The strong EIA-blend average precision internally and EIA-linear soft Dice externally are important negative evidence against universal PCC superiority. They also show why endpoint discipline matters: fixed-threshold localization, continuous overlap and voxel ranking need not favour the same method. The confirmatory family remained limited to Full PCC versus Fixed and no-smoothing versus Full PCC; no outcome-driven EIA hypothesis was added.

No-smoothing has a similarly constrained interpretation. Full PCC, including Gaussian smoothing, was the canonical algorithm. The no-smoothing variant emerged from development analyses and only then became a prelocked candidate for the independent internal and RHUH protocols. Its replication is evidence for a candidate simplification, not evidence that it was the original method. A plausible computational explanation is that Gaussian smoothing attenuates sparse discrepancy amplitudes, spreads corrections across boundaries and reduces exact voxelwise alignment when guidance is clean. Setting S_r=D_r preserves the unsmoothed discrepancy while leaving outside-support suppression unchanged. This is a mechanistic hypothesis about the update rule, not a biological mechanism. Moreover, its advantage narrowed under partial, shifted and mixed guidance, suggesting a possible precision–robustness trade-off that needs prospective evaluation with non-oracle guidance.

The RHUH analysis adds a distinct test of reproducibility. The predictor crossed institutions and data distributions without training, fine-tuning, calibration or test-time adaptation; current-only Stage A physically excluded recurrence arrays. Its lower Fixed Dice, soft Dice and average precision and higher Brier score relative to the internal cohort indicate a meaningful transfer challenge rather than an artificially matched test set. Under that shift, canonical PCC still improved the prelocked paired endpoint and no-smoothing again improved canonical PCC. The descriptive mean Full-PCC effect was about 0.205 internally and 0.176 externally; the additional no-smoothing effect was about 0.193 and 0.086. These differences may reflect domain-shift attenuation, but no between-cohort inferential comparison was prespecified, and the external sample came from one institution. Directional replication therefore supports technical reproducibility, not broad clinical generalizability.

This distinction also positions the work relative to genuinely future-blind recurrence prediction. Cepeda et al. localized later glioblastoma recurrence from postoperative multiparametric MRI features without giving the evaluated future label to the classifier [16]. Such studies ask whether current information forecasts a later spatial event. Our P0 stage has that future-access boundary, although it additionally assumes a current segmentation and uses different training data and architecture. PCC Stage B begins only after the future-added target has been realized. It is not a substitute for Cepeda-type prediction and cannot claim prospective clinical forecasting. A more appropriate use is retrospective methodological analysis: holding a future-blind map fixed, PCC tests how a specified structured correction behaves once the outcome is available.

Several input and reference-standard limitations remain. P0 requires both current T1c and a current binary segmentation. We did not evaluate whether that segmentation would be manual or automated in practice, its acquisition burden, error propagation from an imperfect current mask, or a fully autonomous raw-MRI workflow. The target is also one-sided: future foreground absent from current foreground is included, whereas disappearing foreground, treatment response and total symmetric lesion evolution are not. Both datasets use composite foregrounds. MU includes resection-cavity-related foreground, while RHUH combines necrosis, peritumoral or non-enhancing abnormality and enhancement without a corresponding cavity label. Their locked mapping is clinically adjacent but not ontologically identical, and neither target should be equated with pure viable tumour or histologically confirmed recurrence. Reference-segmentation uncertainty and inter-reader variability were not independently quantified in the present analysis.

Statistical strength and clinical utility are likewise different. The small paired P values, intervals excluding zero and large standardized effects show that the prelocked patient-level contrasts are highly inconsistent with their null hypotheses in these cohorts. They do not establish decision benefit, boundary safety, treatment utility or patient-outcome improvement. Dice@0.5 was the primary localization endpoint; soft Dice, Brier score and average precision supplied complementary probability-map information but remain dependent on the dataset reference labels. A high overlap after target conditioning can coexist with limited value of the starting future-blind map, and the two should not be merged into a single performance narrative. Conversely, calibration-oriented summaries cannot establish that a corrected region is clinically actionable. RHUH included 39 analysable patients from a single institution, no reader study was conducted, and no prospective workflow or clinical-outcome analysis was attempted. Checkpoints were selected by training loss because the historical canonical training did not contain a separate tuning partition; we retained the frozen policy rather than retrospectively redesigning it. This choice preserves the actual experiment but leaves uncertainty about checkpoint stability and hyperparameter selection that a future prospectively designed study should address with a distinct tuning set.

The next step is not to reinterpret target-conditioned scores as predictions, but to test a fully specified future-blind pipeline. That work should predefine how current segmentations are obtained, propagate their uncertainty, evaluate independent multi-institution cohorts and use only guidance available before outcome realization. Prospective studies could then ask whether a frozen predictor provides clinically useful localization. Within the present evidence, PCC is best understood as a reproducible retrospective framework for studying structured, target-conditioned probability-map updates, while Fixed P0 remains the separately reported future-blind cross-case prediction component.

## Methods

### Study design and cohorts

This retrospective secondary analysis used MU-Glioma-Post and RHUH-GBM [2,3]. The evidence hierarchy was fixed before manuscript V2.1: a 40-patient development cohort, an independent internal cohort and an external RHUH cohort. The development set used 40 patient-level pairs and five 32-train/8-test folds. The independent internal source set contained 115 patients; PatientID_0113 and PatientID_0132 were excluded together under the pre-outcome identity/label-assignment anomaly rule before target construction or performance access, leaving 113. RHUH used early-postoperative current and recurrence future timepoints. RHUH-0008 was excluded before P0 generation because lossless orientation operations did not establish physical-grid identity, leaving 39. Geometry repair by registration, resampling, interpolation or header rewriting was prohibited. Cohort denominators and exclusions were not changed during manuscript preparation.

### Clinical metadata and foreground definitions

Descriptive metadata were linked to locked IDs from official MU-Glioma-Post and RHUH-GBM clinical files. Age, source-recorded sex, diagnosis, grade, interval and available RHUH IDH, resection and treatment fields were retained without imputation. Source terminology differed (“Sex at Birth” for MU and “Sex” for RHUH); Table 1 reports Sex, female/male without inferring gender identity. No metadata variable was used for exclusion, subgroup modelling or inferential testing.

MU current and future masks were unions of all non-background dataset labels: non-enhancing tumour core, surrounding non-enhancing FLAIR abnormality, enhancing foreground and resection cavity. RHUH masks were segmentation>0, combining necrosis (label 1), peritumoral/non-enhancing abnormality (label 2) and enhancing tumour (label 3). These definitions were prelocked as the closest available mapping, not perfect ontology equivalence. After P0 freeze, the target was T=(M_future>0) AND NOT(M_current>0), a one-sided, segmentation-derived future-added composite foreground target. Target construction used Boolean logic only, with no morphology, size filtering, manual editing, registration, resampling or interpolation.

### Predictor inputs, supervision and training

The slice-wise CrossCaseSmallUNet was a compact U-Net-derived encoder-decoder [4] with two input channels, one output channel and base width 16. Channel 0 was current T1c normalized by the positive-voxel 1st and 99th percentiles of that current volume and clipped to [0,1]. Channel 1 was the binary current foreground segmentation. Sigmoid converted logits to probabilities. Thus inference was future-blind with respect to the evaluated case's future data but conditional on current MRI and current segmentation.

Training was ordinary supervised learning, not “future-blind training.” Training patients contributed their own one-sided future-added targets as labels, and slices were retained when current foreground or training-label foreground was present. Five patient-level folds used seed 42, 20 epochs, batch size 8, Adam learning rate 0.001, and 0.5 weighted binary cross-entropy plus 0.5 soft-Dice loss, with positive weight capped at 50. Checkpoints minimized mean training loss. The historical canonical implementation contained no separate validation partition; none was retrospectively reconstructed. The critical leakage boundary was patient-specific: the future image, future segmentation and target of an evaluated patient could not enter the pathway producing that patient's P0.

### Cohort-specific P0 pathways

P0 generation differed by cohort. For development, each patient's formal P0 came only from the checkpoint trained for the fold in which that patient was held out. The evaluated patient was absent from that fold's fitting data, including its future label; this was a patient-disjoint out-of-fold single-predictor pathway, not a five-model ensemble. For the independent 113, every evaluated patient was absent from all five development training partitions, so the five frozen checkpoint probability maps were averaged with equal weights of 0.2. RHUH used the same five hash-matched checkpoints and equal weights on a physically isolated current-only Stage A dataset. There was no RHUH training, fine-tuning, calibration, fold selection or test-time adaptation. Each P0 was stored as float32, checked for geometry identity, finiteness and range [0,1], and frozen by SHA-256 before future outcome access.

### Prediction-Comparison-Correction

Let P_r denote the current float32 probability map, T the realized future-added target and R the support comprising voxels within Euclidean distance 26 voxels of T. Initial P_0 was safely clipped to [epsilon,1-epsilon], epsilon=1e-5. At round r, signed discrepancy within support was D_r=(T-P_r)R, Gaussian-smoothed discrepancy was S_r=GaussianSmooth(D_r,sigma=2.0 voxels), and outside-support probability was O_r=P_r(1-R). Canonical PCC then applied the editable logit-space update in equation (1), followed by sigmoid, clipping and state propagation. The coefficient eta was 0.30, calculations were float32, ten rounds were always executed and P10 was the formal output. Outside-support probability was explicitly suppressed; it was not preserved. In Prediction-Comparison-Correction, “Prediction” refers to the pre-existing P0, not to prospective forecasting by the correction stage.



logit(P_{r+1}) = logit(P_r) + eta S_r - eta O_r    (1)

### No-smoothing and comparator methods

No-smoothing PCC was identical to canonical PCC except that S_r=D_r; outside-support suppression, eta, radius, clipping, state propagation, round count and P10 selection were unchanged. Full PCC remained canonical. No-smoothing was identified post hoc in development, then prelocked as a candidate before the independent internal and RHUH outcomes.

Fixed returned safely clipped P0 without target access. Naive applied sigmoid(2.5 logit(P0)), using epsilon 1e-5 and logit clipping [-30,30], without target access. For EIA methods, R used the same 26-voxel radius and G was the [0,1]-normalized Gaussian smoothing of float32 T with sigma 2.0. EIA-linear returned clip[P0+0.30G(1-P0)-0.30(1-R)P0]. EIA-blend-0.90 and EIA-blend-0.75 returned clip(0.90P0+0.10G) and clip(0.75P0+0.25G). Internal-only EIA-morph thresholded P0 at 0.5, intersected it with R, performed one binary closing and hole filling, and retained connected components of at least 20 voxels. EIA methods were retrospective oracle-style target-access controls and were not described as deployable models.

### Development analyses and trajectories

Development evaluation separated threshold-independent or fixed-threshold summaries from the locked target-volume-matched top-k metric. Factorial mechanism variants switched error guidance and outside suppression on or off. A global-discrepancy variant, patient-level shuffled targets and target-construction checks were retained as development controls. Imperfect-guidance conditions included retention of 50% or 25% of target foreground, addition of 25% false-positive guidance, a three-voxel shift and a mixed partial-plus-false-positive condition. These experiments were not rerun for V2.1; only frozen summaries were reported. Canonical Full PCC trajectories recorded P1 through P10 for all 113 internal and 39 RHUH patients. P10 remained formal without per-case best-round selection.

### Evaluation metrics

The primary endpoint in each confirmatory cohort was patient-level Dice at the fixed rule probability>=0.5. Secondary metrics were IoU@0.5, precision@0.5, recall@0.5, soft Dice, Brier score, average precision, predicted positive volume and target-to-predicted-volume ratio [10,11,15]. Target-volume-matched top-k Dice and IoU selected the k highest probabilities where k equalled target volume. They were labelled ORACLE_ASSISTED_RETROSPECTIVE_LOCALIZATION because k depends on the target. Empty-set and failure handling followed the frozen evaluation and failure policies; all case-method status rows remained in the denominator.

### Statistical analysis

The patient was the statistical unit. Each cohort's confirmatory family contained exactly two comparisons on Dice@0.5: Full PCC versus Fixed and no-smoothing versus Full PCC. Paired two-sided scipy.stats.wilcoxon used zero_method='wilcox', alternative='two-sided' and the library default method='auto'; results are therefore reported as P values, not claimed to be exact. Holm adjustment covered exactly two hypotheses at alpha=0.05 [12]. Reports included n, paired mean and median differences, wins/ties/losses, P values, Holm-adjusted P, Cohen dz, rank-biserial effect size and percentile 95% intervals from 10,000 paired patient bootstrap resamples [13]. Locked seeds were 20260803 internally and 20260810 externally. Secondary metrics used descriptive patient bootstrap intervals. No EIA pairwise P values or between-cohort inferential tests were added.

### Protocol isolation, ethics and AI assistance

Protocol locks, manifests, checkpoint hashes, P0 hashes, first-outcome-access records, code hashes and frozen result releases were retained. RHUH Stage A mounted no recurrence voxel arrays; Stage B began only after 39/39 P0 maps were frozen. Manuscript V2.1 read CSV and report authorities and official descriptive metadata only. It did not execute a model or scientific method.

The MU source study reports University of Missouri IRB approval (IRB #2096253 MU) and waiver of informed consent for retrospective de-identified data sharing [2]. The RHUH source study reports written consent and approval by the Río Hortega Institutional Review Board and CEIm of the West Valladolid Health Area (Ref. 22PI-208) [3]. [AUTHOR CONFIRMATION REQUIRED: present-institution secondary-use determination.]

OpenAI Codex assisted author-supervised deterministic document assembly, coding, drafting/editing and consistency checks. It was not an author and did not alter protocols or scientific results. [AUTHOR FINAL VERIFICATION REQUIRED: authors must verify all evidence, code, numbers, citations and text and retain responsibility.]

## Data availability

MU-Glioma-Post is available from The Cancer Imaging Archive (TCIA) under the source collection's conditions [2]. RHUH-GBM is available from TCIA under DOI 10.7937/4545-c905 and applicable access terms [3]. Derived numeric tables, protocol summaries and figure source data will be deposited at [PROCESSED_DATA_REPOSITORY_DOI_REQUIRED]. Source MRI, segmentations and large P0 arrays are not redistributed here.

## Code availability

Custom code, configs, hashes and deterministic manuscript scripts will be archived at [CODE_REPOSITORY_URL_REQUIRED] with an immutable release tag. Reviewer access will be supplied if public release is unavailable at initial submission.

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

16. Cepeda, S. et al. Predicting regions of local recurrence in glioblastomas using voxel-based radiomic features of multiparametric postoperative MRI. Cancers (Basel) 15, 1894 (2023). https://doi.org/10.3390/cancers15061894

## Acknowledgements

[ACKNOWLEDGEMENTS_REQUIRED]

## Author contributions

[AUTHOR_CONTRIBUTIONS_REQUIRED]

## Funding

[FUNDING_INFORMATION_REQUIRED]

## Competing interests

[COMPETING_INTERESTS_DECLARATION_REQUIRED]

## Figure legends

**Figure 1.** Study design and future-access boundary. P0 used current T1c plus current segmentation and was future-blind with respect to the evaluated case's future information. Training-patient future-added labels were ordinary supervision and did not create evaluated-case leakage. PCC began only after P0 freeze and target access.

**Figure 2.** Independent internal prelocked comparisons. Patient-level Dice@0.5 for Fixed, canonical Full PCC and prelocked no-smoothing in 113 patients. Displayed comparisons correspond to the confirmatory family; descriptive target-access controls appear in Table 3.

**Figure 3.** Canonical Full PCC trajectory. Cohort means across the fixed P1–P10 sequence. P10 was retained for every patient; no best-round selection was performed.

**Figure 4.** RHUH external prelocked comparisons. Patient-level Dice@0.5 in 39 patients. Fixed is the future-blind P0 estimate; corrected maps are retrospective target-conditioned outputs. Descriptive target-access controls appear in Table 3.

**Figure 5.** Development-only oracle-assisted target-volume-matched localization. The metric is target-volume-matched top-k Dice, requires target information, is not the fixed-threshold confirmatory endpoint and is not a deployment metric.

## Tables

**Table 1. Cohort characteristics and analysis flow.** Values are median (IQR) or counts. Source sex terminology differed and no between-cohort inference was performed.

| Characteristic | Development 40 | Independent internal 113 | RHUH external 39 |
| --- | --- | --- | --- |
| Source patients / pre-outcome excluded / analysed | 40 / 0 / 40 | 115 / 2 / 113 | 40 / 1 / 39 |
| Age, years, median (IQR) | 57.5 (53.0–65.0); n=40 | 60.0 (43.0–69.0); n=113 | 64.0 (55.0–69.5); n=39 |
| Sex, female / male | 17 / 23 | 47 / 66 | 12 / 27 |
| Current-to-future interval, days, median (IQR) | 78.0 (64.0–108.0); n=39 | 68.0 (39.5–103.0); n=111 | Not consistently available in linked source metadata |
| Diagnosis / grade | GBM / grade 4: 40 | GBM 74; astrocytoma 23; diffuse glioma 9; oligodendroglioma 4; pilocytic astrocytoma 2; glioma with GBM features 1 | Glioblastoma / grade 4: 39 |
| IDH status | Not consistently available | Not consistently available | wt 35; mut 4 |
| Extent of resection | Not consistently available | Not consistently available | GTR 26; NTR 13 |
| Previous treatment | Not consistently available | Not consistently available | no 37; surgery + QT/RT 2 |

**Table 2. Prelocked confirmatory comparisons.** Paired two-sided Wilcoxon tests with Holm adjustment over exactly two hypotheses per cohort.

| Cohort | Comparison | n | Mean difference | Median difference | Wins / ties / losses | 95% bootstrap CI | Two-sided Wilcoxon P | Holm P | Cohen dz | Rank-biserial |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Independent internal | Full PCC vs Fixed | 113 | 0.205 | 0.212 | 113 / 0 / 0 | 0.191 to 0.218 | 2.803e-20 | 5.606e-20 | 2.746 | 1.000 |
| Independent internal | No-smoothing PCC vs Full PCC | 113 | 0.193 | 0.189 | 113 / 0 / 0 | 0.174 to 0.213 | 2.803e-20 | 5.606e-20 | 1.797 | 1.000 |
| RHUH external | Full PCC vs Fixed | 39 | 0.176 | 0.185 | 39 / 0 / 0 | 0.151 to 0.199 | 3.638e-12 | 7.276e-12 | 2.236 | 1.000 |
| RHUH external | No-smoothing PCC vs Full PCC | 39 | 0.086 | 0.088 | 38 / 0 / 1 | 0.072 to 0.101 | 7.276e-12 | 7.276e-12 | 1.807 | 0.997 |

**Table 3. Descriptive performance of retrospective target-access comparators.** Target-access methods receive target-derived information in different representations and are not strictly information-equivalent. Pairwise EIA inference was not prelocked and was not run.

| Method | Target-derived information access | Iterative | Direct target blending | Internal Dice@0.5 | RHUH Dice@0.5 | Interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| Fixed | No | No | No | 0.239 | 0.190 | Frozen future-blind P0 |
| Naive | No | No | No | 0.239 | 0.190 | Target-free logit sharpening |
| EIA-linear | Yes | No | No | 0.296 | 0.246 | One-step target-access correction |
| EIA-blend-0.90 | Yes | No | Yes | 0.259 | 0.206 | Direct 10% target-signal blend |
| EIA-blend-0.75 | Yes | No | Yes | 0.317 | 0.248 | Direct 25% target-signal blend |
| Full PCC | Yes | Yes | No | 0.444 | 0.365 | Canonical target-conditioned PCC |
| No-smoothing PCC | Yes | Yes | No | 0.637 | 0.451 | Prelocked candidate; no discrepancy smoothing |
