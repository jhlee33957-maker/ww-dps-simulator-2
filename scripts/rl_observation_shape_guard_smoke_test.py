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

from env.observation_features import OBSERVATION_VERSION
from env.wuwa_env import WuwaDpsEnv
from rl.evaluate_maskable_ppo import observation_metadata_mismatches


def make_env() -> WuwaDpsEnv:
    env = WuwaDpsEnv(
        ROOT / "data",
        party="aemeath_mornye_test_party",
        initial_active_character="mornye",
        build_profile_overrides={
            "aemeath": "aemeath_user_real_01",
            "mornye": "mornye_user_real_01",
        },
    )
    env.reset()
    return env


def test_shape_is_label_derived_and_deterministic() -> None:
    env = make_env()
    labels = env.observation_labels()
    observation = env._get_observation()
    assert env.observation_version == OBSERVATION_VERSION
    assert env.observation_metadata()["observation_version"] == OBSERVATION_VERSION
    assert len(labels) == len(observation)
    assert env.observation_space.shape == (len(labels),)
    assert env._get_observation_size() == len(labels)

    reset_observation, _ = env.reset()
    reset_labels = env.observation_labels()
    assert len(reset_observation) == len(reset_labels)
    assert env.observation_space.shape == (len(reset_labels),)
    assert len(reset_labels) == len(labels)


def test_observation_values_are_finite_nonnegative() -> None:
    env = make_env()
    for value in env._get_observation():
        numeric = float(value)
        assert math.isfinite(numeric), f"Observation value should be finite, got {numeric}"
        assert numeric >= 0.0, f"Observation value should be non-negative, got {numeric}"
        assert numeric <= 1.0, f"Observation value should be normalized, got {numeric}"


def test_metadata_mismatch_helper_detects_old_shape() -> None:
    env = make_env()
    metadata = env.observation_metadata()
    stale_metadata = dict(metadata)
    stale_metadata["observation_shape"] = [metadata["observation_shape"][0] - 1]
    mismatches = observation_metadata_mismatches(stale_metadata, env)
    assert "observation_shape" in mismatches
    assert mismatches["observation_shape"]["model"] != mismatches["observation_shape"]["evaluation"]

    stale_metadata = dict(metadata)
    stale_metadata["observation_version"] = "off_tune_tune_break_weapon_state_v1"
    mismatches = observation_metadata_mismatches(stale_metadata, env)
    assert "observation_version" in mismatches


def main() -> None:
    test_shape_is_label_derived_and_deterministic()
    test_observation_values_are_finite_nonnegative()
    test_metadata_mismatch_helper_detects_old_shape()
    print("rl_observation_shape_guard_smoke_test ok")


if __name__ == "__main__":
    main()
