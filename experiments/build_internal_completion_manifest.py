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


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--output-root",type=Path,required=True); args=parser.parse_args()
    frame=build(args.output_root)
    status_path=args.output_root/"INTERNAL_COMPLETION_STATUS.csv"
    status=pd.read_csv(status_path) if status_path.exists() else pd.DataFrame()
    payload={"status":"COMPLETE" if len(status) and set(status.status)=={"COMPLETE"} else "COMPLETE_WITH_DOCUMENTED_BLOCKERS","files_hashed":len(frame),"total_small_bytes":int(frame.size_bytes.sum()),"large_artifacts_downloaded":False}
    (args.output_root/"14_reproducibility/PACKAGE_VALIDATION.json").parent.mkdir(parents=True,exist_ok=True)
    (args.output_root/"14_reproducibility/PACKAGE_VALIDATION.json").write_text(json.dumps(payload,indent=2)+"\n")
    print(json.dumps(payload))


if __name__ == "__main__": main()
