import tempfile
from pathlib import Path

from experiments.build_internal_completion_manifest import build, digest


def test_manifest_hashes_files_without_hashing_itself():
    with tempfile.TemporaryDirectory() as temporary:
        root=Path(temporary); (root/"a").mkdir(); source=root/"a/x.txt"; source.write_text("locked\n")
        frame=build(root)
        assert len(frame)==1
        assert frame.iloc[0].sha256==digest(source)
        assert "INTERNAL_COMPLETION_ARTIFACT_MANIFEST.csv" not in set(frame.relative_path)
