from stage2c_timing_test_support import HEAVY_ID, ready_heavy_sim
from copy import deepcopy
from pydantic import ValidationError
from simulator.action_timing_contract import ActionTimingContract


def main() -> None:
    sim = ready_heavy_sim()
    contract = sim.action_timing_contracts[HEAVY_ID]
    group = contract.scheduled_packet_groups[0]
    assert group.scheduled_frames == [66] and contract.same_character_input_frame == contract.swap_input_frame == contract.action_end_frame == 86 and contract.source_action_end_frame == 78
    assert group.damage_payload["damage_multiplier_per_packet"] == 2.5846
    assert group.marker_payload["self_hitstop_frames"] == 8
    array_groups = sim.action_timing_contracts["mornye_skill_distributed_array"].scheduled_packet_groups[1:]
    for packet_group in [group, *array_groups]:
        assert packet_group.detachable is True
        assert packet_group.cancel_on_swap is False
        assert packet_group.persist_after_swap is True
    bad = deepcopy(contract.model_dump(mode="json")); bad["scheduled_packet_groups"][0]["scheduled_frames"] = [65]
    try: ActionTimingContract.model_validate(bad)
    except ValidationError: pass
    else: raise AssertionError("Heavy frame mutation accepted")
    print("mornye_stage2c_detachable_contract_v124_smoke_test ok heavy+array_e2_detachable_persistent")


if __name__ == "__main__": main()
