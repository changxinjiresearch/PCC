import pandas as pd


def test_repeat_aggregation_unit_is_case_condition_method():
    frame=pd.DataFrame({"case_id":["a","a","b","b"],"condition":["x"]*4,"method":["m"]*4,"value":[1,3,2,4]})
    aggregated=frame.groupby(["case_id","condition","method"],as_index=False).value.mean()
    assert len(aggregated)==2 and dict(zip(aggregated.case_id,aggregated.value))=={"a":2,"b":3}
