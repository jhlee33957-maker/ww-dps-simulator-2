from __future__ import annotations

from copy import deepcopy
import json

from pydantic import ValidationError

from v124_timing_test_support import DATA_DIR, MORNYE_LIBERATION_ID, make_mornye_liberation_sim
from simulator.action_timing_contract import ActionTimingContract, load_action_timing_contracts


def assert_required_contract(contract: ActionTimingContract) -> None:
    assert contract.action_id == MORNYE_LIBERATION_ID
    audit = json.loads((DATA_DIR.parent / "audit_inputs" / "WW_3CHAR_ACTION_TIMING_AUDIT_V2.json").read_text(encoding="utf-8"))
    audit_action = next(item for item in audit["actions"] if item["action_id"] == MORNYE_LIBERATION_ID)
    assert contract.source_refs == audit_action["source_refs"] == [
        "角色-女!A4150:AT4150",
        "角色-女!A4153:AT4153",
        "角色-女!A4154:AT4154",
    ]
    assert contract.same_character_input_frame is None
    assert contract.swap_input_frame is None
    assert contract.action_end_frame is None
    variants = {variant.variant_id: variant for variant in contract.timing_variants}
    assert set(variants) == {"normal", "observation"}
    normal, observation = variants["normal"], variants["observation"]
    assert normal.condition.observation_state_active is False
    assert observation.condition.observation_state_active is True
    assert (
        normal.legacy_hit_frame_overrides,
        normal.same_character_input_frame,
        normal.swap_input_frame,
        normal.source_action_end_frame,
        normal.lifecycle_end_frame,
        normal.global_time_stop_frames,
    ) == ([272], 282, 300, 282, 300, 300)
    assert (
        observation.legacy_hit_frame_overrides,
        observation.same_character_input_frame,
        observation.swap_input_frame,
        observation.source_action_end_frame,
        observation.lifecycle_end_frame,
        observation.global_time_stop_frames,
    ) == ([277], 296, 300, 296, 300, 300)
    assert normal.source_action_end_frame < normal.swap_input_frame
    assert observation.source_action_end_frame < observation.swap_input_frame
    sim = make_mornye_liberation_sim(False)
    legacy_hit_count = len(sim.actions[MORNYE_LIBERATION_ID].hits)
    assert len(normal.legacy_hit_frame_overrides) == legacy_hit_count
    assert len(observation.legacy_hit_frame_overrides) == legacy_hit_count


def expect_rejected(payload: dict) -> None:
    try:
        contract = ActionTimingContract.model_validate(payload)
        assert_required_contract(contract)
    except (AssertionError, ValidationError, ValueError):
        return
    raise AssertionError("invalid Mornye timing contract mutation was accepted")


def main() -> None:
    contract = load_action_timing_contracts(DATA_DIR)[MORNYE_LIBERATION_ID]
    assert_required_contract(contract)
    source = contract.model_dump(mode="json")

    for static_frame in (282, 296):
        mutation = deepcopy(source)
        mutation["timing_variants"] = []
        mutation["same_character_input_frame"] = static_frame
        mutation["swap_input_frame"] = 300
        mutation["action_end_frame"] = 300
        expect_rejected(mutation)

    source_end_mutation = deepcopy(source)
    source_end_mutation["timing_variants"][0]["source_action_end_frame"] = 300
    expect_rejected(source_end_mutation)

    lifecycle_mutation = deepcopy(source)
    lifecycle_mutation["timing_variants"][1]["lifecycle_end_frame"] = 299
    expect_rejected(lifecycle_mutation)
    print("mornye_liberation_timing_variant_schema_v124_smoke_test ok mutations_rejected=4")


if __name__ == "__main__":
    main()
