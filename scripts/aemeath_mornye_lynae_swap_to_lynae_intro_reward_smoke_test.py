from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env.wuwa_env import WuwaDpsEnv


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
RESOLVED_ID = "transition:lynae_intro_time_to_show_some_colors"


def set_full_concerto(env: WuwaDpsEnv, character_id: str) -> None:
    env.simulation.state.concerto_energy[character_id] = 100.0
    env.simulation.state.character_states[character_id]["concerto_energy"] = 100.0
    env.simulation.state.character_states[character_id]["concerto_ready"] = True


def main() -> None:
    env = WuwaDpsEnv(data_dir=ROOT / "data", party=PARTY_ID)
    env.reset(seed=7)
    env.simulation.state.active_character_id = "aemeath"
    set_full_concerto(env, "aemeath")

    action_index = env.get_policy_action_ids().index("swap_to_lynae")
    _observation, reward, _terminated, _truncated, info = env.step(action_index)
    row = env.simulation.timeline[-1]

    assert info["valid_action"] is True
    assert info["action_id"] == "swap_to_lynae"
    assert info["resolved_action_id"] == RESOLVED_ID
    assert info["damage_this_action"] > 0.0
    assert reward > 0.0
    assert row.resolved_action_id == RESOLVED_ID
    assert row.total_action_damage == info["damage_this_action"]
    assert row.combat_time_cost == 80 / 60
    assert row.incoming_intro_applied is True

    print(
        "aemeath_mornye_lynae_swap_to_lynae_intro_reward_smoke_test ok",
        {
            "reward": reward,
            "damage_this_action": info["damage_this_action"],
            "resolved_action_id": info["resolved_action_id"],
        },
    )


if __name__ == "__main__":
    main()
