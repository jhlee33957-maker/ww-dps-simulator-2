from __future__ import annotations

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-8) -> None:
    assert math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def main() -> None:
    sim = Simulation.from_json("data", selected_character_ids="aemeath_mornye_lynae_enabled_test_party", initial_active_character="mornye")
    sim.state.resonance_energy["mornye"] = 0.0
    assert sim.execute_action("mornye_echo_reactor_husk")
    row = sim.timeline[-1]

    assert row.action_id == "mornye_echo_reactor_husk"
    assert_close(row.action_time, 1.1, "action time")
    assert_close(row.combat_time_cost, 1.1, "combat time cost")
    assert_close(row.hit_details[0]["hit_time"], 49.0 / 60.0, "hit time")
    assert row.damage > 0.0
    assert_close(row.damage, 2071.3932654700507, "Reactor Husk damage", tolerance=1e-6)
    assert row.damage_bonus_category == "echo_ability"
    assert row.hit_details[0]["damage_bonus_category"] == "echo_ability"
    assert row.hit_details[0]["scaling_stat"] == "atk"
    assert_close(row.hit_details[0]["scaling_value"], 1159.1645, "hit scaling value")
    assert_close(row.hit_details[0]["static_atk"], 1159.1645, "hit static ATK")
    assert_close(row.hit_details[0]["effective_atk"], 1159.1645, "hit effective ATK")
    assert_close(row.hit_details[0]["final_atk_reference"], 1159.1645, "hit final ATK reference")
    assert_close(row.base_resonance_energy_gain, 4.87, "base RE")
    assert_close(row.energy_regen, 2.5424, "Mornye ER")
    assert_close(row.final_resonance_energy_gain, 12.381488, "final RE")
    assert_close(sim.state.resonance_energy["mornye"], 12.381488, "state RE")
    assert_close(sim.state.cooldowns["mornye_echo_reactor_husk"], 20.0, "cooldown")
    action = sim.actions["mornye_echo_reactor_husk"]
    assert action.off_tune_value == 0.0
    assert action.off_tune_value_source_status == "unresolved_echo_off_tune"
    print("mornye_active_echo_runtime_smoke_test ok")


if __name__ == "__main__":
    main()
