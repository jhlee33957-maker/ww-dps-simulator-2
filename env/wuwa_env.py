from __future__ import annotations

from pathlib import Path

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from env.action_mask import action_mask
from env.observation_features import (
    OBSERVATION_VERSION,
    build_observation_channel_mapping,
    build_observation_labels,
    build_observation_slot_mapping,
    build_observation_values,
    observation_metadata,
)
from env.reward import calculate_reward
from simulator.simulation import Simulation


CURRICULUM_RESET_MODES = {
    "none",
    "aemeath_ready_for_lynae",
    "lynae_after_intro",
    "lynae_kaleidoscopic_ready",
    "mixed_lynae_curriculum",
}
MIXED_LYNAE_CURRICULUM_CHOICES = (
    "none",
    "aemeath_ready_for_lynae",
    "lynae_after_intro",
    "lynae_kaleidoscopic_ready",
)


class WuwaDpsEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(
        self,
        data_dir: Path | str = "data",
        selected_character_ids: list[str] | str | None = None,
        selected_party_character_ids: list[str] | str | None = None,
        party_character_ids: list[str] | str | None = None,
        party: list[str] | str | None = None,
        character_ids: list[str] | str | None = None,
        initial_active_character: str | None = None,
        transition_config: dict | None = None,
        build_profile_overrides: dict[str, str] | None = None,
        stat_overrides: dict[str, dict[str, float]] | None = None,
        curriculum_reset_mode: str | None = None,
    ) -> None:
        super().__init__()
        self.data_dir = Path(data_dir)
        self.selected_character_ids_arg = (
            selected_character_ids
            if selected_character_ids is not None
            else selected_party_character_ids
            if selected_party_character_ids is not None
            else party_character_ids
            if party_character_ids is not None
            else party
            if party is not None
            else character_ids
        )
        self.party_id_arg = party if isinstance(party, str) else selected_character_ids if isinstance(selected_character_ids, str) else None
        self.initial_active_character_arg = initial_active_character
        self.transition_config_arg = transition_config
        self.build_profile_overrides_arg = build_profile_overrides
        self.stat_overrides_arg = stat_overrides
        self.curriculum_reset_mode_arg = self._normalize_curriculum_reset_mode(curriculum_reset_mode)
        self.last_curriculum_reset_mode = "none"
        self.simulation = Simulation.from_json(
            self.data_dir,
            selected_character_ids=self.selected_character_ids_arg,
            initial_active_character=self.initial_active_character_arg,
            transition_config=self.transition_config_arg,
            build_profile_overrides=self.build_profile_overrides_arg,
            stat_overrides=self.stat_overrides_arg,
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
        self.observation_version = OBSERVATION_VERSION

    def reset(self, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        self.simulation = Simulation.from_json(
            self.data_dir,
            selected_character_ids=self.selected_character_ids_arg,
            initial_active_character=self.initial_active_character_arg,
            transition_config=self.transition_config_arg,
            build_profile_overrides=self.build_profile_overrides_arg,
            stat_overrides=self.stat_overrides_arg,
        )
        self.action_ids = self._get_action_order()
        self.character_ids = self._get_character_order()
        self.buff_ids = self._get_buff_order()
        applied_curriculum_mode = self._select_curriculum_reset_mode()
        self._apply_curriculum_reset(applied_curriculum_mode)
        self.last_curriculum_reset_mode = applied_curriculum_mode
        return self._get_observation(), {"curriculum_reset_mode": applied_curriculum_mode}

    def step(self, action: int):
        if self.simulation.state.combat_time >= self.simulation.combat_duration:
            info = {
                "action_id": None,
                "resolved_action_id": None,
                "valid_action": False,
                "invalid_action": False,
                "damage_this_action": 0.0,
                "total_damage": self.simulation.state.total_damage,
                "dps": self.simulation.state.total_damage / self.simulation.combat_duration,
                "action_time": self.simulation.state.current_time,
                "combat_time": self.simulation.state.combat_time,
                "curriculum_reset_mode": self.last_curriculum_reset_mode,
            }
            return self._get_observation(), 0.0, True, False, info

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
        if valid and not invalid_action and self.simulation.timeline:
            resolved_action_id = self.simulation.timeline[-1].resolved_action_id or resolved_action_id
        terminated = self.simulation.state.combat_time >= self.simulation.combat_duration
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
            "action_time": self.simulation.state.current_time,
            "combat_time": self.simulation.state.combat_time,
            "curriculum_reset_mode": self.last_curriculum_reset_mode,
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
        return len(self.observation_labels())

    def _get_observation(self) -> np.ndarray:
        values = build_observation_values(self.simulation)
        labels = self.observation_labels()
        assert len(values) == len(labels), f"Observation value/label mismatch: {len(values)} != {len(labels)}"
        return np.array(values, dtype=np.float32)

    def observation_labels(self) -> list[str]:
        return build_observation_labels()

    def global_mechanic_observation_labels(self) -> list[str]:
        return [label for label in self.observation_labels() if label.startswith("global.")]

    def observation_channel_mapping(self) -> dict[str, str]:
        return build_observation_channel_mapping(self.simulation)

    def observation_slot_mapping(self) -> dict[str, str | None]:
        return build_observation_slot_mapping(self.simulation)

    def observation_metadata(self) -> dict:
        metadata = observation_metadata(self)
        metadata["curriculum_reset_mode"] = self.curriculum_reset_mode_arg
        metadata["last_curriculum_reset_mode"] = self.last_curriculum_reset_mode
        return metadata

    @staticmethod
    def _normalize_curriculum_reset_mode(mode: str | None) -> str:
        normalized = "none" if mode is None else str(mode).strip().lower()
        if normalized == "":
            normalized = "none"
        if normalized not in CURRICULUM_RESET_MODES:
            choices = ", ".join(sorted(CURRICULUM_RESET_MODES))
            raise ValueError(f"Unsupported curriculum_reset_mode {mode!r}. Expected one of: {choices}")
        return normalized

    def _select_curriculum_reset_mode(self) -> str:
        if self.curriculum_reset_mode_arg != "mixed_lynae_curriculum":
            return self.curriculum_reset_mode_arg
        index = int(self.np_random.integers(0, len(MIXED_LYNAE_CURRICULUM_CHOICES)))
        return MIXED_LYNAE_CURRICULUM_CHOICES[index]

    def _apply_curriculum_reset(self, mode: str) -> None:
        if mode == "none":
            return
        if mode not in MIXED_LYNAE_CURRICULUM_CHOICES:
            raise ValueError(f"Unsupported applied curriculum reset mode: {mode}")
        self._set_active_character("aemeath")
        self._set_concerto_ready("aemeath", 100.0)
        if mode == "aemeath_ready_for_lynae":
            return
        self._execute_curriculum_action("swap_to_lynae", mode)
        if mode == "lynae_after_intro":
            return
        self._execute_curriculum_action("lynae_resonance_skill", mode)
        self._execute_curriculum_action("lynae_spark_collision", mode)

    def _set_active_character(self, character_id: str) -> None:
        if character_id not in self.simulation.selected_party_character_ids:
            raise RuntimeError(f"Curriculum reset requires party member {character_id!r}.")
        self.simulation.state.active_character_id = character_id

    def _set_concerto_ready(self, character_id: str, amount: float = 100.0) -> None:
        character_state = self.simulation.state.character_states.setdefault(character_id, {})
        cap = float(character_state.get("concerto_energy_cap", 100.0) or 100.0)
        energy = min(float(amount), cap)
        character_state["concerto_energy"] = energy
        character_state["concerto_energy_cap"] = cap
        character_state["concerto_ready"] = energy >= cap
        self.simulation.state.concerto_energy[character_id] = energy

    def _execute_curriculum_action(self, action_id: str, mode: str) -> None:
        if action_id not in self.simulation.actions:
            raise RuntimeError(f"Curriculum reset mode {mode!r} requires missing action {action_id!r}.")
        if not self.simulation.execute_action(action_id):
            active = self.simulation.state.active_character_id
            valid_actions = self.simulation.valid_action_ids()
            raise RuntimeError(
                f"Curriculum reset mode {mode!r} could not execute {action_id!r}; "
                f"active={active!r}, valid_actions={valid_actions!r}."
            )

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

    def get_selected_party_character_ids(self) -> list[str]:
        return list(self.simulation.selected_party_character_ids)

    def get_policy_action_ids(self) -> list[str]:
        return list(self.action_ids)

    def get_initial_active_character(self) -> str:
        return self.simulation.initial_active_character

    def get_party_id(self) -> str | None:
        preset_config = self.simulation.party_preset_config or {}
        return preset_config.get("party_id") or self.party_id_arg

    def get_active_build_profiles(self) -> dict[str, str]:
        return dict(self.simulation.active_build_profiles)

    def get_effective_build_stats_summary(self) -> dict:
        return dict(self.simulation.effective_build_stats_summary)

    def get_curriculum_reset_mode(self) -> str:
        return self.curriculum_reset_mode_arg

    def get_last_curriculum_reset_mode(self) -> str:
        return self.last_curriculum_reset_mode
