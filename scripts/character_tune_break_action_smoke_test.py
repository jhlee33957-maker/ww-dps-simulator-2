from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def multipliers(action) -> list[float]:
    return [hit.tune_break_multiplier for hit in action.hits]


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", selected_character_ids="aemeath_mornye_test_party")
    assert "aemeath_tune_break" in sim.actions
    assert "mornye_tune_break" in sim.actions
    assert sim.actions["aemeath_tune_break"].policy_selectable is True
    assert sim.actions["mornye_tune_break"].policy_selectable is True
    assert multipliers(sim.actions["aemeath_tune_break"]) == [1.0, 12.0]
    assert multipliers(sim.actions["mornye_tune_break"]) == [1.7334, 2.2666, 12.0]
    assert sim.actions["aemeath_tune_break"].scaling_stat == "none"
    assert sim.actions["mornye_tune_break"].damage_bonus_category == "tune_break"
    assert sim.is_action_available(sim.actions["mornye_tune_break"]) is False

    sim.state.enemy_tune_break_available = True
    sim.state.enemy_mistune_active = True
    assert sim.is_action_available(sim.actions["mornye_tune_break"]) is True
    assert sim.is_action_available(sim.actions["aemeath_tune_break"]) is False

    assert sim.execute_action("mornye_tune_break")
    row = sim.timeline[-1]
    assert row.tune_break_damage > 0.0
    assert row.scaling_stat == "none"
    assert row.damage_bonus_category == "tune_break"
    assert row.hit_details[0]["tune_break_base_value"] == 10000.0
    assert row.enemy_tune_break_available is False
    assert row.enemy_tune_break_cooldown_remaining > 0.0

    aemeath = Simulation.from_json(
        ROOT / "data",
        selected_character_ids="aemeath_mornye_test_party",
        initial_active_character="aemeath",
    )
    aemeath.state.enemy_tune_break_available = True
    aemeath.state.enemy_mistune_active = True
    assert aemeath.is_action_available(aemeath.actions["aemeath_tune_break"]) is True
    assert aemeath.is_action_available(aemeath.actions["mornye_tune_break"]) is False

    print("character_tune_break_action_smoke_test ok")


if __name__ == "__main__":
    main()
