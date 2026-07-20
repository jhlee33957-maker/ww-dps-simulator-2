from stage2c_timing_test_support import HEAVY_ID, ready_heavy_sim
from simulator.action_timing_contract import start_ongoing_action


def main() -> None:
    sim = ready_heavy_sim(); state = sim.state.character_mechanics_state["mornye"]
    start_ongoing_action(sim.state, sim.actions[HEAVY_ID], sim.action_timing_contracts[HEAVY_ID])
    sim.advance_timing_runtime(65 / 60); assert not state["observation_marker_active"]
    sim.advance_timing_runtime(1 / 60); assert state["observation_marker_active"] and state["observation_marker_remaining"] >= 30
    event = [e for e in sim.state.chronological_event_log if e.get("source_action_id") == HEAVY_ID][-1]
    assert event["event_wall_time"] == 66 / 60 and event["observation_marker_duration"] == 30 and event["observation_marker_source"] == "Mornye Heavy Inversion"
    print("mornye_heavy_inversion_marker_timing_v124_smoke_test ok absent=65F applied=66F duration=30")


if __name__ == "__main__": main()
