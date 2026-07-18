from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim


def main() -> None:
    consumed = make_account_sim("aemeath")
    consumed.state.rupturous_trail_stacks = 20
    consumed.state.rupturous_trail_remaining = 30.0
    assert consumed.execute_action("aemeath_sync_strike_armament_merge")
    hits = [hit for hit in consumed.last_action_result.hit_details if hit.get("is_generated_mechanic_damage")]
    assert all(hit["tune_response_multiplier"] == 1.0935 * 1.8 for hit in hits)
    assert consumed.state.rupturous_trail_stacks == 10

    preserved = make_account_sim("aemeath")
    preserved.state.rupturous_trail_stacks = 20
    preserved.state.rupturous_trail_remaining = 30.0
    preserved.state.character_mechanics_state["aemeath"]["trail_no_cost_remaining"] = 30.0
    assert preserved.execute_action("aemeath_sync_strike_armament_merge")
    assert preserved.state.rupturous_trail_stacks == 30
    print("aemeath_s2_tune_trajectory_consumption_v121_smoke_test ok")


if __name__ == "__main__":
    main()
