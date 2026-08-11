# Portable Round 3 Validation

The controlled ZIP was extracted into a fresh temporary directory under the project-scoped in-memory workspace. From `/tmp`, the packaged standard-library validator was run with:

`python3 <extracted-package>/scripts/validate_round3_patch.py --root <extracted-package>`

Result: `PASS`.

Validated independently of the repository layout:

- development evaluation-label consistency;
- Supplementary Table S1 schema;
- Supplementary Table S7 exact method/condition coverage and value provenance;
- main and Supplement footer PAGE-field counts;
- visible page-number sequence;
- Figure legend uniqueness and terminal-page orphan guard;
- LibreOffice PDF producer and complete per-page PNG evidence;
- frozen authority hashes from packaged read-only snapshots;
- Table 2 confirmatory and Table 3 comparator SHA-256 identity;
- frozen numeric regression baseline.

`PORTABLE_VALIDATION=PASS`
