# Pair Selection Rules

The executed discovery implementation iterates patient directories in lexical order. Within each patient it sorts `Timepoint_N` directories numerically and retains a timepoint only when exactly one `*_brain_t1c.nii` and exactly one `*_tumorMask.nii` exist. For a patient with at least two usable timepoints, it selects the first two usable timepoints and forms one pair. It stops immediately after 40 eligible patients.

The implementation does not explicitly require consecutive numeric timepoint numbers, despite an older docstring saying “consecutive.” Therefore the precise executed rule is **earliest two usable timepoints**, not necessarily `N` and `N+1`. It neither searches for the best pair nor examines model performance. The manifest writer refuses to overwrite an existing lock.

The dataset scan found 155 eligible patients. The locked cohort is exactly the first 40 under this deterministic ordering. The remaining 115 eligible patients were excluded solely because the prespecified limit had been reached; 48 patients had fewer than two usable timepoints.
