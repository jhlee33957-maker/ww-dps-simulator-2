from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim


def main() -> None:
    sim = make_account_sim("lynae")
    state = sim.state.character_mechanics_state["lynae"]
    state.update({"kaleidoscopic_parade_remaining": 10.0, "lumiflow": 120.0, "true_color": 0.0})
    assert sim.execute_action("lynae_polychrome_leap")
    hit = sim.last_action_result.hit_details[0]
    assert hit["effective_coefficient"] == hit["base_coefficient"] + 1.2
    assert hit["account_coefficient_add"] == 1.2
    print("lynae_s1_light_leap_real_v121_smoke_test ok")


if __name__ == "__main__":
    main()
