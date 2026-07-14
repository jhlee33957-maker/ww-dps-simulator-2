from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_plan import V115_RESUME_V114_PLAN_PATH, load_plan
from search.beam_resume_extension import load_reviewed_inventory, sha256_file, validate_hash_pinned_extension


def main() -> None:
    plan = load_plan(V115_RESUME_V114_PLAN_PATH)
    checkpoint = plan["source_checkpoint_contract"]
    reviewed = load_reviewed_inventory(project_root=ROOT, checkpoint_contract=checkpoint)
    assert reviewed["file_count"] == 649 and reviewed["total_bytes"] == 1752618157
    output = ROOT / plan["output_contract"]["canonical_output_root"]
    if output.exists():
        before = sha256_file(output / "search_state.json")
        result = validate_hash_pinned_extension(project_root=ROOT, plan_path=V115_RESUME_V114_PLAN_PATH,
            plan=plan, stage=plan["stages"][0], output_root=output, write_receipt=True)
        assert result["state_sha256_before"] == result["state_sha256_after"] == before
        receipt = result["receipt"]
        assert receipt["source_best_partial_combat_time"] == 67.48333333333329
        assert receipt["source_best_partial_current_time"] == 107.75000000000001
        assert receipt["source_best_partial_total_damage"] == 2850679.8061139295
        assert receipt["source_best_partial_action_count"] == 92
        assert result["inventory"]["entries"] == reviewed["entries"]
    else:
        assert checkpoint["search_state_sha256"] == "f1ac52b960465a7ea71ea8495b1c1f2d89a79766d5cdf2f6ad3e4872d2e25630"
        print("real checkpoint absent; compact reviewed inventory contract validated only")
    print("beam_search_v115_real_checkpoint_inventory_contract_smoke_test ok")


if __name__ == "__main__":
    main()
