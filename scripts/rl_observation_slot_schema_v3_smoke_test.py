from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def install_gymnasium_stub() -> None:
    try:
        import gymnasium  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    class Env:
        def reset(self, seed=None, options=None):
            return None

    class Discrete:
        def __init__(self, n):
            self.n = n

    class Box:
        def __init__(self, low, high, shape, dtype):
            self.low = low
            self.high = high
            self.shape = shape
            self.dtype = dtype

    spaces = types.SimpleNamespace(Discrete=Discrete, Box=Box)
    sys.modules["gymnasium"] = types.SimpleNamespace(Env=Env, spaces=spaces)
    sys.modules["gymnasium.spaces"] = spaces


install_gymnasium_stub()

from env.wuwa_env import WuwaDpsEnv


def main() -> None:
    env = WuwaDpsEnv(
        ROOT / "data",
        party="aemeath_mornye_test_party",
        build_profile_overrides={
            "aemeath": "aemeath_user_real_01",
            "mornye": "mornye_user_real_01",
        },
    )
    env.reset()
    mapping = env.observation_channel_mapping()
    assert env.observation_version == "slot_generic_mechanics_v4"
    assert env.observation_space.shape == (312,)
    assert len(env._get_observation()) == 312
    assert mapping["slot_1.mechanic_state_4"] == "aemeath_forte_enhancement_stacks"
    assert mapping["slot_1.mechanic_state_5"] == "aemeath_trail_no_cost"
    assert mapping["slot_1.mechanic_state_6"] == "aemeath_rupturous_trail"
    assert mapping["slot_1.mechanic_state_7"] == "aemeath_fusion_trail"
    print("rl_observation_slot_schema_v3_smoke_test ok")


if __name__ == "__main__":
    main()
