# Kaggle Execution Record

| Job | Version | Status | Purpose |
|---|---:|---|---|
| `jeechangxin/pcc-internal-completion-2026-smoke` | 2 | COMPLETE | One-case contract smoke test |
| `jeechangxin/pcc-internal-completion-2026-core` | 1 | COMPLETE | Mechanism, shuffled target, target construction, identity |
| `jeechangxin/pcc-internal-completion-2026-imperfect-shard-0` | 1 | COMPLETE | Imperfect-guidance cases, shard 0/2 |
| `jeechangxin/pcc-internal-completion-2026-imperfect-shard-1` | 1 | COMPLETE | Imperfect-guidance cases, shard 1/2 |
| `jeechangxin/pcc-internal-completion-2026-difference-control` | 1 | COMPLETE | Spatial gate and difference-map control |
| `jeechangxin/pcc-internal-completion-2026-layer1-panels` | 3 | COMPLETE | Inference-only Layer 1 rank-selected panels |
| `jeechangxin/pcc-internal-completion-2026-layer2-panels` | 3 | COMPLETE | Inference-only Layer 2 rank-selected panels |

The two imperfect-guidance shards produced 2,580 rows and 20 disjoint cases each. Their merged table has 5,160 rows, 40 cases, no duplicate `(case_id, condition, method, repeat)` keys, and no failed cases. Neither shard retrained the predictor or regenerated P0.

Layer 2 panel versions 1 and 2 were reporting-only engineering failures (missing difference-control input, then unresolved historical Kaggle path prefix). Version 3 attached the locked dataset and resolved paths in a temporary manifest alias; it did not modify the frozen manifest or scientific calculations.
