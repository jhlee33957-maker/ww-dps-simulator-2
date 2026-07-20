from __future__ import annotations

from v124_timing_test_support import make_sim


def close(actual: float, expected: float) -> None:
    assert abs(actual - expected) < 1e-9, (actual, expected)


def main() -> None:
    sim = make_sim("mornye")
    action = sim.actions["mornye_basic_stage_2"]
    groups = sim.action_timing_contracts[action.id].scheduled_packet_groups
    close(sum(group.damage_payload["damage_multiplier_total"] for group in groups), action.damage_multiplier)
    close(sum(group.resource_payload["off_tune_total"] for group in groups), action.off_tune_value)
    close(sum(group.resource_payload["resonance_energy_total"] for group in groups), action.resonance_energy_gain)
    close(sum(group.resource_payload["concerto_total"] for group in groups), action.concerto_energy_gain)
    close(sum(group.resource_payload["rest_mass_total"] for group in groups), 43.0)
    assert [(group.source_frame_row_ref, group.source_coefficient_resource_row_ref) for group in groups] == [
        ("角色-女!4105", "角色技能类型!2643"),
        ("角色-女!4106", "角色技能类型!2644"),
        ("角色-女!4107", "角色技能类型!2645"),
    ]
    sim.state.resonance_energy["mornye"] = 0.0
    sim.state.concerto_energy["mornye"] = 0.0
    assert sim.execute_action(action.id)
    sim.advance_timing_runtime(8 / 60)
    events = [event for event in sim.state.scheduled_packet_event_log if event.get("source_action_id") == action.id and event.get("packet_instance_id")]
    close(sum(event["damage_payload"]["damage_multiplier"] for event in events), 1.1932)
    close(sum(event["off_tune_value"] for event in events), 33.0)
    assert [
        (round(event["scheduled_wall_time"] * 60), event["off_tune_value"])
        for event in events
    ] == [(11, 12.0), (26, 12.0), (30, 0.0), (39, 0.0), (48, 0.0), (57, 9.0)]
    close(sum(event["base_resonance_energy_gain"] for event in events), 1.92)
    close(sum(event["resource_payload"]["concerto_energy_gain"] for event in events), 6.0)
    close(sim.state.character_mechanics_state["mornye"]["rest_mass_energy"], 43.0)
    print("mornye_basic_stage2_payload_parity_v124_smoke_test ok dmg=1.1932 off=33 re=1.92 concerto=6 rest=43")


if __name__ == "__main__":
    main()
