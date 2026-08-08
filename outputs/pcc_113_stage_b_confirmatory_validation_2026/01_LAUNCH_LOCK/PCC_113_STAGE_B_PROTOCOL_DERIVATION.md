# PCC 113 Stage B protocol derivation

This is a mechanical cohort amendment of the locked 115-patient protocol. The only scientific denominator override is 115 -> 113 after the two pre-outcome identity exclusions. Methods, parameters, endpoints, threshold, failure semantics, and statistical plan remain inherited from the verified authority archives.

- original_locked_holdout: 115
- post_lock_identity_exclusions: 2
- confirmatory_denominator: 113
- excluded_ids: PatientID_0113, PatientID_0132
- performance_seen_before_amendment: false
- P0_regenerated: false
- LUMIERE: false

The Stage B target is `(future_mask > 0.5) AND NOT (current_mask > 0.5)`, without registration or resampling. Fixed threshold is 0.5; Full PCC uses P10; No-smoothing differs only by bypassing the locked Gaussian smoothing of each round discrepancy.
