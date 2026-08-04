"""Finalize target-independent and no-smoothing follow-up outputs."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.internal_statistics import bootstrap_ci, holm_adjust
from src.analysis.validity_patch import one_sample_statistics


def target_outputs(root: Path) -> tuple[pd.DataFrame,pd.DataFrame]:
    path=root/"02_target_independent_evaluation/TARGET_INDEPENDENT_CASE_METRICS.csv"; frame=pd.read_csv(path); assert len(frame)==640 and frame.case_id.nunique()==40 and frame.method.nunique()==8
    metric_names=["dice_fixed","iou_fixed","precision_fixed","recall_fixed","specificity_fixed","soft_dice","brier_score","average_precision","target_probability_mass","outside_target_probability_mass","predicted_positive_voxels","volume_error_voxels"]
    rows=[]
    for keys,g in frame.groupby(["evaluation","method"],sort=True):
        for metric in metric_names:
            values=g[metric].astype(float).to_numpy(); finite=values[np.isfinite(values)]
            low,high=bootstrap_ci(finite,f"target:{keys}:{metric}"); rows.append({"evaluation":keys[0],"method":keys[1],"metric":metric,"N_total":len(values),"N_finite":len(finite),"mean":finite.mean(),"SD":finite.std(ddof=1),"median":np.median(finite),"Q1":np.quantile(finite,.25),"Q3":np.quantile(finite,.75),"bootstrap_95ci_low":low,"bootstrap_95ci_high":high})
    summary=pd.DataFrame(rows); summary.to_csv(root/"02_target_independent_evaluation/TARGET_INDEPENDENT_METHOD_SUMMARY.csv",index=False)
    paired=[]; comparisons=[m for m in sorted(frame.method.unique()) if m!="FULL_PCC"]
    for evaluation in sorted(frame.evaluation.unique()):
        subset=frame[frame.evaluation==evaluation]
        for metric in ["dice_fixed","iou_fixed","soft_dice","brier_score","average_precision"]:
            pivot=subset.pivot(index="case_id",columns="method",values=metric)
            family=[]
            for comparison in comparisons:
                paired_values=pivot[[comparison,"FULL_PCC"]].dropna(); delta=paired_values[comparison].to_numpy()-paired_values.FULL_PCC.to_numpy(); family.append({"family":f"target_independent:{evaluation}:{metric}","evaluation":evaluation,"metric":metric,"comparison":comparison,"reference":"FULL_PCC",**one_sample_statistics(delta,f"target-paired:{evaluation}:{metric}:{comparison}")})
            adjusted=holm_adjust([x["wilcoxon_p_two_sided"] for x in family])
            for row,p in zip(family,adjusted): row["holm_adjusted_p"]=p
            paired.extend(family)
    statistics=pd.DataFrame(paired); statistics.to_csv(root/"02_target_independent_evaluation/TARGET_INDEPENDENT_PAIRED_STATISTICS.csv",index=False); return summary,statistics


def no_smoothing_outputs(root: Path, internal: Path) -> tuple[pd.DataFrame,pd.DataFrame]:
    destination=root/"03_no_smoothing_robustness"; shards=sorted(destination.glob("NO_SMOOTHING_REPEAT_METRICS_SHARD_*.csv")); repeat=pd.concat([pd.read_csv(p) for p in shards],ignore_index=True).sort_values(["case_id","condition","repeat"]); assert len(repeat)==1720 and repeat.case_id.nunique()==40 and not repeat.duplicated(["case_id","condition","repeat"]).any(); repeat.to_csv(destination/"NO_SMOOTHING_REPEAT_METRICS.csv",index=False)
    numeric=[c for c in repeat if pd.api.types.is_numeric_dtype(repeat[c]) and c not in {"seed"}]; nosmooth=repeat.groupby(["case_id","condition"],as_index=False)[numeric].mean(); nosmooth["method"]="NO_SMOOTHING_PCC"
    original=pd.read_csv(internal/"03_imperfect_guidance/IMPERFECT_GUIDANCE_REPEAT_METRICS.csv"); original=original[original.method=="PCC"]; full=original.groupby(["case_id","condition"],as_index=False)[["dice_topk","iou_topk","dice_fixed05","iou_fixed05","target_mass","false_guidance_mass","outside_clean_target_mass","pred_fixed05_voxels"]].mean(); full=full.rename(columns={"pred_fixed05_voxels":"predicted_positive_voxels"}); full["method"]="FULL_PCC"
    mechanism=pd.read_csv(internal/"01_mechanism_ablation/MECHANISM_CASE_METRICS.csv"); independent=pd.read_csv(root/"02_target_independent_evaluation/TARGET_INDEPENDENT_CASE_METRICS.csv"); independent=independent[independent.evaluation=="fixed_0.5"] if "fixed_0.5" in set(independent.evaluation) else independent[independent.evaluation=="fixed_0.5_and_probability"]
    clean_rows=[]
    for condition,method,independent_method in [("FULL_PCC","FULL_PCC","FULL_PCC"),("NO_SMOOTHING","NO_SMOOTHING_PCC","NO_SMOOTHING")]:
        topk=mechanism[mechanism.condition==condition][["case_id","dice","iou"]].rename(columns={"dice":"dice_topk","iou":"iou_topk"}); fixed=independent[independent.method==independent_method][["case_id","dice_fixed","iou_fixed","target_probability_mass","outside_target_probability_mass","predicted_positive_voxels"]].rename(columns={"dice_fixed":"dice_fixed05","iou_fixed":"iou_fixed05","target_probability_mass":"target_mass","outside_target_probability_mass":"outside_clean_target_mass"}); g=topk.merge(fixed,on="case_id",validate="one_to_one"); g["condition"]="CLEAN"; g["false_guidance_mass"]=0.0; g["method"]=method; clean_rows.append(g)
    cases=pd.concat([*clean_rows,full,nosmooth],ignore_index=True,sort=False)
    clean=cases[cases.condition=="CLEAN"].set_index(["case_id","method"])
    for metric in ["dice_topk","iou_topk","dice_fixed05","iou_fixed05"]:
        cases[f"absolute_drop_{metric}"]=cases.apply(lambda row: row[metric]-clean.loc[(row.case_id,row.method),metric],axis=1); cases[f"retention_{metric}"]=cases.apply(lambda row: row[metric]/clean.loc[(row.case_id,row.method),metric] if clean.loc[(row.case_id,row.method),metric]!=0 else np.nan,axis=1)
    cases.to_csv(destination/"NO_SMOOTHING_CASE_AGGREGATED.csv",index=False)
    rows=[]
    for keys,g in cases.groupby(["condition","method"],sort=True):
        for metric in ["dice_topk","iou_topk","dice_fixed05","iou_fixed05","target_mass","false_guidance_mass","outside_clean_target_mass","predicted_positive_voxels"]:
            values=g[metric].astype(float).to_numpy(); low,high=bootstrap_ci(values,f"nosmooth:{keys}:{metric}"); rows.append({"condition":keys[0],"method":keys[1],"metric":metric,"N":len(values),"mean":values.mean(),"SD":values.std(ddof=1),"median":np.median(values),"Q1":np.quantile(values,.25),"Q3":np.quantile(values,.75),"bootstrap_95ci_low":low,"bootstrap_95ci_high":high})
    summary=pd.DataFrame(rows); summary.to_csv(destination/"NO_SMOOTHING_ROBUSTNESS_SUMMARY.csv",index=False)
    paired=[]; did=[]; degraded=["PARTIAL_50","PARTIAL_25","FP_25","SHIFT_3","MIXED"]
    for metric in ["dice_topk","iou_topk","dice_fixed05","iou_fixed05","outside_clean_target_mass"]:
        family=[]; did_family=[]
        pivot=cases.pivot(index="case_id",columns=["condition","method"],values=metric)
        for condition in degraded:
            delta=pivot[(condition,"NO_SMOOTHING_PCC")]-pivot[(condition,"FULL_PCC")]; family.append({"family":f"nosmooth_absolute:{metric}","condition":condition,"metric":metric,"comparison":"NO_SMOOTHING_PCC","reference":"FULL_PCC",**one_sample_statistics(delta.to_numpy(),f"nosmooth-absolute:{metric}:{condition}")})
            difference=(pivot[(condition,"NO_SMOOTHING_PCC")]-pivot[("CLEAN","NO_SMOOTHING_PCC")])-(pivot[(condition,"FULL_PCC")]-pivot[("CLEAN","FULL_PCC")]); did_family.append({"family":f"nosmooth_difference_in_differences:{metric}","condition":condition,"metric":metric,"difference_definition":"(NoSmooth degraded-NoSmooth clean)-(Full degraded-Full clean)",**one_sample_statistics(difference.to_numpy(),f"nosmooth-did:{metric}:{condition}")})
        for group,target in [(family,paired),(did_family,did)]:
            adjusted=holm_adjust([x["wilcoxon_p_two_sided"] for x in group]);
            for row,p in zip(group,adjusted): row["holm_adjusted_p"]=p
            target.extend(group)
    paired_frame=pd.DataFrame(paired); did_frame=pd.DataFrame(did); paired_frame.to_csv(destination/"NO_SMOOTHING_ROBUSTNESS_PAIRED_STATISTICS.csv",index=False); did_frame.to_csv(destination/"NO_SMOOTHING_DIFFERENCE_IN_DIFFERENCES.csv",index=False); return summary,did_frame


def main():
    p=argparse.ArgumentParser(); p.add_argument("--output-root",type=Path,required=True); p.add_argument("--internal-completion-root",type=Path,required=True); a=p.parse_args(); target_outputs(a.output_root); no_smoothing_outputs(a.output_root,a.internal_completion_root)


if __name__=="__main__": main()
