# Phase 1A longitudinal registration provenance report

## MU-Glioma-Post

Known: the source publication describes FeTS preprocessing with DICOM-to-NIfTI conversion, resampling to 1-mm isotropic resolution and rigid registration to SRI24 using CapTK/Greedy, followed by bias correction and brain extraction. Existing project metadata maps all 40 development cases and all 113 internal cases to 240×240×155 arrays with matching shape, spacing, orientation and affine flags.

Verified: the PCC pipeline required exact array/geometry compatibility and did not register, resample, interpolate or repair any pair. This establishes recorded physical-grid compatibility.

Not verified: dedicated current-to-future patient-specific registration, transform files, landmark error, deformable alignment, or perfect voxelwise anatomical correspondence. Independent atlas normalization of timepoints cannot be equated with dedicated longitudinal registration.

Scientific implication: the one-sided future-added target can contain true biological/segmentation change and residual spatial displacement. Recommended wording is limited to source atlas normalization plus verified grid compatibility.

## RHUH-GBM

Known: the official pipeline describes T1ce registration to the SRI atlas and within-timepoint registration of other modalities. The locked 39-case cohort has 39/39 effective physical-grid identity for current T1ce/current segmentation, recurrence T1ce/recurrence segmentation and across timepoints. RHUH-0008 was excluded before outcome access because physical-grid identity could not be established.

Verified: shape, 1-mm spacing, LPS orientation, selected affine, voxel-center ranges and world bounds. qform/sform-only metadata differences were retained rather than silently rewritten. No project-side registration, resampling or interpolation occurred.

Not verified: registration accuracy or dedicated patient-specific inter-timepoint anatomical registration. Effective grid identity is not proof of perfect anatomical correspondence.

Scientific implication: the target is computationally defined on a shared physical grid, but residual longitudinal anatomical/segmentation displacement remains a limitation.

## LUMIERE

Only historical/source provenance was reviewed. The source provides skull-stripped native unregistered images; segmentation pipelines perform within-timepoint coregistration and provide back-transformed outputs. Cohort eligibility, longitudinal geometry, ontology and future-access controls remain `PENDING_PHASE4_FEASIBILITY`. No new LUMIERE outcome or performance was accessed.

## Unsupported claims

Unsupported claims detected in this Phase 1 report: **0**. Neither equal shape, equal affine nor common atlas space is described as perfect longitudinal anatomical registration.
