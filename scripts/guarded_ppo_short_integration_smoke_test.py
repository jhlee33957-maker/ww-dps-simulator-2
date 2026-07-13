from __future__ import annotations

import os
import json
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    canonical_before = _snapshot_canonical_outputs()
    with tempfile.TemporaryDirectory(prefix="guarded-ppo-short-") as temp_dir:
        output_root = Path(temp_dir)
        result = subprocess.run(
            [
                sys.executable,
                "rl/run_guarded_ppo_experiment.py",
                "--execute",
                "--smoke-run",
                "--output-root",
                str(output_root),
            ],
            cwd=ROOT,
            env=_env(),
            text=True,
            capture_output=True,
            timeout=240,
        )
        if result.returncode != 0:
            raise AssertionError(f"smoke run failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        state = output_root / "results" / "guarded_ppo_v109_smoke" / "experiment_state.json"
        leaderboard = output_root / "results" / "guarded_ppo_v109_smoke" / "leaderboard.json"
        best = output_root / "results" / "guarded_ppo_v109_smoke" / "best_checkpoint.json"
        assert state.exists()
        assert leaderboard.exists()
        assert best.exists()
        checkpoints = list((output_root / "models" / "guarded_ppo_v109_smoke").rglob("step_*.zip"))
        assert len(checkpoints) == 3
        checkpoint = sorted(checkpoints)[0]
        before_sha = _sha256(checkpoint)
        before_mtime = checkpoint.stat().st_mtime_ns
        resumed = subprocess.run(
            [
                sys.executable,
                "rl/run_guarded_ppo_experiment.py",
                "--execute",
                "--smoke-run",
                "--resume",
                "--output-root",
                str(output_root),
            ],
            cwd=ROOT,
            env=_env(),
            text=True,
            capture_output=True,
            timeout=240,
        )
        if resumed.returncode != 0:
            raise AssertionError(f"smoke resume failed\nstdout:\n{resumed.stdout}\nstderr:\n{resumed.stderr}")
        assert _sha256(checkpoint) == before_sha
        assert checkpoint.stat().st_mtime_ns == before_mtime
        state_payload = json.loads(state.read_text(encoding="utf-8"))
        best_payload = json.loads(best.read_text(encoding="utf-8"))
        bc_damage = next(item for item in state_payload["incumbents"] if item["kind"] == "verified_bc_model")["total_damage"]
        branch_records = [
            chunk
            for branch_state in state_payload["branches"].values()
            for chunk in branch_state["chunks"]
            if chunk.get("kind") == "guarded_ppo_checkpoint"
        ]
        expected_seeds = {
            "bc_conservative_seed_11": 11,
            "bc_exploratory_seed_73": 73,
            "scratch_control_seed_137": 137,
        }
        assert len(branch_records) == 3
        for record in branch_records:
            expected_seed = expected_seeds[record["branch_id"]]
            assert record["branch_base_seed"] == expected_seed
            assert record["effective_chunk_seed"] == expected_seed
            assert record["actual_model_seed"] == expected_seed
            assert record["model_sha256"] == record["checkpoint_sha256"]
            assert Path(record["metadata_path"]).exists()
            assert Path(record["summary_path"]).exists()
            assert Path(record["timeline_path"]).exists()
            assert Path(record["evaluation_stdout_log_path"]).exists()
            assert Path(record["evaluation_stderr_log_path"]).exists()
        max_branch_damage = max(float(item["total_damage"]) for item in branch_records)
        if max_branch_damage <= float(bc_damage) + 1e-6:
            assert best_payload["winner_kind"] == "verified_bc_model"
        else:
            assert best_payload["total_damage"] == max_branch_damage
        assert not (output_root / "models" / "guarded_ppo_v109_smoke" / "best.zip").exists()
    assert _snapshot_canonical_outputs() == canonical_before
    print("guarded_ppo_short_integration_smoke_test ok")


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    return env


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _snapshot_canonical_outputs() -> dict[str, tuple[str, int]]:
    roots = [ROOT / "models" / "guarded_ppo_v109", ROOT / "results" / "guarded_ppo_v109"]
    snapshot: dict[str, tuple[str, int]] = {}
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            snapshot[path.relative_to(ROOT).as_posix()] = (_sha256(path), path.stat().st_mtime_ns)
    return snapshot


if __name__ == "__main__":
    main()
