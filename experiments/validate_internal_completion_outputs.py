"""Validate the complete PCC_INTERNAL_COMPLETION_2026 artifact contract."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

CONFIG_SHA256="7a36fe0689abae5552395da84b69260e081764c13bd540a2454b2e74494697c4"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite_metrics(frame: pd.DataFrame) -> None:
    for column in ("dice","iou"):
        values=pd.to_numeric(frame[column],errors="raise").to_numpy(float)
        assert np.isfinite(values).all() and ((0<=values)&(values<=1)).all(), column


def validate(root: Path, config: Path) -> dict[str, object]:
    assert sha256(config)==CONFIG_SHA256
    mechanism=pd.read_csv(root/"01_mechanism_ablation/MECHANISM_CASE_METRICS.csv"); assert len(mechanism)==480 and mechanism.case_id.nunique()==40; finite_metrics(mechanism)
    identity=pd.read_csv(root/"09_dataset_identity/LOCKED_CASE_FILE_MAP.csv"); assert len(identity)==120 and identity.case_id.nunique()==40 and identity.sha256.str.fullmatch(r"[0-9a-f]{64}").all()
    donors=pd.read_csv(root/"02_shuffled_target/SHUFFLED_TARGET_DONOR_MAP.csv"); shuffled=pd.read_csv(root/"02_shuffled_target/SHUFFLED_TARGET_CASE_METRICS.csv")
    assert len(donors)==40 and donors.recipient_case_id.nunique()==40 and donors.donor_case_id.nunique()==40
    assert (donors.recipient_case_id!=donors.donor_case_id).all() and (donors.recipient_patient_id!=donors.donor_patient_id).all()
    assert len(shuffled)==40 and shuffled.case_id.nunique()==40; finite_metrics(shuffled)
    imperfect=pd.read_csv(root/"03_imperfect_guidance/IMPERFECT_GUIDANCE_REPEAT_METRICS.csv"); assert len(imperfect)==5160 and imperfect.case_id.nunique()==40; finite_metrics(imperfect)
    assert not imperfect.duplicated(["case_id","condition","method","repeat"]).any()
    expected={"PARTIAL_50":1,"PARTIAL_25":1,"FP_25":5,"SHIFT_3":6,"MIXED":30}
    observed=imperfect.groupby(["case_id","condition","method"])["repeat"].nunique()
    assert all(value==expected[condition] for (_,condition,_),value in observed.items())
    targets=pd.read_csv(root/"04_target_construction/TARGET_CONSTRUCTION_CASE_METRICS.csv"); assert len(targets)==320 and targets.case_id.nunique()==40; finite_metrics(targets)
    gate=json.loads((root/"05_difference_map_control/DIFFERENCE_MAP_GATE_STATUS.json").read_text()); difference_rows=0
    if gate["status"]=="PASS":
        difference=pd.read_csv(root/"05_difference_map_control/DIFFERENCE_MAP_CASE_METRICS.csv"); assert len(difference)==40 and difference.case_id.nunique()==40; finite_metrics(difference); difference_rows=40
    for path in root.glob("0*/FAILED_CASES.csv"):
        assert len(pd.read_csv(path))==0,path
    payload={"status":"PASS","mechanism_rows":480,"identity_rows":120,"shuffled_rows":40,"imperfect_repeat_rows":5160,"target_rows":320,"difference_rows":difference_rows,"unique_cases":40,"case_level_finite":True,"predictor_retrained":False,"p0_regenerated":False}
    destination=root/"14_reproducibility/SCIENTIFIC_CONTRACT_VALIDATION.json"; destination.parent.mkdir(parents=True,exist_ok=True); destination.write_text(json.dumps(payload,indent=2)+"\n")
    return payload


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--output-root",type=Path,required=True); parser.add_argument("--config",type=Path,required=True); args=parser.parse_args(); print(json.dumps(validate(args.output_root,args.config)))


if __name__=="__main__": main()
