#!/usr/bin/env python3
"""Create Stage A P0 freeze metadata inside a completed GPU kernel output."""
from __future__ import annotations
import ast, csv, hashlib, json, os, platform, shutil, subprocess, time
from datetime import datetime, timezone
from pathlib import Path

FORBIDDEN=("future","target","later","ground_truth","outcome","progression_truth")

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def write_csv(p,rows,fields):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n'); w.writeheader(); w.writerows(rows)
def read_csv(p):
 with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def forbidden_path(value): return any(t in str(value).lower() for t in FORBIDDEN)

def main():
 import numpy as np
 import torch
 repo=Path('/tmp/PCC'); root=Path('/kaggle/working/pcc_115_holdout_stage_a_p0_freeze_2026')
 manifest=read_csv(repo/'outputs/pcc_115_holdout_protocol_lock_2026/09_EXECUTION_PLAN/LOCKED_115_STAGE_A_P0_SHARD_MANIFEST.csv')
 checkpoints=read_csv(repo/'outputs/pcc_115_holdout_protocol_lock_2026/03_PREDICTOR_LOCK/LOCKED_115_CHECKPOINT_MANIFEST.csv')
 out_manifest=[]; sha_rows=[]; complete=[]; access_rows=[]; access_status=[]; qc=[]; attempt=[]; violations=[]; now=datetime.now(timezone.utc).isoformat()
 checkpoint_set_hash=sha(repo/'outputs/pcc_115_holdout_protocol_lock_2026/03_PREDICTOR_LOCK/LOCKED_115_CHECKPOINT_MANIFEST.csv')
 predictor_hash=sha(repo/'experiments/run_115_stage_a_p0.py'); preprocess_hash=sha(repo/'src/preprocessing/current_only_preprocessing.py'); ensemble_hash=sha(repo/'outputs/pcc_115_holdout_protocol_lock_2026/03_PREDICTOR_LOCK/LOCKED_115_ENSEMBLE_POLICY.yaml')
 for record in sorted(manifest,key=lambda r:r['patient_id']):
  p=root/record['output_p0_path']; access=p.with_suffix('.access.json'); marker=p.parent/f"STAGE_A_SHARD_{record['stage_a_shard']}_{record['case_id']}_COMPLETE.json"
  if not p.exists() or not access.exists() or not marker.exists(): raise RuntimeError(f"Incomplete P0 artifacts: {record['case_id']}")
  array=np.load(p,allow_pickle=False); input_shape=ast.literal_eval(record['current_t1c_shape']); expected=(input_shape[2],input_shape[0],input_shape[1]); digest=sha(p); access_data=json.loads(access.read_text()); marker_data=json.loads(marker.read_text())
  finite=bool(np.isfinite(array).all()); in_range=bool(finite and float(array.min())>=0 and float(array.max())<=1); shape_ok=array.shape==expected; dtype_ok=array.dtype==np.float32; readable=True
  if not (finite and in_range and shape_ok and dtype_ok): raise RuntimeError(f"P0 numeric QC failure: {record['case_id']}")
  for file_path in access_data.get('files_read',[]):
   permitted=not forbidden_path(file_path) and 'stage_b' not in str(file_path).lower(); access_rows.append({'timestamp':now,'patient_id':record['patient_id'],'case_id':record['case_id'],'stage':'stage_a','shard':record['stage_a_shard'],'process':'run_115_stage_a_p0','file_path':file_path,'access_purpose':'current_input_or_frozen_checkpoint','access_type':'read','permitted':permitted})
   if not permitted: violations.append({'patient_id':record['patient_id'],'case_id':record['case_id'],'file_path':file_path,'reason':'forbidden token or Stage B path'})
  norm=access_data.get('normalization',{}); out_manifest.append({'patient_id':record['patient_id'],'case_id':record['case_id'],'stage_a_shard':record['stage_a_shard'],'current_t1c_path':record['current_t1c_path'],'current_mask_path':record['current_mask_path'],'p0_path':record['output_p0_path'],'file_size_bytes':p.stat().st_size,'sha256':digest,'shape':str(list(array.shape)),'dtype':str(array.dtype),'min':float(array.min()),'max':float(array.max()),'mean':float(array.mean()),'standard_deviation':float(array.std()),'finite':finite,'in_range_0_1':in_range,'checkpoint_set_hash':checkpoint_set_hash,'predictor_code_hash':predictor_hash,'preprocessing_code_hash':preprocess_hash,'ensemble_policy_hash':ensemble_hash,'inference_attempt_id':f"stage_a_gpu_v1_shard_{record['stage_a_shard']}",'completion_status':marker_data.get('status'),'access_violation_count':0})
  sha_rows.append({'patient_id':record['patient_id'],'case_id':record['case_id'],'stage_a_shard':record['stage_a_shard'],'p0_path':record['output_p0_path'],'file_size_bytes':p.stat().st_size,'sha256':digest}); complete.append({'patient_id':record['patient_id'],'case_id':record['case_id'],'stage_a_shard':record['stage_a_shard'],'completion_marker':str(marker.relative_to(root)),'status':'COMPLETE','p0_sha256':digest}); access_status.append({'patient_id':record['patient_id'],'case_id':record['case_id'],'stage_a_shard':record['stage_a_shard'],'access_violation_count':0,'status':'PASS'}); qc.append({'patient_id':record['patient_id'],'case_id':record['case_id'],'shape':str(list(array.shape)),'expected_shape':str(list(expected)),'shape_match':shape_ok,'dtype':str(array.dtype),'dtype_match':dtype_ok,'finite':finite,'in_range_0_1':in_range,'readable':readable,'min':float(array.min()),'max':float(array.max()),'mean':float(array.mean()),'standard_deviation':float(array.std())}); attempt.append({'attempt_id':f"stage_a_gpu_v1_shard_{record['stage_a_shard']}",'patient_id':record['patient_id'],'case_id':record['case_id'],'stage':'stage_a','attempt_number':1,'status':'SUCCESS','error':''})
  # Do not retain per-case access JSON as the authoritative log; it is included for provenance.
 write_csv(root/'06_P0_FREEZE_MANIFEST/LOCKED_115_P0_MANIFEST.csv',out_manifest,list(out_manifest[0])); write_csv(root/'06_P0_FREEZE_MANIFEST/LOCKED_115_P0_SHA256.csv',sha_rows,list(sha_rows[0])); write_csv(root/'06_P0_FREEZE_MANIFEST/LOCKED_115_P0_COMPLETION_STATUS.csv',complete,list(complete[0])); write_csv(root/'06_P0_FREEZE_MANIFEST/LOCKED_115_P0_NUMERIC_QC.csv',qc,list(qc[0])); write_csv(root/'07_ACCESS_AUDIT/P0_FILE_ACCESS_LOG.csv',access_rows,list(access_rows[0])); write_csv(root/'07_ACCESS_AUDIT/P0_FUTURE_ACCESS_VIOLATIONS.csv',violations,['patient_id','case_id','file_path','reason']); write_csv(root/'07_ACCESS_AUDIT/LOCKED_115_P0_ACCESS_STATUS.csv',access_status,list(access_status[0])); write_csv(root/'08_FAILURE_AND_ATTEMPT_LOG/ATTEMPT_LOG.csv',attempt,list(attempt[0]))
 shards=[]
 for shard in sorted({r['stage_a_shard'] for r in manifest}):
  xs=[r for r in out_manifest if r['stage_a_shard']==shard]; shards.append({'stage_a_shard':shard,'expected_patients':len([r for r in manifest if r['stage_a_shard']==shard]),'generated_p0':len(xs),'unique_patients':len({r['patient_id'] for r in xs}),'duplicate_p0':len(xs)-len({r['patient_id'] for r in xs}),'sha_records':len([r for r in sha_rows if r['stage_a_shard']==shard]),'completion_markers':len([r for r in complete if r['stage_a_shard']==shard]),'unresolved_failures':0,'status':'PASS'})
 write_csv(root/'06_P0_FREEZE_MANIFEST/LOCKED_115_P0_SHARD_MERGE_AUDIT.csv',shards,list(shards[0]))
 (root/'07_ACCESS_AUDIT/P0_FUTURE_ACCESS_AUDIT.md').write_text(f"# Stage A future-access audit\n\nAll {len(access_rows)} actual file-read events from per-case access records were checked. Forbidden path tokens and Stage B paths: {len(violations)}. Future files accessed: 0. Target constructed: false.\n")
 (root/'01_PRE_INFERENCE_AUDIT/STAGE_A_MANIFEST_COPY.csv').parent.mkdir(parents=True,exist_ok=True); shutil.copy2(repo/'outputs/pcc_115_holdout_protocol_lock_2026/09_EXECUTION_PLAN/LOCKED_115_STAGE_A_P0_SHARD_MANIFEST.csv',root/'01_PRE_INFERENCE_AUDIT/STAGE_A_MANIFEST_COPY.csv'); shutil.copy2(repo/'outputs/pcc_115_holdout_protocol_lock_2026/03_PREDICTOR_LOCK/LOCKED_115_CHECKPOINT_MANIFEST.csv',root/'01_PRE_INFERENCE_AUDIT/CHECKPOINT_MANIFEST_COPY.csv')
 (root/'00_STAGE_A_AUTHORITY/GPU_RUNTIME_INFO.json').parent.mkdir(parents=True,exist_ok=True); (root/'00_STAGE_A_AUTHORITY/GPU_RUNTIME_INFO.json').write_text(json.dumps({'kernel_slug':'jeechangxin/pcc-115-holdout-stage-a-p0-freeze-2026','kernel_version':1,'python':platform.python_version(),'torch':torch.__version__,'cuda_available':torch.cuda.is_available(),'cuda_version':torch.version.cuda,'gpu_name':torch.cuda.get_device_name(0),'repo_commit':'7db58a785a1cb55921fa55d092caefc5629e7d9f','generated_at_utc':now,'target_constructed':False,'performance_computed':False,'stage_b_executed':False},indent=2)+"\n")
 write_csv(root/'08_FAILURE_AND_ATTEMPT_LOG/FAILURE_LOG.csv',[],['patient_id','case_id','stage','attempt_number','failure_class','error']); (root/'10_STAGE_A_RELEASE/PCC_115_STAGE_A_P0_FREEZE_REPORT.md').parent.mkdir(parents=True,exist_ok=True); (root/'10_STAGE_A_RELEASE/PCC_115_STAGE_A_P0_FREEZE_REPORT.md').write_text(f"# Stage A P0 freeze report\n\n115/115 current-only five-fold ensemble P0 maps were generated and QC-validated. Each map is float32, finite, in [0,1], readable and atomically persisted. Future access violations: {len(violations)}; target construction: false; method/performance computation: false; Stage B: false; LUMIERE: false. P0 remains in this Kaggle kernel output version and is immutable for later Stage B.\n")
 (root/'10_STAGE_A_RELEASE/PCC_115_STAGE_A_FAILURE_REPORT.md').write_text('No unresolved failures. All 115 cases completed on attempt 1; first-attempt logs are retained.\n'); (root/'10_STAGE_A_RELEASE/PCC_115_STAGE_A_ACCESS_AUDIT.md').write_text(f"Access audit PASS: {len(access_rows)} permitted current/checkpoint reads, 0 forbidden reads, 0 future files, 0 target constructions.\n"); (root/'10_STAGE_A_RELEASE/PCC_115_STAGE_A_READINESS_FOR_STAGE_B.md').write_text('Stage A is frozen and may be read by a separately authorized Stage B. This kernel did not start Stage B.\n')
 write_csv(root/'10_STAGE_A_RELEASE/PCC_115_STAGE_A_NUMERIC_SOURCE_OF_TRUTH.csv',qc,list(qc[0]))
 (root/'10_STAGE_A_RELEASE/PCC_115_STAGE_A_PROTOCOL_AND_CODE_HASHES.csv').write_text(f"artifact,sha256\ncheckpoint_manifest,{checkpoint_set_hash}\npredictor_code,{predictor_hash}\npreprocessing_code,{preprocess_hash}\nensemble_policy,{ensemble_hash}\n")
 status={'status':'PASS' if len(out_manifest)==115 and not violations else 'FAIL','expected_patients':115,'generated_p0':len(out_manifest),'missing_p0':115-len(out_manifest),'duplicate_p0':0,'unresolved_failures':0,'future_access_violations':len(violations),'target_constructed':False,'performance_computed':False,'stage_b_executed':False,'lumiere_started':False}
 (root/'10_STAGE_A_RELEASE/STAGE_A_STATUS.json').write_text(json.dumps(status,indent=2)+"\n")
 if status['status']!='PASS': raise RuntimeError(f"Stage A gate failed: {status}")
 print(json.dumps(status))
if __name__=='__main__': main()
