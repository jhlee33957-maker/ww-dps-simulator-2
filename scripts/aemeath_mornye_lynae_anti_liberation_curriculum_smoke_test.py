from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env.wuwa_env import WuwaDpsEnv


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"


def is_valid(env: WuwaDpsEnv, action_id: str) -> bool:
    return env.simulation.is_action_available(env.simulation.actions[action_id])


def main() -> None:
    aemeath_env = WuwaDpsEnv(
        ROOT / "data",
        party=PARTY_ID,
        curriculum_reset_mode="aemeath_post_liberation_ready_for_lynae",
    )
    _obs, info = aemeath_env.reset(seed=13)
    assert info["curriculum_reset_mode"] == "aemeath_post_liberation_ready_for_lynae"
    assert info["training_only"] is True
    assert info["pre_roll_type"] == "artificial_cooldown_energy_adjustment"
    assert aemeath_env.simulation.state.active_character_id == "aemeath"
    assert aemeath_env.simulation.state.character_states["aemeath"]["concerto_energy"] == 100.0
    assert aemeath_env.simulation.state.character_states["aemeath"]["concerto_ready"] is True
    assert is_valid(aemeath_env, "swap_to_lynae")
    assert not is_valid(aemeath_env, "aemeath_resonance_liberation")

    intro_env = WuwaDpsEnv(
        ROOT / "data",
        party=PARTY_ID,
        curriculum_reset_mode="lynae_after_intro_liberation_used",
    )
    _obs, info = intro_env.reset(seed=13)
    lynae_state = intro_env.simulation.state.character_mechanics_state["lynae"]
    assert info["curriculum_reset_mode"] == "lynae_after_intro_liberation_used"
    assert info["training_only"] is True
    assert info["pre_roll_type"] == "source_consistent_pre_roll"
    assert intro_env.simulation.state.active_character_id == "lynae"
    assert not is_valid(intro_env, "lynae_resonance_liberation")
    assert is_valid(intro_env, "lynae_resonance_skill")
    assert lynae_state["overflow"] >= 100.0
    assert lynae_state["photocromic_flux_active"] is True

    kp_env = WuwaDpsEnv(
        ROOT / "data",
        party=PARTY_ID,
        curriculum_reset_mode="lynae_kaleidoscopic_ready_after_liberation",
    )
    _obs, info = kp_env.reset(seed=13)
    kp_state = kp_env.simulation.state.character_mechanics_state["lynae"]
    assert info["curriculum_reset_mode"] == "lynae_kaleidoscopic_ready_after_liberation"
    assert info["training_only"] is True
    assert kp_env.simulation.state.active_character_id == "lynae"
    assert kp_state["kaleidoscopic_parade_remaining"] > 0.0
    assert kp_state["lumiflow"] > 0.0
    assert is_valid(kp_env, "lynae_polychrome_leap")
    assert not is_valid(kp_env, "lynae_resonance_liberation")

    modes_1 = []
    mixed_1 = WuwaDpsEnv(ROOT / "data", party=PARTY_ID, curriculum_reset_mode="mixed_lynae_route_curriculum")
    for seed in (31, None, None, None, None, None, None, None):
        _obs, info = mixed_1.reset(seed=seed)
        modes_1.append((info["curriculum_reset_mode"], info["selected_curriculum_submode"]))
    modes_2 = []
    mixed_2 = WuwaDpsEnv(ROOT / "data", party=PARTY_ID, curriculum_reset_mode="mixed_lynae_route_curriculum")
    for seed in (31, None, None, None, None, None, None, None):
        _obs, info = mixed_2.reset(seed=seed)
        modes_2.append((info["curriculum_reset_mode"], info["selected_curriculum_submode"]))
    assert modes_1 == modes_2
    assert all(submode == mode for mode, submode in modes_1)
    print("aemeath_mornye_lynae_anti_liberation_curriculum_smoke_test ok")


if __name__ == "__main__":
    main()
