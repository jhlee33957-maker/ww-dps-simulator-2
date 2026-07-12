from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.manual_120s_baseline import run_all


def main() -> None:
    first = run_all()
    second = run_all()
    for name, result in first.items():
        assert result["final_combat_time"] == 120.0
        assert result["selected_action_sequence"] == second[name]["selected_action_sequence"]
        assert result["resolved_action_sequence"] == second[name]["resolved_action_sequence"]
        assert result["total_damage"] == second[name]["total_damage"]
        assert result["damage_by_character"] == second[name]["damage_by_character"]
        assert result["selected_sequence_sha256"] == second[name]["selected_sequence_sha256"]
    no_lynae = first["no_lynae_control"]
    assert "swap_to_lynae" not in no_lynae["selected_action_sequence"]
    assert not any(action.startswith("lynae_") for action in no_lynae["selected_action_sequence"])
    assert not any(action.startswith("lynae_") for action in no_lynae["resolved_action_sequence"])
    assert first["primary"]["placeholder_fallback"]["count"] == 1
    assert first["reactor_husk_order_variant"]["placeholder_fallback"]["count"] == 1
    print("manual_120s_baseline_comparison_smoke_test ok")


if __name__ == "__main__":
    main()
