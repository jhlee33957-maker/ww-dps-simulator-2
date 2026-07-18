from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from account_constellation_source_contract_v121 import CONTRACT
from account_constellation_source_workbook_v121 import load_source_cache
def main() -> None:
 source=json.loads((ROOT/'data/source/user_account_constellation_single_boss_v121.json').read_text(encoding='utf-8'))
 cache=load_source_cache(source)
 required={ref for contract in CONTRACT.values() for ref in contract.get('refs', ())}
 referenced={r for m in source['effect_mappings'] for r in m.get('sheet_cell_refs', [])}
 assert required.issubset(referenced)
 assert all(any(v is not None for v in cache.get(r)) for r in referenced)
 print('account_constellation_v121_source_range_sheet_parity_smoke_test ok')
if __name__=='__main__': main()
