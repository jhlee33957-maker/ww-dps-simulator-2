from stage2c_timing_test_support import ARRAY_ID, ready_account_array_sim, ready_heavy_sim
from copy import deepcopy
from pydantic import ValidationError
from simulator.action_timing_contract import ActionTimingContract


def main() -> None:
    contract = ready_heavy_sim().action_timing_contracts[ARRAY_ID]
    assert contract.same_character_input_frame == contract.swap_input_frame == contract.action_end_frame == 60
    assert [g.packet_group_id for g in contract.scheduled_packet_groups] == ["mornye_distributed_array_frame_1_heal", "mornye_distributed_array_e2_1", "mornye_distributed_array_e2_2", "mornye_distributed_array_e2_3", "mornye_distributed_array_e2_4"]
    assert [g.scheduled_frames for g in contract.scheduled_packet_groups] == [[1], [22], [22], [36], [36]]
    bad = deepcopy(contract.model_dump(mode="json")); bad["scheduled_packet_groups"].pop()
    try: ActionTimingContract.model_validate(bad)
    except ValidationError: pass
    else: raise AssertionError("omitted E2 packet accepted")
    sim = ready_account_array_sim()
    action_start = sim.state.current_time
    assert sim.execute_action(ARRAY_ID)
    heals = sim.last_action_result.scheduled_healing_events
    assert len(heals) == 1
    heal = heals[0]
    assert abs(heal["scheduled_wall_time"] - (action_start + 1 / 60)) < 1e-9
    assert abs(heal["processed_wall_time"] - (action_start + 1 / 60)) < 1e-9
    assert heal["source_action_id"] == ARRAY_ID
    assert heal["source_frame_row_ref"] == "角色-女!A4143:AT4143"
    assert heal["team_heal_event_triggered"] is True
    assert heal["scheduled_wall_time"] not in {action_start, action_start + 1.0}
    print("mornye_distributed_array_frame1_heal_v124_smoke_test ok heal=1F E2=22,22,36,36 end=60")


if __name__ == "__main__": main()
