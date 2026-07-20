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
    callback_cursors: list[tuple[int, int, int]] = []
    original_resolver = simulation._resolve_scheduled_action_packet

    def cursor_probe(packet):
        if frame(packet.scheduled_wall_time) == 82:
            callback_cursors.append(
                (
                    frame(simulation.state.current_time),
                    frame(simulation.state.event_cursor_wall_time),
                    frame(simulation.state.event_cursor_combat_time),
                )
            )
        return original_resolver(packet)

    simulation._resolve_scheduled_action_packet = cursor_probe
    assert simulation.execute_action("aemeath_heavy_attack")
    tail = next(event for event in simulation.state.scheduled_packet_event_log if frame(event["scheduled_wall_time"]) == 82)
    assert callback_cursors == [(74, 82, 82)]
    assert frame(tail["scheduled_wall_time"]) == frame(tail["processed_wall_time"]) == 82
    assert frame(tail["scheduled_combat_time"]) == frame(tail["processed_combat_time"]) == 82
    assert frame(tail["resolved_wall_time"]) == frame(tail["processed_wall_time"])
    assert tail["processed_wall_time"] != 219 / 60
    print("scheduled_packet_actual_processing_time_v124_smoke_test ok host_start=74F cursor=82F processed=82F")


if __name__ == "__main__":
    main()
