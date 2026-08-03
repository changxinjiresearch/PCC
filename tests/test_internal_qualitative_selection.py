import numpy as np
import pandas as pd

from experiments.generate_internal_qualitative_panels import guidance_for, selections


def test_qualitative_case_selection_is_ranked_not_manual():
    frame=pd.DataFrame({"case_id":["b","a","c"],"pcc_gain":[.2,.1,.3],"target_voxels":[2,1,3],"target_components":[1,3,2],"smallest_imperfect_retention":[.8,.9,.7]})
    chosen=dict(selections(frame))
    assert chosen["minimum_layer2_gain"]=="a"
    assert chosen["maximum_layer2_gain"]=="c"
    assert chosen["smallest_target"]=="a"
    assert chosen["most_fragmented_target"]=="a"
    assert chosen["worst_imperfect_retention"]=="c"


def test_guidance_repeat_parser_is_deterministic():
    clean=np.zeros((20,20,20),dtype=bool); clean[8:12,8:12,8:12]=True
    a=guidance_for("MIXED","seed_20260803_+x",clean,(1.,1.,1.),"case")
    b=guidance_for("MIXED","seed_20260803_+x",clean,(1.,1.,1.),"case")
    np.testing.assert_array_equal(a,b)
