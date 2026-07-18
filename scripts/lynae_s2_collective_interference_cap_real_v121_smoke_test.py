from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim
from simulator.lynae_tune_strain import refresh_lynae_tune_strain_amp


def main() -> None:
    sim = make_account_sim("lynae")
    assert sim.state.target_tune_strain_interfered_max_stacks == 2
    sim.state.target_interfered_state = "tune_strain_interfered"
    sim.state.target_tune_strain_interfered_remaining = 30.0
    sim.state.target_tune_strain_interfered_stacks = 3
    refresh_lynae_tune_strain_amp(sim.state, sim.characters, sim.buffs)
    assert sim.state.target_tune_strain_interfered_stacks == 2
    print("lynae_s2_collective_interference_cap_real_v121_smoke_test ok")


if __name__ == "__main__":
    main()
