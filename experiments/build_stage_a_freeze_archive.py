#!/usr/bin/env python3
"""Build the small Stage A audit archive; large P0 files remain in Kaggle output."""
from __future__ import annotations
import argparse, csv, hashlib, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def copytree(src,dst): dst.mkdir(parents=True,exist_ok=True); [shutil.copy2(p,dst/p.name) for p in src.iterdir() if p.is_file()]
def main():
 p=argparse.ArgumentParser(); p.add_argument('--kernel-output',type=Path,required=True); p.add_argument('--kernel-log',type=Path,required=True); p.add_argument('--output-root',type=Path,default=ROOT/'outputs/pcc_115_holdout_stage_a_p0_freeze_2026'); a=p.parse_args(); out=a.output_root; out.mkdir(parents=True,exist_ok=True); ko=a.kernel_output
 for name in ['00_STAGE_A_AUTHORITY','01_PRE_INFERENCE_AUDIT','06_P0_FREEZE_MANIFEST','07_ACCESS_AUDIT','08_FAILURE_AND_ATTEMPT_LOG','10_STAGE_A_RELEASE']:
  copytree(ko/name,out/name)
 (out/'09_TESTS/saved_test_outputs').mkdir(parents=True,exist_ok=True); shutil.copy2(a.kernel_log,out/'09_TESTS/saved_test_outputs/GPU_KERNEL_LOG.txt')
 (out/'09_TESTS').mkdir(parents=True,exist_ok=True); shutil.copy2(ROOT/'experiments/stage_a_freeze_static_tests.py',out/'09_TESTS/stage_a_freeze_static_tests.py')
 protocol=ROOT/'outputs/pcc_115_holdout_protocol_lock_2026'
 (out/'00_STAGE_A_AUTHORITY/PROTOCOL_LOCK').mkdir(parents=True,exist_ok=True)
 for f in ['PCC_115_HOLDOUT_PROTOCOL.md','PCC_115_HOLDOUT_PROTOCOL.yaml','PCC_115_PROTOCOL_HASH_LOCK.json','LOCKED_115_STAGE_A_P0_SHARD_MANIFEST.csv','LOCKED_115_CHECKPOINT_MANIFEST.csv','LOCKED_115_PREDICTOR_CONFIG.yaml','LOCKED_115_ENSEMBLE_POLICY.yaml']:
  src=protocol/'11_PROTOCOL_RELEASE'/f if f.startswith('PCC_115_HOLDOUT_PROTOCOL') or f=='PCC_115_PROTOCOL_HASH_LOCK.json' else protocol/'09_EXECUTION_PLAN'/f if 'SHARD' in f else protocol/'03_PREDICTOR_LOCK'/f
  if src.exists(): shutil.copy2(src,out/'00_STAGE_A_AUTHORITY/PROTOCOL_LOCK'/f)
 (out/'00_STAGE_A_AUTHORITY/PROTOCOL_LOCK_SHA256.txt').write_text('34ebddc1a512867f293b30d68c1dc6663a45092dcdcef9c317fd5ca9da239b34  PCC_115_HOLDOUT_PROTOCOL_LOCK_2026.zip\n')
 (out/'00_STAGE_A_AUTHORITY/STORAGE_LOCATION.txt').write_text('storage_type=Kaggle kernel output\nkernel_slug=jeechangxin/pcc-115-holdout-stage-a-p0-freeze-2026\nkernel_version=2\np0_root=/kaggle/working/pcc_115_holdout_stage_a_p0_freeze_2026\nlarge_p0_files_excluded_from_local_audit_zip=true\n')
 (out/'10_STAGE_A_RELEASE/PCC_115_STAGE_A_RELEASE_SUMMARY.txt').write_text('Stage A P0 maps are frozen in the referenced Kaggle kernel output version. This local ZIP contains audit metadata and hashes, not the large P0 arrays. Stage B is not started.\n')
 print(out)
if __name__=='__main__': main()
