from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import (
    ACCOUNT_SCOPE_ID,
    AccountScopeValidationError,
    load_account_scope_contract,
    validate_account_single_boss_scope,
)


DATA_DIR = ROOT / "data"


def main() -> None:
    scope = load_account_scope_contract(DATA_DIR)
    assert validate_account_single_boss_scope(scope)["scope_id"] == ACCOUNT_SCOPE_ID
    assert validate_account_single_boss_scope(ACCOUNT_SCOPE_ID)["enemy_count"] == 1
    for mutation in (
        {"scope_id": ACCOUNT_SCOPE_ID, "enemy_count": 2},
        {"scope_id": ACCOUNT_SCOPE_ID, "enemy_death_enabled": True},
        {"scope_id": ACCOUNT_SCOPE_ID, "enemy_model": "multi_target"},
        {"scope_id": ACCOUNT_SCOPE_ID, "player_hp_model_enabled": True},
        {"scope_id": ACCOUNT_SCOPE_ID, "player_death_enabled": True},
        {"scope_id": ACCOUNT_SCOPE_ID, "target_pull_or_movement_enabled": True},
        {"scope_id": "multi_wave"},
    ):
        try:
            validate_account_single_boss_scope(mutation)
        except AccountScopeValidationError:
            pass
        else:
            raise AssertionError(f"invalid scope accepted: {json.dumps(mutation)}")
    print("user_account_single_boss_scope_v121_smoke_test ok")


if __name__ == "__main__":
    main()
