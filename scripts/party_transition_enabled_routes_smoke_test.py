from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.resource_system import ensure_concerto_state
from simulator.roster import read_party_presets
from simulator.simulation import Simulation
from simulator.transition_config import (
    build_effective_transition_config,
    build_transition_mode_overrides,
    get_character_transition_mode,
    load_transition_config,
)


DATA_DIR = PROJECT_ROOT / "data"
BUFF_ID = "mornye_outro_recursion_all_dmg_amp"


def set_concerto(sim: Simulation, character_id: str, amount: float) -> None:
    state = sim.state.character_states[character_id]
    ensure_concerto_state(state)
    state["concerto_energy"] = min(amount, state["concerto_energy_cap"])
    state["concerto_ready"] = state["concerto_energy"] >= state["concerto_energy_cap"]
    sim.state.concerto_energy[character_id] = state["concerto_energy"]


def enabled_config() -> dict:
    presets = read_party_presets(DATA_DIR)
    return build_effective_transition_config(
        load_transition_config(DATA_DIR),
        presets["aemeath_mornye_enabled_test_party"],
    )


def test_a_effective_config_from_enabled_party_preset() -> None:
    config = enabled_config()
    assert get_character_transition_mode(config, "aemeath", "intro_qte") == "enabled"
    assert get_character_transition_mode(config, "mornye", "intro_qte") == "enabled"
    assert get_character_transition_mode(config, "mornye", "outro") is True
    assert "party_preset" in config["_transition_config_source"]


def test_b_mornye_to_aemeath_full_concerto() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_mornye_enabled_test_party")
    assert sim.state.active_character_id == "mornye"
    sim.state.character_states["aemeath"]["form"] = "aemeath"
    set_concerto(sim, "mornye", 100.0)
    assert sim.execute_action("swap_to_aemeath")
    row = sim.timeline[-1]
    assert row.transition_type == "full_concerto_transition"
    assert row.outgoing_outro_event_id == "mornye_outro_recursion"
    assert row.outgoing_outro_applied is True
    assert row.incoming_qte_applied is True
    assert row.incoming_qte_candidate_id == "aemeath_qte_intro_human"
    assert row.outgoing_concerto_consumed is True
    assert row.damage > 0.0
    assert BUFF_ID in row.applied_buffs
    assert BUFF_ID in row.active_buffs
    assert "aemeath_qte_intro_human" not in sim.get_policy_action_ids()
    assert "aemeath_qte_intro_mech" not in sim.get_policy_action_ids()


def test_c_aemeath_to_mornye_full_concerto() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_mornye_enabled_test_party")
    assert sim.execute_action("swap_to_aemeath")
    set_concerto(sim, "aemeath", 100.0)
    assert sim.execute_action("swap_to_mornye")
    row = sim.timeline[-1]
    state = sim.state.character_mechanics_state["mornye"]
    assert row.transition_type == "full_concerto_transition"
    assert row.incoming_intro_applied is True
    assert row.incoming_intro_candidate_id == "mornye_intro_convergence"
    assert state["mode"] == "wide_field_observation"
    assert state["syntony_field_remaining"] == 25.0
    assert row.damage > 0.0
    assert row.outgoing_concerto_consumed is True
    assert "mornye_intro_convergence" not in sim.get_policy_action_ids()
    assert "transition:mornye_intro_convergence" not in sim.get_policy_action_ids()


def test_d_no_concerto_fallback() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_mornye_enabled_test_party")
    set_concerto(sim, "mornye", 50.0)
    assert sim.execute_action("swap_to_aemeath")
    row = sim.timeline[-1]
    assert row.transition_type == "normal_swap"
    assert row.transition_reason == "concerto_not_ready"
    assert row.outgoing_outro_applied is False
    assert row.incoming_qte_applied is False
    assert row.incoming_intro_applied is False
    assert row.fallback_swap_used is True
    assert row.resolved_action_id == "swap_to_aemeath"


def test_e_cli_override_helper_precedence() -> None:
    base = load_transition_config(DATA_DIR)
    broad_enabled = build_effective_transition_config(
        base,
        cli_overrides=build_transition_mode_overrides(transition_mode="enabled"),
    )
    assert get_character_transition_mode(broad_enabled, "aemeath", "intro_qte") == "enabled"
    assert get_character_transition_mode(broad_enabled, "mornye", "intro_qte") == "enabled"

    specific_disabled = build_effective_transition_config(
        base,
        cli_overrides=build_transition_mode_overrides(
            transition_mode="enabled",
            aemeath_qte_mode="disabled",
        ),
    )
    assert get_character_transition_mode(specific_disabled, "aemeath", "intro_qte") == "disabled"
    assert get_character_transition_mode(specific_disabled, "mornye", "intro_qte") == "enabled"


def main() -> None:
    test_a_effective_config_from_enabled_party_preset()
    test_b_mornye_to_aemeath_full_concerto()
    test_c_aemeath_to_mornye_full_concerto()
    test_d_no_concerto_fallback()
    test_e_cli_override_helper_precedence()
    print("Party transition enabled routes smoke test passed.")


if __name__ == "__main__":
    main()
