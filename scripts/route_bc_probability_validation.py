from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.wuwa_env import WuwaDpsEnv
from scripts.aemeath_mornye_lynae_policy_probability_diagnostic import _masked_probabilities


FOCUS_ROUTE_ACTIONS = {
    "normal_start_to_lynae_intro_entry": "swap_to_lynae",
    "aemeath_concerto_to_lynae_intro_exact": "swap_to_lynae",
    "lynae_skill_to_spark_bridge": "lynae_spark_collision",
    "lynae_spark_to_visual_bridge": "lynae_polychrome_leap",
}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate model probabilities on route demonstration samples.")
    parser.add_argument("--demo-path", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--party", type=str, default="aemeath_mornye_lynae_enabled_test_party")
    parser.add_argument("--write-json", type=Path, default=None)
    return parser


def run_validation(
    *,
    demo_path: Path,
    model_path: Path | None = None,
    party: str = "aemeath_mornye_lynae_enabled_test_party",
    write_json: Path | None = None,
) -> dict[str, Any]:
    demo = _load_demo(demo_path)
    env = WuwaDpsEnv(ROOT / "data", party=party)
    model, model_status, model_error = _load_model(model_path, env)
    report: dict[str, Any] = {
        "diagnostic": "route_bc_probability_validation",
        "demo_path": str(demo_path),
        "model_path": str(model_path) if model_path else None,
        "party": party,
        "model_status": model_status,
        "model_error": model_error,
        "route_set_id": demo["metadata"].get("route_set_id"),
        "sample_count": int(len(demo["action_indices"])),
        "route_sample_counts": dict(Counter(map(str, demo["route_ids"]))),
        "action_counts": dict(Counter(map(str, demo["action_ids"]))),
        "character_counts": dict(Counter(map(str, demo["active_characters"]))),
    }
    if model is None:
        report["status"] = "model_not_loaded"
    else:
        report.update(_probability_report(model, demo, env))
        report["status"] = "ok"
    if write_json is not None:
        write_json.parent.mkdir(parents=True, exist_ok=True)
        write_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _load_demo(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Demo file not found: {path}")
    with np.load(path, allow_pickle=False) as data:
        active_characters = (
            np.asarray(data["active_characters"], dtype=str)
            if "active_characters" in data
            else np.asarray([], dtype=str)
        )
        return {
            "observations": np.asarray(data["observations"], dtype=np.float32),
            "action_indices": np.asarray(data["action_indices"], dtype=np.int64),
            "action_ids": np.asarray(data["action_ids"], dtype=str),
            "action_masks": np.asarray(data["action_masks"], dtype=bool),
            "route_ids": np.asarray(data["route_ids"], dtype=str),
            "active_characters": active_characters,
            "metadata": json.loads(str(data["metadata_json"])),
        }


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
        return MaskablePPO.load(model_path, env=env), "loaded", None
    except Exception as exc:  # pragma: no cover - local model compatibility dependent.
        return None, "model_load_failed", str(exc)


def _probability_report(model: Any, demo: dict[str, Any], env: WuwaDpsEnv) -> dict[str, Any]:
    probabilities: list[float] = []
    by_route: dict[str, list[float]] = {}
    by_action: dict[str, list[float]] = {}
    focus: dict[str, list[float]] = {}
    for observation, action_index, mask, route_id, action_id in zip(
        demo["observations"],
        demo["action_indices"],
        demo["action_masks"],
        demo["route_ids"],
        demo["action_ids"],
        strict=True,
    ):
        masked_probs, error = _masked_probabilities(model, observation, mask)
        if masked_probs is None:
            return {"status": "probability_failed", "probability_error": error}
        probability = float(masked_probs[int(action_index)])
        probabilities.append(probability)
        by_route.setdefault(str(route_id), []).append(probability)
        by_action.setdefault(str(action_id), []).append(probability)
        if FOCUS_ROUTE_ACTIONS.get(str(route_id)) == str(action_id):
            focus.setdefault(f"{route_id}:{action_id}", []).append(probability)

    initial_observation, _ = env.reset(seed=0)
    initial_mask = np.asarray(env.action_masks(), dtype=bool)
    initial_probs, initial_error = _masked_probabilities(model, initial_observation, initial_mask)
    action_ids = env.get_policy_action_ids()
    swap_probability = None
    if initial_probs is not None and "swap_to_lynae" in action_ids:
        swap_probability = float(initial_probs[action_ids.index("swap_to_lynae")])

    return {
        "mean_demonstrated_action_probability": _mean(probabilities),
        "route_wise_mean_probability": {key: _mean(values) for key, values in sorted(by_route.items())},
        "action_wise_mean_probability": {key: _mean(values) for key, values in sorted(by_action.items())},
        "focus_probabilities": {key: _summary(values) for key, values in sorted(focus.items())},
        "overgeneralization_probe": {
            "state": "initial_mornye_normal_reset",
            "action_id": "swap_to_lynae",
            "probability": swap_probability,
            "probability_error": initial_error,
            "note": "Diagnostic only; initial Mornye swap_to_lynae should not be forced high unless the route demonstrates that exact state.",
        },
    }


def _mean(values: list[float]) -> float | None:
    return float(np.mean(values)) if values else None


def _summary(values: list[float]) -> dict[str, Any]:
    return {
        "count": len(values),
        "mean": _mean(values),
        "min": float(np.min(values)) if values else None,
        "max": float(np.max(values)) if values else None,
    }


def main() -> None:
    args = build_arg_parser().parse_args()
    report = run_validation(
        demo_path=args.demo_path,
        model_path=args.model_path,
        party=args.party,
        write_json=args.write_json,
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
