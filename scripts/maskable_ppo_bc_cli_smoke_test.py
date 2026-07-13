from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rl.pretrain_maskable_ppo_bc import build_arg_parser, run_pretrain
from scripts.generate_route_demonstrations import generate_route_demonstrations


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        demo_path = Path(temp_dir) / "route_demo.npz"
        model_path = Path(temp_dir) / "bc_model.zip"
        generate_route_demonstrations(output_path=demo_path, repeat=1)
        args = build_arg_parser().parse_args(
            [
                "--party",
                "aemeath_mornye_lynae_enabled_test_party",
                "--demo-path",
                str(demo_path),
                "--model-path",
                str(model_path),
                "--dry-run",
            ]
        )
        plan = run_pretrain(args)
        assert plan["dry_run"] is True
        assert plan["sample_count"] > 0
        assert "swap_to_lynae" in plan["action_distribution"]
        assert "route_distribution" in plan
        assert "character_distribution" in plan
        assert not model_path.exists()
        print("maskable_ppo_bc_cli_smoke_test ok")


if __name__ == "__main__":
    main()
