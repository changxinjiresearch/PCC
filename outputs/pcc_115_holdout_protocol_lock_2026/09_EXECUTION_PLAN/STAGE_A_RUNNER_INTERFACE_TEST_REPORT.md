# Stage A runner interface test report

The real runner is `experiments/run_115_stage_a_p0.py`. Static tests reject future/target/later fields and unknown future CLI arguments. A mock-only test supplies five synthetic predictors, verifies equal weighting, current-only normalization, atomic `.npy` persistence, SHA-256, access logging and a stage/shard-specific completion marker. Production `execute_stage_a` is not called in this protocol-lock stage.

Result: PASS. Verified by saved pytest output; relevant checks protocol tests 11–17 and 36 pass.
