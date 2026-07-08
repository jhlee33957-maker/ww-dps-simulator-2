from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env.observation_features import (
    build_observation_channel_mapping,
    build_observation_labels,
    build_observation_values,
)
from env.wuwa_env import WuwaDpsEnv
from rl.evaluate_maskable_ppo import _policy_actions_exposed_by_character
from simulator.transition_actions import get_transition_action


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
INTRO_ID = "lynae_intro_time_to_show_some_colors"
RESOLVED_ID = f"transition:{INTRO_ID}"


def observation(env: WuwaDpsEnv) -> dict[str, float]:
    return dict(
        zip(
            build_observation_labels(),
            build_observation_values(env.simulation),
            strict=True,
        )
    )


def lynae_ratios(env: WuwaDpsEnv) -> dict[str, float]:
    values = observation(env)
    return {
        "overflow": values["slot_2.primary_resource_ratio"],
        "lumiflow": values["slot_2.secondary_resource_ratio"],
        "true_color": values["slot_2.tertiary_resource_ratio"],
        "kaleidoscopic_active": values["slot_2.mechanic_state_0_active"],
        "photocromic_flux_active": values["slot_2.mechanic_state_2_active"],
        "visual_impact_cooldown_active": values["slot_2.mechanic_state_4_active"],
        "spray_paint_active": values["slot_2.mechanic_state_5_active"],
        "spectral_analysis_available": values["slot_2.tune_response_0_available"],
    }


def set_full_concerto(env: WuwaDpsEnv, character_id: str) -> None:
    env.simulation.state.concerto_energy[character_id] = 100.0
    env.simulation.state.character_states[character_id]["concerto_energy"] = 100.0
    env.simulation.state.character_states[character_id]["concerto_ready"] = True


def valid_lynae_actions(env: WuwaDpsEnv) -> list[str]:
    sim = env.simulation
    return [
        action_id
        for action_id in sim.get_policy_action_ids()
        if (action_id.startswith("lynae_") or action_id == "swap_to_lynae")
        and sim.is_action_available(sim.actions[action_id])
    ]


def main() -> None:
    env = WuwaDpsEnv(data_dir=ROOT / "data", party=PARTY_ID)
    env.reset(seed=11)
    party_members = env.get_selected_party_character_ids()
    policy_action_ids = env.get_policy_action_ids()
    exposure = _policy_actions_exposed_by_character(policy_action_ids, env.simulation.actions, party_members)
    transition_record = get_transition_action(ROOT / "data", INTRO_ID)
    channel_mapping = build_observation_channel_mapping(env.simulation)
    metadata_path = ROOT / "results" / "training_metadata.json"
    metadata_warning = None
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        model_party = metadata.get("selected_party_character_ids")
        model_policy_ids = metadata.get("policy_action_ids")
        if model_party != party_members or model_policy_ids != policy_action_ids:
            metadata_warning = (
                "Existing PPO metadata does not match the current party/action space; do not use old "
                "models/results as evidence for the fixed transition."
            )

    assert party_members == ["mornye", "aemeath", "lynae"]
    assert transition_record is not None
    assert transition_record["policy_selectable"] is False
    assert INTRO_ID not in policy_action_ids
    assert RESOLVED_ID not in policy_action_ids
    assert "swap_to_lynae" in policy_action_ids
    assert "swap_to_lynae" in exposure["lynae"]
    assert any(action_id.startswith("lynae_") for action_id in exposure["lynae"])
    assert channel_mapping["slot_2.primary_resource_ratio"] == "lynae_overflow"
    assert channel_mapping["slot_2.mechanic_state_2"] == "lynae_photocromic_flux"

    before_swap_ratios = lynae_ratios(env)
    env.simulation.state.active_character_id = "aemeath"
    set_full_concerto(env, "aemeath")
    assert env.simulation.execute_action("swap_to_lynae")
    after_intro_ratios = lynae_ratios(env)
    valid_after_intro = valid_lynae_actions(env)
    assert env.simulation.execute_action("lynae_basic_attack")
    after_basic_ratios = lynae_ratios(env)
    env.simulation.state.character_mechanics_state["lynae"]["overflow"] = 120.0
    assert env.simulation.execute_action("lynae_spark_collision")
    after_spark_ratios = lynae_ratios(env)
    valid_after_spark = valid_lynae_actions(env)

    payload = {
        "party_id": PARTY_ID,
        "party_members": party_members,
        "lynae_policy_actions": exposure["lynae"],
        "lynae_observation_channel_mapping_present": any(
            value.startswith("lynae_") for key, value in channel_mapping.items() if key.startswith("slot_2.")
        ),
        "lynae_observation_ratios_before_swap": before_swap_ratios,
        "lynae_observation_ratios_after_swap_to_lynae": after_intro_ratios,
        "lynae_observation_ratios_after_basic": after_basic_ratios,
        "lynae_observation_ratios_after_spark_collision": after_spark_ratios,
        "valid_lynae_actions_after_intro": valid_after_intro,
        "valid_lynae_actions_after_spark_collision": valid_after_spark,
        "transition_action_present": transition_record is not None,
        "transition_action_policy_selectable": transition_record["policy_selectable"],
        "valid_action_exposure_note": (
            "PPO selects swap_to_lynae; full-Concerto execution resolves it to "
            f"{RESOLVED_ID}. Transition actions are intentionally absent from the policy action space."
        ),
        "metadata_warning": metadata_warning,
    }
    print(json.dumps(payload, indent=2))
    print("aemeath_mornye_lynae_policy_preflight_diagnostic ok")


if __name__ == "__main__":
    main()
