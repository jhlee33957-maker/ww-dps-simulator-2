from __future__ import annotations

import json
import math
import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


EXPECTED = {
    "lynae_intro_time_to_show_some_colors": (13.4, 12.0),
    "lynae_polychrome_leap_stage_2": (2.28, 5.4),
    "lynae_polychrome_leap_stage_3": (1.5, 3.5),
    "lynae_kaleidoscopic_basic_stage_5": (3.76, 13.45),
    "lynae_to_a_vivid_tomorrow": (5.46, 19.42),
}
UNCHANGED_DAMAGE_AND_TIMING = {
    "lynae_intro_time_to_show_some_colors": (2.248, 1.3333333333333333, 1.3333333333333333),
    "lynae_polychrome_leap_stage_2": (1.014, 0.6, 0.6),
    "lynae_polychrome_leap_stage_3": (0.655, 0.6166666666666667, 0.6166666666666667),
    "lynae_kaleidoscopic_basic_stage_5": (2.5181, 1.5166666666666666, 1.5166666666666666),
    "lynae_to_a_vivid_tomorrow": (2.0106, 2.4833333333333334, 2.4833333333333334),
}


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-9) -> None:
    assert math.isclose(actual, expected, rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def main() -> None:
    actions = json.loads((ROOT / "data/actions.json").read_text(encoding="utf-8"))
    transitions = json.loads((ROOT / "data/transition_actions.json").read_text(encoding="utf-8"))
    by_id = {action["id"]: action for action in actions}
    transition_by_id = {action["id"]: action for action in transitions}

    for action_id, (expected_resonance, expected_concerto) in EXPECTED.items():
        action = by_id[action_id]
        assert_close(action["resonance_energy_gain"], expected_resonance, f"{action_id}.RE")
        assert_close(action["concerto_energy_gain"], expected_concerto, f"{action_id}.CE")
        expected_damage, expected_action_time, expected_combat_time = UNCHANGED_DAMAGE_AND_TIMING[action_id]
        assert_close(action["damage_multiplier"], expected_damage, f"{action_id}.damage")
        assert_close(action["action_time"], expected_action_time, f"{action_id}.action_time")
        assert_close(action["combat_time_cost"], expected_combat_time, f"{action_id}.combat_time_cost")
        assert by_id[action_id]["id"] == action_id

    intro = by_id["lynae_intro_time_to_show_some_colors"]
    transition_intro = transition_by_id["lynae_intro_time_to_show_some_colors"]
    assert_close(transition_intro["resonance_energy_gain"], intro["resonance_energy_gain"], "intro transition RE")
    assert_close(transition_intro["concerto_energy_gain"], intro["concerto_energy_gain"], "intro transition CE")
    assert_close(transition_intro["hits"][0], intro["damage_multiplier"], "intro transition damage")
    assert_close(transition_intro["action_time"], intro["action_time"], "intro transition action_time")
    assert_close(transition_intro["combat_time_cost"], intro["combat_time_cost"], "intro transition combat_time")

    runpy.run_path(str(ROOT / "scripts/lynae_source_audit.py"), run_name="__main__")
    alignment = json.loads((ROOT / "data/extracted/lynae_resource_cooldown_alignment.json").read_text(encoding="utf-8"))
    records = {record["action_id"]: record for record in alignment["records"]}
    for action_id, (expected_resonance, expected_concerto) in EXPECTED.items():
        record = records[action_id]
        assert record["resource_aggregation"] == "sum_component_resource_times_repeat_count"
        assert_close(record["source_resonance_energy_gain"], expected_resonance, f"{action_id}.source_RE")
        assert_close(record["source_concerto_energy_gain"], expected_concerto, f"{action_id}.source_CE")

    print("lynae_repeated_resource_totals_smoke_test ok")


if __name__ == "__main__":
    main()
