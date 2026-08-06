# Stage A Cohort Amendment Decision — Rule B

The current T1c and current mask for PatientID_0113 and PatientID_0132 are identical, but their future tumor-mask file and float32 voxel-array SHA-256 values differ. Geometry is identical.

Decision: `DATA_IDENTITY_OR_LABEL_ASSIGNMENT_ANOMALY`.

- Exclude both PatientID_0113 and PatientID_0132 from the main confirmatory analysis.
- Keep the original 115-person manifest and all 115 frozen P0 files unchanged as audit evidence.
- The amended confirmatory manifest contains 113 patients.
- Stage B must not run until human acceptance; if later authorized, it may read only the amended 113-person manifest.
- No target was constructed, no performance was computed, and no P0 was modified or regenerated.

Status: `DATA_IDENTITY_OR_LABEL_ASSIGNMENT_ANOMALY`
Human acceptance: REQUIRED
