from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.reward import calculate_reward
from env.wuwa_env import WuwaDpsEnv
from simulator.buff_system import apply_buff
from scheduled_effect_test_helpers import (
    PARTY_ID,
    assert_close,
    make_sim,
    schedule_mornye_fixture,
    snapshot_player_side_effect_state,
)


def test_direct_scheduled_damage_side_effects() -> None:
    sim = make_sim(initial_active="aemeath")
    schedule_mornye_fixture(sim, time_until_next_tick=1.0)
    effect = sim.scheduled_effect_by_instance_id("sched:mornye:field")
    before = snapshot_player_side_effect_state(sim)
    action_log_count = len(sim.state.action_log)
    event = sim.execute_scheduled_damage_event(
        effect=effect,
        host_action_id="manual_scheduler_probe",
        combat_time=sim.state.combat_time,
        host_action_combat_offset=0.0,
        trigger_index=1,
    )
    after = snapshot_player_side_effect_state(sim)
    assert event["event_type"] == "scheduled_damage"
    assert event["payload_action_id"] == "mornye_syntony_field_damage"
    assert event["source_character_id"] == "mornye"
    assert event["damage"] > 0.0
    assert after["active_character_id"] == before["active_character_id"] == "aemeath"
    assert_close(after["current_time"], before["current_time"], "manual scheduled current time")
    assert_close(after["combat_time"], before["combat_time"], "manual scheduled combat time")
    assert after["resonance_energy"] == before["resonance_energy"]
    assert after["concerto_energy"] == before["concerto_energy"]
    assert after["character_state"] == before["character_state"]
    assert after["cooldowns"] == before["cooldowns"]
    assert after["weapon_effect_cooldowns"] == before["weapon_effect_cooldowns"]
    assert len(sim.state.action_log) == action_log_count
    assert all(log.get("action_id") != "mornye_syntony_field_damage" for log in sim.state.action_log)
    assert sim.state.scheduled_effect_event_log[-1]["event_type"] == "scheduled_damage"


def test_host_action_and_reward_accounting() -> None:
    sim = make_sim(initial_active="mornye")
    schedule_mornye_fixture(sim, time_until_next_tick=0.1)
    before_damage = sim.state.total_damage
    assert sim.execute_action("short_wait")
    row = sim.timeline[-1]
    damage_delta = sim.state.total_damage - before_damage
    assert row.scheduled_damage > 0.0
    assert_close(row.damage, row.direct_action_damage + row.scheduled_damage, "row total damage split")
    assert_close(damage_delta, row.damage, "state damage delta")

    env = WuwaDpsEnv(data_dir="data", party=PARTY_ID, initial_active_character="mornye")
    env.reset()
    env.simulation.schedule_effect(
        instance_id="sched:mornye:field",
        effect_id="test_mornye_field_scheduler_fixture",
        source_character_id="mornye",
        source_action_id="scheduler_fixture_source",
        payload_action_id="mornye_syntony_field_damage",
        remaining_duration=8.0,
        tick_interval=2.0,
        time_until_next_tick=0.1,
        source_status="scheduler_test_fixture",
    )
    action_index = env.action_ids.index("short_wait")
    before_env_damage = env.simulation.state.total_damage
    _obs, reward, _terminated, _truncated, info = env.step(action_index)
    delta = env.simulation.state.total_damage - before_env_damage
    assert_close(info["damage_this_action"], delta, "env damage delta")
    assert_close(reward, calculate_reward(delta), "env reward")
    assert env.simulation.timeline[-1].scheduled_damage > 0.0


def test_buffs_debuffs_and_interfered_marker_once() -> None:
    baseline = make_sim(initial_active="mornye")
    schedule_mornye_fixture(baseline, time_until_next_tick=0.1)
    assert baseline.execute_action("short_wait")
    base_event = baseline.timeline[-1].scheduled_damage_events[0]
    base_damage = base_event["damage"]

    amped = make_sim(initial_active="mornye")
    apply_buff(
        amped.state,
        amped.buffs["mornye_interfered_marker_damage_amp"],
        "mornye",
    )
    amped.state.target_interfered_state = "tune_rupture_interfered"
    amped.state.target_interfered_remaining = 8.0
    amped.state.interfered_marker_remaining = 8.0
    amped.state.interfered_marker_damage_taken_amp = 0.40
    schedule_mornye_fixture(amped, time_until_next_tick=0.1)
    assert amped.execute_action("short_wait")
    event = amped.timeline[-1].scheduled_damage_events[0]
    assert event["damage"] > base_damage * 1.39
    assert event["damage"] < base_damage * 1.41
    direct_hits = [hit for hit in event["hit_details"] if hit.get("hit_damage_category") == "normal"]
    assert direct_hits
    assert all(hit["target_damage_taken_amp"] == 0.40 for hit in direct_hits)
    assert all(hit["target_damage_taken_multiplier"] == 1.40 for hit in direct_hits)
    assert all(hit["interfered_marker_amp_applied_to_direct_damage"] for hit in direct_hits)
    assert all(abs(float(hit.get("applied_damage_amp", 0.0) or 0.0)) < 1e-9 for hit in direct_hits)
    assert_close(amped.timeline[-1].scheduled_damage, event["damage"], "scheduled damage counted once")
    assert_close(
        amped.state.total_damage,
        amped.timeline[-1].direct_action_damage + amped.timeline[-1].scheduled_damage,
        "party damage counted once",
    )


def main() -> None:
    test_direct_scheduled_damage_side_effects()
    test_host_action_and_reward_accounting()
    test_buffs_debuffs_and_interfered_marker_once()
    print("scheduled_damage_execution_smoke_test ok")


if __name__ == "__main__":
    main()
