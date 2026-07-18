from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim


def main() -> None:
    sim = make_account_sim("aemeath")
    sim.state.mechanics_config.setdefault("aemeath", {})["aemeath_resonance_mode"] = "tune_rupture"
    assert sim.execute_action("aemeath_sync_strike_armament_merge")
    hits = [
        hit
        for hit in sim.last_action_result.hit_details
        if hit.get("generated_damage_packet_id") == "aemeath_seraphic_duet_tune_rupture_followup"
    ]
    assert len(hits) == 5
    assert all(hit["source_multiplier"] == 1.0935 for hit in hits)
    assert [hit["hit_time"] for hit in hits] == [frame / 60.0 for frame in (4, 8, 12, 16, 20)]
    events = [
        next(event for event in hit["account_constellation_damage_context"] if event["event_type"] == "aemeath_s2_tune_stack_generated_hit")
        for hit in hits
    ]
    assert [round(event["damage_amp_add"], 4) for event in events] == [0.0, 0.2, 0.4, 0.6, 0.8]
    assert events[-1]["stacks_after"] == 5
    print("aemeath_s2_mechanic_hit_sequence_real_v121_smoke_test ok")


if __name__ == "__main__":
    main()
