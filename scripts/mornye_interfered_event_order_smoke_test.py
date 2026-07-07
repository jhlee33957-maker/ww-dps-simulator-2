from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


DATA_DIR = ROOT / "data"


def tune_ready(sim: Simulation) -> None:
    sim.state.enemy_tune_break_available = True
    sim.state.enemy_mistune_active = True
    sim.state.enemy_tune_break_cooldown_remaining = 0.0
    sim.state.target_tune_shift_state = "tune_rupture_shifting"
    sim.state.target_tune_shift_remaining = 8.0


def response_hits(row) -> list[dict]:
    return [hit for hit in row.hit_details if hit.get("is_tune_response_damage")]


def tune_break_hits(row) -> list[dict]:
    return [hit for hit in row.hit_details if hit.get("is_tune_break_damage")]


def main() -> None:
    sim = Simulation.from_json(DATA_DIR, selected_character_ids="aemeath_mornye_test_party")
    sim.characters["mornye"].energy_regen = 2.7944
    sim.state.character_states["mornye"]["energy_regen"] = 2.7944
    sim.state.character_mechanics_state["mornye"]["mode"] = "wide_field_observation"
    sim.state.character_mechanics_state["mornye"]["relative_momentum"] = 100.0

    assert sim.execute_action("mornye_heavy_attack")
    heavy = sim.timeline[-1]
    assert heavy.resolved_action_id == "mornye_heavy_inversion"
    assert heavy.observation_marker_applied is True
    assert heavy.mornye_interfered_marker_applied is False
    assert sim.state.interfered_marker_remaining == 0.0

    tune_ready(sim)
    assert sim.execute_action("mornye_tune_break")
    tune_break = sim.timeline[-1]
    assert tune_break.mornye_interfered_marker_applied is True
    assert tune_break.interfered_marker_newly_applied_this_action is True
    assert tune_break.interfered_marker_damage_taken_amp == 0.40
    assert tune_break.tune_break_damage_receives_new_interfered_marker_amp is False
    assert tune_break.tune_break_damage_receives_existing_interfered_marker_amp is False
    assert tune_break.tune_break_damage_receives_newly_applied_interfered_marker_amp is False
    assert tune_break.tune_break_damage_before_target_amp == tune_break.tune_break_damage_after_target_amp
    assert all(hit.get("target_damage_taken_amp", 0.0) == 0.0 for hit in tune_break_hits(tune_break))
    assert all(hit.get("tune_break_damage_receives_newly_applied_interfered_marker_amp") is False for hit in tune_break_hits(tune_break))

    responses = response_hits(tune_break)
    assert responses
    assert all(hit["applied_damage_taken_amp"] == 0.40 for hit in responses)
    assert all(hit["response_damage_receives_newly_applied_interfered_marker_amp"] is True for hit in responses)
    assert tune_break.response_damage_receives_newly_applied_interfered_marker_amp is True

    assert sim.execute_action("swap_to_aemeath")
    assert sim.execute_action("aemeath_basic_attack")
    later = sim.timeline[-1]
    direct_hits = [hit for hit in later.hit_details if hit.get("hit_damage_category") == "normal"]
    assert later.normal_damage > 0.0
    assert later.interfered_marker_direct_damage_amp_applied_count == len(direct_hits)
    assert later.interfered_marker_direct_damage_amp_bonus_damage > 0.0
    assert all(hit["target_damage_taken_amp"] == 0.40 for hit in direct_hits)
    assert all(hit["interfered_marker_amp_applied_to_direct_damage"] is True for hit in direct_hits)

    print("mornye_interfered_event_order_smoke_test ok")


if __name__ == "__main__":
    main()
