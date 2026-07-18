from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim


def main() -> None:
    sim = make_account_sim("aemeath")
    sim.state.mechanics_config.setdefault("aemeath", {})["aemeath_resonance_mode"] = "tune_rupture"
    assert sim.execute_action("aemeath_sync_strike_armament_merge")
    assert sim.state.rupturous_trail_stacks == 10
    assert sim.state.rupturous_trail_stacks == 10
    assert sim.state.rupturous_trail_remaining == 30.0
    print("aemeath_s6_real_trajectory_gain_seraphic_v121_smoke_test ok")


if __name__ == "__main__":
    main()
