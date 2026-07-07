from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rl.evaluation_report import add_generated_damage_summary, build_generated_damage_summary


def _generated_hits(count: int, damage: float, *, amp: float = 0.0) -> list[dict[str, float | bool | str]]:
    return [
        {
            "is_generated_mechanic_damage": True,
            "formula_type": "tune_response",
            "damage": damage,
            "effective_damage_taken_amp": amp,
            "applied_damage_taken_amp": amp,
        }
        for _ in range(count)
    ]


def main() -> None:
    timeline = [
        {
            "character_id": "aemeath",
            "actor_character_id": "aemeath",
            "damage_category": "basic_attack",
            "damage_bonus_category": "basic_attack",
            "normal_damage": 700.0,
            "total_action_damage": 1000.0,
            "generated_mechanic_damage": 300.0,
            "generated_mechanic_hit_count": 5,
            "aemeath_forte_generated_damage": 300.0,
            "aemeath_seraphic_duet_followup_triggered": True,
            "aemeath_seraphic_duet_followup_variant": "normal",
            "aemeath_seraphic_duet_followup_damage": 300.0,
            "aemeath_seraphic_duet_followup_repeat_count": 5,
            "aemeath_seraphic_duet_followup_multiplier": 1.0935,
            "hit_details": _generated_hits(5, 60.0),
        },
        {
            "character_id": "aemeath",
            "actor_character_id": "aemeath",
            "damage_category": "basic_attack",
            "damage_bonus_category": "basic_attack",
            "normal_damage": 1000.0,
            "total_action_damage": 2000.0,
            "generated_mechanic_damage": 1000.0,
            "generated_mechanic_hit_count": 10,
            "aemeath_forte_generated_damage": 1000.0,
            "aemeath_seraphic_duet_followup_triggered": True,
            "aemeath_seraphic_duet_followup_variant": "enhanced",
            "aemeath_seraphic_duet_followup_damage": 1000.0,
            "aemeath_seraphic_duet_followup_repeat_count": 10,
            "aemeath_seraphic_duet_followup_multiplier": 1.0935,
            "hit_details": _generated_hits(10, 100.0, amp=0.4),
        },
        {
            "character_id": "mornye",
            "actor_character_id": "mornye",
            "damage_category": "basic_attack",
            "damage_bonus_category": "basic_attack",
            "normal_damage": 500.0,
            "total_action_damage": 500.0,
        },
    ]
    summary = build_generated_damage_summary(timeline, total_damage=3500.0)
    assert summary["generated_mechanic_damage_total"] == 1300.0
    assert summary["generated_mechanic_damage_action_count"] == 2
    assert summary["generated_mechanic_damage_hit_count"] == 15
    assert summary["generated_mechanic_damage_share_of_total"] == 1300.0 / 3500.0
    assert summary["aemeath_forte_generated_damage_total"] == 1300.0
    assert summary["aemeath_seraphic_duet_followup_damage_total"] == 1300.0
    assert summary["aemeath_seraphic_duet_followup_normal_count"] == 1
    assert summary["aemeath_seraphic_duet_followup_enhanced_count"] == 1
    assert summary["aemeath_seraphic_duet_followup_normal_damage_total"] == 300.0
    assert summary["aemeath_seraphic_duet_followup_enhanced_damage_total"] == 1000.0
    assert summary["aemeath_seraphic_duet_followup_total_repeat_count"] == 15
    assert summary["aemeath_seraphic_duet_followup_average_damage"] == 650.0
    assert summary["aemeath_seraphic_duet_followup_average_damage_per_hit"] == 1300.0 / 15.0
    assert summary["aemeath_seraphic_duet_followup_source_multipliers"] == [1.0935]
    assert summary["aemeath_forte_interfered_amp_damage_events"] == 1
    assert summary["aemeath_forte_interfered_amp_damage_total"] == 1000.0
    assert summary["aemeath_forte_interfered_amp_applied_count"] == 10
    assert summary["aemeath_forte_interfered_amp_missing_count"] == 1
    assert summary["damage_by_hit_formula_type"]["tune_response"] == 1300.0
    assert "generated_mechanic_damage" in summary["damage_by_hit_formula_type"]
    assert summary["damage_by_generated_mechanic_source"]["aemeath_forte"] == 1300.0
    assert "basic_attack" not in summary["damage_by_generated_mechanic_source"]
    assert summary["damage_by_character_and_source"]["Aemeath direct action damage"] == 1700.0
    assert summary["damage_by_character_and_source"]["Aemeath generated mechanic damage"] == 1300.0

    payload = add_generated_damage_summary(
        {"damage_by_category": {"basic_attack": 3500.0}},
        timeline,
        total_damage=3500.0,
    )
    assert payload["damage_by_category"] == {"basic_attack": 3500.0}
    assert payload["generated_mechanic_damage_total"] == 1300.0
    print("evaluation_generated_damage_summary_smoke_test ok")


if __name__ == "__main__":
    main()
