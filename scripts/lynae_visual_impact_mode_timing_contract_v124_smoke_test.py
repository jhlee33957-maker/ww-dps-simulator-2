from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.action_timing_contract import ActionTimingContract, load_action_timing_contracts


def main() -> None:
    contract = load_action_timing_contracts(ROOT / "data")["lynae_visual_impact"]
    assert contract.scheduled_payload_end_frame == 45
    variants = {item.variant_id: item for item in contract.timing_variants}
    assert (variants["tune_rupture"].source_action_end_frame, variants["tune_rupture"].same_character_input_frame, variants["tune_rupture"].lifecycle_end_frame) == (42, 53, 53)
    assert (variants["tune_strain"].source_action_end_frame, variants["tune_strain"].same_character_input_frame, variants["tune_strain"].lifecycle_end_frame) == (42, 59, 59)
    assert variants["tune_rupture"].swap_input_frame is None and variants["tune_rupture"].unresolved_swap_runtime_fallback_frame == 53
    assert variants["tune_strain"].swap_input_frame is None and variants["tune_strain"].unresolved_swap_runtime_fallback_frame == 59
    groups = {item.mode_selection: item for item in contract.scheduled_packet_groups}
    assert groups["tune_rupture"].scheduled_frames == groups["tune_strain"].scheduled_frames == [45]
    assert groups["tune_rupture"].source_frame_row_ref.endswith("A2682:AT2682") and groups["tune_rupture"].source_coefficient_resource_row_ref == "dmg!A2464:DF2464"
    assert groups["tune_strain"].source_frame_row_ref.endswith("A2681:AT2681") and groups["tune_strain"].source_coefficient_resource_row_ref == "dmg!A2465:DF2465"
    raw = json.loads((ROOT / "data" / "action_timing_contract_v124.json").read_text(encoding="utf-8"))
    item = next(value for value in raw["actions"] if value["action_id"] == "lynae_visual_impact")
    for mutate in (
        lambda value: value["timing_variants"][0].__setitem__("lifecycle_end_frame", 70),
        lambda value: value["timing_variants"][1].__setitem__("same_character_input_frame", 70),
        lambda value: value["scheduled_packet_groups"][0].__setitem__("scheduled_frames", [45, 45]),
    ):
        changed = copy.deepcopy(item); mutate(changed)
        try: ActionTimingContract.model_validate(changed)
        except ValueError: pass
        else: raise AssertionError("invalid Visual Impact timing mutation accepted")
    print("lynae_visual_impact_mode_timing_contract_v124_smoke_test ok")


if __name__ == "__main__": main()
