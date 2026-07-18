from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import ACCOUNT_SCOPE_ID
from simulator.simulation import Simulation


def _simulation() -> Simulation:
    sim = Simulation.from_json(
        ROOT / "data",
        selected_character_ids=["aemeath"],
        initial_active_character="aemeath",
        build_profile_overrides={"aemeath": "aemeath_account_actual_01"},
        account_simulation_scope=ACCOUNT_SCOPE_ID,
        precombat_elapsed_seconds=5.0,
    )
    sim.state.mechanics_config.setdefault("aemeath", {})["aemeath_resonance_mode"] = "tune_rupture"
    return sim


def _ready_tune_break(sim: Simulation) -> None:
    sim.state.enemy_tune_break_available = True
    sim.state.enemy_tune_break_cooldown_remaining = 0.0
    sim.state.enemy_mistune_active = True
    sim.state.target_tune_shift_state = "tune_rupture_shifting"
    sim.state.target_tune_shift_remaining = 8.0


def main() -> None:
    c0 = _simulation()
    c0.state.character_mechanics_state["_account_constellation"]["aemeath_sequence"] = 0
    _ready_tune_break(c0)
    assert c0.execute_action("aemeath_tune_break")
    assert c0.state.rupturous_trail_stacks == 10

    s6 = _simulation()
    _ready_tune_break(s6)
    assert s6.execute_action("aemeath_tune_break")
    assert s6.state.rupturous_trail_stacks == 20
    print("aemeath_s6_party_response_gain_exact_v121_smoke_test ok")


if __name__ == "__main__":
    main()
