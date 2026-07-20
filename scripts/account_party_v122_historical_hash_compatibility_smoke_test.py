from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rl.demo_contract import party_config_hash
from simulator.account_config_contract import account_config_hash


def main() -> None:
    assert party_config_hash(root=ROOT) == "baff722d9ce79cf7f57891c439b7b3fd746ad76e779e4d582eaa51802eba2684"
    assert hashlib.sha256((ROOT / "data/build_profiles.json").read_bytes()).hexdigest() == "fe0e46aaddb818ecd9b0180b3aa955671328a03c179e9dd5f8b9a7fc85506aa7"
    assert hashlib.sha256((ROOT / "data/weapons.json").read_bytes()).hexdigest() == "1e5595c9c9cb1b300d5f0e21b1f493b527f2868503511b6c1c467209b3c8df33"
    assert account_config_hash(ROOT) != party_config_hash(root=ROOT)
    progress = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    assert progress["candidate_124_timing_core_1"]["historical_results_status"] == "preserved_but_requires_timing_rebaseline"
    print("account_party_v122_historical_hash_compatibility_smoke_test ok")


if __name__ == "__main__":
    main()
