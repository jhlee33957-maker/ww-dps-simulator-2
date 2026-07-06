from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def ready(sim: Simulation) -> None:
    sim.state.enemy_tune_break_available = True
    sim.state.enemy_mistune_active = True
    sim.state.enemy_tune_break_cooldown_remaining = 0.0
    sim.state.target_tune_shift_state = "tune_rupture_shifting"
    sim.state.target_tune_shift_remaining = 8.0


def mark_observed(sim: Simulation) -> None:
    sim.characters["mornye"].energy_regen = 2.7944
    sim.state.character_states["mornye"]["energy_regen"] = 2.7944
    sim.state.character_mechanics_state["mornye"]["mode"] = "wide_field_observation"
    sim.state.character_mechanics_state["mornye"]["relative_momentum"] = 100.0
    assert sim.execute_action("mornye_heavy_attack")
    assert sim.timeline[-1].observation_marker_applied is True


def response_hits(row) -> list[dict]:
    return [hit for hit in row.hit_details if hit.get("is_tune_response_damage")]


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", selected_character_ids="aemeath_mornye_test_party")
    mark_observed(sim)
    ready(sim)
    assert sim.execute_action("mornye_tune_break")
    row = sim.timeline[-1]
    tune_break_hits = [hit for hit in row.hit_details if hit.get("is_tune_break_damage")]
    assert tune_break_hits
    assert response_hits(row)
    assert all(hit.get("applied_damage_taken_amp", 0.0) == 0.0 for hit in tune_break_hits)
    assert all(hit["applied_damage_taken_amp"] == 0.4 for hit in response_hits(row))
    assert all(hit["response_damage_receives_interfered_marker_amp"] is True for hit in response_hits(row))
    assert all(hit["response_damage_receives_newly_applied_interfered_marker_amp"] is True for hit in response_hits(row))
    assert all(hit["response_damage_receives_existing_interfered_marker_amp"] is False for hit in response_hits(row))
    assert row.interfered_marker_newly_applied_this_action is True
    assert row.tune_break_damage_receives_new_interfered_marker_amp is False
    assert row.response_damage_receives_interfered_marker_amp is True
    assert row.response_damage_receives_newly_applied_interfered_marker_amp is True
    assert row.response_damage_receives_existing_interfered_marker_amp is False
    assert row.response_damage_receives_new_interfered_marker_amp is True
    assert row.tune_response_event_order_source_status == "excel_event_order_derived"

    existing = Simulation.from_json(ROOT / "data", selected_character_ids="aemeath_mornye_test_party")
    existing.state.interfered_marker_remaining = 8.0
    existing.state.interfered_marker_damage_taken_amp = 0.4
    ready(existing)
    assert existing.execute_action("mornye_tune_break")
    existing_row = existing.timeline[-1]
    assert existing_row.mornye_interfered_marker_applied is False
    assert existing_row.previous_interfered_marker_active_before_response is True
    assert all(hit["applied_damage_taken_amp"] == 0.4 for hit in response_hits(existing_row))
    assert existing_row.response_damage_receives_interfered_marker_amp is True
    assert existing_row.response_damage_receives_newly_applied_interfered_marker_amp is False
    assert existing_row.response_damage_receives_existing_interfered_marker_amp is True
    assert existing_row.response_damage_receives_new_interfered_marker_amp is False

    no_marker = Simulation.from_json(ROOT / "data", selected_character_ids="aemeath_mornye_test_party")
    ready(no_marker)
    assert no_marker.execute_action("mornye_tune_break")
    no_marker_row = no_marker.timeline[-1]
    assert no_marker_row.mornye_interfered_marker_applied is False
    assert no_marker_row.tune_response_damage > 0.0
    assert all(hit["applied_damage_taken_amp"] == 0.0 for hit in no_marker_row.tune_response_hit_details)
    assert no_marker_row.response_damage_receives_interfered_marker_amp is False
    assert no_marker_row.response_damage_receives_newly_applied_interfered_marker_amp is False
    assert no_marker_row.response_damage_receives_existing_interfered_marker_amp is False
    assert no_marker_row.response_damage_receives_new_interfered_marker_amp is False

    c5 = Simulation.from_json(
        ROOT / "data",
        selected_character_ids="aemeath_mornye_test_party",
        transition_config={
            "mechanics": {
                "tune_break_system": {"mode": "enabled"},
                "mornye": {"mornye_constellation": 5},
            }
        },
    )
    ready(c5)
    assert c5.execute_action("mornye_tune_break")
    assert c5.timeline[-1].mornye_particle_jet_multiplier_used == 7.7536
    assert c5.timeline[-1].mornye_particle_jet_constellation_variant == "c5"

    print("tune_response_event_order_smoke_test ok")


if __name__ == "__main__":
    main()
