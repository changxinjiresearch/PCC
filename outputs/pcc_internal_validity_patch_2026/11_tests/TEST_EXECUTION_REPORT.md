# Test execution report

## Authoritative current run

- Formal command: `/tmp/pcc_internal_test_env/bin/python -m pytest -q tests`
- Raw output: `saved_pytest_outputs/FULL_PYTEST_CURRENT_FINAL.txt`
- Execution metadata: `saved_pytest_outputs/FULL_PYTEST_CURRENT_FINAL.meta.txt`
- Result: **208 passed, 1 skipped, 0 failed, 0 errors, 27 subtests passed; exit code 0**.
- The two warnings are the expected out-of-range Naive regression overflow warnings recorded in the raw output.

- Focused command: `/tmp/pcc_internal_test_env/bin/python -m pytest -q tests/test_validity_patch.py tests/test_validity_patch_statistics.py tests/test_validity_no_pseudoreplication.py tests/test_internal_manifest.py tests/test_internal_statistics.py`
- Raw output: `saved_pytest_outputs/FOCUSED_VALIDITY_PATCH_PYTEST_CURRENT_FINAL.txt`
- Execution metadata: `saved_pytest_outputs/FOCUSED_VALIDITY_PATCH_PYTEST_CURRENT_FINAL.meta.txt`
- Result: **15 passed, 0 skipped, 0 failed, 0 errors; exit code 0**.

- Compile command: `/tmp/pcc_internal_test_env/bin/python -m compileall -q src experiments/finalize_validity_map_analyses.py experiments/finalize_internal_validity_patch.py experiments/build_internal_validity_patch_package.py experiments/run_internal_validity_patch.py experiments/run_internal_completion_2026.py`; exit code 0. Raw output and metadata are `COMPILEALL_CURRENT_FINAL.txt` and `.meta.txt`.
- `git diff --check`; exit code 0. Raw output and metadata are `GIT_DIFF_CHECK_CURRENT_FINAL.txt` and `.meta.txt`.

## Historical-count reconciliation

The prior report's 207 was from an earlier formal test inventory. The previously archived `FULL_PYTEST_FINAL_PACKAGE.txt` and `FULL_PYTEST_ISOLATED_AFTER_FIX.txt` record older package/environment runs of 198 and 193 passed, respectively. The earlier 9/10 focused counts were incomplete historical summaries and are not used as evidence. This release uses only the current complete raw outputs above: 208 formal passed and 15 focused passed.

The repository-root collection form remains intentionally unused because archival copies can create duplicate test-module names.
