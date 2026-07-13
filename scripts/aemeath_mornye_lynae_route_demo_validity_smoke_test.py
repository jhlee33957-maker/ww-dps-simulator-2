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


REQUIRED_ACTIONS = {
    "swap_to_lynae",
    "lynae_resonance_liberation",
    "lynae_resonance_skill",
    "lynae_spark_collision",
    "lynae_polychrome_leap",
    "lynae_visual_impact",
}


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "route_demo.npz"
        generate_route_demonstrations(output_path=output, repeat=1)
        with np.load(output, allow_pickle=False) as data:
            metadata = json.loads(str(data["metadata_json"]))
            action_ids = set(map(str, data["action_ids"]))
            assert REQUIRED_ACTIONS.issubset(action_ids)
            action_indices = np.asarray(data["action_indices"])
            action_masks = np.asarray(data["action_masks"])
            observations_shape = list(data["observations"].shape[1:])
            visual_routes = [
                route_id
                for route_id, action_id in zip(map(str, data["route_ids"]), map(str, data["action_ids"]), strict=True)
                if action_id == "lynae_visual_impact"
            ]
        for row_index, action_index in enumerate(action_indices):
            assert action_masks[row_index, action_index], f"row {row_index} action was invalid under mask"
        env = WuwaDpsEnv(ROOT / "data", party=metadata["party_id"])
        assert observations_shape == list(env.observation_space.shape)
        assert {"lynae_core_after_liberation", "lynae_kp_core", "lynae_full_branch"}.issubset(set(visual_routes))
        print("aemeath_mornye_lynae_route_demo_validity_smoke_test ok")


if __name__ == "__main__":
    main()
