import tempfile
from pathlib import Path

import json

import pandas as pd

from experiments.build_internal_completion_manifest import build, digest, finalize_package


def test_manifest_hashes_files_without_hashing_itself():
    with tempfile.TemporaryDirectory() as temporary:
        root=Path(temporary); (root/"a").mkdir(); source=root/"a/x.txt"; source.write_text("locked\n")
        frame=build(root)
        assert len(frame)==1
        assert frame.iloc[0].sha256==digest(source)
        assert "INTERNAL_COMPLETION_ARTIFACT_MANIFEST.csv" not in set(frame.relative_path)


def test_package_validation_is_written_before_its_hash_is_frozen():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        pd.DataFrame([{"experiment": "x", "status": "COMPLETE", "case_count": 1}]).to_csv(
            root / "INTERNAL_COMPLETION_STATUS.csv", index=False
        )
        frame, payload = finalize_package(root)
        validation = root / "14_reproducibility/PACKAGE_VALIDATION.json"
        row = frame.set_index("relative_path").loc["14_reproducibility/PACKAGE_VALIDATION.json"]
        assert row.sha256 == digest(validation)
        assert json.loads(validation.read_text())["status"] == "COMPLETE"
        assert payload["files_hashed"] == len(frame)
