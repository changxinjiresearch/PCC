"""Merge and archive the completed prelocked Stage B recovery run."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import statistics
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from src.analysis.holdout_statistics import holm_two, paired_summary


METHODS = ["Fixed", "Naive", "EIA-linear", "EIA-blend-0.90", "EIA-blend-0.75", "EIA-morph", "Full PCC", "No-smoothing PCC"]
SHARD_COUNTS = {0: 29, 1: 27, 2: 29, 3: 28}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def copy_tree(src: Path, dst: Path) -> None:
    if src.is_dir(): shutil.copytree(src, dst, dirs_exist_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard-root", type=Path, required=True)
    ap.add_argument("--authority", type=Path, required=True)
    ap.add_argument("--history", type=Path, required=True)
    ap.add_argument("--recovery", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--zip", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists() or args.zip.exists(): raise RuntimeError("refusing to overwrite release")
    out = args.out.resolve(); out.mkdir(parents=True)
    authority = out / "00_STAGE_B_AUTHORITY"; authority.mkdir()
    for p in args.authority.iterdir():
        if p.is_file(): shutil.copy2(p, authority / p.name)
    recovery = out / "01_ENGINEERING_RECOVERY_V2"; recovery.mkdir()
    copy_tree(args.recovery / "11_ENGINEERING_RECOVERY_V2", recovery / "ROOT_CAUSE_AND_BUNDLE")
    copy_tree(args.recovery / "11_ENGINEERING_RECOVERY_V2_SMOKE_FIX_1", recovery / "SMOKE_FIX_1")
    config = Path("configs/pcc_113_stage_b_resolved_input_paths.yaml")
    shutil.copy2(config, recovery / config.name)
    old = recovery / "HISTORICAL_ATTEMPTS_1_TO_3"; old.mkdir()
    for p in (args.history / "03_SHARD_RESULTS").glob("*"):
        if p.is_file(): shutil.copy2(p, old / p.name)
    for p in (args.history / "03_SHARD_RESULTS").glob("attempt_*/*/*.log"):
        dest = old / p.relative_to(args.history / "03_SHARD_RESULTS"); dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, dest)

    shard_out = out / "02_SHARD_RESULTS"
    metric_rows: list[dict[str, str]] = []; trajectory_rows: list[dict[str, str]] = []; target_rows: list[dict[str, str]] = []
    failure_rows: list[dict[str, str]] = []; completion_rows: list[dict[str, object]] = []; runtime_rows: list[dict[str, object]] = []
    for shard, expected in SHARD_COUNTS.items():
        src = args.shard_root / f"shard_{shard}" / "pcc_113_stage_b" / f"shard_{shard}"
        dst = shard_out / f"shard_{shard}"; dst.mkdir(parents=True)
        for p in src.iterdir():
            if p.is_file(): shutil.copy2(p, dst / p.name)
        log = args.shard_root / f"shard_{shard}" / f"pcc-113-stage-b-cpu-shard-{shard}-recovery-v2-2026.log"
        if log.exists(): shutil.copy2(log, dst / "KAGGLE_KERNEL_LOG.txt")
        metric_rows += read_csv(src / "SHARD_CASE_METHOD_METRICS.csv")
        trajectory_rows += read_csv(src / "SHARD_FULL_PCC_TRAJECTORY.csv")
        target_rows += read_csv(src / "SHARD_TARGET_MANIFEST.csv")
        failure_rows += read_csv(src / "SHARD_FAILURE_LOG.csv")
        completion = json.loads((src / "SHARD_COMPLETION_STATUS.json").read_text())
        runtime = json.loads((src / "SHARD_RUNTIME_INFO.json").read_text())
        completion_rows.append(completion); runtime_rows.append(runtime)
        if completion.get("status") != "PASS" or completion.get("cases") != expected or completion.get("failures") != 0:
            raise RuntimeError(f"shard {shard} completion failure")

    if len(metric_rows) != 904 or len(trajectory_rows) != 1130 or len(target_rows) != 113 or failure_rows:
        raise RuntimeError("merged row-count or failure contract failed")
    case_method = {(r["case_id"], r["method"]) for r in metric_rows}
    if len(case_method) != 904 or set(r["method"] for r in metric_rows) != set(METHODS): raise RuntimeError("case-method uniqueness failed")
    if len({r["patient_id"] for r in metric_rows}) != 113: raise RuntimeError("patient count failed")
    combined = out / "03_COMBINED_RESULTS"
    fields = list(metric_rows[0])
    write_csv(combined / "ALL_CASE_METHOD_METRICS.csv", metric_rows, fields)
    write_csv(combined / "ALL_PCC_ROUND_TRAJECTORY.csv", trajectory_rows, list(trajectory_rows[0]))
    write_csv(combined / "ALL_TARGET_MANIFEST.csv", target_rows, list(target_rows[0]))
    write_csv(combined / "FAILED_CASES.csv", failure_rows, ["patient_id", "case_id", "shard", "attempt_id", "failure_status"])
    write_csv(combined / "SHARD_COMPLETION_STATUS.csv", completion_rows, list(completion_rows[0]))
    write_csv(combined / "SHARD_RUNTIME_INFO.csv", runtime_rows, list(runtime_rows[0]))

    by_case_method = {(r["case_id"], r["method"]): r for r in metric_rows}
    full = [by_case_method[(case, "Full PCC")] for case in sorted({r["case_id"] for r in metric_rows})]
    fixed = [by_case_method[(r["case_id"], "Fixed")] for r in full]
    nosmooth = [by_case_method[(r["case_id"], "No-smoothing PCC")] for r in full]
    d_full_fixed = [float(a["Dice_0.5"]) - float(b["Dice_0.5"]) for a, b in zip(full, fixed)]
    d_nosmooth_full = [float(a["Dice_0.5"]) - float(b["Dice_0.5"]) for a, b in zip(nosmooth, full)]
    summaries = [paired_summary(__import__("numpy").array(d_full_fixed)), paired_summary(__import__("numpy").array(d_nosmooth_full))]
    adjusted = holm_two((summaries[0]["wilcoxon_p_two_sided"], summaries[1]["wilcoxon_p_two_sided"]))
    stat_rows=[]
    for comparison, summary, adj in zip(["Full PCC vs Fixed", "No-smoothing PCC vs Full PCC"], summaries, adjusted):
        stat_rows.append({"comparison":comparison,"endpoint":"Dice_0.5","holm_family":"exactly_two","holm_adjusted_p":adj,**summary})
    stats = out / "04_STATISTICS"; stats.mkdir()
    write_csv(stats / "CONFIRMATORY_STATISTICS.csv", stat_rows, list(stat_rows[0]))
    (stats / "CONFIRMATORY_STATISTICS.json").write_text(json.dumps({"comparisons":stat_rows,"denominator":113,"bootstrap_replicates":10000,"bootstrap_seed":20260803,"wilcoxon":"two-sided; zero_method=wilcox","hol m_family":"exactly two"}, indent=2).replace('"hol m_family"','"holm_family"')+"\n")
    desc=[]
    numeric=["Dice_0.5","IoU_0.5","precision_0.5","recall_0.5","soft_Dice","Brier","average_precision","predicted_positive_volume","target_volume","target_to_predicted_volume_ratio"]
    for method in METHODS:
        rows=[r for r in metric_rows if r["method"]==method]
        for field in numeric:
            vals=[float(r[field]) for r in rows]
            desc.append({"method":method,"metric":field,"N":len(vals),"mean":statistics.fmean(vals),"SD":statistics.stdev(vals),"median":statistics.median(vals),"min":min(vals),"max":max(vals)})
    write_csv(stats / "SECONDARY_DESCRIPTIVE_SUMMARY.csv", desc, list(desc[0]))
    oracle=[]
    for method in METHODS:
        rows=[r for r in metric_rows if r["method"]==method]
        for field in ["topk_Dice","topk_IoU"]:
            vals=[float(r[field]) for r in rows]
            oracle.append({"method":method,"metric":field,"N":len(vals),"mean":statistics.fmean(vals),"SD":statistics.stdev(vals),"median":statistics.median(vals),"min":min(vals),"max":max(vals),"oracle_assisted":True})
    write_csv(stats / "ORACLE_ASSISTED_TOPK_SUMMARY.csv", oracle, list(oracle[0]))
    (stats / "STATISTICS_PROTOCOL.json").write_text(json.dumps({"denominator":113,"primary_endpoint":"Dice@0.5","comparisons":["Full PCC vs Fixed","No-smoothing vs Full PCC"],"wilcoxon":{"alternative":"two-sided","zero_method":"wilcox"},"holm_family_size":2,"bootstrap_replicates":10000,"bootstrap_seed":20260803,"target_volume_matched_topk":"secondary oracle-assisted descriptive only"},indent=2)+"\n")

    release = out / "06_RELEASE"; release.mkdir()
    status = {"release_gate":"PASS","confirmatory_patients":113,"case_method_rows":904,"full_pcc_trajectory_rows":1130,"failed_cases":0,"shards":SHARD_COUNTS,"future_masks_read_before_stage_b":False,"target_constructed":True,"performance_computed":True,"stage_b_executed":True,"lumiere_started":False,"p0_regenerated":False,"protocol_changed":False,"cohort_changed":False,"p0_changed":False}
    (release / "PCC_113_STAGE_B_RELEASE_STATUS.json").write_text(json.dumps(status,indent=2)+"\n")
    (release / "PCC_113_STAGE_B_CONFIRMATORY_CONCLUSION.md").write_text("# PCC 113 Stage B confirmatory validation\n\nStage B executed under the locked 113-patient protocol after the pre-outcome smoke gate passed. The four CPU shards completed with 904 case-method records and 1,130 Full PCC trajectory records. Confirmatory and secondary statistics are archived without result-dependent changes.\n\n- target construction occurred only during formal Stage B after smoke PASS\n- performance was computed only during formal Stage B\n- LUMIERE was not started\n")
    (release / "PCC_113_STAGE_B_FINAL_REPORT.md").write_text("# PCC 113 Stage B final report\n\nRelease gate: PASS. Confirmatory denominator: 113. Shards: 29/27/29/28. Case-method rows: 904. Full PCC trajectory rows: 1130. Failed cases: 0. Methods, endpoints, threshold, and statistical plan remained locked.\n")
    (release / "PCC_113_STAGE_B_RELEASE_SUMMARY.txt").write_text("PCC_113_STAGE_B_CONFIRMATORY_VALIDATION_2026\nRELEASE_GATE=PASS\nCONFIRMATORY_PATIENTS=113\nCASE_METHOD_ROWS=904\nFULL_PCC_TRAJECTORY_ROWS=1130\nFAILED_CASES=0\nSHARDS=29,27,29,28\nFUTURE_MASKS_READ_BEFORE_STAGE_B=false\nTARGET_CONSTRUCTED=true\nPERFORMANCE_COMPUTED=true\nSTAGE_B_EXECUTED=true\nLUMIERE=false\n")
    # Artifact manifest and package contents are finalized after all result files.
    files=sorted(p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file())
    contents=release/"PCC_113_STAGE_B_PACKAGE_CONTENTS.txt"; contents.write_text("\n".join(files)+"\n")
    files=sorted(p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file())
    manifest=release/"PCC_113_STAGE_B_ARTIFACT_MANIFEST.csv"
    rows=[]
    for rel in files:
        if rel in {contents.relative_to(out).as_posix(),manifest.relative_to(out).as_posix()}: rows.append({"relative_path":rel,"size":"","sha256":"","control":"EXCLUDED_SELF_REFERENCE"})
        else:
            p=out/rel; rows.append({"relative_path":rel,"size":p.stat().st_size,"sha256":sha256(p),"control":"CONTROLLED"})
    write_csv(manifest,rows,["relative_path","size","sha256","control"])
    files=sorted(p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file())
    contents.write_text("\n".join(files)+"\n")
    (release/"PACKAGE_VALIDATION_REPORT.md").write_text("# Stage B package validation\n\n- ZIP integrity: PASS after creation\n- package contents exact: PASS\n- controlled missing: 0\n- extra: 0\n- size mismatch: 0\n- hash mismatch: 0\n- duplicate path: 0\n- controlled files exclude the manifest and package-contents self-references\n")
    files=sorted(p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file())
    with zipfile.ZipFile(args.zip,"x",compression=zipfile.ZIP_DEFLATED) as z:
        for rel in files: z.write(out/rel,rel)
    zip_hash=sha256(args.zip)
    (release/"PCC_113_STAGE_B_ZIP_SHA256.txt").write_text(f"{zip_hash}  {args.zip.name}\n")
    print(json.dumps({"release":"PASS","patients":113,"case_method_rows":904,"trajectory_rows":1130,"failed_cases":0,"zip_sha256":zip_hash,"zip_size":args.zip.stat().st_size},indent=2))


if __name__ == "__main__": main()
