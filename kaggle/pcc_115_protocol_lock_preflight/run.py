from pathlib import Path
import subprocess, sys

repo = Path('/tmp/PCC')
subprocess.run(['git', 'clone', '--quiet', 'https://github.com/changxinjiresearch/PCC.git', str(repo)], check=True)
subprocess.run(['git', '-C', str(repo), 'checkout', '--quiet', '38181335557214d53147591e29ac4e1a8e132df5'], check=True)
out = Path('/kaggle/working/pcc_115_holdout_protocol_lock_2026/01_COHORT_LOCK')
subprocess.run([sys.executable, str(repo / 'experiments/pcc_115_protocol_lock_preflight.py'), '--input-root', '/kaggle/input', '--output-root', str(out)], cwd=repo, check=True)
