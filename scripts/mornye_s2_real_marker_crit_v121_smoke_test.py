from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim, ready_mornye_inversion


def main() -> None:
    sim = make_account_sim("mornye")
    ready_mornye_inversion(sim)
    assert sim.execute_action("mornye_heavy_inversion")
    assert sim.state.character_mechanics_state["mornye"]["observation_marker_active"] is True

    assert sim.execute_action("mornye_basic_stage_1")
    hit = sim.last_action_result.hit_details[0]
    assert hit["account_crit_damage_after"] == hit["account_crit_damage_before"] + 0.32
    assert any(
        event["event_type"] == "mornye_s2_marker_crit_damage_formula"
        for event in hit["account_constellation_damage_context"]
    )
    print("mornye_s2_real_marker_crit_v121_smoke_test ok")


if __name__ == "__main__":
    main()
