from __future__ import annotations

import copy

from mornye_syntony_field_heal_test_helpers import (
    EXPECTED_NORMAL_DEF,
    EXPECTED_NORMAL_HEAL,
    NORMAL_HEAL,
    assert_close,
    execute_to_geopotential,
    scheduled_heals,
)
from simulator.resource_system import sync_concerto_state
from simulator.simulation import Simulation
from simulator.transition_config import load_transition_config


DATA_DIR = "data"
PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"


def make_transition_sim(initial_active: str = "mornye") -> Simulation:
    config = copy.deepcopy(load_transition_config(DATA_DIR))
    config["concerto_transition"]["qte_mode"] = "enabled"
    return Simulation.from_json(DATA_DIR, party=PARTY_ID, initial_active_character=initial_active, transition_config=config)


def ready(sim: Simulation, character_id: str) -> None:
    state = sync_concerto_state(sim.state, character_id)
    state["concerto_energy"] = 100.0
    state["concerto_ready"] = True
    sim.state.concerto_energy[character_id] = 100.0


def wait_until_next_heal_within(sim: Simulation, seconds: float) -> None:
    for _ in range(20):
        effect = sim.scheduled_effect_by_instance_id(NORMAL_HEAL)
        assert effect is not None
        if 0.0 < effect.time_until_next_tick <= seconds:
            return
        before = len(scheduled_heals(sim))
        assert sim.execute_action("short_wait")
        assert len(scheduled_heals(sim)) == before
    raise AssertionError(f"normal heal did not become due within {seconds}s")


def assert_transition_heal(row, *, actor: str, target: str, source_def: float = EXPECTED_NORMAL_DEF) -> dict:
    heals = row.scheduled_healing_events
    assert len(heals) == 1
    heal = heals[0]
    assert heal["host_action_id"] == row.resolved_action_id
    assert heal["host_action_type"] == row.action_type
    assert heal["outgoing_character_id"] == row.active_character_before
    assert heal["host_actor_character_id"] == actor
    if row.action_type == "swap":
        assert heal["incoming_character_id"] == actor
    else:
        assert heal["incoming_character_id"] is None
    assert heal["source_character_id"] == "mornye"
    assert heal["target_character_id"] == target
    assert_close(heal["host_combat_start_time"], row.combat_time_start, "host combat start")
    assert_close(heal["host_combat_end_time"], row.combat_time_end, "host combat end")
    assert_close(heal["source_runtime_def"], source_def, "source runtime DEF")
    assert heal["team_heal_event_emitted"] is True
    assert heal["halo_of_starry_radiance_5set_same_action_application"] is False
    assert heal["source_ref"] == "角色-女!4120 / 角色技能类型!533"
    return heal


def test_mornye_to_lynae_intro_targets_lynae() -> None:
    sim = make_transition_sim()
    execute_to_geopotential(sim)
    wait_until_next_heal_within(sim, 1.2)
    before_count = len(scheduled_heals(sim))
    assert sim.state.active_character_id == "mornye"
    ready(sim, "mornye")
    assert sim.execute_action("swap_to_lynae")
    row = sim.timeline[-1]
    assert row.resolved_action_id == "transition:lynae_intro_time_to_show_some_colors"
    assert row.active_character_before == "mornye"
    assert row.active_character_after == "lynae"
    heal = assert_transition_heal(row, actor="lynae", target="lynae")
    assert_close(heal["calculated_heal_amount"], EXPECTED_NORMAL_HEAL, "Lynae Intro heal amount")
    assert len(scheduled_heals(sim)) == before_count + 1
    assert sim.state.active_character_id == "lynae"


def test_lynae_to_aemeath_intro_targets_aemeath() -> None:
    sim = make_transition_sim()
    execute_to_geopotential(sim)
    wait_until_next_heal_within(sim, 1.2)
    ready(sim, "mornye")
    assert sim.execute_action("swap_to_lynae")

    wait_until_next_heal_within(sim, 1.0)
    before_count = len(scheduled_heals(sim))
    assert sim.state.active_character_id == "lynae"
    ready(sim, "lynae")
    assert sim.execute_action("swap_to_aemeath")
    row = sim.timeline[-1]
    assert row.resolved_action_id == "transition:aemeath_qte_intro_human"
    assert row.active_character_before == "lynae"
    assert row.active_character_after == "aemeath"
    heal = assert_transition_heal(row, actor="aemeath", target="aemeath")
    assert_close(heal["calculated_heal_amount"], EXPECTED_NORMAL_HEAL, "Aemeath Intro heal amount")
    assert len(scheduled_heals(sim)) == before_count + 1
    assert sim.state.active_character_id == "aemeath"


def test_ordinary_host_action_targets_active_actor() -> None:
    sim = make_transition_sim()
    execute_to_geopotential(sim)
    wait_until_next_heal_within(sim, 1.2)
    ready(sim, "mornye")
    assert sim.execute_action("swap_to_lynae")
    wait_until_next_heal_within(sim, 1.0)
    ready(sim, "lynae")
    assert sim.execute_action("swap_to_aemeath")
    before_count = len(scheduled_heals(sim))
    assert sim.state.active_character_id == "aemeath"
    row = None
    for _ in range(20):
        assert sim.execute_action("aemeath_basic_attack")
        row = sim.timeline[-1]
        if row.scheduled_healing_events:
            break
    assert row is not None
    assert row.scheduled_healing_events
    heal = assert_transition_heal(row, actor="aemeath", target="aemeath")
    assert row.resolved_action_id.startswith("aemeath_")
    assert_close(heal["calculated_heal_amount"], EXPECTED_NORMAL_HEAL, "ordinary action heal amount")
    assert len(scheduled_heals(sim)) == before_count + 1


def test_mornye_intro_targets_mornye_with_temporary_schedule() -> None:
    sim = make_transition_sim(initial_active="aemeath")
    sim.schedule_effect(
        instance_id="test:mornye_intro_scheduled_heal",
        effect_id="test_mornye_intro_scheduled_heal",
        source_character_id="mornye",
        source_action_id="test_setup",
        payload_action_id="mornye_syntony_field_heal",
        remaining_duration=25.0,
        tick_interval=3.0,
        time_until_next_tick=0.5,
        payload_event_type="healing",
        source_status="workbook_confirmed_scheduled_heal",
        source_ref="角色-女!4120 / 角色技能类型!533",
    )
    ready(sim, "aemeath")
    assert sim.execute_action("swap_to_mornye")
    row = sim.timeline[-1]
    assert row.resolved_action_id == "transition:mornye_intro_convergence"
    assert row.active_character_before == "aemeath"
    assert row.active_character_after == "mornye"
    assert_transition_heal(row, actor="mornye", target="mornye")


def test_source_stat_isolation_during_transition_heal() -> None:
    baseline = make_transition_sim()
    execute_to_geopotential(baseline)
    wait_until_next_heal_within(baseline, 1.2)
    baseline.characters["lynae"].runtime_def_flat_bonus += 1000.0
    ready(baseline, "mornye")
    assert baseline.execute_action("swap_to_lynae")
    target_def_heal = baseline.timeline[-1].scheduled_healing_events[0]
    assert_close(target_def_heal["calculated_heal_amount"], EXPECTED_NORMAL_HEAL, "target DEF does not affect heal")

    source_changed = make_transition_sim()
    execute_to_geopotential(source_changed)
    wait_until_next_heal_within(source_changed, 1.2)
    source_changed.characters["mornye"].runtime_def_flat_bonus += 100.0
    ready(source_changed, "mornye")
    assert source_changed.execute_action("swap_to_lynae")
    source_heal = source_changed.timeline[-1].scheduled_healing_events[0]
    assert source_heal["calculated_heal_amount"] > EXPECTED_NORMAL_HEAL + 94.0
    assert source_heal["target_character_id"] == "lynae"
    assert source_heal["source_character_id"] == "mornye"


def main() -> None:
    test_mornye_to_lynae_intro_targets_lynae()
    test_lynae_to_aemeath_intro_targets_aemeath()
    test_ordinary_host_action_targets_active_actor()
    test_mornye_intro_targets_mornye_with_temporary_schedule()
    test_source_stat_isolation_during_transition_heal()
    print("mornye_syntony_field_heal_transition_target_smoke_test ok")


if __name__ == "__main__":
    main()
