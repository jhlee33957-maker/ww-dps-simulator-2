from __future__ import annotations

from pathlib import Path
import sys
import types


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
from rl.evaluate_maskable_ppo import observation_metadata_mismatches


def main() -> None:
    env = WuwaDpsEnv(ROOT / "data", party="aemeath_mornye_lynae_enabled_test_party")
    stale = dict(env.observation_metadata())
    stale["observation_version"] = "slot_generic_mechanics_v4"
    stale["observation_shape"] = [312]
    stale["observation_labels"] = stale["observation_labels"][:-2]
    mismatches = observation_metadata_mismatches(stale, env)
    assert "observation_version" in mismatches
    assert "observation_shape" in mismatches
    assert "observation_labels" in mismatches
    print("rl_observation_v4_incompatibility_smoke_test ok")


if __name__ == "__main__":
    main()
