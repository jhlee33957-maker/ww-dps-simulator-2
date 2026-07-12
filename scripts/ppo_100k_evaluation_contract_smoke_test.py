from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
PPO_MODEL = ROOT / "models" / "maskable_ppo_candidate_after_bc_v105.zip"
EXPECTED_PPO_MODEL_SHA256 = "9b62faa610c3710bf4e17603a92baf8e8c657b51e8fba22d8525a1e33a257513"
EXPECTED_BC_DAMAGE = 5165134.682363356
EXPECTED_TOTAL_DAMAGE = 3600637.129626801
EXPECTED_DPS = 30005.309413556675
EXPECTED_SELECTED_SHA256 = "0bba8688b3a085fde3a842901f659b24fdefd009102cc1ccba5a0d971a27c11d"
EXPECTED_RESOLVED_SHA256 = "9650b6e4d1b8f9ba616c26293f60c8cc4a5d6ea57dcf7153305aa085f84ad6e1"
EXPECTED_DAMAGE_BY_CHARACTER = {
    "aemeath": 2674131.053725695,
    "mornye": 201528.93426401448,
    "lynae": 724977.1416370921,
}
EXPECTED_SCHEDULED_DAMAGE = 140026.5111366104
EXPECTED_MANUAL_DAMAGE = 5165134.682363359
EXPECTED_MANUAL_RATIO = 0.6971042094839032
EXPECTED_MANUAL_DELTA = -1564497.5527365585

PROTECTED_FILES = (
    "models/maskable_ppo_bc_v105.zip",
    "models/maskable_ppo_bc_v105.zip.bc_metadata.json",
    "models/maskable_ppo_candidate_after_bc_v105.zip",
    "results/training_metadata.json",
    "results/ppo_evaluation_summary.json",
    "results/ppo_timeline.csv",
    "results/ppo_100k_evaluation_summary.json",
    "results/ppo_100k_timeline.csv",
    "results/manual_bc_ppo_comparison_v108.json",
    "data/manual_120s_baseline_routes_v104.json",
    "data/generated/manual_120s_bc_demonstration_v105.npz",
    "direct_action_data_patch_manifest_v61.json",
)


def main() -> None:
    before = _hashes(PROTECTED_FILES)
    assert _sha256(PPO_MODEL) == EXPECTED_PPO_MODEL_SHA256
    metadata = json.loads((ROOT / "results" / "training_metadata.json").read_text(encoding="utf-8"))
    _assert_training_metadata(metadata)
    with TemporaryDirectory() as temp_dir:
        summary_path = Path(temp_dir) / "ppo_100k_summary.json"
        timeline_path = Path(temp_dir) / "ppo_100k_timeline.csv"
        command = [
            PYTHON,
            "rl/evaluate_maskable_ppo.py",
            "--model-path",
            "models/maskable_ppo_candidate_after_bc_v105.zip",
            "--party",
            "aemeath_mornye_lynae_enabled_test_party",
            "--initial-active-character",
            "aemeath",
            "--summary-path",
            str(summary_path),
            "--timeline-path",
            str(timeline_path),
        ]
        env = dict(os.environ)
        env.update(
            {
                "OMP_NUM_THREADS": "1",
                "MKL_NUM_THREADS": "1",
                "OPENBLAS_NUM_THREADS": "1",
                "NUMEXPR_NUM_THREADS": "1",
            }
        )
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        assert result.returncode == 0, result.stdout + "\n" + result.stderr
        assert summary_path.exists()
        assert timeline_path.exists()
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _assert_summary(summary)
    after = _hashes(PROTECTED_FILES)
    assert before == after
    print("ppo_100k_evaluation_contract_smoke_test ok")


def _assert_training_metadata(metadata: dict[str, object]) -> None:
    assert metadata["model_path"].replace("\\", "/") == "models/maskable_ppo_candidate_after_bc_v105.zip"
    assert metadata["source_bc_model"] == "models/maskable_ppo_bc_v105.zip"
    assert metadata["source_bc_model_sha256"] == "7b5ef151b7ac9299a8134032e58f1d75919832a3823c8715653852393045461e"
    assert metadata["ppo_model_path"] == "models/maskable_ppo_candidate_after_bc_v105.zip"
    assert metadata["ppo_model_sha256"] == EXPECTED_PPO_MODEL_SHA256
    assert metadata["timesteps"] == 100000
    assert metadata["seed"] == 42
    _assert_close(float(metadata["learning_rate"]), 0.0003)
    _assert_close(float(metadata["ent_coef"]), 0.01)
    assert metadata["n_steps"] == 512
    assert metadata["batch_size"] == 64
    _assert_close(float(metadata["gamma"]), 0.999)
    assert metadata["initial_active_character"] == "aemeath"
    assert metadata["curriculum_reset_mode"] == "none"
    _assert_close(float(metadata["elapsed_seconds"]), 321.1551833000267)
    assert metadata["train_started_at"] == "2026-07-12T16:33:45.564697+00:00"
    assert metadata["train_finished_at"] == "2026-07-12T16:39:06.719900+00:00"
    assert metadata["training_started_at"] == "2026-07-12T16:33:45.564697+00:00"
    assert metadata["training_finished_at"] == "2026-07-12T16:39:06.719900+00:00"
    assert metadata["policy_action_count"] == 25
    assert metadata["action_data_hash"] == "d6377d54a1abb985dc5f58866321c61c7b904a6b73ddc1538be7e38d36a99ff1"
    assert metadata["party_config_hash"] == "bd106ba1c0f5581436c35fea736a00fd6ad92b131f8b43ba8cf1e3dc89cbcb11"


def _assert_summary(summary: dict[str, object]) -> None:
    _assert_close(float(summary["total_damage"]), EXPECTED_TOTAL_DAMAGE)
    _assert_close(float(summary["dps"]), EXPECTED_DPS)
    _assert_close(float(summary["final_time"]), 120.0)
    assert summary["selected_action_count"] == 152
    assert summary["resolved_action_count"] == 152
    assert summary["selected_sequence_sha256"] == EXPECTED_SELECTED_SHA256
    assert summary["resolved_sequence_sha256"] == EXPECTED_RESOLVED_SHA256
    damage_by_character = summary["damage_by_character"]
    assert isinstance(damage_by_character, dict)
    for character_id, expected in EXPECTED_DAMAGE_BY_CHARACTER.items():
        _assert_close(float(damage_by_character[character_id]), expected)
    role_breakdown = summary["effective_damage_role_breakdown"]
    assert isinstance(role_breakdown, dict)
    _assert_close(float(role_breakdown["scheduled_damage"]), EXPECTED_SCHEDULED_DAMAGE)
    _assert_close(float(role_breakdown["total_damage_delta"]), 0.0)
    assert summary["model_metadata_mismatches"] == {}
    assert summary["model_space_mismatches"] == {}
    _assert_close(float(summary["manual_baseline_total_damage"]), EXPECTED_MANUAL_DAMAGE)
    _assert_close(float(summary["manual_baseline_damage_ratio"]), EXPECTED_MANUAL_RATIO)
    _assert_close(float(summary["manual_baseline_damage_delta"]), EXPECTED_MANUAL_DELTA)
    assert summary["manual_baseline_selected_sequence_match"] is False
    assert summary["manual_baseline_resolved_sequence_match"] is False
    assert summary["manual_baseline_character_damage_match"] is False
    assert float(summary["total_damage"]) < EXPECTED_BC_DAMAGE


def _hashes(paths: tuple[str, ...]) -> dict[str, str]:
    return {path: _sha256(ROOT / path) for path in paths}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_close(actual: float, expected: float, *, tolerance: float = 1e-6) -> None:
    assert abs(actual - expected) <= tolerance, (actual, expected)


if __name__ == "__main__":
    main()
