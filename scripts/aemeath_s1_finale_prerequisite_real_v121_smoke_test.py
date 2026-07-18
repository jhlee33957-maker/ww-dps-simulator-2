from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim, ready_aemeath_charged_ii


def main() -> None:
    sim = make_account_sim("aemeath")
    ready_aemeath_charged_ii(sim)
    assert sim.execute_action("aemeath_heavy_aemeath_charged_2")
    assert sim.state.character_mechanics_state["aemeath"]["synchronization_rate"] == 100.0
    sim = make_account_sim("aemeath")
    ready_aemeath_charged_ii(sim)
    sim.state.character_mechanics_state["aemeath"]["heavenfall_unbound"] = True
    sim.state.character_mechanics_state["aemeath"]["heavenfall_unbound_remaining"] = 30.0
    assert sim.execute_action("aemeath_heavy_aemeath_charged_2")
    assert sim.state.character_mechanics_state["aemeath"]["synchronization_rate"] == 0.0
    print("aemeath_s1_finale_prerequisite_real_v121_smoke_test ok")


if __name__ == "__main__":
    main()
