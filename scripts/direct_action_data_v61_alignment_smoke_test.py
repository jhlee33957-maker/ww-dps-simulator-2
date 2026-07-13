from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from apply_direct_action_data_v61 import apply_manifest
from simulator.action_executor import resolve_action_timing
from simulator.models import ActionData
from simulator.transition_actions import transition_action_to_action_data


MANIFEST_PATH = DATA_DIR / "source" / "direct_action_data_patch_manifest_v61.json"
ACTIONS_PATH = DATA_DIR / "actions.json"
TRANSITIONS_PATH = DATA_DIR / "transition_actions.json"
TUNE_RESPONSES_PATH = DATA_DIR / "tune_responses.json"


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-9) -> None:
    assert math.isclose(float(actual), float(expected), rel_tol=tolerance, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def indexed(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    duplicates: list[str] = []
    for record in records:
        action_id = record["id"]
        if action_id in result:
            duplicates.append(action_id)
        result[action_id] = record
    assert not duplicates, f"duplicate ids: {sorted(set(duplicates))}"
    return result


def action_after_total(patch: dict[str, Any]) -> tuple[str, float]:
    after = patch["after"]
    if patch["damage_kind"] == "tune_break":
        return "tune_break", float(after["tune_break_total"])
    return "normal", float(after["damage_total"])


def test_manifest_records_match_runtime_json() -> None:
    manifest = load_json(MANIFEST_PATH)
    actions = load_json(ACTIONS_PATH)
    transitions = load_json(TRANSITIONS_PATH)
    action_records = indexed(actions)
    transition_records = indexed(transitions)

    assert len(manifest["action_patches"]) == 74
    assert len(manifest["transition_action_patches"]) == 4

    for patch in manifest["action_patches"]:
        action_id = patch["action_id"]
        assert action_id in action_records, f"{action_id} missing from data/actions.json"
        record = action_records[action_id]
        after = patch["after"]
        for field in (
            "duration",
            "action_time",
            "combat_time_cost",
            "resonance_energy_gain",
            "concerto_energy_gain",
        ):
            assert_close(record[field], after[field], f"{action_id}.{field}")
        assert record["action_time"] >= record["combat_time_cost"], action_id

        kind, total = action_after_total(patch)
        if total <= 0.0:
            assert record["damage_multiplier"] == 0.0
            assert record["tune_break_multiplier"] == 0.0
            assert record.get("hits", []) == []
            continue

        hits = record.get("hits", [])
        assert len(hits) == 1, f"{action_id} should use one lumped hit"
        hit = hits[0]
        assert_close(hit["time"], record["action_time"], f"{action_id}.hit.time")
        if kind == "tune_break":
            assert hit["damage_category"] == "tune_break"
            assert_close(hit["tune_break_multiplier"], total, f"{action_id}.hit.tune_break_multiplier")
            assert_close(record["tune_break_multiplier"], total, f"{action_id}.tune_break_multiplier")
            assert record["damage_multiplier"] == 0.0
        else:
            assert hit["damage_category"] == record.get("damage_category", "normal")
            assert_close(hit["damage_multiplier"], total, f"{action_id}.hit.damage_multiplier")
            assert_close(record["damage_multiplier"], total, f"{action_id}.damage_multiplier")
            assert record["tune_break_multiplier"] == 0.0

    for patch in manifest["transition_action_patches"]:
        action_id = patch["action_id"]
        assert action_id in transition_records, f"{action_id} missing from data/transition_actions.json"
        record = transition_records[action_id]
        after = patch["after"]
        for field in ("action_time", "combat_time_cost", "resonance_energy_gain", "concerto_energy_gain"):
            assert_close(record[field], after[field], f"{action_id}.{field}")
        assert record["action_time"] >= record["combat_time_cost"], action_id
        assert record["hits"] == [float(after["damage_total"])]


def test_mornye_scaling_and_damage_corrections() -> None:
    manifest = load_json(MANIFEST_PATH)
    actions = indexed(load_json(ACTIONS_PATH))

    for patch in manifest["action_patches"]:
        action_id = patch["action_id"]
        record = actions[action_id]
        if (
            record.get("character_id") == "mornye"
            and patch.get("damage_kind") == "direct"
            and float(patch["after"].get("damage_total", 0.0)) > 0.0
            and patch.get("preserve_scaling") is True
        ):
            assert record.get("scaling_stat") == "def", f"{action_id} should remain DEF scaling"

    assert_close(actions["aemeath_tune_break"]["tune_break_multiplier"], 12.0, "aemeath_tune_break correction")
    assert_close(actions["mornye_heavy_geopotential_shift"]["damage_multiplier"], 0.4414, "mornye GP correction")
    assert_close(actions["mornye_tune_break"]["tune_break_multiplier"], 12.0, "mornye_tune_break correction")
    manifest_ids = {patch["action_id"] for patch in manifest["action_patches"]}
    assert "mornye_syntony_field_damage" not in manifest_ids
    assert actions["mornye_syntony_field_damage"].get("hits"), "syntony field damage should remain a separate event"


def test_runtime_timing_branches() -> None:
    actions = {record["id"]: ActionData(**record) for record in load_json(ACTIONS_PATH)}

    assert resolve_action_timing(actions["aemeath_tune_break"], {}) == (90 / 60, 0.0)
    assert resolve_action_timing(actions["aemeath_tune_break"], {"form": "mech"}) == (94 / 60, 0.0)

    assert resolve_action_timing(actions["mornye_liberation_critical_protocol"], {}) == (282 / 60, 0.0)
    assert resolve_action_timing(
        actions["mornye_liberation_critical_protocol"],
        {"mode": "wide_field_observation"},
    ) == (296 / 60, 0.0)

    assert resolve_action_timing(actions["lynae_kaleidoscopic_basic_stage_1"], {}) == (35 / 60, 35 / 60)
    assert resolve_action_timing(actions["lynae_kaleidoscopic_basic_stage_1"], {"lumiflow": 120.0}) == (
        40 / 60,
        40 / 60,
    )

    assert resolve_action_timing(actions["aemeath_heavy_aemeath_charged_2"], {"instant_response": True}) == (
        91 / 60,
        91 / 60,
    )
    assert resolve_action_timing(actions["aemeath_heavy_mech_charged_2"], {"instant_response": True}) == (
        56 / 60,
        56 / 60,
    )


def test_order_tune_responses_constellation_and_models() -> None:
    actions, _transitions, changes, summary = apply_manifest()
    assert not changes, "apply script should find no differences after --apply"
    assert summary["action_id_order_unchanged"] is True
    assert summary["policy_selectable_action_id_order_unchanged"] is True

    tune_responses = indexed(load_json(TUNE_RESPONSES_PATH))
    assert_close(tune_responses["aemeath_starburst"]["multiplier"], 5.9643, "Aemeath tune response")
    assert_close(tune_responses["mornye_particle_jet"]["multiplier"], 2.9822, "Mornye tune response")
    assert_close(tune_responses["lynae_spectral_analysis"]["multiplier"], 18.8075, "Lynae tune response")

    action_records = indexed(actions)
    variants = {
        "lynae_iridescent_splash_c3": (8.13, 7.65),
        "lynae_visual_impact_c3": (14.05, 14.58),
        "lynae_polychrome_leap_stage_1_c1": (2.25, 5.40),
        "lynae_polychrome_leap_stage_2_c1": (0.38, 0.90),
        "lynae_polychrome_leap_stage_3_c1": (0.60, 1.40),
        "lynae_resonance_liberation_prismatic_overblast_c5": (0.0, 20.0),
    }
    for action_id, (resonance, concerto) in variants.items():
        assert action_id in action_records
        assert_close(action_records[action_id]["resonance_energy_gain"], resonance, f"{action_id}.RE")
        assert_close(action_records[action_id]["concerto_energy_gain"], concerto, f"{action_id}.CE")
        base_id = action_id.rsplit("_c", 1)[0]
        assert base_id in action_records, f"{action_id} should remain separate from {base_id}"
        assert action_records[action_id]["id"] != action_records[base_id]["id"]

    for record in actions:
        ActionData(**record)
    for record in load_json(TRANSITIONS_PATH):
        transition_action_to_action_data(record)


def main() -> None:
    test_manifest_records_match_runtime_json()
    test_mornye_scaling_and_damage_corrections()
    test_runtime_timing_branches()
    test_order_tune_responses_constellation_and_models()
    print("direct_action_data_v61_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
