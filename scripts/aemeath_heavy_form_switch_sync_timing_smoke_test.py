from __future__ import annotations

import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.action_executor import resolve_action_timing
from simulator.models import ActionData
from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"


def approx(actual: float, expected: float, tolerance: float = 1e-4) -> bool:
    return math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance)


def actions_by_id() -> dict[str, dict]:
    actions = json.loads((DATA_DIR / "actions.json").read_text(encoding="utf-8-sig"))
    return {action["id"]: action for action in actions}


def action_model(action: dict) -> ActionData:
    return ActionData.model_validate(action)


def combat_time(action: dict) -> float:
    return action.get("combat_time_cost", action["action_time"])


def multipliers(action: dict) -> list[float]:
    return [hit.get("damage_multiplier", 0.0) for hit in action.get("hits", [])]


def assert_approx(actual: float, expected: float, label: str) -> None:
    assert approx(actual, expected), f"{label} expected {expected}, got {actual}"


def assert_time(action: dict, action_time: float, combat_time_cost: float) -> None:
    assert_approx(action["action_time"], action_time, f"{action['id']} action_time")
    assert_approx(combat_time(action), combat_time_cost, f"{action['id']} combat_time_cost")


def assert_multipliers(action: dict, expected: list[float]) -> None:
    actual = multipliers(action)
    assert actual == expected, f"{action['id']} multipliers expected {expected}, got {actual}"


def assert_resources(action: dict, *, cost: float, resonance_gain: float, concerto_gain: float) -> None:
    assert action.get("resonance_energy_cost", 0.0) == cost, f"{action['id']} resonance cost changed"
    assert action.get("resonance_energy_gain", 0.0) == resonance_gain, f"{action['id']} resonance gain changed"
    assert action.get("concerto_energy_gain", 0.0) == concerto_gain, f"{action['id']} concerto gain changed"


def assert_effect_keys(action: dict, expected_keys: set[str]) -> None:
    actual_keys = set(action.get("mechanic_effects", {}))
    missing = expected_keys - actual_keys
    assert not missing, f"{action['id']} mechanic_effects missing keys: {sorted(missing)}"


def test_sync_strike_timings(actions: dict[str, dict]) -> None:
    assert_time(actions["aemeath_sync_strike_armament_merge"], 1.1667, 1.1667)
    assert_time(actions["aemeath_sync_strike_call_of_dawn"], 0.9667, 0.9667)


def test_heavy_timings_and_overrides(actions: dict[str, dict]) -> None:
    expected = {
        "aemeath_heavy_aemeath_charged_1": (1.8333, 1.8333),
        "aemeath_heavy_aemeath_charged_2": (3.6667, 3.6667),
        "aemeath_heavy_mech_charged_1": (1.0333, 1.0333),
        "aemeath_heavy_mech_charged_2": (2.0667, 2.0667),
    }
    for action_id, (action_time, combat_time_cost) in expected.items():
        assert_time(actions[action_id], action_time, combat_time_cost)

    human_override = actions["aemeath_heavy_aemeath_charged_2"]["timing_overrides"]["instant_response"]
    assert_approx(human_override["action_time"], 1.8333, "human Instant Response action_time")
    assert_approx(human_override["combat_time_cost"], 1.8333, "human Instant Response combat_time_cost")

    mech_override = actions["aemeath_heavy_mech_charged_2"]["timing_overrides"]["instant_response"]
    assert_approx(mech_override["action_time"], 1.0333, "mech Instant Response action_time")
    assert_approx(mech_override["combat_time_cost"], 1.0333, "mech Instant Response combat_time_cost")


def test_resolver_instant_response(actions: dict[str, dict]) -> None:
    human = action_model(actions["aemeath_heavy_aemeath_charged_2"])
    assert resolve_action_timing(human, {"instant_response": False}) == (3.6667, 3.6667)
    assert resolve_action_timing(human, {"instant_response": True}) == (1.8333, 1.8333)

    mech = action_model(actions["aemeath_heavy_mech_charged_2"])
    assert resolve_action_timing(mech, {"instant_response": False}) == (2.0667, 2.0667)
    assert resolve_action_timing(mech, {"instant_response": True}) == (1.0333, 1.0333)


def set_unbound_instant_response(sim: Simulation, *, form: str) -> None:
    data = sim.state.character_mechanics_state["aemeath"]
    data["form"] = form
    data["heavenfall_unbound"] = True
    data["heavenfall_unbound_remaining"] = 60.0
    data["synchronization_rate"] = 20.0
    data["resonance_rate"] = 4.0
    data["instant_response"] = True
    data["instant_response_consumed"] = False


def test_execution_uses_override_before_clear() -> None:
    sim = Simulation.from_json(DATA_DIR, selected_character_ids=["aemeath"])
    set_unbound_instant_response(sim, form="aemeath")
    assert sim.execute_action("aemeath_heavy_attack")
    entry = sim.timeline[-1]
    data = sim.state.character_mechanics_state["aemeath"]

    assert entry.resolved_action_id == "aemeath_heavy_aemeath_charged_2"
    assert_approx(entry.action_time, 1.8333, "executed human Instant Response action_time")
    assert_approx(entry.combat_time_cost, 1.8333, "executed human Instant Response combat_time_cost")
    assert data["instant_response"] is False
    assert data["instant_response_consumed"] is True

    sim = Simulation.from_json(DATA_DIR, selected_character_ids=["aemeath"])
    set_unbound_instant_response(sim, form="mech")
    assert sim.execute_action("aemeath_heavy_attack")
    entry = sim.timeline[-1]
    data = sim.state.character_mechanics_state["aemeath"]

    assert entry.resolved_action_id == "aemeath_heavy_mech_charged_2"
    assert_approx(entry.action_time, 1.0333, "executed mech Instant Response action_time")
    assert_approx(entry.combat_time_cost, 1.0333, "executed mech Instant Response combat_time_cost")
    assert data["instant_response"] is False
    assert data["instant_response_consumed"] is True


def test_form_switch_stage_1_behavior(actions: dict[str, dict]) -> None:
    to_mech = actions["aemeath_form_switch_to_mech_normal"]
    mech_a1 = actions["aemeath_mech_basic_stage_1"]
    assert_time(to_mech, mech_a1["action_time"], combat_time(mech_a1))
    assert_multipliers(to_mech, multipliers(mech_a1))
    assert to_mech["mechanic_effects"]["set_form"] == "mech"
    assert to_mech["mechanic_effects"]["set_mech_combo_stage"] == 2

    to_aemeath = actions["aemeath_form_switch_to_aemeath_normal"]
    human_a1 = actions["aemeath_basic_form_stage_1"]
    assert_time(to_aemeath, human_a1["action_time"], combat_time(human_a1))
    assert_multipliers(to_aemeath, multipliers(human_a1))
    assert to_aemeath["mechanic_effects"]["set_form"] == "aemeath"
    assert to_aemeath["mechanic_effects"]["set_aemeath_combo_stage"] == 2


def test_time_stop_and_coefficient_guardrails(actions: dict[str, dict]) -> None:
    assert_time(actions["aemeath_liberation_overdrive"], 4.3667, 0.0)
    assert_multipliers(actions["aemeath_liberation_overdrive"], [2.008, 2.6774, 2.6774, 2.6774])

    assert_time(actions["aemeath_heavenfall_finale"], 5.6667, 0.0)
    assert_multipliers(actions["aemeath_heavenfall_finale"], [17.8929])

    seraphic_id = (
        "aemeath_seraphic_duet_overture"
        if "aemeath_seraphic_duet_overture" in actions
        else "aemeath_seraphic_duet_overturn"
    )
    assert_time(actions[seraphic_id], 3.0, 1.3167)
    assert_time(actions["aemeath_seraphic_duet_encore"], 2.4167, 1.3333)
    assert_multipliers(
        actions["aemeath_seraphic_duet_encore"],
        [0.179, 0.179, 0.3579, 0.3579, 0.179, 0.179, 1.7893, 0.3579],
    )


def test_resource_and_mechanic_key_guardrails(actions: dict[str, dict]) -> None:
    expected_resources = {
        "aemeath_form_switch_to_mech_normal": (0, 6, 4),
        "aemeath_form_switch_to_aemeath_normal": (0, 5, 4),
        "aemeath_sync_strike_armament_merge": (0, 10, 8),
        "aemeath_sync_strike_call_of_dawn": (0, 10, 8),
        "aemeath_heavy_aemeath_charged_1": (0, 5, 4),
        "aemeath_heavy_aemeath_charged_2": (0, 5, 5),
        "aemeath_heavy_mech_charged_1": (0, 6, 4),
        "aemeath_heavy_mech_charged_2": (0, 6, 5),
        "aemeath_liberation_overdrive": (125, 0, 20),
        "aemeath_heavenfall_finale": (0, 0, 20),
        "aemeath_seraphic_duet_overturn": (0, 8, 8),
        "aemeath_seraphic_duet_encore": (0, 8, 10),
    }
    for action_id, (cost, resonance_gain, concerto_gain) in expected_resources.items():
        assert_resources(actions[action_id], cost=cost, resonance_gain=resonance_gain, concerto_gain=concerto_gain)

    expected_effect_keys = {
        "aemeath_form_switch_to_mech_normal": {"set_form", "sync_delta", "set_mech_combo_stage"},
        "aemeath_form_switch_to_aemeath_normal": {"set_form", "sync_delta", "set_aemeath_combo_stage"},
        "aemeath_sync_strike_armament_merge": {"set_form", "sync_delta", "set_mech_combo_stage"},
        "aemeath_sync_strike_call_of_dawn": {"set_form", "sync_delta", "set_aemeath_combo_stage"},
        "aemeath_heavy_aemeath_charged_1": {"set_aemeath_combo_stage", "set_sync_strike_window"},
        "aemeath_heavy_aemeath_charged_2": {
            "set_aemeath_combo_stage",
            "instant_response_sync_delta",
            "instant_response",
            "instant_response_consumed",
            "set_sync_strike_window",
        },
        "aemeath_heavy_mech_charged_1": {"set_mech_combo_stage", "set_sync_strike_window"},
        "aemeath_heavy_mech_charged_2": {
            "set_mech_combo_stage",
            "instant_response_sync_delta",
            "instant_response",
            "instant_response_consumed",
            "set_sync_strike_window",
        },
        "aemeath_liberation_overdrive": {
            "sync_delta",
            "resonance_rate_delta",
            "set_form",
            "set_mech_combo_stage",
            "stardust_resonance_duration",
            "heavenfall_unbound_duration",
            "instant_response_consumed",
        },
        "aemeath_heavenfall_finale": {
            "set_form",
            "set_synchronization_rate",
            "set_resonance_rate",
            "seraphic_duo_duration",
            "heavenfall_unbound_duration",
            "stardust_resonance_duration",
            "instant_response",
            "instant_response_consumed",
            "finale_available",
            "set_aemeath_combo_stage",
            "set_mech_combo_stage",
        },
        "aemeath_seraphic_duet_overturn": {
            "set_mech_combo_stage",
            "resonance_rate_delta",
            "sync_delta",
            "set_form",
            "seraphic_duo_duration",
        },
        "aemeath_seraphic_duet_encore": {
            "set_aemeath_combo_stage",
            "resonance_rate_delta",
            "sync_delta",
            "set_form",
            "seraphic_duo_duration",
        },
    }
    for action_id, keys in expected_effect_keys.items():
        assert_effect_keys(actions[action_id], keys)


def main() -> None:
    actions = actions_by_id()
    test_sync_strike_timings(actions)
    test_heavy_timings_and_overrides(actions)
    test_resolver_instant_response(actions)
    test_execution_uses_override_before_clear()
    test_form_switch_stage_1_behavior(actions)
    test_time_stop_and_coefficient_guardrails(actions)
    test_resource_and_mechanic_key_guardrails(actions)
    print("Aemeath Heavy/Form Switch/Sync Strike timing smoke test passed.")


if __name__ == "__main__":
    main()
