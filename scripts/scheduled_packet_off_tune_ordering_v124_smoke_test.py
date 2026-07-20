from __future__ import annotations

from scheduled_packet_chronological_interleaving_v124_smoke_test import PARTY_ID, ROOT, frame
from simulator.simulation import Simulation


def main() -> None:
    simulation = Simulation.from_json(
        ROOT / "data",
        party=PARTY_ID,
        initial_active_character="mornye",
        precombat_elapsed_seconds=4.01,
    )
    assert simulation.execute_action("mornye_basic_stage_1")
    assert simulation.execute_action("mornye_basic_stage_2")
    assert simulation.execute_action("swap_to_aemeath")
    simulation.state.enemy_off_tune_current = simulation.state.enemy_off_tune_max - 4.5
    simulation.state.enemy_mistune_active = False
    simulation.state.enemy_tune_break_available = False
    assert frame(simulation.state.current_time) == 74
    assert simulation.state.enemy_mistune_active is False

    assert simulation.execute_action("aemeath_heavy_attack")
    tail = next(event for event in simulation.state.scheduled_packet_event_log if frame(event["scheduled_wall_time"]) == 82)
    heavy_hit = next(
        event
        for event in simulation.state.chronological_event_log
        if event["event_type"] == "action_hit"
        and event["source_action_id"] == "aemeath_heavy_aemeath_charged_2"
    )
    off_tune_log = tail["off_tune_accumulation_log"]
    assert tail["off_tune_value"] == 9.0
    assert off_tune_log["enemy_off_tune_current_before"] == simulation.state.enemy_off_tune_max - 4.5
    assert off_tune_log["enemy_off_tune_current_after"] == simulation.state.enemy_off_tune_max
    assert off_tune_log["enemy_mistune_entered_this_action"] is True
    assert tail["event_sequence"] < heavy_hit["event_sequence"]
    assert heavy_hit["enemy_mistune_active"] is True
    assert heavy_hit["enemy_tune_break_available"] is True
    print(
        "scheduled_packet_off_tune_ordering_v124_smoke_test ok "
        f"tail=82F(seq={tail['event_sequence']}) mistune=true heavy=219F(seq={heavy_hit['event_sequence']})"
    )


if __name__ == "__main__":
    main()
