from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    actions = {action["id"]: action for action in json.loads((ROOT / "data" / "actions.json").read_text(encoding="utf-8"))}
    overblast = actions["lynae_resonance_liberation_prismatic_overblast"]
    c5 = actions["lynae_resonance_liberation_prismatic_overblast_c5"]
    report = (ROOT / "reports" / "lynae_timing_cooldown_audit.md").read_text(encoding="utf-8")

    for action in (overblast, c5):
        assert action["action_time"] == 4.0
        assert action["combat_time_cost"] == 0.0
        assert action["resonance_energy_cost"] == 125
        assert action["cooldown"] == 25
        assert action["cooldown_group"] == "lynae_resonance_liberation"
        assert "workbook_confirmed_global_timestop" in action["source_status"]
        assert "decision_frame_240F" in action["source_status"]
        assert "damage_repeat_from_2695" in action["source_status"]
        assert {2692, 2693, 2695}.issubset(set(action["source_rows"]))

    assert 2482 in overblast["source_rows"]
    assert "global time stop row `2693`" in report
    assert "decision frame `240F`" in report
    assert "damage repeat row `2695`" in report
    assert "299F is the timed-combat duration" not in report
    assert "action_time `4.9833`" not in report

    print("lynae_global_timestop_timing_guard_smoke_test ok")


if __name__ == "__main__":
    main()
