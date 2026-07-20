from __future__ import annotations

from scheduled_packet_chronological_interleaving_v124_smoke_test import exact_route, frame


def close(actual: float, expected: float) -> None:
    assert abs(float(actual) - float(expected)) < 1e-9, (actual, expected)


def main() -> None:
    simulation = exact_route()
    mornye = next(row for row in simulation.timeline if row.resolved_action_id == "mornye_basic_stage_2")
    heavy = next(row for row in simulation.timeline if row.resolved_action_id == "aemeath_heavy_aemeath_charged_2")
    tail = next(event for event in mornye.scheduled_damage_events if frame(event["scheduled_wall_time"]) == 82)
    assert len(mornye.scheduled_damage_events) == 6
    close(mornye.scheduled_damage, 2453.3443054141835)
    close(mornye.total_action_damage, 2453.3443054141835)
    close(heavy.direct_action_damage, 33787.202572331465)
    close(heavy.scheduled_damage, 0.0)
    close(heavy.total_action_damage, 33787.202572331465)
    assert tail["owner_character_id"] == "mornye"
    assert tail["source_action_id"] == "mornye_basic_stage_2"
    assert tail["action_instance_id"] == mornye.action_instance_id
    close(sum(row.damage for row in simulation.timeline), simulation.state.total_damage)
    print(
        "scheduled_packet_source_attribution_v124_smoke_test ok "
        "mornye=2453.3443054141835 heavy=33787.202572331465 heavy_scheduled=0"
    )


if __name__ == "__main__":
    main()
