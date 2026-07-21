from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.action_timing_contract import ActionTimingContract, ROLE_FEMALE_SHEET, load_action_timing_contracts
from scripts.lynae_polychrome_leap_stage2_frame1_resource_timing_v124_smoke_test import ready_stage_2


def main() -> None:
    contract = load_action_timing_contracts(ROOT / "data")["lynae_polychrome_leap_stage_2"]
    audit = json.loads((ROOT / "audit_inputs" / "WW_3CHAR_ACTION_TIMING_AUDIT_V2.json").read_text(encoding="utf-8"))
    audit_action = next(item for item in audit["actions"] if item["action_id"] == contract.action_id)
    assert contract.same_character_input_frame == 36
    assert contract.swap_input_frame is None and contract.source_action_end_frame is None
    assert contract.unresolved_swap_runtime_fallback_frame == 36
    assert contract.action_end_frame == contract.scheduled_payload_end_frame == 42
    assert contract.global_time_stop_frames == 0
    assert contract.source_refs[:5] == audit_action["source_refs"]
    resource, rupture, strain = contract.scheduled_packet_groups
    assert resource.scheduled_frames == [1]
    assert resource.source_frame_row_ref == f"{ROLE_FEMALE_SHEET}!A2647:AT2647"
    assert rupture.mode_selection == "tune_rupture" and strain.mode_selection == "tune_strain"
    assert rupture.scheduled_frames == strain.scheduled_frames == [12, 18, 24, 30, 36, 42]
    assert rupture.source_frame_row_ref == f"{ROLE_FEMALE_SHEET}!A2649:AT2649"
    assert strain.source_frame_row_ref == f"{ROLE_FEMALE_SHEET}!A2650:AT2650"
    assert rupture.source_coefficient_resource_row_ref == strain.source_coefficient_resource_row_ref == "dmg!A2474:DF2474"

    raw = json.loads((ROOT / "data" / "action_timing_contract_v124.json").read_text(encoding="utf-8"))
    raw_contract = next(item for item in raw["actions"] if item["action_id"] == contract.action_id)
    for mutate in (
        lambda value: value["scheduled_packet_groups"][1].__setitem__("scheduled_frames", [12, 18, 24, 30, 36]),
        lambda value: value.__setitem__("swap_input_frame", 42),
        lambda value: value.__setitem__("source_action_end_frame", 36),
        lambda value: value.__setitem__("source_action_end_frame", 42),
        lambda value: value.__setitem__("unresolved_swap_runtime_fallback_frame", 42),
        lambda value: value.pop("unresolved_swap_runtime_fallback_frame"),
        lambda value: value["scheduled_packet_groups"][1].__setitem__("detachable", True),
        lambda value: value["scheduled_packet_groups"][2].__setitem__("mode_selection", "tune_rupture"),
    ):
        mutated = copy.deepcopy(raw_contract)
        mutate(mutated)
        try:
            ActionTimingContract.model_validate(mutated)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid Stage-2 packet contract mutation was accepted")

    sim = ready_stage_2()
    assert sim.execute_action("lynae_polychrome_leap")
    instance = next(
        item for item in sim.state.ongoing_action_instances
        if item.source_action_id == "lynae_polychrome_leap_stage_2"
    )
    assert instance.selected_swap_input_frame is None
    assert instance.effective_swap_lock_source == "unresolved_swap_same_character_control_fallback"
    assert instance.effective_swap_lock_until_wall_time == instance.start_wall_time + 36 / 60
    assert instance.swap_lock_until_wall_time == instance.effective_swap_lock_until_wall_time
    assert instance.swap_lock_until_wall_time != instance.lifecycle_end_wall_time
    print("lynae_polychrome_leap_stage2_packet_contract_v124_smoke_test ok")


if __name__ == "__main__":
    main()
