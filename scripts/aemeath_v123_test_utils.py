from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


PARTY_ID = "aemeath_mornye_lynae_account_actual_01"


def make_account_sim(*, precombat_elapsed_seconds: float = 4.01) -> Simulation:
    return Simulation.from_json(
        ROOT / "data",
        party=PARTY_ID,
        precombat_elapsed_seconds=precombat_elapsed_seconds,
    )


def aemeath_state(simulation: Simulation) -> dict:
    return simulation.state.character_mechanics_state["aemeath"]


def set_concerto_ready(simulation: Simulation, character_id: str) -> None:
    simulation.state.concerto_energy[character_id] = 100.0
    simulation.state.character_states[character_id]["concerto_energy"] = 100.0
    simulation.state.character_states[character_id]["concerto_ready"] = True


def enter_aemeath_from_lynae(simulation: Simulation):
    """Use real concerto transitions; direct resource setup is fixture-only."""
    set_concerto_ready(simulation, "mornye")
    assert simulation.execute_action("swap_to_lynae")
    assert simulation.timeline[-1].resolved_action_id == "transition:lynae_intro_time_to_show_some_colors"
    set_concerto_ready(simulation, "lynae")
    assert "swap_to_aemeath" in simulation.valid_action_ids()
    assert simulation.execute_action("swap_to_aemeath")
    row = simulation.timeline[-1]
    assert row.resolved_action_id == "transition:aemeath_qte_intro_human"
    assert row.outgoing_outro_applied is True
    assert row.incoming_intro_applied is True
    assert row.incoming_intro_candidate_id == "aemeath_qte_intro_human"
    return row


def action_snapshot(simulation: Simulation) -> dict[str, float | bool | str]:
    state = aemeath_state(simulation)
    return {
        "combat_time": round(float(simulation.state.combat_time), 6),
        "form": str(state["form"]),
        "aemeath_combo_stage": int(state["aemeath_combo_stage"]),
        "mech_combo_stage": int(state["mech_combo_stage"]),
        "synchronization_rate": round(float(state["synchronization_rate"]), 6),
        "resonance_rate": round(float(state["resonance_rate"]), 6),
        "seraphic_duo_remaining": round(float(state["seraphic_duo_remaining"]), 6),
        "starlume_acceleration_remaining": round(float(state["starlume_acceleration_remaining"]), 6),
        "instant_response": bool(state["instant_response"]),
        "instant_response_consumed": bool(state["instant_response_consumed"]),
        "radiance_ready": bool(state.get("account_radiance_quick_charge_ready", False)),
        "finale_available": bool(state["finale_available"]),
    }
