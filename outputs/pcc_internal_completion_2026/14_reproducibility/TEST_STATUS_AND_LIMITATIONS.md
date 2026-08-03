# Test status and limitations

The final isolated environment uses Python 3.11 with `include-system-site-packages=false`; exact requested package versions are recorded in `requirements-test-lock.txt`.

After correcting test-only fixtures that used an invalid placeholder case ID and a global import mock that interfered with PyTorch's lazy CUDA check, the repository test directory completed with:

- 193 passed;
- 1 skipped;
- 27 subtests passed;
- 2 expected overflow warnings from the existing Naive out-of-range boundary test.

The skipped test is documented in the saved pytest output. `compileall` and `git diff --check` also pass. A bare repository-root `pytest` is not a valid collection command in this worktree because `outputs/final_report/` and `kaggle-one-case-output/` contain read-only copied test modules with duplicate basenames; the authoritative command is `pytest tests`.
