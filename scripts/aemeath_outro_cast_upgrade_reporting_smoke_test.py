from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.rebaseline_transition_contract_v114 import replay_manual


EXPECTED_DAMAGE = 5268418.084869607
EXPECTED_DPS = 43903.484040580064
EXPECTED_SELECTED_SHA = "e3ddea873cb5059bd29a8a9eb7165ea0e45a9a9e4fa4f68e5e229db2f622daf1"
EXPECTED_RESOLVED_SHA = "3edca6f6f258999a9c915a9ec32ee88c0db570d2303846e0fb8b6da367970229"


def main() -> None:
    summary, timeline = replay_manual()
    base_rows = [row for row in timeline if row["aemeath_outro_applied"]]
    upgrade_rows = [row for row in timeline if row["aemeath_outro_upgrade_applied"]]
    assert len(base_rows) == 3
    assert len(upgrade_rows) == 3
    assert all(not row["aemeath_outro_upgrade_applied"] for row in base_rows)
    assert all(not row["aemeath_outro_applied"] for row in upgrade_rows)
    assert all(row["outgoing_character_id"] == "aemeath" for row in base_rows)
    assert all(row["outgoing_outro_event_id"] == "aemeath_outro_unseen_guard" for row in base_rows)
    assert all(row["aemeath_outro_upgraded_character_ids"] == ["lynae"] for row in upgrade_rows)
    assert summary["aemeath_outro_cast_count"] == 3
    assert summary["aemeath_outro_upgrade_count"] == 3
    assert summary["aemeath_outro_upgrade_counts_by_recipient"] == {"lynae": 3}
    assert summary["total_damage"] == EXPECTED_DAMAGE
    assert summary["dps"] == EXPECTED_DPS
    assert summary["selected_route_sha256"] == EXPECTED_SELECTED_SHA
    assert summary["resolved_route_sha256"] == EXPECTED_RESOLVED_SHA
    assert summary["final_aemeath_outro_recipient_state"] == {
        "mornye": {"value": 0.1, "remaining_duration": 4.249999999999998},
        "lynae": {"value": 0.2, "remaining_duration": 4.249999999999998},
    }
    artifact = json.loads((ROOT / "results/manual_120s_baseline_v114_summary.json").read_text(encoding="utf-8"))
    if artifact.get("schema_version") == "manual_120s_baseline_v114":
        assert artifact["aemeath_outro_cast_count"] != 6
    print("aemeath_outro_cast_upgrade_reporting_smoke_test ok")


if __name__ == "__main__":
    main()
