from __future__ import annotations

import math
import sys
from pathlib import Path

from pydantic import ValidationError


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.models import ActionData
from simulator.simulation import Simulation


BASE_AUX_ACTION = {
    "id": "aux_zero",
    "name": "Aux Zero",
    "character_id": "aemeath",
    "action_type": "echo_skill",
    "duration": 0.0,
    "action_time": 0.0,
    "combat_time_cost": 0.0,
    "cooldown": 1.0,
    "resonance_energy_cost": 0.0,
    "mechanic_effects": {"auxiliary_zero_time_action": True},
}


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-9) -> None:
    assert math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def main() -> None:
    ActionData.model_validate(BASE_AUX_ACTION)
    for field in ("duration", "action_time", "combat_time_cost"):
        malformed = dict(BASE_AUX_ACTION)
        malformed[field] = 0.001
        try:
            ActionData.model_validate(malformed)
        except ValidationError:
            pass
        else:
            raise AssertionError(f"auxiliary action with positive {field} was accepted")
    try:
        ActionData.model_validate(
            {
                "id": "bad_zero",
                "name": "Bad Zero",
                "character_id": "aemeath",
                "action_type": "echo_skill",
                "duration": 0.0,
                "action_time": 0.0,
                "combat_time_cost": 0.0,
                "cooldown": 1.0,
                "resonance_energy_cost": 0.0,
            }
        )
    except ValidationError:
        pass
    else:
        raise AssertionError("non-auxiliary zero-time action was accepted")

    sim = Simulation.from_json("data", selected_character_ids="aemeath_mornye_lynae_enabled_test_party", initial_active_character="aemeath")
    before = {
        "current_time": sim.state.current_time,
        "combat_time": sim.state.combat_time,
        "cooldowns": dict(sim.state.cooldowns),
        "active_buffs": list(sim.state.active_buffs),
        "weapon_effect_cooldowns": dict(sim.state.weapon_effect_cooldowns),
    }
    assert sim.execute_action("aemeath_echo_sigillum")
    assert_close(sim.state.current_time, before["current_time"], "current time")
    assert_close(sim.state.combat_time, before["combat_time"], "combat time")
    assert sim.timeline[-1].scheduled_damage_events == []
    assert sim.state.weapon_effect_cooldowns == before["weapon_effect_cooldowns"]
    assert sim.state.cooldowns != before["cooldowns"]
    assert sim.state.cooldowns["aemeath_echo_sigillum"] == 20.0
    print("zero_time_auxiliary_action_guard_smoke_test ok")


if __name__ == "__main__":
    main()
