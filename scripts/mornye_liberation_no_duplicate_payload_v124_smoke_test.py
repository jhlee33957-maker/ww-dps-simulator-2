from __future__ import annotations

from v124_timing_test_support import MORNYE_LIBERATION_ID, make_mornye_liberation_sim


def main() -> None:
    for observation_active, source_end in ((False, 282), (True, 296)):
        sim = make_mornye_liberation_sim(observation_active)
        assert sim.execute_action(MORNYE_LIBERATION_ID)
        result = sim.last_action_result
        assert len(result.hit_details) == 1
        assert result.concerto_gain == 20
        assert len([row for row in sim.state.damage_log if row.get("action_id") == MORNYE_LIBERATION_ID]) == 1
        damage_before_tail = sim.state.total_damage
        concerto_before_tail = sim.state.concerto_energy["mornye"]
        sim.advance_timing_runtime((300 - source_end) / 60, combat_elapsed=0)
        assert sim.state.total_damage == damage_before_tail
        assert sim.state.concerto_energy["mornye"] == concerto_before_tail == 20
        assert len([row for row in sim.state.damage_log if row.get("action_id") == MORNYE_LIBERATION_ID]) == 1
    print("mornye_liberation_no_duplicate_payload_v124_smoke_test ok branches=2")


if __name__ == "__main__":
    main()
