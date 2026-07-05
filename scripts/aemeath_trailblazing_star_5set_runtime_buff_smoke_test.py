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


def make_sim(mode: str = "fusion_burst") -> Simulation:
    return Simulation.from_json(
        DATA_DIR,
        party="aemeath",
        transition_config=config_for_mode(mode),
        build_profile_overrides={"aemeath": "aemeath_user_real_01"},
    )


def assert_trigger_damage_receives_buff(row, expected_event_tag: str) -> None:
    assert row.emitted_mechanic_event_tags == [expected_event_tag]
    assert row.echo_set_triggered_buff_ids == [AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID]
    assert row.aemeath_trailblazing_star_5set_active is True
    assert row.aemeath_trailblazing_star_5set_applied_before_triggering_damage is True
    assert row.trailblazing_star_5set_same_action_application is True
    assert row.trailblazing_star_5set_application_timing == "same_action_aggregate_approximation"
    assert math.isclose(row.crit_rate_before_buffs, BASE_CRIT_RATE, rel_tol=1e-9)
    assert math.isclose(row.crit_rate_after_buffs, BUFFED_CRIT_RATE, rel_tol=1e-9)
    assert row.damage_element == "fusion"
    assert math.isclose(row.echo_set_damage_bonus, 0.2, rel_tol=1e-9)
    assert math.isclose(row.runtime_element_damage_bonus, 0.2, rel_tol=1e-9)
    assert math.isclose(row.element_dmg_bonus, 0.6, rel_tol=1e-9)
    assert row.hit_details
    assert all(detail["aemeath_trailblazing_star_5set_active"] for detail in row.hit_details)
    assert all(math.isclose(detail["crit_rate_after_buffs"], BUFFED_CRIT_RATE, rel_tol=1e-9) for detail in row.hit_details)
    for detail in row.hit_details:
        if detail["hit_damage_category"] != "normal":
            continue
        assert detail["aemeath_trailblazing_star_5set_applied_before_triggering_damage"] is True
        assert detail["trailblazing_star_5set_same_action_application"] is True
        assert detail["trailblazing_star_5set_application_timing"] == "same_action_aggregate_approximation"
        assert detail["echo_set_triggered_buff_ids"] == [AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID]
        assert detail["echo_set_buff_refreshed"] == row.echo_set_buff_refreshed
        assert detail["emitted_mechanic_event_tags"] == [expected_event_tag]
        assert detail["mechanic_event_triggered"] is True
        assert detail["mechanic_event_trigger_id"] == "aemeath_resonance_mode_damage_trigger"
        assert detail["mechanic_event_cooldown_blocked"] is False
        assert detail["aemeath_resonance_mode"] in {"fusion_burst", "tune_rupture"}
        assert math.isclose(detail["echo_set_damage_bonus"], 0.2, rel_tol=1e-9)
        assert math.isclose(detail["runtime_element_damage_bonus"], 0.2, rel_tol=1e-9)


def test_fusion_burst_triggering_action_receives_buff() -> None:
    sim = make_sim("fusion_burst")
    assert sim.characters["aemeath"].echo_sets["trailblazing_star"]["conditional_5set_enabled"] is True
    assert sim.execute_action("aemeath_basic_form_stage_3")

    summary = sim.summary()
    row = summary.timeline[-1]
    assert_trigger_damage_receives_buff(row, "fusion_burst")
    assert row.echo_set_buff_refreshed is False
    assert AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID in row.active_buffs
    assert AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID in summary.echo_set_active_buffs
    assert summary.aemeath_trailblazing_star_5set_trigger_count == 1
    assert summary.aemeath_trailblazing_star_5set_buff_windows
    assert sim.state.damage_log[-1]["aemeath_trailblazing_star_5set_applied_before_triggering_damage"] is True


def test_tune_rupture_triggering_action_receives_buff() -> None:
    sim = make_sim("tune_rupture")
    assert sim.execute_action("aemeath_basic_form_stage_3")
    assert_trigger_damage_receives_buff(sim.summary().timeline[-1], "tune_rupture_shifting")


def test_unresolved_mode_does_not_activate_buff() -> None:
    sim = make_sim("unresolved")
    assert sim.execute_action("aemeath_basic_form_stage_3")
    summary = sim.summary()
    row = summary.timeline[-1]
    assert row.emitted_mechanic_event_tags == []
    assert row.echo_set_triggered_buff_ids == []
    assert row.aemeath_trailblazing_star_5set_active is False
    assert row.aemeath_trailblazing_star_5set_applied_before_triggering_damage is False
    assert math.isclose(row.crit_rate_after_buffs, BASE_CRIT_RATE, rel_tol=1e-9)
    assert math.isclose(row.echo_set_damage_bonus, 0.0, abs_tol=1e-12)
    for detail in row.hit_details:
        assert detail["aemeath_trailblazing_star_5set_applied_before_triggering_damage"] is False
        assert detail["trailblazing_star_5set_same_action_application"] is False
        assert detail["trailblazing_star_5set_application_timing"] is None
        assert detail.get("echo_set_triggered_buff_ids", []) == []
        assert detail["emitted_mechanic_event_tags"] == []
        assert detail["mechanic_event_triggered"] is False
        assert math.isclose(detail["crit_rate_after_buffs"], BASE_CRIT_RATE, rel_tol=1e-9)
        assert math.isclose(detail["echo_set_damage_bonus"], 0.0, abs_tol=1e-12)
    assert AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID not in row.active_buffs
    assert summary.aemeath_trailblazing_star_5set_enabled is True
    assert summary.aemeath_trailblazing_star_5set_trigger_count == 0
    assert summary.echo_set_active_buffs == []


def test_non_trigger_action_does_not_newly_activate_buff() -> None:
    sim = make_sim("fusion_burst")
    assert sim.execute_action("aemeath_basic_form_stage_1")
    row = sim.summary().timeline[-1]
    assert row.emitted_mechanic_event_tags == []
    assert row.echo_set_triggered_buff_ids == []
    assert row.aemeath_trailblazing_star_5set_active is False
    assert math.isclose(row.crit_rate_after_buffs, BASE_CRIT_RATE, rel_tol=1e-9)


def test_non_trigger_action_benefits_while_buff_is_active() -> None:
    sim = make_sim("fusion_burst")
    assert sim.execute_action("aemeath_basic_form_stage_3")
    assert sim.execute_action("aemeath_basic_form_stage_1")
    row = sim.summary().timeline[-1]
    assert row.echo_set_triggered_buff_ids == []
    assert row.aemeath_trailblazing_star_5set_active is True
    assert math.isclose(row.crit_rate_after_buffs, BUFFED_CRIT_RATE, rel_tol=1e-9)
    assert math.isclose(row.echo_set_damage_bonus, 0.2, rel_tol=1e-9)
    for detail in row.hit_details:
        assert detail["aemeath_trailblazing_star_5set_active"] is True
        assert detail["aemeath_trailblazing_star_5set_applied_before_triggering_damage"] is False
        assert detail["trailblazing_star_5set_same_action_application"] is False
        assert detail.get("echo_set_triggered_buff_ids", []) == []


def test_same_action_cooldown_blocks_refresh_but_existing_buff_remains() -> None:
    sim = make_sim("fusion_burst")
    assert sim.execute_action("aemeath_basic_form_stage_3")
    first_remaining = next(buff.remaining_duration for buff in sim.state.active_buffs if buff.buff_id == AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID)
    assert sim.execute_action("aemeath_basic_form_stage_3")

    summary = sim.summary()
    row = summary.timeline[-1]
    second_remaining = next(buff.remaining_duration for buff in sim.state.active_buffs if buff.buff_id == AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID)
    assert row.emitted_mechanic_event_tags == []
    assert row.mechanic_event_cooldown_blocked is True
    assert row.echo_set_triggered_buff_ids == []
    assert row.aemeath_trailblazing_star_5set_active is True
    assert row.aemeath_trailblazing_star_5set_applied_before_triggering_damage is False
    assert math.isclose(row.crit_rate_after_buffs, BUFFED_CRIT_RATE, rel_tol=1e-9)
    assert summary.aemeath_trailblazing_star_5set_trigger_count == 1
    assert second_remaining < first_remaining
    for detail in row.hit_details:
        assert detail["mechanic_event_cooldown_blocked"] is True
        assert detail["aemeath_trailblazing_star_5set_active"] is True
        assert detail["aemeath_trailblazing_star_5set_applied_before_triggering_damage"] is False
        assert detail["trailblazing_star_5set_same_action_application"] is False
        assert detail.get("echo_set_triggered_buff_ids", []) == []


def test_retrigger_after_cooldown_refreshes_without_stacking() -> None:
    sim = make_sim("fusion_burst")
    assert sim.execute_action("aemeath_basic_form_stage_3")
    for _ in range(6):
        assert sim.execute_action("short_wait")
    assert sim.execute_action("aemeath_basic_form_stage_3")

    summary = sim.summary()
    row = summary.timeline[-1]
    assert row.emitted_mechanic_event_tags == ["fusion_burst"]
    assert row.echo_set_triggered_buff_ids == [AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID]
    assert row.echo_set_buff_refreshed is True
    assert math.isclose(row.crit_rate_after_buffs, BUFFED_CRIT_RATE, rel_tol=1e-9)
    assert summary.aemeath_trailblazing_star_5set_trigger_count == 2
    assert len([buff for buff in sim.state.active_buffs if buff.buff_id == AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID]) == 1


def test_buff_expires_after_eight_seconds() -> None:
    sim = make_sim("fusion_burst")
    assert sim.execute_action("aemeath_basic_form_stage_3")
    for _ in range(17):
        assert sim.execute_action("short_wait")
    assert AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID not in [buff.buff_id for buff in sim.state.active_buffs]
    assert sim.execute_action("aemeath_basic_form_stage_1")
    row = sim.summary().timeline[-1]
    assert row.aemeath_trailblazing_star_5set_active is False
    assert math.isclose(row.crit_rate_after_buffs, BASE_CRIT_RATE, rel_tol=1e-9)
    assert math.isclose(row.echo_set_damage_bonus, 0.0, abs_tol=1e-12)


def test_event_mode_still_adds_no_extra_damage_events() -> None:
    unresolved_damage = make_sim("unresolved")
    fusion_damage = make_sim("fusion_burst")
    assert unresolved_damage.execute_action("aemeath_basic_form_stage_3")
    assert fusion_damage.execute_action("aemeath_basic_form_stage_3")
    unresolved_row = unresolved_damage.summary().timeline[-1]
    fusion_row = fusion_damage.summary().timeline[-1]
    assert unresolved_row.hit_count == fusion_row.hit_count
    assert unresolved_row.direct_anomaly_damage == fusion_row.direct_anomaly_damage == 0.0
    assert unresolved_row.anomaly_tick_damage == fusion_row.anomaly_tick_damage == 0.0
    assert set(fusion_damage.summary().damage_by_resolved_action) == {"aemeath_basic_form_stage_3"}


def main() -> None:
    test_fusion_burst_triggering_action_receives_buff()
    test_tune_rupture_triggering_action_receives_buff()
    test_unresolved_mode_does_not_activate_buff()
    test_non_trigger_action_does_not_newly_activate_buff()
    test_non_trigger_action_benefits_while_buff_is_active()
    test_same_action_cooldown_blocks_refresh_but_existing_buff_remains()
    test_retrigger_after_cooldown_refreshes_without_stacking()
    test_buff_expires_after_eight_seconds()
    test_event_mode_still_adds_no_extra_damage_events()
    print("aemeath_trailblazing_star_5set_runtime_buff_smoke_test ok")


if __name__ == "__main__":
    main()
