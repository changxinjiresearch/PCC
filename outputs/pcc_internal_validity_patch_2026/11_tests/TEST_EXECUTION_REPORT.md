# Test execution report

- Focused validity-patch tests: 9 passed.
- Formal repository suite (`pytest -q tests`): 207 passed, 1 skipped, 27 subtests passed; two expected overflow warnings in the out-of-range Naive regression test.
- `compileall -q src experiments tests`: passed.
- `git diff --check`: passed at the recorded pre-finalization checkpoint and repeated after packaging.

An unscoped repository-root `pytest` attempt stopped during collection because archival copies under `outputs/final_report/` and `kaggle-one-case-output/` have the same module basenames as authoritative tests. No test body failed in that attempt. The authoritative project test directory was therefore executed explicitly. The single skipped test remains dependency/environment documented by pytest output.
