from __future__ import annotations

from pathlib import Path

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from env.action_mask import action_mask
from env.reward import calculate_reward
from simulator.simulation import Simulation


class WuwaDpsEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(
        self,
        data_dir: Path | str = "data",
        selected_character_ids: list[str] | str | None = None,
        character_ids: list[str] | str | None = None,
        initial_active_character: str | None = None,
    ) -> None:
        super().__init__()
        self.data_dir = Path(data_dir)
        self.selected_character_ids_arg = selected_character_ids if selected_character_ids is not None else character_ids
        self.initial_active_character_arg = initial_active_character
        self.simulation = Simulation.from_json(
            self.data_dir,
            selected_character_ids=self.selected_character_ids_arg,
            initial_active_character=self.initial_active_character_arg,
        )
        self.action_ids = self._get_action_order()
        self.character_ids = self._get_character_order()
        self.buff_ids = self._get_buff_order()
        self.action_space = spaces.Discrete(len(self.action_ids))
        self.observation_space = spaces.Box(
            low=0.0,
            high=np.inf,
            shape=(self._get_observation_size(),),
            dtype=np.float32,
        )

    def reset(self, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        self.simulation = Simulation.from_json(
            self.data_dir,
            selected_character_ids=self.selected_character_ids_arg,
            initial_active_character=self.initial_active_character_arg,
        )
        self.action_ids = self._get_action_order()
        self.character_ids = self._get_character_order()
        self.buff_ids = self._get_buff_order()
        return self._get_observation(), {}

    def step(self, action: int):
        before_damage = self.simulation.state.total_damage
        invalid_action = False

        if action < 0 or action >= len(self.action_ids):
            invalid_action = True
            action_id = "short_wait"
            resolved_action_id = self.simulation.resolve_action_id(action_id)
            valid = self.simulation.execute_action(action_id)
        else:
            action_id = self.action_ids[action]
            resolved_action_id = self.simulation.resolve_action_id(action_id)
            valid = self.simulation.execute_action(action_id)
            if not valid:
                invalid_action = True
                if "short_wait" in self.simulation.actions:
                    self.simulation.execute_action("short_wait")

        damage_this_action = self.simulation.state.total_damage - before_damage
        terminated = self.simulation.state.current_time >= self.simulation.combat_duration
        truncated = False
        reward = calculate_reward(damage_this_action) if not invalid_action else -1.0
        info = {
            "action_id": action_id,
            "resolved_action_id": resolved_action_id,
            "valid_action": valid and not invalid_action,
            "invalid_action": invalid_action,
            "damage_this_action": damage_this_action,
            "total_damage": self.simulation.state.total_damage,
            "dps": self.simulation.state.total_damage / self.simulation.combat_duration,
        }
        return self._get_observation(), reward, terminated, truncated, info

    def action_masks(self) -> np.ndarray:
        return action_mask(self.simulation)

    def _get_action_order(self) -> list[str]:
        return self.simulation.get_policy_action_ids()

    def _get_character_order(self) -> list[str]:
        return list(self.simulation.selected_character_ids)

    def _get_buff_order(self) -> list[str]:
        return list(self.simulation.buffs)

    def _get_observation_size(self) -> int:
        base_values = 3
        active_character_one_hot = len(self.character_ids)
        resonance_ratios = len(self.character_ids)
        concerto_ratios = len(self.character_ids)
        cooldown_ratios = len(self.action_ids)
        buff_duration_ratios = len(self.buff_ids)
        anomaly_stack_counts = 4
        anomaly_duration_ratios = 4
        character_mechanic_values = sum(
            len(self.simulation.character_mechanics[character_id].get_observation_labels())
            for character_id in self.character_ids
        )
        return (
            base_values
            + active_character_one_hot
            + resonance_ratios
            + concerto_ratios
            + cooldown_ratios
            + buff_duration_ratios
            + anomaly_stack_counts
            + anomaly_duration_ratios
            + character_mechanic_values
        )

    def _get_observation(self) -> np.ndarray:
        state = self.simulation.state
        duration = self.simulation.combat_duration
        values: list[float] = [
            state.current_time / duration,
            max(0.0, duration - state.current_time) / duration,
            state.total_damage / 1_000_000.0,
        ]
        values.extend(
            1.0 if character_id == state.active_character_id else 0.0
            for character_id in self.character_ids
        )
        values.extend(
            state.resonance_energy.get(character_id, 0.0)
            / self.simulation.characters[character_id].resonance_energy_max
            for character_id in self.character_ids
        )
        values.extend(
            state.concerto_energy.get(character_id, 0.0) / 100.0
            for character_id in self.character_ids
        )
        values.extend(self._cooldown_ratio(action_id) for action_id in self.action_ids)
        values.extend(self._buff_duration_ratio(buff_id) for buff_id in self.buff_ids)
        anomaly_order = ["aero_erosion", "spectro_frazzle", "electro_flare", "havoc_bane"]
        values.extend(
            self.simulation.state.active_anomalies.get(anomaly_type).stacks / 99.0
            if anomaly_type in self.simulation.state.active_anomalies
            else 0.0
            for anomaly_type in anomaly_order
        )
        values.extend(
            self.simulation.state.active_anomalies.get(anomaly_type).remaining_duration / 6.0
            if anomaly_type in self.simulation.state.active_anomalies
            else 0.0
            for anomaly_type in anomaly_order
        )
        for character_id in self.character_ids:
            mechanic = self.simulation.character_mechanics[character_id]
            values.extend(mechanic.get_observation_values(state))
        return np.array(values, dtype=np.float32)

    def observation_labels(self) -> list[str]:
        labels = [
            "time_elapsed",
            "time_remaining",
            "total_damage",
        ]
        labels.extend(f"active_character.{character_id}" for character_id in self.character_ids)
        labels.extend(f"resonance_ratio.{character_id}" for character_id in self.character_ids)
        labels.extend(f"concerto_ratio.{character_id}" for character_id in self.character_ids)
        labels.extend(f"cooldown_ratio.{action_id}" for action_id in self.action_ids)
        labels.extend(f"buff_duration_ratio.{buff_id}" for buff_id in self.buff_ids)
        labels.extend(f"anomaly_stacks.{anomaly_type}" for anomaly_type in ["aero_erosion", "spectro_frazzle", "electro_flare", "havoc_bane"])
        labels.extend(f"anomaly_duration.{anomaly_type}" for anomaly_type in ["aero_erosion", "spectro_frazzle", "electro_flare", "havoc_bane"])
        for character_id in self.character_ids:
            labels.extend(self.simulation.character_mechanics[character_id].get_observation_labels())
        return labels

    def _cooldown_ratio(self, action_id: str) -> float:
        action_data = self.simulation.resolve_action(self.simulation.actions[action_id])
        if action_data.cooldown <= 0.0:
            return 0.0
        key = action_data.cooldown_group or action_data.id
        return self.simulation.state.cooldowns.get(key, 0.0) / action_data.cooldown

    def _buff_duration_ratio(self, buff_id: str) -> float:
        buff = self.simulation.buffs[buff_id]
        remaining = max(
            (active.remaining_duration for active in self.simulation.state.active_buffs if active.buff_id == buff_id),
            default=0.0,
        )
        return remaining / buff.duration

    def _observation(self) -> np.ndarray:
        return self._get_observation()

    def get_selected_character_ids(self) -> list[str]:
        return list(self.simulation.selected_character_ids)

    def get_policy_action_ids(self) -> list[str]:
        return list(self.action_ids)

    def get_initial_active_character(self) -> str:
        return self.simulation.initial_active_character
