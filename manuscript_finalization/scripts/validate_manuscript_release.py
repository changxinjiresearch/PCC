#!/usr/bin/env python3
"""Independent validation of the generated PCC manuscript release."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import statistics
import zipfile
from pathlib import Path

from docx import Document
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'manuscript_finalization'
FINAL=OUT/'FINAL_SUBMISSION_PACKAGE'

def rows(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def check(name,condition,detail=''):
    checks.append({'check':name,'status':'PASS' if condition else 'FAIL','detail':detail})
    if not condition: failures.append(f'{name}: {detail}')

checks=[];failures=[]
int_case=ROOT/'outputs/pcc_113_stage_b_final_audit_patch_v2_2026/V1_SNAPSHOT/03_COMBINED_RESULTS/ALL_CASE_METHOD_METRICS.csv'
int_traj=ROOT/'outputs/pcc_113_stage_b_final_audit_patch_v2_2026/V1_SNAPSHOT/03_COMBINED_RESULTS/ALL_PCC_ROUND_TRAJECTORY.csv'
int_stat=ROOT/'outputs/pcc_113_stage_b_final_audit_patch_v2_2026/V1_SNAPSHOT/04_STATISTICS/CONFIRMATORY_STATISTICS.csv'
ext_case=ROOT/'outputs/pcc_rhuh_external_stage_b_confirmatory_validation_2026/02_CASE_RESULTS/RHUH_STAGE_B_CASE_METHOD_METRICS.csv'
ext_traj=ROOT/'outputs/pcc_rhuh_external_stage_b_confirmatory_validation_2026/03_TRAJECTORIES/RHUH_STAGE_B_FULL_PCC_ROUND_TRAJECTORY.csv'
ext_stat=ROOT/'outputs/pcc_rhuh_external_stage_b_confirmatory_validation_2026/06_CONFIRMATORY_STATISTICS/RHUH_STAGE_B_CONFIRMATORY_STATISTICS.csv'

ir=rows(int_case);it=rows(int_traj);isr=rows(int_stat);er=rows(ext_case);et=rows(ext_traj);esr=rows(ext_stat)
check('internal case-method rows',len(ir)==904,str(len(ir)))
check('internal unique patients',len({r['patient_id'] for r in ir})==113,str(len({r['patient_id'] for r in ir})))
check('internal trajectory rows',len(it)==1130,str(len(it)))
check('RHUH case-method rows',len(er)==273,str(len(er)))
check('RHUH unique patients',len({r['patient_id'] for r in er})==39,str(len({r['patient_id'] for r in er})))
check('RHUH-0008 absent','RHUH-0008' not in {r['patient_id'] for r in er})
check('RHUH trajectory rows',len(et)==390,str(len(et)))
check('confirmatory families',len(isr)==2 and len(esr)==2,'2 internal + 2 external')

md=(OUT/'PCC_MANUSCRIPT_DRAFT_V2.md').read_text()
def mean(rs,m,k):return statistics.fmean(float(r[k]) for r in rs if r['method']==m)
for prefix,rs in [('internal',ir),('RHUH',er)]:
    for m in ['Fixed','Full PCC','No-smoothing PCC']:
        value=f'{mean(rs,m,"Dice_0.5"):.3f}'
        check(f'{prefix} {m} rendered mean',value in md,value)
for r in isr:
    check('internal exact raw p rendered',f"{float(r['wilcoxon_p_two_sided']):.3e}" in md,r['comparison'])
    check('internal Holm p rendered',f"{float(r['holm_adjusted_p']):.3e}" in md,r['comparison'])
for r in esr:
    check('RHUH exact raw p rendered',f"{float(r['wilcoxon_p_two_sided']):.3e}" in md,r['comparison'])
    check('RHUH Holm p rendered',f"{float(r['holm_adjusted_p']):.3e}" in md,r['comparison'])

audit=rows(OUT/'AUDITS/MANUSCRIPT_NUMERIC_CLAIM_AUDIT.csv')
check('numeric audit nonempty',len(audit)>=70,str(len(audit)))
check('numeric mismatches zero',all(r['status']=='PASS' for r in audit),str(sum(r['status']!='PASS' for r in audit)))
ca=rows(OUT/'AUDITS/MANUSCRIPT_CITATION_CLAIM_AUDIT.csv')
check('citation claim failures zero',all(r['status']=='PASS' and r['supports_claim']=='YES' for r in ca),str(len(ca)))

refs=rows(OUT/'03_LITERATURE/REFERENCE_MASTER_LEDGER.csv')
dois=[r['doi'].lower() for r in refs]
check('references verified',len(refs)==15 and all(r['verified']=='YES' for r in refs),str(len(refs)))
check('reference DOI uniqueness',len(dois)==len(set(dois)),str(len(dois)-len(set(dois))))
check('reference identifiers present',all(r['doi'] and r['url'] for r in refs))
check('known corrected metric reference',any(r['doi']=='10.1186/s13104-022-06096-y' for r in refs))
check('RHUH peer-reviewed DOI',any(r['doi']=='10.1016/j.dib.2023.109617' for r in refs))

areg=rows(OUT/'01_AUTHORITY_REGISTRY/PCC_MANUSCRIPT_AUTHORITATIVE_EVIDENCE_REGISTRY.csv')
drift=[]
for r in areg:
    p=ROOT/r['relative_path']
    if r['exists']=='true' and (not p.exists() or sha(p)!=r['sha256']):drift.append(r['relative_path'])
check('authority registry hash drift zero',not drift,';'.join(drift))

required=[
 '01_PCC_SCIENTIFIC_REPORTS_SUBMISSION_READY.docx','02_PCC_SCIENTIFIC_REPORTS_SUBMISSION_READY.pdf',
 '03_PCC_SCIENTIFIC_REPORTS_SUPPLEMENTARY_INFORMATION.docx','04_PCC_SCIENTIFIC_REPORTS_SUPPLEMENTARY_INFORMATION.pdf',
 '05_PCC_SCIENTIFIC_REPORTS_COVER_LETTER.docx','FINAL_MANUSCRIPT_RELEASE_REPORT.md',
 'FINAL_SUBMISSION_READINESS_ASSESSMENT.md','SUBMISSION_ACTIONS_REQUIRED.md']
check('required final files',all((FINAL/x).exists() for x in required),','.join(x for x in required if not (FINAL/x).exists()))
for name in required[:5]:
    p=FINAL/name
    check(f'{name} nonempty',p.stat().st_size>500,str(p.stat().st_size))
for name in required[:5:2]:
    if name.endswith('.docx'):
        try:d=Document(FINAL/name);ok=len(d.paragraphs)>5
        except Exception:ok=False
        check(f'{name} opens',ok)
for name in ['02_PCC_SCIENTIFIC_REPORTS_SUBMISSION_READY.pdf','04_PCC_SCIENTIFIC_REPORTS_SUPPLEMENTARY_INFORMATION.pdf']:
    b=(FINAL/name).read_bytes();check(f'{name} PDF header/trailer',b.startswith(b'%PDF') and b'%%EOF' in b[-1024:])

svgs=sorted((FINAL/'FIGURES').glob('*.svg'));pngs=sorted((FINAL/'FIGURES').glob('*.png'))
check('figure counts',len(svgs)==5 and len(pngs)==5,f'{len(svgs)} SVG, {len(pngs)} PNG')
for p in pngs:
    with Image.open(p) as im:check(f'{p.name} dimensions',im.size==(2400,1520),str(im.size))

zip_path=OUT/'PCC_SCIENTIFIC_REPORTS_FINAL_SUBMISSION_PACKAGE_2026.zip'
with zipfile.ZipFile(zip_path) as z:
    bad=z.testzip();names=z.namelist();actual={n.split('/',1)[1]:z.read(n) for n in names if n.startswith('FINAL_SUBMISSION_PACKAGE/') and not n.endswith('/')}
tree={p.relative_to(FINAL).as_posix():p.read_bytes() for p in FINAL.rglob('*') if p.is_file()}
check('ZIP integrity',bad is None,str(bad))
check('ZIP duplicate paths',len(names)==len(set(names)),str(len(names)-len(set(names))))
check('ZIP/tree paths equal',set(actual)==set(tree),f'missing={len(set(tree)-set(actual))}, extra={len(set(actual)-set(tree))}')
check('ZIP/tree bytes equal',all(actual[k]==v for k,v in tree.items() if k in actual))

mf=rows(FINAL/'PACKAGE_FILE_MANIFEST.csv');controlled=[r for r in mf if r['control_status']=='CONTROLLED']
mm=[]
for r in controlled:
    b=actual.get(r['path'])
    if b is None or len(b)!=int(r['size']) or hashlib.sha256(b).hexdigest()!=r['sha256']:mm.append(r['path'])
check('controlled package mismatches',not mm,';'.join(mm))
check('self-reference policy',sum(r['control_status']=='EXCLUDED_SELF_REFERENCE' for r in mf)==2)

text='\n'.join(p.read_text(errors='ignore') for p in [OUT/'PCC_MANUSCRIPT_DRAFT_V2.md',FINAL/'FINAL_MANUSCRIPT_RELEASE_REPORT.md'])
check('no LUMIERE result claim','LUMIERE was not started' in text)
check('target-conditioning limitation explicit','not prospective recurrence forecasting' in md and 'requires the true future-change target' in md)
check('no unsupported PASS gate','PASS_WITH_AUTHOR_ACTIONS' in (FINAL/'FINAL_MANUSCRIPT_RELEASE_REPORT.md').read_text())

status='PASS' if not failures else 'FAIL'
report=OUT/'AUDITS/MANUSCRIPT_RELEASE_TEST_REPORT.md'
report.write_text('# Manuscript release test report\n\n'+f'- checks: {len(checks)}\n- passed: {sum(x["status"]=="PASS" for x in checks)}\n- failed: {len(failures)}\n- exit status: {status}\n\n'+('\n'.join(f'- {x}' for x in failures) if failures else 'All deterministic authority, numeric, citation, document, figure and package checks passed.')+'\n')
with (OUT/'AUDITS/MANUSCRIPT_RELEASE_TEST_RESULTS.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['check','status','detail']);w.writeheader();w.writerows(checks)
print(json.dumps({'status':status,'checks':len(checks),'passed':sum(x['status']=='PASS' for x in checks),'failed':len(failures),'failures':failures},indent=2))
raise SystemExit(0 if not failures else 1)
