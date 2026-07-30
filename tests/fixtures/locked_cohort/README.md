# Canonical locked cohort fixture

Status: **Placeholder — authoritative files unavailable locally.**

No case identifiers are included here because the canonical locked cohort must
not be reconstructed or guessed.

To enable the locked-cohort regression test, place these approved files in this
directory:

- `direct_target_case_metrics.csv`: the authoritative Model A metrics CSV used
  by notebook cell 110. It must contain the `case_id` column.
- `locked_case_ids.txt`: the verified expected case IDs, one per line, in the
  exact lexically sorted and silently deduplicated notebook order.

The regression test remains explicitly skipped until both files are present.
