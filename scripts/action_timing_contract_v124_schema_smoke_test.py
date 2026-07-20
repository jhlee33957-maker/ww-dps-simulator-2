from __future__ import annotations

from v124_timing_test_support import DATA_DIR, LIBERATION_ID, MORNYE_LIBERATION_ID, VIVID_ID
from simulator.action_timing_contract import TIMING_CONTRACT_SCHEMA_VERSION, load_action_timing_contracts


def main() -> None:
    contracts = load_action_timing_contracts(DATA_DIR)
    assert TIMING_CONTRACT_SCHEMA_VERSION == "action_timing_contract_v124"
    assert set(contracts) == {
        MORNYE_LIBERATION_ID,
        LIBERATION_ID,
        VIVID_ID,
        "mornye_basic_stage_2",
        "mornye_basic_stage_3",
        "mornye_heavy_inversion",
        "mornye_skill_distributed_array",
    }
    liberation, vivid = contracts[LIBERATION_ID], contracts[VIVID_ID]
    assert (liberation.same_character_input_frame, liberation.swap_input_frame, liberation.action_end_frame) == (238, 240, 299)
    assert liberation.global_time_stop_frames == 240
    assert (vivid.swap_input_frame, vivid.same_character_input_frame, vivid.action_end_frame) == (1, 153, 181)
    assert vivid.persist_if_swapped_before_frame == 179
    assert [group.packet_group_id for group in vivid.scheduled_packet_groups] == ["row_2697_packet_family", "row_2698_packet_family"]
    print("action_timing_contract_v124_schema_smoke_test ok")


if __name__ == "__main__":
    main()
