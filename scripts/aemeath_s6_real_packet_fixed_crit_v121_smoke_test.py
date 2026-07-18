from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim


def main() -> None:
    sim = make_account_sim("aemeath")
    sim.state.mechanics_config.setdefault("aemeath", {})["aemeath_resonance_mode"] = "tune_rupture"
    assert sim.execute_action("aemeath_sync_strike_armament_merge")
    packets = [
        hit
        for hit in sim.last_action_result.hit_details
        if hit.get("generated_damage_packet_id") == "aemeath_seraphic_duet_tune_rupture_followup"
    ]
    assert packets and all(hit["crit_rate_after_override"] == 0.8 and hit["crit_damage_after_override"] == 2.75 for hit in packets)
    assert all(hit["expected_crit_multiplier"] == 2.4 for hit in packets)
    print("aemeath_s6_real_packet_fixed_crit_v121_smoke_test ok")


if __name__ == "__main__":
    main()
