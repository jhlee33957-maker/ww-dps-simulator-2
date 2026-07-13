from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rl.demo_contract import SAMPLE_COUNT, load_demo_npz
from scripts.generate_manual_120s_bc_demonstration import generate_manual_120s_bc_demonstration


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "manual_120s_bc_demo.npz"
        metadata = generate_manual_120s_bc_demonstration(output)
        demo = load_demo_npz(output)
        assert metadata["sample_count"] == SAMPLE_COUNT
        assert demo["observations"].shape == (148, 314)
        assert demo["action_masks"].shape == (148, 25)
        assert demo["metadata"]["route_id"] == "manual_120s_primary_v105"
    print("manual_120s_bc_demo_generation_smoke_test ok")


if __name__ == "__main__":
    main()
