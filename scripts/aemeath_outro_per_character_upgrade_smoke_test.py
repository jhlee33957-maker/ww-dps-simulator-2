from __future__ import annotations

from v114_test_support import add_event_action, assert_close, build, outro_instances, set_concerto, value


def check_mode(mode: str, event_tag: str) -> None:
    sim = build()
    sim.state.mechanics_config.setdefault("aemeath", {})["aemeath_resonance_mode"] = mode
    set_concerto(sim, "aemeath")
    assert sim.execute_action("swap_to_mornye")
    action_id = add_event_action(sim, "mornye", event_tag)
    before_remaining = outro_instances(sim)["mornye"].remaining_duration
    assert sim.execute_action(action_id)
    row = sim.timeline[-1]
    instances = outro_instances(sim)
    assert value(instances["mornye"]) == 0.2
    assert value(instances["lynae"]) == 0.1
    assert row.aemeath_outro_upgraded_character_ids == ["mornye"]
    assert row.aemeath_outro_upgrade_event_tag == event_tag
    assert not row.aemeath_outro_upgrade_duration_refreshed
    assert_close(instances["mornye"].remaining_duration, before_remaining - 0.5)
    # Triggering damage captured the pre-upgrade 10% action-start value.
    assert row.hit_details[0]["applied_damage_amp"] == 0.1


def main() -> None:
    check_mode("tune_rupture", "tune_rupture_shifting")
    check_mode("fusion_burst", "fusion_burst")
    print("aemeath_outro_per_character_upgrade_smoke_test ok")


if __name__ == "__main__":
    main()
