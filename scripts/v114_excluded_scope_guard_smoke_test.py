from __future__ import annotations

import hashlib
import json

from v114_test_support import ROOT, build
from rl.demo_contract import action_data_hash


ACTION_SHA = "d6377d54a1abb985dc5f58866321c61c7b904a6b73ddc1538be7e38d36a99ff1"
MANIFEST_SHA = "ed8bda448ce1d74cf34208e90a0d4dc8b21214197309e28a8c5ca53a6be8eb6d"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    sim = build()
    order = sim.get_policy_action_ids()
    assert len(order) == 25
    lowered = " ".join(order).lower()
    assert "counter" not in lowered and "dodge" not in lowered and "aerial" not in lowered
    assert "mornye_optimal_solution" not in order
    assert sim.state.mechanics_config["mornye"]["mornye_expectation_error_mode"] == "expectation_error_only"
    reactor = sim.actions["mornye_echo_reactor_husk"]
    assert reactor.duration == reactor.action_time == 1.1
    assert reactor.hits[0].time == 49.0 / 60.0
    assert reactor.mechanic_effects["source_end_frame"] == 66
    assert "enemy_hp" not in type(sim.state).model_fields and "wave" not in type(sim.state).model_fields
    assert action_data_hash(root=ROOT) == ACTION_SHA
    assert sha(ROOT / "direct_action_data_patch_manifest_v61.json") == MANIFEST_SHA
    print("v114_excluded_scope_guard_smoke_test ok")


if __name__ == "__main__":
    main()
