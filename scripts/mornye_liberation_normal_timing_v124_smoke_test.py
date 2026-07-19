from __future__ import annotations

from v124_timing_test_support import MORNYE_LIBERATION_ID, make_mornye_liberation_sim
from simulator.action_executor import is_action_valid
from simulator.action_timing_contract import start_ongoing_action


def main() -> None:
    sim = make_mornye_liberation_sim(False)
    assert sim.execute_action(MORNYE_LIBERATION_ID)
    result = sim.last_action_result
    instance = sim.state.ongoing_action_instances[-1]
    assert instance.selected_timing_variant_id == "normal"
    assert instance.selected_timing_variant_source == "character_mechanics_state.mornye.observation_marker_active"
    assert result.hit_details[0]["hit_time"] * 60 == 272
    assert result.action_time * 60 == 282
    assert instance.selected_source_action_end_frame == 282
    assert instance.selected_lifecycle_end_frame == 300
    assert instance.source_action_ended and not instance.ended

    boundary = make_mornye_liberation_sim(False)
    boundary_instance = start_ongoing_action(
        boundary.state,
        boundary.actions[MORNYE_LIBERATION_ID],
        boundary.action_timing_contracts[MORNYE_LIBERATION_ID],
    )
    followup = boundary.actions["mornye_basic_stage_1"]
    swap = boundary.actions["swap_to_lynae"]
    boundary.advance_timing_runtime(281 / 60, combat_elapsed=0)
    assert not is_action_valid(followup, boundary.state)[0]
    assert not is_action_valid(swap, boundary.state)[0]
    boundary.advance_timing_runtime(1 / 60, combat_elapsed=0)
    assert is_action_valid(followup, boundary.state)[0]
    assert not is_action_valid(swap, boundary.state)[0]
    assert boundary_instance.source_action_ended and not boundary_instance.ended
    boundary.advance_timing_runtime(17 / 60, combat_elapsed=0)
    assert not is_action_valid(swap, boundary.state)[0]
    boundary.advance_timing_runtime(1 / 60, combat_elapsed=0)
    assert is_action_valid(swap, boundary.state)[0]
    assert boundary_instance.ended
    print("mornye_liberation_normal_timing_v124_smoke_test ok hit=272 same=282 swap=300")


if __name__ == "__main__":
    main()
