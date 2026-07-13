from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_state import clone_simulation_for_search, diversity_key, diversity_quantization_contract  # noqa: E402
from simulator.simulation import Simulation  # noqa: E402


WINDOW_FIELDS = {
    "aemeath": {
        "sync_strike_window_remaining": 1.0,
        "overdrive_form_switch_window_remaining": 1.0,
        "forte_enhancement_remaining": 1.0,
        "trail_no_cost_remaining": 1.0,
    },
    "mornye": {
        "syntony_field_remaining": 1.0,
        "high_syntony_field_remaining": 1.0,
        "observation_marker_remaining": 1.0,
    },
    "lynae": {
        "spray_paint_window_remaining": 1.0,
        "visual_impact_cooldown_remaining": 1.0,
        "to_vivid_tomorrow_window_remaining": 1.0,
        "target_tune_shift_remaining": 1.0,
    },
}


def main() -> None:
    contract = diversity_quantization_contract()
    encoders = contract["declared_mechanic_field_encoders"]
    base = _sim()
    base_key = diversity_key(base)
    for character_id, fields in WINDOW_FIELDS.items():
        for field_name, positive_value in fields.items():
            changed = clone_simulation_for_search(base)
            changed.state.character_mechanics_state[character_id][field_name] = positive_value
            assert diversity_key(changed) != base_key, f"{character_id}.{field_name}"
            assert field_name in encoders[character_id], f"missing encoder for {character_id}.{field_name}"
    _assert_same_band("aemeath", "sync_strike_window_remaining", 0.25, 0.49)
    _assert_different_band("aemeath", "sync_strike_window_remaining", 0.49, 0.51)
    _assert_same_band("mornye", "syntony_field_remaining", 1.0, 4.9)
    _assert_different_band("mornye", "syntony_field_remaining", 4.9, 5.1)
    _assert_same_band("lynae", "visual_impact_cooldown_remaining", 0.2, 0.9)
    _assert_different_band("lynae", "visual_impact_cooldown_remaining", 0.0, 0.2)
    forbidden = diversity_key(base).lower()
    for token in ("manual", "route", "ppo", "bc_model", "probability"):
        assert token not in forbidden
    print("beam_search_short_window_diversity_smoke_test ok")


def _assert_same_band(character_id: str, field_name: str, left_value: float, right_value: float) -> None:
    left = _sim()
    right = _sim()
    left.state.character_mechanics_state[character_id][field_name] = left_value
    right.state.character_mechanics_state[character_id][field_name] = right_value
    assert diversity_key(left) == diversity_key(right), (character_id, field_name, left_value, right_value)


def _assert_different_band(character_id: str, field_name: str, left_value: float, right_value: float) -> None:
    left = _sim()
    right = _sim()
    left.state.character_mechanics_state[character_id][field_name] = left_value
    right.state.character_mechanics_state[character_id][field_name] = right_value
    assert diversity_key(left) != diversity_key(right), (character_id, field_name, left_value, right_value)


def _sim() -> Simulation:
    return Simulation.from_json(
        ROOT / "data",
        selected_character_ids="aemeath_mornye_lynae_enabled_test_party",
        initial_active_character="aemeath",
    )


if __name__ == "__main__":
    main()
