from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env.wuwa_env import WuwaDpsEnv
from rl.demo_contract import DEFAULT_DEMO_PATH, json_safe, load_demo_npz


def compute_small_overfit_metrics(
    demo_path: Path = DEFAULT_DEMO_PATH,
    *,
    epochs: int = 300,
    seed: int = 11,
    device: str = "cpu",
) -> dict[str, float | int | bool | str]:
    try:
        import torch
        from sb3_contrib import MaskablePPO
    except ModuleNotFoundError as exc:
        return {"status": "dependency_missing", "message": str(exc), "temporary_artifacts_only": True}

    if device != "cpu":
        raise ValueError("manual_120s_bc_small_overfit_smoke_test is intentionally CPU-only")
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass

    started = time.perf_counter()
    demo = load_demo_npz(demo_path)
    env = WuwaDpsEnv(
        ROOT / "data",
        party="aemeath_mornye_lynae_enabled_test_party",
        initial_active_character="aemeath",
        curriculum_reset_mode="none",
    )
    env.reset(seed=seed)
    with tempfile.TemporaryDirectory() as temp_dir:
        model = MaskablePPO(
            "MlpPolicy",
            env,
            learning_rate=0.003,
            gamma=0.999,
            n_steps=512,
            batch_size=64,
            ent_coef=0.0,
            verbose=0,
            seed=seed,
            device=device,
        )
        observations = torch.as_tensor(demo["observations"], dtype=torch.float32, device=model.device)
        action_indices = torch.as_tensor(demo["action_indices"], dtype=torch.long, device=model.device)
        action_masks = torch.as_tensor(demo["action_masks"], dtype=torch.bool, device=model.device)
        optimizer = model.policy.optimizer
        initial_metrics = _metrics(model, observations, action_indices, action_masks)
        model.policy.train()
        for _epoch in range(epochs):
            distribution = model.policy.get_distribution(observations, action_masks=action_masks)
            loss = -distribution.log_prob(action_indices).mean()
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        final_metrics = _metrics(model, observations, action_indices, action_masks)
        temp_model_path = Path(temp_dir) / "manual_120s_bc_small_overfit.zip"
        model.save(temp_model_path)
        assert temp_model_path.exists()

    nll_decrease = float(initial_metrics["masked_nll"] - final_metrics["masked_nll"])
    return {
        "status": "ok",
        "seed": seed,
        "epochs": epochs,
        "device": device,
        "initial_masked_nll": initial_metrics["masked_nll"],
        "final_masked_nll": final_metrics["masked_nll"],
        "nll_decrease": nll_decrease,
        "initial_top1_accuracy": initial_metrics["top1_accuracy"],
        "final_top1_accuracy": final_metrics["top1_accuracy"],
        "invalid_top1_count": final_metrics["invalid_top1_count"],
        "temporary_artifacts_only": True,
        "canonical_artifacts_mutated": False,
        "runtime_seconds": round(time.perf_counter() - started, 6),
    }


def main() -> None:
    metrics = compute_small_overfit_metrics()
    if metrics.get("status") == "dependency_missing":
        print(f"manual_120s_bc_small_overfit_smoke_test dependency-missing: {metrics['message']}")
        return
    assert metrics["nll_decrease"] > 0.1, json.dumps(metrics, indent=2)
    assert metrics["final_masked_nll"] < metrics["initial_masked_nll"], json.dumps(metrics, indent=2)
    assert metrics["final_top1_accuracy"] >= 0.95, json.dumps(metrics, indent=2)
    assert metrics["invalid_top1_count"] == 0, json.dumps(metrics, indent=2)
    print(json.dumps(json_safe(metrics), indent=2, ensure_ascii=False))
    print("manual_120s_bc_small_overfit_smoke_test ok")


def _metrics(model, observations, action_indices, action_masks) -> dict[str, float | int]:
    import torch

    model.policy.eval()
    with torch.no_grad():
        distribution = model.policy.get_distribution(observations, action_masks=action_masks)
        nll = float((-distribution.log_prob(action_indices).mean()).detach().cpu().item())
        categorical = distribution.distribution
        if hasattr(categorical, "probs"):
            scores = categorical.probs
        else:
            scores = categorical.logits
        predictions = torch.argmax(scores, dim=1)
        correct = (predictions == action_indices).float().mean()
        invalid = (~action_masks[torch.arange(action_masks.shape[0], device=action_masks.device), predictions]).sum()
    return {
        "masked_nll": nll,
        "top1_accuracy": float(correct.detach().cpu().item()),
        "invalid_top1_count": int(invalid.detach().cpu().item()),
    }


if __name__ == "__main__":
    main()
