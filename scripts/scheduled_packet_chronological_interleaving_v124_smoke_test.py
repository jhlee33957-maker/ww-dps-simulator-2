from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


PARTY_ID = "aemeath_mornye_lynae_account_actual_01"


def frame(value: float) -> int:
    return round(float(value) * 60)


def exact_route() -> Simulation:
    simulation = Simulation.from_json(
        ROOT / "data",
        party=PARTY_ID,
        initial_active_character="mornye",
        precombat_elapsed_seconds=4.01,
    )
    assert simulation.execute_action("mornye_basic_stage_1") and frame(simulation.state.current_time) == 25
    assert simulation.execute_action("mornye_basic_stage_2") and frame(simulation.state.current_time) == 74
    assert simulation.execute_action("swap_to_aemeath") and frame(simulation.state.current_time) == 74
    assert simulation.execute_action("aemeath_heavy_attack") and frame(simulation.state.current_time) == 219
    return simulation


def main() -> None:
    simulation = exact_route()
    tail = next(
        event
        for event in simulation.state.chronological_event_log
        if event["event_type"] == "v124_scheduled_action_packet"
        and event["source_action_id"] == "mornye_basic_stage_2"
        and frame(event["event_wall_time"]) == 82
    )
    heavy_hit = next(
        event
        for event in simulation.state.chronological_event_log
        if event["event_type"] == "action_hit"
        and event["source_action_id"] == "aemeath_heavy_aemeath_charged_2"
    )
    assert frame(tail["event_wall_time"]) == frame(tail["scheduled_wall_time"]) == 82
    assert frame(heavy_hit["event_wall_time"]) == 219
    assert tail["event_sequence"] < heavy_hit["event_sequence"]
    assert tail["action_instance_id"].endswith(":mornye_basic_stage_2")
    assert heavy_hit["action_instance_id"].endswith(":aemeath_heavy_aemeath_charged_2")
    print(
        "scheduled_packet_chronological_interleaving_v124_smoke_test ok "
        f"tail=82F(seq={tail['event_sequence']}) heavy=219F(seq={heavy_hit['event_sequence']})"
    )


if __name__ == "__main__":
    main()
