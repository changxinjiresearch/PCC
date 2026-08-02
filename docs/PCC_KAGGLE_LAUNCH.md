# PCC leakage-free Kaggle launch

Canonical experiment: `PCC_LEAKAGE_FREE_RERUN_2026`.

One-fold/one-case smoke command:

```bash
python3 experiments/run_pcc_leakage_free_full.py \
  --config configs/pcc_leakage_free_canonical.yaml \
  --smoke
```

After inspection of the smoke completion marker, full P0 command:

```bash
python3 experiments/run_pcc_leakage_free_full.py \
  --config configs/pcc_leakage_free_canonical.yaml
```

Direct Kaggle notebook cell:

```python
import subprocess, sys
subprocess.run([
    sys.executable,
    "experiments/run_pcc_leakage_free_full.py",
    "--config", "configs/pcc_leakage_free_canonical.yaml",
    "--smoke",
], check=True)
```

The entry discovers a unique `MU-Glioma-Post` tree below `/kaggle/input`, locks the earliest usable consecutive pair for the first 40 sorted patients, writes the case manifest, writes a patient-group five-fold manifest exactly once, and hashes both. Existing manifests cannot be overwritten. The engineering smoke route uses fold 1, two train cases, two epochs, and one held-out case. It may fall back to CPU only when an actual CUDA Conv2d compatibility probe fails; the full run requires a working CUDA device and never silently falls back.

Historical fold assignments were not found as a surviving file or Git object. Although notebook cell 14 specifies its deterministic KFold algorithm, this rerun labels the newly generated patient-group assignment as new and does not claim original-fold reproduction.
