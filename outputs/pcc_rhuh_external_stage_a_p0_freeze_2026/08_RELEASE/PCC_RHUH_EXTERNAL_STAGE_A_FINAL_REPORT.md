# PCC RHUH External Stage A P0 freeze final report

The locked 39-patient external cohort was processed using only early-postoperative T1ce, the locked binary current mask (`RHUH segmentation > 0`), and the five frozen internal checkpoints. All 39 float32 P0 maps are finite, in range, shape-valid, and matched their manifest and SHA-256 table after an independent local download.

- Current-only dataset: `jeechangxin/pcc-rhuh-stage-a-current-only-2026`, version `2`
- Frozen checkpoint source: `jeechangxin/pcc-leakage-free-rerun-2026`, version `8`
- Stable P0 source: `jeechangxin/pcc-rhuh-external-stage-a-p0-freeze-2026`, version `1`
- P0: 39/39
- Completion markers: 39/39
- Missing/hash/dtype/finite/range/shape failures: 0
- Failed patients: 0
- Recurrence segmentation voxel access: 0
- Recurrence T1ce voxel access: 0
- Target constructed: false
- Performance computed: false
- External Stage B executed: false
- `EXTERNAL_STAGE_A_P0_FREEZE_GATE=PASS`
