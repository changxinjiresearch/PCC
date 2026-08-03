"""Generate automatically ranked Layer 2 qualitative panels from frozen P0."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
import pandas as pd

from experiments.run_internal_completion_2026 import arrays, normalized_intensity, spacing_and_masks
from src.analysis.internal_completion import fp25_guidance, mixed_guidance, partial_guidance, run_variant, shift_no_wrap


def guidance_for(condition: str, repeat: str, clean: np.ndarray, spacing: tuple[float,float,float], case: str) -> np.ndarray:
    if condition == "PARTIAL_50": return partial_guidance(clean,.5)[0]
    if condition == "PARTIAL_25": return partial_guidance(clean,.25)[0]
    if condition == "FP_25": return fp25_guidance(clean,spacing,case,int(repeat.removeprefix("seed_")))[0]
    if condition == "SHIFT_3": return shift_no_wrap(clean,repeat)
    if condition == "MIXED":
        payload=repeat.removeprefix("seed_"); seed,direction=payload.split("_",1)
        return mixed_guidance(clean,spacing,case,int(seed),direction)[0]
    return clean


def selections(failure: pd.DataFrame) -> list[tuple[str,str]]:
    median=float(failure.pcc_gain.median())
    return [
        ("median_layer2_gain",failure.assign(distance=(failure.pcc_gain-median).abs()).sort_values(["distance","case_id"]).iloc[0].case_id),
        ("maximum_layer2_gain",failure.sort_values(["pcc_gain","case_id"],ascending=[False,True]).iloc[0].case_id),
        ("minimum_layer2_gain",failure.sort_values(["pcc_gain","case_id"]).iloc[0].case_id),
        ("smallest_target",failure.sort_values(["target_voxels","case_id"]).iloc[0].case_id),
        ("most_fragmented_target",failure.sort_values(["target_components","case_id"],ascending=[False,True]).iloc[0].case_id),
        ("worst_imperfect_retention",failure.sort_values(["smallest_imperfect_retention","case_id"]).iloc[0].case_id),
    ]


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--frozen-root",type=Path,required=True); parser.add_argument("--analysis-root",type=Path,required=True); parser.add_argument("--output-root",type=Path,required=True); args=parser.parse_args()
    failure=pd.read_csv(args.analysis_root/"06_failure_analysis/INTERNAL_FAILURE_BOUNDARY_CASES.csv")
    repeats=pd.read_csv(args.analysis_root/"03_imperfect_guidance/IMPERFECT_GUIDANCE_REPEAT_METRICS.csv")
    with (args.frozen_root/"LOCKED_CASE_MANIFEST.csv").open(newline="") as handle: manifest={row["case_id"]:row for row in csv.DictReader(handle)}
    output=args.output_root/"07_qualitative_panels"; output.mkdir(parents=True,exist_ok=True); source_rows=[]
    for category,case in selections(failure):
        record=manifest[case]; p0,clean=arrays(args.frozen_root,case); spacing,current_mask,future_mask,_,_=spacing_and_masks(record)
        p1=run_variant(p0,clean,rounds=1).probability; p10=run_variant(p0,clean,rounds=10).probability; correction=p10-p0
        guide=clean; guide_label="clean target"
        if category=="worst_imperfect_retention":
            condition=failure.set_index("case_id").loc[case,"worst_imperfect_condition"]
            candidates=repeats[(repeats.case_id==case)&(repeats.condition==condition)&(repeats.method=="PCC")].sort_values(["dice","repeat"])
            repeat=str(candidates.iloc[0]["repeat"]); guide=guidance_for(condition,repeat,clean,spacing,case); guide_label=f"{condition}: worst saved repeat {repeat}"
        image=normalized_intensity(nib.load(record["current_t1c_path"])); score=clean.sum(axis=(1,2))+10*np.abs(correction).sum(axis=(1,2)); z=int(np.argmax(score))
        panels=[("Current T1c",image[z],"gray"),("Current mask",current_mask[z],"gray"),("Future mask",future_mask[z],"gray"),("Clean change target",clean[z],"gray"),("Frozen P0",p0[z],"viridis"),("PCC P1",p1[z],"viridis"),("PCC P10",p10[z],"viridis"),("P10 - P0",correction[z],"coolwarm"),(guide_label,guide[z],"magma")]
        fig,axes=plt.subplots(3,3,figsize=(12,12))
        for axis,(title,data,cmap) in zip(axes.flat,panels): axis.imshow(data,cmap=cmap); axis.set_title(title,fontsize=9); axis.axis("off")
        fig.suptitle(f"{category}: {case}; axial index {z}"); fig.tight_layout()
        stem=f"{category}__{case}"; fig.savefig(output/f"{stem}.png",dpi=300,bbox_inches="tight"); fig.savefig(output/f"{stem}.svg",bbox_inches="tight"); plt.close(fig)
        source_rows.append({"category":category,"case_id":case,"slice_zyx_z":z,"selection_rule":"prespecified deterministic rank; case_id ascending tie break","p0_source":"frozen v8","p1_p10_source":"canonical refinement recomputed for visualization only","guidance_panel":guide_label,"png":f"{stem}.png","svg":f"{stem}.svg"})
    pd.DataFrame(source_rows).to_csv(output/"QUALITATIVE_PANEL_SOURCE_MAP.csv",index=False)


if __name__=="__main__": main()
