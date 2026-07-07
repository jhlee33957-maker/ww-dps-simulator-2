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

from env.observation_features import OBSERVATION_VERSION
from env.wuwa_env import WuwaDpsEnv


DATA_DIR = ROOT / "data"
BUILD_PROFILES = {
    "aemeath": "aemeath_user_real_01",
    "mornye": "mornye_user_real_01",
}


def make_env(**kwargs) -> WuwaDpsEnv:
    options = {
        "data_dir": DATA_DIR,
        "party": "aemeath_mornye_test_party",
        "initial_active_character": "mornye",
        "build_profile_overrides": BUILD_PROFILES,
    }
    options.update(kwargs)
    env = WuwaDpsEnv(**options)
    env.reset()
    return env


def obs_value(env: WuwaDpsEnv, label: str) -> float:
    labels = env.observation_labels()
    return float(env._get_observation()[labels.index(label)])


def channel_for(env: WuwaDpsEnv, mapped_name: str) -> str:
    matches = [channel for channel, name in env.observation_channel_mapping().items() if name == mapped_name]
    assert matches, f"Missing channel mapping for {mapped_name}"
    return matches[0]


def assert_positive(env: WuwaDpsEnv, label: str) -> None:
    value = obs_value(env, label)
    assert value > 0.0, f"{label} should be positive, got {value}"


def test_labels_shape_and_metadata() -> None:
    env = make_env()
    labels = env.observation_labels()
    observation = env._get_observation()
    metadata = env.observation_metadata()
    assert metadata["observation_version"] == OBSERVATION_VERSION
    assert metadata["max_party_slots"] == 3
    assert metadata["observation_shape"] == list(env.observation_space.shape)
    assert metadata["observation_labels"] == labels
    assert len(observation) == len(labels)
    assert env.observation_space.shape == (len(labels),)
    assert "global.target_marker_0" in metadata["observation_channel_mapping"]
    assert "global.target_marker_1" in metadata["observation_channel_mapping"]
    assert channel_for(env, "aemeath_forte_enhancement_stacks") == "slot_1.mechanic_state_4"
    assert channel_for(env, "aemeath_trail_no_cost") == "slot_1.mechanic_state_5"
    assert channel_for(env, "aemeath_rupturous_trail") == "slot_1.mechanic_state_6"
    assert channel_for(env, "aemeath_fusion_trail") == "slot_1.mechanic_state_7"
    assert metadata["observation_slot_mapping"]["slot_0"] == "mornye"
    assert metadata["observation_slot_mapping"]["slot_1"] == "aemeath"


def test_off_tune_mistune_and_cooldown_state() -> None:
    env = make_env()
    assert obs_value(env, "global.enemy_off_tune_ratio") == 0.0
    aemeath_mode_channel = channel_for(env, "aemeath_resonance_mode")
    assert obs_value(env, f"{aemeath_mode_channel}_active") == 1.0
    assert obs_value(env, f"{aemeath_mode_channel}_value_scaled") == 1.0

    assert env.simulation.execute_action("mornye_basic_attack")
    assert_positive(env, "global.enemy_off_tune_ratio")
    assert_positive(env, "global.enemy_off_tune_current_scaled")
    assert_positive(env, "global.current_off_tune_buildup_rate_scaled")

    state = env.simulation.state
    state.enemy_off_tune_current = state.enemy_off_tune_max
    state.enemy_mistune_active = True
    state.enemy_tune_break_available = True
    assert obs_value(env, "global.enemy_mistune_active") == 1.0
    assert obs_value(env, "global.enemy_tune_break_available") == 1.0

    state.enemy_tune_break_cooldown_remaining = 1.5
    state.enemy_tune_break_cooldown_seconds = 3.0
    assert obs_value(env, "global.enemy_tune_break_cooldown_ratio") == 0.5
    assert obs_value(env, "global.off_tune_accumulation_blocked_by_tune_break_cooldown") == 1.0


def test_marker_interfered_and_response_state() -> None:
    env = make_env()
    sim = env.simulation
    sim.characters["mornye"].energy_regen = 2.7944
    sim.state.character_states["mornye"]["energy_regen"] = 2.7944
    sim.state.character_mechanics_state["mornye"]["mode"] = "wide_field_observation"
    sim.state.character_mechanics_state["mornye"]["relative_momentum"] = 100.0
    assert sim.execute_action("mornye_heavy_attack")
    assert sim.timeline[-1].observation_marker_applied is True
    observation_marker_channel = channel_for(env, "observation_marker")
    assert obs_value(env, f"{observation_marker_channel}_active") == 1.0
    assert obs_value(env, f"{observation_marker_channel}_remaining_ratio") > 0.0

    sim.state.enemy_tune_break_available = True
    sim.state.enemy_mistune_active = True
    sim.state.enemy_tune_break_cooldown_remaining = 0.0
    sim.state.target_tune_shift_state = "tune_rupture_shifting"
    sim.state.target_tune_shift_remaining = 8.0
    assert sim.execute_action("mornye_tune_break")
    assert sim.timeline[-1].mornye_interfered_marker_applied is True
    interfered_marker_channel = channel_for(env, "interfered_marker")
    assert obs_value(env, f"{interfered_marker_channel}_active") == 1.0
    assert obs_value(env, f"{interfered_marker_channel}_value_scaled") == 1.0
    assert_positive(env, f"{channel_for(env, 'aemeath_starburst')}_cooldown_ratio")
    assert_positive(env, f"{channel_for(env, 'mornye_particle_jet')}_cooldown_ratio")


def test_fields_echo_weapon_and_trailblazing_state() -> None:
    env = make_env()
    sim = env.simulation
    sim.state.character_states["mornye"]["rest_mass_energy"] = 100.0
    assert sim.execute_action("mornye_heavy_attack")
    syntony_channel = channel_for(env, "mornye_syntony_field")
    halo_channel = channel_for(env, "mornye_halo_of_starry_radiance_5set")
    starfield_buff_channel = channel_for(env, "starfield_calibrator_party_crit_damage")
    assert obs_value(env, f"{syntony_channel}_active") == 1.0
    assert obs_value(env, f"{halo_channel}_active") == 1.0
    assert_positive(env, f"{halo_channel}_value_scaled")
    assert obs_value(env, f"{starfield_buff_channel}_active") == 1.0
    assert_positive(env, f"{starfield_buff_channel}_value_scaled")

    sim.state.resonance_energy["mornye"] = sim.characters["mornye"].resonance_energy_max
    assert sim.execute_action("mornye_resonance_liberation")
    high_syntony_channel = channel_for(env, "mornye_high_syntony_field")
    assert obs_value(env, f"{high_syntony_channel}_active") == 1.0
    assert obs_value(env, f"{high_syntony_channel}_value_scaled") == 1.0

    weapon_env = make_env()
    assert weapon_env.simulation.execute_action("mornye_resonance_skill")
    assert_positive(weapon_env, f"{channel_for(weapon_env, 'starfield_calibrator_concerto_restore')}_cooldown_ratio")

    trail_env = WuwaDpsEnv(
        DATA_DIR,
        party="aemeath",
        initial_active_character="aemeath",
        build_profile_overrides={"aemeath": "aemeath_user_real_01"},
        transition_config={"mechanics": {"aemeath": {"aemeath_resonance_mode": "fusion_burst"}}},
    )
    trail_env.reset()
    assert obs_value(trail_env, f"{channel_for(trail_env, 'aemeath_resonance_mode')}_value_scaled") == 0.5
    assert trail_env.simulation.execute_action("aemeath_basic_form_stage_3")
    trail_channel = channel_for(trail_env, "aemeath_trailblazing_star_5set")
    assert obs_value(trail_env, f"{trail_channel}_active") == 1.0
    assert_positive(trail_env, f"{trail_channel}_remaining_ratio")


def main() -> None:
    test_labels_shape_and_metadata()
    test_off_tune_mistune_and_cooldown_state()
    test_marker_interfered_and_response_state()
    test_fields_echo_weapon_and_trailblazing_state()
    print("rl_observation_global_mechanics_smoke_test ok")


if __name__ == "__main__":
    main()
