"""Execute map-dependent validity-patch analyses without predictor access."""
from __future__ import annotations

import argparse, csv, json
from pathlib import Path

import numpy as np
import pandas as pd

from experiments.run_internal_completion_2026 import arrays, atomic_csv, spacing_and_masks
from src.analysis.internal_completion import FP_SEEDS, SHIFT_DIRECTIONS, fp25_guidance, mixed_guidance, partial_guidance, run_variant, shift_no_wrap
from src.analysis.validity_patch import METHOD_FILES, select_crossfit_threshold, target_independent_metrics, threshold_grid_case_dice


def map_for(frozen: Path, case: str, method: str, p0: np.ndarray, target: np.ndarray) -> np.ndarray:
    case_root=frozen/"retrospective/cases"/case
    if method=="FIXED": return p0
    if method=="NO_SMOOTHING": return run_variant(p0,target,smoothing=False).probability
    return np.load(case_root/METHOD_FILES[method],allow_pickle=False)


def run_target_independent(frozen: Path, output: Path) -> None:
    manifest=pd.read_csv(frozen/"LOCKED_CASE_MANIFEST.csv"); folds=pd.read_csv(frozen/"LOCKED_FOLD_MANIFEST.csv")
    held=folds[folds.split=="test"][["case_id","fold"]]; fold_by_case=dict(zip(held.case_id,held.fold)); rows=[]; curves={}; grid=np.arange(.01,1,.01)
    for record in manifest.to_dict("records"):
        case=record["case_id"]; p0,target=arrays(frozen,case)
        for method in METHOD_FILES | {"NO_SMOOTHING": "computed_locked"}:
            probability=map_for(frozen,case,method,p0,target); metric=target_independent_metrics(probability,target,.5)
            rows.append({"case_id":case,"fold":fold_by_case[case],"method":method,"evaluation":"fixed_0.5_and_probability","probability_source":"frozen_v8" if method!="NO_SMOOTHING" else "locked_no_smoothing_recomputation",**metric})
            curves[(case,method)]=threshold_grid_case_dice(probability,target,grid)
    for fold in sorted(held.fold.unique()):
        test_cases=held.loc[held.fold==fold,"case_id"].tolist(); training_cases=held.loc[held.fold!=fold,"case_id"].tolist()
        for method in METHOD_FILES | {"NO_SMOOTHING":"computed_locked"}:
            threshold=select_crossfit_threshold(np.stack([curves[(case,method)] for case in training_cases]),grid)
            for case in test_cases:
                p0,target=arrays(frozen,case); probability=map_for(frozen,case,method,p0,target); metric=target_independent_metrics(probability,target,threshold)
                rows.append({"case_id":case,"fold":fold,"method":method,"evaluation":"crossfitted_threshold","probability_source":"frozen_v8" if method!="NO_SMOOTHING" else "locked_no_smoothing_recomputation",**metric})
    atomic_csv(output/"02_target_independent_evaluation/TARGET_INDEPENDENT_CASE_METRICS.csv",rows)


def guidance_specs(clean: np.ndarray, spacing: tuple[float,float,float], case: str):
    for fraction,name in [(.5,"PARTIAL_50"),(.25,"PARTIAL_25")]:
        guide,retained=partial_guidance(clean,fraction); yield name,"deterministic",guide,{"retained_true_target_fraction":retained,"seed":None,"displacement":"none"}
    for seed in FP_SEEDS:
        guide,added,shortfall=fp25_guidance(clean,spacing,case,seed); yield "FP_25",f"seed_{seed}",guide,{"retained_true_target_fraction":1.0,"added_false_positive_volume":added,"seed":seed,"displacement":"none","fp_shortfall":shortfall}
    for direction in SHIFT_DIRECTIONS:
        yield "SHIFT_3",direction,shift_no_wrap(clean,direction),{"retained_true_target_fraction":1.0,"added_false_positive_volume":0,"seed":None,"displacement":direction}
    for seed in FP_SEEDS:
        for direction in SHIFT_DIRECTIONS:
            guide,metadata=mixed_guidance(clean,spacing,case,seed,direction); yield "MIXED",f"seed_{seed}_{direction}",guide,metadata


def resolve_record_paths(record: dict[str, object], search_root: Path = Path("/kaggle/input")) -> dict[str, object]:
    """Resolve immutable manifest basenames when Kaggle changes mount prefixes."""
    resolved=dict(record)
    for column in ("current_t1c_path","current_mask_path","future_mask_path"):
        source=Path(str(resolved[column]))
        if source.exists():
            continue
        matches=list(search_root.rglob(source.name))
        if len(matches)!=1:
            raise FileNotFoundError(f"Expected one mounted match for {source.name}, found {len(matches)}")
        resolved[column]=str(matches[0])
    return resolved


def run_no_smoothing(frozen: Path, original_repeats: Path, output: Path, shard_index: int, shard_count: int) -> None:
    manifest=pd.read_csv(frozen/"LOCKED_CASE_MANIFEST.csv").sort_values("case_id"); manifest=manifest.iloc[shard_index::shard_count]
    original=pd.read_csv(original_repeats); rows=[]; failures=[]
    for record in manifest.to_dict("records"):
        record=resolve_record_paths(record)
        case=record["case_id"]
        try:
            p0,clean=arrays(frozen,case); spacing,*_=spacing_and_masks(record)
            clean_probability=run_variant(p0,clean,smoothing=False).probability
            for condition,repeat,guide,metadata in guidance_specs(clean,spacing,case):
                expected=original[(original.case_id==case)&(original.condition==condition)&(original.method=="PCC")&(original["repeat"].astype(str)==repeat)]
                if len(expected)!=1: raise RuntimeError(f"Original repeat identity mismatch {case} {condition} {repeat}: {len(expected)}")
                source=expected.iloc[0]
                if int(guide.sum())!=int(source.guidance_voxels): raise RuntimeError("Guidance voxel count mismatch")
                probability=run_variant(p0,guide,smoothing=False).probability
                metrics=target_independent_metrics(probability,clean,.5)
                # Locked top-k evaluation uses target-volume matching.
                order=np.argpartition(probability.ravel(),-int(clean.sum()))[-int(clean.sum()):]; pred=np.zeros(probability.size,dtype=bool); pred[order]=True; pred=pred.reshape(clean.shape)
                tp=int((pred&clean).sum()); topk_dice=2*tp/(pred.sum()+clean.sum()); topk_iou=tp/(pred.sum()+clean.sum()-tp)
                rows.append({"case_id":case,"condition":condition,"repeat":repeat,"method":"NO_SMOOTHING_PCC","dice_topk":topk_dice,"iou_topk":topk_iou,"dice_fixed05":metrics["dice_fixed"],"iou_fixed05":metrics["iou_fixed"],"predicted_positive_voxels":metrics["predicted_positive_voxels"],"target_mass":float(probability[clean].sum()),"false_guidance_mass":float(probability[guide&~clean].sum()),"outside_clean_target_mass":float(probability[~clean].sum()),"own_clean_dice_topk":target_independent_metrics(clean_probability,clean,.5)["dice_fixed"],"guidance_voxels":int(guide.sum()),**metadata})
        except Exception as exc: failures.append({"case_id":case,"error":repr(exc)})
    destination=output/"03_no_smoothing_robustness"; atomic_csv(destination/f"NO_SMOOTHING_REPEAT_METRICS_SHARD_{shard_index}.csv",rows); atomic_csv(destination/f"FAILED_CASES_SHARD_{shard_index}.csv",failures,fields=["case_id","error"])
    (output/f"NO_SMOOTHING_SHARD_{shard_index}_COMPLETE.json").write_text(json.dumps({"status":"COMPLETE" if not failures else "COMPLETE_WITH_FAILURES","cases":len(manifest),"rows":len(rows),"predictor_retrained":False,"p0_regenerated":False},indent=2)+"\n")


def main():
    p=argparse.ArgumentParser(); p.add_argument("--family",choices=["target","no_smoothing"],required=True); p.add_argument("--frozen-root",type=Path,required=True); p.add_argument("--output-root",type=Path,required=True); p.add_argument("--original-repeats",type=Path); p.add_argument("--shard-index",type=int,default=0); p.add_argument("--shard-count",type=int,default=1); a=p.parse_args()
    if a.family=="target": run_target_independent(a.frozen_root,a.output_root)
    else: run_no_smoothing(a.frozen_root,a.original_repeats,a.output_root,a.shard_index,a.shard_count)


if __name__=="__main__": main()
