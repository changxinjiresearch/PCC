# Cohort identity freeze before protocol supplement

The five cohort identity files listed in `PRE_SUPPLEMENT_COHORT_FILE_HASHES.csv` are frozen byte-for-byte before this supplement. The supplement must not change patient identity, case ID, current/future timepoint, pair rank, or eligibility.

Frozen facts: 203 source patients; 155 eligible patient-level pairs; 40 development patients; 115 holdout patients; zero overlap; exactly one pair per holdout patient. The authoritative pair rule remains the earliest two usable timepoints after deterministic patient/timepoint sorting.
