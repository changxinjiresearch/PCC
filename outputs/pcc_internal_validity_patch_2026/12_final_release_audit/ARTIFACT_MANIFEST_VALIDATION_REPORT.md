# Artifact Manifest Validation Report

- Scope: `INTERNAL_VALIDITY_PATCH_ARTIFACT_MANIFEST.csv` excludes itself, `PCC_INTERNAL_VALIDITY_PATCH_PACKAGE_CONTENTS.txt`, and this validation CSV. The first two are self/mutual-reference indexes; the validation CSV is generated from the manifest and would otherwise create a manifest-validation self-reference. These exclusions are explicit; package contents lists both release-index files with their final hashes.
- Manifest rows: 112.
- Expected scoped files: 112.
- Missing: 0.
- Extra: 0.
- Size/hash mismatches: 0.
- Duplicate paths: 0.
- Result: **PASS**.
