from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "maskable_ppo_bc_v105.zip"
EXPECTED_DAMAGE_BY_CHARACTER = {
    "aemeath": 3733934.8538652016,
    "mornye": 268807.92005964793,
    "lynae": 1162391.9084385103,
}


def main() -> None:
    _set_thread_limits()
    before = _protected_hashes()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        command = [
            sys.executable,
            str(ROOT / "rl" / "evaluate_maskable_ppo.py"),
            "--model-path",
            str(MODEL_PATH),
            "--party",
            "aemeath_mornye_lynae_enabled_test_party",
            "--initial-active-character",
            "aemeath",
            "--summary-path",
            str(temp_root / "results" / "ppo_evaluation_summary.json"),
            "--timeline-path",
            str(temp_root / "results" / "ppo_timeline.csv"),
        ]
        result = subprocess.run(command, cwd=temp_root, text=True, capture_output=True, timeout=120, env=_env())
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        summary_path = temp_root / "results" / "ppo_evaluation_summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary["selected_action_count"] == 148
    assert summary["resolved_action_count"] == 148
    assert summary["selected_sequence_sha256"] == "e3ddea873cb5059bd29a8a9eb7165ea0e45a9a9e4fa4f68e5e229db2f622daf1"
    assert summary["resolved_sequence_sha256"] == "3edca6f6f258999a9c915a9ec32ee88c0db570d2303846e0fb8b6da367970229"
    _assert_close(summary["total_damage"], 5165134.682363356, "total damage")
    _assert_close(summary["dps"], 43042.78901969464, "dps")
    assert summary["manual_baseline_selected_sequence_match"] is True
    assert summary["manual_baseline_resolved_sequence_match"] is True
    assert summary["manual_baseline_character_damage_match"] is True
    assert summary["model_training_metadata_source"] == "model_sidecar"
    assert summary["model_metadata_mismatches"] == {}
    assert summary["model_space_mismatches"] == {}
    for character_id, expected in EXPECTED_DAMAGE_BY_CHARACTER.items():
        _assert_close(summary["damage_by_character"][character_id], expected, f"damage {character_id}")
    _assert_close(sum(summary["damage_by_character"].values()), summary["total_damage"], "damage by character sum")
    role = summary["effective_damage_role_breakdown"]
    assert role["scheduled_damage"] > 0.0
    _assert_close(role["scheduled_damage"], 205987.4042873791, "scheduled damage")
    _assert_close(role["total_damage_delta"], 0.0, "role total delta")
    assert before == _protected_hashes()
    print("bc_evaluation_manual_baseline_parity_smoke_test ok")


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
    import hashlib

    paths = [
        ROOT / "models" / "maskable_ppo_bc_v105.zip",
        ROOT / "models" / "maskable_ppo_bc_v105.zip.bc_metadata.json",
        ROOT / "data" / "generated" / "manual_120s_bc_demonstration_v105.npz",
        ROOT / "results" / "manual_120s_bc_demonstration_v105_summary.json",
        ROOT / "PROJECT_PROGRESS_STATE.json",
    ]
    return {path.as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths if path.exists()}


def _assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-6) -> None:
    if abs(float(actual) - float(expected)) > tolerance:
        raise AssertionError(f"{label}: {actual!r} != {expected!r}")


if __name__ == "__main__":
    main()
