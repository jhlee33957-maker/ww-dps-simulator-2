from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.wuwa_env import WuwaDpsEnv


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
FOCUS_ACTION_IDS = (
    "swap_to_lynae",
    "lynae_resonance_skill",
    "lynae_spark_collision",
    "lynae_polychrome_leap",
    "lynae_visual_impact",
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect Aemeath/Mornye/Lynae action masks and PPO probabilities.")
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--write-json", type=Path, default=None)
    parser.add_argument("--party", type=str, default=PARTY_ID)
    return parser


def set_full_concerto(env: WuwaDpsEnv, character_id: str) -> None:
    state = env.simulation.state.character_states[character_id]
    cap = float(state.get("concerto_energy_cap", 100.0) or 100.0)
    state["concerto_energy"] = cap
    state["concerto_ready"] = True
    env.simulation.state.concerto_energy[character_id] = cap


def run_policy_probability_diagnostic(
    model_path: Path | None = None,
    party: str = PARTY_ID,
    write_json: Path | None = None,
) -> dict[str, Any]:
    env = WuwaDpsEnv(data_dir=ROOT / "data", party=party)
    observation, _ = env.reset(seed=0)
    model, model_status, model_error = _load_model(model_path, env)

    states: list[dict[str, Any]] = []

    states.append(_state_report("A_initial_mornye", env, observation, model))

    _execute_or_record(env, "swap_to_aemeath")
    observation = env._get_observation()
    states.append(_state_report("B_after_swap_to_aemeath", env, observation, model))

    set_full_concerto(env, "aemeath")
    observation = env._get_observation()
    states.append(_state_report("C_aemeath_concerto_forced_100", env, observation, model))

    _execute_or_record(env, "swap_to_lynae")
    observation = env._get_observation()
    states.append(_state_report("D_after_swap_to_lynae_intro", env, observation, model))

    _execute_or_record(env, "lynae_resonance_skill")
    observation = env._get_observation()
    states.append(_state_report("E_after_lynae_resonance_skill", env, observation, model))

    _execute_or_record(env, "lynae_spark_collision")
    observation = env._get_observation()
    states.append(_state_report("F_after_lynae_spark_collision", env, observation, model))

    report = {
        "party_id": party,
        "diagnostic": "aemeath_mornye_lynae_policy_probability",
        "model_path": str(model_path) if model_path else None,
        "model_probability_status": model_status,
        "model_probability_error": model_error,
        "note": "Diagnostic only: no PPO quality pass/fail threshold is applied.",
        "states": states,
    }
    if write_json is not None:
        write_json.parent.mkdir(parents=True, exist_ok=True)
        write_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _load_model(model_path: Path | None, env: WuwaDpsEnv) -> tuple[Any | None, str, str | None]:
    if model_path is None:
        return None, "not_requested", None
    if not model_path.exists():
        return None, "model_path_missing", f"No model found at {model_path}"
    try:
        from sb3_contrib import MaskablePPO
    except ModuleNotFoundError as exc:
        return None, "dependency_missing", str(exc)
    try:
        model = MaskablePPO.load(model_path, env=env)
    except Exception as exc:  # pragma: no cover - model-file compatibility is user/local-state dependent.
        return None, "model_load_failed", str(exc)
    return model, "loaded", None


def _execute_or_record(env: WuwaDpsEnv, action_id: str) -> None:
    if not env.simulation.execute_action(action_id):
        raise RuntimeError(
            f"Could not execute diagnostic setup action {action_id!r}; "
            f"active={env.simulation.state.active_character_id!r}, valid={env.simulation.valid_action_ids()!r}"
        )


def _state_report(name: str, env: WuwaDpsEnv, observation: np.ndarray, model: Any | None) -> dict[str, Any]:
    action_ids = env.get_policy_action_ids()
    mask = np.asarray(env.action_masks(), dtype=bool)
    valid_action_ids = [action_id for action_id, valid in zip(action_ids, mask, strict=True) if valid]
    probabilities, probability_error = _masked_probabilities(model, observation, mask) if model is not None else (None, None)
    ranked_ids = _ranked_valid_action_ids(action_ids, mask, probabilities)
    return {
        "state": name,
        "active_character": env.simulation.state.active_character_id,
        "valid_action_ids": valid_action_ids,
        "valid_action_count": len(valid_action_ids),
        "top_10_valid_action_probabilities": _top_valid_action_probabilities(action_ids, mask, probabilities),
        "focus_actions": {
            action_id: _focus_action_report(action_id, action_ids, mask, probabilities, ranked_ids)
            for action_id in FOCUS_ACTION_IDS
        },
        "model_probability_error": probability_error,
    }


def _masked_probabilities(
    model: Any,
    observation: np.ndarray,
    mask: np.ndarray,
) -> tuple[np.ndarray | None, str | None]:
    try:
        import torch

        with torch.no_grad():
            obs_tensor, _ = model.policy.obs_to_tensor(observation)
            distribution = model.policy.get_distribution(obs_tensor, action_masks=mask.reshape(1, -1))
            probs = distribution.distribution.probs.detach().cpu().numpy()[0]
    except Exception as exc:  # pragma: no cover - depends on installed sb3-contrib internals.
        return None, str(exc)
    masked = np.asarray(probs, dtype=float)
    masked[~mask] = 0.0
    total = float(masked.sum())
    if total > 0.0:
        masked = masked / total
    return masked, None


def _ranked_valid_action_ids(
    action_ids: list[str],
    mask: np.ndarray,
    probabilities: np.ndarray | None,
) -> list[str]:
    if probabilities is None:
        return []
    valid_indices = np.flatnonzero(mask)
    ordered = sorted(valid_indices, key=lambda index: float(probabilities[index]), reverse=True)
    return [action_ids[index] for index in ordered]


def _top_valid_action_probabilities(
    action_ids: list[str],
    mask: np.ndarray,
    probabilities: np.ndarray | None,
) -> list[dict[str, Any]]:
    if probabilities is None:
        return []
    valid_indices = np.flatnonzero(mask)
    ordered = sorted(valid_indices, key=lambda index: float(probabilities[index]), reverse=True)[:10]
    return [
        {"action_id": action_ids[index], "probability": float(probabilities[index])}
        for index in ordered
    ]


def _focus_action_report(
    action_id: str,
    action_ids: list[str],
    mask: np.ndarray,
    probabilities: np.ndarray | None,
    ranked_ids: list[str],
) -> dict[str, Any]:
    if action_id not in action_ids:
        return {"present": False, "valid": False, "probability": None, "rank": None}
    index = action_ids.index(action_id)
    probability = float(probabilities[index]) if probabilities is not None else None
    rank = ranked_ids.index(action_id) + 1 if action_id in ranked_ids else None
    return {
        "present": True,
        "valid": bool(mask[index]),
        "probability": probability,
        "rank": rank,
    }


def main() -> None:
    args = build_arg_parser().parse_args()
    report = run_policy_probability_diagnostic(
        model_path=args.model_path,
        party=args.party,
        write_json=args.write_json,
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
