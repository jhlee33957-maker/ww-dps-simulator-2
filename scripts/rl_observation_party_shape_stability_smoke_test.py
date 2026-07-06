from __future__ import annotations

import math
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


def make_env(**kwargs) -> WuwaDpsEnv:
    env = WuwaDpsEnv(ROOT / "data", **kwargs)
    env.reset()
    return env


def obs_value(env: WuwaDpsEnv, label: str) -> float:
    labels = env.observation_labels()
    return float(env._get_observation()[labels.index(label)])


def test_party_shapes_match() -> None:
    aemeath = make_env(
        party="aemeath",
        build_profile_overrides={"aemeath": "aemeath_user_real_01"},
    )
    duo = make_env(
        party="aemeath_mornye_test_party",
        build_profile_overrides={"aemeath": "aemeath_user_real_01", "mornye": "mornye_user_real_01"},
    )
    dummy = make_env(selected_character_ids="main,sub,support")
    assert aemeath.observation_space.shape == duo.observation_space.shape == dummy.observation_space.shape
    assert len(aemeath._get_observation()) == len(duo._get_observation()) == len(dummy._get_observation())


def test_empty_and_absent_channels_are_zero_filled() -> None:
    env = make_env(
        party="aemeath",
        build_profile_overrides={"aemeath": "aemeath_user_real_01"},
    )
    assert env.observation_slot_mapping() == {"slot_0": "aemeath", "slot_1": None, "slot_2": None}
    for slot_index in (1, 2):
        for label in env.observation_labels():
            if label.startswith(f"slot_{slot_index}."):
                assert obs_value(env, label) == 0.0, f"{label} should be zero-filled"
    assert obs_value(env, "slot_0.weapon_effect_0_active") == 0.0
    assert obs_value(env, "slot_0.weapon_effect_1_active") == 0.0


def test_values_are_finite_and_reset_stable() -> None:
    env = make_env(
        party="aemeath_mornye_test_party",
        build_profile_overrides={"aemeath": "aemeath_user_real_01", "mornye": "mornye_user_real_01"},
    )
    before_shape = env.observation_space.shape
    before_len = len(env._get_observation())
    for value in env._get_observation():
        numeric = float(value)
        assert math.isfinite(numeric)
        assert numeric >= 0.0
    observation, _ = env.reset()
    assert env.observation_space.shape == before_shape
    assert len(observation) == before_len


def main() -> None:
    test_party_shapes_match()
    test_empty_and_absent_channels_are_zero_filled()
    test_values_are_finite_and_reset_stable()
    print("rl_observation_party_shape_stability_smoke_test ok")


if __name__ == "__main__":
    main()
