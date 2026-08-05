import pandas as pd

def test_manifest_is_current_only():
 p=pd.read_csv('outputs/pcc_115_holdout_protocol_lock_2026/01_COHORT_LOCK/P0_INFERENCE_MANIFEST.csv')
 bad=[c for c in p.columns if any(x in c.lower() for x in ('future','target','later'))]
 assert not bad, bad
