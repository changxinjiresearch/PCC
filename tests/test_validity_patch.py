import numpy as np

from experiments.run_internal_validity_patch import resolve_record_paths
from src.analysis.validity_patch import average_precision_binary, select_crossfit_threshold, target_independent_metrics, threshold_grid_case_dice


def test_target_independent_metrics_known_confusion():
    p=np.array([.9,.8,.4,.1]); y=np.array([1,0,1,0],dtype=bool); m=target_independent_metrics(p,y,.5)
    assert m["dice_fixed"]==.5 and m["iou_fixed"]==1/3 and m["precision_fixed"]==.5 and m["recall_fixed"]==.5
    assert m["predicted_positive_voxels"]==2 and m["true_target_voxels"]==2 and m["volume_error_voxels"]==0


def test_average_precision_and_empty_target_are_explicit():
    assert average_precision_binary(np.array([1,0,1]),np.array([.9,.8,.7]))==(1+2/3)/2
    assert np.isnan(average_precision_binary(np.zeros(3,dtype=bool),np.arange(3)))
    assert average_precision_binary(np.array([1,0]),np.array([.5,.5]))==.5


def test_crossfit_threshold_tie_uses_smallest_value():
    grid=np.array([.01,.02,.03]); curves=np.array([[.5,.5,.1],[.5,.5,.2]])
    assert select_crossfit_threshold(curves,grid)==.01


def test_manifest_mount_prefix_resolution_is_basename_exact(tmp_path):
    mounted=tmp_path/"dataset"; mounted.mkdir(); source=mounted/"case_mask.nii"; source.write_bytes(b"x")
    record={"current_t1c_path":str(source),"current_mask_path":"/old/case_mask.nii","future_mask_path":str(source)}
    result=resolve_record_paths(record,tmp_path)
    assert result["current_mask_path"]==str(source)


def test_sorted_threshold_counts_equal_direct_voxel_scans():
    p=np.array([.9,.8,.4,.1,.01]); y=np.array([1,0,1,0,0],dtype=bool); grid=np.array([.01,.4,.5,.9,.99])
    expected=[]
    for threshold in grid:
        pred=p>=threshold; tp=(pred&y).sum(); fp=(pred&~y).sum(); fn=(~pred&y).sum(); expected.append(2*tp/(2*tp+fp+fn))
    assert np.allclose(threshold_grid_case_dice(p,y,grid),expected)
