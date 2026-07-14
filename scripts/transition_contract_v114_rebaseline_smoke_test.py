from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    summary = json.loads((ROOT / "results/manual_120s_baseline_v114_summary.json").read_text(encoding="utf-8"))
    assert summary["schema_version"] == "manual_120s_baseline_v114"
    assert summary["completed_120s"]
    assert summary["final_combat_time"] == 120.0
    assert summary["runtime_contract"]["observation_version"] == "slot_generic_mechanics_v5"
    assert summary["runtime_contract"]["observation_shape"] == 314
    assert summary["runtime_contract"]["policy_action_count"] == 25
    assert summary["raw_route_sha256"] == "c510204b78fc547e2ba1224e82193cbaf43728d9a4107eb1090b6ebaab59a90a"
    assert summary["generic_swap_count"] > 0
    assert summary["aemeath_outro_cast_count"] == 3
    assert summary["aemeath_outro_upgrade_count"] == 3
    assert summary["aemeath_outro_upgrade_counts_by_recipient"] == {"lynae": 3}
    assert summary["total_damage"] == 5268418.084869607
    assert summary["dps"] == 43903.484040580064
    assert summary["selected_route_sha256"] == "e3ddea873cb5059bd29a8a9eb7165ea0e45a9a9e4fa4f68e5e229db2f622daf1"
    assert summary["resolved_route_sha256"] == "3edca6f6f258999a9c915a9ec32ee88c0db570d2303846e0fb8b6da367970229"
    assert summary["runtime_contract"]["party_config_hash"] == "baff722d9ce79cf7f57891c439b7b3fd746ad76e779e4d582eaa51802eba2684"
    assert summary["runtime_contract"]["transition_config_sha256"] == "210538d4bf99789d0af08ecff5fb76dc3f472f5b170a144d9f1b3b1f46116b9c"
    assert (ROOT / "results/manual_120s_baseline_v114_timeline.csv").exists()
    assert (ROOT / "reports/manual_120s_baseline_v114.md").exists()
    print("transition_contract_v114_rebaseline_smoke_test ok")


if __name__ == "__main__":
    main()
