# Known reproducibility limitations

- **GAP-001:** Phase 0 tree manifest contains a self-hash entry; self-hashes are intrinsically non-verifiable. External entries match.
- **GAP-002:** Only a test dependency lock is present; the exact complete historical Kaggle runtime is not consolidated into one environment lock.
- **GAP-003:** Frozen checkpoint binaries are not staged and require availability/licence verification.
- **GAP-004:** Frozen Internal/RHUH P0 arrays are referenced by remote provenance but are not locally staged.
- **GAP-005:** Full PCC P10 and No-smoothing P10 maps were intentionally not retained, blocking Phase 1 qualitative rendering without prohibited re-execution.
- **GAP-006:** MU per-case registration transforms/interpolation details and landmark accuracy are not available in frozen project metadata.
