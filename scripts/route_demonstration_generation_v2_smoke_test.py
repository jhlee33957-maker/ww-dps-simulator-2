from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.generate_route_demonstrations import generate_route_demonstrations


ROUTE_SET_ID = "aemeath_mornye_lynae_balanced_route_warm_start_v2"
REQUIRED_ROUTES = {
    "normal_start_aemeath_mornye_baseline",
    "normal_start_to_aemeath_concerto_ready",
    "normal_start_to_lynae_intro_entry",
    "aemeath_concerto_to_lynae_intro_exact",
    "lynae_after_intro_core_no_liberation",
    "lynae_after_intro_liberation_core",
    "lynae_skill_to_spark_bridge",
    "lynae_spark_to_visual_bridge",
    "lynae_full_branch_with_exit",
}


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "route_demo_v2.npz"
        metadata = generate_route_demonstrations(route_set_id=ROUTE_SET_ID, output_path=output, repeat=1)
        assert output.exists()
        with np.load(output, allow_pickle=False) as data:
            saved_metadata = json.loads(str(data["metadata_json"]))
            route_ids = set(map(str, data["route_ids"]))
            action_ids = set(map(str, data["action_ids"]))
        assert metadata["route_set_id"] == ROUTE_SET_ID
        assert saved_metadata["route_set_id"] == ROUTE_SET_ID
        assert REQUIRED_ROUTES.issubset(route_ids)
        assert any(not action_id.startswith("lynae_") and action_id != "swap_to_lynae" for action_id in action_ids)
        assert any(action_id.startswith("lynae_") or action_id == "swap_to_lynae" for action_id in action_ids)
        for action_id in ("swap_to_lynae", "lynae_spark_collision", "lynae_polychrome_leap", "lynae_visual_impact"):
            assert action_id in action_ids
        assert saved_metadata["warnings"] == []
        print("route_demonstration_generation_v2_smoke_test ok")


if __name__ == "__main__":
    main()
