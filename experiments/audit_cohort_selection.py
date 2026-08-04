"""Read-only cohort discovery audit matching the locked 2026 discovery code."""
from __future__ import annotations

import argparse, json, re
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd


def tp_number(path: Path) -> int:
    match=re.search(r"Timepoint_(\d+)",path.name); return int(match.group(1)) if match else -1


def main():
    p=argparse.ArgumentParser(); p.add_argument("--dataset-root",type=Path,required=True); p.add_argument("--locked-manifest",type=Path,required=True); p.add_argument("--output-root",type=Path,required=True); a=p.parse_args(); out=a.output_root/"06_cohort_selection_audit"; out.mkdir(parents=True,exist_ok=True)
    locked=pd.read_csv(a.locked_manifest); locked_ids=set(locked.case_id); included=[]; excluded=[]; patients=sorted(a.dataset_root.glob("PatientID_*")); studies=0; candidate_pairs=0; usable_patient_pairs=0
    for patient in patients:
        timepoints=sorted(patient.glob("Timepoint_*"),key=tp_number); studies+=len(timepoints); usable=[]
        for tp in timepoints:
            t1c=list(tp.glob("*_brain_t1c.nii")); mask=list(tp.glob("*_tumorMask.nii"))
            if len(t1c)==len(mask)==1: usable.append((tp_number(tp),tp,t1c[0],mask[0]))
        candidate_pairs+=max(0,len(usable)-1)
        if len(usable)<2:
            excluded.append({"patient_id":patient.name,"candidate_case_id":"","reason":"FEWER_THAN_TWO_TIMEPOINTS_WITH_EXACTLY_ONE_T1C_AND_MASK","usable_timepoints":len(usable)}); continue
        usable_patient_pairs+=1; current,future=usable[0],usable[1]; case=f"{patient.name}_T{current[0]}_to_T{future[0]}_t1c"
        images=[nib.load(str(x)) for x in [current[2],current[3],future[3]]]; compatible=all(im.shape==images[0].shape and np.allclose(im.affine,images[0].affine,rtol=0,atol=1e-5) and nib.aff2axcodes(im.affine)==nib.aff2axcodes(images[0].affine) for im in images[1:])
        cm=images[1].get_fdata()>0.5; fm=images[2].get_fdata()>0.5; target=fm&~cm
        row={"case_id":case,"patient_id":patient.name,"current_timepoint":current[1].name,"future_timepoint":future[1].name,"current_t1c_path":str(current[2]),"current_mask_path":str(current[3]),"future_mask_path":str(future[3]),"shape_affine_orientation_compatible":compatible,"current_mask_nonempty":bool(cm.any()),"future_mask_nonempty":bool(fm.any()),"future_change_target_nonempty":bool(target.any())}
        if case in locked_ids: included.append(row)
        else: excluded.append({"patient_id":patient.name,"candidate_case_id":case,"reason":"AFTER_FIRST_40_ELIGIBLE_PATIENTS_IN_SORTED_ORDER","usable_timepoints":len(usable)})
    pd.DataFrame(included).to_csv(out/"INCLUDED_CASES.csv",index=False); pd.DataFrame(excluded).to_csv(out/"EXCLUDED_CASES.csv",index=False)
    flow=[{"stage":"dataset_patient_directories","count":len(patients),"evidence":"direct dataset scan"},{"stage":"timepoint_directories","count":studies,"evidence":"direct dataset scan"},{"stage":"adjacent_pairs_among_usable_timepoints","count":candidate_pairs,"evidence":"direct dataset scan; descriptive, discovery selects only first pair"},{"stage":"patients_with_at_least_two_usable_timepoints","count":usable_patient_pairs,"evidence":"exact discovery eligibility"},{"stage":"locked_first_40_pairs","count":len(included),"evidence":"authoritative locked manifest"},{"stage":"locked_grid_compatible","count":sum(x["shape_affine_orientation_compatible"] for x in included),"evidence":"NIfTI header audit"},{"stage":"locked_nonempty_current_mask","count":sum(x["current_mask_nonempty"] for x in included),"evidence":"mask audit"},{"stage":"locked_nonempty_future_mask","count":sum(x["future_mask_nonempty"] for x in included),"evidence":"mask audit"},{"stage":"locked_nonempty_future_change_target","count":sum(x["future_change_target_nonempty"] for x in included),"evidence":"mask audit"}]
    pd.DataFrame(flow).to_csv(out/"COHORT_FLOW.csv",index=False); (out/"COHORT_AUDIT_STATUS.json").write_text(json.dumps({"status":"COMPLETE","locked_case_set_matches":set(x["case_id"] for x in included)==locked_ids,"patients":len(patients),"timepoints":studies,"eligible_patients":usable_patient_pairs,"locked_cases":len(included)},indent=2)+"\n")


if __name__=="__main__": main()
