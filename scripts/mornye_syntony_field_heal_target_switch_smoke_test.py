from __future__ import annotations

from mornye_syntony_field_heal_test_helpers import EXPECTED_NORMAL_HEAL, NORMAL_HEAL, assert_close, execute_to_geopotential, make_sim, scheduled_heals


def main() -> None:
    sim = make_sim()
    execute_to_geopotential(sim)
    assert scheduled_heals(sim)[-1]["target_character_id"] == "mornye"

    sim.state.active_character_id = "lynae"
    while len(scheduled_heals(sim)) < 2:
        assert sim.execute_action("short_wait")
    second = scheduled_heals(sim)[-1]
    assert second["host_action_type"] == "wait"
    assert second["host_actor_character_id"] == "lynae"
    assert second["incoming_character_id"] is None
    assert "host_combat_start_time" in second
    assert "host_combat_end_time" in second
    assert second["target_character_id"] == "lynae"
    assert_close(second["calculated_heal_amount"], EXPECTED_NORMAL_HEAL, "target swap heal unchanged")

    sim.state.active_character_id = "aemeath"
    while len(scheduled_heals(sim)) < 3:
        assert sim.execute_action("short_wait")
    third = scheduled_heals(sim)[-1]
    assert third["host_action_type"] == "wait"
    assert third["host_actor_character_id"] == "aemeath"
    assert third["incoming_character_id"] is None
    assert "host_combat_start_time" in third
    assert "host_combat_end_time" in third
    assert third["target_character_id"] == "aemeath"
    assert_close(third["calculated_heal_amount"], EXPECTED_NORMAL_HEAL, "second target swap heal unchanged")

    sim.characters["mornye"].runtime_def_flat_bonus += 100.0
    while len(scheduled_heals(sim)) < 4 and sim.scheduled_effect_by_instance_id(NORMAL_HEAL) is not None:
        assert sim.execute_action("short_wait")
    fourth = scheduled_heals(sim)[-1]
    assert fourth["calculated_heal_amount"] > EXPECTED_NORMAL_HEAL + 94.0
    print("mornye_syntony_field_heal_target_switch_smoke_test ok")


if __name__ == "__main__":
    main()
