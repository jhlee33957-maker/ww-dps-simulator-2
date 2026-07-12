from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env.wuwa_env import WuwaDpsEnv
from rl.demo_contract import DEFAULT_DEMO_PATH, load_demo_npz, validate_demo_contract


def main() -> None:
    demo = load_demo_npz(DEFAULT_DEMO_PATH)
    env = WuwaDpsEnv(ROOT / "data", party="aemeath_mornye_lynae_enabled_test_party", initial_active_character="aemeath")
    env.reset(seed=0)
    result = validate_demo_contract(demo, env, root=ROOT)
    assert result["status"] == "ok"
    assert result["sample_count"] == 148
    print("manual_120s_bc_demo_contract_smoke_test ok")


if __name__ == "__main__":
    main()
