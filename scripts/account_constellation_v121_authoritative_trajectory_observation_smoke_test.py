from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim
from simulator.account_constellation_effects import build_account_observation_labels


def main() -> None:
    sim = make_account_sim("aemeath")
    sim.state.rupturous_trail_stacks = 30
    sim.state.character_mechanics_state["_account_constellation"]["aemeath_s6_trajectories"] = 0
    index = build_account_observation_labels().index("account_aemeath.s6_trajectory_ratio")
    assert sim.account_observation_values()[index] == 0.5
    print("account_constellation_v121_authoritative_trajectory_observation_smoke_test ok")


if __name__ == "__main__":
    main()
