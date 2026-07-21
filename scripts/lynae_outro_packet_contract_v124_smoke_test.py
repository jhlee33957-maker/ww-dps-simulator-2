from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.action_timing_contract import ActionTimingContract, ROLE_FEMALE_SHEET, load_action_timing_contracts


def main() -> None:
    contract = load_action_timing_contracts(ROOT / "data")["lynae_outro_lets_hit_the_road"]
    first, second = contract.scheduled_packet_groups
    assert contract.same_character_input_frame == contract.swap_input_frame == 0
    assert contract.transition_start_frame == 0
    assert contract.source_control_effective_frame == 153
    assert contract.source_action_end_frame == contract.action_end_frame == 181
    assert contract.global_time_stop_frames == 0
    assert contract.transition_source_persistence is True
    assert first.scheduled_frames == [52, 58, 64, 70, 76, 82, 88, 94, 100, 106, 112, 118]
    assert second.scheduled_frames == [92, 98, 104, 110, 116, 122, 128, 134, 140, 146]
    assert first.packet_count == 12 and second.packet_count == 10
    assert first.detachable is False and first.cancel_on_swap is False
    assert first.cancel_on_generic_owner_exit is False and first.persist_after_swap is False
    assert first.transition_source_persistence is True and first.cancel_on_outro_transition is False
    assert second.detachable is True and second.cancel_on_swap is False
    assert second.persist_after_swap is True and second.transition_source_persistence is True
    expected_refs = [
        f"{ROLE_FEMALE_SHEET}!A2699:AT2699",
        f"{ROLE_FEMALE_SHEET}!A2700:AT2700",
        f"{ROLE_FEMALE_SHEET}!A2701:AT2701",
        "dmg!A2486:DF2486",
        "dmg!A2487:DF2487",
        "verified_transition_runtime:lynae_outro_zero_time",
    ]
    assert contract.source_refs == expected_refs
    assert first.source_frame_row_ref == expected_refs[1]
    assert first.source_refs == [expected_refs[1], expected_refs[3]]
    assert second.source_frame_row_ref == expected_refs[2]
    assert second.source_refs == [expected_refs[2], expected_refs[4]]
    assert all("?" not in ref and "\ufffd" not in ref and "\ufeff" not in ref for ref in expected_refs)

    payload = json.loads((ROOT / "data" / "action_timing_contract_v124.json").read_text(encoding="utf-8"))
    raw_contract = next(item for item in payload["actions"] if item["action_id"] == contract.action_id)
    audit = json.loads((ROOT / "audit_inputs" / "WW_3CHAR_ACTION_TIMING_AUDIT_V2.json").read_text(encoding="utf-8"))
    audit_action = next(item for item in audit["actions"] if item["action_id"] == contract.action_id)
    assert audit_action["source_refs"] == expected_refs[:3]
    assert contract.source_refs[:3] == audit_action["source_refs"]
    for mutate in (
        lambda value: value["source_refs"].__setitem__(0, f"{ROLE_FEMALE_SHEET}?A2699:AT2699"),
        lambda value: value["source_refs"].__setitem__(1, f"{ROLE_FEMALE_SHEET}!A2702:AT2702"),
        lambda value: value["scheduled_packet_groups"][0].__setitem__("source_frame_row_ref", "mojibake:A2700"),
        lambda value: value["scheduled_packet_groups"][1].__setitem__(
            "source_coefficient_resource_row_ref", "dmg!A2486:DF2486"
        ),
        lambda value: value["source_refs"].__setitem__(0, "\ufffdA2699:AT2699"),
        lambda value: value["source_refs"].__setitem__(0, f"\ufeff{ROLE_FEMALE_SHEET}!A2699:AT2699"),
    ):
        mutated = copy.deepcopy(raw_contract)
        mutate(mutated)
        try:
            ActionTimingContract.model_validate(mutated)
        except ValueError:
            pass
        else:
            raise AssertionError("mutated Lynae Outro source join must be rejected")
    print("lynae_outro_packet_contract_v124_smoke_test ok")


if __name__ == "__main__":
    main()
