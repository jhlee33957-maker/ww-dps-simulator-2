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
    bad = deepcopy(contract.model_dump(mode="json")); bad["scheduled_packet_groups"][0]["scheduled_frames"] = [65]
    try: ActionTimingContract.model_validate(bad)
    except ValidationError: pass
    else: raise AssertionError("Heavy frame mutation accepted")
    print("mornye_heavy_inversion_packet_contract_v124_smoke_test ok packet=66 end=78 control=86 lifecycle=86")


if __name__ == "__main__": main()
