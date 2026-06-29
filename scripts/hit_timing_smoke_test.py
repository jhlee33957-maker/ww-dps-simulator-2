from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.models import AnomalyState
from simulator.simulation import Simulation


def main() -> None:
    sim = Simulation.from_json(PROJECT_ROOT / "data", selected_character_ids=["main", "sub", "support"])
    sim.execute_action("main_resonance_liberation")
    row = sim.timeline[-1]
    print("Multi-hit action:", row.action_id)
    print("Action time:", row.action_time)
    print("Hit count:", row.hit_count)
    print("Hit details:", row.hit_details)
    print("Total action damage:", row.total_action_damage)
    print("Hit category sum:", sum(row.hit_damage_by_category.values()))

    timing = Simulation.from_json(PROJECT_ROOT / "data", selected_character_ids=["main", "sub", "support"])
    timing.state.active_anomalies["havoc_bane"] = AnomalyState(
        anomaly_type="havoc_bane",
        stacks=5,
        remaining_duration=0.30,
        tick_interval=1.0,
        tick_timer=1.0,
    )
    timing.execute_action("main_resonance_liberation")
    timed_row = timing.timeline[-1]
    print("Havoc timing hit details:", timed_row.hit_details)
    reductions = [hit["applied_havoc_bane_def_reduction"] for hit in timed_row.hit_details]
    print("Havoc reductions by hit:", reductions)
    print("Early hit has Havoc Bane:", reductions[0] > 0.0)
    print("Later hit lost Havoc Bane:", reductions[-1] == 0.0)


if __name__ == "__main__":
    main()
