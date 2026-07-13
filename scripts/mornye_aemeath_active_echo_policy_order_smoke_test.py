from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


EXPECTED = [
    "mornye_basic_attack",
    "mornye_heavy_attack",
    "mornye_resonance_skill",
    "mornye_resonance_liberation",
    "mornye_tune_break",
    "swap_to_aemeath",
    "aemeath_basic_attack",
    "aemeath_resonance_skill",
    "aemeath_heavy_attack",
    "aemeath_resonance_liberation",
    "aemeath_tune_break",
    "short_wait",
    "lynae_basic_attack",
    "lynae_spark_collision",
    "lynae_resonance_skill",
    "lynae_resonance_liberation",
    "lynae_echo_hyvatia",
    "lynae_tune_break",
    "lynae_polychrome_leap",
    "lynae_visual_impact",
    "lynae_iridescent_splash",
    "swap_to_mornye",
    "swap_to_lynae",
    "mornye_echo_reactor_husk",
    "aemeath_echo_sigillum",
]


def main() -> None:
    sim = Simulation.from_json("data", selected_character_ids="aemeath_mornye_lynae_enabled_test_party")
    assert list(sim.policy_actions) == EXPECTED
    assert len(sim.policy_actions) == 25
    print("mornye_aemeath_active_echo_policy_order_smoke_test ok")


if __name__ == "__main__":
    main()
