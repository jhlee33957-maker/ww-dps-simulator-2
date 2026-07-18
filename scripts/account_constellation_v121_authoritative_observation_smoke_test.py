from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim, ready_mornye_inversion
from simulator.account_constellation_effects import (
    ACCOUNT_OBSERVATION_EXTRA_LABELS,
    ACCOUNT_OBSERVATION_SHAPE,
    build_account_observation_labels,
)


def main() -> None:
    labels = build_account_observation_labels()
    assert len(labels) == ACCOUNT_OBSERVATION_SHAPE
    assert labels[-len(ACCOUNT_OBSERVATION_EXTRA_LABELS) :] == ACCOUNT_OBSERVATION_EXTRA_LABELS

    sim = make_account_sim("mornye")
    before = sim.account_observation_values()
    assert len(before) == ACCOUNT_OBSERVATION_SHAPE
    ready_mornye_inversion(sim)
    assert sim.execute_action("mornye_heavy_inversion")
    after = sim.account_observation_values()
    marker_index = labels.index("account_mornye.s1_marker_remaining_ratio")
    crit_index = labels.index("account_mornye.s2_marker_crit_damage_scaled")
    assert after[marker_index] > before[marker_index]
    assert after[crit_index] == 0.32
    print("account_constellation_v121_authoritative_observation_smoke_test ok")


if __name__ == "__main__":
    main()
