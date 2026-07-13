from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.observation_features import MAX_POLICY_ACTION_SLOTS, OBSERVATION_VERSION, build_observation_labels
from env.wuwa_env import WuwaDpsEnv


def main() -> None:
    env = WuwaDpsEnv(data_dir="data", party="aemeath_mornye_lynae_enabled_test_party")
    assert env.action_ids[23] == "mornye_echo_reactor_husk"
    assert env.action_ids[24] == "aemeath_echo_sigillum"
    assert len(env.action_ids) == 25
    assert MAX_POLICY_ACTION_SLOTS == 32
    assert OBSERVATION_VERSION == "slot_generic_mechanics_v5"
    assert len(build_observation_labels()) == 314
    print("mornye_aemeath_active_echo_ui_action_list_smoke_test ok")


if __name__ == "__main__":
    main()
