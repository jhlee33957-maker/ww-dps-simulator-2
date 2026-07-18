from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from account_party_v122_test_utils import PARTY_ID
from simulator.simulation import Simulation
from validate_account_party_v122 import dry_validate_account_party


def main() -> None:
    with patch.object(Simulation, "execute_action", side_effect=AssertionError("action execution is forbidden")):
        result = dry_validate_account_party(ROOT, PARTY_ID)
    assert result["action_execution_count"] == 0
    assert result["combat_time"] == 0.0
    assert not list((ROOT / "results").glob("*v122*"))
    assert not list((ROOT / "data").glob("*route*v122*"))
    print("account_party_v122_no_action_execution_smoke_test ok")


if __name__ == "__main__":
    main()
