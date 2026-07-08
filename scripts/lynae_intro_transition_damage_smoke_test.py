from __future__ import annotations

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation
from simulator.transition_actions import get_transition_action, transition_action_to_action_data


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
INTRO_ID = "lynae_intro_time_to_show_some_colors"
RESOLVED_ID = f"transition:{INTRO_ID}"


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-6) -> None:
    assert math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def set_full_concerto(sim: Simulation, character_id: str) -> None:
    sim.state.concerto_energy[character_id] = 100.0
    sim.state.character_states[character_id]["concerto_energy"] = 100.0
    sim.state.character_states[character_id]["concerto_ready"] = True


def main() -> None:
    record = get_transition_action(ROOT / "data", INTRO_ID)
    assert record is not None
    assert record["transition_event_type"] == "incoming_intro_qte"
    assert record["transition_only"] is True
    assert record["policy_selectable"] is False
    assert record["exclude_from_policy_action_space"] is True
    assert record["character_id"] == "lynae"
    assert record["trigger_classification"] == "intro"
    assert record["damage_bonus_category"] == "intro"
    assert record["element"] == "spectro"
    assert record["scaling_stat"] == "atk"
    assert_close(record["action_time"], 1.0, "action_time")
    assert_close(record["combat_time_cost"], 1.0, "combat_time_cost")
    assert record["hits"] == [0.2248] * 10
    assert_close(sum(record["hits"]), 2.248, "total multiplier")
    assert_close(record["resonance_energy_gain"], 1.34, "resonance gain")
    assert_close(record["concerto_energy_gain"], 1.2, "concerto gain")
    assert record["apply_character_mechanics"] is False
    assert record["mechanic_effects"]["overflow_gain"] == 100.0
    assert record["mechanic_effects"]["applies_photocromic_flux"] is True

    action = transition_action_to_action_data(record)
    assert action.id == RESOLVED_ID
    assert action.policy_selectable is False
    assert action.mechanic_effects["skip_character_after_action"] is True

    sim = Simulation.from_json(ROOT / "data", party=PARTY_ID)
    sim.state.active_character_id = "aemeath"
    set_full_concerto(sim, "aemeath")
    assert sim.execute_action("swap_to_lynae")
    row = sim.timeline[-1]
    state = sim.state.character_mechanics_state["lynae"]

    assert row.selected_action_id == "swap_to_lynae"
    assert row.resolved_action_id == RESOLVED_ID
    assert row.incoming_intro_candidate_id == INTRO_ID
    assert row.incoming_intro_applied is True
    assert row.incoming_intro_mode == "enabled"
    assert row.fallback_swap_used is False
    assert row.outgoing_concerto_consumed is True
    assert row.outgoing_concerto_after == 0.0
    assert row.damage > 0.0
    assert row.total_action_damage == row.damage
    assert row.damage_bonus_category == "intro"
    assert row.damage_element == "spectro"
    assert row.scaling_stat == "atk"
    assert_close(row.action_time, 1.0, "row action_time")
    assert_close(row.combat_time_cost, 1.0, "row combat_time_cost")
    assert_close(row.concerto_gain, 1.2, "row concerto_gain")
    assert_close(row.base_resonance_energy_gain, 1.34, "row base_resonance_energy_gain")
    assert row.lynae_overflow == 100.0
    assert state["overflow"] == 100.0
    assert state["overflow"] != 200.0
    assert row.lynae_photocromic_flux_active is True
    assert row.lynae_photocromic_flux_remaining == 25.0
    assert state["photocromic_flux_active"] is True
    assert state["photocromic_flux_source_action_id"] == INTRO_ID
    assert "lynae_intro_spectro_damage_bonus" in row.applied_buffs
    assert any(
        event.get("action_id") == INTRO_ID
        and event.get("transition_action_id") == INTRO_ID
        and event.get("applied") is True
        for event in row.transition_events
    )

    print(
        "lynae_intro_transition_damage_smoke_test ok",
        {
            "resolved_action_id": row.resolved_action_id,
            "damage": row.damage,
            "combat_time_cost": row.combat_time_cost,
            "overflow": state["overflow"],
            "photocromic_flux_active": state["photocromic_flux_active"],
        },
    )


if __name__ == "__main__":
    main()
