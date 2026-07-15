from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from search.mcts_production_result import build_compact_artifacts, validate_all


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Validate and ingest all three reviewed v118 50k production seeds")
    value.add_argument("--project-root", type=Path, default=Path("."))
    value.add_argument("--seed-118001-root", type=Path, required=True)
    value.add_argument("--seed-118002-root", type=Path, required=True)
    value.add_argument("--seed-118003-root", type=Path, required=True)
    mode = value.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    return value


def main() -> None:
    args = parser().parse_args()
    project = args.project_root.resolve()
    roots = {
        seed: (path if path.is_absolute() else project / path).resolve()
        for seed, path in {
            118001: args.seed_118001_root,
            118002: args.seed_118002_root,
            118003: args.seed_118003_root,
        }.items()
    }
    if args.execute:
        result = build_compact_artifacts(project, seed_roots=roots)
    else:
        validated = validate_all(project, seed_roots=roots, replay=True)
        result = {
            "status": "dry_run_validated_no_writes",
            "seeds": {
                str(seed): {
                    "inventory": item["inventory_validation"],
                    "winner": item["winner"],
                    "raw_files_mutated": False,
                }
                for seed, item in validated["seeds"].items()
            },
            "global_optimum_proven": False,
        }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
