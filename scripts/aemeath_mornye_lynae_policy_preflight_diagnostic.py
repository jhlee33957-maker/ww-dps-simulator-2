from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env.wuwa_env import WuwaDpsEnv
from rl.evaluate_maskable_ppo import _policy_actions_exposed_by_character
from simulator.transition_actions import get_transition_action


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
INTRO_ID = "lynae_intro_time_to_show_some_colors"
RESOLVED_ID = f"transition:{INTRO_ID}"


def main() -> None:
    env = WuwaDpsEnv(data_dir=ROOT / "data", party=PARTY_ID)
    party_members = env.get_selected_party_character_ids()
    policy_action_ids = env.get_policy_action_ids()
    exposure = _policy_actions_exposed_by_character(policy_action_ids, env.simulation.actions, party_members)
    transition_record = get_transition_action(ROOT / "data", INTRO_ID)
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

    payload = {
        "party_id": PARTY_ID,
        "party_members": party_members,
        "lynae_policy_actions": exposure["lynae"],
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
