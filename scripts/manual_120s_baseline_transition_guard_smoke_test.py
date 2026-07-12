from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.manual_120s_baseline import execute_route


def main() -> None:
    result = execute_route("primary")
    placeholders = result["placeholder_fallback"]["steps"]
    assert len(placeholders) == 1
    opening = placeholders[0]
    assert opening["step"] == 6
    assert opening["selected_action_id"] == "swap_to_mornye"
    assert opening["resolved_action_id"] == "swap_to_mornye"
    for swap in result["swaps"]:
        if swap["step"] == 6:
            continue
        assert swap["fallback_swap_used"] is False
        assert swap["swap_timing_is_placeholder"] is False
        assert str(swap["resolved_action_id"]).startswith("transition:")
    print("manual_120s_baseline_transition_guard_smoke_test ok")


if __name__ == "__main__":
    main()
