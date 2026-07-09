from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.generate_route_demonstrations import generate_route_demonstrations


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        demo_path = Path(temp_dir) / "route_demo_v2.npz"
        output_prefix = Path(temp_dir) / "tmp_bc_refresh_plan"
        generate_route_demonstrations(
            route_set_id="aemeath_mornye_lynae_balanced_route_warm_start_v2",
            output_path=demo_path,
            repeat=1,
        )
        command = [
            sys.executable,
            str(ROOT / "rl" / "train_maskable_ppo_bc_refresh_plan.py"),
            "--party",
            "aemeath_mornye_lynae_enabled_test_party",
            "--demo-path",
            str(demo_path),
            "--initial-model",
            str(ROOT / "models" / "maskable_ppo_aemeath_mornye_lynae_bc_init.zip"),
            "--output-prefix",
            str(output_prefix),
            "--dry-run-plan",
        ]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=60)
        output = f"{result.stdout}\n{result.stderr}"
        if result.returncode != 0:
            print(output)
            raise SystemExit(result.returncode)
        for phrase in (
            "PPO cycle",
            "BC refresh",
            "final none stage",
            "reward_formula_unchanged",
            "no_character_specific_usage_reward_bonus",
        ):
            assert phrase in output, phrase
        assert Path(f"{output_prefix}_plan_metadata.json").exists()
        print("bc_refresh_plan_cli_smoke_test ok")


if __name__ == "__main__":
    main()
