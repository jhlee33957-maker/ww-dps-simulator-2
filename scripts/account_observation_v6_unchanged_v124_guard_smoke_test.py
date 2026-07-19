from __future__ import annotations

import hashlib
import json
from v124_timing_test_support import make_sim
from simulator.account_constellation_effects import ACCOUNT_OBSERVATION_SHAPE, ACCOUNT_OBSERVATION_VERSION, build_account_observation_labels


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def main() -> None:
    labels = build_account_observation_labels()
    values = make_sim("mornye").account_observation_values()
    assert ACCOUNT_OBSERVATION_VERSION == "slot_account_constellation_single_boss_v6"
    assert len(labels) == len(values) == ACCOUNT_OBSERVATION_SHAPE == 330
    assert digest(labels) == "b32bfb6fc3287ccf10bef65b9ac146902c69cb0b1ce6808ef0acadf7bc50e374"
    assert digest(values) == "6ccc4a5f228329c7b02ed72d4b1354cffc0c8a222d0ed1115be40316a18b3a4f"
    print("account_observation_v6_unchanged_v124_guard_smoke_test ok")


if __name__ == "__main__":
    main()

