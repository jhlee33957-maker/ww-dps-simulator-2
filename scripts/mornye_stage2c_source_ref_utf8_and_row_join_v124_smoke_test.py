from __future__ import annotations

from copy import deepcopy

from pydantic import ValidationError

from stage2c_timing_test_support import ARRAY_ID, HEAVY_ID, ready_heavy_sim
from simulator.action_timing_contract import ActionTimingContract, TIMING_CONTRACT_SCHEMA_VERSION


def main() -> None:
    contracts = ready_heavy_sim().action_timing_contracts
    assert TIMING_CONTRACT_SCHEMA_VERSION == "action_timing_contract_v124"
    heavy = contracts[HEAVY_ID].scheduled_packet_groups[0]
    array = contracts[ARRAY_ID].scheduled_packet_groups
    assert (heavy.source_frame_row_ref, heavy.source_coefficient_resource_row_ref) == (
        "角色-女!A4136:AT4136", "角色技能类型!A2664:AH2664"
    )
    assert [(group.source_frame_row_ref, group.source_coefficient_resource_row_ref) for group in array] == [
        ("角色-女!A4143:AT4143", None),
        ("角色-女!A4144:AT4144", "角色技能类型!A2666:AH2666"),
        ("角色-女!A4145:AT4145", "角色技能类型!A2667:AH2667"),
        ("角色-女!A4146:AT4146", "角色技能类型!A2668:AH2668"),
        ("角色-女!A4147:AT4147", "角色技能类型!A2669:AH2669"),
    ]
    corrupted = deepcopy(contracts[HEAVY_ID].model_dump(mode="json"))
    corrupted["scheduled_packet_groups"][0]["source_frame_row_ref"] = "鰲믦돯-也?A4135:AT4135"
    try:
        ActionTimingContract.model_validate(corrupted)
    except ValidationError:
        pass
    else:
        raise AssertionError("shifted/mojibake source row was accepted")
    print("mornye_stage2c_source_ref_utf8_and_row_join_v124_smoke_test ok rows=4136,4143-4147 coefficients=2664,2666-2669")


if __name__ == "__main__":
    main()
