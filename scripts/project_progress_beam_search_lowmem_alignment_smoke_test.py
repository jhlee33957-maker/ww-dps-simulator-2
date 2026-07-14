from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.beam_search_lowmem_32gb_plan_contract_smoke_test import EXPECTED_PLAN_SHA256


def main() -> int:
    state = json.loads(Path("PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    text = json.dumps(state, sort_keys=True)
    for required in (
        '"latest_externally_verified_baseline": "112"',
        '"current_candidate": "113"',
        EXPECTED_PLAN_SHA256,
        "beam_search_v113_lowmem_32gb",
        "LOWMEM_WORKSPACE_MANIFEST.json",
        "beam_search_accumulator_chunk_jsonl_gzip_v113",
        "b602af3cd1b87cac1529baa23042e023ce2c90e9d1560426567943da95515fc5",
    ):
        assert required in text, required
    assert '"low_memory_full_search_executed": false' in text
    assert '"mcts_executed": false' in text
    assert '"global_optimum_claimed": false' in text
    assert '"candidate_113_ready_for_3m": false' in text
    assert '"low_memory_10000_probe_status": "corrected_windows_pass_posix_packaged_validation_pending"' in text
    print("project_progress_beam_search_lowmem_alignment_smoke_test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
