from __future__ import annotations

from pathlib import Path

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from env.reward import reward_from_damage
from simulator.simulation import Simulation


class WuwaDpsEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, data_dir: Path | str = "data") -> None:
        super().__init__()
        self.data_dir = Path(data_dir)
        self.simulation = Simulation.from_json(self.data_dir)
        self.action_ids = list(self.simulation.actions)
        self.action_space = spaces.Discrete(len(self.action_ids))
        self.observation_space = spaces.Box(
            low=0.0,
            high=np.inf,
            shape=(5,),
            dtype=np.float32,
        )

    def reset(self, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        self.simulation = Simulation.from_json(self.data_dir)
        return self._observation(), {}

    def step(self, action: int):
        before_damage = self.simulation.state.total_damage
        action_id = self.action_ids[action]
        valid = self.simulation.execute_action(action_id)

        if not valid:
            self.simulation.execute_action("short_wait")

        damage_this_action = self.simulation.state.total_damage - before_damage
        terminated = self.simulation.state.current_time >= self.simulation.combat_duration
        truncated = False
        reward = reward_from_damage(damage_this_action)
        info = {
            "action_id": action_id,
            "valid_action": valid,
            "damage_this_action": damage_this_action,
            "total_damage": self.simulation.state.total_damage,
            "dps": self.simulation.state.total_damage / self.simulation.combat_duration,
        }
        return self._observation(), reward, terminated, truncated, info

    def _observation(self) -> np.ndarray:
        state = self.simulation.state
        active = state.active_character_id
        return np.array(
            [
                state.current_time / self.simulation.combat_duration,
                state.total_damage / 1_000_000.0,
                state.resonance_energy.get(active, 0.0) / 100.0,
                state.concerto_energy.get(active, 0.0) / 100.0,
                float(len(state.active_buffs)),
            ],
            dtype=np.float32,
        )
