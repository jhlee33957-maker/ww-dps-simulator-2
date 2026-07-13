from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SPOT_CHECKPOINTS = (
    ("bc_conservative_seed_11", "step_000010000", 5165134.682363356),
    ("bc_conservative_seed_11", "step_000070000", 5156315.608505706),
    ("bc_conservative_seed_11", "step_000100000", 5134470.883053988),
    ("bc_exploratory_seed_73", "step_000020000", 5158201.636481964),
    ("scratch_control_seed_137", "step_000050000", 2566933.375001255),
)


def main() -> None:
    canonical_before = _snapshot_canonical_outputs()
    with tempfile.TemporaryDirectory(prefix="guarded-ppo-spot-eval-") as temp_dir:
        temp_root = Path(temp_dir)
        for branch_id, step, expected_damage in SPOT_CHECKPOINTS:
            model_path = Path("models") / "guarded_ppo_v109" / branch_id / f"{step}.zip"
            summary_path = temp_root / f"{branch_id}_{step}_summary.json"
            timeline_path = temp_root / f"{branch_id}_{step}_timeline.csv"
            result = subprocess.run(
                [
                    sys.executable,
                    "rl/evaluate_maskable_ppo.py",
                    "--model-path",
                    model_path.as_posix(),
                    "--party",
                    "aemeath_mornye_lynae_enabled_test_party",
                    "--initial-active-character",
                    "aemeath",
                    "--summary-path",
                    str(summary_path),
                    "--timeline-path",
                    str(timeline_path),
                ],
                cwd=ROOT,
                env=_env(),
                text=True,
                capture_output=True,
                timeout=240,
            )
            if result.returncode != 0:
                raise AssertionError(
                    f"spot evaluation failed for {model_path}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
                )
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            assert timeline_path.exists()
            _assert_close(summary["total_damage"], expected_damage)
            _assert_close(summary["final_time"], 120.0)
            assert summary["model_training_metadata_source"] == "ppo_model_sidecar"
            assert summary["model_training_metadata_path"] == f"{model_path.as_posix()}.ppo_metadata.json"
            assert summary["model_metadata_mismatches"] == {}
            assert summary["model_space_mismatches"] == {}
            role_breakdown = summary["effective_damage_role_breakdown"]
            _assert_close(role_breakdown["total_damage_delta"], 0.0)
    assert _snapshot_canonical_outputs() == canonical_before
    print("guarded_ppo_completed_experiment_spot_evaluation_smoke_test ok")


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


def _snapshot_canonical_outputs() -> dict[str, str]:
    roots = [ROOT / "models" / "guarded_ppo_v109", ROOT / "results" / "guarded_ppo_v109"]
    snapshot: dict[str, str] = {}
    for root in roots:
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            snapshot[path.relative_to(ROOT).as_posix()] = _sha256(path)
    return snapshot


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_close(actual: Any, expected: float, *, tolerance: float = 1e-6) -> None:
    assert abs(float(actual) - expected) <= tolerance, (actual, expected)


if __name__ == "__main__":
    main()
