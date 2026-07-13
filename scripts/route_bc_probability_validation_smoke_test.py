from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.generate_route_demonstrations import generate_route_demonstrations
from scripts.route_bc_probability_validation import run_validation


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        demo_path = Path(temp_dir) / "route_demo_v2.npz"
        generate_route_demonstrations(
            route_set_id="aemeath_mornye_lynae_balanced_route_warm_start_v2",
            output_path=demo_path,
            repeat=1,
        )
        report = run_validation(demo_path=demo_path)
        assert report["status"] == "model_not_loaded"
        assert report["sample_count"] > 0
        assert "normal_start_to_lynae_intro_entry" in report["route_sample_counts"]
        assert "swap_to_lynae" in report["action_counts"]
        model_path = ROOT / "models" / "maskable_ppo_aemeath_mornye_lynae_bc_init.zip"
        if model_path.exists():
            model_report = run_validation(demo_path=demo_path, model_path=model_path)
            if model_report["model_status"] == "loaded":
                assert "mean_demonstrated_action_probability" in model_report
                assert "overgeneralization_probe" in model_report
        print("route_bc_probability_validation_smoke_test ok")


if __name__ == "__main__":
    main()
