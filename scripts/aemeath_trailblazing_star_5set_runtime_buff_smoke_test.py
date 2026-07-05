from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.echo_sets import AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID
from simulator.simulation import Simulation
from simulator.transition_config import load_transition_config


def config_for_mode(mode: str) -> dict:
    config = copy.deepcopy(load_transition_config(DATA_DIR))
    config.setdefault("mechanics", {}).setdefault("aemeath", {})["aemeath_resonance_mode"] = mode
    return config


def make_sim(mode: str = "fusion_burst") -> Simulation:
    return Simulation.from_json(
        DATA_DIR,
        party="aemeath",
        transition_config=config_for_mode(mode),
        build_profile_overrides={"aemeath": "aemeath_user_real_01"},
    )


def test_trigger_applies_after_action_and_not_retroactively() -> None:
    sim = make_sim("fusion_burst")
    assert sim.characters["aemeath"].echo_sets["trailblazing_star"]["conditional_5set_enabled"] is True
    assert sim.execute_action("aemeath_basic_form_stage_3")

    summary = sim.summary()
    row = summary.timeline[-1]
    assert row.emitted_mechanic_event_tags == ["fusion_burst"]
    assert row.echo_set_triggered_buff_ids == [AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID]
    assert row.echo_set_buff_refreshed is False
    assert row.aemeath_trailblazing_star_5set_active is True
    assert AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID in row.active_buffs
    assert AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID in summary.echo_set_active_buffs
    assert summary.aemeath_trailblazing_star_5set_trigger_count == 1
    assert summary.aemeath_trailblazing_star_5set_uptime_seconds == 0.0
    assert summary.aemeath_trailblazing_star_5set_buff_windows

    assert math.isclose(row.crit_rate_before_buffs, 0.832, rel_tol=1e-9)
    assert math.isclose(row.crit_rate_after_buffs, 0.832, rel_tol=1e-9)
    assert math.isclose(row.echo_set_damage_bonus, 0.0, abs_tol=1e-12)
    assert math.isclose(row.runtime_element_damage_bonus, 0.0, abs_tol=1e-12)
    assert row.hit_details
    assert all(not detail["aemeath_trailblazing_star_5set_active"] for detail in row.hit_details)


def test_next_action_receives_crit_and_fusion_damage_bonus() -> None:
    sim = make_sim("fusion_burst")
    assert sim.execute_action("aemeath_basic_form_stage_3")
    assert sim.execute_action("aemeath_basic_form_stage_1")

    row = sim.summary().timeline[-1]
    assert sim.summary().aemeath_trailblazing_star_5set_uptime_seconds > 0.0
    assert row.echo_set_triggered_buff_ids == []
    assert row.aemeath_trailblazing_star_5set_active is True
    assert math.isclose(row.crit_rate_before_buffs, 0.832, rel_tol=1e-9)
    assert math.isclose(row.crit_rate_after_buffs, 1.032, rel_tol=1e-9)
    assert row.damage_element == "fusion"
    assert math.isclose(row.echo_set_damage_bonus, 0.2, rel_tol=1e-9)
    assert math.isclose(row.runtime_element_damage_bonus, 0.2, rel_tol=1e-9)
    assert math.isclose(row.element_dmg_bonus, 0.6, rel_tol=1e-9)


def test_tune_rupture_event_also_triggers_and_refreshes() -> None:
    sim = make_sim("tune_rupture")
    assert sim.execute_action("aemeath_basic_form_stage_3")
    first = sim.summary().timeline[-1]
    assert first.emitted_mechanic_event_tags == ["tune_rupture_shifting"]
    assert first.echo_set_triggered_buff_ids == [AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID]

    sim.state.combat_time += 3.0
    sim.state.current_time += 3.0
    assert sim.execute_action("aemeath_basic_form_stage_3")
    second_summary = sim.summary()
    second = second_summary.timeline[-1]
    assert second.emitted_mechanic_event_tags == ["tune_rupture_shifting"]
    assert second.echo_set_triggered_buff_ids == [AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID]
    assert second.echo_set_buff_refreshed is True
    assert second_summary.aemeath_trailblazing_star_5set_trigger_count == 2
    assert len(second_summary.aemeath_trailblazing_star_5set_buff_windows) == 1


def test_unresolved_mode_does_not_activate_buff() -> None:
    sim = make_sim("unresolved")
    assert sim.execute_action("aemeath_basic_form_stage_3")
    summary = sim.summary()
    row = summary.timeline[-1]
    assert row.emitted_mechanic_event_tags == []
    assert row.echo_set_triggered_buff_ids == []
    assert row.aemeath_trailblazing_star_5set_active is False
    assert AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID not in row.active_buffs
    assert summary.aemeath_trailblazing_star_5set_enabled is True
    assert summary.aemeath_trailblazing_star_5set_trigger_count == 0
    assert summary.echo_set_active_buffs == []


def main() -> None:
    test_trigger_applies_after_action_and_not_retroactively()
    test_next_action_receives_crit_and_fusion_damage_bonus()
    test_tune_rupture_event_also_triggers_and_refreshes()
    test_unresolved_mode_does_not_activate_buff()
    print("aemeath_trailblazing_star_5set_runtime_buff_smoke_test ok")


if __name__ == "__main__":
    main()
