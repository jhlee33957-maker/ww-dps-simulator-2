from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    report_path = ROOT / "reports" / "lynae_resource_cooldown_alignment.md"
    json_path = ROOT / "data" / "extracted" / "lynae_resource_cooldown_alignment.json"
    assert report_path.exists()
    assert json_path.exists()

    report = report_path.read_text(encoding="utf-8")
    alignment = json.loads(json_path.read_text(encoding="utf-8"))
    records = {record["action_id"]: record for record in alignment["records"]}
    overblast = records["lynae_resonance_liberation_prismatic_overblast"]
    palette = records["lynae_resonance_skill_palette"]
    additive = records["lynae_resonance_skill_additive_color"]

    assert overblast["resonance_energy_cost"] == 125
    assert overblast["cooldown"] == 25
    assert overblast["cooldown_group"] == "lynae_resonance_liberation"
    assert palette["cooldown"] == 6.0
    assert additive["cooldown"] == 6.0
    assert palette["cooldown_group"] == "lynae_resonance_skill"
    assert additive["cooldown_group"] == "lynae_resonance_skill"
    assert "Prismatic Overblast" in report
    assert "cost 125" in report
    assert "cooldown 25s" in report
    assert "share cooldown group `lynae_resonance_skill`" in report
    assert "free/no-cooldown" not in report
    assert "299F is the timed-combat duration" not in report

    print("lynae_resource_cooldown_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
