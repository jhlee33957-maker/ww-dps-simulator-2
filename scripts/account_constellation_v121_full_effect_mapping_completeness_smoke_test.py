from __future__ import annotations

import ast
import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from account_constellation_source_contract_v121 import CONTRACT
from account_constellation_source_workbook_v121 import load_source_cache

PLACEHOLDER_INTERPRETATION = "Atomic candidate-121 single-boss mapping."


def normalized(value: object) -> str:
    return "".join(str(value).split())


def runtime_symbol_exists(runtime_code_id: str) -> bool:
    try:
        relative_path, dotted_symbol = runtime_code_id.split("::", 1)
    except ValueError:
        return False
    path = ROOT / relative_path
    if not path.is_file() or not dotted_symbol:
        return False
    parts = dotted_symbol.split(".")
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    node = next((item for item in tree.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and item.name == parts[0]), None)
    if node is None:
        return False
    for part in parts[1:]:
        if not isinstance(node, ast.ClassDef):
            return False
        node = next((item for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and item.name == part), None)
        if node is None:
            return False
    return True


def validate_mappings(mappings: list[dict], cache=None) -> None:
    by_id = {mapping["effect_id"]: mapping for mapping in mappings}
    assert set(by_id) == set(CONTRACT)
    assert len(mappings) == len(by_id) == 46
    for effect_id, contract in CONTRACT.items():
        mapping = by_id[effect_id]
        assert mapping["character_id"] == contract["character_id"]
        assert int(mapping["sequence"]) == contract["sequence"] > 0
        assert mapping["support_status"] == contract["support_status"]
        assert mapping["source_type"] == contract["source_type"]
        interpretation = mapping.get("implementation_interpretation")
        assert interpretation and interpretation != PLACEHOLDER_INTERPRETATION
        assert runtime_symbol_exists(mapping.get("runtime_code_id", "")), mapping.get("runtime_code_id")
        assert not mapping["runtime_code_id"].endswith("::AemeathMechanic")
        assert (ROOT / mapping["real_end_to_end_test_id"]).is_file(), mapping["real_end_to_end_test_id"]
        if contract["source_type"] == "workbook_exact":
            assert set(contract["refs"]).issubset(mapping.get("sheet_cell_refs", []))
            excerpt = mapping.get("exact_source_excerpt")
            assert excerpt and "\n" not in excerpt and len(normalized(excerpt)) <= 260
            assert all(normalized(token) in normalized(excerpt) for token in contract["tokens"]), (effect_id, contract["tokens"])
            if cache is not None:
                required_values = [value for ref in contract["refs"] for value in cache.get(ref)]
                assert any(normalized(excerpt) in normalized(value) for value in required_values)
        elif contract["source_type"] == "bwiki_exact":
            assert mapping.get("source_url") == contract["url"]
            assert mapping.get("access_date")
            assert mapping.get("exact_source_excerpt")
            assert all(token in normalized(mapping["exact_source_excerpt"]) for token in contract["tokens"])
            assert not mapping.get("sheet_cell_refs")
        else:
            assert mapping.get("source_artifact") == contract["artifact"]
            assert mapping.get("weapon_source_artifact") == contract["weapon_artifact"]
            assert mapping.get("exact_source_excerpt") is None
            assert set(contract["refs"]).issubset(mapping.get("sheet_cell_refs", []))
            evidence = mapping.get("source_evidence", {})
            assert evidence == {
                "mornye_s3_source_refs": list(contract["refs"]), "mornye_s3_concerto_restore": 25,
                "mornye_s3_relative_momentum_restore": 100, "mornye_s3_internal_cooldown_seconds": 25,
                "account_profile_id": contract["profile_id"], "weapon_id": contract["weapon_id"],
                "weapon_rank": 5, "weapon_concerto_restore": 16, "weapon_internal_cooldown_seconds": 20,
                "separate_source_ids_and_cooldowns": True,
            }
            account = json.loads((ROOT / contract["artifact"]).read_text(encoding="utf-8"))
            equipment = account["profiles"][contract["profile_id"]]["equipment"]
            assert equipment["weapon_id"] == contract["weapon_id"] and equipment["weapon_rank"] == 5
            weapons = json.loads((ROOT / contract["weapon_artifact"]).read_text(encoding="utf-8"))
            weapon = weapons["weapons"][contract["weapon_id"]]
            assert weapon["rank_values"]["5"]["concerto_restore_on_resonance_skill"] == 16.0
            assert weapon["effects"]["resonance_skill_concerto_restore"]["cooldown_seconds"] == 20.0
            assert all(token in interpretation for token in contract["tokens"])


def _rejected(mappings: list[dict]) -> None:
    try:
        validate_mappings(mappings)
    except AssertionError:
        return
    raise AssertionError("semantic source-contract mutation unexpectedly passed")


def run_mutation_checks(mappings: list[dict]) -> None:
    by_id = {mapping["effect_id"]: mapping for mapping in mappings}

    def mutate(effect_id: str) -> list[dict]:
        rows = copy.deepcopy(mappings)
        return rows, next(row for row in rows if row["effect_id"] == effect_id)

    rows, row = mutate("lynae_s1_light_leap_coefficient"); row["sheet_cell_refs"] = [f"{next(iter(CONTRACT['aemeath_s2_tune_packet_normal']['refs'])).split('!')[0]}!C2679:D2679"]; _rejected(rows)
    rows, row = mutate("lynae_s1_paint_application_cadence"); row["sheet_cell_refs"] = []; _rejected(rows)
    rows, row = mutate("lynae_s2_outro_deepen"); row["sheet_cell_refs"] = [f"{next(iter(CONTRACT['lynae_s2_collective_interference_cap']['refs'])).split('!')[0]}!C2728:D2728"]; _rejected(rows)
    rows, row = mutate("mornye_s1_marker_duration"); row["sheet_cell_refs"] = [f"{next(iter(CONTRACT['mornye_s2_field_off_tune_bonus']['refs']))}"]; _rejected(rows)
    rows, row = mutate("mornye_s2_party_crit_damage_formula"); row["sheet_cell_refs"] = []; _rejected(rows)
    rows, row = mutate("mornye_s3_concerto_restore"); row["sheet_cell_refs"] = [f"{next(iter(CONTRACT['mornye_s2_field_off_tune_bonus']['refs']))}"]; _rejected(rows)
    rows, row = mutate("mornye_s3_starfield_independent_trigger"); row["source_type"] = "workbook_exact"; _rejected(rows)
    rows, row = mutate("aemeath_s2_tune_packet_normal"); row["sheet_cell_refs"] = ["base!FF73"]; _rejected(rows)
    rows, row = mutate("aemeath_s2_fusion_c2_enhancement_formula"); row["sheet_cell_refs"] = []; _rejected(rows)
    rows, row = mutate("aemeath_s1_kill_trajectory_transfer_unsupported"); row["exact_source_excerpt"] = "非战斗状态且不处于重击"; _rejected(rows)
    rows, row = mutate("aemeath_s2_tune_stack_duration_refresh"); row["exact_source_excerpt"] = "强化E伤害倍率提升100%"; _rejected(rows)
    rows, row = mutate("aemeath_s2_fusion_c2_enhancement_formula"); row["sheet_cell_refs"] = [next(iter(CONTRACT['aemeath_s2_tune_trajectory_removed_bonus']['refs']))]; row["exact_source_excerpt"] = "200%"; _rejected(rows)
    rows, row = mutate("aemeath_s2_kill_settlement_unsupported"); row["exact_source_excerpt"] = "解锁C2"; _rejected(rows)
    rows, row = mutate("aemeath_s6_tune_response_trajectory_gain"); row["sheet_cell_refs"] = [next(iter(CONTRACT['aemeath_s2_tune_trajectory_removed_bonus']['refs']))]; _rejected(rows)
    rows, row = mutate("aemeath_s6_fusion_application_trajectory_gain"); row["sheet_cell_refs"] = [next(iter(CONTRACT['aemeath_s2_tune_trajectory_removed_bonus']['refs']))]; _rejected(rows)
    rows, row = mutate("aemeath_s6_fusion_fixed_crit"); row["exact_source_excerpt"] = "震谐类型伤害有80%概率"; _rejected(rows)
    rows, row = mutate("aemeath_s1_heavy_crit_damage"); row["implementation_interpretation"] = PLACEHOLDER_INTERPRETATION; _rejected(rows)
    rows, row = mutate("mornye_s3_starfield_independent_trigger"); row["source_type"] = "workbook_exact"; _rejected(rows)
    rows, row = mutate("mornye_s3_starfield_independent_trigger"); row.pop("weapon_source_artifact"); _rejected(rows)
    rows = copy.deepcopy(mappings)
    for row in rows:
        if row["character_id"] == "aemeath":
            row["runtime_code_id"] = "characters/aemeath.py::AemeathMechanic"
    _rejected(rows)


def main() -> None:
    source = json.loads((ROOT / "data/source/user_account_constellation_single_boss_v121.json").read_text(encoding="utf-8"))
    cache = load_source_cache(source)
    validate_mappings(source["effect_mappings"], cache)
    run_mutation_checks(source["effect_mappings"])
    print("account_constellation_v121_full_effect_mapping_completeness_smoke_test ok mappings=46")


if __name__ == "__main__":
    main()
