from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.buff_system import apply_buff, support_stat_context
from simulator.echo_sets import (
    MORNYE_HIGH_SYNTONY_FIELD_DEF_BUFF_ID,
    MORNYE_HIGH_SYNTONY_FIELD_OFF_TUNE_BUFF_ID,
    MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID,
    apply_syntony_field_off_tune_buff,
)
from simulator.simulation import Simulation


DATA_DIR = ROOT / "data"
TIMING_MODE = "same_action_high_syntony_field_creation_approximation"


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-8) -> None:
    assert math.isclose(actual, expected, rel_tol=tol, abs_tol=tol), f"{label}: expected {expected}, got {actual}"


def make_sim(mode: str = "simplified_syntony_field_uptime") -> Simulation:
    sim = Simulation.from_json(
        DATA_DIR,
        party="aemeath_mornye_test_party",
        initial_active_character="mornye",
        build_profile_overrides={
            "aemeath": "aemeath_user_real_01",
            "mornye": "mornye_user_real_01",
        },
        transition_config={"mechanics": {"mornye": {"mornye_heal_event_mode": mode}}},
    )
    sim.state.resonance_energy["mornye"] = sim.characters["mornye"].resonance_energy_max
    return sim


def prime_syntony(sim: Simulation) -> None:
    sim.state.character_states["mornye"]["syntony_field_remaining"] = 25.0
    apply_syntony_field_off_tune_buff(state=sim.state, constellation=0)


def test_data_buff_definition() -> None:
    buffs = {item["id"]: item for item in json.loads((DATA_DIR / "buffs.json").read_text(encoding="utf-8-sig"))}
    buff = buffs[MORNYE_HIGH_SYNTONY_FIELD_DEF_BUFF_ID]
    assert_close(buff["duration"], 25.0, "High Syntony DEF duration")
    assert_close(buff["stat_modifiers"]["def_percent"], 0.20, "High Syntony DEF percent")
    assert buff["target"] in {"team", "party"}
    assert buff["target_scope"] in {"team", "party"}


def test_requires_active_syntony_field() -> None:
    sim = make_sim()
    assert sim.execute_action("mornye_resonance_liberation")
    row = sim.timeline[-1]
    assert row.high_syntony_field_active is False
    assert row.high_syntony_field_unavailable_reason == "requires_active_syntony_field"
    assert sim.state.character_states["mornye"]["high_syntony_field_remaining"] == 0.0


def test_high_syntony_runtime_support_and_damage_formula() -> None:
    sim = make_sim()
    prime_syntony(sim)
    base_def = sim.characters["mornye"].effective_def
    expected_def = sim.characters["mornye"].static_def + sim.characters["mornye"].base_def_total * 0.20

    assert sim.execute_action("mornye_resonance_liberation")
    row = sim.timeline[-1]
    state = sim.state.character_states["mornye"]
    assert row.resolved_action_id == "mornye_liberation_critical_protocol"
    assert row.high_syntony_field_same_action_application is True
    assert row.high_syntony_field_application_timing == TIMING_MODE
    assert row.critical_protocol_high_syntony_created_before_damage is True
    assert state["syntony_field_remaining"] == 0.0
    assert state["high_syntony_field_remaining"] > 0.0
    assert state["high_syntony_field_created_count"] == 1
    assert MORNYE_HIGH_SYNTONY_FIELD_DEF_BUFF_ID in row.active_buffs
    assert MORNYE_HIGH_SYNTONY_FIELD_OFF_TUNE_BUFF_ID in row.active_buffs
    assert_close(row.runtime_def_percent_bonus, 0.20, "runtime DEF bonus")
    assert_close(row.effective_def, expected_def, "effective DEF with High Syntony")
    assert row.effective_def > base_def
    assert row.scaling_stat == "def"
    assert row.high_syntony_field_def_bonus_active is True
    assert row.high_syntony_field_off_tune_inherited is True
    assert_close(row.current_off_tune_buildup_rate, 1.5, "current Off-Tune")
    assert row.c2_off_tune_bonus_active is False
    assert row.high_syntony_field_heal_proxy_active is True
    assert row.halo_of_starry_radiance_5set_active is True
    assert_close(row.halo_of_starry_radiance_5set_atk_percent_bonus, 0.25, "Halo cap")
    assert row.halo_atk_buff_does_not_affect_mornye_def_damage is True
    assert all(float(event.get("damage_added", 0.0)) == 0.0 for event in sim.state.mechanic_event_log)
    assert all(log["action_id"] != "mornye_syntony_field_damage" for log in sim.state.damage_log)

    context = support_stat_context(sim.characters["mornye"], sim.state, sim.buffs)
    assert_close(context["current_off_tune_buildup_rate"], 1.5, "post-action Off-Tune")
    sim.characters["mornye"].energy_regen = 9.99
    context_after_er_change = support_stat_context(sim.characters["mornye"], sim.state, sim.buffs)
    assert_close(context_after_er_change["current_off_tune_buildup_rate"], 1.5, "Energy Regen does not affect Off-Tune")


def test_high_def_does_not_add_atk_or_hp_and_expiry() -> None:
    sim = make_sim("disabled")
    prime_syntony(sim)
    assert sim.execute_action("mornye_resonance_liberation")
    base_atk = sim.characters["aemeath"].effective_atk
    base_hp = sim.characters["aemeath"].effective_hp
    assert sim.execute_action("swap_to_aemeath")
    assert sim.execute_action("aemeath_basic_attack")
    row = sim.timeline[-1]
    assert row.high_syntony_field_def_bonus_active is True
    assert_close(row.runtime_def_percent_bonus, 0.20, "Aemeath receives runtime DEF")
    assert_close(row.effective_atk, base_atk, "High Syntony DEF does not add ATK")
    assert_close(row.effective_hp, base_hp, "High Syntony DEF does not add HP")

    while sim.state.character_states["mornye"]["high_syntony_field_remaining"] > 0.0:
        assert sim.execute_action("short_wait")
    assert not any(
        buff.buff_id in {MORNYE_HIGH_SYNTONY_FIELD_DEF_BUFF_ID, MORNYE_HIGH_SYNTONY_FIELD_OFF_TUNE_BUFF_ID}
        for buff in sim.state.active_buffs
    )


def test_field_creation_only_heal_proxy() -> None:
    sim = make_sim("field_creation_only")
    prime_syntony(sim)
    assert sim.execute_action("mornye_resonance_liberation")
    row = sim.timeline[-1]
    assert row.high_syntony_field_heal_proxy_active is True
    assert row.team_heal_event_triggered is True
    assert MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID in row.echo_set_triggered_buff_ids


def main() -> None:
    test_data_buff_definition()
    test_requires_active_syntony_field()
    test_high_syntony_runtime_support_and_damage_formula()
    test_high_def_does_not_add_atk_or_hp_and_expiry()
    test_field_creation_only_heal_proxy()
    print("mornye_high_syntony_field_runtime_buff_smoke_test ok")


if __name__ == "__main__":
    main()
