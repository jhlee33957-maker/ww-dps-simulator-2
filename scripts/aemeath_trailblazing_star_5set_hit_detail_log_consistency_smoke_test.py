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


BASE_CRIT_RATE = 0.832
BUFFED_CRIT_RATE = 1.032


def config_for_mode(mode: str) -> dict:
    config = copy.deepcopy(load_transition_config(DATA_DIR))
    config.setdefault("mechanics", {}).setdefault("aemeath", {})["aemeath_resonance_mode"] = mode
    return config


def make_sim(mode: str) -> Simulation:
    return Simulation.from_json(
        DATA_DIR,
        party="aemeath",
        transition_config=config_for_mode(mode),
        build_profile_overrides={"aemeath": "aemeath_user_real_01"},
    )


def assert_hits_match_action_and_damage_log(sim: Simulation, expected_event_tags: list[str]) -> None:
    row = sim.summary().timeline[-1]
    damage_log = sim.state.damage_log[-1]
    assert damage_log["emitted_mechanic_event_tags"] == expected_event_tags
    assert damage_log["echo_set_triggered_buff_ids"] == row.echo_set_triggered_buff_ids
    assert row.hit_details
    for detail in row.hit_details:
        assert detail["emitted_mechanic_event_tags"] == expected_event_tags
        assert detail["echo_set_triggered_buff_ids"] == row.echo_set_triggered_buff_ids
        assert detail["echo_set_buff_refreshed"] == row.echo_set_buff_refreshed
        assert detail["mechanic_event_triggered"] == row.mechanic_event_triggered
        assert detail["mechanic_event_cooldown_blocked"] == row.mechanic_event_cooldown_blocked
        assert detail["aemeath_trailblazing_star_5set_applied_before_triggering_damage"] == (
            row.aemeath_trailblazing_star_5set_applied_before_triggering_damage
        )
        assert detail["trailblazing_star_5set_same_action_application"] == (
            row.trailblazing_star_5set_same_action_application
        )
        assert detail["trailblazing_star_5set_application_timing"] == row.trailblazing_star_5set_application_timing


def test_fusion_trigger_hit_details() -> None:
    sim = make_sim("fusion_burst")
    assert sim.execute_action("aemeath_basic_form_stage_3")
    row = sim.summary().timeline[-1]
    assert row.echo_set_triggered_buff_ids == [AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID]
    assert_hits_match_action_and_damage_log(sim, ["fusion_burst"])
    for detail in row.hit_details:
        assert detail["aemeath_trailblazing_star_5set_active"] is True
        assert detail["aemeath_trailblazing_star_5set_applied_before_triggering_damage"] is True
        assert math.isclose(detail["crit_rate_after_buffs"], BUFFED_CRIT_RATE, rel_tol=1e-9)
        assert math.isclose(detail["echo_set_damage_bonus"], 0.2, rel_tol=1e-9)


def test_tune_rupture_trigger_hit_details() -> None:
    sim = make_sim("tune_rupture")
    assert sim.execute_action("aemeath_basic_form_stage_3")
    assert_hits_match_action_and_damage_log(sim, ["tune_rupture_shifting"])


def test_unresolved_hit_details() -> None:
    sim = make_sim("unresolved")
    assert sim.execute_action("aemeath_basic_form_stage_3")
    row = sim.summary().timeline[-1]
    assert_hits_match_action_and_damage_log(sim, [])
    for detail in row.hit_details:
        assert detail["aemeath_trailblazing_star_5set_active"] is False
        assert detail["aemeath_trailblazing_star_5set_applied_before_triggering_damage"] is False
        assert detail["trailblazing_star_5set_same_action_application"] is False
        assert detail["echo_set_triggered_buff_ids"] == []
        assert math.isclose(detail["crit_rate_after_buffs"], BASE_CRIT_RATE, rel_tol=1e-9)


def test_cooldown_blocked_hit_details() -> None:
    sim = make_sim("fusion_burst")
    assert sim.execute_action("aemeath_basic_form_stage_3")
    assert sim.execute_action("aemeath_basic_form_stage_3")
    row = sim.summary().timeline[-1]
    assert row.mechanic_event_cooldown_blocked is True
    assert row.echo_set_triggered_buff_ids == []
    assert_hits_match_action_and_damage_log(sim, [])
    for detail in row.hit_details:
        assert detail["aemeath_trailblazing_star_5set_active"] is True
        assert detail["aemeath_trailblazing_star_5set_applied_before_triggering_damage"] is False
        assert detail["trailblazing_star_5set_same_action_application"] is False
        assert detail["echo_set_triggered_buff_ids"] == []


def test_active_buff_non_trigger_hit_details() -> None:
    sim = make_sim("fusion_burst")
    assert sim.execute_action("aemeath_basic_form_stage_3")
    assert sim.execute_action("aemeath_basic_form_stage_1")
    row = sim.summary().timeline[-1]
    assert row.aemeath_trailblazing_star_5set_active is True
    assert row.echo_set_triggered_buff_ids == []
    assert_hits_match_action_and_damage_log(sim, [])
    for detail in row.hit_details:
        assert detail["aemeath_trailblazing_star_5set_active"] is True
        assert detail["aemeath_trailblazing_star_5set_applied_before_triggering_damage"] is False
        assert detail["trailblazing_star_5set_same_action_application"] is False
        assert detail["echo_set_triggered_buff_ids"] == []


def main() -> None:
    test_fusion_trigger_hit_details()
    test_tune_rupture_trigger_hit_details()
    test_unresolved_hit_details()
    test_cooldown_blocked_hit_details()
    test_active_buff_non_trigger_hit_details()
    print("aemeath_trailblazing_star_5set_hit_detail_log_consistency_smoke_test ok")


if __name__ == "__main__":
    main()
