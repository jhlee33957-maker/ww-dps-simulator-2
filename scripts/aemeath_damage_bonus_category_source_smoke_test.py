from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.build_profiles import raw_damage_type_to_damage_bonus_category
from simulator.simulation import Simulation


BASIC_ACTIONS = [
    "aemeath_basic_form_stage_1",
    "aemeath_basic_form_stage_2",
    "aemeath_basic_form_stage_3",
    "aemeath_basic_form_stage_4",
    "aemeath_mech_basic_stage_1",
    "aemeath_mech_basic_stage_2",
    "aemeath_mech_basic_stage_3",
    "aemeath_mech_basic_stage_4",
]
LIBERATION_ACTIONS = [
    "aemeath_liberation_overdrive",
    "aemeath_heavenfall_finale",
    "aemeath_seraphic_duet_overturn",
    "aemeath_seraphic_duet_encore",
    "aemeath_heavy_aemeath_charged_1",
    "aemeath_heavy_aemeath_charged_2",
    "aemeath_heavy_mech_charged_1",
    "aemeath_heavy_mech_charged_2",
]
SERAPHIC_ACTIONS = ["aemeath_seraphic_duet_overturn", "aemeath_seraphic_duet_encore"]
HEAVY_CHARGED_ACTIONS = [
    "aemeath_heavy_aemeath_charged_1",
    "aemeath_heavy_aemeath_charged_2",
    "aemeath_heavy_mech_charged_1",
    "aemeath_heavy_mech_charged_2",
]


def load_actions() -> dict[str, dict]:
    return {
        item["id"]: item
        for item in json.loads((DATA_DIR / "actions.json").read_text(encoding="utf-8-sig"))
    }


def run_internal(action_id: str, profile: str | None = None):
    sim = Simulation.from_json(
        DATA_DIR,
        party="aemeath",
        build_profile_overrides={"aemeath": profile} if profile else None,
    )
    data = sim.state.character_states["aemeath"]
    if "mech" in action_id:
        data["form"] = "mech"
    if action_id in SERAPHIC_ACTIONS:
        data["form"] = "mech" if action_id.endswith("_encore") else "aemeath"
        data["synchronization_rate"] = 100.0
        data["seraphic_duo_remaining"] = 5.0
    if action_id == "aemeath_heavenfall_finale":
        data["heavenfall_unbound"] = True
        data["heavenfall_unbound_remaining"] = 30.0
        data["synchronization_rate"] = 200.0
        data["resonance_rate"] = 4.0
        data["finale_available"] = True
    assert sim.execute_action(action_id), f"{action_id} should execute"
    return sim.timeline[-1]


def assert_metadata(action: dict) -> None:
    assert action.get("raw_skill_category"), f"{action['id']} missing raw_skill_category"
    assert action.get("raw_damage_type"), f"{action['id']} missing raw_damage_type"
    assert action.get("damage_bonus_category_source") == "data/extracted/aemeath_excel_actions.json"


def test_source_mapping_helper() -> None:
    assert raw_damage_type_to_damage_bonus_category("普通攻击伤害") == "basic_attack"
    assert raw_damage_type_to_damage_bonus_category("普攻伤害") == "basic_attack"
    assert raw_damage_type_to_damage_bonus_category("重击伤害") == "heavy_attack"
    assert raw_damage_type_to_damage_bonus_category("共鸣技能伤害") == "resonance_skill"
    assert raw_damage_type_to_damage_bonus_category("共鸣解放伤害") == "resonance_liberation"
    assert raw_damage_type_to_damage_bonus_category("变奏伤害") == "intro"
    assert raw_damage_type_to_damage_bonus_category("延奏伤害") == "outro"
    assert raw_damage_type_to_damage_bonus_category("震谐伤害") == "other"
    assert raw_damage_type_to_damage_bonus_category("") == "other"


def test_aemeath_explicit_categories() -> None:
    actions = load_actions()
    extracted_path = DATA_DIR / "extracted" / "aemeath_excel_actions.json"
    assert extracted_path.exists(), "Extracted Aemeath source data is required for this smoke test."
    json.loads(extracted_path.read_text(encoding="utf-8-sig"))

    for action_id in BASIC_ACTIONS:
        action = actions[action_id]
        assert action["action_type"] == "basic_attack"
        assert action.get("damage_bonus_category") == "basic_attack"

    for action_id in LIBERATION_ACTIONS:
        action = actions[action_id]
        assert action.get("damage_bonus_category") == "resonance_liberation"
        assert_metadata(action)

    for action_id in SERAPHIC_ACTIONS:
        assert actions[action_id]["action_type"] == "resonance_skill"
        assert actions[action_id]["raw_skill_category"] == "共鸣技能"
        assert actions[action_id]["raw_damage_type"] == "共鸣解放伤害"

    for action_id in HEAVY_CHARGED_ACTIONS:
        assert actions[action_id]["action_type"] == "heavy_attack"
        assert actions[action_id]["raw_skill_category"] == "重击"
        assert actions[action_id]["raw_damage_type"] == "共鸣解放伤害"


def test_liberation_focus_applies_to_source_liberation_damage() -> None:
    for action_id in [
        "aemeath_liberation_overdrive",
        "aemeath_heavenfall_finale",
        "aemeath_seraphic_duet_overturn",
        "aemeath_seraphic_duet_encore",
        *HEAVY_CHARGED_ACTIONS,
    ]:
        row = run_internal(action_id, "liberation_focus_test")
        assert row.damage_bonus_category == "resonance_liberation", action_id
        assert row.category_dmg_bonus > 0.0, action_id

    basic = run_internal("aemeath_basic_form_stage_1", "liberation_focus_test")
    assert basic.damage_bonus_category == "basic_attack"
    assert basic.category_dmg_bonus == 0.0


def main() -> None:
    test_source_mapping_helper()
    test_aemeath_explicit_categories()
    test_liberation_focus_applies_to_source_liberation_damage()
    print("aemeath_damage_bonus_category_source_smoke_test ok")


if __name__ == "__main__":
    main()
