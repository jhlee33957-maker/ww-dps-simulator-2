from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import ACCOUNT_SCOPE_ID
from simulator.simulation import Simulation


ACCOUNT_BUILD_OVERRIDES = {
    "aemeath": "aemeath_account_actual_01",
    "lynae": "lynae_account_actual_01",
    "mornye": "mornye_account_actual_01",
}
PARTY = ["aemeath", "lynae", "mornye"]


def make_account_sim(
    initial_active_character: str = "aemeath",
    *,
    precombat: float = 5.0,
    aemeath_resonance_mode: str | None = "tune_rupture",
) -> Simulation:
    simulation = Simulation.from_json(
        ROOT / "data",
        selected_character_ids=PARTY,
        initial_active_character=initial_active_character,
        build_profile_overrides=ACCOUNT_BUILD_OVERRIDES,
        account_simulation_scope=ACCOUNT_SCOPE_ID,
        precombat_elapsed_seconds=precombat,
        account_optical_sampling_active=True,
    )
    if aemeath_resonance_mode is not None:
        simulation.state.mechanics_config.setdefault("aemeath", {})["aemeath_resonance_mode"] = aemeath_resonance_mode
    if aemeath_resonance_mode == "fusion_burst":
        simulation.character_mechanics["aemeath"]._ensure_fusion_minimum_effect(simulation.state)
    return simulation


def ready_aemeath_charged_ii(sim: Simulation) -> None:
    state = sim.state.character_mechanics_state.setdefault("aemeath", {})
    state["instant_response"] = True
    state["account_radiance_quick_charge_ready"] = True


def ready_lynae_visual_impact(sim: Simulation) -> None:
    state = sim.state.character_mechanics_state.setdefault("lynae", {})
    state["kaleidoscopic_parade_remaining"] = 10.0
    state["true_color"] = 3.0


def ready_mornye_distributed_array(sim: Simulation) -> None:
    state = sim.state.character_mechanics_state.setdefault("mornye", {})
    state["mode"] = "wide_field_observation"
    state["wide_field_observation_remaining"] = 10.0


def ready_mornye_inversion(sim: Simulation) -> None:
    state = sim.state.character_mechanics_state.setdefault("mornye", {})
    state["mode"] = "wide_field_observation"
    state["wide_field_observation_remaining"] = 10.0
    state["relative_momentum"] = 100.0


def event_types(result: Any) -> set[str]:
    return {str(event.get("event_type")) for event in result.account_constellation_events}
