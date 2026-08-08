# PCC 113 Stage B launch lock

**Launch gate: PASS — pre-outcome boundary**

This lock was generated after exact SHA-256 verification of the locked 115-patient protocol archive and the accepted V2 113-patient amendment archive. It validates the 113-patient identity, the two deterministic exclusions, the unchanged original shard assignment for all retained patients, the 113 frozen P0 hashes, and the locked method/evaluation/statistics source hashes.

- Original locked holdout: 115
- Post-lock identity exclusions: PatientID_0113, PatientID_0132
- Confirmatory denominator: 113
- Performance seen before amendment: false
- P0 regenerated: false
- Shards: 0=29, 1=27, 2=29, 3=28
- Future mask arrays read before this lock: false
- LUMIERE started: false

The only denominator override is 115 → 113. All method equations, parameters, target rule, fixed threshold 0.5, P10 final Full PCC state, failure semantics, confirmatory tests, Holm family, bootstrap count and seed remain inherited from the locked authority.

This file is the final protocol boundary. Stage B performance execution is authorized only after the Git commit containing this lock has been pushed successfully.
