"""Freeze and analyse the completed PCC_LEAKAGE_FREE_RERUN_2026 v8 outputs.

This is a result-analysis utility. It never loads or changes predictor
checkpoints, probability maps, targets, manifests, or scientific configs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
from collections import defaultdict
from pathlib import Path

import numpy as np


SEED = 20260803
BOOTSTRAPS = 10_000
METHODS = (
    "fixed_baseline",
    "naive_self_tightening",
    "eia_linear",
    "eia_blend090",
    "eia_blend075",
    "eia_morph",
    "pcc_correction",
)
ANCHORS = ("fixed_baseline", "naive_self_tightening", "eia_linear", "pcc_correction")
METRICS = ("dice", "iou")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temp.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ranks(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    out = np.empty(len(values), dtype=float)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and values[order[end]] == values[order[start]]:
            end += 1
        out[order[start:end]] = (start + 1 + end) / 2.0
        start = end
    return out


def exact_wilcoxon(diff: np.ndarray) -> tuple[float, float, int]:
    nonzero = diff[diff != 0.0]
    n = len(nonzero)
    if n == 0:
        return 0.0, 1.0, 0
    rank = ranks(np.abs(nonzero))
    positive = float(rank[nonzero > 0].sum())
    negative = float(rank[nonzero < 0].sum())
    statistic = min(positive, negative)
    scaled = np.rint(rank * 2).astype(int)
    observed = int(round(positive * 2))
    total = int(scaled.sum())
    counts = [0] * (total + 1)
    counts[0] = 1
    active = 0
    for value in scaled:
        for current in range(active, -1, -1):
            if counts[current]:
                counts[current + value] += counts[current]
        active += int(value)
    lower = min(observed, total - observed)
    extreme = sum(counts[: lower + 1]) + sum(counts[total - lower :])
    p_value = min(1.0, extreme / (2**n))
    return statistic, p_value, n


def bootstrap_mean_ci(values: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    n = len(values)
    means = np.empty(BOOTSTRAPS, dtype=float)
    chunk = 500
    for start in range(0, BOOTSTRAPS, chunk):
        count = min(chunk, BOOTSTRAPS - start)
        sample = rng.integers(0, n, size=(count, n))
        means[start : start + count] = values[sample].mean(axis=1)
    low, high = np.quantile(means, [0.025, 0.975])
    return float(low), float(high)


def describe(values: np.ndarray, rng: np.random.Generator) -> dict[str, object]:
    q1, median, q3 = np.quantile(values, [0.25, 0.5, 0.75])
    low, high = bootstrap_mean_ci(values, rng)
    return {
        "n": len(values),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)),
        "median": float(median),
        "q1": float(q1),
        "q3": float(q3),
        "iqr": float(q3 - q1),
        "bootstrap_95ci_low": low,
        "bootstrap_95ci_high": high,
        "bootstrap_resamples": BOOTSTRAPS,
        "bootstrap_seed": SEED,
    }


def rank_biserial(diff: np.ndarray) -> float:
    nonzero = diff[diff != 0]
    if len(nonzero) == 0:
        return 0.0
    rank = ranks(np.abs(nonzero))
    total = rank.sum()
    return float((rank[nonzero > 0].sum() - rank[nonzero < 0].sum()) / total)


def holm(rows: list[dict[str, object]]) -> None:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["reference_method"]), str(row["metric"]))].append(row)
    for family in grouped.values():
        ordered = sorted(family, key=lambda row: float(row["wilcoxon_p_exact"]))
        running = 0.0
        m = len(ordered)
        for index, row in enumerate(ordered):
            adjusted = min(1.0, (m - index) * float(row["wilcoxon_p_exact"]))
            running = max(running, adjusted)
            row["holm_adjusted_p"] = running
            row["holm_family_size"] = m


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    return float(np.corrcoef(ranks(x), ranks(y))[0, 1])


def permutation_spearman_p(
    x: np.ndarray, y: np.ndarray, rng: np.random.Generator, permutations: int = 20_000
) -> float:
    observed = abs(spearman(x, y))
    xr, yr = ranks(x), ranks(y)
    count = 0
    for _ in range(permutations):
        if abs(float(np.corrcoef(xr, rng.permutation(yr))[0, 1])) >= observed:
            count += 1
    return (count + 1) / (permutations + 1)


def svg_plot(path: Path, title: str, body: str, width: int = 1000, height: int = 620) -> None:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        '<rect width="100%" height="100%" fill="white"/>\n'
        f'<text x="{width/2}" y="34" text-anchor="middle" font-family="Arial" '
        f'font-size="22" font-weight="bold">{title}</text>\n{body}\n</svg>\n'
    )
    path.write_text(svg, encoding="utf-8")


def line_figure(path: Path, rounds: list[int], dice: list[float], iou: list[float]) -> None:
    left, top, width, height = 90, 70, 840, 460
    def point(i: int, value: float) -> tuple[float, float]:
        return left + i * width / (len(rounds) - 1), top + (1 - value) * height
    body = [f'<line x1="{left}" y1="{top+height}" x2="{left+width}" y2="{top+height}" stroke="black"/>',
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+height}" stroke="black"/>']
    for tick in np.linspace(0, 1, 6):
        y = top + (1 - tick) * height
        body.append(f'<line x1="{left}" y1="{y}" x2="{left+width}" y2="{y}" stroke="#ddd"/>')
        body.append(f'<text x="{left-12}" y="{y+5}" text-anchor="end" font-family="Arial" font-size="13">{tick:.1f}</text>')
    for idx, r in enumerate(rounds):
        x = left + idx * width / (len(rounds) - 1)
        body.append(f'<text x="{x}" y="{top+height+25}" text-anchor="middle" font-family="Arial" font-size="13">P{r}</text>')
    for values, colour, label in [(dice, "#1261a0", "Dice"), (iou, "#d1495b", "IoU")]:
        pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in (point(i, v) for i, v in enumerate(values)))
        body.append(f'<polyline points="{pts}" fill="none" stroke="{colour}" stroke-width="3"/>')
        for i, value in enumerate(values):
            x, y = point(i, value); body.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{colour}"/>')
        body.append(f'<text x="{left+width-80}" y="{top+25+(25 if label=="IoU" else 0)}" fill="{colour}" font-family="Arial" font-size="15">{label}</text>')
    svg_plot(path, "PCC mean trajectory (version 8)", "\n".join(body))


def scatter_figure(path: Path, x: np.ndarray, y: np.ndarray, title: str, xlabel: str) -> None:
    left, top, width, height = 100, 70, 820, 460
    xmin, xmax, ymin, ymax = float(x.min()), float(x.max()), float(y.min()), float(y.max())
    padx, pady = (xmax-xmin)*0.05 or 1, (ymax-ymin)*0.08 or 1
    xmin, xmax, ymin, ymax = xmin-padx, xmax+padx, ymin-pady, ymax+pady
    sx=lambda v:left+(v-xmin)/(xmax-xmin)*width
    sy=lambda v:top+(ymax-v)/(ymax-ymin)*height
    body=[f'<line x1="{left}" y1="{top+height}" x2="{left+width}" y2="{top+height}" stroke="black"/>',
          f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+height}" stroke="black"/>']
    for xv,yv in zip(x,y): body.append(f'<circle cx="{sx(float(xv)):.2f}" cy="{sy(float(yv)):.2f}" r="5" fill="#1261a0" fill-opacity="0.72"/>')
    body.append(f'<text x="{left+width/2}" y="{top+height+48}" text-anchor="middle" font-family="Arial" font-size="15">{xlabel}</text>')
    body.append(f'<text x="25" y="{top+height/2}" transform="rotate(-90 25 {top+height/2})" text-anchor="middle" font-family="Arial" font-size="15">PCC − Fixed Dice</text>')
    svg_plot(path,title,"\n".join(body))


def method_figure(path: Path, summary: list[dict[str, object]]) -> None:
    labels = ["Fixed", "Naive", "EIA-linear", "EIA-blend090", "EIA-blend075", "EIA-morph", "PCC"]
    left, top, width, height = 90, 70, 840, 460
    body = [f'<line x1="{left}" y1="{top+height}" x2="{left+width}" y2="{top+height}" stroke="black"/>',
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+height}" stroke="black"/>']
    for tick in np.linspace(0, 0.6, 7):
        y = top + (0.6 - tick) / 0.6 * height
        body.append(f'<line x1="{left}" y1="{y}" x2="{left+width}" y2="{y}" stroke="#ddd"/>')
        body.append(f'<text x="{left-12}" y="{y+5}" text-anchor="end" font-family="Arial" font-size="13">{tick:.1f}</text>')
    group = width / len(METHODS)
    for idx, (method, label) in enumerate(zip(METHODS, labels)):
        centre = left + (idx + 0.5) * group
        for offset, metric, colour in [(-17, "dice", "#1261a0"), (17, "iou", "#d1495b")]:
            value = next(float(row["mean"]) for row in summary if row["method"] == method and row["metric"] == metric)
            bar_height = value / 0.6 * height
            body.append(f'<rect x="{centre+offset-14}" y="{top+height-bar_height}" width="28" height="{bar_height}" fill="{colour}"/>')
        body.append(f'<text x="{centre}" y="{top+height+20}" transform="rotate(35 {centre} {top+height+20})" text-anchor="start" font-family="Arial" font-size="12">{label}</text>')
    body.append(f'<rect x="{left+width-145}" y="{top+10}" width="14" height="14" fill="#1261a0"/><text x="{left+width-125}" y="{top+22}" font-family="Arial" font-size="14">Dice</text>')
    body.append(f'<rect x="{left+width-75}" y="{top+10}" width="14" height="14" fill="#d1495b"/><text x="{left+width-55}" y="{top+22}" font-family="Arial" font-size="14">IoU</text>')
    svg_plot(path, "Main method performance (version 8)", "\n".join(body))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    args.freeze.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    source_names = ["ALL_CASE_METHOD_METRICS.csv", "ALL_PCC_ROUND_TRAJECTORIES.csv", "FAILED_CASES.csv", "FULL_RUN_STATUS.json", "LOCKED_CASE_MANIFEST.csv", "LOCKED_FOLD_MANIFEST.csv"]
    hashes = []
    for name in source_names:
        source = args.input / name
        target = args.freeze / name
        if not target.exists():
            shutil.copy2(source, target)
        if sha256(source) != sha256(target):
            raise RuntimeError(f"Frozen copy hash mismatch: {name}")
        hashes.append({"file": name, "sha256": sha256(target), "bytes": target.stat().st_size})
    write_csv(args.freeze / "SOURCE_HASHES.csv", hashes, ["file", "sha256", "bytes"])

    raw = read_csv(args.freeze / "ALL_CASE_METHOD_METRICS.csv")
    trajectory = read_csv(args.freeze / "ALL_PCC_ROUND_TRAJECTORIES.csv")
    fold_rows = read_csv(args.freeze / "LOCKED_FOLD_MANIFEST.csv")
    if read_csv(args.freeze / "FAILED_CASES.csv"):
        raise RuntimeError("Version 8 contains failed cases")
    index = {(row["case_id"], row["method"]): row for row in raw}
    cases = sorted({row["case_id"] for row in raw})
    if len(cases) != 40 or len(index) != 280:
        raise RuntimeError("Expected exactly 40 cases x 7 methods")

    summary = []
    for method in METHODS:
        for metric in METRICS:
            values = np.array([float(index[(case, method)][metric]) for case in cases])
            summary.append({"method": method, "metric": metric, **describe(values, rng)})
    write_csv(args.output / "MAIN_METHOD_SUMMARY.csv", summary, list(summary[0]))

    paired = []
    for reference in ANCHORS:
        for method in METHODS:
            if method == reference:
                continue
            for metric in METRICS:
                a = np.array([float(index[(case, method)][metric]) for case in cases])
                b = np.array([float(index[(case, reference)][metric]) for case in cases])
                diff = a - b
                desc = describe(diff, rng)
                statistic, p_value, nonzero = exact_wilcoxon(diff)
                sd = float(diff.std(ddof=1))
                paired.append({
                    "method": method, "reference_method": reference, "metric": metric,
                    "difference_definition": "method_minus_reference", **desc,
                    "wilcoxon_statistic": statistic, "wilcoxon_p_exact": p_value,
                    "wilcoxon_nonzero_n": nonzero, "holm_adjusted_p": "", "holm_family_size": "",
                    "cohens_dz": float(diff.mean()/sd) if sd else (math.inf if diff.mean() else 0.0),
                    "matched_pairs_rank_biserial": rank_biserial(diff),
                    "wins": int((diff>0).sum()), "ties": int((diff==0).sum()), "losses": int((diff<0).sum()),
                })
    holm(paired)
    write_csv(args.output / "MAIN_PAIRED_STATISTICS.csv", paired, list(paired[0]))

    fixed = {case: float(index[(case,"fixed_baseline")]["dice"]) for case in cases}
    fixed_iou = {case: float(index[(case,"fixed_baseline")]["iou"]) for case in cases}
    by_round: dict[int, list[dict[str,str]]] = defaultdict(list)
    by_case_round: dict[str, dict[int,dict[str,str]]] = defaultdict(dict)
    for row in trajectory:
        rnd=int(row["round"]); by_round[rnd].append(row); by_case_round[row["case_id"]][rnd]=row
    round_summary=[]
    previous_dice=np.array([fixed[c] for c in cases]); previous_iou=np.array([fixed_iou[c] for c in cases])
    for rnd in range(1,11):
        dice=np.array([float(by_case_round[c][rnd]["dice"]) for c in cases]); iou=np.array([float(by_case_round[c][rnd]["iou"]) for c in cases])
        dice_gain=dice-np.array([fixed[c] for c in cases]); iou_gain=iou-np.array([fixed_iou[c] for c in cases])
        for metric,values,gain,increment in [("dice",dice,dice_gain,dice-previous_dice),("iou",iou,iou_gain,iou-previous_iou)]:
            round_summary.append({"round":rnd,"metric":metric,**describe(values,rng),"mean_gain_vs_p0":float(gain.mean()),"mean_increment_vs_previous":float(increment.mean()),"cases_improved_vs_previous":int((increment>0).sum()),"cases_tied_vs_previous":int((increment==0).sum()),"cases_degraded_vs_previous":int((increment<0).sum())})
        previous_dice,previous_iou=dice,iou
    write_csv(args.output/"PCC_ROUND_SUMMARY.csv",round_summary,list(round_summary[0]))

    test_fold={row["case_id"]:row["fold"] for row in fold_rows if row["split"]=="test"}
    case_gain=[]
    for case in cases:
        p0=fixed[case]; pcc=float(index[(case,"pcc_correction")]["dice"]); rounds={r:float(by_case_round[case][r]["dice"]) for r in range(1,11)}
        best=max(rounds,key=rounds.get); p1=rounds[1]; p10=rounds[10]
        case_gain.append({"case_id":case,"fold":test_fold[case],"target_voxels":int(float(index[(case,"fixed_baseline")]["target_voxels"])),"p0_dice":p0,"pcc_p10_dice":pcc,"pcc_minus_p0_dice":pcc-p0,"p1_dice":p1,"p10_minus_p1_dice":p10-p1,"best_round":best,"best_round_dice":rounds[best],"p10_minus_best_dice":p10-rounds[best],"late_degradation":p10 < rounds[best]-1e-12})
    write_csv(args.output/"PCC_CASE_GAIN_ANALYSIS.csv",case_gain,list(case_gain[0]))

    fold_summary=[]
    for fold in sorted({row["fold"] for row in case_gain},key=int):
        subset=[row for row in case_gain if row["fold"]==fold]
        for method in METHODS:
            dice=np.array([float(index[(row["case_id"],method)]["dice"]) for row in subset]); iou=np.array([float(index[(row["case_id"],method)]["iou"]) for row in subset])
            gain=np.array([float(index[(row["case_id"],method)]["dice"])-fixed[row["case_id"]] for row in subset])
            fold_summary.append({"fold":fold,"method":method,"n":len(subset),"dice_mean":float(dice.mean()),"dice_sd":float(dice.std(ddof=1)),"iou_mean":float(iou.mean()),"iou_sd":float(iou.std(ddof=1)),"dice_gain_vs_fixed_mean":float(gain.mean())})
    write_csv(args.output/"FOLD_LEVEL_SUMMARY.csv",fold_summary,list(fold_summary[0]))

    p0=np.array([row["p0_dice"] for row in case_gain],float); gain=np.array([row["pcc_minus_p0_dice"] for row in case_gain],float); target=np.log10(np.array([row["target_voxels"] for row in case_gain],float))
    correlations=[]
    for label,x in [("baseline_p0_dice",p0),("log10_target_voxels",target)]:
        correlations.append({"x":label,"y":"pcc_minus_fixed_dice","spearman_rho":spearman(x,gain),"permutation_p_two_sided":permutation_spearman_p(x,gain,rng),"permutations":20000,"seed":SEED})
    write_csv(args.output/"PCC_GAIN_CORRELATIONS.csv",correlations,list(correlations[0]))

    pub_summary=[row for row in summary if row["metric"] in METRICS]
    write_csv(args.output/"PUBLICATION_TABLE_MAIN_METHODS.csv",pub_summary,list(pub_summary[0]))
    pub_pairs=[row for row in paired if row["method"]=="pcc_correction" and row["reference_method"]!="pcc_correction"]
    write_csv(args.output/"PUBLICATION_TABLE_PCC_COMPARISONS.csv",pub_pairs,list(pub_pairs[0]))
    dice_means=[next(float(r["mean"]) for r in round_summary if r["round"]==rnd and r["metric"]=="dice") for rnd in range(1,11)]
    iou_means=[next(float(r["mean"]) for r in round_summary if r["round"]==rnd and r["metric"]=="iou") for rnd in range(1,11)]
    line_figure(args.output/"FIGURE_PCC_ROUND_CONVERGENCE.svg",list(range(1,11)),dice_means,iou_means)
    method_figure(args.output/"FIGURE_MAIN_METHOD_DICE_IOU.svg", summary)
    scatter_figure(args.output/"FIGURE_BASELINE_VS_PCC_GAIN.svg",p0,gain,"Baseline quality versus PCC gain","Fixed P0 Dice")
    scatter_figure(args.output/"FIGURE_TARGET_SIZE_VS_PCC_GAIN.svg",target,gain,"Target size versus PCC gain","log10 target voxels")

    status=json.loads((args.freeze/"FULL_RUN_STATUS.json").read_text())
    provenance={"experiment":"PCC_LEAKAGE_FREE_RERUN_2026","kaggle_kernel":"jeechangxin/pcc-leakage-free-rerun-2026","kaggle_version":8,"run_git_commit":status["git_commit"],"config_sha256":status["config_sha256"],"case_manifest_sha256":status["case_manifest_sha256"],"fold_manifest_sha256":status["fold_manifest_sha256"],"analysis_seed":SEED,"bootstrap_resamples":BOOTSTRAPS,"source_hashes":hashes}
    (args.freeze/"provenance.json").write_text(json.dumps(provenance,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","output":str(args.output),"freeze":str(args.freeze),"correlations":correlations,"largest_gains":sorted(case_gain,key=lambda r:r["pcc_minus_p0_dice"],reverse=True)[:3],"smallest_gains":sorted(case_gain,key=lambda r:r["pcc_minus_p0_dice"])[:3],"late_degradation_cases":sum(bool(r["late_degradation"]) for r in case_gain)},indent=2))


if __name__ == "__main__":
    main()
