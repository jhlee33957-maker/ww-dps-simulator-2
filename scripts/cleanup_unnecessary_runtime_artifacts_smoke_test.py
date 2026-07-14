from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.cleanup_unnecessary_runtime_artifacts import cleanup


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        abandoned = root / "results/beam_search_v111_full_120s"
        calibration = root / "results/beam_search_v111"
        abandoned.mkdir(parents=True)
        calibration.mkdir(parents=True)
        (abandoned / "search_state.json").write_text(json.dumps({"termination_status": "expansion_budget_exhausted", "completed_routes": []}))
        calibration_file = calibration / "execution_result.json"
        calibration_file.write_text('{"combat_duration": 30.0}\n')
        (root / "PROJECT_PROGRESS_STATE.json").write_text('{"current_candidate": "113"}\n')
        dry = cleanup(root, apply=False)
        assert dry["removed_file_count"] == 1
        assert abandoned.exists()
        applied = cleanup(root, apply=True)
        assert applied["removed_file_count"] == 1
        assert not abandoned.exists()
        assert calibration_file.exists()
        assert (root / "results/runtime_cleanup_v113_receipt.json").exists()
    print("cleanup_unnecessary_runtime_artifacts_smoke_test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
