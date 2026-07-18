from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim, ready_aemeath_charged_ii


def main() -> None:
    enabled = make_account_sim("aemeath")
    ready_aemeath_charged_ii(enabled)
    assert enabled.execute_action("aemeath_heavy_aemeath_charged_2")
    enabled_result = enabled.last_action_result

    disabled = make_account_sim("aemeath")
    disabled.characters["aemeath"].sequence = 0
    ready_aemeath_charged_ii(disabled)
    assert disabled.execute_action("aemeath_heavy_aemeath_charged_2")
    disabled_result = disabled.last_action_result

    assert enabled_result.total_action_damage > disabled_result.total_action_damage
    assert enabled_result.direct_action_damage == enabled_result.total_action_damage
    assert abs(sum(hit["damage"] for hit in enabled_result.hit_details) - enabled_result.total_action_damage) < 1e-6
    contexts = [
        event
        for hit in enabled_result.hit_details
        for event in hit.get("account_constellation_damage_context", [])
    ]
    assert any(event["event_type"] == "aemeath_s1_heavy_crit_damage_formula" for event in contexts)
    assert all("damage_delta" not in event for event in enabled_result.account_constellation_events)
    assert enabled.state.total_damage > disabled.state.total_damage
    print("account_constellation_v121_real_action_damage_smoke_test ok")


if __name__ == "__main__":
    main()
