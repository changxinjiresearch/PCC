# Manuscript-ready registration text draft

This draft is not integrated into frozen V2.1.1.

MU-Glioma-Post images were distributed after source preprocessing that included 1-mm isotropic resampling and rigid registration to the SRI24 atlas. In the PCC cohorts, existing geometry records confirmed matching shape, spacing, orientation and affine flags for all 40 development and 113 independent-internal pairs. RHUH-GBM source preprocessing included atlas registration of T1ce and within-timepoint modality coregistration; all 39 locked external pairs had matching effective physical grids by shape, spacing, orientation, selected affine, voxel-center range and world bounds. The PCC pipeline itself performed no registration, resampling, interpolation or header repair.

These checks establish physical-grid compatibility, not perfect longitudinal anatomical correspondence. We did not verify dedicated pairwise patient-specific current-to-future registration, transform accuracy, landmark error or deformable correspondence. Accordingly, the one-sided future-added segmentation target may reflect both biological/segmentation change and residual spatial displacement. This limitation should be considered when interpreting target-conditioned correction.
