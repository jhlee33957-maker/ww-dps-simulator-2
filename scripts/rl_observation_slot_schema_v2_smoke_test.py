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


EXPECTED_V4_SHAPE = (312,)
OLD_V3_SHAPE = (204,)
OLD_V2_SHAPE = (186,)
OLD_V1_SHAPE = (168,)


def make_env(party: str) -> WuwaDpsEnv:
    env = WuwaDpsEnv(
        ROOT / "data",
        party=party,
        build_profile_overrides={
            "aemeath": "aemeath_user_real_01",
            "mornye": "mornye_user_real_01",
        },
    )
    env.reset()
    return env


def test_observation_schema_v4_shape_and_mapping() -> None:
    env = make_env("aemeath_mornye_test_party")
    labels = env.observation_labels()
    mapping = env.observation_channel_mapping()
    assert env.observation_version == "slot_generic_mechanics_v4"
    assert env.observation_space.shape == EXPECTED_V4_SHAPE
    assert env.observation_space.shape != OLD_V3_SHAPE
    assert env.observation_space.shape != OLD_V2_SHAPE
    assert env.observation_space.shape != OLD_V1_SHAPE
    assert len(env._get_observation()) == len(labels) == EXPECTED_V4_SHAPE[0]
    assert mapping["slot_1.mechanic_state_3"] == "aemeath_heavenfall_unbound_or_stardust_resonance"
    assert mapping["slot_1.mechanic_state_4"] == "aemeath_forte_enhancement_stacks"
    assert mapping["slot_1.mechanic_state_5"] == "aemeath_trail_no_cost"
    assert mapping["slot_1.mechanic_state_6"] == "aemeath_rupturous_trail"
    assert mapping["slot_1.mechanic_state_7"] == "aemeath_fusion_trail"
    for label in (
        "slot_1.mechanic_state_4_active",
        "slot_1.mechanic_state_4_remaining_ratio",
        "slot_1.mechanic_state_4_value_scaled",
        "slot_1.mechanic_state_5_active",
        "slot_1.mechanic_state_5_remaining_ratio",
        "slot_1.mechanic_state_5_value_scaled",
        "slot_1.mechanic_state_6_active",
        "slot_1.mechanic_state_6_remaining_ratio",
        "slot_1.mechanic_state_6_value_scaled",
        "slot_1.mechanic_state_7_active",
        "slot_1.mechanic_state_7_remaining_ratio",
        "slot_1.mechanic_state_7_value_scaled",
    ):
        assert label in labels


def test_party_shape_stays_stable_with_new_channels() -> None:
    aemeath = make_env("aemeath")
    duo = make_env("aemeath_mornye_test_party")
    assert aemeath.observation_space.shape == duo.observation_space.shape == EXPECTED_V4_SHAPE


def main() -> None:
    test_observation_schema_v4_shape_and_mapping()
    test_party_shape_stays_stable_with_new_channels()
    print("rl_observation_slot_schema_v2_smoke_test ok (v4 schema)")


if __name__ == "__main__":
    main()
