from __future__ import annotations

import copy
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


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
TEST_CASES = (
    ("aemeath_resonance_skill", "mornye"),
    ("aemeath_resonance_liberation", "mornye"),
    ("mornye_resonance_skill", "aemeath"),
    ("mornye_resonance_liberation", "aemeath"),
    ("lynae_resonance_skill", "aemeath"),
    ("lynae_resonance_liberation", "aemeath"),
    ("lynae_echo_hyvatia", "aemeath"),
)


def make_env() -> WuwaDpsEnv:
    env = WuwaDpsEnv(ROOT / "data", party=PARTY_ID)
    env.reset()
    return env


def observation(env: WuwaDpsEnv) -> dict[str, float]:
    return dict(zip(env.observation_labels(), [float(value) for value in env._get_observation()], strict=True))


def action_slot_index(env: WuwaDpsEnv, action_id: str) -> int:
    reverse = {action: slot for slot, action in env.observation_action_slot_mapping().items() if action is not None}
    return int(reverse[action_id].rsplit("_", 1)[1])


def snapshot_state(env: WuwaDpsEnv) -> dict:
    state = env.simulation.state
    return {
        "active_character_id": state.active_character_id,
        "character_mechanics_state": copy.deepcopy(state.character_mechanics_state),
        "resonance_energy": copy.deepcopy(state.resonance_energy),
        "concerto_energy": copy.deepcopy(state.concerto_energy),
        "cooldowns": copy.deepcopy(state.cooldowns),
    }


def cooldown_key_and_duration(env: WuwaDpsEnv, action_id: str) -> tuple[str, float, str]:
    action = env.simulation.policy_actions[action_id]
    resolved = env.simulation.resolve_action_for_character(action, action.character_id)
    key = resolved.cooldown_group or resolved.id
    return key, float(resolved.cooldown or 0.0), resolved.id


def main() -> None:
    env = make_env()
    assert env.observation_version == "slot_generic_mechanics_v4"
    assert env.observation_space.shape == (312,)

    observed_unavailable_with_cooldown = False
    expected_resolutions = {
        "aemeath_resonance_skill": ("aemeath_form_switch_to_mech_normal", 1.0, "aemeath_form_switch"),
        "aemeath_resonance_liberation": ("aemeath_liberation_overdrive", 25.0, "aemeath_overdrive"),
        "mornye_resonance_skill": ("mornye_skill_expectation_error", 5.0, "mornye_expectation_error"),
        "mornye_resonance_liberation": ("mornye_liberation_critical_protocol", 25.0, "mornye_liberation_critical_protocol"),
        "lynae_resonance_skill": ("lynae_resonance_skill_palette", 6.0, "lynae_resonance_skill"),
        "lynae_resonance_liberation": (
            "lynae_resonance_liberation_prismatic_overblast",
            25.0,
            "lynae_resonance_liberation",
        ),
        "lynae_echo_hyvatia": ("lynae_echo_hyvatia", 20.0, "lynae_echo_hyvatia"),
    }

    for action_id, active_character_id in TEST_CASES:
        env = make_env()
        env.simulation.state.active_character_id = active_character_id
        key, cooldown, resolved_id = cooldown_key_and_duration(env, action_id)
        expected_id, expected_cooldown, expected_key = expected_resolutions[action_id]
        assert resolved_id == expected_id
        assert cooldown == expected_cooldown
        assert key == expected_key

        env.simulation.state.cooldowns[key] = cooldown / 2.0
        before = snapshot_state(env)
        obs = observation(env)
        after = snapshot_state(env)
        assert after == before, f"observation mutated state for {action_id}"
        assert env.simulation.state.active_character_id == active_character_id

        slot = action_slot_index(env, action_id)
        mask_available = float(env.action_masks()[env.get_policy_action_ids().index(action_id)])
        assert obs[f"action_slot_{slot}.present"] == 1.0
        assert obs[f"action_slot_{slot}.available"] == mask_available
        assert obs[f"action_slot_{slot}.cooldown_remaining_ratio"] == 0.5
        if mask_available == 0.0:
            observed_unavailable_with_cooldown = True

        env.simulation.state.cooldowns.pop(key, None)
        cleared = observation(env)
        assert cleared[f"action_slot_{slot}.cooldown_remaining_ratio"] == 0.0

    assert observed_unavailable_with_cooldown
    print("rl_observation_off_field_cooldown_v4_smoke_test ok")


if __name__ == "__main__":
    main()
