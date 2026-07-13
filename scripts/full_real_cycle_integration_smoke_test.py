from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.full_real_cycle_integration import assert_route_contract, run_determinism_check


def main() -> None:
    first, second = run_determinism_check()
    assert_route_contract(first)
    assert first.result["determinism_signature"] == second.result["determinism_signature"]
    print("full_real_cycle_integration_smoke_test ok")


if __name__ == "__main__":
    main()
