from pathlib import Path

def test_p0_manifest_paths_are_current_only():
 text=Path('outputs/pcc_115_holdout_protocol_lock_2026/01_COHORT_LOCK/P0_INFERENCE_MANIFEST.csv').read_text().lower()
 assert 'future_mask' not in text and 'future_image' not in text and 'target_' not in text
