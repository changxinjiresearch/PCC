# Package validation policy

The package is independently verified after ZIP creation. `PACKAGE_FILE_MANIFEST.csv` and this report are marked EXCLUDED_SELF_REFERENCE because neither can stably contain its own final hash. All other package files are controlled by path, size and SHA-256. The external post-package report records ZIP integrity, actual path equality and controlled-file mismatches.
