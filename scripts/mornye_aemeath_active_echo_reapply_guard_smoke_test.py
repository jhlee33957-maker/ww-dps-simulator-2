from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    actions = json.loads((ROOT / "data" / "actions.json").read_text(encoding="utf-8-sig"))
    counts = Counter(action["id"] for action in actions)
    expected = {
        "mornye_echo_reactor_husk",
        "aemeath_echo_sigillum",
        "aemeath_echo_sigillum_hit_1",
        "aemeath_echo_sigillum_hit_2",
    }
    assert all(counts[action_id] == 1 for action_id in expected)
    assert actions[-4]["id"] == "mornye_echo_reactor_husk"
    assert actions[-3]["id"] == "aemeath_echo_sigillum"
    assert actions[-2]["id"] == "aemeath_echo_sigillum_hit_1"
    assert actions[-1]["id"] == "aemeath_echo_sigillum_hit_2"

    audit = json.loads(
        (ROOT / "data" / "source" / "mornye_aemeath_active_echo_source_audit_v102.json").read_text(
            encoding="utf-8-sig"
        )
    )
    assert audit["audit_id"] == "mornye_aemeath_active_echo_source_audit_v102"
    print("mornye_aemeath_active_echo_reapply_guard_smoke_test ok")


if __name__ == "__main__":
    main()
