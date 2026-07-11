from __future__ import annotations

from lynae_spray_paint_test_helpers import PAYLOAD_ID, TUNE_STRAIN_REF, assert_canonical_source_refs, make_sim


def main() -> None:
    assert_canonical_source_refs()
    sim = make_sim("tune_strain")
    sim.schedule_effect(
        instance_id="test:scheduled_status_application",
        effect_id="test_status_application",
        source_character_id="lynae",
        source_action_id="test",
        payload_action_id=PAYLOAD_ID,
        remaining_duration=1.0,
        tick_interval=1.0,
        time_until_next_tick=1.0,
        max_trigger_count=1,
        payload_event_type="status_application",
        scheduled_resource_policy="none",
        source_status="test_status_application",
        source_ref="test",
        metadata={
            "scheduled_status_effect_id": "lynae_photocromic_flux",
            "paint_mode_snapshot": "tune_strain",
            "target_shift_state_snapshot": "tune_strain_shifting",
            "source_row": TUNE_STRAIN_REF,
            "source_ref": TUNE_STRAIN_REF,
            "target_presence_assumption": "single_target_remains_inside_paint_area",
        },
    )
    effect = sim.scheduled_effect_by_instance_id("test:scheduled_status_application")
    assert effect is not None
    event = sim.execute_scheduled_effect_event(
        effect=effect,
        host_action_id="manual_status_probe",
        combat_time=sim.state.combat_time,
        host_action_combat_offset=0.0,
        trigger_index=1,
    )
    assert event["event_type"] == "scheduled_status_application"
    assert event["payload_event_type"] == "status_application"
    assert event["payload_action_id"] == PAYLOAD_ID
    assert event["paint_mode_snapshot"] == "tune_strain"
    assert event["applied_target_shift_state"] == "tune_strain_shifting"
    assert event["damage"] == 0.0 and event["off_tune_gain"] == 0.0
    print("scheduled_status_application_smoke_test ok")


if __name__ == "__main__":
    main()
