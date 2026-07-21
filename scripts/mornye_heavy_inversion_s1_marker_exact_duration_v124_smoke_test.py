from account_constellation_v121_runtime_test_utils import make_account_sim, ready_mornye_inversion
from stage2c_timing_test_support import HEAVY_ID
from simulator.action_timing_contract import start_ongoing_action


def main() -> None:
    sim = make_account_sim("mornye"); ready_mornye_inversion(sim); state = sim.state.character_mechanics_state["mornye"]
    start_ongoing_action(sim.state, sim.actions[HEAVY_ID], sim.action_timing_contracts[HEAVY_ID])
    sim.advance_timing_runtime(65 / 60); assert not state.get("observation_marker_active", False) and sim.state.interfered_marker_remaining == 0
    sim.advance_timing_runtime(1 / 60); assert state["observation_marker_active"] and state["observation_marker_remaining"] == 30
    assert sim.state.interfered_marker_remaining == 20
    active = next(buff for buff in sim.state.active_buffs if buff.buff_id == "mornye_interfered_marker_damage_amp")
    assert active.remaining_duration == 20
    event = [e for e in sim.state.chronological_event_log if e.get("source_action_id") == HEAVY_ID][-1]
    assert event["event_wall_time"] == 66 / 60 and event["observation_marker_duration"] == 30 and event["observation_marker_source"] == "Mornye Heavy Inversion"
    final_sim = make_account_sim("mornye"); ready_mornye_inversion(final_sim)
    assert final_sim.execute_action(HEAVY_ID)
    final_state = final_sim.state.character_mechanics_state["mornye"]
    active = next(buff for buff in final_sim.state.active_buffs if buff.buff_id == "mornye_interfered_marker_damage_amp")
    assert abs(final_state["observation_marker_remaining"] - 29.666666666666668) < 1e-9
    assert abs(final_sim.state.interfered_marker_remaining - 19.666666666666668) < 1e-9
    assert abs(active.remaining_duration - 19.666666666666668) < 1e-9
    print("mornye_heavy_inversion_s1_marker_exact_duration_v124_smoke_test ok 66F=30/20 86F=29.666666666666668/19.666666666666668")


if __name__ == "__main__": main()
