from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ROLE_FEMALE_SHEET = "\u89d2\u8272-\u5973"
DAMAGE_1_ACTION_REF = f"{ROLE_FEMALE_SHEET}!4126"
DAMAGE_2_ACTION_REF = f"{ROLE_FEMALE_SHEET}!4127"


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-8) -> None:
    assert math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def main() -> None:
    actions = {item["id"]: item for item in json.loads((DATA_DIR / "actions.json").read_text(encoding="utf-8"))}
    damage_1 = actions["mornye_syntony_field_damage"]
    damage_2 = actions["mornye_syntony_field_target_damage"]
    heavy = actions["mornye_heavy_geopotential_shift"]

    assert damage_1["policy_selectable"] is False
    assert damage_1["scaling_stat"] == "def"
    assert damage_1["action_type"] == "resonance_liberation"
    assert damage_1["damage_bonus_category"] == "resonance_liberation"
    assert len(damage_1["hits"]) == 1
    assert_close(damage_1["hits"][0]["damage_multiplier"], 0.3977, "Damage 1 multiplier")
    assert_close(damage_1["off_tune_value"], 0.0, "Damage 1 Off-Tune")
    assert damage_1["off_tune_value_source_status"] == "workbook_confirmed_zero_for_damage_1"
    assert DAMAGE_1_ACTION_REF in damage_1["off_tune_value_source_ref"]
    assert_close(damage_1["resonance_energy_gain"], 0.0, "Damage 1 RE")
    assert_close(damage_1["concerto_energy_gain"], 0.0, "Damage 1 CE")
    assert damage_1["mechanic_effects"]["scheduled_resource_policy"] == "none"

    assert damage_2["policy_selectable"] is False
    assert damage_2["scaling_stat"] == "def"
    assert damage_2["action_type"] == "heavy_attack"
    assert damage_2["damage_bonus_category"] == "heavy_attack"
    assert len(damage_2["hits"]) == 1
    assert_close(damage_2["hits"][0]["damage_multiplier"], 0.9902, "Damage 2 multiplier")
    assert_close(damage_2["off_tune_value"], 66.4, "Damage 2 Off-Tune")
    assert damage_2["off_tune_value_source_status"] == "workbook_confirmed"
    assert DAMAGE_2_ACTION_REF in damage_2["off_tune_value_source_ref"]
    assert_close(damage_2["resonance_energy_gain"], 2.08, "Damage 2 RE")
    assert_close(damage_2["concerto_energy_gain"], 6.65, "Damage 2 CE")
    assert damage_2["mechanic_effects"]["scheduled_resource_policy"] == "source_confirmed_positive_gains"

    assert_close(heavy["hits"][0]["damage_multiplier"], 0.4414, "Geopotential direct multiplier")
    assert "mornye_syntony_field_target_damage" not in [
        item["id"] for item in actions.values() if item.get("policy_selectable", True)
    ]

    print("mornye_syntony_field_payload_data_smoke_test ok")


if __name__ == "__main__":
    main()
