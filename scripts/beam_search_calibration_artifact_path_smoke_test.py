from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "results" / "beam_search_v111"


def main() -> None:
    summary = json.loads((RESULT_ROOT / "calibration_result_summary.json").read_text(encoding="utf-8"))
    execution = json.loads((RESULT_ROOT / "execution_result.json").read_text(encoding="utf-8"))
    replay = execution["route_replay_summaries"][0]
    paths = summary["canonical_paths"]
    assert paths["replay_summary"] == "results/beam_search_v111/routes/a301f753b3ddf6e4_summary.json"
    assert paths["replay_timeline"] == "results/beam_search_v111/routes/a301f753b3ddf6e4_timeline.csv"
    assert paths["replay_summary"] == f"results/beam_search_v111/{replay['summary_path']}"
    assert paths["replay_timeline"] == f"results/beam_search_v111/{replay['timeline_csv_path']}"
    for name, path_text in paths.items():
        assert (ROOT / path_text).exists(), f"{name}: {path_text}"
    print("beam_search_calibration_artifact_path_smoke_test ok")


if __name__ == "__main__":
    main()
