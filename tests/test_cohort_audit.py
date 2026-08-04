from pathlib import Path

from experiments.audit_cohort_selection import tp_number


def test_timepoint_sort_is_numeric_and_missing_is_explicit():
    assert tp_number(Path("Timepoint_10"))==10
    assert tp_number(Path("Timepoint_2"))==2
    assert tp_number(Path("other"))==-1
