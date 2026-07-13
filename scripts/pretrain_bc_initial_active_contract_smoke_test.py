from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rl.demo_contract import DEFAULT_DEMO_PATH, file_sha256, load_demo_npz  # noqa: E402
from rl.pretrain_maskable_ppo_bc import bc_metadata_path  # noqa: E402


PARTY = "aemeath_mornye_lynae_enabled_test_party"


def main() -> None:
    _set_thread_limits()
    try:
        import torch
    except ModuleNotFoundError as exc:
        print(f"pretrain_bc_initial_active_contract_smoke_test dependency-missing: {exc}")
        return
    torch.manual_seed(123)
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass

    protected_hashes_before = _protected_hashes()
    demo = load_demo_npz(DEFAULT_DEMO_PATH)
    assert demo["metadata"]["initial_active_character"] == "aemeath"
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        model_path = temp_root / "maskable_ppo_bc_initial_active.zip"
        dry_run = _run(
            [
                sys.executable,
                "rl/pretrain_maskable_ppo_bc.py",
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
        dry_plan = _first_json_object(dry_run.stdout)
        assert dry_plan["initial_active_character"] == "aemeath", dry_run.stdout
        assert not model_path.exists()

        trained = _run(
            [
                sys.executable,
                "rl/pretrain_maskable_ppo_bc.py",
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
            ],
            timeout=120,
        )
        sidecar = json.loads(bc_metadata_path(model_path).read_text(encoding="utf-8"))
        assert sidecar["initial_active_character"] == "aemeath", trained.stdout

        aemeath_eval = _run(
            [
                sys.executable,
                "rl/evaluate_maskable_ppo.py",
                "--dry-run-contract",
                "--model-path",
                str(model_path),
                "--party",
                PARTY,
                "--initial-active-character",
                "aemeath",
            ]
        )
        aemeath_payload = _first_json_object(aemeath_eval.stdout)
        assert aemeath_payload["metadata_source"] == "bc_model_sidecar"
        assert aemeath_payload["metadata_mismatches"] == {}
        assert aemeath_payload["model_space_mismatches"] == {}

        mornye_eval = subprocess.run(
            [
                sys.executable,
                "rl/evaluate_maskable_ppo.py",
                "--dry-run-contract",
                "--model-path",
                str(model_path),
                "--party",
                PARTY,
                "--initial-active-character",
                "mornye",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
            env=_env(),
        )
        assert mornye_eval.returncode != 0, mornye_eval.stdout
        assert "initial_active_character" in mornye_eval.stdout, mornye_eval.stdout
        _first_json_object(mornye_eval.stdout)

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
                str(temp_root / "invalid_temp.zip"),
                "--dry-run",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
            env=_env(),
        )
        assert bad_dry_run.returncode != 0
        assert not (temp_root / "invalid_temp.zip").exists()
        assert "initial_active_character" in (bad_dry_run.stdout + bad_dry_run.stderr)

    assert protected_hashes_before == _protected_hashes()
    print("pretrain_bc_initial_active_contract_smoke_test ok")


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


def _run(command: list[str], *, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=timeout, env=_env())
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    return result


def _protected_hashes() -> dict[str, str]:
    paths = {
        "npz": DEFAULT_DEMO_PATH,
        "summary": ROOT / "results" / "manual_120s_bc_demonstration_v105_summary.json",
        "report": ROOT / "reports" / "manual_120s_bc_demonstration_v105.md",
        "progress": ROOT / "PROJECT_PROGRESS_STATE.json",
    }
    return {key: file_sha256(path) for key, path in paths.items() if path.exists()}


def _first_json_object(text: str) -> dict:
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char == "{":
            try:
                payload, _end = decoder.raw_decode(text[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload
    raise AssertionError(text)


if __name__ == "__main__":
    main()
