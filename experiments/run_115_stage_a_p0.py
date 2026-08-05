#!/usr/bin/env python3
"""Future-blind Stage A P0 runner (defined but not executed by protocol lock)."""
from __future__ import annotations

import argparse, csv, hashlib, json, os, tempfile
from pathlib import Path
from typing import Callable, Iterable

import numpy as np

from src.preprocessing.current_only_preprocessing import prepare_current_only_inputs

FORBIDDEN_TOKENS = ("future", "target", "later")
ENSEMBLE_WEIGHTS = (0.2, 0.2, 0.2, 0.2, 0.2)


def sha256(path: Path) -> str:
    value=hashlib.sha256(); value.update(path.read_bytes()); return value.hexdigest()


def validate_current_only_record(record: dict[str, str]) -> None:
    forbidden=[key for key in record if any(token in key.lower() for token in FORBIDDEN_TOKENS)]
    if forbidden: raise ValueError(f"Stage A record contains forbidden fields: {forbidden}")
    required={"patient_id","case_id","current_t1c_path","current_mask_path","output_p0_path","stage_a_shard"}
    missing=required-set(record)
    if missing: raise ValueError(f"Stage A record missing fields: {sorted(missing)}")


def equal_weight_average(predictions: Iterable[np.ndarray]) -> np.ndarray:
    values=[np.asarray(x,dtype=np.float32) for x in predictions]
    if len(values)!=5 or any(x.shape!=values[0].shape for x in values): raise ValueError("Exactly five shape-identical predictions are required")
    return np.sum(np.stack(values),axis=0,dtype=np.float32)/np.float32(5.0)


def atomic_save_p0(path: Path, probability: np.ndarray) -> str:
    path.parent.mkdir(parents=True,exist_ok=True)
    if probability.dtype!=np.float32 or not np.isfinite(probability).all(): raise ValueError("P0 must be finite float32")
    with tempfile.NamedTemporaryFile(dir=path.parent,prefix=path.name+'.',suffix='.tmp',delete=False) as handle:
        temporary=Path(handle.name); np.save(handle,probability,allow_pickle=False); handle.flush(); os.fsync(handle.fileno())
    temporary.replace(path)
    return sha256(path)


def run_case_with_predictors(record: dict[str,str], current_t1c: np.ndarray, current_mask: np.ndarray,
                             predictors: list[Callable[[np.ndarray],np.ndarray]], output_root: Path) -> dict[str,object]:
    """Synthetic/mock-testable case boundary; production callers supply five frozen models."""
    validate_current_only_record(record)
    if len(predictors)!=5: raise ValueError("Exactly five frozen fold predictors are required")
    prepared=prepare_current_only_inputs(current_t1c,current_mask)
    predictions=[predictor(prepared.model_input_zchw) for predictor in predictors]
    p0=equal_weight_average(predictions).astype(np.float32)
    output=output_root/record["output_p0_path"]
    digest=atomic_save_p0(output,p0)
    access_log=output.with_suffix('.access.json')
    access={"case_id":record["case_id"],"stage":"stage_a","stage_a_shard":record["stage_a_shard"],
            "files_read":[record["current_t1c_path"],record["current_mask_path"]],"forbidden_file_access":False,
            "checkpoint_count":5,"ensemble_weights":list(ENSEMBLE_WEIGHTS),"p0_sha256":digest}
    access_log.write_text(json.dumps(access,indent=2)+"\n")
    marker=output.parent/f"STAGE_A_SHARD_{record['stage_a_shard']}_{record['case_id']}_COMPLETE.json"
    marker.write_text(json.dumps({"status":"COMPLETE","stage":"stage_a","shard":record["stage_a_shard"],"case_id":record["case_id"],"p0_sha256":digest})+"\n")
    return access


def parser() -> argparse.ArgumentParser:
    result=argparse.ArgumentParser()
    result.add_argument("--stage-a-manifest",type=Path,required=True)
    result.add_argument("--checkpoint-manifest",type=Path,required=True)
    result.add_argument("--output-root",type=Path,required=True)
    result.add_argument("--stage-a-shard",type=int,choices=range(4),required=True)
    return result


def execute_stage_a(stage_a_manifest: Path, checkpoint_manifest: Path, output_root: Path, stage_a_shard: int) -> None:
    """Production Stage A implementation; protocol-lock tests do not call it."""
    import nibabel as nib
    import torch
    from src.models.crosscase_future_predictor import CrossCaseSmallUNet

    with stage_a_manifest.open(newline="",encoding="utf-8") as handle:
        records=[r for r in csv.DictReader(handle) if int(r["stage_a_shard"])==stage_a_shard]
    with checkpoint_manifest.open(newline="",encoding="utf-8") as handle:
        checkpoints=list(csv.DictReader(handle))
    if len(checkpoints)!=5: raise RuntimeError("Checkpoint manifest must contain exactly five folds")
    models=[]
    for checkpoint in checkpoints:
        path=Path(checkpoint["checkpoint_path"])
        if sha256(path)!=checkpoint["sha256"]: raise RuntimeError(f"Checkpoint hash mismatch: {path}")
        raw=torch.load(path,map_location="cpu",weights_only=False)
        state=raw.get("model_state_dict",raw.get("state_dict",raw)) if isinstance(raw,dict) else raw
        model=CrossCaseSmallUNet(in_channels=2,out_channels=1,base=16)
        model.load_state_dict(state,strict=True); model.eval(); models.append(model)
    for record in records:
        validate_current_only_record(record)
        t1c=nib.load(record["current_t1c_path"]).get_fdata(dtype=np.float32)
        mask=nib.load(record["current_mask_path"]).get_fdata(dtype=np.float32)
        prepared=prepare_current_only_inputs(t1c,mask); batch=torch.from_numpy(prepared.model_input_zchw.astype(np.float32))
        predictions=[]
        with torch.inference_mode():
            for model in models:
                slices=[]
                for start in range(0,len(batch),64): slices.append(torch.sigmoid(model(batch[start:start+64])).cpu().numpy()[:,0])
                predictions.append(np.concatenate(slices).astype(np.float32))
        p0=equal_weight_average(predictions).astype(np.float32)
        output=output_root/record["output_p0_path"]; digest=atomic_save_p0(output,p0)
        access={"case_id":record["case_id"],"stage":"stage_a","stage_a_shard":stage_a_shard,
                "files_read":[record["current_t1c_path"],record["current_mask_path"]]+[r["checkpoint_path"] for r in checkpoints],
                "forbidden_file_access":False,"checkpoint_count":5,"ensemble_weights":list(ENSEMBLE_WEIGHTS),"p0_sha256":digest}
        output.with_suffix('.access.json').write_text(json.dumps(access,indent=2)+"\n")
        (output.parent/f"STAGE_A_SHARD_{stage_a_shard}_{record['case_id']}_COMPLETE.json").write_text(json.dumps({"status":"COMPLETE","stage":"stage_a","shard":stage_a_shard,"case_id":record["case_id"],"p0_sha256":digest})+"\n")


def main() -> None:
    args=parser().parse_args()
    execute_stage_a(args.stage_a_manifest,args.checkpoint_manifest,args.output_root,args.stage_a_shard)

if __name__=="__main__": main()
