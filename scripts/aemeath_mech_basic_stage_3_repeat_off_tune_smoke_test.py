from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    actions = json.loads((ROOT / "data" / "actions.json").read_text(encoding="utf-8-sig"))
    action = {item["id"]: item for item in actions}["aemeath_mech_basic_stage_3"]

    multipliers = [hit["damage_multiplier"] for hit in action["hits"]]
    assert multipliers == [1.0875]
    assert math.isclose(action["off_tune_value"], 62.54, rel_tol=1e-9, abs_tol=1e-9)
    assert action["off_tune_value_source_status"] == "workbook_confirmed_repeat_aware"
    assert action["off_tune_value_source_ref"] == "角色-女!S2889:S2892"
    assert action["off_tune_value_repeat_formula"] == "6.7 + 2.24 * 3 + 2.24 + 46.88"
    assert action["off_tune_value_repeat_source_ref"] == "角色-女!D2890"
    assert math.isclose(action["mechanic_effects"]["sync_delta"], 18.54, rel_tol=1e-9, abs_tol=1e-9)
    assert action["sync_delta_source_status"] == "workbook_confirmed_repeat_aware"
    assert action["sync_delta_repeat_formula"] == "1.99 + 0.67 * 3 + 0.67 + 13.87"
    assert action["resonance_energy_gain"] == 1.96
    assert action["concerto_energy_gain"] == 3.91
    assert action["damage_bonus_category"] == "basic_attack"
    assert action["scaling_stat"] == "atk"

    print("aemeath_mech_basic_stage_3_repeat_off_tune_smoke_test ok")


if __name__ == "__main__":
    main()
