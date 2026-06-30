from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.roster import is_dummy_character
from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"


def assert_contains(actions: list[str], expected: list[str]) -> None:
    missing = [action_id for action_id in expected if action_id not in actions]
    assert not missing, f"Missing expected policy actions: {missing}"


def assert_excludes(actions: list[str], forbidden_prefixes: list[str]) -> None:
    found = [
        action_id
        for action_id in actions
        if any(action_id.startswith(prefix) for prefix in forbidden_prefixes)
    ]
    assert not found, f"Found forbidden policy actions: {found}"


def main() -> None:
    characters = {
        item["id"]: item
        for item in json.loads((DATA_DIR / "characters.json").read_text(encoding="utf-8-sig"))
    }
    for character_id in ["main", "sub", "support"]:
        assert is_dummy_character(characters[character_id]), f"{character_id} should be marked dummy_sample"
    if "aemeath" in characters:
        assert not is_dummy_character(characters["aemeath"]), "aemeath should not be marked dummy_sample"

    aemeath = Simulation.from_json(DATA_DIR, selected_character_ids=["aemeath"])
    assert aemeath.selected_character_ids == ["aemeath"]
    assert aemeath.state.active_character_id == "aemeath"
    aemeath_actions = aemeath.get_policy_action_ids()
    assert_contains(aemeath_actions, ["aemeath_basic_attack", "aemeath_heavy_attack", "aemeath_resonance_skill", "aemeath_resonance_liberation"])
    assert_excludes(aemeath_actions, ["main_", "sub_", "support_", "swap_to_main", "swap_to_sub", "swap_to_support"])
    print("Aemeath-only policy actions:", aemeath_actions)

    dummy = Simulation.from_json(DATA_DIR, selected_character_ids=["main", "sub", "support"])
    assert dummy.selected_character_ids == ["main", "sub", "support"]
    dummy_actions = dummy.get_policy_action_ids()
    assert_contains(dummy_actions, ["main_basic_attack", "main_resonance_skill"])
    assert_excludes(dummy_actions, ["aemeath_"])
    print("Dummy trio policy actions:", dummy_actions)

    mixed = Simulation.from_json(DATA_DIR, selected_character_ids=["aemeath", "support"])
    mixed_actions = mixed.get_policy_action_ids()
    assert_contains(mixed_actions, ["aemeath_basic_attack", "aemeath_heavy_attack", "support_basic_attack", "swap_to_aemeath", "swap_to_support"])
    assert_excludes(mixed_actions, ["main_", "sub_", "swap_to_main", "swap_to_sub"])
    print("Mixed policy actions:", mixed_actions)

    try:
        from env.wuwa_env import WuwaDpsEnv

        env = WuwaDpsEnv(DATA_DIR, selected_character_ids=["aemeath"])
        assert env.action_space.n == len(env.get_policy_action_ids())
        assert len(env.action_masks()) == env.action_space.n
        print("Env action count:", env.action_space.n)
    except ModuleNotFoundError:
        print("Gymnasium dependency missing; skipped env portion.")

    sequence_sim = Simulation.from_json(DATA_DIR, selected_character_ids=["aemeath"])
    for selected_action_id in ["aemeath_basic_attack", "aemeath_resonance_skill", "aemeath_basic_attack"]:
        resolved_action_id = sequence_sim.resolve_action_id(selected_action_id)
        ok = sequence_sim.execute_action(selected_action_id)
        assert ok, f"Failed deterministic Aemeath action {selected_action_id}"
        print(f"{selected_action_id} -> {resolved_action_id}")

    print("Character selection smoke test passed.")


if __name__ == "__main__":
    main()
