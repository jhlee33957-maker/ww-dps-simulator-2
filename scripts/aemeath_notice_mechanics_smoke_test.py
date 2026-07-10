from __future__ import annotations

import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"
MANIFEST_PATH = DATA_DIR / "source" / "direct_action_data_patch_manifest_v61.json"


def approx(actual: float, expected: float, tolerance: float = 1e-4) -> bool:
    return math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance)


def assert_approx(actual: float, expected: float, label: str) -> None:
    assert approx(actual, expected), f"{label} expected {expected}, got {actual}"


def actions_by_id() -> dict[str, dict]:
    actions = json.loads((DATA_DIR / "actions.json").read_text(encoding="utf-8-sig"))
    return {action["id"]: action for action in actions}


def manifest_patches_by_id() -> dict[str, dict]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {patch["action_id"]: patch for patch in manifest["action_patches"]}


def make_sim() -> Simulation:
    return Simulation.from_json(DATA_DIR, selected_character_ids=["aemeath"])


def state(sim: Simulation) -> dict:
    return sim.state.character_mechanics_state["aemeath"]


def derive(sim: Simulation) -> None:
    sim.character_mechanics["aemeath"].advance_time(sim.state, 0.0)


def execute(sim: Simulation, selected_action_id: str, expected_resolved_id: str) -> None:
    resolved_id = sim.resolve_action_id(selected_action_id)
    assert resolved_id == expected_resolved_id, f"{selected_action_id}: expected {expected_resolved_id}, got {resolved_id}"
    assert sim.execute_action(selected_action_id), f"Failed to execute {selected_action_id} resolved as {resolved_id}"


def multipliers(action: dict) -> list[float]:
    return [hit.get("damage_multiplier", 0.0) for hit in action.get("hits", [])]


def combat_time(action: dict) -> float:
    return action.get("combat_time_cost", action["action_time"])


def prepare_overdrive(sim: Simulation) -> None:
    sim.state.resonance_energy["aemeath"] = 125.0


def set_finale_ready(sim: Simulation) -> None:
    data = state(sim)
    data["heavenfall_unbound"] = True
    data["heavenfall_unbound_remaining"] = 60.0
    data["synchronization_rate"] = 200.0
    data["resonance_rate"] = 4.0
    derive(sim)


def test_special_overdrive_e1_switch(actions: dict[str, dict]) -> None:
    sim = make_sim()
    prepare_overdrive(sim)
    execute(sim, "aemeath_resonance_liberation", "aemeath_liberation_overdrive")
    data = state(sim)

    assert data["form"] == "mech"
    assert data["overdrive_form_switch_window_remaining"] == 1
    assert sim.resolve_action_id("aemeath_resonance_skill") == "aemeath_form_switch_to_aemeath_after_overdrive"

    before_sync = data["synchronization_rate"]
    execute(sim, "aemeath_resonance_skill", "aemeath_form_switch_to_aemeath_after_overdrive")
    entry = sim.timeline[-1]
    data = state(sim)

    special = actions["aemeath_form_switch_to_aemeath_after_overdrive"]
    aemeath_a2 = actions["aemeath_basic_form_stage_2"]
    assert data["form"] == "aemeath"
    assert data["aemeath_combo_stage"] == 3
    assert data["overdrive_form_switch_window_remaining"] == 0
    assert_approx(data["synchronization_rate"], before_sync + 6.44, "post-Overdrive E1 sync")
    assert multipliers(special) == multipliers(aemeath_a2)
    assert_approx(special["action_time"], aemeath_a2["action_time"], "post-Overdrive E1 action_time")
    assert_approx(combat_time(special), combat_time(aemeath_a2), "post-Overdrive E1 combat_time_cost")
    assert_approx(entry.action_time, aemeath_a2["action_time"], "executed post-Overdrive E1 action_time")
    assert "aemeath_form_switch" in sim.state.cooldowns


def test_priority_guard() -> None:
    sim = make_sim()
    prepare_overdrive(sim)
    execute(sim, "aemeath_resonance_liberation", "aemeath_liberation_overdrive")
    data = state(sim)
    data["seraphic_duo_remaining"] = 5.0
    data["synchronization_rate"] = 100.0
    assert sim.resolve_action_id("aemeath_resonance_skill") == "aemeath_seraphic_duet_encore"

    sim = make_sim()
    prepare_overdrive(sim)
    execute(sim, "aemeath_resonance_liberation", "aemeath_liberation_overdrive")
    data = state(sim)
    data["synchronization_rate"] = 200.0
    data["resonance_rate"] = 4.0
    derive(sim)
    assert sim.resolve_action_id("aemeath_resonance_skill") == "aemeath_heavenfall_finale"

    sim = make_sim()
    prepare_overdrive(sim)
    execute(sim, "aemeath_resonance_liberation", "aemeath_liberation_overdrive")
    data = state(sim)
    data["sync_strike_window_type"] = "call_of_dawn"
    data["sync_strike_window_remaining"] = 1
    assert sim.resolve_action_id("aemeath_resonance_skill") == "aemeath_sync_strike_call_of_dawn"


def test_e1_shared_cooldown() -> None:
    sim = make_sim()
    execute(sim, "aemeath_resonance_skill", "aemeath_form_switch_to_mech_normal")
    assert sim.state.cooldowns["aemeath_form_switch"] == 1
    assert sim.resolve_action_id("aemeath_resonance_skill") == "aemeath_form_switch_to_aemeath_normal"
    assert not sim.is_action_available(sim.actions["aemeath_resonance_skill"])

    execute(sim, "short_wait", "short_wait")
    assert not sim.is_action_available(sim.actions["aemeath_resonance_skill"])
    execute(sim, "short_wait", "short_wait")
    assert sim.is_action_available(sim.actions["aemeath_resonance_skill"])

    sim = make_sim()
    sim.state.cooldowns["aemeath_form_switch"] = 1.0
    data = state(sim)
    data["form"] = "mech"
    data["seraphic_duo_remaining"] = 5.0
    data["synchronization_rate"] = 100.0
    assert sim.resolve_action_id("aemeath_resonance_skill") == "aemeath_seraphic_duet_encore"
    assert sim.is_action_available(sim.actions["aemeath_resonance_skill"])

    sim = make_sim()
    sim.state.cooldowns["aemeath_form_switch"] = 1.0
    data = state(sim)
    data["sync_strike_window_type"] = "armament_merge"
    data["sync_strike_window_remaining"] = 1
    assert sim.resolve_action_id("aemeath_resonance_skill") == "aemeath_sync_strike_armament_merge"
    assert sim.is_action_available(sim.actions["aemeath_resonance_skill"])

    sim = make_sim()
    sim.state.cooldowns["aemeath_form_switch"] = 1.0
    set_finale_ready(sim)
    assert sim.resolve_action_id("aemeath_resonance_skill") == "aemeath_heavenfall_finale"
    assert sim.is_action_available(sim.actions["aemeath_resonance_skill"])

    sim = make_sim()
    sim.state.cooldowns["aemeath_form_switch"] = 1.0
    sim.state.resonance_energy["aemeath"] = 125.0
    assert sim.resolve_action_id("aemeath_resonance_liberation") == "aemeath_liberation_overdrive"
    assert sim.is_action_available(sim.actions["aemeath_resonance_liberation"])


def test_sync_delta_source_alignment(actions: dict[str, dict]) -> None:
    expected = {
        "aemeath_basic_form_stage_1": 3.29,
        "aemeath_basic_form_stage_2": 6.44,
        "aemeath_basic_form_stage_3": 16.66,
        "aemeath_basic_form_stage_4": 23.31,
        "aemeath_mech_basic_stage_1": 6.45,
        "aemeath_mech_basic_stage_2": 9.60,
        "aemeath_mech_basic_stage_3": 18.54,
        "aemeath_mech_basic_stage_4": 23.28,
        "aemeath_sync_strike_armament_merge": 18.29,
        "aemeath_sync_strike_call_of_dawn": 22.18,
        "aemeath_form_switch_to_mech_normal": 6.45,
        "aemeath_form_switch_to_aemeath_normal": 3.29,
        "aemeath_form_switch_to_aemeath_after_overdrive": 6.44,
    }
    for action_id, sync_delta in expected.items():
        actual = actions[action_id]["mechanic_effects"]["sync_delta"]
        assert_approx(actual, sync_delta, f"{action_id} sync_delta")

    for action_id in (
        "aemeath_heavy_aemeath_charged_1",
        "aemeath_heavy_aemeath_charged_2",
        "aemeath_heavy_mech_charged_1",
        "aemeath_heavy_mech_charged_2",
    ):
        assert "sync_delta" not in actions[action_id].get("mechanic_effects", {}), f"{action_id} gained sync_delta"


def test_timing_and_coefficient_guardrails(actions: dict[str, dict]) -> None:
    assert_approx(actions["aemeath_liberation_overdrive"]["action_time"], 4.3667, "Overdrive action_time")
    assert_approx(actions["aemeath_liberation_overdrive"]["combat_time_cost"], 0.0, "Overdrive combat_time_cost")
    assert multipliers(actions["aemeath_liberation_overdrive"]) == [10.0402]

    assert_approx(actions["aemeath_heavenfall_finale"]["action_time"], 5.6667, "Finale action_time")
    assert_approx(actions["aemeath_heavenfall_finale"]["combat_time_cost"], 0.0, "Finale combat_time_cost")
    assert multipliers(actions["aemeath_heavenfall_finale"]) == [17.8929]

    assert_approx(actions["aemeath_seraphic_duet_overturn"]["action_time"], 185 / 60, "Seraphic Overturn action_time")
    assert_approx(actions["aemeath_seraphic_duet_overturn"]["combat_time_cost"], 84 / 60, "Seraphic Overturn combat_time_cost")
    assert multipliers(actions["aemeath_seraphic_duet_overturn"]) == [3.5795]
    assert_approx(actions["aemeath_seraphic_duet_encore"]["action_time"], 145 / 60, "Seraphic Encore action_time")
    assert_approx(actions["aemeath_seraphic_duet_encore"]["combat_time_cost"], 80 / 60, "Seraphic Encore combat_time_cost")
    assert multipliers(actions["aemeath_seraphic_duet_encore"]) == [3.579]

    expected_heavy_times = {
        "aemeath_heavy_aemeath_charged_1": (72 / 60, 72 / 60, None),
        "aemeath_heavy_aemeath_charged_2": (145 / 60, 145 / 60, (91 / 60, 91 / 60)),
        "aemeath_heavy_mech_charged_1": (56 / 60, 56 / 60, None),
        "aemeath_heavy_mech_charged_2": (116 / 60, 116 / 60, (56 / 60, 56 / 60)),
    }
    for action_id, (action_time, combat_time_cost, override) in expected_heavy_times.items():
        action = actions[action_id]
        assert_approx(action["action_time"], action_time, f"{action_id} action_time")
        assert_approx(action["combat_time_cost"], combat_time_cost, f"{action_id} combat_time_cost")
        if override is not None:
            instant_response = action["timing_overrides"]["instant_response"]
            assert_approx(instant_response["action_time"], override[0], f"{action_id} IR action_time")
            assert_approx(instant_response["combat_time_cost"], override[1], f"{action_id} IR combat_time_cost")


def test_resource_guardrails(actions: dict[str, dict]) -> None:
    patches = manifest_patches_by_id()
    action_ids = [
        "aemeath_basic_form_stage_1",
        "aemeath_basic_form_stage_2",
        "aemeath_basic_form_stage_3",
        "aemeath_basic_form_stage_4",
        "aemeath_mech_basic_stage_1",
        "aemeath_mech_basic_stage_2",
        "aemeath_mech_basic_stage_3",
        "aemeath_mech_basic_stage_4",
        "aemeath_form_switch_to_mech_normal",
        "aemeath_form_switch_to_aemeath_normal",
        "aemeath_form_switch_to_aemeath_after_overdrive",
        "aemeath_sync_strike_armament_merge",
        "aemeath_sync_strike_call_of_dawn",
        "aemeath_liberation_overdrive",
        "aemeath_heavenfall_finale",
    ]
    for action_id in action_ids:
        action = actions[action_id]
        after = patches[action_id]["after"]
        resonance_cost = 125 if action_id == "aemeath_liberation_overdrive" else 0
        assert action.get("resonance_energy_cost", 0) == resonance_cost, f"{action_id} resonance cost changed"
        assert_approx(action.get("resonance_energy_gain", 0), after["resonance_energy_gain"], f"{action_id} resonance gain")
        assert_approx(action.get("concerto_energy_gain", 0), after["concerto_energy_gain"], f"{action_id} concerto gain")


def main() -> None:
    actions = actions_by_id()
    test_special_overdrive_e1_switch(actions)
    test_priority_guard()
    test_e1_shared_cooldown()
    test_sync_delta_source_alignment(actions)
    test_timing_and_coefficient_guardrails(actions)
    test_resource_guardrails(actions)
    print("Aemeath notice mechanics smoke test passed.")


if __name__ == "__main__":
    main()
