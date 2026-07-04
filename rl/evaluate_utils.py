from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from env.wuwa_env import WuwaDpsEnv


def run_masked_episode(
    model: Any,
    data_dir: Path | str = "data",
    deterministic: bool = True,
    selected_character_ids: list[str] | str | None = None,
    selected_party_character_ids: list[str] | str | None = None,
    party: list[str] | str | None = None,
    initial_active_character: str | None = None,
    transition_config: dict | None = None,
    build_profile_overrides: dict[str, str] | None = None,
) -> tuple[WuwaDpsEnv, list[str], list[str]]:
    env = WuwaDpsEnv(
        data_dir,
        selected_character_ids=selected_character_ids,
        selected_party_character_ids=selected_party_character_ids,
        party=party,
        initial_active_character=initial_active_character,
        transition_config=transition_config,
        build_profile_overrides=build_profile_overrides,
    )
    observation, _ = env.reset()
    action_sequence: list[str] = []
    resolved_action_sequence: list[str] = []

    while env.simulation.state.combat_time < env.simulation.combat_duration:
        mask = env.action_masks()
        action, _ = model.predict(observation, deterministic=deterministic, action_masks=mask)
        action_index = int(action)
        observation, _reward, terminated, truncated, info = env.step(action_index)
        action_sequence.append(str(info["action_id"]))
        resolved_action_sequence.append(str(info["resolved_action_id"]))
        if terminated or truncated:
            break

    return env, action_sequence, resolved_action_sequence


def action_count_breakdown(action_sequence: list[str]) -> dict[str, int]:
    return dict(Counter(action_sequence))
