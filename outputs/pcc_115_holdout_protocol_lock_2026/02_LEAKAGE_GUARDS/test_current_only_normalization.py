import numpy as np
from src.preprocessing.current_only_preprocessing import normalize_current_t1c

def test_normalization_is_current_array_only():
 x=np.arange(200,dtype=np.float32).reshape(10,10,2); y=normalize_current_t1c(x)
 assert y.shape==x.shape and np.isfinite(y).all() and float(y.min())>=0 and float(y.max())<=1
