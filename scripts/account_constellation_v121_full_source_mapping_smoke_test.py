from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from account_constellation_source_workbook_v121 import load_source_cache
from account_constellation_source_contract_v121 import CONTRACT
from account_constellation_v121_full_effect_mapping_completeness_smoke_test import validate_mappings
def main() -> None:
 source=json.loads((ROOT/'data/source/user_account_constellation_single_boss_v121.json').read_text(encoding='utf-8'))
 cache=load_source_cache(source); mappings=source['effect_mappings']
 validate_mappings(mappings, cache)
 for m in mappings:
  assert m['runtime_code_id'] and (ROOT/m['real_end_to_end_test_id']).exists()
  contract=CONTRACT[m['effect_id']]
  if contract['source_type']=='workbook_exact':
   assert m['exact_source_excerpt'] and any(''.join(str(m['exact_source_excerpt']).split()) in ''.join(str(v).split()) for r in m['sheet_cell_refs'] for v in cache.get(r))
  elif contract['source_type']=='bwiki_exact':
   assert m['source_url']==contract['url'] and m['access_date'] and m['exact_source_excerpt']
  else:
   assert m['source_artifact']==contract['artifact'] and m['exact_source_excerpt'] is None
 print('account_constellation_v121_full_source_mapping_smoke_test ok')
if __name__=='__main__': main()
