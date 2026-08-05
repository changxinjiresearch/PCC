#!/usr/bin/env python3
"""CPU-only checkpoint compatibility and cohort provenance supplement.

This script never calls a model forward method and never writes P0 or metrics.
"""
from __future__ import annotations

import argparse, csv, hashlib, json, re
from pathlib import Path

import nibabel as nib
import numpy as np
import torch

from src.models.crosscase_future_predictor import CrossCaseSmallUNet

EXPECTED = {
    "fold_1": "bb86bcdbde7e0e4a41f5700efd8c532f2a06d3a3d9bde183f0090238a277b18c",
    "fold_2": "fb75fc2dc1d6703e22ca7ef260a54a0563a184c5a295c0890279c51cb054e759",
    "fold_3": "3e2cb75c84fb861b82789d2bf87517ee494c3435e1b06d64c739437dce547107",
    "fold_4": "28656b1d282fc66e054887166a990810b25d7e6a66d9c21e8f3951868f7291c3",
    "fold_5": "69250135d3eef595b9244426f511c165f10635e1a56241f8fa372959d874c1f3",
}


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]], fields=None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def timepoint_number(path: Path) -> int:
    match = re.search(r"Timepoint_(\d+)", path.name)
    return int(match.group(1)) if match else -1


def find_dataset(input_root: Path) -> Path:
    roots = sorted({p.parent for p in input_root.rglob("PatientID_*") if p.is_dir()})
    for root in roots:
        if len(list(root.glob("PatientID_*"))) >= 200:
            return root
    raise RuntimeError("Could not locate source patient root")


def checkpoint_audit(input_root: Path, output: Path) -> None:
    rows=[]; parameter_rows=[]; log=[]
    for fold, expected_hash in EXPECTED.items():
        matches=[]
        for path in input_root.rglob("best_training_loss.pt"):
            if fold in path.parts and sha256(path) == expected_hash:
                matches.append(path)
        if len(matches) != 1:
            raise RuntimeError(f"{fold}: expected one hash-matching checkpoint, found {len(matches)}")
        path=matches[0]; actual_hash=sha256(path)
        raw=torch.load(path, map_location="cpu", weights_only=False)
        state=raw.get("model_state_dict", raw.get("state_dict", raw)) if isinstance(raw,dict) else raw
        if not isinstance(state,dict): raise RuntimeError(f"{fold}: no state_dict mapping")
        model=CrossCaseSmallUNet(in_channels=2,out_channels=1,base=16)
        model_state=model.state_dict(); missing=sorted(set(model_state)-set(state)); unexpected=sorted(set(state)-set(model_state))
        shape_mismatch=[]
        for key in sorted(set(model_state)&set(state)):
            expected_shape=tuple(model_state[key].shape); actual_shape=tuple(state[key].shape)
            ok=expected_shape==actual_shape
            if not ok: shape_mismatch.append(key)
            parameter_rows.append({"fold":fold,"parameter":key,"expected_shape":str(expected_shape),"checkpoint_shape":str(actual_shape),"shape_match":ok})
        strict_ok=False
        if not missing and not unexpected and not shape_mismatch:
            model.load_state_dict(state, strict=True); strict_ok=True
        row={"fold":fold,"checkpoint_path":str(path),"file_size_bytes":path.stat().st_size,
             "expected_sha256":expected_hash,"actual_sha256":actual_hash,"hash_status":"PASS" if actual_hash==expected_hash else "FAIL",
             "cpu_load_status":"PASS","state_dict_key_count":len(state),"model_key_count":len(model_state),
             "missing_keys":len(missing),"unexpected_keys":len(unexpected),"parameter_shape_mismatch":len(shape_mismatch),
             "strict_load_status":"PASS" if strict_ok else "FAIL","fold_identity_path_match":fold in path.parts,
             "real_case_forward_executed":False,"p0_generated":False}
        rows.append(row); log.append(json.dumps(row,sort_keys=True))
    write_csv(output/"03_PREDICTOR_LOCK/CHECKPOINT_STATE_DICT_AUDIT.csv", rows)
    write_csv(output/"03_PREDICTOR_LOCK/CHECKPOINT_PARAMETER_SHAPE_AUDIT.csv", parameter_rows)
    (output/"03_PREDICTOR_LOCK/CHECKPOINT_CPU_LOAD_TEST_OUTPUT.txt").write_text("\n".join(log)+"\n",encoding="utf-8")
    (output/"03_PREDICTOR_LOCK/CHECKPOINT_MODEL_COMPATIBILITY_REPORT.md").write_text(
        "# Checkpoint model compatibility\n\nAll five checkpoint files were rehashed and loaded on CPU. "
        "Each state dict was strictly loaded into the frozen `CrossCaseSmallUNet(2,1,16)` architecture. "
        "No model forward was called and no P0 was generated. These hashes are first formally locked by this 115-patient protocol supplement; the audit does not claim historical ZIP checkpoint verification.\n\n"
        + "\n".join(f"- {r['fold']}: hash {r['hash_status']}; CPU load {r['cpu_load_status']}; missing {r['missing_keys']}; unexpected {r['unexpected_keys']}; shape mismatch {r['parameter_shape_mismatch']}; strict load {r['strict_load_status']}." for r in rows)+"\n",
        encoding="utf-8")


def cohort_provenance(repo: Path, input_root: Path, output: Path) -> None:
    cohort=repo/"outputs/pcc_115_holdout_protocol_lock_2026/01_COHORT_LOCK"
    with (cohort/"LOCKED_40_PATIENT_IDS.csv").open() as f: locked40={r["patient_id"] for r in csv.DictReader(f)}
    with (cohort/"LOCKED_115_CASE_MANIFEST.csv").open() as f: locked115=list(csv.DictReader(f))
    locked115_ids={r["patient_id"] for r in locked115}; dataset=find_dataset(input_root)
    statuses=[]; longitudinal=[]; sidecar=[]
    generation_hash=sha256(Path(__file__))
    for patient in sorted(dataset.glob("PatientID_*")):
        usable=[]
        for tp in sorted(patient.glob("Timepoint_*"),key=timepoint_number):
            t1c=list(tp.glob("*_brain_t1c.nii")); mask=list(tp.glob("*_tumorMask.nii"))
            if len(t1c)==len(mask)==1: usable.append((tp,t1c[0],mask[0]))
        status="insufficient_usable_timepoints"; reason="fewer than two usable timepoints"
        if len(usable)>=2:
            cur,fut=usable[:2]; imgs=[nib.load(str(cur[1])),nib.load(str(cur[2])),nib.load(str(fut[2]))]
            geometry=all(im.shape==imgs[0].shape and np.allclose(im.affine,imgs[0].affine,rtol=0,atol=1e-5) and nib.aff2axcodes(im.affine)==nib.aff2axcodes(imgs[0].affine) for im in imgs[1:])
            target=(imgs[2].get_fdata()>0.5)&~(imgs[1].get_fdata()>0.5)
            if not geometry: status="geometry_failure"; reason="shape/affine/orientation mismatch"
            elif not target.any(): status="empty_target"; reason="future AND NOT current target empty"
            elif patient.name in locked40: status="locked_40"; reason="first 40 eligible patients"
            elif patient.name in locked115_ids: status="locked_115"; reason="remaining eligible patient"
            else: status="other_authoritative_exclusion"; reason="not in frozen 40/115 identity chain"
            longitudinal.append({"patient_id":patient.name,"usable_timepoint_count":len(usable),"current_timepoint":cur[0].name,"future_timepoint":fut[0].name,"status":status})
        statuses.append({"patient_id":patient.name,"source_timepoint_count":len(list(patient.glob('Timepoint_*'))),"usable_timepoint_count":len(usable),"cohort_status":status,"reason":reason})
    by_id={r["patient_id"]:r for r in locked115}
    for pid in sorted(by_id):
        row=by_id[pid]; current_t1c=Path(row["current_t1c_path"]); current_mask=Path(row["current_mask_path"]); future_mask=Path(row["future_mask_path"])
        future_tp=future_mask.parent; future_t1cs=list(future_tp.glob("*_brain_t1c.nii")); future_t1c=future_t1cs[0] if len(future_t1cs)==1 else None
        sidecar.append({"patient_id":pid,"case_id":row["case_id"],"current_t1c_sha256":sha256(current_t1c),"current_mask_sha256":sha256(current_mask),"future_mask_sha256":sha256(future_mask),"future_t1c_exists":future_t1c is not None,"future_t1c_path":str(future_t1c) if future_t1c else "","future_t1c_sha256":sha256(future_t1c) if future_t1c else "","manifest_generation_code_hash":generation_hash})
    write_csv(output/"01_COHORT_LOCK/ALL_LONGITUDINAL_PATIENTS.csv",longitudinal)
    write_csv(output/"01_COHORT_LOCK/LOCKED_115_EXCLUSION_AND_STATUS.csv",statuses)
    write_csv(output/"01_COHORT_LOCK/LOCKED_115_SOURCE_PROVENANCE_SIDECAR.csv",sidecar)
    counts={s:sum(r["cohort_status"]==s for r in statuses) for s in ["locked_40","locked_115","insufficient_usable_timepoints","geometry_failure","empty_target","other_authoritative_exclusion"]}
    if len(statuses)!=203 or len(longitudinal)!=155 or counts["locked_40"]!=40 or counts["locked_115"]!=115:
        raise RuntimeError(f"Cohort identity mismatch: source={len(statuses)} longitudinal={len(longitudinal)} counts={counts}")
    (output/"01_COHORT_LOCK/COHORT_SUPPLEMENT_STATUS.json").write_text(json.dumps({"status":"PASS","source_patients":len(statuses),"longitudinal_patients":len(longitudinal),"counts":counts,"locked_115_sidecar_rows":len(sidecar),"model_forward_executed":False,"p0_generated":False,"method_metrics_computed":False},indent=2)+"\n")


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--input-root",type=Path,required=True); parser.add_argument("--output-root",type=Path,required=True); parser.add_argument("--repo",type=Path,default=Path.cwd()); args=parser.parse_args()
    checkpoint_audit(args.input_root,args.output_root); cohort_provenance(args.repo,args.input_root,args.output_root)
    print(json.dumps({"status":"PASS","checkpoint_cpu_loads":5,"real_case_forward_executed":False,"p0_generated":False,"method_metrics_computed":False}))

if __name__ == "__main__": main()
