from __future__ import annotations

from collections import Counter
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env.wuwa_env import WuwaDpsEnv
from rl.evaluate_maskable_ppo import (
    _action_counts_by_character_prefix,
    _policy_actions_exposed_by_character,
)


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"


def main() -> None:
    env = WuwaDpsEnv(data_dir=ROOT / "data", party=PARTY_ID)
    party_members = env.get_selected_party_character_ids()
    policy_exposure = _policy_actions_exposed_by_character(
        env.get_policy_action_ids(),
        env.simulation.actions,
        party_members,
    )
    selected_counts = _action_counts_by_character_prefix(["mornye_basic_attack", "swap_to_aemeath"])
    resolved_counts = _action_counts_by_character_prefix(["mornye_basic_stage_1", "transition:aemeath_qte_intro_human"])
    damage_by_character: Counter[str] = Counter({"mornye": 100.0, "aemeath": 50.0})
    unused_party_members = [
        character_id
        for character_id in party_members
        if selected_counts.get(character_id, 0) == 0
        and resolved_counts.get(character_id, 0) == 0
        and damage_by_character.get(character_id, 0.0) == 0.0
    ]

    assert party_members == ["mornye", "aemeath", "lynae"]
    assert "lynae" in unused_party_members
    assert "swap_to_lynae" in policy_exposure["lynae"]
    assert any(action_id.startswith("lynae_") for action_id in policy_exposure["lynae"])

    print(
        "aemeath_mornye_lynae_unused_party_member_diagnostic_smoke_test ok",
        {
            "unused_party_members": unused_party_members,
            "lynae_policy_action_count": len(policy_exposure["lynae"]),
        },
    )


if __name__ == "__main__":
    main()
