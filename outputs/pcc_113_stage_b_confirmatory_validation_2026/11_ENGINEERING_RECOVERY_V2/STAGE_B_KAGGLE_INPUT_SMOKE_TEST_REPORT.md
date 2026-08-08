# Stage B Kaggle input smoke test — BLOCKED

- kernel: jeechangxin/pcc-113-stage-b-input-smoke-v2-2026
- submitted version: 1
- status: ERROR
- scientific data read: false
- future masks read: false
- target constructed: false
- performance computed: false
- Stage B methods executed: false
- LUMIERE started: false

The private dataset was accepted and its file listing shows the bundle files under `manifest/`, `policy/`, and `authority/`. Kaggle expanded the uploaded ZIP during dataset ingestion, so the smoke script's exact search for `PCC_113_STAGE_B_INPUT_BUNDLE_2026.zip` found no file and stopped before reading any CSV. No formal Stage B shard was submitted.

Per the recovery authorization, execution stops after this smoke-test failure. A further smoke submission requires a new explicit decision.
