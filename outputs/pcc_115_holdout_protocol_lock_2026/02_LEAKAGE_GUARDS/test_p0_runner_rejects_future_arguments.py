import pytest
from experiments.run_115_stage_a_p0 import parser, validate_current_only_record

def test_real_stage_a_runner_rejects_future_record():
 with pytest.raises(ValueError):
  validate_current_only_record({"future_mask_path": "forbidden.nii"})

def test_real_stage_a_cli_rejects_future_argument():
 with pytest.raises(SystemExit):
  parser().parse_args(["--future-mask", "forbidden.nii"])
