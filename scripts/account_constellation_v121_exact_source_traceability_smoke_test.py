from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from account_constellation_source_workbook_v121 import load_source_cache
from account_constellation_source_contract_v121 import CONTRACT
from account_constellation_v121_full_effect_mapping_completeness_smoke_test import validate_mappings

REQUIRED = {
    "aemeath_s1_heavy_crit_damage", "aemeath_s2_tune_packet_normal", "aemeath_s2_fusion_c2_enhancement_formula",
    "aemeath_s3_finale_coefficient", "aemeath_s4_party_all_attribute_bonus", "aemeath_s5_fatal_state_shield_revive_unsupported",
    "aemeath_s6_tune_fixed_crit", "lynae_s1_paint_application_cadence", "lynae_s2_outro_duration_and_early_end",
    "mornye_s1_marker_amp_formula", "mornye_s2_party_crit_damage_formula", "mornye_s3_internal_cooldown",
}

def main() -> None:
    source=json.loads((ROOT/'data/source/user_account_constellation_single_boss_v121.json').read_text(encoding='utf-8'))
    cache=load_source_cache(source); mappings={m['effect_id']:m for m in source['effect_mappings']}
    validate_mappings(list(mappings.values()), cache)
    for effect_id in REQUIRED:
        mapping=mappings[effect_id]
        contract=CONTRACT[effect_id]
        assert contract['source_type']=='workbook_exact' and mapping['exact_source_excerpt']
        assert set(contract['refs']).issubset(mapping['sheet_cell_refs'])
        assert any(''.join(mapping['exact_source_excerpt'].split()) in ''.join(str(value).split()) for ref in mapping['sheet_cell_refs'] for value in cache.get(ref))
    print('account_constellation_v121_exact_source_traceability_smoke_test ok')
if __name__=='__main__': main()
