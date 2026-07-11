from __future__ import annotations

from mornye_syntony_field_heal_test_helpers import (
    EXPECTED_NORMAL_HEAL,
    NORMAL_HEAL,
    assert_close,
    execute_to_geopotential,
    make_sim,
    scheduled_heals,
)


def wait_until_swap_heal_due(sim, *, max_next_tick: float = 0.5) -> None:
    for _ in range(20):
        effect = sim.scheduled_effect_by_instance_id(NORMAL_HEAL)
        assert effect is not None
        if 0.0 < effect.time_until_next_tick <= max_next_tick:
            return
        before = len(scheduled_heals(sim))
        assert sim.execute_action("short_wait")
        assert len(scheduled_heals(sim)) == before
    raise AssertionError("scheduled heal did not become due during generic swap window")


def assert_generic_swap_heal(row, *, outgoing: str, incoming: str) -> dict:
    assert row.resolved_action_id == f"swap_to_{incoming}"
    assert row.action_type == "swap"
    assert row.fallback_swap_used is True
    assert row.incoming_intro_applied is False
    assert row.active_character_before == outgoing
    assert row.active_character_after == incoming
    assert len(row.scheduled_healing_events) == 1
    heal = row.scheduled_healing_events[0]
    assert heal["host_action_id"] == row.resolved_action_id
    assert heal["host_action_type"] == "swap"
    assert heal["outgoing_character_id"] == outgoing
    assert heal["incoming_character_id"] == incoming
    assert heal["host_actor_character_id"] == incoming
    assert_close(heal["host_combat_start_time"], row.combat_time_start, "generic swap host combat start")
    assert_close(heal["host_combat_end_time"], row.combat_time_end, "generic swap host combat end")
    assert heal["source_character_id"] == "mornye"
    assert heal["target_character_id"] == incoming
    assert heal["team_heal_event_emitted"] is True
    assert heal["applied_weapon_effect_ids"] == []
    assert heal["source_ref"] == "角色-女!4120 / 角色技能类型!533"
    assert_close(heal["calculated_heal_amount"], EXPECTED_NORMAL_HEAL, "generic swap heal amount")
    assert row.team_heal_event_triggered is False
    assert row.halo_of_starry_radiance_5set_same_action_application is False
    return heal


def setup_mornye_field():
    sim = make_sim()
    execute_to_geopotential(sim)
    return sim


def test_mornye_to_lynae_generic_swap_targets_lynae() -> None:
    sim = setup_mornye_field()
    wait_until_swap_heal_due(sim)
    before = len(scheduled_heals(sim))
    assert sim.state.active_character_id == "mornye"
    assert sim.state.concerto_energy.get("mornye", 0.0) < 100.0
    assert sim.execute_action("swap_to_lynae")
    row = sim.timeline[-1]
    assert_generic_swap_heal(row, outgoing="mornye", incoming="lynae")
    assert len(scheduled_heals(sim)) == before + 1
    assert sim.state.active_character_id == "lynae"


def test_lynae_to_aemeath_generic_swap_targets_aemeath() -> None:
    sim = setup_mornye_field()
    wait_until_swap_heal_due(sim)
    assert sim.execute_action("swap_to_lynae")
    wait_until_swap_heal_due(sim)
    before = len(scheduled_heals(sim))
    assert sim.state.active_character_id == "lynae"
    assert sim.state.concerto_energy.get("lynae", 0.0) < 100.0
    assert sim.execute_action("swap_to_aemeath")
    row = sim.timeline[-1]
    assert_generic_swap_heal(row, outgoing="lynae", incoming="aemeath")
    assert len(scheduled_heals(sim)) == before + 1
    assert sim.state.active_character_id == "aemeath"


def test_aemeath_to_mornye_generic_swap_targets_mornye() -> None:
    sim = setup_mornye_field()
    wait_until_swap_heal_due(sim)
    assert sim.execute_action("swap_to_lynae")
    wait_until_swap_heal_due(sim)
    assert sim.execute_action("swap_to_aemeath")
    wait_until_swap_heal_due(sim)
    before = len(scheduled_heals(sim))
    assert sim.state.active_character_id == "aemeath"
    assert sim.execute_action("swap_to_mornye")
    row = sim.timeline[-1]
    assert_generic_swap_heal(row, outgoing="aemeath", incoming="mornye")
    assert len(scheduled_heals(sim)) == before + 1
    assert sim.state.active_character_id == "mornye"


def test_wait_targets_current_active_actor() -> None:
    sim = setup_mornye_field()
    wait_until_swap_heal_due(sim)
    assert sim.execute_action("swap_to_lynae")
    wait_until_swap_heal_due(sim)
    assert sim.execute_action("swap_to_aemeath")
    wait_until_swap_heal_due(sim)
    before = len(scheduled_heals(sim))
    assert sim.state.active_character_id == "aemeath"
    assert sim.execute_action("short_wait")
    row = sim.timeline[-1]
    heal = row.scheduled_healing_events[0]
    assert heal["host_action_id"] == "short_wait"
    assert heal["host_action_type"] == "wait"
    assert heal["outgoing_character_id"] == "aemeath"
    assert heal["incoming_character_id"] is None
    assert heal["host_actor_character_id"] == "aemeath"
    assert_close(heal["host_combat_start_time"], row.combat_time_start, "wait host combat start")
    assert_close(heal["host_combat_end_time"], row.combat_time_end, "wait host combat end")
    assert heal["target_character_id"] == "aemeath"
    assert heal["source_character_id"] == "mornye"
    assert len(scheduled_heals(sim)) == before + 1


def test_source_stat_isolation_during_generic_swap() -> None:
    target_changed = setup_mornye_field()
    wait_until_swap_heal_due(target_changed)
    target_changed.characters["lynae"].runtime_def_flat_bonus += 1000.0
    assert target_changed.execute_action("swap_to_lynae")
    heal = target_changed.timeline[-1].scheduled_healing_events[0]
    assert_close(heal["calculated_heal_amount"], EXPECTED_NORMAL_HEAL, "target DEF does not affect generic swap heal")

    source_changed = setup_mornye_field()
    wait_until_swap_heal_due(source_changed)
    source_changed.characters["mornye"].runtime_def_flat_bonus += 100.0
    assert source_changed.execute_action("swap_to_lynae")
    heal = source_changed.timeline[-1].scheduled_healing_events[0]
    assert heal["calculated_heal_amount"] > EXPECTED_NORMAL_HEAL + 94.0
    assert heal["source_character_id"] == "mornye"
    assert heal["target_character_id"] == "lynae"


def main() -> None:
    test_mornye_to_lynae_generic_swap_targets_lynae()
    test_lynae_to_aemeath_generic_swap_targets_aemeath()
    test_aemeath_to_mornye_generic_swap_targets_mornye()
    test_wait_targets_current_active_actor()
    test_source_stat_isolation_during_generic_swap()
    print("mornye_syntony_field_heal_generic_swap_target_smoke_test ok")


if __name__ == "__main__":
    main()
