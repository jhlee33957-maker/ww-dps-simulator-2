from __future__ import annotations

import copy
import hashlib
import json
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.apply_direct_action_data_v61 import apply_manifest_documents


OLD_VALUES = {
    "lynae_intro_time_to_show_some_colors": (1.34, 1.2),
    "lynae_polychrome_leap_stage_2": (0.38, 0.9),
    "lynae_polychrome_leap_stage_3": (0.6, 1.4),
    "lynae_kaleidoscopic_basic_stage_5": (2.84, 10.21),
    "lynae_to_a_vivid_tomorrow": (0.5, 1.78),
}
EXPECTED = {
    "lynae_intro_time_to_show_some_colors": (13.4, 12.0),
    "lynae_polychrome_leap_stage_2": (2.28, 5.4),
    "lynae_polychrome_leap_stage_3": (1.5, 3.5),
    "lynae_kaleidoscopic_basic_stage_5": (3.76, 13.45),
    "lynae_to_a_vivid_tomorrow": (5.46, 19.42),
}


def assert_close(actual: float, expected: float, label: str) -> None:
    assert math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-9), (
        f"{label}: expected {expected}, got {actual}"
    )


def index(records: list[dict]) -> dict[str, dict]:
    return {record["id"]: record for record in records}


def main() -> None:
    manifest_path = ROOT / "data/source/direct_action_data_patch_manifest_v61.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    actions = json.loads((ROOT / "data/actions.json").read_text(encoding="utf-8"))
    transitions = json.loads((ROOT / "data/transition_actions.json").read_text(encoding="utf-8"))
    original_actions = copy.deepcopy(actions)
    original_transitions = copy.deepcopy(transitions)

    actions_by_id = index(actions)
    transitions_by_id = index(transitions)
    for action_id, (old_resonance, old_concerto) in OLD_VALUES.items():
        actions_by_id[action_id]["resonance_energy_gain"] = old_resonance
        actions_by_id[action_id]["concerto_energy_gain"] = old_concerto
    transitions_by_id["lynae_intro_time_to_show_some_colors"]["resonance_energy_gain"] = 1.34
    transitions_by_id["lynae_intro_time_to_show_some_colors"]["concerto_energy_gain"] = 1.2

    corrected_actions, corrected_transitions, changes, _summary = apply_manifest_documents(
        manifest,
        actions,
        transitions,
        manifest_hash=manifest_hash,
    )
    assert changes, "--check --fail-on-diff equivalent should detect old repeated-resource values"
    corrected_by_id = index(corrected_actions)
    corrected_transition_by_id = index(corrected_transitions)
    for action_id, (expected_resonance, expected_concerto) in EXPECTED.items():
        assert_close(corrected_by_id[action_id]["resonance_energy_gain"], expected_resonance, f"{action_id}.RE")
        assert_close(corrected_by_id[action_id]["concerto_energy_gain"], expected_concerto, f"{action_id}.CE")
    assert_close(
        corrected_transition_by_id["lynae_intro_time_to_show_some_colors"]["resonance_energy_gain"],
        13.4,
        "transition intro RE",
    )
    assert_close(
        corrected_transition_by_id["lynae_intro_time_to_show_some_colors"]["concerto_energy_gain"],
        12.0,
        "transition intro CE",
    )

    _again_actions, _again_transitions, second_changes, _second_summary = apply_manifest_documents(
        manifest,
        corrected_actions,
        corrected_transitions,
        manifest_hash=manifest_hash,
    )
    assert not second_changes, "second manifest application should be idempotent"

    untouched_action_ids = set(index(original_actions)) - set(EXPECTED)
    untouched_transition_ids = set(index(original_transitions)) - {"lynae_intro_time_to_show_some_colors"}
    final_by_id = index(corrected_actions)
    final_transition_by_id = index(corrected_transitions)
    for action_id in untouched_action_ids:
        assert final_by_id[action_id] == index(original_actions)[action_id]
    for action_id in untouched_transition_ids:
        assert final_transition_by_id[action_id] == index(original_transitions)[action_id]

    print("lynae_repeated_resource_manifest_reapply_smoke_test ok")


if __name__ == "__main__":
    main()
