from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir)
        timeline_path = results_dir / "ppo_timeline.csv"
        summary_path = results_dir / "ppo_evaluation_summary.json"
        rows = [
            {
                "character_id": "aemeath",
                "actor_character_id": "aemeath",
                "damage_category": "resonance_liberation",
                "damage_bonus_category": "resonance_liberation",
                "normal_damage": "600",
                "tune_break_damage": "0",
                "tune_response_damage": "0",
                "total_action_damage": "1000",
                "generated_mechanic_damage": "400",
                "generated_mechanic_hit_count": "5",
                "aemeath_forte_generated_damage": "400",
                "aemeath_seraphic_duet_followup_triggered": "True",
                "aemeath_seraphic_duet_followup_variant": "normal",
                "aemeath_seraphic_duet_followup_damage": "400",
                "aemeath_seraphic_duet_followup_repeat_count": "5",
                "aemeath_seraphic_duet_followup_multiplier": "1.0935",
            },
            {
                "character_id": "mornye",
                "actor_character_id": "mornye",
                "damage_category": "basic_attack",
                "damage_bonus_category": "basic_attack",
                "normal_damage": "250",
                "tune_break_damage": "0",
                "tune_response_damage": "50",
                "total_action_damage": "300",
                "generated_mechanic_damage": "0",
                "generated_mechanic_hit_count": "0",
                "aemeath_forte_generated_damage": "0",
                "aemeath_seraphic_duet_followup_triggered": "False",
                "aemeath_seraphic_duet_followup_variant": "",
                "aemeath_seraphic_duet_followup_damage": "0",
                "aemeath_seraphic_duet_followup_repeat_count": "0",
                "aemeath_seraphic_duet_followup_multiplier": "0",
            },
        ]
        with timeline_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        old_summary = {
            "total_damage": 1300.0,
            "dps": 1300.0,
            "damage_by_category": {"resonance_liberation": 1000.0, "basic_attack": 300.0},
            "damage_by_selected_action": {"aemeath_seraphic_duet_overturn": 1000.0},
        }
        summary_path.write_text(json.dumps(old_summary, indent=2), encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "backfill_generated_damage_summary_from_timeline.py"),
                "--results-dir",
                str(results_dir),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "generated_mechanic_damage_total" in result.stdout
        updated = json.loads(summary_path.read_text(encoding="utf-8"))
    assert updated["report_generation_version"].endswith("backfilled")
    assert updated["generated_mechanic_damage_total"] == 400.0
    assert updated["aemeath_forte_generated_damage_total"] == 400.0
    assert updated["direct_damage_by_category"]["resonance_liberation"] == 600.0
    assert updated["direct_damage_by_category"]["basic_attack"] == 300.0
    assert updated["legacy_damage_by_source_action_category"]["resonance_liberation"] == 1000.0
    assert updated["generated_damage_by_source_action_category"]["resonance_liberation"] == 400.0
    assert updated["effective_damage_role_breakdown"]["total_damage_check"] == 1300.0
    assert updated["damage_by_category"] == old_summary["damage_by_category"]
    assert updated["damage_by_selected_action"] == old_summary["damage_by_selected_action"]
    print("evaluation_generated_damage_backfill_smoke_test ok")


if __name__ == "__main__":
    main()
