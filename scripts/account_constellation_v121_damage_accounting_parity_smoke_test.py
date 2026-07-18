from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim, ready_aemeath_charged_ii


def main() -> None:
    sim = make_account_sim("aemeath")
    ready_aemeath_charged_ii(sim)
    assert sim.execute_action("aemeath_heavy_aemeath_charged_2")
    result = sim.last_action_result
    hit_total = sum(float(hit["damage"]) for hit in result.hit_details)
    assert abs(hit_total - result.direct_action_damage) < 1e-6
    assert result.direct_action_damage == result.total_action_damage
    assert "account_constellation_damage_delta" not in sim.state.damage_log[-1]
    contexts = [
        event
        for hit in result.hit_details
        for event in hit.get("account_constellation_damage_context", [])
    ]
    assert any(event["event_type"] == "aemeath_s1_heavy_crit_damage_formula" for event in contexts)
    assert all("damage_delta" not in event for event in result.account_constellation_events)
    print("account_constellation_v121_damage_accounting_parity_smoke_test ok")


if __name__ == "__main__":
    main()
