from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_completed_result import (
    build_compact_artifacts,
    validate_completed_result,
    validate_review_archive,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Validate and ingest the reviewed completed Beam result.")
    result.add_argument("--project-root", type=Path, default=Path("."))
    result.add_argument("--output-root", type=Path, required=True)
    result.add_argument("--review-inventory", type=Path, required=True)
    result.add_argument("--execute", action="store_true", help="Write compact candidate-116 artifacts after validation.")
    return result


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def main() -> None:
    args = parser().parse_args()
    project_root = args.project_root.resolve()
    output_root = _resolve(project_root, args.output_root).resolve()
    review_inventory = _resolve(project_root, args.review_inventory).resolve()
    review_archive = project_root / "beam_search_v115_6p5m_review.zip"
    archive_result = validate_review_archive(review_archive)
    if args.execute:
        result = build_compact_artifacts(
            project_root=project_root,
            output_root=output_root,
            review_inventory=review_inventory,
        )
        result["review_archive"] = archive_result
    else:
        validated = validate_completed_result(
            project_root=project_root,
            output_root=output_root,
            review_inventory=review_inventory,
            replay=True,
        )
        result = {
            "status": "dry_run_completed_result_validated_no_writes",
            "review_archive": archive_result,
            "inventory": validated["inventory_validation"],
            "winning_route_id": validated["winning_route"]["route_id"],
            "winning_damage": validated["winning_route"]["total_damage"],
            "winning_dps": validated["winning_route"]["dps"],
        }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
