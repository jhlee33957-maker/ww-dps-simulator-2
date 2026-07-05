from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.echo_sets import MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID
from simulator.resource_system import ensure_concerto_state
from simulator.simulation import Simulation


DATA_DIR = ROOT / "data"
TIMING_MODE = "same_action_field_creation_approximation"


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-8) -> None:
    assert math.isclose(actual, expected, rel_tol=tol, abs_tol=tol), f"{label}: expected {expected}, got {actual}"


def make_sim(mode: str = "field_creation_only") -> Simulation:
    sim = Simulation.from_json(
        DATA_DIR,
        party="aemeath_mornye_test_party",
        build_profile_overrides={
            "aemeath": "aemeath_user_real_01",
            "mornye": "mornye_user_real_01",
        },
    )
    sim.state.mechanics_config.setdefault("mornye", {})["mornye_heal_event_mode"] = mode
    sim.transition_config.setdefault("mechanics", {}).setdefault("mornye", {})["mornye_heal_event_mode"] = mode
    return sim


def prepare_geopotential_shift(sim: Simulation) -> None:
    state = sim.state.character_states["mornye"]
    state["mode"] = "baseline"
    state["rest_mass_energy"] = 100.0


def assert_same_action_halo(row, damage_log: dict) -> None:
    assert row.team_heal_event_triggered is True
    assert row.halo_of_starry_radiance_5set_active is True
    assert row.halo_of_starry_radiance_5set_applied_before_field_creation_damage is True
    assert row.halo_of_starry_radiance_5set_same_action_application is True
    assert row.halo_of_starry_radiance_5set_application_timing == TIMING_MODE
    assert row.base_off_tune_buildup_rate == 1.0
    assert_close(row.runtime_off_tune_buildup_rate_bonus, 0.5, "runtime Off-Tune bonus")
    assert_close(row.current_off_tune_buildup_rate, 1.5, "current Off-Tune")
    assert row.syntony_field_off_tune_bonus_active is True
    assert_close(row.syntony_field_off_tune_bonus_value, 0.5, "Syntony Off-Tune")
    assert_close(row.halo_of_starry_radiance_5set_atk_percent_bonus, 0.25, "Halo ATK cap")
    assert MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID in row.echo_set_triggered_buff_ids

    for key in (
        "team_heal_event_triggered",
        "halo_of_starry_radiance_5set_active",
        "halo_of_starry_radiance_5set_applied_before_field_creation_damage",
        "halo_of_starry_radiance_5set_same_action_application",
        "halo_of_starry_radiance_5set_application_timing",
        "current_off_tune_buildup_rate",
        "halo_of_starry_radiance_5set_atk_percent_bonus",
    ):
        assert damage_log[key] == getattr(row, key), key

    assert row.hit_details
    for detail in row.hit_details:
        if detail.get("hit_damage_category") != "normal":
            continue
        assert detail["team_heal_event_triggered"] is True
        assert detail["halo_of_starry_radiance_5set_active"] is True
        assert detail["halo_of_starry_radiance_5set_applied_before_field_creation_damage"] is True
        assert detail["halo_of_starry_radiance_5set_same_action_application"] is True
        assert detail["halo_of_starry_radiance_5set_application_timing"] == TIMING_MODE
        assert_close(detail["current_off_tune_buildup_rate"], 1.5, "hit current Off-Tune")
        assert_close(detail["halo_of_starry_radiance_5set_atk_percent_bonus"], 0.25, "hit Halo ATK cap")


def test_geopotential_shift_same_action_application() -> None:
    sim = make_sim("field_creation_only")
    sim.characters["mornye"].energy_regen = 9.0
    prepare_geopotential_shift(sim)
    assert sim.execute_action("mornye_heavy_attack")
    row = sim.timeline[-1]
    assert row.resolved_action_id == "mornye_heavy_geopotential_shift"
    assert_same_action_halo(row, sim.state.damage_log[-1])
    assert_close(row.runtime_atk_percent_bonus, 0.25, "runtime ATK bonus logged")
    assert_close(row.effective_def, sim.characters["mornye"].effective_def, "Mornye DEF unchanged")
    assert sim.state.total_damage == row.damage
    assert all(float(event.get("damage_added", 0.0)) == 0.0 for event in sim.state.mechanic_event_log)


def test_intro_convergence_same_action_application() -> None:
    sim = make_sim("field_creation_only")
    assert sim.execute_action("swap_to_aemeath")
    sim.transition_config["characters"]["mornye"]["intro_qte"]["mode"] = "enabled"
    aemeath_state = sim.state.character_states["aemeath"]
    ensure_concerto_state(aemeath_state)
    aemeath_state["concerto_energy"] = aemeath_state["concerto_energy_cap"]
    aemeath_state["concerto_ready"] = True
    sim.state.concerto_energy["aemeath"] = aemeath_state["concerto_energy"]

    assert sim.execute_action("swap_to_mornye")
    row = sim.timeline[-1]
    assert row.resolved_action_id == "transition:mornye_intro_convergence"
    assert row.incoming_intro_applied is True
    assert_same_action_halo(row, sim.state.damage_log[-1])


def test_disabled_and_non_trigger_actions_do_not_same_action_apply() -> None:
    disabled = make_sim("disabled")
    prepare_geopotential_shift(disabled)
    assert disabled.execute_action("mornye_heavy_attack")
    row = disabled.timeline[-1]
    assert row.team_heal_event_triggered is False
    assert row.halo_of_starry_radiance_5set_same_action_application is False
    assert row.halo_of_starry_radiance_5set_applied_before_field_creation_damage is False

    non_trigger = make_sim("field_creation_only")
    assert non_trigger.execute_action("mornye_basic_attack")
    row = non_trigger.timeline[-1]
    assert row.team_heal_event_triggered is False
    assert row.halo_of_starry_radiance_5set_same_action_application is False
    assert MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID not in row.echo_set_triggered_buff_ids


def test_active_halo_benefits_later_atk_actions_expires_and_retriggers() -> None:
    sim = make_sim("field_creation_only")
    prepare_geopotential_shift(sim)
    assert sim.execute_action("mornye_heavy_attack")
    assert len([buff for buff in sim.state.active_buffs if buff.buff_id == MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID]) == 1

    base_aemeath_atk = sim.characters["aemeath"].effective_atk
    assert sim.execute_action("swap_to_aemeath")
    assert sim.execute_action("aemeath_basic_attack")
    atk_row = sim.timeline[-1]
    assert atk_row.halo_of_starry_radiance_5set_same_action_application is False
    assert atk_row.effective_atk > base_aemeath_atk
    assert atk_row.runtime_atk_percent_bonus >= 0.25

    while any(buff.buff_id == MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID for buff in sim.state.active_buffs):
        assert sim.execute_action("short_wait")
    assert not any(buff.buff_id == MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID for buff in sim.state.active_buffs)

    assert sim.execute_action("swap_to_mornye")
    prepare_geopotential_shift(sim)
    assert sim.execute_action("mornye_heavy_attack")
    halo_buffs = [buff for buff in sim.state.active_buffs if buff.buff_id == MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID]
    assert len(halo_buffs) == 1
    assert halo_buffs[0].stack_count == 1
    assert sim.timeline[-1].echo_set_buff_refreshed is False

    prepare_geopotential_shift(sim)
    assert sim.execute_action("mornye_heavy_attack")
    halo_buffs = [buff for buff in sim.state.active_buffs if buff.buff_id == MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID]
    assert len(halo_buffs) == 1
    assert halo_buffs[0].stack_count == 1
    assert sim.timeline[-1].echo_set_buff_refreshed is True


def main() -> None:
    test_geopotential_shift_same_action_application()
    test_intro_convergence_same_action_application()
    test_disabled_and_non_trigger_actions_do_not_same_action_apply()
    test_active_halo_benefits_later_atk_actions_expires_and_retriggers()
    print("mornye_halo_5set_same_action_timing_smoke_test ok")


if __name__ == "__main__":
    main()
