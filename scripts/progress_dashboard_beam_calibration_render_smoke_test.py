from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CapturingStreamlit:
    def __init__(self) -> None:
        self.text: list[str] = []

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> bool:
        return False

    def cache_data(self, **_kwargs):
        return lambda function: function

    def _record(self, value, **_kwargs) -> None:
        self.text.append(str(value))

    markdown = _record
    caption = _record
    info = _record
    write = _record
    success = _record
    warning = _record
    error = _record

    def columns(self, count: int):
        return [self] * count

    def tabs(self, labels):
        return [self] * len(labels)

    def expander(self, label: str, **_kwargs):
        self._record(label)
        return self

    def dataframe(self, data, **_kwargs) -> None:
        self._record(data)

    def vega_lite_chart(self, data, **_kwargs) -> None:
        self._record(data)


def _load_dashboard(fake_streamlit: CapturingStreamlit):
    original = sys.modules.get("streamlit")
    sys.modules["streamlit"] = fake_streamlit
    try:
        spec = importlib.util.spec_from_file_location("progress_dashboard_render_under_test", ROOT / "progress_dashboard.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if original is None:
            del sys.modules["streamlit"]
        else:
            sys.modules["streamlit"] = original


def _render_text(dashboard, fake_streamlit: CapturingStreamlit, data: dict) -> str:
    dashboard.render_current_status(data)
    dashboard.render_performance_chart(data)
    dashboard.render_algorithm_comparison()
    dashboard.render_beam_plan(data)
    return "\n".join(fake_streamlit.text)


def _assert_current_rendered_text(text: str) -> None:
    required = (
        "외부 검증 완료",
        "30초 보정 실행됨 완료",
        "후보 112 외부 검토 대기",
        "120초 전체 탐색 미실행",
        "MCTS 미실행",
        "현재 프로젝트 최고 검증 결과는 120초 BC 모델",
        "30초 보정 피해는 120초 BC와 직접 수치 비교하지 않음",
        "Beam Search는 유효한 30초 보정 결과가 있지만 120초 비교와 시간 지평이 달라 이 차트에 표시하지 않습니다.",
        "30초 보정 완료, 120초 전체 탐색 미실행",
        "120초 전체 Beam Search 실행",
        "중단되면 재시작 대신 체크포인트에서 재개",
        "완료된 120초 경로만 검증된 BC 결과와 비교",
    )
    stale = (
        "30초 보정 미실행",
        "Beam Search와 MCTS는 유효 실행 결과가 없어",
        "인프라 구현, 장기 탐색 미실행",
        "2. 30초 보정",
        "BC 초과 Beam 경로 없음",
    )
    for phrase in required:
        assert phrase in text, phrase
    for phrase in stale:
        assert phrase not in text, phrase


def main() -> None:
    fallback_streamlit = CapturingStreamlit()
    dashboard = _load_dashboard(fallback_streamlit)
    fallback = copy.deepcopy(dashboard.EMBEDDED_PROGRESS_SNAPSHOT)
    _assert_current_rendered_text(_render_text(dashboard, fallback_streamlit, fallback))

    merged_streamlit = CapturingStreamlit()
    dashboard = _load_dashboard(merged_streamlit)
    progress = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8-sig"))
    plan = json.loads((ROOT / "data" / "beam_search_plan_v111.json").read_text(encoding="utf-8"))
    merged, source_mode = dashboard.merge_progress_data(
        copy.deepcopy(dashboard.EMBEDDED_PROGRESS_SNAPSHOT),
        {"PROJECT_PROGRESS_STATE.json": {"data": progress}, "data/beam_search_plan_v111.json": {"data": plan}},
    )
    assert source_mode == "저장소 최신 데이터"
    _assert_current_rendered_text(_render_text(dashboard, merged_streamlit, merged))

    source = (ROOT / "progress_dashboard.py").read_text(encoding="utf-8")
    for stale_phrase in (
        "30초 보정 미실행",
        "Beam Search와 MCTS는 유효 실행 결과가 없어",
        "인프라 구현, 장기 탐색 미실행",
        "BC 초과 Beam 경로 없음",
    ):
        assert stale_phrase not in source, stale_phrase
    print("progress_dashboard_beam_calibration_render_smoke_test ok")


if __name__ == "__main__":
    main()
