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
from simulator.buff_system import apply_buff, tick_buffs


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
TEST_ACTION_IDS = (
    "aemeath_resonance_skill",
    "aemeath_resonance_liberation",
    "mornye_resonance_liberation",
    "lynae_resonance_skill",
    "lynae_resonance_liberation",
    "lynae_echo_hyvatia",
)


def make_env() -> WuwaDpsEnv:
    env = WuwaDpsEnv(ROOT / "data", party=PARTY_ID)
    env.reset()
    return env


def observation(env: WuwaDpsEnv) -> dict[str, float]:
    values = env._get_observation()
    return dict(zip(env.observation_labels(), [float(value) for value in values], strict=True))


def assert_normalized(env: WuwaDpsEnv) -> None:
    assert env.observation_space.shape == (312,)
    for value in env._get_observation():
        numeric = float(value)
        assert math.isfinite(numeric)
        assert 0.0 <= numeric <= 1.0


def action_slot_index(env: WuwaDpsEnv, action_id: str) -> int:
    reverse = {action: slot for slot, action in env.observation_action_slot_mapping().items() if action is not None}
    slot = reverse[action_id]
    return int(slot.rsplit("_", 1)[1])


def cooldown_label(env: WuwaDpsEnv, action_id: str) -> str:
    return f"action_slot_{action_slot_index(env, action_id)}.cooldown_remaining_ratio"


def available_label(env: WuwaDpsEnv, action_id: str) -> str:
    return f"action_slot_{action_slot_index(env, action_id)}.available"


def set_active_for_action(env: WuwaDpsEnv, action_id: str) -> None:
    if action_id.startswith("aemeath"):
        env.simulation.state.active_character_id = "aemeath"
    elif action_id.startswith("mornye"):
        env.simulation.state.active_character_id = "mornye"
    elif action_id.startswith("lynae"):
        env.simulation.state.active_character_id = "lynae"


def resolved_cooldown_key_and_duration(env: WuwaDpsEnv, action_id: str) -> tuple[str, float]:
    action = env.simulation.resolve_action(env.simulation.actions[action_id])
    key = action.cooldown_group or action.id
    return key, float(action.cooldown or 0.0)


def test_lynae_liberation_party_buff() -> None:
    env = make_env()
    before = observation(env)
    cooldown_labels = [cooldown_label(env, action_id) for action_id in env.get_policy_action_ids()]

    apply_buff(env.simulation.state, env.simulation.buffs["lynae_liberation_party_damage_amp"], "lynae")
    after = observation(env)

    for slot_index in range(3):
        assert after[f"slot_{slot_index}.runtime_all_damage_amp_scaled"] > before[f"slot_{slot_index}.runtime_all_damage_amp_scaled"]
        assert after[f"slot_{slot_index}.runtime_all_damage_amp_remaining_ratio"] > 0.0
    for label in cooldown_labels:
        assert after[label] == before[label], f"{label} should not change when only a buff is applied"
    assert_normalized(env)


def test_lynae_outro_targeted_buffs_and_expiration() -> None:
    env = make_env()
    before = observation(env)
    env.simulation._apply_specific_character_buff(
        buff_id="lynae_outro_all_damage_amp",
        source_character_id="lynae",
        target_character_id="aemeath",
        application_time=env.simulation.state.current_time,
        metadata={"event_source": "test_lynae_outro"},
    )
    env.simulation._apply_specific_character_buff(
        buff_id="lynae_outro_liberation_damage_amp",
        source_character_id="lynae",
        target_character_id="aemeath",
        application_time=env.simulation.state.current_time,
        metadata={"event_source": "test_lynae_outro"},
    )
    after = observation(env)

    aemeath_slot = 1
    mornye_slot = 0
    lynae_slot = 2
    assert after[f"slot_{aemeath_slot}.runtime_all_damage_amp_scaled"] > before[f"slot_{aemeath_slot}.runtime_all_damage_amp_scaled"]
    assert after[f"slot_{aemeath_slot}.runtime_liberation_damage_amp_scaled"] > before[f"slot_{aemeath_slot}.runtime_liberation_damage_amp_scaled"]
    assert after[f"slot_{aemeath_slot}.runtime_all_damage_amp_remaining_ratio"] > 0.0
    assert after[f"slot_{aemeath_slot}.runtime_liberation_damage_amp_remaining_ratio"] > 0.0
    for slot_index in (mornye_slot, lynae_slot):
        assert after[f"slot_{slot_index}.runtime_all_damage_amp_scaled"] == before[f"slot_{slot_index}.runtime_all_damage_amp_scaled"]
        assert (
            after[f"slot_{slot_index}.runtime_liberation_damage_amp_scaled"]
            == before[f"slot_{slot_index}.runtime_liberation_damage_amp_scaled"]
        )

    tick_buffs(env.simulation.state, 15.0)
    expired = observation(env)
    assert expired[f"slot_{aemeath_slot}.runtime_all_damage_amp_scaled"] == 0.0
    assert expired[f"slot_{aemeath_slot}.runtime_all_damage_amp_remaining_ratio"] == 0.0
    assert expired[f"slot_{aemeath_slot}.runtime_liberation_damage_amp_scaled"] == 0.0
    assert expired[f"slot_{aemeath_slot}.runtime_liberation_damage_amp_remaining_ratio"] == 0.0
    assert_normalized(env)


def test_action_cooldown_slots_and_availability() -> None:
    env = make_env()
    for action_id in TEST_ACTION_IDS:
        set_active_for_action(env, action_id)
        key, cooldown = resolved_cooldown_key_and_duration(env, action_id)
        assert cooldown > 0.0, f"{action_id} should resolve to a cooldown-bearing action"
        env.simulation.state.cooldowns.pop(key, None)
        zero = observation(env)
        env.simulation.state.cooldowns[key] = cooldown / 2.0
        with_cooldown = observation(env)
        slot = action_slot_index(env, action_id)
        assert with_cooldown[f"action_slot_{slot}.present"] == 1.0
        assert with_cooldown[f"action_slot_{slot}.cooldown_remaining_ratio"] > 0.0
        assert with_cooldown[f"action_slot_{slot}.cooldown_remaining_ratio"] != zero[f"action_slot_{slot}.cooldown_remaining_ratio"]
        mask_available = float(env.action_masks()[env.get_policy_action_ids().index(action_id)])
        assert with_cooldown[f"action_slot_{slot}.available"] == mask_available
        env.simulation.state.cooldowns.pop(key, None)
        cleared = observation(env)
        assert cleared[f"action_slot_{slot}.cooldown_remaining_ratio"] == 0.0


def test_resource_unavailable_is_not_cooldown() -> None:
    env = make_env()
    env.simulation.state.active_character_id = "lynae"
    env.simulation.state.resonance_energy["lynae"] = 0.0
    key, _cooldown = resolved_cooldown_key_and_duration(env, "lynae_resonance_liberation")
    env.simulation.state.cooldowns.pop(key, None)
    obs = observation(env)
    assert obs[available_label(env, "lynae_resonance_liberation")] == 0.0
    assert obs[cooldown_label(env, "lynae_resonance_liberation")] == 0.0
    assert_normalized(env)


def main() -> None:
    env = make_env()
    assert env.observation_version == "slot_generic_mechanics_v4"
    assert env.observation_space.shape == (312,)
    test_lynae_liberation_party_buff()
    test_lynae_outro_targeted_buffs_and_expiration()
    test_action_cooldown_slots_and_availability()
    test_resource_unavailable_is_not_cooldown()
    print("rl_observation_delayed_reward_v4_smoke_test ok")


if __name__ == "__main__":
    main()
