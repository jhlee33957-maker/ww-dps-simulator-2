from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env.wuwa_env import WuwaDpsEnv


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"


def main() -> None:
    env = WuwaDpsEnv(data_dir=ROOT / "data", party=PARTY_ID)
    assert env.get_selected_party_character_ids() == ["mornye", "aemeath", "lynae"]
    assert "dummy_sub_dps" not in env.get_selected_party_character_ids()

    action_ids = set(env.get_policy_action_ids())
    assert any(action_id.startswith("mornye_") for action_id in action_ids)
    assert any(action_id.startswith("aemeath_") for action_id in action_ids)
    assert any(action_id.startswith("lynae_") for action_id in action_ids)
    for action_id in {
        "lynae_basic_attack",
        "lynae_resonance_skill",
        "lynae_resonance_liberation",
        "lynae_spark_collision",
        "lynae_polychrome_leap",
        "lynae_visual_impact",
    }:
        assert action_id in action_ids
    assert "swap_to_lynae" in action_ids
    print("aemeath_mornye_lynae_rl_action_space_smoke_test ok")


if __name__ == "__main__":
    main()
