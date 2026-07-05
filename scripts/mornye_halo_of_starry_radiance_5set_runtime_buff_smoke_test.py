from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.buff_system import support_stat_context, tick_buffs
from simulator.echo_sets import (
    MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID,
    TEAM_HEAL_EVENT_TAG,
    apply_mornye_halo_of_starry_radiance_5set_event_buff,
    apply_syntony_field_off_tune_buff,
    halo_of_starry_radiance_atk_percent,
)
from simulator.simulation import Simulation


DATA_DIR = ROOT / "data"
TIMING_MODE = "same_action_field_creation_approximation"


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-8) -> None:
    assert abs(actual - expected) <= tol, f"{label}: expected {expected}, got {actual}"


def make_sim(*, constellation: int = 0, heal_mode: str = "disabled") -> Simulation:
    return Simulation.from_json(
        DATA_DIR,
        party="aemeath_mornye_test_party",
        build_profile_overrides={
            "aemeath": "aemeath_user_real_01",
            "mornye": "mornye_user_real_01",
        },
        transition_config={
            "mechanics": {
                "mornye": {
                    "mornye_constellation": constellation,
                    "mornye_heal_event_mode": heal_mode,
                }
            }
        },
    )


def test_data_and_formula() -> None:
    buffs = {item["id"]: item for item in json.loads((DATA_DIR / "buffs.json").read_text(encoding="utf-8-sig"))}
    buff = buffs[MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID]
    assert buff["duration"] == 4.0
    assert buff["target"] in {"team", "party"}
    assert buff["target_scope"] in {"team", "party"}
    assert buff["max_stacks"] == 1
    assert buff["stacking_rule"] == "refresh_duration"
    assert buff["metadata"]["dynamic_value_formula"] == "min(current_off_tune_buildup_rate * 0.20, 0.25)"

    profile = json.loads((DATA_DIR / "build_profiles.json").read_text(encoding="utf-8-sig"))["profiles"]["mornye"]["mornye_user_real_01"]
    assert profile["echo_sets"]["halo_of_starry_radiance"]["pieces"] == 5
    assert_close(halo_of_starry_radiance_atk_percent(1.0), 0.20, "base halo")
    assert_close(halo_of_starry_radiance_atk_percent(1.5), 0.25, "syntony halo cap")
    assert_close(halo_of_starry_radiance_atk_percent(1.7), 0.25, "c2 halo cap")


def test_runtime_application_and_scaling_scope() -> None:
    sim = make_sim()
    sim.characters["mornye"].energy_regen = 9.0
    apply_mornye_halo_of_starry_radiance_5set_event_buff(
        source_character_id="mornye",
        emitted_event_tags=[TEAM_HEAL_EVENT_TAG],
        characters=sim.characters,
        state=sim.state,
        buffs=sim.buffs,
        application_time=sim.state.current_time,
        event_source="test_base_team_heal",
    )
    active = next(buff for buff in sim.state.active_buffs if buff.buff_id == MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID)
    assert_close(active.metadata["dynamic_value"], 0.20, "base dynamic value ignores ER")

    base_atk = sim.characters["aemeath"].effective_atk
    sim.state.active_character_id = "aemeath"
    assert sim.execute_action("aemeath_basic_attack")
    row = sim.timeline[-1]
    assert row.effective_atk > base_atk
    assert row.runtime_atk_percent_bonus >= 0.20

    mornye_def_before = sim.characters["mornye"].effective_def
    sim.state.active_character_id = "mornye"
    sim.state.cooldowns.clear()
    assert sim.execute_action("mornye_basic_attack")
    mornye_row = sim.timeline[-1]
    assert_close(mornye_row.effective_def, mornye_def_before, "Mornye DEF unchanged by ATK buff")


def test_syntony_cap_expiry_refresh_and_no_healing_damage() -> None:
    sim = make_sim()
    apply_syntony_field_off_tune_buff(state=sim.state, constellation=0)
    context = support_stat_context(sim.characters["mornye"], sim.state, sim.buffs)
    assert_close(context["current_off_tune_buildup_rate"], 1.5, "syntony current")
    apply_mornye_halo_of_starry_radiance_5set_event_buff(
        source_character_id="mornye",
        emitted_event_tags=[TEAM_HEAL_EVENT_TAG],
        characters=sim.characters,
        state=sim.state,
        buffs=sim.buffs,
        application_time=0.0,
        event_source="test_syntony_team_heal",
    )
    active = next(buff for buff in sim.state.active_buffs if buff.buff_id == MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID)
    assert_close(active.metadata["dynamic_value"], 0.25, "syntony capped halo")

    apply_mornye_halo_of_starry_radiance_5set_event_buff(
        source_character_id="mornye",
        emitted_event_tags=[TEAM_HEAL_EVENT_TAG],
        characters=sim.characters,
        state=sim.state,
        buffs=sim.buffs,
        application_time=1.0,
        event_source="test_refresh",
    )
    active_halo = [buff for buff in sim.state.active_buffs if buff.buff_id == MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID]
    assert len(active_halo) == 1
    assert active_halo[0].stack_count == 1
    assert_close(active_halo[0].remaining_duration, 4.0, "refreshed duration")

    tick_buffs(sim.state, 4.1)
    assert not any(buff.buff_id == MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID for buff in sim.state.active_buffs)
    assert all(float(event.get("damage_added", 0.0)) == 0.0 for event in sim.state.mechanic_event_log)


def test_field_creation_same_action_timing() -> None:
    for heal_mode in ("field_creation_only", "simplified_syntony_field_uptime"):
        sim = make_sim(heal_mode=heal_mode)
        sim.characters["mornye"].energy_regen = 9.0
        sim.state.character_states["mornye"]["rest_mass_energy"] = 100.0
        assert sim.execute_action("mornye_heavy_attack")
        row = sim.timeline[-1]
        damage_log = sim.state.damage_log[-1]
        assert row.resolved_action_id == "mornye_heavy_geopotential_shift"
        assert row.team_heal_event_triggered is True
        assert row.halo_of_starry_radiance_5set_applied_before_field_creation_damage is True
        assert row.halo_of_starry_radiance_5set_same_action_application is True
        assert row.halo_of_starry_radiance_5set_application_timing == TIMING_MODE
        assert_close(row.current_off_tune_buildup_rate, 1.5, f"{heal_mode} current Off-Tune")
        assert_close(row.halo_of_starry_radiance_5set_atk_percent_bonus, 0.25, f"{heal_mode} Halo cap")
        assert_close(row.runtime_atk_percent_bonus, 0.25, f"{heal_mode} runtime ATK")
        assert row.syntony_field_off_tune_bonus_active is True
        assert MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID in row.echo_set_triggered_buff_ids
        assert damage_log["halo_of_starry_radiance_5set_same_action_application"] is True
        assert damage_log["halo_of_starry_radiance_5set_application_timing"] == TIMING_MODE
        for detail in row.hit_details:
            if detail.get("hit_damage_category") != "normal":
                continue
            assert detail["halo_of_starry_radiance_5set_applied_before_field_creation_damage"] is True
            assert detail["halo_of_starry_radiance_5set_same_action_application"] is True
            assert detail["halo_of_starry_radiance_5set_application_timing"] == TIMING_MODE
            assert_close(detail["current_off_tune_buildup_rate"], 1.5, "hit current Off-Tune")
            assert_close(detail["halo_of_starry_radiance_5set_atk_percent_bonus"], 0.25, "hit Halo cap")

    disabled = make_sim(heal_mode="disabled")
    disabled.state.character_states["mornye"]["rest_mass_energy"] = 100.0
    assert disabled.execute_action("mornye_heavy_attack")
    disabled_row = disabled.timeline[-1]
    assert disabled_row.halo_of_starry_radiance_5set_same_action_application is False
    assert disabled_row.halo_of_starry_radiance_5set_applied_before_field_creation_damage is False

    non_trigger = make_sim(heal_mode="field_creation_only")
    assert non_trigger.execute_action("mornye_basic_attack")
    non_trigger_row = non_trigger.timeline[-1]
    assert non_trigger_row.team_heal_event_triggered is False
    assert non_trigger_row.halo_of_starry_radiance_5set_same_action_application is False


def main() -> None:
    test_data_and_formula()
    test_runtime_application_and_scaling_scope()
    test_syntony_cap_expiry_refresh_and_no_healing_damage()
    test_field_creation_same_action_timing()
    print("mornye_halo_of_starry_radiance_5set_runtime_buff_smoke_test ok")


if __name__ == "__main__":
    main()
