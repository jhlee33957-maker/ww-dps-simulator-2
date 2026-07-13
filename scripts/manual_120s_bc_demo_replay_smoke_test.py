from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env.wuwa_env import WuwaDpsEnv
from rl.demo_contract import DEFAULT_DEMO_PATH, load_demo_npz, replay_validate_demo


def make_env() -> WuwaDpsEnv:
    return WuwaDpsEnv(
        ROOT / "data",
        party="aemeath_mornye_lynae_enabled_test_party",
        initial_active_character="aemeath",
        curriculum_reset_mode="none",
    )


def main() -> None:
    demo = load_demo_npz(DEFAULT_DEMO_PATH)
    result = replay_validate_demo(demo, make_env)
    assert result["status"] == "ok"
    assert result["sample_count"] == 148
    assert result["short_wait_substitution_count"] == 0
    print("manual_120s_bc_demo_replay_smoke_test ok")


if __name__ == "__main__":
    main()
