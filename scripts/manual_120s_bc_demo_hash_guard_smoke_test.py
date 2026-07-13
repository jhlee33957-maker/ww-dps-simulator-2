from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rl.demo_contract import (
    DEFAULT_DEMO_PATH,
    DIRECT_ACTION_MANIFEST_SHA256,
    RESOLVED_SEQUENCE_SHA256,
    SELECTED_SEQUENCE_SHA256,
    action_data_hash,
    file_sha256,
    load_demo_npz,
    party_config_hash,
)


def main() -> None:
    demo = load_demo_npz(DEFAULT_DEMO_PATH)
    metadata = demo["metadata"]
    assert file_sha256(DEFAULT_DEMO_PATH)
    assert metadata["selected_sequence_sha256"] == SELECTED_SEQUENCE_SHA256
    assert metadata["resolved_sequence_sha256"] == RESOLVED_SEQUENCE_SHA256
    assert metadata["action_data_hash"] == action_data_hash(root=ROOT)
    assert metadata["party_config_hash"] == party_config_hash(root=ROOT)
    assert metadata["direct_action_manifest_sha256"] == DIRECT_ACTION_MANIFEST_SHA256
    assert set(map(str, demo["action_data_hashes"])) == {metadata["action_data_hash"]}
    assert set(map(str, demo["party_config_hashes"])) == {metadata["party_config_hash"]}
    print("manual_120s_bc_demo_hash_guard_smoke_test ok")


if __name__ == "__main__":
    main()
