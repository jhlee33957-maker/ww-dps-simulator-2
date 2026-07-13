from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation
from simulator.transition_actions import transition_action_to_action_data


DATA_DIR = ROOT / "data"
TIMING_MODE = "same_action_field_creation_approximation"
ELIGIBLE_ACTIONS = {"mornye_heavy_geopotential_shift", "mornye_liberation_critical_protocol"}


def make_sim(mode: str) -> Simulation:
    sim = Simulation.from_json(
        DATA_DIR,
        party="aemeath_mornye_test_party",
        build_profile_overrides={"mornye": "mornye_user_real_01"},
        transition_config={"mechanics": {"mornye": {"mornye_heal_event_mode": mode}}},
    )
    sim.state.character_states["mornye"]["rest_mass_energy"] = 100.0
    return sim


def test_metadata_is_targeted() -> None:
    actions = {item["id"]: item for item in json.loads((DATA_DIR / "actions.json").read_text(encoding="utf-8-sig"))}
    for action_id in ELIGIBLE_ACTIONS:
        assert "team_heal" not in actions[action_id].get("mechanic_event_tags", [])
        effects = actions[action_id]["mechanic_effects"]
        assert effects["healing_implementation_status"] == "scheduled_180f_exact"
        assert "scheduled_180f_exact" in effects["heal_event_mode_support"]
        assert effects["scheduled_healing_first_tick_frames"] == 1
        assert effects["scheduled_healing_interval_frames"] == 180
        assert effects["scheduled_healing_max_trigger_count"] == 9
    arbitrary = [
        action
        for action in actions.values()
        if action.get("character_id") == "mornye"
        and action["id"] not in ELIGIBLE_ACTIONS
        and "syntony_field" not in action["id"]
    ]
    assert all("team_heal" not in action.get("mechanic_event_tags", []) for action in arbitrary)

    transition_records = json.loads((DATA_DIR / "transition_actions.json").read_text(encoding="utf-8-sig"))
    intro = next(item for item in transition_records if item["id"] == "mornye_intro_convergence")
    transition_action = transition_action_to_action_data(intro)
    assert "team_heal" not in transition_action.mechanic_event_tags
    assert transition_action.policy_selectable is False
    effects = transition_action.mechanic_effects
    assert effects["set_syntony_field_remaining"] == 25.0
    assert effects["healing_implementation_status"] == "scheduled_180f_exact"
    assert effects["scheduled_healing_first_tick_frames"] == 1
    assert effects["scheduled_healing_interval_frames"] == 180
    assert "field_creation_only" in effects["heal_event_mode_support"]
    assert "simplified_syntony_field_uptime" in effects["heal_event_mode_support"]


def test_heal_event_modes() -> None:
    disabled = make_sim("disabled")
    assert disabled.execute_action("mornye_heavy_attack")
    assert disabled.state.mechanic_event_emitted_counts.get("team_heal", 0) == 0

    creation = make_sim("field_creation_only")
    assert creation.execute_action("mornye_heavy_attack")
    assert creation.state.mechanic_event_emitted_counts.get("team_heal", 0) == 1
    creation_row = creation.timeline[-1]
    assert creation_row.team_heal_event_triggered is True
    assert creation_row.halo_of_starry_radiance_5set_same_action_application is True
    assert creation_row.halo_of_starry_radiance_5set_application_timing == TIMING_MODE

    simplified = make_sim("simplified_syntony_field_uptime")
    assert simplified.execute_action("mornye_heavy_attack")
    first_count = simplified.state.mechanic_event_emitted_counts.get("team_heal", 0)
    assert first_count == 1
    simplified_row = simplified.timeline[-1]
    assert simplified_row.team_heal_event_triggered is True
    assert simplified_row.halo_of_starry_radiance_5set_same_action_application is True
    assert simplified_row.halo_of_starry_radiance_5set_application_timing == TIMING_MODE
    assert simplified.execute_action("short_wait")
    assert simplified.state.mechanic_event_emitted_counts.get("team_heal", 0) > first_count
    assert all(float(event.get("damage_added", 0.0)) == 0.0 for event in simplified.state.mechanic_event_log)


def main() -> None:
    test_metadata_is_targeted()
    test_heal_event_modes()
    print("mornye_heal_event_trigger_smoke_test ok")


if __name__ == "__main__":
    main()
