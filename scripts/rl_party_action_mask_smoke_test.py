from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from env.action_mask import action_mask
from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"


def mask_for(sim: Simulation) -> dict[str, bool]:
    return dict(zip(sim.get_policy_action_ids(), [bool(item) for item in action_mask(sim)]))


def main() -> None:
    solo = Simulation.from_json(DATA_DIR, party="aemeath")
    solo_policy_ids = solo.get_policy_action_ids()
    assert not any(action_id.startswith("swap_to_") for action_id in solo_policy_ids)
    assert all("qte" not in action_id.lower() for action_id in solo_policy_ids)
    solo_mask = mask_for(solo)
    assert len(solo_mask) == len(solo_policy_ids)
    assert solo_mask["aemeath_basic_attack"] is True

    party = Simulation.from_json(DATA_DIR, party="aemeath_test_party")
    policy_ids = party.get_policy_action_ids()
    party_mask = mask_for(party)
    assert len(party_mask) == len(policy_ids)
    assert "swap_to_dummy_support" in policy_ids
    assert "swap_to_dummy_sub_dps" in policy_ids
    assert "aemeath_qte_intro_human" not in policy_ids
    assert "aemeath_qte_intro_mech" not in policy_ids
    assert party_mask["swap_to_aemeath"] is False
    assert party_mask["swap_to_dummy_support"] is True
    assert party_mask["aemeath_basic_attack"] is True
    assert party_mask["dummy_support_attack"] is False
    assert party_mask["dummy_sub_dps_attack"] is False

    assert party.execute_action("swap_to_dummy_support")
    assert party.timeline[-1].transition_type == "normal_swap"
    assert party.timeline[-1].transition_reason == "concerto_not_ready"
    swapped_mask = mask_for(party)
    assert swapped_mask["swap_to_aemeath"] is True
    assert swapped_mask["swap_to_dummy_support"] is False
    assert swapped_mask["aemeath_basic_attack"] is False
    assert swapped_mask["dummy_support_attack"] is True
    assert swapped_mask["dummy_support_buff"] is True

    try:
        from env.wuwa_env import WuwaDpsEnv

        env = WuwaDpsEnv(DATA_DIR, party="aemeath_test_party")
        assert len(env.action_masks()) == env.action_space.n
        assert env.get_policy_action_ids() == policy_ids
        print("Env party action count:", env.action_space.n)
    except ModuleNotFoundError:
        print("Gymnasium dependency missing; skipped env portion.")

    print("RL party action mask smoke test passed.")


if __name__ == "__main__":
    main()
