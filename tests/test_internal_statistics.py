import numpy as np
import pandas as pd
import tempfile
from pathlib import Path

from src.analysis.internal_statistics import aggregate_repeats, holm_adjust, paired_family
from experiments.finalize_internal_completion_2026 import read_numeric


def test_holm_is_monotone_in_rank_and_bounded():
    adjusted = holm_adjust([0.04, 0.01, 0.03])
    assert all(0 <= value <= 1 for value in adjusted)
    assert adjusted[1] <= adjusted[2] <= adjusted[0]


def test_repeat_aggregation_preserves_case_as_unit():
    frame = pd.DataFrame({"case_id":["a","a","b","b"], "condition":["FP"]*4, "method":["PCC"]*4, "repeat":[1,2,1,2], "dice":[0.,1.,.2,.4], "iou":[0.,.5,.1,.3]})
    result = aggregate_repeats(frame)
    assert len(result) == 2
    assert result.loc[result.case_id == "a", "dice"].item() == .5


def test_paired_statistics_never_treat_repeats_as_cases():
    frame = pd.DataFrame({"case_id":["a","a","b","b"], "condition":["FULL","ABL","FULL","ABL"], "dice":[.5,.4,.6,.5], "iou":[.3,.2,.4,.3]})
    result = paired_family(frame, condition_column="condition", reference="FULL", comparisons=["ABL"], family="mechanism")
    assert set(result.N) == {2}
    assert set(result.wins) == {0}
    assert set(result.losses) == {2}


def test_reporting_numeric_conversion_preserves_text_columns():
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "rows.csv"
        path.write_text("case_id,dice,note\na,0.5,locked\n")
        frame = read_numeric(path)
    assert frame.dice.dtype.kind == "f"
    assert frame.note.iloc[0] == "locked"
