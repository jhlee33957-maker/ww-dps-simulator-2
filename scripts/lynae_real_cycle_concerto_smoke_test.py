from __future__ import annotations

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
MORNYE_OPENER = [
    "mornye_resonance_skill",
    "mornye_basic_attack",
    "mornye_basic_attack",
    "mornye_basic_attack",
    "mornye_heavy_attack",
    "mornye_resonance_liberation",
    "mornye_resonance_skill",
    "mornye_basic_attack",
    "mornye_basic_attack",
    "mornye_basic_attack",
    "mornye_heavy_attack",
]
LYNAE_SEQUENCE = [
    ("lynae_resonance_skill", 21.83),
    ("lynae_spark_collision", 51.43),
    ("lynae_polychrome_leap", 56.83),
    ("lynae_polychrome_leap", 62.23),
    ("lynae_polychrome_leap", 65.73),
    ("lynae_visual_impact", 80.31),
    ("lynae_resonance_liberation", 100.0),
    ("lynae_echo_hyvatia", 100.0),
]


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-6) -> None:
    assert math.isclose(actual, expected, rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party=PARTY_ID, initial_active_character="mornye")
    assert sim.characters["mornye"].weapon["weapon_id"] == "discord"
    assert sim.characters["mornye"].weapon["rank"] == 5

    for action_id in MORNYE_OPENER:
        assert sim.execute_action(action_id), action_id
    assert_close(sim.state.concerto_energy["mornye"], 100.0, "Mornye Concerto before Lynae swap")

    assert sim.execute_action("swap_to_lynae")
    intro = sim.timeline[-1]
    assert intro.resolved_action_id == "transition:lynae_intro_time_to_show_some_colors"
    assert intro.incoming_intro_event_id == "lynae_intro_time_to_show_some_colors"
    assert intro.outgoing_outro_event_id == "mornye_outro_recursion"
    assert intro.swap_timing_is_placeholder is False
    assert_close(sim.state.concerto_energy["lynae"], 12.0, "after Intro")

    for action_id, expected_concerto in LYNAE_SEQUENCE:
        assert sim.execute_action(action_id), action_id
        assert_close(sim.state.concerto_energy["lynae"], expected_concerto, f"after {action_id}")

    assert_close(sim.state.concerto_energy["lynae"], 100.0, "Lynae clamped Concerto")
    assert_close(sim.state.wasted_concerto_energy["lynae"], 0.31, "Lynae wasted Concerto")
    assert_close(
        sim.state.concerto_energy["lynae"] + sim.state.wasted_concerto_energy["lynae"],
        100.31,
        "Lynae unclamped Concerto",
    )

    assert sim.execute_action("swap_to_aemeath")
    transition = sim.timeline[-1]
    assert transition.outgoing_character_id == "lynae"
    assert transition.outgoing_outro_event_id == "lynae_outro_lets_hit_the_road"
    assert transition.outgoing_outro_applied is True
    assert transition.incoming_character_id == "aemeath"
    assert transition.incoming_intro_event_id == "aemeath_qte_intro_human"
    assert transition.resolved_action_id == "transition:aemeath_qte_intro_human"
    assert transition.swap_timing_is_placeholder is False
    assert sim.state.concerto_energy["lynae"] == 0.0
    assert sim.state.active_character_id == "aemeath"
    assert "lynae_outro_all_damage_amp" in transition.applied_buffs
    assert "lynae_outro_liberation_damage_amp" in transition.applied_buffs
    assert "static_mist_incoming_atk" in transition.applied_buffs
    assert "pact_neonlight_incoming_atk" in transition.applied_buffs

    print("lynae_real_cycle_concerto_smoke_test ok")


if __name__ == "__main__":
    main()
