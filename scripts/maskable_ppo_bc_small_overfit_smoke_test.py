from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rl.pretrain_maskable_ppo_bc import build_arg_parser, run_pretrain
from scripts.aemeath_mornye_lynae_policy_probability_diagnostic import run_policy_probability_diagnostic
from scripts.generate_route_demonstrations import generate_route_demonstrations


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        demo_path = Path(temp_dir) / "route_demo.npz"
        model_path = Path(temp_dir) / "bc_model.zip"
        generate_route_demonstrations(output_path=demo_path, repeat=2)
        args = build_arg_parser().parse_args(
            [
                "--party",
                "aemeath_mornye_lynae_enabled_test_party",
                "--demo-path",
                str(demo_path),
                "--model-path",
                str(model_path),
                "--epochs",
                "2",
                "--batch-size",
                "16",
                "--learning-rate",
                "0.0003",
                "--seed",
                "7",
            ]
        )
        try:
            run_pretrain(args)
        except SystemExit as exc:
            if exc.code == 3:
                print("maskable_ppo_bc_small_overfit_smoke_test dependency-missing")
                return
            raise
        assert model_path.exists()
        sidecar = Path(str(model_path) + ".bc_metadata.json")
        metadata = json.loads(sidecar.read_text(encoding="utf-8"))
        assert metadata["route_ids"]
        assert metadata["route_sample_counts"]
        assert metadata["action_counts"]
        assert metadata["character_counts"]
        assert metadata["no_character_specific_usage_reward_bonus"] is True
        assert metadata["reward_formula_unchanged"] is True
        report = run_policy_probability_diagnostic(model_path=model_path, route_demo_path=demo_path)
        demo_report = report["route_demo_probability_report"]
        assert demo_report["status"] == "ok"
        assert demo_report["mean_demonstrated_action_probability"] > 0.05
        swap_summary = demo_report["action_wise_probabilities"]["swap_to_lynae"]
        assert swap_summary["mean"] > 0.05
        print("maskable_ppo_bc_small_overfit_smoke_test ok")


if __name__ == "__main__":
    main()
