"""Execute locked PCC_INTERNAL_COMPLETION_2026 analyses from frozen v8 P0.

No predictor module is imported.  This program cannot train or regenerate P0.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

import nibabel as nib
import numpy as np

from src.analysis.internal_completion import (
    FP_SEEDS, SHIFT_DIRECTIONS, component_count, deranged_donors,
    fp25_guidance, large_components, mixed_guidance, partial_guidance,
    physical_dilate, physical_erode, run_variant, shift_no_wrap,
)
from src.evaluation.metrics import eval_prob_map
from src.models.eia import apply_eia

CONFIG_SHA256 = "7a36fe0689abae5552395da84b69260e081764c13bd540a2454b2e74494697c4"
STATUS_EXPECTED = {"status": "COMPLETE", "completed_folds": 5, "completed_p0_cases": 40, "completed_retrospective_cases": 40, "failed_cases": 0}


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def atomic_csv(path: Path, rows: list[dict[str, object]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    columns = fields or list(rows[0])
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)
    temporary.replace(path)


def validate(frozen: Path, config: Path) -> list[dict[str, str]]:
    if sha256(config) != CONFIG_SHA256:
        raise RuntimeError("Locked internal-completion config hash mismatch")
    status = json.loads((frozen / "FULL_RUN_STATUS.json").read_text())
    for key, expected in STATUS_EXPECTED.items():
        if status.get(key) != expected:
            raise RuntimeError(f"Frozen v8 mismatch {key}: {status.get(key)!r}")
    with (frozen / "LOCKED_CASE_MANIFEST.csv").open(newline="", encoding="utf-8") as handle:
        manifest = list(csv.DictReader(handle))
    if len(manifest) != 40 or len({row["case_id"] for row in manifest}) != 40:
        raise RuntimeError("Locked case manifest is not 40 unique cases")
    for row in manifest:
        case = row["case_id"]
        if not (frozen / "held_out_p0" / case / "P0_float32.npy").exists():
            raise RuntimeError(f"Missing frozen P0: {case}")
        if not (frozen / "retrospective/cases" / case / "target.npy").exists():
            raise RuntimeError(f"Missing frozen target: {case}")
    return manifest


def arrays(frozen: Path, case: str) -> tuple[np.ndarray, np.ndarray]:
    p0 = np.load(frozen / "held_out_p0" / case / "P0_float32.npy", allow_pickle=False)
    target = np.load(frozen / "retrospective/cases" / case / "target.npy", allow_pickle=False).astype(bool)
    if p0.dtype != np.float32 or p0.shape != target.shape or not np.isfinite(p0).all():
        raise RuntimeError(f"Frozen array contract failed: {case}")
    return p0, target


def metric_row(case: str, condition: str, probability: np.ndarray, evaluation_target: np.ndarray, guidance: np.ndarray, **extra: object) -> dict[str, object]:
    metrics = eval_prob_map(probability, evaluation_target)
    clean = evaluation_target.astype(bool)
    guide = guidance.astype(bool)
    return {
        "case_id": case, "condition": condition, **metrics,
        "guidance_voxels": int(guide.sum()), "evaluation_target_voxels": int(clean.sum()),
        "target_mass": float(probability[clean].sum()),
        "false_guidance_mass": float(probability[guide & ~clean].sum()),
        "outside_clean_target_mass": float(probability[~clean].sum()),
        **extra,
    }


def frozen_reference_rows(frozen: Path) -> tuple[dict[tuple[str, str], dict[str, str]], dict[tuple[str, int], dict[str, str]]]:
    with (frozen / "ALL_CASE_METHOD_METRICS.csv").open(newline="", encoding="utf-8") as handle:
        methods = {(row["case_id"], row["method"]): row for row in csv.DictReader(handle)}
    with (frozen / "ALL_PCC_ROUND_TRAJECTORIES.csv").open(newline="", encoding="utf-8") as handle:
        rounds = {(row["case_id"], int(row["round"])): row for row in csv.DictReader(handle)}
    return methods, rounds


def run_mechanism(frozen: Path, manifest: list[dict[str, str]], out: Path) -> None:
    methods, rounds = frozen_reference_rows(frozen)
    family = out / "01_mechanism_ablation"; cases_dir = family / "cases"; failures = []
    variants = {
        "NO_ERROR_GUIDED_TERM": dict(error_guided=False, outside_suppression=True),
        "NO_OUTSIDE_SUPPRESSION": dict(error_guided=True, outside_suppression=False),
        "NO_SMOOTHING": dict(error_guided=True, outside_suppression=True, smoothing=False),
        "GLOBAL_DISCREPANCY": dict(error_guided=True, outside_suppression=True, global_discrepancy=True),
        "FACTORIAL_ERROR_ON_SUPPRESSION_ON": dict(error_guided=True, outside_suppression=True),
        "FACTORIAL_ERROR_ON_SUPPRESSION_OFF": dict(error_guided=True, outside_suppression=False),
        "FACTORIAL_ERROR_OFF_SUPPRESSION_ON": dict(error_guided=False, outside_suppression=True),
        "FACTORIAL_ERROR_OFF_SUPPRESSION_OFF": dict(error_guided=False, outside_suppression=False),
    }
    for record in manifest:
        case = record["case_id"]; destination = cases_dir / case; complete = destination / "COMPLETE.json"
        if complete.exists(): continue
        destination.mkdir(parents=True, exist_ok=True)
        try:
            p0, target = arrays(frozen, case); rows = []
            for name in ["fixed_baseline", "naive_self_tightening", "pcc_correction"]:
                source = methods[(case, name)]
                rows.append({"case_id": case, "condition": {"fixed_baseline":"FIXED_P0", "naive_self_tightening":"NAIVE", "pcc_correction":"FULL_PCC"}[name], "dice": source["dice"], "iou": source["iou"], "source": "frozen_v8"})
            p1 = rounds[(case, 1)]; rows.append({"case_id": case, "condition": "ONE_ROUND", "dice": p1["dice"], "iou": p1["iou"], "source": "frozen_v8_P1"})
            for name, parameters in variants.items():
                result = run_variant(p0, target, **parameters).probability
                if name.endswith("OFF_SUPPRESSION_OFF") and not np.array_equal(result, p0):
                    raise RuntimeError("Factorial identity output differs from P0")
                rows.append(metric_row(case, name, result, target, target, source="new_2026"))
            atomic_csv(destination / "metrics.csv", rows)
            complete.write_text(json.dumps({"case_id":case,"status":"complete","p0_sha256":sha256(frozen/'held_out_p0'/case/'P0_float32.npy')})+"\n")
        except Exception as exc: failures.append({"case_id":case,"family":"mechanism","error":repr(exc)})
    combine_case_csvs(cases_dir, family / "MECHANISM_CASE_METRICS.csv")
    write_failures(family / "FAILED_CASES.csv", failures)


def run_shuffled(frozen: Path, manifest: list[dict[str, str]], out: Path) -> None:
    family = out / "02_shuffled_target"; family.mkdir(parents=True, exist_ok=True)
    volumes = {}; patients = {}
    for record in manifest:
        _, target = arrays(frozen, record["case_id"]); volumes[record["case_id"]] = int(target.sum()); patients[record["case_id"]] = record["patient_id"]
    mapping = deranged_donors(list(volumes), volumes, patients)
    map_rows = [{"recipient_case_id":case,"recipient_patient_id":patients[case],"donor_case_id":donor,"donor_patient_id":patients[donor],"recipient_target_voxels":volumes[case],"donor_target_voxels":volumes[donor]} for case,donor in sorted(mapping.items())]
    atomic_csv(family / "SHUFFLED_TARGET_DONOR_MAP.csv", map_rows)
    (family / "SHUFFLED_TARGET_DONOR_MAP.sha256").write_text(sha256(family/"SHUFFLED_TARGET_DONOR_MAP.csv")+"  SHUFFLED_TARGET_DONOR_MAP.csv\n")
    failures=[]; cases_dir=family/"cases"
    for record in manifest:
        case=record["case_id"]; destination=cases_dir/case; complete=destination/"COMPLETE.json"
        if complete.exists(): continue
        destination.mkdir(parents=True, exist_ok=True)
        try:
            p0,clean=arrays(frozen,case); _,donor=arrays(frozen,mapping[case])
            if donor.shape != clean.shape: raise RuntimeError(f"Donor shape mismatch: {donor.shape} vs {clean.shape}")
            probability=run_variant(p0,donor).probability
            atomic_csv(destination/"metrics.csv",[metric_row(case,"SHUFFLED_TARGET_PCC",probability,clean,donor,donor_case_id=mapping[case])])
            complete.write_text(json.dumps({"case_id":case,"status":"complete","donor":mapping[case]})+"\n")
        except Exception as exc: failures.append({"case_id":case,"family":"shuffled","error":repr(exc)})
    combine_case_csvs(cases_dir,family/"SHUFFLED_TARGET_CASE_METRICS.csv"); write_failures(family/"FAILED_CASES.csv",failures)


def spacing_and_masks(record: dict[str, str]) -> tuple[tuple[float,float,float],np.ndarray,np.ndarray,nib.Nifti1Image,nib.Nifti1Image]:
    current_image=nib.load(record["current_mask_path"]); future_image=nib.load(record["future_mask_path"])
    current=np.moveaxis(current_image.get_fdata()>0.5,-1,0); future=np.moveaxis(future_image.get_fdata()>0.5,-1,0)
    spacing_xyz=tuple(float(x) for x in current_image.header.get_zooms()[:3]); spacing_zyx=tuple(reversed(spacing_xyz))
    return spacing_zyx,current,future,current_image,future_image


def run_imperfect(frozen: Path, manifest: list[dict[str, str]], out: Path) -> None:
    family=out/"03_imperfect_guidance"; cases_dir=family/"cases"; failures=[]
    for record in manifest:
        case=record["case_id"]; destination=cases_dir/case; complete=destination/"COMPLETE.json"
        if complete.exists(): continue
        destination.mkdir(parents=True,exist_ok=True)
        try:
            p0,clean=arrays(frozen,case); spacing,*_=spacing_and_masks(record); rows=[]
            guidance_specs=[]
            for fraction,name in [(0.50,"PARTIAL_50"),(0.25,"PARTIAL_25")]:
                guide,retained=partial_guidance(clean,fraction); guidance_specs.append((name,guide,{"repeat":"deterministic","retained_true_target_fraction":retained,"added_false_positive_volume":0,"displacement":"none"}))
            for seed in FP_SEEDS:
                guide,added,shortfall=fp25_guidance(clean,spacing,case,seed); guidance_specs.append(("FP_25",guide,{"repeat":f"seed_{seed}","seed":seed,"retained_true_target_fraction":1.0,"added_false_positive_volume":added,"fp_shortfall":shortfall,"displacement":"none"}))
            for direction in SHIFT_DIRECTIONS:
                guide=shift_no_wrap(clean,direction); guidance_specs.append(("SHIFT_3",guide,{"repeat":direction,"retained_true_target_fraction":float((guide&clean).sum()/clean.sum()),"added_false_positive_volume":int((guide&~clean).sum()),"displacement":direction}))
            for seed,direction in __import__('itertools').product(FP_SEEDS,SHIFT_DIRECTIONS):
                guide,details=mixed_guidance(clean,spacing,case,seed,direction); guidance_specs.append(("MIXED",guide,{"repeat":f"seed_{seed}_{direction}",**details}))
            for condition,guide,details in guidance_specs:
                pcc=run_variant(p0,guide).probability; eia=apply_eia(p0,guide)
                for method,probability in [("PCC",pcc),("EIA_LINEAR",eia.linear),("EIA_BLEND_075",eia.blend075)]:
                    rows.append(metric_row(case,condition,probability,clean,guide,method=method,retention_relative_to_clean_pcc="COMPUTE_IN_AGGREGATION",**details))
            atomic_csv(destination/"repeat_metrics.csv",rows); complete.write_text(json.dumps({"case_id":case,"status":"complete","rows":len(rows)})+"\n")
        except Exception as exc: failures.append({"case_id":case,"family":"imperfect","error":repr(exc)})
    combine_case_csvs(cases_dir,family/"IMPERFECT_GUIDANCE_REPEAT_METRICS.csv",filename="repeat_metrics.csv"); write_failures(family/"FAILED_CASES.csv",failures)


def run_targets(frozen: Path, manifest: list[dict[str,str]], out: Path) -> None:
    family=out/"04_target_construction"; cases_dir=family/"cases"; failures=[]
    for record in manifest:
        case=record["case_id"]; destination=cases_dir/case; complete=destination/"COMPLETE.json"
        if complete.exists(): continue
        destination.mkdir(parents=True,exist_ok=True)
        try:
            p0,original=arrays(frozen,case); spacing,current,future,_,_=spacing_and_masks(record)
            definitions={"ORIGINAL":future&~current,"BOUNDARY_TOLERANT":future&~physical_dilate(current,spacing),"ERODED_CURRENT":future&~physical_erode(current,spacing),"LARGE_CHANGE_ONLY":large_components(original,spacing)}
            rows=[]
            for name,target in definitions.items():
                probability=run_variant(p0,target).probability
                for mode,evaluation in [("same_definition",target),("original_clean",original)]:
                    row=metric_row(case,name,probability,evaluation,target,evaluation_mode=mode,empty_target=not bool(target.any()),target_components=component_count(target),voxel_volume_mm3=float(np.prod(spacing)))
                    rows.append(row)
            atomic_csv(destination/"metrics.csv",rows); complete.write_text(json.dumps({"case_id":case,"status":"complete"})+"\n")
        except Exception as exc: failures.append({"case_id":case,"family":"targets","error":repr(exc)})
    combine_case_csvs(cases_dir,family/"TARGET_CONSTRUCTION_CASE_METRICS.csv"); write_failures(family/"FAILED_CASES.csv",failures)


def run_identity(frozen: Path, manifest: list[dict[str,str]], out: Path) -> None:
    family=out/"09_dataset_identity"; rows=[]
    for record in manifest:
        spacing,current,future,current_image,future_image=spacing_and_masks(record)
        paths={k:record[k] for k in ["current_t1c_path","current_mask_path","future_mask_path"]}
        for role,path in paths.items():
            source=Path(path); rows.append({"case_id":record["case_id"],"patient_id":record["patient_id"],"role":role,"kaggle_path":path,"size_bytes":source.stat().st_size,"sha256":sha256(source),"shape":str(current_image.shape if role!="future_mask_path" else future_image.shape),"spacing_xyz":str(current_image.header.get_zooms()[:3] if role!="future_mask_path" else future_image.header.get_zooms()[:3])})
    atomic_csv(family/"LOCKED_CASE_FILE_MAP.csv",rows)
    (family/"DATASET_IDENTITY_LOCK.json").write_text(json.dumps({"status":"LOCKED","owner_slug":"stacyvangepuram/mu-glioma-post","cases":40,"file_rows":len(rows),"file_map_sha256":sha256(family/'LOCKED_CASE_FILE_MAP.csv'),"case_manifest_modified":False,"fold_manifest_modified":False},indent=2)+"\n")


def combine_case_csvs(cases_dir: Path, destination: Path, filename: str="metrics.csv") -> None:
    rows=[]
    for path in sorted(cases_dir.glob(f"*/{filename}")):
        with path.open(newline="",encoding="utf-8") as handle: rows.extend(csv.DictReader(handle))
    if rows: atomic_csv(destination,rows)


def write_failures(path: Path, failures: list[dict[str,str]]) -> None:
    atomic_csv(path,failures,["case_id","family","error"])


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--family",choices=["mechanism","shuffled","imperfect","targets","identity"],required=True); parser.add_argument("--frozen-root",type=Path,required=True); parser.add_argument("--output-root",type=Path,required=True); parser.add_argument("--config",type=Path,required=True); parser.add_argument("--shard-index",type=int,default=0); parser.add_argument("--shard-count",type=int,default=1); parser.add_argument("--case-limit",type=int); args=parser.parse_args()
    manifest=validate(args.frozen_root,args.config)
    if args.shard_count < 1 or not 0 <= args.shard_index < args.shard_count:
        raise ValueError("Invalid deterministic shard specification")
    manifest=[row for index,row in enumerate(sorted(manifest,key=lambda item:item["case_id"])) if index % args.shard_count == args.shard_index]
    if args.case_limit is not None: manifest=manifest[:args.case_limit]
    args.output_root.mkdir(parents=True,exist_ok=True)
    {"mechanism":run_mechanism,"shuffled":run_shuffled,"imperfect":run_imperfect,"targets":run_targets,"identity":run_identity}[args.family](args.frozen_root,manifest,args.output_root)
    print(json.dumps({"status":"COMPLETE","family":args.family,"cases":len(manifest),"shard_index":args.shard_index,"shard_count":args.shard_count,"predictor_retrained":False,"p0_regenerated":False}))


if __name__ == "__main__": main()
