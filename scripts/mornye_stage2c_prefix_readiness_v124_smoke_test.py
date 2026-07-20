from account_constellation_v121_runtime_test_utils import make_account_sim
from stage2c_timing_test_support import ARRAY_ID, HEAVY_ID, packet_events


def main() -> None:
    sim = make_account_sim("mornye")
    prefix = [
        "mornye_basic_stage_1", "mornye_basic_stage_2", "swap_to_aemeath",
        "aemeath_heavy_aemeath_charged_2", "swap_to_mornye", "mornye_basic_stage_1",
        "mornye_heavy_geopotential_shift", "swap_to_lynae",
        "lynae_resonance_liberation_prismatic_overblast", "lynae_to_a_vivid_tomorrow",
        "swap_to_mornye", ARRAY_ID,
    ]
    assert all(sim.execute_action(action_id) for action_id in prefix)
    state = sim.state.character_mechanics_state["mornye"]
    assert len(packet_events(sim, ARRAY_ID)) == 4 and state["relative_momentum"] == 100.0
    assert sim.execute_action(HEAVY_ID)
    heavy, = packet_events(sim, HEAVY_ID)
    assert abs(heavy["event_wall_time"] - sim.last_action_result.start_time - 66 / 60) < 1e-9
    assert state["observation_marker_active"] and sim.last_action_result.valid
    print("mornye_stage2c_prefix_readiness_v124_smoke_test ok array_then_inversion_natural_marker_ready")


if __name__ == "__main__": main()
