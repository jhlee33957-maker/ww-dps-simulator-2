from __future__ import annotations

import contextlib
import io
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
from rl.demo_contract import DEFAULT_DEMO_PATH, DemoContractError, file_sha256, json_safe, load_demo_npz  # noqa: E402
from rl.evaluate_maskable_ppo import (  # noqa: E402
    _model_space_mismatches,
    bc_metadata_path,
    load_model_metadata,
    model_metadata_mismatches,
)
from rl.pretrain_maskable_ppo_bc import build_arg_parser, resolve_demo_initial_active_character, run_pretrain  # noqa: E402


PARTY = "aemeath_mornye_lynae_enabled_test_party"
SMOKE_TIMEOUT_SECONDS = 120.0


def main() -> None:
    started = time.perf_counter()
    _set_thread_limits()
    try:
        import numpy as np
        import torch
        from sb3_contrib import MaskablePPO
    except ModuleNotFoundError as exc:
        print(f"bc_pretrain_evaluator_contract_smoke_test dependency-missing: {exc}")
        return

    np.random.seed(123)
    torch.manual_seed(123)
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    assert json_safe({"value": np.int64(7)}) == {"value": 7}

    protected_hashes_before = _protected_hashes()
    demo = load_demo_npz(DEFAULT_DEMO_PATH)
    assert demo["metadata"]["initial_active_character"] == "aemeath"
    assert demo["metadata"]["curriculum_reset_mode"] == "none"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        model_path = temp_root / "maskable_ppo_bc_contract.zip"
        stale_global = temp_root / "training_metadata.json"
        invalid_model_path = temp_root / "invalid_temp.zip"

        dry_plan = _run_pretrain(
            [
                "--party",
                PARTY,
                "--initial-active-character",
                "aemeath",
                "--demo-path",
                "data/generated/manual_120s_bc_demonstration_v105.npz",
                "--model-path",
                str(model_path),
                "--dry-run",
            ]
        )
        assert dry_plan["initial_active_character"] == "aemeath", dry_plan
        assert dry_plan["curriculum_reset_mode"] == "none", dry_plan
        assert dry_plan["sample_count"] == 148, dry_plan
        assert dry_plan["observation_shape"] == [314], dry_plan
        assert dry_plan["action_count"] == 25, dry_plan
        assert not model_path.exists()

        train_metadata = _run_pretrain(
            [
                "--party",
                PARTY,
                "--initial-active-character",
                "aemeath",
                "--demo-path",
                "data/generated/manual_120s_bc_demonstration_v105.npz",
                "--model-path",
                str(model_path),
                "--epochs",
                "0",
                "--batch-size",
                "148",
                "--learning-rate",
                "0.003",
                "--seed",
                "11",
                "--device",
                "cpu",
            ]
        )
        assert model_path.exists()
        sidecar_path = bc_metadata_path(model_path)
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        assert sidecar["initial_active_character"] == "aemeath", train_metadata
        assert sidecar["observation_shape"] == [314], sidecar
        assert sidecar["policy_action_count"] == 25, sidecar
        assert sidecar["selected_party_character_ids"] == ["mornye", "aemeath", "lynae"], sidecar
        assert sidecar["action_data_hash"] == dry_plan["action_data_hash"], sidecar
        assert sidecar["party_config_hash"] == dry_plan["party_config_hash"], sidecar

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
        model = MaskablePPO.load(model_path, device="cpu")
        aemeath_result = _evaluate_contract(model, model_path, stale_global, initial_active_character="aemeath")
        assert aemeath_result["metadata_source"] == "bc_model_sidecar", aemeath_result
        assert aemeath_result["metadata_mismatches"] == {}, aemeath_result
        assert aemeath_result["model_space_mismatches"] == {}, aemeath_result

        mornye_result = _evaluate_contract(model, model_path, stale_global, initial_active_character="mornye")
        assert "initial_active_character" in mornye_result["metadata_mismatches"], mornye_result
        json.dumps(json_safe(mornye_result["metadata_mismatches"]), indent=2, ensure_ascii=False)

        try:
            resolve_demo_initial_active_character(demo, explicit_initial_active_character="mornye")
        except DemoContractError as exc:
            assert "initial_active_character" in str(exc)
        else:
            raise AssertionError("Explicit Mornye initial-active pretrain contract unexpectedly passed")
        assert not invalid_model_path.exists()

        bad_dry_run = subprocess.run(
            [
                sys.executable,
                "rl/pretrain_maskable_ppo_bc.py",
                "--party",
                PARTY,
                "--initial-active-character",
                "mornye",
                "--demo-path",
                "data/generated/manual_120s_bc_demonstration_v105.npz",
                "--model-path",
                str(invalid_model_path),
                "--dry-run",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
            env=_env(),
        )
        assert bad_dry_run.returncode != 0
        assert not invalid_model_path.exists()
        assert "initial_active_character" in (bad_dry_run.stdout + bad_dry_run.stderr)

    assert protected_hashes_before == _protected_hashes()
    runtime_seconds = time.perf_counter() - started
    assert runtime_seconds < SMOKE_TIMEOUT_SECONDS, runtime_seconds
    print(
        json.dumps(
            {
                "status": "ok",
                "runtime_seconds": round(runtime_seconds, 6),
                "aemeath_evaluator_metadata_mismatches": {},
                "aemeath_evaluator_model_space_mismatches": {},
                "mornye_evaluator_mismatch_keys": sorted(mornye_result["metadata_mismatches"].keys()),
                "temporary_artifacts_only": True,
                "full_bc_training_executed": False,
                "ppo_training_executed": False,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    print("bc_pretrain_evaluator_contract_smoke_test ok")


def _run_pretrain(arguments: list[str]) -> dict:
    parser = build_arg_parser()
    args = parser.parse_args(arguments)
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        result = run_pretrain(args)
    assert isinstance(result, dict), buffer.getvalue()
    return result


def _evaluate_contract(
    model: object,
    model_path: Path,
    stale_global: Path,
    *,
    initial_active_character: str,
) -> dict:
    env = WuwaDpsEnv(ROOT / "data", party=PARTY, initial_active_character=initial_active_character)
    metadata_info = load_model_metadata(model_path, stale_global)
    metadata = metadata_info["metadata"]
    metadata_mismatches = model_metadata_mismatches(metadata, env)
    model_space_mismatches = _model_space_mismatches(model, env)
    payload = {
        "status": "ok" if not metadata_mismatches and not model_space_mismatches else "mismatch",
        "dry_run_contract": True,
        "metadata_source": metadata_info["source"],
        "metadata_path": metadata_info["path"],
        "metadata_mismatches": metadata_mismatches,
        "model_space_mismatches": model_space_mismatches,
    }
    json.dumps(json_safe(payload), indent=2, ensure_ascii=False)
    return payload


def _set_thread_limits() -> None:
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
        }
    )
    return env


def _protected_hashes() -> dict[str, str]:
    paths = {
        "npz": DEFAULT_DEMO_PATH,
        "summary": ROOT / "results" / "manual_120s_bc_demonstration_v105_summary.json",
        "report": ROOT / "reports" / "manual_120s_bc_demonstration_v105.md",
        "progress": ROOT / "PROJECT_PROGRESS_STATE.json",
        "canonical_model": ROOT / "models" / "maskable_ppo_bc_v105.zip",
        "canonical_model_sidecar": ROOT / "models" / "maskable_ppo_bc_v105.zip.bc_metadata.json",
    }
    return {key: file_sha256(path) for key, path in paths.items() if path.exists()}


if __name__ == "__main__":
    main()
