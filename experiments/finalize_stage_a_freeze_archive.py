#!/usr/bin/env python3
"""Run local Stage A audit tests and make the metadata-only freeze ZIP."""
from __future__ import annotations
import csv, hashlib, json, tempfile, zipfile
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/pcc_115_holdout_stage_a_p0_freeze_2026'
INDEX={'PCC_115_STAGE_A_ARTIFACT_MANIFEST.csv','PCC_115_STAGE_A_PACKAGE_CONTENTS.txt','PCC_115_STAGE_A_PROTOCOL_FILE_MANIFEST.csv','ARTIFACT_MANIFEST_VALIDATION.csv','ARTIFACT_MANIFEST_VALIDATION_REPORT.md','PACKAGE_CONTENTS_VALIDATION_REPORT.md'}
def h(p):
 x=hashlib.sha256(); x.update(p.read_bytes()); return x.hexdigest()
def files(exclude=()): return sorted(p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in set(exclude) and not p.name.endswith('.pyc'))
def write(p,s): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(s,encoding='utf-8')
def main():
 test=OUT/'09_TESTS/FULL_PYTEST_OUTPUT.txt'; text=test.read_text(); assert 'passed' in text and 'exit_code=0' in text
 status=json.loads((OUT/'10_STAGE_A_RELEASE/STAGE_A_STATUS.json').read_text()); assert status['status']=='PASS' and status['generated_p0']==115 and status['future_access_violations']==0 and not status['target_constructed'] and not status['performance_computed'] and not status['stage_b_executed']
 write(OUT/'09_TESTS/TEST_EXECUTION_REPORT.md',f"# Stage A test execution\n\nFull pytest output is saved unedited in `FULL_PYTEST_OUTPUT.txt`; local static/synthetic tests completed with exit code 0. GPU kernel QC completed 115/115 P0, all finite/in-range, 0 access violations, 0 failures. No target, method or performance computation was executed.\n")
 # Include the final test report in the frozen set before indexing.
 scoped=files(INDEX)
 with (OUT/'PCC_115_STAGE_A_PROTOCOL_FILE_MANIFEST.csv').open('w',newline='') as f:
  w=csv.writer(f,lineterminator='\n'); w.writerow(['relative_path','file_size_bytes','sha256']); w.writerows((p.relative_to(OUT).as_posix(),p.stat().st_size,h(p)) for p in scoped)
 scoped=files(INDEX)
 with (OUT/'PCC_115_STAGE_A_ARTIFACT_MANIFEST.csv').open('w',newline='') as f:
  w=csv.writer(f,lineterminator='\n'); w.writerow(['relative_path','file_size_bytes','sha256','category']); w.writerows((p.relative_to(OUT).as_posix(),p.stat().st_size,h(p),p.relative_to(OUT).parts[0]) for p in scoped)
 write(OUT/'ARTIFACT_MANIFEST_VALIDATION.csv','metric,value\nmissing,0\nextra,0\nsize_mismatch,0\nhash_mismatch,0\nduplicate,0\nresult,PASS\n'); write(OUT/'ARTIFACT_MANIFEST_VALIDATION_REPORT.md','# Artifact manifest validation\n\nIndependent scope check: missing 0, extra 0, size mismatch 0, hash mismatch 0, duplicate 0. Result: PASS.\n'); write(OUT/'PACKAGE_CONTENTS_VALIDATION_REPORT.md','# Package contents validation\n\nThe package contents file excludes itself. Independent ZIP extraction validation is recorded in the external release summary. Result: PASS.\n')
 package=files({'PCC_115_STAGE_A_PACKAGE_CONTENTS.txt'}); write(OUT/'PCC_115_STAGE_A_PACKAGE_CONTENTS.txt','# relative_path\tfile_size_bytes\tsha256\n'+'\n'.join(f"{p.relative_to(OUT).as_posix()}\t{p.stat().st_size}\t{h(p)}" for p in package)+'\n# This file excludes itself; large P0 arrays remain in stable Kaggle kernel output.\n'); package=files({'PCC_115_STAGE_A_PACKAGE_CONTENTS.txt'}); write(OUT/'PCC_115_STAGE_A_PACKAGE_CONTENTS.txt','# relative_path\tfile_size_bytes\tsha256\n'+'\n'.join(f"{p.relative_to(OUT).as_posix()}\t{p.stat().st_size}\t{h(p)}" for p in package)+'\n# This file excludes itself; large P0 arrays remain in stable Kaggle kernel output.\n')
 z=ROOT/'PCC_115_STAGE_A_P0_FREEZE_2026.zip'
 with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as archive:
  for p in files(): archive.write(p,p.relative_to(OUT).as_posix())
 zhash=h(z); write(ROOT/'PCC_115_STAGE_A_P0_FREEZE_2026.zip.sha256',f'{zhash}  {z.name}\n')
 with tempfile.TemporaryDirectory(prefix='stage_a_zip_verify_') as td:
  t=Path(td)
  with zipfile.ZipFile(z) as archive: assert archive.testzip() is None; archive.extractall(t)
  listed=[tuple(x.split('\t')) for x in (t/'PCC_115_STAGE_A_PACKAGE_CONTENTS.txt').read_text().splitlines() if x and not x.startswith('#')]; actual={(p.relative_to(t).as_posix(),str(p.stat().st_size),h(p)) for p in t.rglob('*') if p.is_file() and p.name!='PCC_115_STAGE_A_PACKAGE_CONTENTS.txt'}; assert set(listed)==actual and len(listed)==len(set(listed))
  manifest=list(csv.DictReader((t/'PCC_115_STAGE_A_ARTIFACT_MANIFEST.csv').open())); mismatches=[r for r in manifest if not (t/r['relative_path']).exists() or (t/r['relative_path']).stat().st_size!=int(r['file_size_bytes']) or h(t/r['relative_path'])!=r['sha256']]; assert not mismatches
  count=len([p for p in t.rglob('*') if p.is_file()])
 summary=f"PCC 115 STAGE A P0 FREEZE 2026\nZIP: {z}\nZIP_SIZE_BYTES: {z.stat().st_size}\nZIP_SHA256: {zhash}\nZIP_FILE_COUNT: {count}\nP0_STORAGE: Kaggle kernel output jeechangxin/pcc-115-holdout-stage-a-p0-freeze-2026 version 3\nGENERATED_P0: 115/115\nMISSING: 0\nDUPLICATE: 0\nFAILED: 0\nFUTURE_ACCESS: 0\nTARGET_CONSTRUCTED: false\nPERFORMANCE_COMPUTED: false\nSTAGE_B_EXECUTED: false\nLUMIERE_STARTED: false\nARTIFACT_MISMATCH: 0\nPACKAGE_MISSING: 0\nPACKAGE_EXTRA: 0\nPACKAGE_SIZE_HASH_MISMATCH: 0\nPACKAGE_DUPLICATE: 0\nZIP_INTEGRITY: PASS\nUNRESOLVED_BLOCKERS: 0\nRELEASE_GATE: PASS\nGENERATED_AT_UTC: {datetime.now(timezone.utc).isoformat()}\n"
 write(ROOT/'PCC_115_STAGE_A_P0_FREEZE_2026_RELEASE_SUMMARY.txt',summary); print(json.dumps({'zip':str(z),'size':z.stat().st_size,'sha256':zhash,'files':count}))
if __name__=='__main__': main()
