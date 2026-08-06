# 0113/0132 Future Identity Audit

Only the eight locked-pair current/future NIfTI files for PatientID_0113 and PatientID_0132 were inspected. No target was constructed and no performance was computed.

| Component | File SHA equal | Array SHA equal | Geometry equal |
|---|---:|---:|---:|
| current_t1c | True | True | True |
| current_mask | True | True | True |
| future_t1c | True | True | True |
| future_mask | False | False | True |

判定: B — `DATA_IDENTITY_OR_LABEL_ASSIGNMENT_ANOMALY`; exclude both 0113 and 0132 from the amended confirmatory manifest; amended primary confirmatory sample size = 113; stop for human acceptance.
