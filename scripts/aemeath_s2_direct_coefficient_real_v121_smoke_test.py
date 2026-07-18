from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim


def main() -> None:
    sim = make_account_sim("aemeath")
    assert sim.execute_action("aemeath_sync_strike_armament_merge")
    hit = next(hit for hit in sim.last_action_result.hit_details if not hit.get("is_generated_mechanic_damage"))
    assert hit["effective_coefficient"] == hit["base_coefficient"] * 2.0
    assert hit["account_coefficient_multiplier"] == 2.0
    print("aemeath_s2_direct_coefficient_real_v121_smoke_test ok")


if __name__ == "__main__":
    main()
