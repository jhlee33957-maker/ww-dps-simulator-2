from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "data" / "guarded_ppo_experiment_plan_v109.json"


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="ppo-sidecar-smoke-") as temp_dir:
        temp = Path(temp_dir)
        model1 = temp / "step1.zip"
        sidecar1 = Path(str(model1) + ".ppo_metadata.json")
        _run(
            [
                sys.executable,
                "rl/train_maskable_ppo.py",
                "--timesteps",
                "32",
                "--model-path",
                str(model1),
                "--metadata-path",
                str(sidecar1),
                "--party",
                "aemeath_mornye_lynae_enabled_test_party",
                "--initial-active-character",
                "aemeath",
                "--curriculum-reset-mode",
                "none",
                "--n-steps",
                "32",
                "--batch-size",
                "32",
                "--verbose",
                "0",
                "--log-interval",
                "1",
                "--branch-id",
                "sidecar_smoke",
                "--chunk-index",
                "1",
                "--cumulative-timesteps",
                "32",
                "--experiment-plan-path",
                str(PLAN),
                "--skip-global-metadata",
            ]
        )
        metadata = json.loads(sidecar1.read_text(encoding="utf-8"))
        assert metadata["model_sha256"]
        assert metadata["branch_id"] == "sidecar_smoke"
        assert metadata["chunk_index"] == 1
        assert metadata["no_route_similarity_reward"] is True
        assert metadata["no_character_specific_reward"] is True

        dry = _run_eval(model1)
        assert dry["metadata_source"] == "ppo_model_sidecar"
        assert dry["metadata_mismatches"] == {}

        model2 = temp / "step2.zip"
        _run(
            [
                sys.executable,
                "rl/train_maskable_ppo.py",
                "--timesteps",
                "32",
                "--load-model",
                str(model1),
                "--model-path",
                str(model2),
                "--metadata-path",
                str(model2) + ".ppo_metadata.json",
                "--party",
                "aemeath_mornye_lynae_enabled_test_party",
                "--initial-active-character",
                "aemeath",
                "--curriculum-reset-mode",
                "none",
                "--n-steps",
                "32",
                "--batch-size",
                "32",
                "--verbose",
                "0",
                "--log-interval",
                "1",
                "--branch-id",
                "sidecar_smoke",
                "--chunk-index",
                "2",
                "--cumulative-timesteps",
                "64",
                "--experiment-plan-path",
                str(PLAN),
                "--skip-global-metadata",
            ]
        )

        wrong_initial = _run_eval(model1, initial="mornye", check=False)
        assert wrong_initial.returncode != 0
        assert "initial_active_character" in wrong_initial.stdout

        global_metadata = temp / "training_metadata.json"
        wrong_global = dict(metadata)
        wrong_global["model_path"] = str(model1)
        wrong_global["initial_active_character"] = "mornye"
        global_metadata.write_text(json.dumps(wrong_global, indent=2), encoding="utf-8")
        dry = _run_eval(model1, training_metadata_path=global_metadata)
        assert dry["metadata_source"] == "ppo_model_sidecar"
        assert dry["metadata_mismatches"] == {}

        corrupt = dict(metadata)
        corrupt["observation_shape"] = [999]
        sidecar1.write_text(json.dumps(corrupt, indent=2), encoding="utf-8")
        bad_contract = _run_eval(model1, check=False)
        assert bad_contract.returncode != 0
        assert "stale_observation_shape" in bad_contract.stdout

        corrupt["observation_shape"] = metadata["observation_shape"]
        corrupt["model_sha256"] = "0" * 64
        sidecar1.write_text(json.dumps(corrupt, indent=2), encoding="utf-8")
        bad_sha = _run_eval(model1, check=False)
        assert bad_sha.returncode != 0
        assert "model_sha256" in bad_sha.stdout
    print("ppo_checkpoint_sidecar_smoke_test ok")


def _run_eval(
    model_path: Path,
    *,
    initial: str = "aemeath",
    training_metadata_path: Path | None = None,
    check: bool = True,
) -> dict[str, object] | subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        "rl/evaluate_maskable_ppo.py",
        "--model-path",
        str(model_path),
        "--party",
        "aemeath_mornye_lynae_enabled_test_party",
        "--initial-active-character",
        initial,
        "--dry-run-contract",
    ]
    if training_metadata_path is not None:
        command.extend(["--training-metadata-path", str(training_metadata_path)])
    result = _run(command, check=check)
    if not check:
        return result
    start = result.stdout.find("{")
    assert start >= 0, result.stdout
    return json.loads(result.stdout[start:])


def _run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.update(
        {
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
        }
    )
    result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, timeout=120)
    if check and result.returncode != 0:
        raise AssertionError(
            f"command failed: {' '.join(command)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


if __name__ == "__main__":
    main()
