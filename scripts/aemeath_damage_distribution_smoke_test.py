from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.simulation import Simulation


SEQUENCE = [
    "aemeath_basic_attack",
    "aemeath_resonance_liberation",
    "aemeath_resonance_liberation",
]


def run_sequence(profile: str | None = None) -> tuple[float, dict[str, dict[str, float]], list]:
    sim = Simulation.from_json(
        DATA_DIR,
        party="aemeath",
        build_profile_overrides={"aemeath": profile} if profile else None,
    )
    for action_id in SEQUENCE:
        if not sim.execute_action(action_id):
            sim.execute_action("short_wait")
    by_selected: Counter[str] = Counter()
    by_resolved: Counter[str] = Counter()
    by_bonus_category: Counter[str] = Counter()
    for row in sim.timeline:
        by_selected[row.selected_action_id or row.action_id] += row.total_action_damage
        by_resolved[row.resolved_action_id or row.action_id] += row.total_action_damage
        by_bonus_category[row.damage_bonus_category] += row.total_action_damage
    distributions = {
        "selected_action": dict(by_selected),
        "resolved_action": dict(by_resolved),
        "damage_bonus_category": dict(by_bonus_category),
    }
    print("Damage distribution:", distributions)
    return sim.state.total_damage, distributions, sim.timeline


def test_liberation_profile_changes_distribution() -> None:
    default_total, default_dist, _default_rows = run_sequence()
    focus_total, focus_dist, focus_rows = run_sequence("liberation_focus_test")
    assert focus_total > default_total
    default_liberation_share = default_dist["damage_bonus_category"].get("resonance_liberation", 0.0) / default_total
    focus_liberation_share = focus_dist["damage_bonus_category"].get("resonance_liberation", 0.0) / focus_total
    assert focus_liberation_share > default_liberation_share
    basic_rows = [row for row in focus_rows if row.damage_bonus_category == "basic_attack"]
    assert basic_rows
    assert all(row.category_dmg_bonus == 0.0 for row in basic_rows)
    assert focus_dist["selected_action"]
    assert focus_dist["resolved_action"]


def main() -> None:
    test_liberation_profile_changes_distribution()
    print("aemeath_damage_distribution_smoke_test ok")


if __name__ == "__main__":
    main()
