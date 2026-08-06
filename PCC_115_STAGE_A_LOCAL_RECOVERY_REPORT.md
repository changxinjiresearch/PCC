# PCC 115 Stage A local recovery report

Date: 2026-08-06

## Authority and restrictions

Remote kernel `jeechangxin/pcc-115-holdout-stage-a-p0-freeze-2026` was confirmed `COMPLETE`. The downloaded metadata reports `PASS`, `expected_patients=115`, `generated_p0=115`, `target_constructed=false`, `performance_computed=false`, `stage_b_executed=false`, and `lumiere_started=false`.

No Kaggle kernel was rerun. No P0 was regenerated. Stage B and LUMIERE were not executed.

## Verified local result

Stable local result: `/home/changxinjiresearch/pcc115_stage_a_complete_download_v3`

- P0 files: 115
- completion markers: 115
- manifest records: 115
- SHA-256 records: 115
- unique cases: 115
- missing: 0
- duplicate: 0
- zero-byte: 0
- unreadable: 0
- size mismatch: 0
- SHA-256 mismatch: 0
- shape mismatch: 0
- dtype mismatch: 0
- non-finite: 0
- out-of-range: 0
- future access violations: 0
- target constructed: false
- performance computed: false
- Stage B executed: false
- LUMIERE: false

## Tests and archives

The repository Stage A static suite produced 29 passing tests and one known filename false positive: `test_21_no_stage_b_outputs` treats the required file `PCC_115_STAGE_A_READINESS_FOR_STAGE_B.md` as a Stage B output. The first unfiltered run is retained in the generated test output context; the 29 remaining tests pass with exit code 0. No Stage B data or execution was found.

Metadata/audit archive:

- `PCC_115_STAGE_A_P0_FREEZE_2026.zip`
- SHA-256: `46252435dc06f6ce8e45c98799b7582c0823199cbca81fcd7319a1847d1e66de`

Full local v3 ZIP:

- `/home/changxinjiresearch/pcc115_stage_a_complete_download_v3.zip`
- SHA-256: `e71c900e4375db0d03bdb59019c0335c024d7f35f2999847ed43f9458f7cd6a0`
- ZIP integrity: PASS; 368 entries

## Cleanup

The previous incomplete `/home/changxinjiresearch/pcc115_stage_a_complete_download` directory was removed only after v3 validation and cleanup audit generation. The requested `_v2` directory was absent and was not touched. See `PCC_115_STAGE_A_V3_CLEANUP_AUDIT.txt`.

Final Stage A status: PASS. Stop here; no Stage B or LUMIERE work is authorized.
