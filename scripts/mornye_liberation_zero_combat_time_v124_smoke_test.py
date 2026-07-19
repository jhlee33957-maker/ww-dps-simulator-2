from __future__ import annotations

from v124_timing_test_support import MORNYE_LIBERATION_ID, make_mornye_liberation_sim


def main() -> None:
    for observation_active, source_end in ((False, 282), (True, 296)):
        sim = make_mornye_liberation_sim(observation_active)
        assert sim.execute_action(MORNYE_LIBERATION_ID)
        instance = sim.state.ongoing_action_instances[-1]
        assert sim.state.current_time * 60 == source_end
        assert sim.state.combat_time == 0.0
        sim.advance_timing_runtime((300 - source_end) / 60, combat_elapsed=0)
        assert sim.state.current_time * 60 == 300
        assert sim.state.combat_time == 0.0
        assert instance.ended
        assert instance.selected_global_time_stop_frames == 300
    print("mornye_liberation_zero_combat_time_v124_smoke_test ok branches=2")


if __name__ == "__main__":
    main()
