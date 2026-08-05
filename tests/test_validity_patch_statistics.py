import numpy as np
import pandas as pd

from experiments.build_internal_validity_patch_package import tagged
from src.analysis.validity_patch import apply_holm_by_family, one_sample_statistics


def test_case_level_one_sample_counts_signs_and_is_deterministic():
    values=np.array([1.,2.,-1.,0.]); a=one_sample_statistics(values,"locked"); b=one_sample_statistics(values,"locked")
    assert a==b and a["N"]==4 and (a["positive"],a["zero"],a["negative"])==(2,1,1)


def test_holm_is_within_family_not_global():
    frame=pd.DataFrame({"family":["a","a","b"],"wilcoxon_p_two_sided":[.01,.04,.03]})
    result=apply_holm_by_family(frame)
    assert np.allclose(result.holm_adjusted_p,[.02,.04,.03])


def test_package_tagging_preserves_existing_source_file(tmp_path):
    path = tmp_path / "claim.csv"
    pd.DataFrame([{"claim": "x", "source_file": "frozen.csv"}]).to_csv(path, index=False)
    result = tagged(path, "audit")
    assert result.loc[0, "source_file"] == "frozen.csv"
    assert result.loc[0, "audit_source_file"] == str(path)
