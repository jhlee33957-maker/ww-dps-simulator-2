from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


EXPECTED = [1.0875]


def main() -> None:
    actions = {
        action["id"]: action
        for action in json.loads((DATA_DIR / "actions.json").read_text(encoding="utf-8-sig"))
    }
    action = actions["aemeath_mech_basic_stage_3"]
    actual = [hit["damage_multiplier"] for hit in action["hits"]]
    assert actual == EXPECTED, f"Unexpected Mech A3 multipliers: {actual}"
    assert math.isclose(sum(actual), 1.0875, rel_tol=1e-9, abs_tol=1e-9)
    assert all(not math.isclose(value, 0.6165, rel_tol=0.0, abs_tol=1e-12) for value in actual)
    assert len(actual) == 1
    assert action["damage_bonus_category"] == "basic_attack"
    assert action["scaling_stat"] == "atk"
    assert action["mechanic_event_triggers"]
    assert action["policy_selectable"] is False
    assert action["raw_skill_category"] == "普攻"
    assert action["raw_damage_type"] == "普攻伤害"
    print("aemeath_mech_basic_stage_3_coeff_guard_smoke_test ok")


if __name__ == "__main__":
    main()
