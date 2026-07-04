from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"


def main() -> None:
    solo = Simulation.from_json(DATA_DIR, party=["aemeath"])
    solo_actions = solo.get_policy_action_ids()
    assert solo.selected_party_character_ids == ["aemeath"]
    assert solo.state.active_character_id == "aemeath"
    assert "aemeath_basic_attack" in solo_actions
    assert "aemeath_heavy_attack" in solo_actions
    assert "aemeath_resonance_skill" in solo_actions
    assert "aemeath_resonance_liberation" in solo_actions
    assert "short_wait" in solo_actions
    assert "swap_to_aemeath" not in solo_actions
    assert all("qte" not in action_id.lower() for action_id in solo_actions)
    assert not any(action.startswith(("main_", "sub_", "support_")) for action in solo_actions)
    print("Solo party policy actions:", solo_actions)

    preset_solo = Simulation.from_json(DATA_DIR, party="aemeath")
    assert preset_solo.selected_party_character_ids == ["aemeath"]
    assert preset_solo.state.active_character_id == "aemeath"
    assert preset_solo.get_policy_action_ids() == solo_actions

    preset_party = Simulation.from_json(DATA_DIR, party="aemeath_test_party")
    preset_party_actions = preset_party.get_policy_action_ids()
    assert preset_party.selected_party_character_ids == ["aemeath", "dummy_support", "dummy_sub_dps"]
    assert preset_party.state.active_character_id == "aemeath"
    assert "swap_to_dummy_support" in preset_party_actions
    assert "dummy_support_attack" in preset_party_actions
    assert "dummy_sub_dps_quick_burst" in preset_party_actions
    assert "aemeath_qte_intro_human" not in preset_party_actions
    assert "aemeath_qte_intro_mech" not in preset_party_actions
    assert not preset_party.is_action_available(preset_party.actions["swap_to_aemeath"])
    print("Aemeath test party policy actions:", preset_party_actions)

    dummy = Simulation.from_json(DATA_DIR, party=["main", "sub", "support"])
    dummy_actions = dummy.get_policy_action_ids()
    assert all(action_id in dummy_actions for action_id in ["main_basic_attack", "sub_basic_attack", "support_basic_attack"])
    assert not any(action.startswith("aemeath_") for action in dummy_actions)
    assert all(action_id in dummy_actions for action_id in ["swap_to_main", "swap_to_sub", "swap_to_support"])
    print("Dummy trio policy actions:", dummy_actions)

    mixed = Simulation.from_json(DATA_DIR, party=["aemeath", "support"])
    mixed_actions = mixed.get_policy_action_ids()
    assert "aemeath_basic_attack" in mixed_actions
    assert "aemeath_heavy_attack" in mixed_actions
    assert "support_basic_attack" in mixed_actions
    assert "swap_to_aemeath" in mixed_actions
    assert "swap_to_support" in mixed_actions
    assert "swap_to_main" not in mixed_actions
    assert "swap_to_sub" not in mixed_actions
    assert not mixed.is_action_available(mixed.actions["swap_to_aemeath"])
    print("Mixed party policy actions:", mixed_actions)

    sequence = ["aemeath_basic_attack", "aemeath_resonance_skill", "aemeath_basic_attack"]
    for action_id in sequence:
        assert solo.execute_action(action_id)
    rows = solo.summary().timeline
    assert rows[0].selected_action_id == "aemeath_basic_attack"
    assert rows[0].resolved_action_id == "aemeath_basic_form_stage_1"
    assert any(row.selected_action_id != row.resolved_action_id for row in rows)
    assert rows[-1].mechanic_debug_after.get("aemeath")
    print("Timeline selected/resolved:", [(row.selected_action_id, row.resolved_action_id) for row in rows])

    try:
        from env.wuwa_env import WuwaDpsEnv

        env = WuwaDpsEnv(DATA_DIR, party=["aemeath"])
        assert "swap_to_aemeath" not in env.get_policy_action_ids()
        assert len(env.action_masks()) == env.action_space.n
        print("Env solo party action count:", env.action_space.n)
    except ModuleNotFoundError:
        print("Gymnasium dependency missing; skipped env portion.")

    print("Party selection smoke test passed.")


if __name__ == "__main__":
    main()
