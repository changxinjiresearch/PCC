# Two-stage data access

Stage A may read current T1c/current mask, current-only preprocessing and frozen checkpoints, and produces no output in this protocol-lock stage. Stage B may read future mask only after all P0 maps are generated, persisted and hash-frozen. This package performs neither stage.
