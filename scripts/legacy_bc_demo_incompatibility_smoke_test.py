from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env.wuwa_env import WuwaDpsEnv
from rl.demo_contract import DemoContractError, LEGACY_DEMO_PATHS, load_demo_npz, validate_legacy_demo_rejected
from rl.pretrain_maskable_ppo_bc import _validate_demo_contract


def main() -> None:
    env = WuwaDpsEnv(ROOT / "data", party="aemeath_mornye_lynae_enabled_test_party", initial_active_character="aemeath")
    env.reset(seed=0)
    checked = 0
    for path in LEGACY_DEMO_PATHS:
        if not path.exists():
            continue
        rejection = validate_legacy_demo_rejected(path)
        assert rejection["status"] == "rejected"
        assert rejection["actual_observation_shape"] == [204]
        assert rejection["actual_action_count"] == 23
        demo = load_demo_npz(path)
        try:
            _validate_demo_contract(demo, env, demo_path=path)
        except DemoContractError as exc:
            message = str(exc)
            assert "incompatible legacy BC demo" in message
            assert "actual observation shape [204]" in message
            assert "action count 23" in message
        else:
            raise AssertionError(f"legacy demo was not rejected: {path}")
        checked += 1
    assert checked >= 1
    print("legacy_bc_demo_incompatibility_smoke_test ok")


if __name__ == "__main__":
    main()
