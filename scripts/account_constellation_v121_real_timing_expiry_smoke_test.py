from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim, ready_lynae_visual_impact


def main() -> None:
    aemeath = make_account_sim("aemeath")
    aemeath.state.mechanics_config.setdefault("aemeath", {})["aemeath_resonance_mode"] = "tune_rupture"
    assert aemeath.execute_action("aemeath_sync_strike_armament_merge")
    assert any(
        event["event_type"] == "aemeath_s2_tune_stack_generated_hit"
        for hit in aemeath.last_action_result.hit_details
        for event in hit["account_constellation_damage_context"]
    )
    account_state = aemeath.state.character_mechanics_state["_account_constellation"]
    assert account_state["aemeath_s2_remaining"] == 0.0
    assert account_state["aemeath_s2_stacks"] == 0
    assert aemeath.execute_action("short_wait")
    assert account_state["aemeath_s2_remaining"] == 0.0

    lynae = make_account_sim("lynae")
    ready_lynae_visual_impact(lynae)
    assert lynae.execute_action("lynae_visual_impact")
    effect = lynae.scheduled_effect_by_instance_id(lynae.LYNAE_SPRAY_PAINT_INSTANCE_ID)
    assert effect is not None
    assert effect.remaining_duration == 10.0
    assert effect.max_trigger_count == 5
    assert effect.metadata["relative_application_frames"] == [1, 121, 241, 361, 481]
    assert effect.metadata["pull_diagnostic_frames"] == [360]
    assert effect.metadata["movement_effect_value"] == 0.0
    assert lynae.execute_action("short_wait")
    effect = lynae.scheduled_effect_by_instance_id(lynae.LYNAE_SPRAY_PAINT_INSTANCE_ID)
    assert effect is not None
    assert effect.trigger_count == 1
    assert effect.remaining_duration < 10.0
    print("account_constellation_v121_real_timing_expiry_smoke_test ok")


if __name__ == "__main__":
    main()
