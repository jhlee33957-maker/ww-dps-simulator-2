from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_plan import V115_RESUME_V114_PLAN_PATH, load_plan
from search.beam_resume_extension import sha256_file, validate_hash_pinned_extension


def main() -> None:
    output = ROOT / "results/beam_search_v114_lowmem_32gb"
    if output.exists():
        state = output / "search_state.json"
        before = sha256_file(state)
        plan = load_plan(V115_RESUME_V114_PLAN_PATH)
        result = validate_hash_pinned_extension(
            project_root=ROOT,
            plan_path=V115_RESUME_V114_PLAN_PATH,
            plan=plan,
            stage=plan["stages"][0],
            output_root=output,
            write_receipt=False,
        )
        receipt, inventory = result["receipt"], result["inventory"]
        assert before == sha256_file(state) == result["state_sha256_after"]
        assert inventory["file_count"] == 649 and inventory["total_bytes"] == 1752618157
        assert receipt["source_best_partial_total_damage"] == 2850679.8061139295
        assert receipt["long_resume_executed"] is False
    else:
        from search.beam_plan import validate_plan
        assert validate_plan(load_plan(V115_RESUME_V114_PLAN_PATH), plan_path=V115_RESUME_V114_PLAN_PATH)["status"] == "ok"
        print("real local checkpoint absent; fixture/source contract validated and checkpoint remains an external resume prerequisite")
    print("beam_search_v115_resume_extension_validation_smoke_test ok")


if __name__ == "__main__":
    main()
