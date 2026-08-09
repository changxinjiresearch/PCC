
# Locked RHUH external geometry policy

All primary external pairs must have identical effective physical voxel grids between current T1ce/current segmentation, recurrence T1ce/recurrence segmentation, and current/recurrence target grids. Identity requires matching shape, selected NIfTI affine, spacing, orientation, voxel-center ranges, and world bounds. qform/sform metadata differences remain recorded but cannot override a matching selected effective grid.

Header verification and lossless orientation representation checks are allowed. Registration, resampling, interpolation, case-specific affine repair, forced header rewriting, and outcome-driven correction are forbidden. The locked cohort passes effective geometry in 39/39 cases; RHUH-0008 was excluded before outcome access.
