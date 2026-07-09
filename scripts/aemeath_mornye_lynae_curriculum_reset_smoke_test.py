from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env.wuwa_env import WuwaDpsEnv


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"


def observation_values(env: WuwaDpsEnv) -> dict[str, float]:
    return dict(zip(env.observation_labels(), env._get_observation(), strict=True))


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-6) -> None:
    assert abs(actual - expected) <= tolerance, f"{label}: expected {expected}, got {actual}"


def main() -> None:
    ready_env = WuwaDpsEnv(ROOT / "data", party=PARTY_ID, curriculum_reset_mode="aemeath_ready_for_lynae")
    _obs, info = ready_env.reset(seed=7)
    assert info["curriculum_reset_mode"] == "aemeath_ready_for_lynae"
    assert ready_env.simulation.state.active_character_id == "aemeath"
    assert ready_env.simulation.state.character_states["aemeath"]["concerto_energy"] == 100.0
    assert ready_env.simulation.state.character_states["aemeath"]["concerto_ready"] is True
    assert ready_env.simulation.is_action_available(ready_env.simulation.actions["swap_to_lynae"])

    intro_env = WuwaDpsEnv(ROOT / "data", party=PARTY_ID, curriculum_reset_mode="lynae_after_intro")
    _obs, info = intro_env.reset(seed=7)
    intro_state = intro_env.simulation.state.character_mechanics_state["lynae"]
    assert info["curriculum_reset_mode"] == "lynae_after_intro"
    assert intro_env.simulation.state.active_character_id == "lynae"
    assert intro_state["overflow"] == 100.0
    assert intro_state["photocromic_flux_active"] is True
    assert_close(observation_values(intro_env)["slot_2.primary_resource_ratio"], 100.0 / 120.0, "Lynae overflow observation")

    kp_env = WuwaDpsEnv(ROOT / "data", party=PARTY_ID, curriculum_reset_mode="lynae_kaleidoscopic_ready")
    _obs, info = kp_env.reset(seed=7)
    kp_state = kp_env.simulation.state.character_mechanics_state["lynae"]
    assert info["curriculum_reset_mode"] == "lynae_kaleidoscopic_ready"
    assert kp_env.simulation.state.active_character_id == "lynae"
    assert kp_state["lumiflow"] == 120.0
    assert kp_state["kaleidoscopic_parade_remaining"] > 0.0
    assert kp_env.simulation.is_action_available(kp_env.simulation.actions["lynae_polychrome_leap"])

    modes_1 = []
    mixed_1 = WuwaDpsEnv(ROOT / "data", party=PARTY_ID, curriculum_reset_mode="mixed_lynae_curriculum")
    for seed in (23, None, None, None, None, None):
        _obs, info = mixed_1.reset(seed=seed)
        modes_1.append(info["curriculum_reset_mode"])
    modes_2 = []
    mixed_2 = WuwaDpsEnv(ROOT / "data", party=PARTY_ID, curriculum_reset_mode="mixed_lynae_curriculum")
    for seed in (23, None, None, None, None, None):
        _obs, info = mixed_2.reset(seed=seed)
        modes_2.append(info["curriculum_reset_mode"])
    assert modes_1 == modes_2
    assert set(modes_1).issubset({"none", "aemeath_ready_for_lynae", "lynae_after_intro", "lynae_kaleidoscopic_ready"})
    print("aemeath_mornye_lynae_curriculum_reset_smoke_test ok")


if __name__ == "__main__":
    main()
