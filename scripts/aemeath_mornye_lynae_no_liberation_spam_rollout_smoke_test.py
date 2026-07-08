from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env.wuwa_env import WuwaDpsEnv


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
SELECTOR_ID = "lynae_resonance_liberation"
RESOLVED_ID = "lynae_resonance_liberation_prismatic_overblast"
COOLDOWN_GROUP = "lynae_resonance_liberation"


def step_action(env: WuwaDpsEnv, action_id: str):
    action_index = env.get_policy_action_ids().index(action_id)
    before_energy = env.simulation.state.resonance_energy.get("lynae", 0.0)
    before_cooldown = env.simulation.state.cooldowns.get(COOLDOWN_GROUP, 0.0)
    observation, reward, terminated, truncated, info = env.step(action_index)
    return before_energy, before_cooldown, observation, reward, terminated, truncated, info


def main() -> None:
    env = WuwaDpsEnv(data_dir=ROOT / "data", party=PARTY_ID)
    observation, _info = env.reset(seed=321)
    initial_shape = observation.shape

    env.simulation.state.active_character_id = "lynae"
    env.simulation.state.resonance_energy["lynae"] = 125.0

    seen_resolved: list[str] = []
    before_energy, before_cooldown, observation, _reward, terminated, _truncated, info = step_action(env, SELECTOR_ID)
    assert info["valid_action"] is True
    assert info["resolved_action_id"] == RESOLVED_ID
    assert before_energy >= 125.0
    assert before_cooldown <= 0.0
    assert env.simulation.state.cooldowns.get(COOLDOWN_GROUP, 0.0) > 0.0
    assert env.simulation.state.resonance_energy.get("lynae", 0.0) < 125.0
    seen_resolved.append(str(info["resolved_action_id"]))

    rng = np.random.default_rng(321)
    for _step in range(30):
        if terminated:
            break
        mask = env.action_masks()
        valid_indices = np.flatnonzero(mask)
        assert len(valid_indices) > 0
        action = int(rng.choice(valid_indices))
        before_energy = env.simulation.state.resonance_energy.get("lynae", 0.0)
        before_cooldown = env.simulation.state.cooldowns.get(COOLDOWN_GROUP, 0.0)
        observation, _reward, terminated, _truncated, info = env.step(action)
        assert observation.shape == initial_shape
        if info["valid_action"] and info["resolved_action_id"] == RESOLVED_ID:
            assert not seen_resolved or seen_resolved[-1] != RESOLVED_ID
            assert before_energy >= 125.0
            assert before_cooldown <= 0.0
        if info["valid_action"]:
            seen_resolved.append(str(info["resolved_action_id"]))

    print("aemeath_mornye_lynae_no_liberation_spam_rollout_smoke_test ok")


if __name__ == "__main__":
    main()
