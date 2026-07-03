from __future__ import annotations

import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.action_executor import combat_time_cutoff
from simulator.models import ActionData, CharacterData, HitData
from simulator.simulation import Simulation


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-6) -> None:
    assert math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def make_character() -> CharacterData:
    return CharacterData(
        id="tester",
        name="Tester",
        character_base_atk=1000.0,
        weapon_base_atk=0.0,
        resonance_energy=0.0,
        concerto_energy=0.0,
        active=True,
    )


def make_action(
    action_id: str,
    *,
    action_time: float,
    combat_time_cost: float,
    damage_multiplier: float = 0.0,
    hits: list[HitData] | None = None,
    cooldown: float = 0.0,
) -> ActionData:
    return ActionData(
        id=action_id,
        name=action_id,
        character_id="tester",
        action_type="basic_attack",
        duration=action_time,
        action_time=action_time,
        combat_time_cost=combat_time_cost,
        cooldown=cooldown,
        damage_multiplier=damage_multiplier,
        tune_break_multiplier=0.0,
        tune_break_boost_points=0.0,
        resonance_energy_cost=0.0,
        hits=hits or [],
    )


def make_sim(actions: dict[str, ActionData], combat_duration: float = 120.0) -> Simulation:
    character = make_character()
    return Simulation(
        characters={character.id: character},
        actions=actions,
        buffs={},
        combat_duration=combat_duration,
        selected_character_ids=["tester"],
    )


def test_combat_time_clamp() -> None:
    action = make_action(
        "crossing_hit",
        action_time=0.75,
        combat_time_cost=0.75,
        hits=[HitData(time=0.1, damage_multiplier=1.0)],
    )
    sim = make_sim({"crossing_hit": action})
    sim.state.combat_time = 119.65
    assert sim.execute_action("crossing_hit")
    row = sim.timeline[-1]

    assert_close(sim.state.combat_time, 120.0, "clamped combat_time")
    assert_close(row.combat_time_start, 119.65, "combat_time_start")
    assert_close(row.combat_time_end, 120.0, "combat_time_end")
    assert_close(row.combat_time_cost, 0.75, "full combat_time_cost")
    assert_close(row.effective_combat_time_cost, 0.35, "effective combat_time_cost")
    assert row.truncated_by_combat_limit is True


def test_cooldown_ticks_by_effective_clipped_time() -> None:
    _, effective, truncated = combat_time_cutoff(119.65, 0.75, 120.0)
    assert truncated is True
    assert_close(effective, 0.35, "effective clipped time")

    action = make_action(
        "cooldown_probe",
        action_time=0.75,
        combat_time_cost=0.75,
        hits=[HitData(time=0.1, damage_multiplier=0.0)],
    )
    sim = make_sim({"cooldown_probe": action})
    sim.state.combat_time = 119.65
    sim.state.cooldowns["probe"] = 10.0
    assert sim.execute_action("cooldown_probe")
    assert_close(sim.state.cooldowns["probe"], 9.65, "cooldown after clipped tick")


def test_no_action_after_limit() -> None:
    action = make_action("after_limit", action_time=0.5, combat_time_cost=0.5)
    sim = make_sim({"after_limit": action})
    sim.state.combat_time = 120.0
    before_action_time = sim.state.current_time
    assert sim.execute_action("after_limit") is False
    assert sim.timeline == []
    assert_close(sim.state.combat_time, 120.0, "post-limit combat_time")
    assert_close(sim.state.current_time, before_action_time, "post-limit action_time")


def test_zero_combat_cost_action_before_limit() -> None:
    action = make_action(
        "zero_cost",
        action_time=4.0,
        combat_time_cost=0.0,
        hits=[HitData(time=2.0, damage_multiplier=1.0)],
    )
    sim = make_sim({"zero_cost": action})
    sim.state.combat_time = 119.9
    sim.state.cooldowns["probe"] = 10.0
    assert sim.execute_action("zero_cost")
    row = sim.timeline[-1]

    assert_close(sim.state.combat_time, 119.9, "zero-cost combat_time")
    assert_close(row.effective_combat_time_cost, 0.0, "zero-cost effective tick")
    assert row.truncated_by_combat_limit is False
    assert_close(sim.state.cooldowns["probe"], 10.0, "zero-cost cooldown tick")


def test_untimed_final_crossing_action_excludes_damage() -> None:
    action = make_action(
        "untimed_crossing",
        action_time=0.75,
        combat_time_cost=0.75,
        damage_multiplier=1.0,
    )
    sim = make_sim({"untimed_crossing": action})
    sim.state.combat_time = 119.65
    assert sim.execute_action("untimed_crossing")
    row = sim.timeline[-1]

    assert row.truncated_by_combat_limit is True
    assert_close(row.total_action_damage, 0.0, "cutoff-valid untimed damage")
    assert_close(row.damage_before_cutoff, 0.0, "damage_before_cutoff")
    assert row.damage_after_cutoff_excluded > 0.0
    assert_close(sim.state.total_damage, 0.0, "state total damage")


def test_summary_caps_final_combat_time() -> None:
    action = make_action(
        "repeat",
        action_time=0.6,
        combat_time_cost=0.6,
        hits=[HitData(time=0.1, damage_multiplier=0.0)],
    )
    sim = make_sim({"repeat": action}, combat_duration=1.0)
    while sim.state.combat_time < sim.combat_duration:
        assert sim.execute_action("repeat")

    summary = sim.summary()
    assert_close(summary.final_time, 1.0, "summary final_time")
    assert summary.final_time <= sim.combat_duration + 1e-9
    assert sim.timeline[-1].truncated_by_combat_limit is True


def test_environment_step_after_limit_if_available() -> None:
    try:
        from env.wuwa_env import WuwaDpsEnv
    except ModuleNotFoundError:
        print("Gymnasium dependency missing; skipped env cutoff portion.")
        return

    env = WuwaDpsEnv(PROJECT_ROOT / "data", selected_character_ids=["aemeath"])
    env.reset()
    env.simulation.state.combat_time = env.simulation.combat_duration
    observation, reward, terminated, truncated, info = env.step(0)
    assert observation is not None
    assert reward == 0.0
    assert terminated is True
    assert truncated is False
    assert info["damage_this_action"] == 0.0
    assert info["combat_time"] <= env.simulation.combat_duration


def main() -> None:
    test_combat_time_clamp()
    test_cooldown_ticks_by_effective_clipped_time()
    test_no_action_after_limit()
    test_zero_combat_cost_action_before_limit()
    test_untimed_final_crossing_action_excludes_damage()
    test_summary_caps_final_combat_time()
    test_environment_step_after_limit_if_available()
    print("Combat time cutoff smoke test passed.")


if __name__ == "__main__":
    main()
