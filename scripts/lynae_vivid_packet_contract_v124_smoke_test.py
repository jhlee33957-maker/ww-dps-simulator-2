from copy import deepcopy

from pydantic import ValidationError

from v124_timing_test_support import make_sim
from simulator.action_timing_contract import ActionTimingContract


def main() -> None:
    contract = make_sim("lynae").action_timing_contracts["lynae_to_a_vivid_tomorrow"]
    assert (contract.same_character_input_frame, contract.swap_input_frame, contract.source_action_end_frame, contract.action_end_frame) == (153, 1, 181, 181)
    assert contract.source_type == "user_measured" and contract.confidence == "high"
    assert [group.scheduled_frames for group in contract.scheduled_packet_groups] == [[52, 57, 62, 67, 72, 77, 82, 87, 92, 97, 102, 107], [92, 98, 104, 110, 116, 122, 128, 134, 140, 146]]
    assert sum(group.packet_count or 0 for group in contract.scheduled_packet_groups) == 22
    first, second = contract.scheduled_packet_groups
    assert first.persist_after_swap is False
    assert first.persist_on_vivid_pre_179_swap_branch is True
    assert second.persist_after_swap is True
    for field, value in (("swap_input_frame", 2), ("same_character_input_frame", 152), ("source_action_end_frame", 180), ("action_end_frame", 180)):
        bad = deepcopy(contract.model_dump(mode="json")); bad[field] = value
        try: ActionTimingContract.model_validate(bad)
        except ValidationError: pass
        else: raise AssertionError(f"Vivid {field} mutation accepted")
    bad = deepcopy(contract.model_dump(mode="json")); bad["scheduled_packet_groups"][0]["persist_after_swap"] = True
    try: ActionTimingContract.model_validate(bad)
    except ValidationError: pass
    else: raise AssertionError("generic row-2697 persistence mutation accepted")
    print("lynae_vivid_packet_contract_v124_smoke_test ok swap=1 same=153 end=181 packets=22")


if __name__ == "__main__": main()
