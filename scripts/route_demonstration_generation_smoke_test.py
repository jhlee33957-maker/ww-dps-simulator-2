from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.generate_route_demonstrations import generate_route_demonstrations


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "route_demo.npz"
        metadata = generate_route_demonstrations(output_path=output, repeat=1)
        assert output.exists()
        with np.load(output, allow_pickle=False) as data:
            saved_metadata = json.loads(str(data["metadata_json"]))
            assert metadata["total_samples"] == saved_metadata["total_samples"]
            assert saved_metadata["route_set_id"] == "aemeath_mornye_lynae_route_warm_start"
            assert saved_metadata["total_samples"] > 0
            assert data["observations"].shape[0] == data["action_indices"].shape[0]
        print("route_demonstration_generation_smoke_test ok")


if __name__ == "__main__":
    main()
