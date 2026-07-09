from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env.wuwa_env import WuwaDpsEnv
from scripts.generate_route_demonstrations import generate_route_demonstrations


ROUTE_SET_ID = "aemeath_mornye_lynae_balanced_route_warm_start_v2"


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "route_demo_v2.npz"
        generate_route_demonstrations(route_set_id=ROUTE_SET_ID, output_path=output, repeat=1)
        with np.load(output, allow_pickle=False) as data:
            metadata = json.loads(str(data["metadata_json"]))
            action_indices = np.asarray(data["action_indices"])
            action_masks = np.asarray(data["action_masks"])
            observations_shape = list(data["observations"].shape[1:])
            action_ids = set(map(str, data["action_ids"]))
            route_ids = list(map(str, data["route_ids"]))
            active_characters = list(map(str, data["active_characters"]))
        for row_index, action_index in enumerate(action_indices):
            assert action_masks[row_index, action_index], f"row {row_index} action was invalid under mask"
        env = WuwaDpsEnv(ROOT / "data", party=metadata["party_id"])
        assert observations_shape == list(env.observation_space.shape)
        assert metadata["non_lynae_baseline_samples"] > 0
        assert metadata["lynae_route_samples"] > 0
        assert "normal_start_aemeath_mornye_baseline" in route_ids
        assert "normal_start_to_lynae_intro_entry" in route_ids
        assert route_ids[0] == "normal_start_aemeath_mornye_baseline"
        assert active_characters[0] == "mornye"
        assert "swap_to_lynae" in action_ids
        assert "lynae_spark_collision" in action_ids
        assert "lynae_polychrome_leap" in action_ids
        assert "lynae_visual_impact" in action_ids
        print("aemeath_mornye_lynae_balanced_route_demo_validity_smoke_test ok")


if __name__ == "__main__":
    main()
