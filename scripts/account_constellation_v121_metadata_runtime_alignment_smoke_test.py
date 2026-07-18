from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.mechanic_events import UNSUPPORTED_AEMEATH_FOLLOWUP_MECHANICS
from account_constellation_source_contract_v121 import CONTRACT
from account_constellation_source_workbook_v121 import load_source_cache
from account_constellation_v121_full_effect_mapping_completeness_smoke_test import validate_mappings


def main() -> None:
    forte = json.loads((ROOT / "data/character_mechanic_effects/aemeath_forte_circuit.json").read_text(encoding="utf-8-sig"))
    assert forte["remaining_unresolved_mechanics"] == [
        "Aemeath S1 kill trajectory transfer",
        "Aemeath S2 kill-triggered detonation",
        "Aemeath S5 all-effects behavior",
        "Multi-target trail tracking",
    ]
    assert UNSUPPORTED_AEMEATH_FOLLOWUP_MECHANICS == [
        "stardust_resonance_extra_effects",
        "aemeath_s1_kill_trajectory_transfer",
        "aemeath_s2_kill_triggered_detonation",
        "aemeath_s5_all_effects",
        "enemy_movement_or_pull",
        "player_survival_effects",
        "multi_target_trajectory_tracking",
    ]

    source = json.loads((ROOT / "data/source/user_account_constellation_single_boss_v121.json").read_text(encoding="utf-8-sig"))
    cache = load_source_cache(source)
    validate_mappings(source["effect_mappings"], cache)
    mappings = {row["effect_id"]: row for row in source["effect_mappings"]}
    required = {
        "aemeath_s2_fusion_base_enhancement_formula": CONTRACT["aemeath_s2_fusion_base_enhancement_formula"]["refs"],
        "aemeath_s2_fusion_c2_enhancement_formula": CONTRACT["aemeath_s2_fusion_c2_enhancement_formula"]["refs"],
        "aemeath_s2_kill_settlement_unsupported": CONTRACT["aemeath_s2_kill_settlement_unsupported"]["refs"],
        "aemeath_s3_enhanced_heavy_mode_application": CONTRACT["aemeath_s3_enhanced_heavy_mode_application"]["refs"],
        "aemeath_s6_fusion_application_trajectory_gain": CONTRACT["aemeath_s6_fusion_application_trajectory_gain"]["refs"],
        "aemeath_s6_fusion_fixed_crit": CONTRACT["aemeath_s6_fusion_fixed_crit"]["refs"],
    }
    for effect_id, source_refs in required.items():
        entry = mappings[effect_id]
        contract = CONTRACT[effect_id]
        assert entry["source_type"] == contract["source_type"] == "workbook_exact"
        assert set(source_refs).issubset(entry["sheet_cell_refs"])
        assert entry["exact_source_excerpt"]
        assert entry["runtime_code_id"] and entry["real_end_to_end_test_id"]
    print("account_constellation_v121_metadata_runtime_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
