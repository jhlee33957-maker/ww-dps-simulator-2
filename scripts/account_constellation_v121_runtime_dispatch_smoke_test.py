from __future__ import annotations

from account_constellation_v121_runtime_test_utils import (
    event_types,
    make_account_sim,
    ready_aemeath_charged_ii,
    ready_lynae_visual_impact,
    ready_mornye_distributed_array,
)


def main() -> None:
    aemeath = make_account_sim("aemeath")
    ready_aemeath_charged_ii(aemeath)
    assert aemeath.execute_action("aemeath_heavy_aemeath_charged_2")
    assert aemeath.state.character_mechanics_state["_account_constellation"]["dispatch_counts"]["aemeath"] == 1
    assert "aemeath_s1_charged_ii_sync" in event_types(aemeath.last_action_result)

    lynae = make_account_sim("lynae")
    ready_lynae_visual_impact(lynae)
    assert lynae.execute_action("lynae_visual_impact")
    assert lynae.state.character_mechanics_state["_account_constellation"]["dispatch_counts"]["lynae"] == 1
    assert "lynae_s2_self_deepen_intrinsic" in event_types(lynae.last_action_result)
    assert any(
        event["event_type"] == "lynae_s2_self_deepen_formula"
        for event in lynae.last_action_result.hit_details[0]["account_constellation_damage_context"]
    )

    mornye = make_account_sim("mornye")
    ready_mornye_distributed_array(mornye)
    assert mornye.execute_action("mornye_skill_distributed_array")
    assert mornye.state.character_mechanics_state["_account_constellation"]["dispatch_counts"]["mornye"] == 1
    assert "mornye_s3_distributed_array" in event_types(mornye.last_action_result)
    print("account_constellation_v121_runtime_dispatch_smoke_test ok")


if __name__ == "__main__":
    main()
