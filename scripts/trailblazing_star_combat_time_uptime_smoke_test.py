from __future__ import annotations

import copy
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.echo_sets import AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID, trailblazing_star_uptime_seconds
from simulator.simulation import Simulation
from simulator.transition_config import load_transition_config


DATA_DIR = ROOT / "data"


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-8) -> None:
    assert math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def config_for_mode(mode: str = "fusion_burst") -> dict:
    config = copy.deepcopy(load_transition_config(DATA_DIR))
    config.setdefault("mechanics", {}).setdefault("aemeath", {})["aemeath_resonance_mode"] = mode
    return config


def make_sim() -> Simulation:
    return Simulation.from_json(
        DATA_DIR,
        party="aemeath",
        transition_config=config_for_mode("fusion_burst"),
        build_profile_overrides={"aemeath": "aemeath_user_real_01"},
    )


def active_trailblazing_buff(sim: Simulation):
    active = [buff for buff in sim.state.active_buffs if buff.buff_id == AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID]
    assert len(active) == 1
    return active[0]


def trailblazing_windows(sim: Simulation) -> list[dict]:
    return [
        window
        for window in sim.state.echo_set_buff_windows
        if window.get("buff_id") == AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID
    ]


def latest_window(sim: Simulation) -> dict:
    windows = trailblazing_windows(sim)
    assert windows
    return windows[-1]


def execute_zero_combat_liberation(sim: Simulation):
    sim.state.resonance_energy["aemeath"] = sim.characters["aemeath"].resonance_energy_max
    current_before = sim.state.current_time
    combat_before = sim.state.combat_time
    assert sim.execute_action("aemeath_resonance_liberation")
    row = sim.timeline[-1]
    assert row.action_time > 0.0
    assert_close(row.effective_combat_time_cost, 0.0, "zero combat time")
    assert_close(sim.state.current_time, current_before + row.action_time, "current_time elapsed")
    assert_close(sim.state.combat_time, combat_before, "combat_time frozen")
    return row


def activate_after_zero_time_stop() -> Simulation:
    sim = make_sim()
    execute_zero_combat_liberation(sim)
    visual_before_activation = sim.state.current_time
    combat_before_activation = sim.state.combat_time

    assert sim.execute_action("aemeath_basic_form_stage_3")
    row = sim.timeline[-1]
    assert row.aemeath_trailblazing_star_5set_applied_before_triggering_damage is True
    window = latest_window(sim)
    duration = sim.buffs[AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID].duration

    assert_close(window["start_time"], combat_before_activation, "Trailblazing uptime combat start")
    assert not math.isclose(float(window["start_time"]), visual_before_activation, rel_tol=0.0, abs_tol=1e-8)
    assert_close(window["end_time"], combat_before_activation + duration, "Trailblazing uptime combat end")
    return sim


def activate_without_prior_time_stop() -> Simulation:
    sim = make_sim()
    assert sim.execute_action("aemeath_basic_form_stage_3")
    row = sim.timeline[-1]
    assert row.aemeath_trailblazing_star_5set_applied_before_triggering_damage is True
    assert trailblazing_windows(sim)
    return sim


def test_activation_after_complete_time_stop_uses_combat_time() -> None:
    sim = activate_after_zero_time_stop()
    assert_close(latest_window(sim)["start_time"], 0.0, "post-time-stop Trailblazing window start")
    assert sim.state.current_time > sim.state.combat_time
    assert trailblazing_star_uptime_seconds(sim.state, sim.state.combat_time) > 0.0


def test_runtime_duration_and_reported_uptime_alignment() -> None:
    sim = activate_after_zero_time_stop()
    buff = active_trailblazing_buff(sim)
    window = latest_window(sim)
    assert_close(window["end_time"] - sim.state.combat_time, buff.remaining_duration, "interval remaining after activation")
    uptime_before = trailblazing_star_uptime_seconds(sim.state, sim.state.combat_time)
    remaining_before = buff.remaining_duration

    assert sim.execute_action("aemeath_basic_form_stage_1")
    row = sim.timeline[-1]
    assert row.effective_combat_time_cost > 0.0
    assert_close(
        active_trailblazing_buff(sim).remaining_duration,
        remaining_before - row.effective_combat_time_cost,
        "runtime remaining after ordinary action",
    )
    assert_close(
        trailblazing_star_uptime_seconds(sim.state, sim.state.combat_time) - uptime_before,
        row.effective_combat_time_cost,
        "reported uptime after ordinary action",
    )


def test_zero_combat_time_action_while_active_freezes_uptime() -> None:
    sim = activate_without_prior_time_stop()
    remaining_before = active_trailblazing_buff(sim).remaining_duration
    uptime_before = trailblazing_star_uptime_seconds(sim.state, sim.state.combat_time)
    window_before = dict(latest_window(sim))

    execute_zero_combat_liberation(sim)

    assert_close(active_trailblazing_buff(sim).remaining_duration, remaining_before, "remaining after active zero")
    assert_close(trailblazing_star_uptime_seconds(sim.state, sim.state.combat_time), uptime_before, "uptime after active zero")
    assert latest_window(sim) == window_before


def test_partial_expiration_caps_reported_uptime() -> None:
    sim = activate_after_zero_time_stop()
    active_trailblazing_buff(sim).remaining_duration = 0.1
    uptime_before = trailblazing_star_uptime_seconds(sim.state, sim.state.combat_time)
    window_count_before = len(trailblazing_windows(sim))

    assert sim.execute_action("aemeath_basic_form_stage_1")
    row = sim.timeline[-1]
    assert row.effective_combat_time_cost > 0.1
    assert any(detail["aemeath_trailblazing_star_5set_active"] for detail in row.hit_details)
    assert AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID not in [buff.buff_id for buff in sim.state.active_buffs]
    assert_close(
        trailblazing_star_uptime_seconds(sim.state, sim.state.combat_time) - uptime_before,
        0.1,
        "partial expiration uptime",
    )
    assert len(trailblazing_windows(sim)) == window_count_before

    assert sim.execute_action("aemeath_basic_form_stage_1")
    assert sim.timeline[-1].aemeath_trailblazing_star_5set_active is False


def test_refresh_uses_combat_time_and_merges_interval() -> None:
    sim = activate_without_prior_time_stop()
    first_window = dict(latest_window(sim))
    execute_zero_combat_liberation(sim)

    for _ in range(6):
        assert sim.execute_action("short_wait")
    combat_before_refresh = sim.state.combat_time
    visual_before_refresh = sim.state.current_time
    assert sim.execute_action("aemeath_basic_form_stage_3")
    row = sim.timeline[-1]
    assert row.echo_set_buff_refreshed is True

    windows = trailblazing_windows(sim)
    assert len(windows) == 1
    window = windows[0]
    duration = sim.buffs[AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID].duration
    assert_close(window["start_time"], first_window["start_time"], "refresh keeps merged start")
    assert_close(window["end_time"], combat_before_refresh + duration, "refresh combat-time end")
    assert not math.isclose(float(window["end_time"]), visual_before_refresh + duration, rel_tol=0.0, abs_tol=1e-8)
    assert trailblazing_star_uptime_seconds(sim.state, sim.state.combat_time) <= window["duration"]


def main() -> None:
    test_activation_after_complete_time_stop_uses_combat_time()
    test_runtime_duration_and_reported_uptime_alignment()
    test_zero_combat_time_action_while_active_freezes_uptime()
    test_partial_expiration_caps_reported_uptime()
    test_refresh_uses_combat_time_and_merges_interval()
    print("trailblazing_star_combat_time_uptime_smoke_test ok")


if __name__ == "__main__":
    main()
