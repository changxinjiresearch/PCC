# Stage B release test execution

Command: `PYTHONPATH=. /tmp/pcc113_stage_b_stats_venv/bin/pytest -q tests`

Result: `166 passed, 43 skipped, 0 failed, 0 errors, 2 warnings, 27 subtests passed`.

The 42 model/formal skips are the repository's existing PyTorch-dependent optional tests; one dataset-identity test is skipped because its canonical locked fixture is unavailable. No scientific model or Stage B runner was re-executed locally.
