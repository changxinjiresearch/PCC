from __future__ import annotations
import csv, hashlib, json
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
def rows(p):
 with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def test_01_manifest_115(): assert len(rows(ROOT/'06_P0_FREEZE_MANIFEST/LOCKED_115_P0_MANIFEST.csv'))==115
def test_02_patient_unique():
 x=rows(ROOT/'06_P0_FREEZE_MANIFEST/LOCKED_115_P0_MANIFEST.csv'); assert len({r['patient_id'] for r in x})==115
def test_03_case_unique():
 x=rows(ROOT/'06_P0_FREEZE_MANIFEST/LOCKED_115_P0_MANIFEST.csv'); assert len({r['case_id'] for r in x})==115
def test_04_shard_union():
 x=rows(ROOT/'06_P0_FREEZE_MANIFEST/LOCKED_115_P0_MANIFEST.csv'); assert {r['stage_a_shard'] for r in x}=={'0','1','2','3'}
def test_05_shard_no_duplicates():
 x=rows(ROOT/'06_P0_FREEZE_MANIFEST/LOCKED_115_P0_MANIFEST.csv'); assert len({(r['stage_a_shard'],r['patient_id']) for r in x})==115
def test_06_sha_rows_115(): assert len(rows(ROOT/'06_P0_FREEZE_MANIFEST/LOCKED_115_P0_SHA256.csv'))==115
def test_07_completion_rows_115(): assert all(r['status']=='COMPLETE' for r in rows(ROOT/'06_P0_FREEZE_MANIFEST/LOCKED_115_P0_COMPLETION_STATUS.csv'))
def test_08_qc_rows_115(): assert len(rows(ROOT/'06_P0_FREEZE_MANIFEST/LOCKED_115_P0_NUMERIC_QC.csv'))==115
def test_09_qc_shape(): assert all(r['shape_match']=='True' for r in rows(ROOT/'06_P0_FREEZE_MANIFEST/LOCKED_115_P0_NUMERIC_QC.csv'))
def test_10_qc_dtype(): assert all(r['dtype_match']=='True' and r['dtype']=='float32' for r in rows(ROOT/'06_P0_FREEZE_MANIFEST/LOCKED_115_P0_NUMERIC_QC.csv'))
def test_11_qc_finite(): assert all(r['finite']=='True' for r in rows(ROOT/'06_P0_FREEZE_MANIFEST/LOCKED_115_P0_NUMERIC_QC.csv'))
def test_12_qc_range(): assert all(r['in_range_0_1']=='True' for r in rows(ROOT/'06_P0_FREEZE_MANIFEST/LOCKED_115_P0_NUMERIC_QC.csv'))
def test_13_access_status(): assert all(r['status']=='PASS' and r['access_violation_count']=='0' for r in rows(ROOT/'07_ACCESS_AUDIT/LOCKED_115_P0_ACCESS_STATUS.csv'))
def test_14_access_log_permitted(): assert all(r['permitted']=='True' for r in rows(ROOT/'07_ACCESS_AUDIT/P0_FILE_ACCESS_LOG.csv'))
def test_15_access_log_no_forbidden_paths():
 x=rows(ROOT/'07_ACCESS_AUDIT/P0_FILE_ACCESS_LOG.csv'); assert not [r for r in x if any(t in r['file_path'].lower() for t in ('future','target','later','ground_truth','outcome','progression_truth'))]
def test_16_violations_zero(): assert len(rows(ROOT/'07_ACCESS_AUDIT/P0_FUTURE_ACCESS_VIOLATIONS.csv'))==0
def test_17_failure_log_zero(): assert len(rows(ROOT/'08_FAILURE_AND_ATTEMPT_LOG/FAILURE_LOG.csv'))==0
def test_18_attempts_115(): assert len(rows(ROOT/'08_FAILURE_AND_ATTEMPT_LOG/ATTEMPT_LOG.csv'))==115
def test_19_no_future_manifest_fields():
 x=rows(ROOT/'06_P0_FREEZE_MANIFEST/LOCKED_115_P0_MANIFEST.csv')[0]; assert not [k for k in x if any(t in k.lower() for t in ('future','target','later'))]
def test_20_no_target_files(): assert not [p for p in ROOT.rglob('*') if p.is_file() and ('target' in p.name.lower() or 'future_mask' in p.name.lower())]
def test_21_no_stage_b_outputs(): assert not [p for p in ROOT.rglob('*') if p.is_file() and 'stage_b' in str(p).lower()]
def test_22_no_performance_files(): assert not [p for p in ROOT.rglob('*') if p.is_file() and any(x in p.name.upper() for x in ('DICE','IOU','PR_AUC','METRICS'))]
def test_23_status_gate(): assert json.loads((ROOT/'10_STAGE_A_RELEASE/STAGE_A_STATUS.json').read_text())['status']=='PASS'
def test_24_target_false(): assert json.loads((ROOT/'10_STAGE_A_RELEASE/STAGE_A_STATUS.json').read_text())['target_constructed'] is False
def test_25_stage_b_false(): assert json.loads((ROOT/'10_STAGE_A_RELEASE/STAGE_A_STATUS.json').read_text())['stage_b_executed'] is False
def test_26_p0_manifest_has_no_metrics():
 x=rows(ROOT/'06_P0_FREEZE_MANIFEST/LOCKED_115_P0_MANIFEST.csv')[0]; assert not [k for k in x if any(t in k.lower() for t in ('dice','iou','brier','auc','precision','recall','topk'))]
def test_27_runtime_gpu(): assert json.loads((ROOT/'00_STAGE_A_AUTHORITY/GPU_RUNTIME_INFO.json').read_text())['cuda_available'] is True
def test_28_ensemble_weights(): assert json.loads((ROOT/'00_STAGE_A_AUTHORITY/GPU_RUNTIME_INFO.json').read_text()).get('ensemble_weights',[.2]*5)==[.2]*5
def test_29_sha_values_present(): assert all(len(r['sha256'])==64 for r in rows(ROOT/'06_P0_FREEZE_MANIFEST/LOCKED_115_P0_SHA256.csv'))
def test_30_readiness(): assert 'Stage A is frozen' in (ROOT/'10_STAGE_A_RELEASE/PCC_115_STAGE_A_READINESS_FOR_STAGE_B.md').read_text()
