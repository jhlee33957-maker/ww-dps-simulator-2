from __future__ import annotations

from account_constellation_v121_runtime_test_utils import (
    make_account_sim,
    ready_lynae_visual_impact,
    ready_mornye_inversion,
)


def main() -> None:
    lynae = make_account_sim("lynae")
    ready_lynae_visual_impact(lynae)
    assert lynae.execute_action("lynae_visual_impact")
    first_hit = lynae.last_action_result.hit_details[0]
    assert first_hit["account_damage_amp_add"] == 0.25
    assert any(
        event["event_type"] == "lynae_s2_self_deepen_formula"
        for event in first_hit["account_constellation_damage_context"]
    )

    mornye = make_account_sim("mornye")
    ready_mornye_inversion(mornye)
    assert mornye.execute_action("mornye_heavy_inversion")
    state = mornye.state.character_mechanics_state["mornye"]
    assert state["observation_marker_active"] is True
    assert state["observation_marker_remaining"] == 20.0
    assert mornye.state.interfered_marker_remaining == 20.0
    assert "mornye_interfered_marker_damage_amp" in {buff.buff_id for buff in mornye.state.active_buffs}
    assert mornye.execute_action("mornye_basic_stage_1")
    marker_hit = mornye.last_action_result.hit_details[0]
    assert marker_hit["account_crit_damage_after"] > marker_hit["account_crit_damage_before"]
    assert any(
        event["event_type"] == "mornye_s2_marker_crit_damage_formula"
        for event in marker_hit["account_constellation_damage_context"]
    )
    print("account_constellation_v121_real_buff_marker_smoke_test ok")


if __name__ == "__main__":
    main()
