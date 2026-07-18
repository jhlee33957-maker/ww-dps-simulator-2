from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim


def main() -> None:
    sim = make_account_sim("aemeath")
    assert sim.execute_action("aemeath_liberation_overdrive")
    hit = sim.last_action_result.hit_details[0]
    assert hit["account_damage_amp_add"] == 0.4
    assert any(event["event_type"] == "aemeath_s6_liberation_target_deepen" for event in hit["account_constellation_damage_context"])
    print("aemeath_s6_liberation_deepen_real_v121_smoke_test ok")


if __name__ == "__main__":
    main()
