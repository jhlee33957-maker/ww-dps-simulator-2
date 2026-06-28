from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from env.wuwa_env import WuwaDpsEnv


def run_masked_episode(model: Any, data_dir: Path | str = "data", deterministic: bool = True) -> tuple[WuwaDpsEnv, list[str]]:
    env = WuwaDpsEnv(data_dir)
    observation, _ = env.reset()
    action_sequence: list[str] = []

    while env.simulation.state.current_time < env.simulation.combat_duration:
        mask = env.action_masks()
        action, _ = model.predict(observation, deterministic=deterministic, action_masks=mask)
        action_index = int(action)
        observation, _reward, terminated, truncated, info = env.step(action_index)
        action_sequence.append(str(info["action_id"]))
        if terminated or truncated:
            break

    return env, action_sequence


def action_count_breakdown(action_sequence: list[str]) -> dict[str, int]:
    return dict(Counter(action_sequence))
