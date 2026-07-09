from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rl.train_maskable_ppo import build_arg_parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args(
        [
            "--timesteps",
            "1",
            "--party",
            "aemeath_mornye_lynae_enabled_test_party",
            "--curriculum-reset-mode",
            "mixed_lynae_curriculum",
            "--load-model",
            "models/old.zip",
            "--ent-coef",
            "0.02",
            "--learning-rate",
            "0.0001",
            "--n-steps",
            "256",
            "--batch-size",
            "32",
            "--gamma",
            "0.995",
        ]
    )
    assert args.curriculum_reset_mode == "mixed_lynae_curriculum"
    assert str(args.load_model) == "models\\old.zip" or str(args.load_model) == "models/old.zip"
    assert args.ent_coef == 0.02
    assert args.learning_rate == 0.0001
    assert args.n_steps == 256
    assert args.batch_size == 32
    assert args.gamma == 0.995
    for mode in (
        "aemeath_post_liberation_ready_for_lynae",
        "lynae_after_intro_liberation_used",
        "lynae_kaleidoscopic_ready_after_liberation",
        "mixed_lynae_route_curriculum",
    ):
        parsed = parser.parse_args(["--curriculum-reset-mode", mode])
        assert parsed.curriculum_reset_mode == mode
    print("aemeath_mornye_lynae_curriculum_training_cli_smoke_test ok")


if __name__ == "__main__":
    main()
