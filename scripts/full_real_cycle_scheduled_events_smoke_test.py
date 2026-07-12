from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.full_real_cycle_integration import (
    assert_route_contract,
    assert_scheduled_event_contract,
    execute_strict_route,
)


def main() -> None:
    run = execute_strict_route()
    assert_route_contract(run)
    assert_scheduled_event_contract(run)
    print("full_real_cycle_scheduled_events_smoke_test ok")


if __name__ == "__main__":
    main()
