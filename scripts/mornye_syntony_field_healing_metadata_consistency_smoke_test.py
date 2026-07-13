from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mornye_syntony_field_heal_test_helpers import HIGH_HEAL, NORMAL_HEAL, execute_to_geopotential, make_sim


TARGET_SCOPE = "host_action_actor_else_active_character"
OLD_TARGET_SCOPE = "active_character_at_trigger_time"
PAYLOAD_IDS = ("mornye_syntony_field_heal", "mornye_high_syntony_field_heal")


def load_json(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def assert_no_old_value(value: Any, label: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            assert_no_old_value(child, f"{label}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_no_old_value(child, f"{label}[{index}]")
    else:
        assert value != OLD_TARGET_SCOPE, f"{label} still uses {OLD_TARGET_SCOPE}"


def assert_manifest_scope_fields(manifest: dict[str, Any], label: str) -> None:
    section = manifest["mornye_syntony_field_healing_patches"]
    assert section["formula"]["target_scope"] == TARGET_SCOPE
    for record in section["payloads"]:
        if record["action_id"] in PAYLOAD_IDS:
            assert record["record"]["mechanic_effects"]["target_scope"] == TARGET_SCOPE
    for record in section["action_metadata_records"]:
        if record["action_id"] in {"mornye_heavy_geopotential_shift", "mornye_liberation_critical_protocol"}:
            assert record["fields"]["mechanic_effects"]["scheduled_healing_target_scope"] == TARGET_SCOPE
    for record in section["transition_metadata_records"]:
        if record["action_id"] == "mornye_intro_convergence":
            assert record["fields"]["mechanic_effects"]["scheduled_healing_target_scope"] == TARGET_SCOPE
    assert_no_old_value(section, label)


def main() -> None:
    actions = load_json("data/actions.json")
    actions_by_id = {row["id"]: row for row in actions}
    for action_id in PAYLOAD_IDS:
        effects = actions_by_id[action_id]["mechanic_effects"]
        assert effects["target_scope"] == TARGET_SCOPE
        assert_no_old_value(effects, f"action:{action_id}.mechanic_effects")

    transitions = load_json("data/transition_actions.json")
    transitions_by_id = {row["id"]: row for row in transitions}
    intro_effects = transitions_by_id["mornye_intro_convergence"]["mechanic_effects"]
    assert intro_effects["scheduled_healing_target_scope"] == TARGET_SCOPE
    assert_no_old_value(intro_effects, "transition:mornye_intro_convergence.mechanic_effects")

    sim = make_sim()
    execute_to_geopotential(sim)
    normal_effect = sim.scheduled_effect_by_instance_id(NORMAL_HEAL)
    assert normal_effect is not None
    assert normal_effect.metadata["target_scope"] == TARGET_SCOPE
    assert_no_old_value(normal_effect.metadata, "runtime:normal_heal.metadata")

    assert sim.execute_action("mornye_resonance_liberation")
    high_effect = sim.scheduled_effect_by_instance_id(HIGH_HEAL)
    assert high_effect is not None
    assert high_effect.metadata["target_scope"] == TARGET_SCOPE
    assert_no_old_value(high_effect.metadata, "runtime:high_heal.metadata")

    root_manifest = (ROOT / "direct_action_data_patch_manifest_v61.json").read_bytes()
    source_manifest = (ROOT / "data" / "source" / "direct_action_data_patch_manifest_v61.json").read_bytes()
    assert root_manifest == source_manifest
    manifest = json.loads(root_manifest.decode("utf-8"))
    assert_manifest_scope_fields(manifest, "manifest:mornye_syntony_field_healing_patches")

    report = (ROOT / "reports" / "mornye_syntony_field_healing_scheduler_audit.md").read_text(encoding="utf-8")
    assert TARGET_SCOPE in report
    assert OLD_TARGET_SCOPE not in report
    assert "Intro and generic swaps therefore target the incoming character" in report
    assert "Mornye remains the source-stat owner" in report

    progress = load_json("PROJECT_PROGRESS_STATE.json")
    task = progress["current_in_progress_task"]
    assert task["normal_syntony_field_healing"]["target_scope"] == TARGET_SCOPE
    assert task["high_syntony_field_healing"]["target_scope"] == TARGET_SCOPE
    assert task["transition_target_resolution"]["target_scope"] == TARGET_SCOPE
    assert_no_old_value(task["normal_syntony_field_healing"], "progress.normal_syntony_field_healing")
    assert_no_old_value(task["high_syntony_field_healing"], "progress.high_syntony_field_healing")
    assert_no_old_value(task["transition_target_resolution"], "progress.transition_target_resolution")

    print("mornye_syntony_field_healing_metadata_consistency_smoke_test ok")


if __name__ == "__main__":
    main()
