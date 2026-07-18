from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.account_config_contract import (
    ACCOUNT_CONFIG_COMPONENT_PATHS,
    account_config_hash,
    load_account_config_manifest,
    validate_account_config_manifest,
)


def main() -> None:
    manifest = validate_account_config_manifest(ROOT)
    assert manifest == load_account_config_manifest(ROOT)
    assert manifest["account_config_hash"] == account_config_hash(ROOT)
    assert manifest["component_paths"] == list(ACCOUNT_CONFIG_COMPONENT_PATHS)
    assert manifest["observation_version"] == "slot_account_constellation_single_boss_v6"
    assert manifest["observation_shape"] == 330
    assert manifest["policy_action_count"] == 25
    with tempfile.TemporaryDirectory() as temp:
        clone = Path(temp)
        for relative_path in ACCOUNT_CONFIG_COMPONENT_PATHS:
            destination = clone / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative_path, destination)
        original = account_config_hash(clone)
        for relative_path in ACCOUNT_CONFIG_COMPONENT_PATHS:
            target = clone / relative_path
            original_bytes = target.read_bytes()
            target.write_bytes(original_bytes + b" ")
            assert account_config_hash(clone) != original
            target.write_bytes(original_bytes)
    print("account_config_hash_v122_smoke_test ok")


if __name__ == "__main__":
    main()
