from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_dashboard():
    fake_streamlit = types.SimpleNamespace(cache_data=lambda **_kwargs: (lambda function: function))
    original = sys.modules.get("streamlit")
    sys.modules["streamlit"] = fake_streamlit
    try:
        spec = importlib.util.spec_from_file_location("progress_dashboard_under_test", ROOT / "progress_dashboard.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if original is None:
            del sys.modules["streamlit"]
        else:
            sys.modules["streamlit"] = original


def _status_by_stage(data: dict) -> dict[str, str]:
    return {item["stage"]: item["status"] for item in data["stage_status"]}


def main() -> None:
    dashboard = _load_dashboard()
    fallback = dashboard.EMBEDDED_PROGRESS_SNAPSHOT
    fallback_status = _status_by_stage(fallback)
    assert fallback_status["Beam Search 인프라"] == "외부 검증"
    assert fallback_status["Beam Search 30초 보정"] == "내부 검증"
    assert fallback_status["Beam Search 120초 탐색"] == "미착수"
    assert fallback_status["MCTS"] == "미착수"
    assert fallback["beam_stages"][0]["status"] == "내부 검증"
    assert fallback["beam_stages"][1]["status"] == "미착수"

    progress = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8-sig"))
    plan = json.loads((ROOT / "data" / "beam_search_plan_v111.json").read_text(encoding="utf-8"))
    merged, source_mode = dashboard.merge_progress_data(
        fallback,
        {"PROJECT_PROGRESS_STATE.json": {"data": progress}, "data/beam_search_plan_v111.json": {"data": plan}},
    )
    assert source_mode == "저장소 최신 데이터"
    merged_status = _status_by_stage(merged)
    assert merged_status["Beam Search 인프라"] == "외부 검증"
    assert merged_status["Beam Search 30초 보정"] == "내부 검증"
    assert merged_status["Beam Search 120초 탐색"] == "미착수"
    assert merged_status["MCTS"] == "미착수"
    assert merged["beam_search"]["calibration_30s_status"] == "실행됨"
    assert merged["beam_search"]["full_120s_status"] == "미실행"
    assert [stage["status"] for stage in merged["beam_stages"]] == ["내부 검증", "미착수"]
    print("progress_dashboard_beam_calibration_alignment_smoke_test ok")


if __name__ == "__main__":
    main()
