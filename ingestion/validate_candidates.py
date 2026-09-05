#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.curated_data import load_curated_dataset, validate_curated_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the reviewed public-domain tarot CSV package.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=BACKEND / "data" / "curated",
        help="Directory containing the curated CSV files.",
    )
    args = parser.parse_args()

    dataset = load_curated_dataset(args.data_dir)
    report = validate_curated_dataset(dataset)
    for warning in report.warnings:
        print(f"WARNING: {warning}")
    if report.errors:
        for error in report.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    metrics = ", ".join(f"{key}={value}" for key, value in sorted(report.metrics.items()))
    print(f"Curated tarot dataset valid: {metrics}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
