from __future__ import annotations

import hashlib
import json
from v124_timing_test_support import make_sim


def main() -> None:
    action_ids = make_sim("mornye").get_policy_action_ids()
    digest = hashlib.sha256(json.dumps(action_ids, separators=(",", ":")).encode()).hexdigest()
    assert len(action_ids) == 25
    assert digest == "e947749f3113dae8aef0b2186f713582422a7fdf8cc763ad01b953e37eb6b88d"
    print("policy_action_order_v124_guard_smoke_test ok")


if __name__ == "__main__":
    main()

