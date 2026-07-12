from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.full_real_cycle_integration import assert_close
from scripts.manual_120s_baseline import execute_route


EXPECTED_CATEGORIES = {
    "basic_attack": 1094364.097381991,
    "echo_ability": 77591.16254205018,
    "heavy_attack": 18666.068939718352,
    "intro": 80937.57188460515,
    "other": 0.0,
    "resonance_liberation": 2361954.741286322,
    "resonance_skill": 752161.9697089317,
    "tune_break": 779459.070619741,
}

EXPECTED_ECHO = {
    "mornye_echo_reactor_husk": {
        "activation_count": 4,
        "direct_damage": 11093.654850417735,
        "scheduled_damage": 0.0,
        "total_damage": 11093.654850417735,
    },
    "lynae_echo_hyvatia": {
        "activation_count": 4,
        "direct_damage": 61574.7223428314,
        "scheduled_damage": 0.0,
        "total_damage": 61574.7223428314,
    },
    "aemeath_echo_sigillum": {
        "activation_count": 3,
        "direct_damage": 0.0,
        "resolved_hit_count": 6,
        "scheduled_damage": 189947.5737285981,
        "total_damage": 189947.5737285981,
        "excluded_after_cutoff_hit_count": 0,
        "excluded_after_cutoff_damage": 0.0,
        "excluded_after_cutoff_resonance_energy": 0.0,
    },
}


def main() -> None:
    result = execute_route("primary")
    assert_close(sum(result["damage_by_character"].values()), result["total_damage"], "damage sum", 1e-6)
    tune_sources = {
        event["source_character_id"]
        for tune_break in result["tune_breaks"]
        for event in tune_break["response_events"]
        if float(event.get("damage", 0.0) or 0.0) > 0.0
    }
    assert {"aemeath", "mornye", "lynae"}.issubset(tune_sources)
    scheduled_sources = {
        event.get("source_character_id")
        for event in result["scheduled_effect_event_data"]
        if float(event.get("damage", 0.0) or 0.0) > 0.0
    }
    assert "mornye" in scheduled_sources
    assert "aemeath" in scheduled_sources
    categories = result["damage_by_damage_bonus_category"]
    assert_close(sum(categories.values()), result["total_damage"], "category sum", 1e-6)
    for category, expected in EXPECTED_CATEGORIES.items():
        assert_close(categories[category], expected, f"category {category}", 1e-6)

    echo_summary = result["active_echo_summary"]
    for action_id, expected_values in EXPECTED_ECHO.items():
        actual = echo_summary[action_id]
        for key, expected in expected_values.items():
            if isinstance(expected, int):
                assert actual[key] == expected
            else:
                assert_close(actual[key], expected, f"{action_id} {key}", 1e-6)
    assert_close(echo_summary["total_active_echo_damage"], 262615.95092184725, "total active Echo damage", 1e-6)
    assert result["aemeath_sigillum"]["excluded_after_cutoff_hit_count"] == 0
    assert_close(result["aemeath_sigillum"]["excluded_after_cutoff_damage"], 0.0, "Sigillum excluded damage")
    assert_close(result["aemeath_sigillum"]["excluded_after_cutoff_resonance_energy"], 0.0, "Sigillum excluded RE")
    print("manual_120s_baseline_damage_attribution_smoke_test ok")


if __name__ == "__main__":
    main()
