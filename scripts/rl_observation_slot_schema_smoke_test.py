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


FORBIDDEN_LABEL_PARTS = (
    "aemeath",
    "mornye",
    "starfield",
    "trailblazing",
    "halo",
    "particle_jet",
    "starburst",
)


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


def test_slot_schema_labels_and_metadata() -> None:
    env = make_env()
    labels = env.observation_labels()
    metadata = env.observation_metadata()
    assert env.observation_version == "slot_generic_mechanics_v3"
    assert metadata["deprecated_observation_version"] == "off_tune_tune_break_weapon_state_v1"
    assert metadata["max_party_slots"] == 3
    for forbidden in FORBIDDEN_LABEL_PARTS:
        assert not any(forbidden in label for label in labels), f"Found hardcoded label part {forbidden}"
    for slot_index in range(3):
        assert f"slot_{slot_index}.present" in labels
        assert f"slot_{slot_index}.weapon_effect_1_cooldown_ratio" in labels
    assert "global.target_marker_0_active" in labels
    assert "global.target_marker_1_value_scaled" in labels
    assert len(env._get_observation()) == len(labels)
    assert env.observation_space.shape == (len(labels),)


def test_current_channel_mapping() -> None:
    env = make_env()
    mapping = env.observation_channel_mapping()
    slot_mapping = env.observation_slot_mapping()
    assert slot_mapping == {"slot_0": "mornye", "slot_1": "aemeath", "slot_2": "dummy_sub_dps"}
    assert mapping["global.target_marker_0"] == "observation_marker"
    assert mapping["global.target_marker_1"] == "interfered_marker"
    assert mapping["slot_0.echo_effect_0"] == "mornye_halo_of_starry_radiance_5set"
    assert mapping["slot_0.weapon_effect_0"] == "starfield_calibrator_concerto_restore"
    assert mapping["slot_0.weapon_effect_1"] == "starfield_calibrator_party_crit_damage"
    assert mapping["slot_0.tune_response_0"] == "mornye_particle_jet"
    assert mapping["slot_1.echo_effect_0"] == "aemeath_trailblazing_star_5set"
    assert mapping["slot_1.tune_response_0"] == "aemeath_starburst"
    assert mapping["slot_1.mechanic_state_3"] == "aemeath_heavenfall_unbound_or_stardust_resonance"
    assert mapping["slot_1.mechanic_state_4"] == "aemeath_forte_enhancement_stacks"
    assert mapping["slot_1.mechanic_state_5"] == "aemeath_trail_no_cost"
    assert mapping["slot_1.mechanic_state_6"] == "aemeath_rupturous_trail"
    assert mapping["slot_1.mechanic_state_7"] == "aemeath_fusion_trail"


def main() -> None:
    test_slot_schema_labels_and_metadata()
    test_current_channel_mapping()
    print("rl_observation_slot_schema_smoke_test ok")


if __name__ == "__main__":
    main()
