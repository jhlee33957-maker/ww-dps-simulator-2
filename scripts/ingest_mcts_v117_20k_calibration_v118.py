from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from search.mcts_completed_result import build_compact_artifacts, validate_calibration


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Validate and ingest the reviewed candidate-117 20k MCTS calibration")
    value.add_argument("--project-root", type=Path, default=Path("."))
    value.add_argument("--output-root", type=Path, required=True)
    mode = value.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    return value


def main() -> None:
    args = parser().parse_args(); project_root = args.project_root.resolve()
    output_root = args.output_root if args.output_root.is_absolute() else project_root / args.output_root
    if args.execute:
        result = build_compact_artifacts(project_root, output_root)
    else:
        validated = validate_calibration(project_root, output_root, replay=True)
        result = {"status": "dry_run_validated_no_writes", "inventory": validated["inventory_validation"],
                  "winner": validated["winner"], "global_optimum_proven": False}
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
