from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env.wuwa_env import WuwaDpsEnv  # noqa: E402
from rl.demo_contract import action_data_hash, json_safe, party_config_hash  # noqa: E402
from rl.evaluate_maskable_ppo import bc_metadata_path  # noqa: E402


PARTY = "aemeath_mornye_lynae_enabled_test_party"
SMOKE_TIMEOUT_SECONDS = 90.0


def main() -> None:
    started = time.perf_counter()
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
    try:
        import numpy as np
        import torch
        from sb3_contrib import MaskablePPO
    except ModuleNotFoundError as exc:
        print(f"evaluate_bc_sidecar_compatibility_smoke_test dependency-missing: {exc}")
        return

    np.random.seed(123)
    torch.manual_seed(123)
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    assert json_safe({"value": np.int64(7)}) == {"value": 7}
    env = WuwaDpsEnv(ROOT / "data", party=PARTY, initial_active_character="aemeath", curriculum_reset_mode="none")
    env.reset(seed=123)
    observation_metadata = env.observation_metadata()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        model_path = temp_root / "maskable_ppo_bc_v105.zip"
        stale_global = temp_root / "training_metadata.json"
        model = MaskablePPO("MlpPolicy", env, seed=123, device="cpu", verbose=0)
        model.save(model_path)
        sidecar = {
            "selected_party_character_ids": env.get_selected_party_character_ids(),
            "initial_active_character": env.get_initial_active_character(),
            "policy_action_ids": env.get_policy_action_ids(),
            "policy_action_count": int(env.action_space.n),
            "active_build_profiles": env.get_active_build_profiles(),
            "effective_build_stats_summary": env.get_effective_build_stats_summary(),
            "action_data_hash": action_data_hash(root=ROOT),
            "party_config_hash": party_config_hash(root=ROOT),
            "observation_shape": list(env.observation_space.shape),
            "observation_version": observation_metadata["observation_version"],
            "observation_labels": observation_metadata["observation_labels"],
            "max_party_slots": observation_metadata["max_party_slots"],
            "max_policy_action_slots": observation_metadata["max_policy_action_slots"],
            "observation_action_slot_mapping": observation_metadata["observation_action_slot_mapping"],
            "model_path": model_path.as_posix(),
        }
        bc_metadata_path(model_path).write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
        stale_global.write_text(
            json.dumps(
                {
                    "model_path": model_path.as_posix(),
                    "observation_shape": [204],
                    "observation_version": "legacy",
                    "policy_action_count": 23,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        command = [
            sys.executable,
            "rl/evaluate_maskable_ppo.py",
            "--dry-run-contract",
            "--model-path",
            str(model_path),
            "--party",
            PARTY,
            "--initial-active-character",
            "aemeath",
            "--training-metadata-path",
            str(stale_global),
        ]
        env_vars = dict(os.environ)
        env_vars.update(
            {
                "OMP_NUM_THREADS": "1",
                "MKL_NUM_THREADS": "1",
                "OPENBLAS_NUM_THREADS": "1",
                "NUMEXPR_NUM_THREADS": "1",
            }
        )
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=60, env=env_vars)
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        assert '"metadata_source": "bc_model_sidecar"' in result.stdout, result.stdout
        assert '"model_space_mismatches": {}' in result.stdout, result.stdout
        assert '"metadata_mismatches": {}' in result.stdout, result.stdout
        mismatch_command = [
            sys.executable,
            "rl/evaluate_maskable_ppo.py",
            "--dry-run-contract",
            "--model-path",
            str(model_path),
            "--party",
            PARTY,
            "--initial-active-character",
            "mornye",
            "--training-metadata-path",
            str(stale_global),
        ]
        mismatch = subprocess.run(
            mismatch_command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
            env=env_vars,
        )
        assert mismatch.returncode != 0, mismatch.stdout
        assert "initial_active_character" in mismatch.stdout, mismatch.stdout
    runtime_seconds = time.perf_counter() - started
    assert runtime_seconds < SMOKE_TIMEOUT_SECONDS, runtime_seconds
    print(json.dumps({"status": "ok", "runtime_seconds": round(runtime_seconds, 6)}, indent=2))
    print("evaluate_bc_sidecar_compatibility_smoke_test ok")


if __name__ == "__main__":
    main()
