from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env.wuwa_env import WuwaDpsEnv


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
REAL_MEMBERS = {"mornye", "aemeath", "lynae"}


def main() -> None:
    env = WuwaDpsEnv(data_dir=ROOT / "data", party=PARTY_ID)
    observation, _info = env.reset(seed=123)
    initial_shape = observation.shape
    rng = np.random.default_rng(123)

    for _step in range(30):
        mask = env.action_masks()
        assert mask.shape == (env.action_space.n,)
        valid_indices = np.flatnonzero(mask)
        assert len(valid_indices) > 0
        action = int(rng.choice(valid_indices))
        observation, _reward, terminated, _truncated, _info = env.step(action)
        assert observation.shape == initial_shape
        assert env.simulation.state.active_character_id in REAL_MEMBERS
        assert env.simulation.state.active_character_id != "dummy_sub_dps"
        if terminated:
            break

    assert env.get_selected_party_character_ids() == ["mornye", "aemeath", "lynae"]
    print("aemeath_mornye_lynae_short_rollout_smoke_test ok")


if __name__ == "__main__":
    main()
