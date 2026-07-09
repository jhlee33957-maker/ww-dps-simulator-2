from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rl.train_maskable_ppo import build_arg_parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args(
        [
            "--party",
            "aemeath_mornye_lynae_enabled_test_party",
            "--curriculum-reset-mode",
            "mixed_lynae_route_curriculum",
            "--timesteps",
            "300000",
            "--verbose",
            "1",
            "--log-interval",
            "1",
            "--progress-every-steps",
            "10000",
            "--dry-run-train-config",
        ]
    )
    assert args.verbose == 1
    assert args.log_interval == 1
    assert args.progress_every_steps == 10000
    assert args.dry_run_train_config is True

    command = [
        sys.executable,
        str(ROOT / "rl" / "train_maskable_ppo.py"),
        "--party",
        "aemeath_mornye_lynae_enabled_test_party",
        "--curriculum-reset-mode",
        "mixed_lynae_route_curriculum",
        "--timesteps",
        "300000",
        "--ent-coef",
        "0.02",
        "--verbose",
        "1",
        "--log-interval",
        "1",
        "--progress-every-steps",
        "10000",
        "--dry-run-train-config",
    ]
    load_model = ROOT / "models" / "maskable_ppo_aemeath_mornye_lynae_bc_init.zip"
    if load_model.exists():
        command.extend(["--load-model", str(load_model)])

    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=60)
    combined_output = f"{result.stdout}\n{result.stderr}"
    if result.returncode == 3 and "dependency-missing" in combined_output:
        print("train_maskable_ppo_progress_cli_smoke_test dependency-missing")
        return
    if result.returncode != 0:
        print(combined_output)
        raise SystemExit(result.returncode)

    required_fragments = [
        '"party_id"',
        "aemeath_mornye_lynae_enabled_test_party",
        '"curriculum_reset_mode"',
        "mixed_lynae_route_curriculum",
        '"timesteps"',
        "300000",
        '"observation_shape"',
        '"action_count"',
        '"model_env_compatibility_check"',
        '"ok"',
        "dry_run_train_config ok",
    ]
    for fragment in required_fragments:
        assert fragment in combined_output, fragment
    assert "Saved model" not in combined_output
    print("train_maskable_ppo_progress_cli_smoke_test ok")


if __name__ == "__main__":
    main()
