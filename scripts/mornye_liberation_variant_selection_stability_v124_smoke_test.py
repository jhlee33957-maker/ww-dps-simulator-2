from __future__ import annotations

from v124_timing_test_support import (
    MORNYE_LIBERATION_ID,
    make_mornye_liberation_sim,
    set_mornye_observation_state,
)
from simulator.action_timing_contract import prepare_control_point_action, select_action_timing, start_ongoing_action


def assert_stable(start_active: bool, expected_variant: str, expected_hit: int, expected_same: int) -> None:
    sim = make_mornye_liberation_sim(start_active)
    action = sim.actions[MORNYE_LIBERATION_ID]
    contract = sim.action_timing_contracts[MORNYE_LIBERATION_ID]
    selected = select_action_timing(sim.state, action, contract)
    instance = start_ongoing_action(sim.state, action, contract, selected)
    set_mornye_observation_state(sim, not start_active)
    prepared = prepare_control_point_action(action, contract, selected)
    assert instance.selected_timing_variant_id == expected_variant
    assert instance.selected_same_character_input_frame == expected_same
    assert instance.selected_swap_input_frame == 300
    assert instance.selected_lifecycle_end_frame == 300
    assert prepared.hits[0].time * 60 == expected_hit
    sim.advance_timing_runtime(expected_same / 60, combat_elapsed=0)
    assert instance.source_action_ended and not instance.ended
    assert instance.selected_timing_variant_id == expected_variant
    assert instance.selected_same_character_input_frame == expected_same


def main() -> None:
    assert_stable(True, "observation", 277, 296)
    assert_stable(False, "normal", 272, 282)
    print("mornye_liberation_variant_selection_stability_v124_smoke_test ok")


if __name__ == "__main__":
    main()
