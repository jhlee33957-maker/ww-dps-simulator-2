from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim


def _hits(sim):
    return [hit for hit in sim.last_action_result.hit_details if hit.get("is_generated_mechanic_damage")]


def main() -> None:
    normal = make_account_sim("aemeath")
    assert normal.execute_action("aemeath_sync_strike_armament_merge")
    assert len(_hits(normal)) == 5

    enhanced = make_account_sim("aemeath")
    state = enhanced.state.character_mechanics_state["aemeath"]
    state["forte_enhancement_stacks"] = 1
    state["forte_enhancement_remaining"] = 30.0
    assert enhanced.execute_action("aemeath_sync_strike_armament_merge")
    hits = _hits(enhanced)
    assert len(hits) == 10
    assert all(hit["generated_damage_packet_id"] == "aemeath_seraphic_duet_tune_rupture_enhanced_followup" for hit in hits)
    assert all(hit["source_multiplier"] == 1.0935 and hit["hit_interval_frames"] == 2 for hit in hits)
    s2_events = [
        event
        for hit in hits
        for event in hit["account_constellation_damage_context"]
        if event["event_type"] == "aemeath_s2_tune_stack_generated_hit"
    ]
    assert [round(event["damage_amp_add"], 4) for event in s2_events] == [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.0, 1.0, 1.0, 1.0]
    print("aemeath_s2_tune_variant_5_vs_10_hits_v121_smoke_test ok")


if __name__ == "__main__":
    main()
