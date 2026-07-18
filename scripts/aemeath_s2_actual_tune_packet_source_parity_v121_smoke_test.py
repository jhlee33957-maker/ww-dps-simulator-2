from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim


def main() -> None:
    sim = make_account_sim("aemeath")
    assert sim.execute_action("aemeath_sync_strike_armament_merge")
    hits = [
        hit for hit in sim.last_action_result.hit_details
        if hit.get("generated_damage_packet_id") == "aemeath_seraphic_duet_tune_rupture_followup"
    ]
    assert len(hits) == 5
    assert all(hit["source_multiplier"] == 1.0935 for hit in hits)
    assert all(hit["hit_interval_frames"] == 4 for hit in hits)
    assert [hit["hit_time"] for hit in hits] == [frame / 60.0 for frame in (4, 8, 12, 16, 20)]
    assert sim.last_action_result.total_action_damage == sum(hit["damage"] for hit in sim.last_action_result.hit_details)
    print("aemeath_s2_actual_tune_packet_source_parity_v121_smoke_test ok")


if __name__ == "__main__":
    main()
