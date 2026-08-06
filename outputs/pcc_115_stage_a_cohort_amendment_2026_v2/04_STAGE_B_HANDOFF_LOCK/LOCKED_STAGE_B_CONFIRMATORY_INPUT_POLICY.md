# Locked Stage B Confirmatory Input Policy

Stage B has not executed. If separately authorized, the main confirmatory runner may read only `02_AMENDED_COHORT_LOCK/LOCKED_113_CONFIRMATORY_CASE_MANIFEST.csv` and `03_P0_MAPPING/LOCKED_113_P0_MANIFEST.csv`/`LOCKED_113_P0_SHA256.csv`.

The runner must reject the original 115-person manifest, PatientID_0113, PatientID_0132, any case absent from the locked 113-person manifest, and any regenerated or replacement P0. This package does not create Stage B results.
