from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.wuwa_env import WuwaDpsEnv


DEFAULT_CONFIG_PATH = ROOT / "data" / "rl_route_demonstrations.json"
DEFAULT_ROUTE_SET = "aemeath_mornye_lynae_route_warm_start"
DEFAULT_OUTPUT = ROOT / "data" / "generated" / "route_demonstrations_aemeath_mornye_lynae.npz"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate generic route demonstration samples for BC warm-starts.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--route-set", type=str, default=DEFAULT_ROUTE_SET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--repeat", type=int, default=64)
    return parser


def load_route_set(config_path: Path, route_set_id: str) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    for route_set in config.get("route_sets", []):
        if route_set.get("route_set_id") == route_set_id:
            return route_set
    raise ValueError(f"Route set {route_set_id!r} not found in {config_path}")


def generate_route_demonstrations(
    *,
    route_set_id: str = DEFAULT_ROUTE_SET,
    output_path: Path = DEFAULT_OUTPUT,
    repeat: int = 64,
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    route_set = load_route_set(config_path, route_set_id)
    party_id = route_set["party_id"]
    observations: list[np.ndarray] = []
    action_indices: list[int] = []
    action_ids: list[str] = []
    action_masks: list[np.ndarray] = []
    route_ids: list[str] = []
    active_characters: list[str] = []
    resolved_action_ids: list[str] = []
    rewards: list[float] = []
    damages: list[float] = []
    combat_time_costs: list[float] = []
    route_summaries: dict[str, dict[str, Any]] = {}
    action_distribution: Counter[str] = Counter()
    resolved_distribution: Counter[str] = Counter()
    character_distribution: Counter[str] = Counter()

    reference_shape: tuple[int, ...] | None = None
    reference_action_ids: list[str] | None = None

    for route in route_set.get("routes", []):
        route_id = route["route_id"]
        route_repeat = max(1, int(repeat * int(route.get("repeat_weight", 1))))
        route_damage = 0.0
        route_time = 0.0
        route_samples = 0
        for iteration in range(route_repeat):
            env = WuwaDpsEnv(data_dir=ROOT / "data", party=route.get("party_id") or party_id)
            env.reset(seed=iteration)
            _apply_setup_steps(env, route.get("setup_steps", []), route_id)
            if reference_shape is None:
                reference_shape = tuple(env.observation_space.shape)
                reference_action_ids = env.get_policy_action_ids()
            elif tuple(env.observation_space.shape) != reference_shape:
                raise RuntimeError(
                    f"Observation shape changed in route {route_id}: "
                    f"{env.observation_space.shape} != {reference_shape}"
                )
            if env.get_policy_action_ids() != reference_action_ids:
                raise RuntimeError(f"Policy action space changed while generating route {route_id}.")

            for entry in route.get("demonstration_actions", []):
                for sample in _record_and_execute_demonstration_entry(env, entry, route_id):
                    observations.append(sample["observation"])
                    action_indices.append(sample["action_index"])
                    action_ids.append(sample["action_id"])
                    action_masks.append(sample["action_mask"])
                    route_ids.append(route_id)
                    active_characters.append(sample["active_character"])
                    resolved_action_ids.append(sample["resolved_action_id"])
                    rewards.append(sample["reward"])
                    damages.append(sample["damage"])
                    combat_time_costs.append(sample["combat_time_cost"])
                    route_damage += sample["damage"]
                    route_time += sample["combat_time_cost"]
                    route_samples += 1
                    action_distribution[sample["action_id"]] += 1
                    resolved_distribution[sample["resolved_action_id"]] += 1
                    character_distribution[sample["active_character"]] += 1
        route_summaries[route_id] = {
            "samples": route_samples,
            "total_damage": route_damage,
            "combat_time_cost": route_time,
            "repeat_weight": int(route.get("repeat_weight", 1)),
            "demonstration_actions": list(route.get("demonstration_actions", [])),
        }

    baseline_route_ids = {
        route["route_id"]
        for route in route_set.get("routes", [])
        if "baseline" in str(route.get("route_id", "")) or "aemeath_concerto_ready" in str(route.get("route_id", ""))
    }
    non_lynae_baseline_samples = sum(
        1 for route_id in route_ids if route_id in baseline_route_ids
    )
    lynae_route_samples = len(route_ids) - non_lynae_baseline_samples
    warning_messages: list[str] = []
    if len(route_ids) > 0 and lynae_route_samples == len(route_ids):
        warning_messages.append("all generated samples are Lynae-route samples")
    if len(route_ids) > 0 and non_lynae_baseline_samples == len(route_ids):
        warning_messages.append("all generated samples are non-Lynae baseline samples")

    metadata = {
        "schema_version": "2026-07-09-route-demonstration-npz-v2",
        "route_set_id": route_set_id,
        "party_id": party_id,
        "repeat": repeat,
        "total_samples": len(action_indices),
        "observation_shape": list(reference_shape or []),
        "policy_action_ids": reference_action_ids or [],
        "samples_per_route": {key: value["samples"] for key, value in route_summaries.items()},
        "action_distribution": dict(action_distribution),
        "resolved_action_distribution": dict(resolved_distribution),
        "character_distribution": dict(character_distribution),
        "non_lynae_baseline_samples": non_lynae_baseline_samples,
        "lynae_route_samples": lynae_route_samples,
        "non_lynae_baseline_sample_percentage": _percentage(non_lynae_baseline_samples, len(route_ids)),
        "lynae_route_sample_percentage": _percentage(lynae_route_samples, len(route_ids)),
        "warnings": warning_messages,
        "route_summaries": route_summaries,
        "training_only": bool(route_set.get("training_only", True)),
        "reward_shaping": bool(route_set.get("reward_shaping", False)),
        "character_usage_bonus": bool(route_set.get("character_usage_bonus", False)),
        "no_character_specific_usage_reward_bonus": True,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        observations=np.asarray(observations, dtype=np.float32),
        action_indices=np.asarray(action_indices, dtype=np.int64),
        action_ids=np.asarray(action_ids, dtype=str),
        action_masks=np.asarray(action_masks, dtype=bool),
        route_ids=np.asarray(route_ids, dtype=str),
        active_characters=np.asarray(active_characters, dtype=str),
        resolved_action_ids=np.asarray(resolved_action_ids, dtype=str),
        rewards=np.asarray(rewards, dtype=np.float32),
        damages=np.asarray(damages, dtype=np.float32),
        combat_time_costs=np.asarray(combat_time_costs, dtype=np.float32),
        metadata_json=np.asarray(json.dumps(metadata, ensure_ascii=False), dtype=str),
    )
    return metadata


def _apply_setup_steps(env: WuwaDpsEnv, setup_steps: list[dict[str, Any]], route_id: str) -> None:
    for step in setup_steps:
        op = step.get("op")
        if op == "reset":
            continue
        if op == "set_active_character":
            env.simulation.state.active_character_id = str(step["character_id"])
            continue
        if op == "set_concerto":
            character_id = str(step["character_id"])
            energy = float(step.get("energy", 100.0))
            state = env.simulation.state.character_states[character_id]
            cap = float(state.get("concerto_energy_cap", 100.0) or 100.0)
            state["concerto_energy"] = min(energy, cap)
            state["concerto_ready"] = bool(step.get("ready", state["concerto_energy"] >= cap))
            env.simulation.state.concerto_energy[character_id] = float(state["concerto_energy"])
            continue
        if op == "set_action_unavailable":
            character_id = str(step["character_id"])
            action_id = str(step["action_id"])
            env.simulation.state.resonance_energy[character_id] = 0.0
            env.simulation.state.cooldowns[action_id] = max(
                float(env.simulation.state.cooldowns.get(action_id, 0.0) or 0.0),
                25.0,
            )
            continue
        if op == "execute_action":
            action_id = str(step["action_id"])
            if not env.simulation.execute_action(action_id):
                raise RuntimeError(_invalid_action_message(env, route_id, action_id, setup=True))
            continue
        if op == "auto_build_concerto":
            _auto_build_concerto(env, step, route_id, record=False)
            continue
        raise ValueError(f"Unsupported setup op {op!r} in route {route_id!r}.")


def _record_and_execute_demonstration_entry(env: WuwaDpsEnv, entry: Any, route_id: str) -> list[dict[str, Any]]:
    if isinstance(entry, str):
        return [_record_and_execute_action(env, entry, route_id)]
    if not isinstance(entry, dict):
        raise ValueError(f"Unsupported demonstration entry {entry!r} in route {route_id!r}.")
    op = entry.get("op")
    if op == "auto_build_concerto":
        return _auto_build_concerto(env, entry, route_id, record=True)
    if op == "action":
        return [_record_and_execute_action(env, str(entry["action_id"]), route_id)]
    raise ValueError(f"Unsupported demonstration op {op!r} in route {route_id!r}.")


def _auto_build_concerto(
    env: WuwaDpsEnv,
    step: dict[str, Any],
    route_id: str,
    *,
    record: bool,
) -> list[dict[str, Any]]:
    target_character = str(step["target_character"])
    target_concerto = float(step.get("target_concerto", 100.0))
    max_steps = int(step.get("max_steps", 60))
    action_priority = [str(action_id) for action_id in step.get("action_priority", [])]
    if not action_priority:
        raise ValueError(f"auto_build_concerto in route {route_id!r} requires action_priority.")

    samples: list[dict[str, Any]] = []
    for _step_index in range(max(1, max_steps)):
        if _concerto_target_reached(env, target_character, target_concerto):
            return samples
        valid_actions = set(env.simulation.valid_action_ids())
        action_id = next((candidate for candidate in action_priority if candidate in valid_actions), None)
        if action_id is None:
            raise RuntimeError(
                json.dumps(
                    {
                        "error": "auto_build_concerto found no valid priority action",
                        "route_id": route_id,
                        "target_character": target_character,
                        "target_concerto": target_concerto,
                        "valid_actions": sorted(valid_actions),
                        "action_priority": action_priority,
                    },
                    indent=2,
                )
            )
        if record:
            samples.append(_record_and_execute_action(env, action_id, route_id))
        elif not env.simulation.execute_action(action_id):
            raise RuntimeError(_invalid_action_message(env, route_id, action_id, setup=True))
    if _concerto_target_reached(env, target_character, target_concerto):
        return samples
    state = env.simulation.state.character_states.get(target_character, {})
    raise RuntimeError(
        json.dumps(
            {
                "error": "auto_build_concerto target not reached",
                "route_id": route_id,
                "target_character": target_character,
                "target_concerto": target_concerto,
                "max_steps": max_steps,
                "active_character": env.simulation.state.active_character_id,
                "actual_concerto": state.get("concerto_energy"),
                "actual_concerto_ready": state.get("concerto_ready"),
                "valid_actions": env.simulation.valid_action_ids(),
            },
            indent=2,
            default=str,
        )
    )


def _concerto_target_reached(env: WuwaDpsEnv, target_character: str, target_concerto: float) -> bool:
    state = env.simulation.state.character_states.get(target_character, {})
    return (
        env.simulation.state.active_character_id == target_character
        and float(state.get("concerto_energy", 0.0) or 0.0) >= target_concerto
    )


def _record_and_execute_action(env: WuwaDpsEnv, action_id: str, route_id: str) -> dict[str, Any]:
    policy_action_ids = env.get_policy_action_ids()
    if action_id not in policy_action_ids:
        raise RuntimeError(f"Route {route_id} action {action_id!r} is not in the policy action space.")
    action_index = policy_action_ids.index(action_id)
    observation = env._get_observation()
    mask = env.action_masks()
    if len(observation) != env.observation_space.shape[0]:
        raise RuntimeError(f"Observation shape mismatch in route {route_id}.")
    if not bool(mask[action_index]):
        raise RuntimeError(_invalid_action_message(env, route_id, action_id, setup=False))
    active_character = env.simulation.state.active_character_id
    combat_time_before = float(env.simulation.state.combat_time)
    _next_obs, reward, terminated, truncated, info = env.step(action_index)
    if not info.get("valid_action", False):
        raise RuntimeError(_invalid_action_message(env, route_id, action_id, setup=False))
    return {
        "observation": observation,
        "action_index": action_index,
        "action_id": action_id,
        "action_mask": np.asarray(mask, dtype=bool),
        "active_character": active_character,
        "resolved_action_id": str(info["resolved_action_id"]),
        "reward": float(reward),
        "damage": float(info["damage_this_action"]),
        "combat_time_cost": float(info["combat_time"]) - combat_time_before,
        "terminated": bool(terminated),
        "truncated": bool(truncated),
    }


def _invalid_action_message(env: WuwaDpsEnv, route_id: str, action_id: str, *, setup: bool) -> str:
    lynae_state = env.simulation.state.character_mechanics_state.get("lynae", {})
    return json.dumps(
        {
            "error": "invalid route demonstration action",
            "route_id": route_id,
            "action_id": action_id,
            "phase": "setup" if setup else "demonstration",
            "active_character": env.simulation.state.active_character_id,
            "valid_policy_actions": env.simulation.valid_action_ids(),
            "lynae_state": lynae_state,
            "cooldowns": env.simulation.state.cooldowns,
            "resonance_energy": env.simulation.state.resonance_energy,
            "concerto_energy": env.simulation.state.concerto_energy,
        },
        indent=2,
        default=str,
    )


def _percentage(count: int, total: int) -> float:
    return 0.0 if total <= 0 else round((float(count) / float(total)) * 100.0, 4)


def main() -> None:
    args = build_arg_parser().parse_args()
    metadata = generate_route_demonstrations(
        route_set_id=args.route_set,
        output_path=args.output,
        repeat=args.repeat,
        config_path=args.config,
    )
    print(json.dumps(metadata, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
