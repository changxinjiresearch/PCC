"""Kaggle entry point for the final formal Layer 2R execution path."""

from __future__ import annotations

import argparse
import importlib
import json
from dataclasses import asdict


REQUIRED_DEPENDENCIES = (
    "numpy",
    "pandas",
    "scipy",
    "nibabel",
    "matplotlib",
    "torch",
)


def _dependency_errors() -> list[str]:
    errors = []
    for dependency in REQUIRED_DEPENDENCIES:
        try:
            importlib.import_module(dependency)
        except Exception as error:
            errors.append(f"Cannot import {dependency}: {error!r}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--preflight", action="store_true")
    arguments = parser.parse_args()

    dependency_errors = _dependency_errors()
    if dependency_errors:
        print(json.dumps({"errors": dependency_errors}, indent=2))
        return 2

    from src.pipelines.formal_layer2r import (
        load_formal_config,
        preflight_formal_layer2r,
        run_formal_layer2r,
    )

    config = load_formal_config(arguments.config)
    preflight = preflight_formal_layer2r(config)
    print(json.dumps(asdict(preflight), indent=2))
    if not preflight.ok:
        return 2
    if arguments.preflight:
        return 0
    result = run_formal_layer2r(config)
    return 1 if result.experiment.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
