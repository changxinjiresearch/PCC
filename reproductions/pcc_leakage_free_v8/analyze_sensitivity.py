"""Summarize locked version-8 sensitivity results against frozen P10."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path

import numpy as np

from reproductions.pcc_leakage_free_v8.analyze_version8 import (
    SEED, describe, exact_wilcoxon, rank_biserial, spearman, write_csv,
)


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sensitivity-root", type=Path, required=True)
    parser.add_argument("--frozen-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=True)
    for name in ["SENSITIVITY_CASE_METRICS.csv", "SENSITIVITY_STATUS.json", "FAILED_CASES.csv"]:
        shutil.copy2(args.sensitivity_root / name, args.output / name)
    rows = read(args.output / "SENSITIVITY_CASE_METRICS.csv")
    main_rows = read(args.frozen_root / "FROZEN_MAIN_RESULTS.csv")
    canonical = {(r["case_id"], r["method"]): r for r in main_rows}
    cases = sorted({r["case_id"] for r in rows})
    configs = sorted({r["configuration"] for r in rows})
    rng = np.random.default_rng(SEED)
    summary=[]; paired=[]
    for config in configs:
        for metric, source_metric in [("dice", "dice_topk"), ("iou", "iou_topk")]:
            values=np.array([float(next(r[source_metric] for r in rows if r["case_id"]==case and r["configuration"]==config)) for case in cases])
            ref=np.array([float(canonical[(case,"pcc_correction")][metric]) for case in cases]); diff=values-ref
            summary.append({"configuration":config,"metric":metric,**describe(values,rng),"canonical_mean":float(ref.mean()),"mean_difference_vs_canonical":float(diff.mean()),"case_rank_spearman_vs_canonical":spearman(values,ref)})
            stat,p,n=exact_wilcoxon(diff); dsd=float(diff.std(ddof=1))
            paired.append({"method":config,"reference_method":"canonical_p10","metric":metric,"difference_definition":"configuration_minus_canonical",**describe(diff,rng),"wilcoxon_statistic":stat,"wilcoxon_p_exact":p,"wilcoxon_nonzero_n":n,"holm_adjusted_p":"","holm_family_size":"","cohens_dz":float(diff.mean()/dsd) if dsd else 0.0,"matched_pairs_rank_biserial":rank_biserial(diff),"wins":int((diff>0).sum()),"ties":int((diff==0).sum()),"losses":int((diff<0).sum())})
    # One predeclared family per metric across all eight configurations.
    for metric in ["dice","iou"]:
        family=[r for r in paired if r["metric"]==metric]; ordered=sorted(family,key=lambda r:r["wilcoxon_p_exact"]); running=0.0
        for i,row in enumerate(ordered):
            running=max(running,min(1.0,(len(ordered)-i)*row["wilcoxon_p_exact"]));row["holm_adjusted_p"]=running;row["holm_family_size"]=len(ordered)
    write_csv(args.output/"SENSITIVITY_SUMMARY.csv",summary,list(summary[0]));write_csv(args.output/"SENSITIVITY_PAIRED_STATISTICS.csv",paired,list(paired[0]))
    print(json.dumps({"status":"PASS","rows":len(rows),"summary_rows":len(summary),"paired_rows":len(paired)},indent=2))


if __name__ == "__main__":
    main()
