from __future__ import annotations
import ast, csv, hashlib, inspect, json
from pathlib import Path
import numpy as np
import pytest

from experiments.run_115_stage_a_p0 import ENSEMBLE_WEIGHTS, equal_weight_average, parser, run_case_with_predictors, validate_current_only_record
from src.analysis.holdout_statistics import holm_two, paired_summary
from src.analysis.internal_completion import ETA, RADIUS, ROUNDS, SIGMA, run_variant
from src.analysis.validity_patch import average_precision_binary, target_independent_metrics
from src.evaluation.metrics import topk_mask
from src.models.eia import EIA_ALPHA,EIA_BETA,EIA_BLEND_LAMBDA_075,EIA_BLEND_LAMBDA_090,MIN_COMPONENT_SIZE,THRESHOLD
from src.models.naive_self_tightening import NAIVE_GAMMA
from src.models.pcc import apply_pcc
from src.preprocessing.current_only_preprocessing import construct_future_change_label, normalize_current_t1c

ROOT=Path('outputs/pcc_115_holdout_protocol_lock_2026'); C=ROOT/'01_COHORT_LOCK'
def rows(p):
 with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def test_01_source_count_203(): assert len(rows(C/'ALL_SOURCE_PATIENTS.csv'))==203
def test_02_eligible_count_155(): assert len(rows(C/'ALL_ELIGIBLE_PATIENT_LEVEL_PAIRS.csv'))==155
def test_03_locked40_count_40(): assert len(rows(C/'LOCKED_40_PATIENT_IDS.csv'))==40
def test_04_locked115_count_115(): assert len(rows(C/'LOCKED_115_CASE_MANIFEST.csv'))==115
def test_05_overlap_zero(): assert {r['patient_id'] for r in rows(C/'LOCKED_40_PATIENT_IDS.csv')}.isdisjoint({r['patient_id'] for r in rows(C/'LOCKED_115_CASE_MANIFEST.csv')})
def test_06_one_pair_per_patient():
 x=rows(C/'LOCKED_115_CASE_MANIFEST.csv'); assert len({r['patient_id'] for r in x})==len(x)
def test_07_case_ids_unique():
 x=rows(C/'LOCKED_115_CASE_MANIFEST.csv'); assert len({r['case_id'] for r in x})==115
def test_08_pair_ranks_complete(): assert sorted(int(r['pair_selection_rank']) for r in rows(C/'ALL_ELIGIBLE_PATIENT_LEVEL_PAIRS.csv'))==list(range(1,156))
def test_09_p0_manifest_no_future_columns(): assert not [c for c in rows(C/'P0_INFERENCE_MANIFEST.csv')[0] if any(t in c.lower() for t in ('future','target','later'))]
def test_10_p0_manifest_no_future_paths():
 for r in rows(C/'P0_INFERENCE_MANIFEST.csv'):
  assert all('future' not in v.lower() and 'later' not in v.lower() for v in r.values())
def test_11_runner_rejects_future_record():
 with pytest.raises(ValueError): validate_current_only_record({'future_mask_path':'x'})
def test_12_runner_parser_rejects_future_argument():
 with pytest.raises(SystemExit): parser().parse_args(['--future-mask','x'])
def test_13_current_only_normalization():
 x=np.arange(200,dtype=np.float32).reshape(10,10,2); y=normalize_current_t1c(x); assert y.dtype==np.float32 and y.min()>=0 and y.max()<=1
def test_14_checkpoint_hashes_pass(): assert len(rows(ROOT/'03_PREDICTOR_LOCK/CHECKPOINT_STATE_DICT_AUDIT.csv'))==5 and all(r['hash_status']=='PASS' for r in rows(ROOT/'03_PREDICTOR_LOCK/CHECKPOINT_STATE_DICT_AUDIT.csv'))
def test_15_checkpoint_state_dict_compatible():
 x=rows(ROOT/'03_PREDICTOR_LOCK/CHECKPOINT_STATE_DICT_AUDIT.csv'); assert all(r['cpu_load_status']=='PASS' and r['strict_load_status']=='PASS' and r['missing_keys']=='0' and r['unexpected_keys']=='0' and r['parameter_shape_mismatch']=='0' for r in x)
def test_16_ensemble_weights(): assert ENSEMBLE_WEIGHTS==(0.2,)*5 and sum(ENSEMBLE_WEIGHTS)==1
def test_17_equal_weight_average(): assert np.allclose(equal_weight_average([np.full((2,2),i,dtype=np.float32) for i in range(5)]),2)
def test_18_full_pcc_constants(): assert (ROUNDS,ETA,RADIUS,SIGMA)==(10,0.30,26.0,2.0)
def test_19_full_variant_matches_canonical():
 p=np.linspace(.1,.9,125,dtype=np.float32).reshape(5,5,5); t=np.zeros_like(p,bool); t[2,2,2]=1
 assert np.allclose(run_variant(p,t,smoothing=True).probability,apply_pcc(p,t).corrected_probability,atol=1e-7)
def test_20_no_smoothing_single_branch_ast():
 tree=ast.parse(Path('src/analysis/internal_completion.py').read_text()); tests=[n for n in ast.walk(tree) if isinstance(n,ast.IfExp) and isinstance(n.test,ast.Name) and n.test.id=='smoothing']; assert len(tests)==1
def test_21_target_construction():
 c=np.array([0,1,1,0.]); f=np.array([1,1,0,0.]); assert np.array_equal(construct_future_change_label(c,f),[1,0,0,0])
def test_22_target_shape_mismatch():
 with pytest.raises(ValueError): construct_future_change_label(np.zeros(2),np.zeros(3))
def test_23_fixed_metrics():
 m=target_independent_metrics(np.array([.9,.8,.2,.1]),np.array([1,0,1,0]),.5); assert m['dice_fixed']==.5 and m['iou_fixed']==1/3 and m['precision_fixed']==.5 and m['recall_fixed']==.5
def test_24_soft_dice_brier_ap():
 m=target_independent_metrics(np.array([.9,.2]),np.array([1,0]),.5); assert np.isclose(m['soft_dice'],1.8/2.1) and np.isclose(m['brier_score'],.025) and m['average_precision']==1
def test_25_empty_prediction_nonempty_target():
 m=target_independent_metrics(np.zeros(3),np.array([1,0,0]),.5); assert m['dice_fixed']==0 and m['iou_fixed']==0
def test_26_empty_target_all_zero():
 m=target_independent_metrics(np.zeros(3),np.zeros(3,bool),.5); assert m['dice_fixed']==1 and m['iou_fixed']==1 and np.isnan(m['average_precision'])
def test_27_topk_target_volume_and_ties():
 p=np.ones(6,dtype=np.float32); a=topk_mask(p,2); b=topk_mask(p,2); assert a.sum()==2 and np.array_equal(a,b)
def test_28_oracle_label_present(): assert 'oracle_assisted' in (ROOT/'06_EVALUATION_LOCK/LOCKED_115_EVALUATION_POLICY.yaml').read_text()
def test_29_wilcoxon_all_zero():
 s=paired_summary(np.zeros(4)); assert s['wilcoxon_p_two_sided']==1 and s['wilcoxon_status']=='ALL_ZERO' and s['ties']==4
def test_30_rank_biserial_and_dz_policy():
 s=paired_summary(np.ones(4)); assert s['rank_biserial']==1 and s['cohens_dz_status']=='SD_ZERO' and np.isnan(s['cohens_dz'])
def test_31_holm_family_exactly_two():
 assert holm_two((.01,.04))==(.02,.04)
 with pytest.raises(ValueError): holm_two((.01,))
def test_32_failure_policy_locked():
 t=(ROOT/'08_FAILURE_POLICY/LOCKED_115_FAILURE_POLICY.yaml').read_text(); assert 'end_to_end_denominator: 115' in t and 'failed_patient_paired_difference: 0' in t and 'retry_limit_per_case_stage: 3' in t
def test_33_stage_a_shard_identity():
 legacy={r['patient_id']:r['shard'] for r in rows(C/'P0_INFERENCE_MANIFEST.csv')}; a=rows(ROOT/'09_EXECUTION_PLAN/LOCKED_115_STAGE_A_P0_SHARD_MANIFEST.csv'); assert len(a)==115 and len({r['patient_id'] for r in a})==115 and all(r['stage_a_shard']==legacy[r['patient_id']] and f"stage_a/shard_{r['stage_a_shard']}/" in r['output_p0_path'] for r in a)
def test_34_stage_b_shard_identity():
 b=rows(ROOT/'09_EXECUTION_PLAN/LOCKED_115_STAGE_B_CORRECTION_SHARD_MANIFEST.csv'); assert len(b)==115 and len({r['patient_id'] for r in b})==115 and {r['stage_b_shard'] for r in b}=={'0','1','2','3'}
def test_35_stage_manifests_not_mixable():
 assert 'stage_a_shard' in rows(ROOT/'09_EXECUTION_PLAN/LOCKED_115_STAGE_A_P0_SHARD_MANIFEST.csv')[0] and 'stage_b_shard' not in rows(ROOT/'09_EXECUTION_PLAN/LOCKED_115_STAGE_A_P0_SHARD_MANIFEST.csv')[0]
 assert 'stage_b_shard' in rows(ROOT/'09_EXECUTION_PLAN/LOCKED_115_STAGE_B_CORRECTION_SHARD_MANIFEST.csv')[0] and 'stage_a_shard' not in rows(ROOT/'09_EXECUTION_PLAN/LOCKED_115_STAGE_B_CORRECTION_SHARD_MANIFEST.csv')[0]
def test_36_mock_stage_a_runner(tmp_path):
 r=rows(ROOT/'09_EXECUTION_PLAN/LOCKED_115_STAGE_A_P0_SHARD_MANIFEST.csv')[0]; predictors=[lambda x,i=i:np.full(x.shape[0:1]+x.shape[2:],i/4,dtype=np.float32) for i in range(5)]
 access=run_case_with_predictors(r,np.arange(200,dtype=np.float32).reshape(10,10,2),np.zeros((10,10,2)),predictors,tmp_path); assert access['forbidden_file_access'] is False and len(list(tmp_path.rglob('*.npy')))==1
def test_37_no_repository_p0_files(): assert not list(ROOT.rglob('P0_float32.npy')) and not list(ROOT.rglob('P0/*.npy'))
def test_38_no_115_performance_results(): assert not [p for p in ROOT.rglob('*') if p.is_file() and any(x in p.name.upper() for x in ('115_METRICS','115_PERFORMANCE','METHOD_RESULTS'))]
def test_39_no_real_forward_evidence():
 statuses=list(ROOT.rglob('*STATUS.json')); assert all(json.loads(p.read_text()).get('model_forward_executed',False) is False for p in statuses)
def test_40_lumiere_not_started(): assert not list(ROOT.rglob('*LUMIERE*'))
def test_41_cohort_files_immutable():
 frozen={r['relative_path']:r for r in rows(ROOT/'00_PROTOCOL_AUTHORITY/PRE_SUPPLEMENT_COHORT_FILE_HASHES.csv')}
 assert all((ROOT/p).stat().st_size==int(r['file_size_bytes']) and digest(ROOT/p)==r['sha256'] for p,r in frozen.items())
def test_42_method_parameters(): assert (NAIVE_GAMMA,EIA_ALPHA,EIA_BETA,EIA_BLEND_LAMBDA_090,EIA_BLEND_LAMBDA_075,THRESHOLD,MIN_COMPONENT_SIZE)==(2.5,.3,.3,.9,.75,.5,20)
