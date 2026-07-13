from __future__ import annotations

import json
import tempfile
from pathlib import Path
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    from rl.guarded_ppo import (
        DEFAULT_PLAN_PATH,
        EXPECTED_ACTION_DATA_HASH,
        EXPECTED_MAX_POLICY_ACTION_SLOTS,
        EXPECTED_OBSERVATION_SHAPE,
        EXPECTED_OBSERVATION_VERSION,
        EXPECTED_PARTY_CONFIG_HASH,
        EXPECTED_POLICY_ACTION_COUNT,
        REQUIRED_CHECKPOINT_SIDECAR_KEYS,
        canonicalize_guarded_path,
        effective_seed,
        expected_policy_action_ids,
        load_plan,
        sha256_file,
        validate_checkpoint_sidecar,
    )

    plan = load_plan(DEFAULT_PLAN_PATH)
    branch = next(item for item in plan["branches"] if item["branch_id"] == "scratch_control_seed_137")
    with tempfile.TemporaryDirectory(prefix="guarded-sidecar-strict-") as temp_dir:
        root = Path(temp_dir)
        model = root / "models" / "guarded_ppo_v109" / branch["branch_id"] / "step_000010000.zip"
        model.parent.mkdir(parents=True)
        _write_synthetic_model(model, num_timesteps=10240, seed=effective_seed(branch, 1), n_steps=512)
        sidecar = Path(str(model) + ".ppo_metadata.json")
        metadata = _valid_metadata(
            model=model,
            branch=branch,
            plan_path=DEFAULT_PLAN_PATH,
            model_sha=sha256_file(model),
            effective_seed_value=effective_seed(branch, 1),
            policy_ids=expected_policy_action_ids(),
            constants={
                "shape": EXPECTED_OBSERVATION_SHAPE,
                "version": EXPECTED_OBSERVATION_VERSION,
                "policy_count": EXPECTED_POLICY_ACTION_COUNT,
                "max_slots": EXPECTED_MAX_POLICY_ACTION_SLOTS,
                "action_hash": EXPECTED_ACTION_DATA_HASH,
                "party_hash": EXPECTED_PARTY_CONFIG_HASH,
            },
        )
        _write(sidecar, metadata)
        validate_checkpoint_sidecar(branch=branch, chunk_index=1, plan_path=DEFAULT_PLAN_PATH, model_path=model, metadata_path=sidecar, parent_model_path=None)

        incomplete = {
            "model_path": metadata["model_path"],
            "model_sha256": metadata["model_sha256"],
            "branch_id": metadata["branch_id"],
        }
        _assert_fails(incomplete, sidecar, branch, model, "incomplete three-field sidecar")

        for key in REQUIRED_CHECKPOINT_SIDECAR_KEYS:
            bad = dict(metadata)
            bad.pop(key)
            _assert_fails(bad, sidecar, branch, model, f"missing {key}")

        mutations = {
            "model_path": "models/guarded_ppo_v109/other_branch/step_000010000.zip",
            "model_sha256": "0" * 64,
            "branch_id": "wrong_branch",
            "chunk_index": 2,
            "cumulative_branch_timesteps": 999,
            "branch_base_seed": 999,
            "effective_chunk_seed": 999,
            "actual_model_seed": 999,
            "requested_chunk_timesteps": 999,
            "requested_cumulative_timesteps": 999,
            "actual_chunk_timesteps": 999,
            "actual_model_num_timesteps": 999,
            "rollout_granularity": 999,
            "timestep_overshoot": 999,
            "timestep_overshoot_ratio": 9.99,
            "experiment_plan_path": "data/other_plan.json",
            "experiment_plan_sha256": "1" * 64,
            "source_experiment_plan_path": "data/other_plan.json",
            "source_experiment_plan_sha256": "2" * 64,
            "parent_model_path": "models/maskable_ppo_bc_v105.zip",
            "parent_model_sha256": "3" * 64,
            "selected_party_id": "wrong_party",
            "initial_active_character": "mornye",
            "curriculum_reset_mode": "lynae_after_intro",
            "policy_action_ids": metadata["policy_action_ids"][:-1],
            "policy_action_count": 99,
            "observation_version": "wrong",
            "observation_shape": [999],
            "max_policy_action_slots": 99,
            "action_data_hash": "4" * 64,
            "party_config_hash": "5" * 64,
            "reward_formula": "route_similarity",
            "no_character_specific_reward": False,
            "no_route_similarity_reward": False,
        }
        for key, value in mutations.items():
            bad = dict(metadata)
            bad[key] = value
            _assert_fails(bad, sidecar, branch, model, f"wrong {key}")

        windows = "C:/Users/coree/OneDrive/Documents/GitHub/ww-dps-simulator-2/ww-dps-simulator-2/results/training_metadata.json"
        posix = "/tmp/extract/results/training_metadata.json"
        nested_data_plan = "/mnt/data/review121/data/guarded_ppo_experiment_plan_v109.json"
        nested_data_metadata = "/mnt/data/review121/results/training_metadata.json"
        assert canonicalize_guarded_path(windows) == "results/training_metadata.json"
        assert canonicalize_guarded_path(windows.replace("/", "\\")) == "results/training_metadata.json"
        assert canonicalize_guarded_path(posix) == "results/training_metadata.json"
        assert canonicalize_guarded_path(nested_data_plan) == "data/guarded_ppo_experiment_plan_v109.json"
        assert canonicalize_guarded_path(nested_data_metadata) == "results/training_metadata.json"
    print("guarded_ppo_checkpoint_sidecar_strict_contract_smoke_test ok")


def _valid_metadata(*, model: Path, branch: dict[str, object], plan_path: Path, model_sha: str, effective_seed_value: int, policy_ids: list[str], constants: dict[str, object]) -> dict[str, object]:
    from rl.guarded_ppo import sha256_file

    return {
        "model_path": model.as_posix(),
        "model_sha256": model_sha,
        "branch_id": branch["branch_id"],
        "chunk_index": 1,
        "chunk_timesteps": branch["chunk_timesteps"],
        "cumulative_branch_timesteps": branch["chunk_timesteps"],
        "branch_base_seed": branch["seed"],
        "effective_chunk_seed": effective_seed_value,
        "actual_model_seed": effective_seed_value,
        "requested_chunk_timesteps": branch["chunk_timesteps"],
        "requested_cumulative_timesteps": branch["chunk_timesteps"],
        "actual_chunk_timesteps": 10240,
        "actual_model_num_timesteps": 10240,
        "rollout_granularity": 512,
        "timestep_overshoot": 240,
        "timestep_overshoot_ratio": 0.024,
        "experiment_plan_path": plan_path.as_posix(),
        "experiment_plan_sha256": sha256_file(plan_path),
        "source_experiment_plan_path": plan_path.as_posix(),
        "source_experiment_plan_sha256": sha256_file(plan_path),
        "parent_model_path": None,
        "parent_model_sha256": None,
        "selected_party_id": "aemeath_mornye_lynae_enabled_test_party",
        "initial_active_character": branch["initial_active_character"],
        "curriculum_reset_mode": branch["curriculum_reset_mode"],
        "policy_action_ids": policy_ids,
        "policy_action_count": constants["policy_count"],
        "observation_version": constants["version"],
        "observation_shape": [constants["shape"]],
        "max_policy_action_slots": constants["max_slots"],
        "action_data_hash": constants["action_hash"],
        "party_config_hash": constants["party_hash"],
        "reward_formula": "damage_this_action / 10000.0",
        "no_character_specific_reward": True,
        "no_route_similarity_reward": True,
    }


def _write(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_synthetic_model(path: Path, *, num_timesteps: int, seed: int, n_steps: int) -> None:
    payload = {
        "num_timesteps": num_timesteps,
        "seed": seed,
        "n_steps": n_steps,
    }
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("data", json.dumps(payload))


def _assert_fails(payload: dict[str, object], sidecar: Path, branch: dict[str, object], model: Path, label: str) -> None:
    from rl.guarded_ppo import DEFAULT_PLAN_PATH, validate_checkpoint_sidecar

    _write(sidecar, payload)
    try:
        validate_checkpoint_sidecar(branch=branch, chunk_index=1, plan_path=DEFAULT_PLAN_PATH, model_path=model, metadata_path=sidecar, parent_model_path=None)
    except ValueError:
        return
    raise AssertionError(f"strict sidecar mutation unexpectedly passed: {label}")


if __name__ == "__main__":
    main()
