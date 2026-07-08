from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env.observation_features import (
    SLOT_SCHEMA,
    build_observation_channel_mapping,
    build_observation_slot_mapping,
)
from simulator.simulation import Simulation


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
LYNAE_SLOT = "slot_2"


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party=PARTY_ID)
    slot_mapping = build_observation_slot_mapping(sim)
    mapping = build_observation_channel_mapping(sim)
    expected = {
        f"{LYNAE_SLOT}.primary_resource_ratio": "lynae_overflow",
        f"{LYNAE_SLOT}.secondary_resource_ratio": "lynae_lumiflow",
        f"{LYNAE_SLOT}.tertiary_resource_ratio": "lynae_true_color",
        f"{LYNAE_SLOT}.mechanic_state_0": "lynae_kaleidoscopic_parade",
        f"{LYNAE_SLOT}.mechanic_state_1": "lynae_optical_sampling_stage",
        f"{LYNAE_SLOT}.mechanic_state_2": "lynae_photocromic_flux",
        f"{LYNAE_SLOT}.mechanic_state_3": "lynae_resonance_mode",
        f"{LYNAE_SLOT}.mechanic_state_4": "lynae_visual_impact_cooldown",
        f"{LYNAE_SLOT}.mechanic_state_5": "lynae_spray_paint",
        f"{LYNAE_SLOT}.mechanic_state_6": "lynae_to_vivid_tomorrow_window",
        f"{LYNAE_SLOT}.mechanic_state_7": "lynae_spectral_analysis_cooldown_or_available",
        f"{LYNAE_SLOT}.echo_effect_0": "lynae_pact_neonlight_or_static_mist_handoff",
        f"{LYNAE_SLOT}.echo_effect_1": "lynae_hyvatia_handoff",
        f"{LYNAE_SLOT}.tune_response_0": "lynae_spectral_analysis",
    }

    assert slot_mapping[LYNAE_SLOT] == "lynae"
    for key, value in expected.items():
        assert mapping[key] == value
    assert len(SLOT_SCHEMA) == 57
    assert all(value.startswith("lynae_") for value in expected.values())
    print("lynae_rl_observation_channels_smoke_test ok")


if __name__ == "__main__":
    main()
