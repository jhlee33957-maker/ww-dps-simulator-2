from __future__ import annotations

from lynae_spray_paint_test_helpers import TUNE_RUPTURE_REF, assert_canonical_source_refs, execute_visual_impact


def main() -> None:
    assert_canonical_source_refs()
    sim, row, _activation_time = execute_visual_impact("tune_rupture")
    assert row.lynae_spray_paint_mode_snapshot == "tune_rupture"
    sim.state.character_mechanics_state["lynae"]["lynae_resonance_mode"] = "tune_strain"
    assert sim.execute_action("short_wait")
    events = sim.timeline[-1].scheduled_status_application_events
    assert len(events) == 1
    event = events[0]
    assert event["paint_mode_snapshot"] == "tune_rupture"
    assert event["applied_target_shift_state"] == "tune_rupture_shifting"
    assert event["source_ref"] == TUNE_RUPTURE_REF
    assert sim.state.character_mechanics_state["lynae"]["target_tune_shift_state"] == "tune_rupture_shifting"
    print("lynae_spray_paint_mode_snapshot_smoke_test ok")


if __name__ == "__main__":
    main()
