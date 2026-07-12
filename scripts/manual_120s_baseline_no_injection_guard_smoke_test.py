from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "manual_120s_baseline.py"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.manual_120s_baseline import execute_route


FORBIDDEN_STATE_ATTRS = {
    "combat_time",
    "current_time",
    "resonance_energy",
    "concerto_energy",
    "enemy_off_tune_current",
    "enemy_tune_break_available",
    "enemy_tune_break_cooldown_remaining",
    "rupturous_trail_stacks",
    "rupturous_trail_remaining",
    "interfered_marker_remaining",
    "cooldowns",
    "active_character_id",
    "character_mechanics_state",
    "scheduled_effects",
}


def main() -> None:
    tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = []
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
            else:
                targets = [node.target]
            for target in targets:
                for child in ast.walk(target):
                    if isinstance(child, ast.Attribute) and child.attr in FORBIDDEN_STATE_ATTRS:
                        raise AssertionError(f"forbidden direct state assignment: {child.attr}")
    first = execute_route("primary")
    second = execute_route("primary")
    assert first["final_combat_time"] == second["final_combat_time"]
    assert first["selected_action_sequence"] == second["selected_action_sequence"]
    print("manual_120s_baseline_no_injection_guard_smoke_test ok")


if __name__ == "__main__":
    main()
