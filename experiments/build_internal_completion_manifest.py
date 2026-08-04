"""Build immutable hashes and completion reports for the internal package."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def build(root: Path) -> pd.DataFrame:
    manifest_path = root / "INTERNAL_COMPLETION_ARTIFACT_MANIFEST.csv"
    rows=[]
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path == manifest_path:
            continue
        relative = path.relative_to(root)
        rows.append({"relative_path":str(relative),"file_name":path.name,"file_type":path.suffix.lower() or "none","size_bytes":path.stat().st_size,"sha256":digest(path),"category":relative.parts[0] if len(relative.parts)>1 else "root","large_artifact":False,"source":"local_or_small_kaggle_output"})
    frame=pd.DataFrame(rows)
    temporary=manifest_path.with_suffix(".csv.tmp"); frame.to_csv(temporary,index=False); temporary.replace(manifest_path)
    return frame


def finalize_package(root: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    """Write the validation record before hashing it into the final manifest.

    The manifest excludes itself.  Writing validation after the manifest would
    invalidate the recorded validation-file hash, so determine its stable
    payload first and build the manifest second.
    """
    manifest_path = root / "INTERNAL_COMPLETION_ARTIFACT_MANIFEST.csv"
    validation_path = root / "14_reproducibility/PACKAGE_VALIDATION.json"
    status_path = root / "INTERNAL_COMPLETION_STATUS.csv"
    status = pd.read_csv(status_path) if status_path.exists() else pd.DataFrame()
    existing = [path for path in root.rglob("*") if path.is_file() and path not in {manifest_path, validation_path}]
    payload: dict[str, object] = {
        "status": "COMPLETE" if len(status) and set(status.status) == {"COMPLETE"} else "COMPLETE_WITH_DOCUMENTED_BLOCKERS",
        "files_hashed": len(existing) + 1,
        "total_small_bytes": 0,
        "large_artifacts_downloaded": False,
    }
    validation_path.parent.mkdir(parents=True, exist_ok=True)
    # Size is deliberately not embedded because doing so would be self-referential.
    validation_path.write_text(json.dumps(payload, indent=2) + "\n")
    frame = build(root)
    payload["total_small_bytes"] = int(frame.size_bytes.sum())
    # Keep the hashed JSON stable; total bytes are emitted to stdout and manifest.
    return frame, payload


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--output-root",type=Path,required=True); args=parser.parse_args()
    _, payload = finalize_package(args.output_root)
    print(json.dumps(payload))


if __name__ == "__main__": main()
