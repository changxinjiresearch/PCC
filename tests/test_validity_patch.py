import numpy as np

from src.analysis.validity_patch import average_precision_binary, select_crossfit_threshold, target_independent_metrics


def test_target_independent_metrics_known_confusion():
    p=np.array([.9,.8,.4,.1]); y=np.array([1,0,1,0],dtype=bool); m=target_independent_metrics(p,y,.5)
    assert m["dice_fixed"]==.5 and m["iou_fixed"]==1/3 and m["precision_fixed"]==.5 and m["recall_fixed"]==.5
    assert m["predicted_positive_voxels"]==2 and m["true_target_voxels"]==2 and m["volume_error_voxels"]==0


def test_average_precision_and_empty_target_are_explicit():
    assert average_precision_binary(np.array([1,0,1]),np.array([.9,.8,.7]))==(1+2/3)/2
    assert np.isnan(average_precision_binary(np.zeros(3,dtype=bool),np.arange(3)))


def test_crossfit_threshold_tie_uses_smallest_value():
    grid=np.array([.01,.02,.03]); curves=np.array([[.5,.5,.1],[.5,.5,.2]])
    assert select_crossfit_threshold(curves,grid)==.01
