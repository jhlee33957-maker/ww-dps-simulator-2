from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.full_real_cycle_integration import EXPECTED_RESOLVED_ROUTE, SELECTED_ROUTE, assert_close
from scripts.manual_120s_baseline import ROUTE_PATH, TARGET_COMBAT_TIME, execute_route


def main() -> None:
    first = execute_route("primary")
    second = execute_route("primary")
    assert_close(first["final_combat_time"], TARGET_COMBAT_TIME, "final combat time")
    assert first["total_damage"] > 0.0
    assert_close(first["dps"], first["total_damage"] / TARGET_COMBAT_TIME, "dps")
    routes = json.loads(ROUTE_PATH.read_text(encoding="utf-8"))
    primary = routes["routes"]["primary"]
    assert primary["selected_policy_actions"][:41] == SELECTED_ROUTE
    assert primary["expected_resolved_actions"][:41] == EXPECTED_RESOLVED_ROUTE
    assert first["selected_sequence_sha256"] == primary["selected_sequence_sha256"]
    assert first["resolved_sequence_sha256"] == primary["resolved_sequence_sha256"]
    assert "short_wait" not in first["selected_action_sequence"]
    assert "short_wait" not in first["resolved_action_sequence"]
    assert first["selected_action_sequence"] == second["selected_action_sequence"]
    assert first["resolved_action_sequence"] == second["resolved_action_sequence"]
    assert first["total_damage"] == second["total_damage"]
    assert first["damage_by_character"] == second["damage_by_character"]
    assert first["final_clipped_action"] == second["final_clipped_action"]
    print("manual_120s_baseline_smoke_test ok")


if __name__ == "__main__":
    main()
