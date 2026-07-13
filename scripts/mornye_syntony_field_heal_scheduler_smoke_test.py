from __future__ import annotations

from mornye_syntony_field_heal_test_helpers import (
    EXPECTED_NORMAL_DEF,
    EXPECTED_NORMAL_HEAL,
    NORMAL_FRAMES,
    NORMAL_HEAL,
    advance_until_no_effect,
    assert_close,
    execute_to_geopotential,
    frame_offsets,
    make_sim,
    scheduled_heals,
)


def main() -> None:
    sim = make_sim()
    heavy = execute_to_geopotential(sim)
    activation = heavy.combat_time_start + 48.0 / 60.0
    events = heavy.scheduled_damage_events
    assert [(event["event_type"], event["payload_action_id"]) for event in events[:2]] == [
        ("scheduled_heal", "mornye_syntony_field_heal"),
        ("scheduled_damage", "mornye_syntony_field_damage"),
    ]
    heal = events[0]
    assert round((heal["combat_time"] - heavy.combat_time_start) * 60) == 49
    assert_close(heal["source_runtime_def"], EXPECTED_NORMAL_DEF, "normal runtime DEF")
    assert_close(heal["calculated_heal_amount"], EXPECTED_NORMAL_HEAL, "normal heal")
    assert heal["target_character_id"] == "mornye"
    assert heal["team_heal_event_emitted"] is True
    assert heal["damage"] == 0.0 and heal["off_tune_gain"] == 0.0
    assert heal["resonance_energy_gain"] == 0.0 and heal["concerto_energy_gain"] == 0.0

    advance_until_no_effect(sim, NORMAL_HEAL)
    heals = [event for event in scheduled_heals(sim) if event["payload_action_id"] == "mornye_syntony_field_heal"]
    assert frame_offsets(heals, activation) == NORMAL_FRAMES
    assert len(heals) == 9
    print("mornye_syntony_field_heal_scheduler_smoke_test ok")


if __name__ == "__main__":
    main()
