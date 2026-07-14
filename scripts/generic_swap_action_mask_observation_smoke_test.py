from __future__ import annotations

from v114_test_support import assert_close, build
from env.action_mask import action_mask
from env.observation_features import OBSERVATION_VERSION, build_observation_labels, build_observation_values


def main() -> None:
    sim = build()
    order = sim.get_policy_action_ids()
    assert len(order) == 25
    assert OBSERVATION_VERSION == "slot_generic_mechanics_v5"
    assert len(build_observation_labels()) == len(build_observation_values(sim)) == 314
    target = sim.actions["swap_to_mornye"]
    assert target.cooldown == 1.0
    assert target.cooldown_group == "swap_reentry:mornye"
    assert sim.execute_action("swap_to_mornye")
    assert "swap_reentry:mornye" not in sim.state.cooldowns
    assert sim.execute_action("swap_to_lynae")
    mask = action_mask(sim)
    assert not bool(mask[order.index("swap_to_mornye")])
    values = build_observation_values(sim)
    slot = order.index("swap_to_mornye")
    action_slot_start = 314 - 32 * 3
    assert_close(values[action_slot_start + slot * 3 + 2], 1.0)
    print("generic_swap_action_mask_observation_smoke_test ok")


if __name__ == "__main__":
    main()
