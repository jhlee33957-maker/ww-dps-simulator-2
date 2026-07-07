from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rl.evaluation_report import add_generated_damage_summary


BACKFILLED_VERSION = "generated_damage_reporting_v2_backfilled"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Backfill generated mechanic damage summary fields from ppo_timeline.csv."
    )
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    results_dir = args.results_dir
    timeline_path = results_dir / "ppo_timeline.csv"
    summary_path = results_dir / "ppo_evaluation_summary.json"
    if not timeline_path.exists():
        raise SystemExit(f"Missing timeline file: {timeline_path}")
    if not summary_path.exists():
        raise SystemExit(f"Missing summary file: {summary_path}")

    timeline = _load_timeline(timeline_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    total_damage = _float(summary.get("total_damage"))
    if total_damage <= 0.0:
        total_damage = sum(_float(row.get("total_action_damage")) for row in timeline)

    updated = add_generated_damage_summary(summary, timeline, total_damage=total_damage)
    updated["report_generation_version"] = BACKFILLED_VERSION
    summary_path.write_text(json.dumps(updated, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "generated_mechanic_damage_total": updated["generated_mechanic_damage_total"],
                "aemeath_forte_generated_damage_total": updated["aemeath_forte_generated_damage_total"],
                "aemeath_seraphic_duet_followup_normal_count": updated[
                    "aemeath_seraphic_duet_followup_normal_count"
                ],
                "aemeath_seraphic_duet_followup_enhanced_count": updated[
                    "aemeath_seraphic_duet_followup_enhanced_count"
                ],
                "direct_damage_by_category": updated["direct_damage_by_category"],
                "effective_damage_role_breakdown": updated["effective_damage_role_breakdown"],
            },
            indent=2,
        )
    )


def _load_timeline(path: Path) -> list[dict[str, Any]]:
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        return [dict(row) for row in csv.DictReader(file)]


def _float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


if __name__ == "__main__":
    main()
