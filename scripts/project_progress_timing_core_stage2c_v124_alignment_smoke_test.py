from __future__ import annotations
import json
from pathlib import Path


def main() -> None:
    progress = json.loads((Path(__file__).resolve().parents[1] / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8-sig"))
    current = progress["candidate_history"][-1]
    assert current["candidate"] == "124" and current["stage"] == "timing-core-2c-mornye-inversion-distributed-array"
    assert current["mornye_heavy_inversion_packet_timing_implemented"] is True
    assert current["distributed_array_complete_first_cast_concerto"] == 51
    assert current["training_search_blocked"] is True and current["account_first_cycle_executed"] is False
    print("project_progress_timing_core_stage2c_v124_alignment_smoke_test ok")


if __name__ == "__main__": main()
