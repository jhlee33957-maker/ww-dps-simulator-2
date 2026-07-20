from __future__ import annotations

from copy import deepcopy

from pydantic import ValidationError

from v124_timing_test_support import make_sim
from simulator.action_timing_contract import ActionTimingContract, prepare_control_point_action


def main() -> None:
    sim = make_sim("mornye")
    contract = sim.action_timing_contracts["mornye_basic_stage_3"]
    frames = [frame for group in contract.scheduled_packet_groups for frame in group.scheduled_frames]
    assert frames == [24, 31, 40, 49, 58, 67, 76]
    assert contract.same_character_input_frame == contract.swap_input_frame == 50
    assert contract.action_end_frame == 91
    assert [frame for frame in frames if frame > 50] == [58, 67, 76]
    assert all(group.detachable and group.persist_after_swap and not group.cancel_on_swap for group in contract.scheduled_packet_groups)
    assert [group.marker_payload["self_hitstop_frames"] for group in contract.scheduled_packet_groups] == [9, 2]
    assert contract.scheduled_packet_groups[-1].marker_payload == {
        "self_hitstop_frames": 2,
        "repeat_interval_frames": 9,
        "maximum_occurrences": 6,
        "derivation_frame": 39,
    }
    prepared = prepare_control_point_action(sim.actions[contract.action_id], contract)
    assert prepared.action_time * 60 == 50 and prepared.hits == []
    assert prepared.mechanic_effects.get("rest_mass_energy_delta") is None
    omitted = deepcopy(contract.model_dump(mode="json"))
    omitted["scheduled_packet_groups"][-1]["scheduled_frames"] = [31, 40, 49]
    try:
        ActionTimingContract.model_validate(omitted)
    except ValidationError:
        pass
    else:
        raise AssertionError("omitting 58F/67F/76F must violate packet_count")
    print("mornye_basic_stage3_packet_contract_v124_smoke_test ok frames=24,31,40,49,58,67,76 control=50 end=91")


if __name__ == "__main__":
    main()
