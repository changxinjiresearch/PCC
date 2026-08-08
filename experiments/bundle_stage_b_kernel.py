"""Bundle exact locked source modules into Kaggle's single script upload."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KERNEL_ROOT = ROOT / "kaggle"
MODULES = {
    "src.models.pcc": ROOT / "src/models/pcc.py",
    "src.models.eia": ROOT / "src/models/eia.py",
    "src.models.naive_self_tightening": ROOT / "src/models/naive_self_tightening.py",
    "src.analysis.internal_completion": ROOT / "src/analysis/internal_completion.py",
    "src.analysis.internal_statistics": ROOT / "src/analysis/internal_statistics.py",
    "src.analysis.validity_patch": ROOT / "src/analysis/validity_patch.py",
    "src.evaluation.metrics": ROOT / "src/evaluation/metrics.py",
}


def main() -> None:
    runner = (KERNEL_ROOT / "pcc_113_stage_b_cpu_shards/run.py").read_text(encoding="utf-8")
    prefix = '''# Exact locked source bundle; generated mechanically from repository files.\nimport sys, types\n\nfor _pkg in ("src", "src.models", "src.analysis", "src.evaluation"):\n    sys.modules.setdefault(_pkg, types.ModuleType(_pkg))\n\ndef _load_locked(_name, _source):\n    _module = types.ModuleType(_name)\n    _module.__file__ = _name.replace(".", "/") + ".py"\n    sys.modules[_name] = _module\n    exec(compile(_source, _module.__file__, "exec"), _module.__dict__)\n    return _module\n\n'''
    for name, path in MODULES.items():
        prefix += f"_load_locked({name!r}, {path.read_text(encoding='utf-8')!r})\n"
    # Remove imports that would otherwise shadow the exact bundled modules.
    marker = 'from src.analysis.internal_completion import run_variant\n'
    runner = runner.replace(marker, marker)
    for line in [
        "from src.analysis.internal_completion import run_variant\n",
        "from src.analysis.validity_patch import target_independent_metrics\n",
        "from src.evaluation.metrics import eval_prob_map\n",
        "from src.models.eia import apply_eia\n",
        "from src.models.naive_self_tightening import naive_self_tighten\n",
        "from src.models.pcc import apply_pcc, safe_clip_prob\n",
    ]:
        # Keep imports: they now resolve to the exact bundled modules.
        if line not in runner:
            raise RuntimeError(f"runner import missing: {line.strip()}")
    future_line = "from __future__ import annotations\n"
    if future_line not in runner:
        raise RuntimeError("runner future import missing")
    head, body = runner.split(future_line, 1)
    bundled_runner = head + future_line + prefix + body
    for shard in range(4):
        path = KERNEL_ROOT / f"pcc_113_stage_b_cpu_shard_{shard}/run.py"
        path.write_text(bundled_runner, encoding="utf-8")


if __name__ == "__main__":
    main()
