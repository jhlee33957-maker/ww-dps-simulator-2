from stage2c_timing_test_support import ARRAY_ID, ready_heavy_sim
from copy import deepcopy
from pydantic import ValidationError
from simulator.action_timing_contract import ActionTimingContract


def main() -> None:
    contract = ready_heavy_sim().action_timing_contracts[ARRAY_ID]
    assert contract.same_character_input_frame == contract.swap_input_frame == contract.action_end_frame == 60
    assert [g.packet_group_id for g in contract.scheduled_packet_groups] == ["mornye_distributed_array_e2_1", "mornye_distributed_array_e2_2", "mornye_distributed_array_e2_3", "mornye_distributed_array_e2_4"]
    assert [g.scheduled_frames for g in contract.scheduled_packet_groups] == [[22], [22], [36], [36]]
    bad = deepcopy(contract.model_dump(mode="json")); bad["scheduled_packet_groups"].pop()
    try: ActionTimingContract.model_validate(bad)
    except ValidationError: pass
    else: raise AssertionError("omitted E2 packet accepted")
    print("mornye_distributed_array_packet_contract_v124_smoke_test ok heal=1 E2=22,22,36,36 end=60")


if __name__ == "__main__": main()
