from pathlib import Path
import csv, json, hashlib, yaml

ROOT=Path(__file__).resolve().parents[1]
def rows(rel):
    with (ROOT/rel).open(newline="",encoding="utf-8") as f: return list(csv.DictReader(f))
def y(rel): return yaml.safe_load((ROOT/rel).read_text())
def j(rel): return json.loads((ROOT/rel).read_text())

def test_01_cohort_39(): assert len(rows("01_COHORT_LOCK/LOCKED_RHUH_39_EXTERNAL_CONFIRMATORY_CASE_MANIFEST.csv"))==39
def test_02_unique_patients_39(): assert len({r["patient_id"] for r in rows("01_COHORT_LOCK/LOCKED_RHUH_39_EXTERNAL_CONFIRMATORY_CASE_MANIFEST.csv")})==39
def test_03_unique_pairs_39(): assert len({r["case_id"] for r in rows("01_COHORT_LOCK/LOCKED_RHUH_39_EXTERNAL_CONFIRMATORY_CASE_MANIFEST.csv")})==39
def test_04_only_0008_excluded(): assert [r["patient_id"] for r in rows("01_COHORT_LOCK/EXCLUDED_RHUH_EXTERNAL_CASES.csv")]==["RHUH-0008"]
def test_05_exclusion_pre_outcome():
    r=rows("01_COHORT_LOCK/EXCLUDED_RHUH_EXTERNAL_CASES.csv")[0]; assert r["external_p0_seen_before_exclusion"]==r["target_constructed_before_exclusion"]==r["performance_seen_before_exclusion"]=="false"
def test_06_original_audit_40(): assert len(rows("01_COHORT_LOCK/RHUH_40_TO_39_COHORT_AUDIT.csv"))==40
def test_07_geometry_39(): assert len(rows("02_GEOMETRY_LOCK/LOCKED_RHUH_39_GEOMETRY_MANIFEST.csv"))==39
def test_08_geometry_all_valid(): assert all(r["effective_geometry_valid"]=="true" for r in rows("02_GEOMETRY_LOCK/LOCKED_RHUH_39_GEOMETRY_MANIFEST.csv"))
def test_09_geometry_forbids_transforms(): assert set(y("02_GEOMETRY_LOCK/LOCKED_RHUH_EXTERNAL_GEOMETRY_POLICY.yaml")["forbidden"])=={"registration","resampling","interpolation","case-specific affine repair","header rewriting to force alignment","outcome-driven geometry correction"}
def test_10_mask_mapping(): assert y("03_MASK_LOCK/LOCKED_RHUH_EXTERNAL_MASK_MAPPING.yaml")["RHUH_expression"]=="segmentation > 0"
def test_11_mask_labels(): assert y("03_MASK_LOCK/LOCKED_RHUH_EXTERNAL_MASK_MAPPING.yaml")["RHUH_labels"]=={1:"necrosis",2:"peritumoral / non-enhancing abnormality",3:"enhancing tumor"}
def test_12_checkpoints_5_match():
    r=rows("04_PREDICTOR_LOCK/LOCKED_RHUH_FROZEN_PREDICTOR_MANIFEST.csv"); assert len(r)==5 and all(x["hash_status"]=="MATCH" for x in r)
def test_13_no_training_or_finetuning():
    s=j("11_RELEASE/PCC_RHUH_EXTERNAL_PROTOCOL_STATUS.json"); assert not s["RHUH_training"] and not s["fine_tuning"]
def test_14_no_p0_or_forward():
    s=j("11_RELEASE/PCC_RHUH_EXTERNAL_PROTOCOL_STATUS.json"); assert not s["external_p0_generated"] and not s["predictor_forward_executed"]
def test_15_no_future_voxel_access(): assert not j("11_RELEASE/PCC_RHUH_EXTERNAL_PROTOCOL_STATUS.json")["recurrence_segmentation_voxel_arrays_read"]
def test_16_no_target_or_performance():
    s=j("11_RELEASE/PCC_RHUH_EXTERNAL_PROTOCOL_STATUS.json"); assert not s["target_constructed"] and not s["performance_computed"] and not s["stage_b_executed"]
def test_17_seven_methods(): assert len(y("06_STAGE_B_LOCK/LOCKED_RHUH_EXTERNAL_STAGE_B_PROTOCOL.yaml")["methods"])==7
def test_18_full_pcc_p10(): assert y("06_STAGE_B_LOCK/LOCKED_RHUH_EXTERNAL_STAGE_B_PROTOCOL.yaml")["methods"]["Full PCC"]["formal_final"]=="P10"
def test_19_threshold_point5(): assert y("06_STAGE_B_LOCK/LOCKED_RHUH_EXTERNAL_EVALUATION_POLICY.yaml")["prediction_rule"]=="probability >= 0.5"
def test_20_exactly_two_confirmatory(): assert len(y("07_STATISTICS_LOCK/LOCKED_RHUH_EXTERNAL_STATISTICAL_ANALYSIS_PLAN.yaml")["confirmatory_family_exactly"])==2
def test_21_bootstrap_10000(): assert y("07_STATISTICS_LOCK/LOCKED_RHUH_EXTERNAL_STATISTICAL_ANALYSIS_PLAN.yaml")["bootstrap"]["replicates"]==10000
def test_22_bootstrap_seed(): assert y("07_STATISTICS_LOCK/LOCKED_RHUH_EXTERNAL_STATISTICAL_ANALYSIS_PLAN.yaml")["bootstrap"]["seed"]==20260810
def test_23_failure_denominator_39(): assert y("08_FAILURE_LOCK/LOCKED_RHUH_EXTERNAL_FAILURE_POLICY.yaml")["locked_denominator"]==39
def test_24_no_lumiere(): assert not j("11_RELEASE/PCC_RHUH_EXTERNAL_PROTOCOL_STATUS.json")["lumiere_started"]
