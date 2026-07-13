from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rl.demo_contract import DEFAULT_DEMO_PATH, alias_audit, load_demo_npz


def main() -> None:
    demo = load_demo_npz(DEFAULT_DEMO_PATH)
    result = alias_audit(demo)
    assert result["status"] == "ok"
    assert result["unique_observation_mask_keys"] == 148
    assert result["conflicting_target_key_count"] == 0
    print("manual_120s_bc_demo_alias_smoke_test ok")


if __name__ == "__main__":
    main()
