from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.v114_test_support import assert_close, build
from simulator.party_transition import GENERIC_SWAP_SOURCE_STATUS, PLACEHOLDER_WARNING


LEGACY_WARNING_FRAGMENTS = (
    "placeholder for party-structure testing",
    "not sourced from Excel/client data",
)


def main() -> None:
    active = build()
    assert active.execute_action("swap_to_mornye")
    row = active.timeline[-1]
    assert_close(row.action_time, 0.0)
    assert_close(row.combat_time_cost, 0.0)
    assert row.swap_timing_is_placeholder is False
    assert row.generic_swap_zero_time is True
    assert row.swap_contract_source_status == GENERIC_SWAP_SOURCE_STATUS
    assert row.transition_warnings == []
    assert not any(
        fragment in warning.lower()
        for warning in row.transition_warnings
        for fragment in LEGACY_WARNING_FRAGMENTS
    )

    legacy = build()
    legacy.preset_generic_swap.update(
        {
            "action_time": 0.5,
            "combat_time_cost": 0.5,
            "is_placeholder": True,
            "warning": "",
        }
    )
    assert legacy.execute_action("swap_to_mornye")
    legacy_row = legacy.timeline[-1]
    assert legacy_row.swap_timing_is_placeholder is True
    assert legacy_row.transition_warnings == [PLACEHOLDER_WARNING]

    print("generic_swap_no_legacy_placeholder_warning_smoke_test: PASS")


if __name__ == "__main__":
    main()
