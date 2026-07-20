from __future__ import annotations

from copy import deepcopy

from pydantic import ValidationError

from v124_timing_test_support import make_sim
from simulator.action_timing_contract import ActionTimingContract, prepare_control_point_action


def main() -> None:
    sim = make_sim("mornye")
    contract = sim.action_timing_contracts["mornye_basic_stage_2"]
    frames = [frame for group in contract.scheduled_packet_groups for frame in group.scheduled_frames]
    assert frames == [11, 26, 30, 39, 48, 57]
    assert contract.same_character_input_frame == contract.swap_input_frame == 49
    assert contract.action_end_frame == 68
    assert [frame for frame in frames if frame > 49] == [57]
    assert all(group.detachable and group.persist_after_swap and not group.cancel_on_swap for group in contract.scheduled_packet_groups)
    assert all(group.source_frame_row_ref and group.source_coefficient_resource_row_ref for group in contract.scheduled_packet_groups)
    assert [group.marker_payload["self_hitstop_frames"] for group in contract.scheduled_packet_groups] == [0, 4, 0]
    assert contract.scheduled_packet_groups[-1].marker_payload == {
        "self_hitstop_frames": 0,
        "repeat_interval_frames": 9,
        "maximum_occurrences": 4,
        "derivation_frame": 45,
    }
    assert contract.scheduled_packet_groups[-1].payload_partition_rules["off_tune"] == (
        "source_row_total_final_occurrence"
    )
    assert contract.scheduled_packet_groups[-1].resource_payload["off_tune_application"] == (
        "source_row_total_final_occurrence"
    )
    prepared = prepare_control_point_action(sim.actions[contract.action_id], contract)
    assert prepared.action_time * 60 == 49 and prepared.hits == []
    assert prepared.damage_multiplier == prepared.off_tune_value == 0.0
    assert prepared.resonance_energy_gain == prepared.concerto_energy_gain == 0.0

    omitted = contract.model_dump(mode="json")
    omitted["scheduled_packet_groups"][-1]["scheduled_frames"].remove(57)
    try:
        ActionTimingContract.model_validate(omitted)
    except ValidationError:
        pass
    else:
        raise AssertionError("omitting the 57F packet must violate packet_count")
    equal_split = deepcopy(contract.model_dump(mode="json"))
    equal_split["scheduled_packet_groups"][-1]["payload_partition_rules"]["damage"] = "equal_split"
    try:
        ActionTimingContract.model_validate(equal_split)
    except ValidationError:
        pass
    else:
        raise AssertionError("equal splitting without a source contract must be rejected")
    print("mornye_basic_stage2_packet_contract_v124_smoke_test ok frames=11,26,30,39,48,57 control=49 end=68")


if __name__ == "__main__":
    main()
