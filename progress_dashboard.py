# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import streamlit as st


BASE_DIR = Path(__file__).resolve().parent

SOURCE_FILES = {
    "PROJECT_PROGRESS_STATE.json": BASE_DIR / "PROJECT_PROGRESS_STATE.json",
    "results/beam_search_v114_completed_v116/result_manifest.json": BASE_DIR
    / "results"
    / "beam_search_v114_completed_v116"
    / "result_manifest.json",
    "data/mcts_plan_v117_32gb.json": BASE_DIR / "data" / "mcts_plan_v117_32gb.json",
    "data/mcts_plan_v118_32gb_3x50k.json": BASE_DIR / "data" / "mcts_plan_v118_32gb_3x50k.json",
    "results/mcts_v117_calibration_20k_v118/result_manifest.json": BASE_DIR
    / "results" / "mcts_v117_calibration_20k_v118" / "result_manifest.json",
    "results/mcts_v118_production_3x50k_v119/result_manifest.json": BASE_DIR
    / "results" / "mcts_v118_production_3x50k_v119" / "result_manifest.json",
    "reports/mcts_v118_3x50k_production_v119.md": BASE_DIR / "reports" / "mcts_v118_3x50k_production_v119.md",
    "reports/mcts_v117_20k_calibration_v118.md": BASE_DIR / "reports" / "mcts_v117_20k_calibration_v118.md",
    "reports/mcts_v117_32gb_design.md": BASE_DIR / "reports" / "mcts_v117_32gb_design.md",
    "data/beam_search_plan_v111.json": BASE_DIR / "data" / "beam_search_plan_v111.json",
    "data/guarded_ppo_experiment_plan_v109.json": BASE_DIR
    / "data"
    / "guarded_ppo_experiment_plan_v109.json",
    "reports/guarded_ppo_experiment_v109_results.md": BASE_DIR
    / "reports"
    / "guarded_ppo_experiment_v109_results.md",
    "reports/beam_search_v111.md": BASE_DIR / "reports" / "beam_search_v111.md",
    "reports/beam_search_v111_calibration_results.md": BASE_DIR
    / "reports"
    / "beam_search_v111_calibration_results.md",
    "reports/manual_120s_baseline_v104.md": BASE_DIR
    / "reports"
    / "manual_120s_baseline_v104.md",
    "reports/manual_120s_bc_demonstration_v105.md": BASE_DIR
    / "reports"
    / "manual_120s_bc_demonstration_v105.md",
}

TEXT_ENCODINGS = ("utf-8-sig", "utf-8", "cp949")

STATUS_LEVELS = {
    "미착수": 0,
    "계획": 1,
    "구현 완료": 2,
    "내부 검증": 3,
    "외부 검증": 4,
}

CHARACTER_NAMES = {
    "aemeath": "에이메스",
    "mornye": "모니에",
    "lynae": "린네",
}

EMBEDDED_PROGRESS_SNAPSHOT: dict[str, Any] = {
    "project_title": "명조 종말 매트릭스 DPS 시뮬레이터",
    "project_subtitle": "개발 진행 현황 및 학습·탐색 알고리즘 설명",
    "project_description": (
        "Wuthering Waves Endgame Matrix 전투를 120초 동안 재현해 "
        "파티 총 피해량과 DPS를 비교하는 결정론적 시뮬레이터입니다."
    ),
    "combat_duration_seconds": 120,
    "primary_party": ["aemeath", "mornye", "lynae"],
    "externally_verified_baseline": "ww-dps-simulator-2-111.zip",
    "current_candidate_version": "ww-dps-simulator-2-112.zip",
    "current_review_status": "구현 완료, 외부 검토 대기",
    "review_status_key": "candidate_pending_external_review",
    "last_updated_label": "2026-07-14",
    "best_total_damage": 5_165_134.68,
    "best_dps": 43_042.79,
    "best_method": "행동 복제(Behavior Cloning, BC)",
    "best_model": "models/maskable_ppo_bc_v105.zip",
    "manual_baseline": {
        "status": "외부 검증 완료",
        "damage": 5_165_134.68,
        "dps": 43_042.79,
        "description": "사람이 작성한 합법 120초 기준 경로입니다. 전역 최적성을 증명하지는 않습니다.",
    },
    "bc_status": {
        "status": "외부 검증 완료",
        "damage": 5_165_134.68,
        "dps": 43_042.79,
        "description": "검증된 수동 경로를 모방해 현재 최고 검증 결과를 재현합니다.",
    },
    "ppo_results": [
        {"name": "BC 기준 모델", "damage": 5_165_134.68, "status": "검증 완료"},
        {"name": "BC 보수적 PPO", "damage": 5_165_134.68, "status": "BC 초과 실패"},
        {"name": "BC 탐색적 PPO", "damage": 5_165_134.68, "status": "BC 초과 실패"},
        {"name": "Scratch PPO", "damage": 2_566_933.38, "status": "BC 대비 약 49.70%"},
    ],
    "beam_search": {
        "implementation_status": "외부 검증",
        "internal_tests": "내부 검증",
        "external_review": "외부 검토 대기",
        "calibration_30s_status": "실행됨",
        "full_120s_status": "미실행",
        "has_confirmed_damage_result": True,
        "has_bc_beating_route": False,
        "summary": (
            "30초 보정은 완료되어 유효한 완료 경로를 생성했고, 120초 전체 탐색은 아직 실행되지 않았습니다."
        ),
    },
    "mcts": {
        "status": "미실행",
        "summary": "Beam Search가 지나치게 좁거나 근시안적이라고 확인될 때 검토할 미래 선택지입니다.",
        "has_confirmed_damage_result": False,
    },
    "characters": {
        "aemeath": {
            "status": "외부 검토 기반 구현",
            "items": [
                "인간형과 메카형 상태 처리",
                "Instant Response 조건부 타이밍 처리",
                "Seraphic Duet 처리",
                "Rupturous Trail 상태 처리",
                "Active Echo와 무기·장비 효과 반영",
            ],
            "limitations": "일부 세부 타이밍과 메타데이터 추적은 후보별 외부 검토를 따릅니다.",
        },
        "mornye": {
            "status": "외부 검토 기반 구현",
            "items": [
                "방어력 기반 피해 스케일링",
                "High Syntony Field",
                "파티 공격력 버프",
                "Interfered Marker와 Discord 처리",
                "Active Echo, 예약 피해, 예약 치유 처리",
            ],
            "limitations": "정확한 반격 타이밍과 적 카운터 행동은 단순화가 남아 있습니다.",
        },
        "lynae": {
            "status": "외부 검토 기반 구현",
            "items": [
                "반복 타격 피해와 리소스 처리",
                "Outro와 Intro 연결",
                "파티 버프와 지연 효과",
                "Spray Paint 예약 상태 적용",
                "Off-Tune 값 매핑",
            ],
            "limitations": "Hyvatia Off-Tune 값은 미해결 항목으로 계속 표시합니다.",
        },
    },
    "unresolved_items": [
        {
            "title": "린네 Hyvatia Off-Tune 값",
            "status": "미해결",
            "description": "Active Echo / Hyvatia 관련 Off-Tune 값은 확정 검증으로 승격하지 않습니다.",
            "impact": "린네 Echo 선택과 Off-Tune 평가",
        },
        {
            "title": "오프닝 normal-swap 정확 타이밍",
            "status": "제한",
            "description": "초반 일반 공격과 스왑 타이밍은 법적 경로 기준으로 유지하되, 프레임 단위 완전성은 제한됩니다.",
            "impact": "초반 자원·버프 정렬",
        },
        {
            "title": "적 카운터 행동 단순화",
            "status": "제한",
            "description": "실전 적 반격과 카운터 반응은 결정론 비교를 위해 단순화되어 있습니다.",
            "impact": "실전 재현성",
        },
        {
            "title": "과거 PPO/BC 산출물 누락 또는 노후화",
            "status": "주의",
            "description": "일부 오래된 학습 산출물은 현재 후보의 직접 검증 근거로 사용하지 않습니다.",
            "impact": "과거 실험 재현성",
        },
    ],
    "beam_stages": [
        {
            "name": "30초 보정",
            "duration_seconds": 30,
            "beam_width": 1024,
            "time_bucket_width": 0.5,
            "global_quota": 512,
            "diversity_quota": 512,
            "max_expansions": 500_000,
            "checkpoint": "주기적 체크포인트 계획",
            "resume": "중단 후 재개 가능",
            "status": "내부 검증",
        },
        {
            "name": "120초 전체 탐색",
            "duration_seconds": 120,
            "beam_width": 4096,
            "time_bucket_width": 0.5,
            "global_quota": 2048,
            "diversity_quota": 2048,
            "max_expansions": 5_000_000,
            "checkpoint": "장기 실행 체크포인트 계획",
            "resume": "중단 후 재개 가능",
            "status": "미착수",
        },
    ],
    "stage_status": [
        {"stage": "시뮬레이터 코어", "status": "외부 검증"},
        {"stage": "캐릭터 메커니즘", "status": "외부 검증"},
        {"stage": "수동 기준선", "status": "외부 검증"},
        {"stage": "행동 복제", "status": "외부 검증"},
        {"stage": "PPO 실험", "status": "내부 검증"},
        {"stage": "Beam Search 인프라", "status": "외부 검증"},
        {"stage": "Beam Search 30초 보정", "status": "내부 검증"},
        {"stage": "Beam Search 120초 탐색", "status": "미착수"},
        {"stage": "MCTS", "status": "미착수"},
    ],
    "development_flow": [
        {"name": "수동 기준선", "reason": "합법 참조 경로 확립"},
        {"name": "행동 복제", "reason": "참조 경로를 효과적으로 재현"},
        {"name": "PPO 실험", "reason": "BC 초과 개선 실패"},
        {"name": "독립 Beam Search", "reason": "학습 정책과 독립적으로 탐색"},
        {"name": "MCTS", "reason": "필요할 때만 검토할 조건부 대안"},
    ],
    "optional_source_files": list(SOURCE_FILES.keys()),
}


def _read_text_with_encoding(path: Path) -> tuple[str | None, str | None, str | None]:
    for encoding in TEXT_ENCODINGS:
        try:
            return path.read_text(encoding=encoding), encoding, None
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            return None, None, "파일 없음"
        except OSError as exc:
            return None, None, f"읽기 실패: {exc}"
    return None, None, "지원 인코딩으로 해석할 수 없음"


@st.cache_data(show_spinner=False)
def safe_load_text(path_text: str) -> tuple[str | None, dict[str, str | None]]:
    path = Path(path_text)
    text, encoding, error = _read_text_with_encoding(path)
    return text, {"encoding": encoding, "error": error}


@st.cache_data(show_spinner=False)
def safe_load_json(path_text: str) -> tuple[dict[str, Any] | list[Any] | None, dict[str, str | None]]:
    text, meta = safe_load_text(path_text)
    if text is None:
        return None, meta
    try:
        return json.loads(text), meta
    except json.JSONDecodeError:
        meta = dict(meta)
        meta["error"] = "JSON 형식 오류"
        return None, meta


def format_number(value: Any) -> str:
    if value is None:
        return "결과 없음"
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return "결과 없음"


def format_optional_number(value: Any) -> str:
    return format_number(value)


def translate_status(status: Any) -> str:
    mapping = {
        "externally_verified_complete": "외부 검증 완료",
        "complete": "완료",
        "implemented_tests_passed_pending_external_review": "구현 및 내부 테스트 통과, 외부 검토 대기",
        "candidate_pending_external_review": "구현 완료, 외부 검토 대기",
        "pending": "대기",
        "unresolved": "미해결",
        "not_executed": "미실행",
        "not_run": "미실행",
        "implemented": "구현 완료",
        "internal_tested": "내부 검증",
    }
    return mapping.get(str(status), str(status or "확인 불가"))


def translate_character_name(character_id: str) -> str:
    return CHARACTER_NAMES.get(character_id, character_id)


def get_source_load_status(sources: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    status = {"loaded": [], "missing": [], "failed": []}
    for name, source in sources.items():
        error = source.get("meta", {}).get("error")
        if error is None:
            status["loaded"].append(name)
        elif error == "파일 없음":
            status["missing"].append(name)
        else:
            status["failed"].append(f"{name}: {error}")
    return status


def normalize_stage_mapping(raw_stages: Any) -> dict[str, dict[str, Any]]:
    if isinstance(raw_stages, dict):
        result: dict[str, dict[str, Any]] = {}
        for key, value in raw_stages.items():
            if isinstance(value, dict):
                result[str(key)] = dict(value)
            else:
                result[str(key)] = {"value": value}
        return result

    if isinstance(raw_stages, list):
        result = {}
        for index, value in enumerate(raw_stages, start=1):
            if isinstance(value, dict):
                stage = dict(value)
                raw_name = (
                    stage.get("name")
                    or stage.get("id")
                    or stage.get("stage_id")
                    or stage.get("stage")
                    or stage.get("stage_name")
                    or stage.get("key")
                    or f"stage_{index}"
                )
                result[str(raw_name)] = stage
            else:
                result[f"stage_{index}"] = {"value": value}
        return result

    return {}


def has_stage_plan_fields(stage: dict[str, Any]) -> bool:
    plan_fields = {
        "duration_seconds",
        "beam_width",
        "time_bucket_width",
        "global_survivors",
        "diversity_survivors",
        "max_expansions",
        "status",
    }
    return any(field in stage for field in plan_fields)


def merge_progress_data(
    snapshot: dict[str, Any], sources: dict[str, dict[str, Any]]
) -> tuple[dict[str, Any], str]:
    merged = copy.deepcopy(snapshot)
    progress = sources.get("PROJECT_PROGRESS_STATE.json", {}).get("data")
    beam_plan = sources.get("data/beam_search_plan_v111.json", {}).get("data")
    source_mode = "내장 스냅샷"

    if isinstance(progress, dict):
        source_mode = "저장소 최신 데이터"
        status = progress.get("status") or {}
        current = progress.get("current_in_progress_task") or {}
        project = progress.get("project") or {}

        if status.get("last_updated"):
            merged["last_updated_label"] = status["last_updated"]
        if status.get("latest_verified_archive"):
            merged["externally_verified_baseline"] = status["latest_verified_archive"]
        if status.get("candidate_expected_next_archive"):
            merged["current_candidate_version"] = status["candidate_expected_next_archive"]
        if status.get("current_task_status"):
            merged["current_review_status"] = translate_status(status["current_task_status"])
            merged["review_status_key"] = status["current_task_status"]
        if project.get("primary_party"):
            merged["primary_party"] = project["primary_party"]
        if current.get("current_best_result") is not None:
            merged["best_total_damage"] = current["current_best_result"]
        if current.get("current_best_dps") is not None:
            merged["best_dps"] = current["current_best_dps"]
        if current.get("current_best_model"):
            merged["best_model"] = current["current_best_model"]

        manual = progress.get("manual_cycle_reference") or {}
        if manual.get("total_damage") is not None:
            merged["manual_baseline"]["damage"] = manual["total_damage"]
        if manual.get("dps") is not None:
            merged["manual_baseline"]["dps"] = manual["dps"]

        merged["beam_search"]["calibration_30s_status"] = (
            "실행됨" if current.get("calibration_stage_executed") else "미실행"
        )
        merged["beam_search"]["full_120s_status"] = (
            "실행됨" if current.get("full_search_stage_executed") else "미실행"
        )
        merged["beam_search"]["has_confirmed_damage_result"] = bool(
            current.get("canonical_beam_search_results_written")
        )
        if current.get("calibration_stage_executed"):
            merged["beam_search"]["summary"] = (
                "30초 보정은 완료되어 유효한 완료 경로를 생성했습니다. "
                "120초 전체 탐색은 후보 112 외부 검토 후에만 실행합니다."
            )
        stage_status = {item["stage"]: item for item in merged["stage_status"]}
        stage_status["Beam Search 인프라"]["status"] = "외부 검증"
        stage_status["Beam Search 30초 보정"]["status"] = (
            "내부 검증" if current.get("calibration_stage_executed") else "미착수"
        )
        stage_status["Beam Search 120초 탐색"]["status"] = (
            "내부 검증" if current.get("full_search_stage_executed") else "미착수"
        )
        stage_status["MCTS"]["status"] = "미착수"

    if isinstance(beam_plan, dict):
        raw_stages = beam_plan.get("stages")
        stages = normalize_stage_mapping(raw_stages)
        planned_stages = []
        for raw_name, stage in stages.items():
            if not isinstance(stage, dict) or not has_stage_plan_fields(stage):
                continue
            display_name = "30초 보정" if "calibration" in raw_name else "120초 전체 탐색"
            planned_stages.append(
                {
                    "name": display_name,
                    "duration_seconds": stage.get("duration_seconds"),
                    "beam_width": stage.get("beam_width"),
                    "time_bucket_width": stage.get("time_bucket_width"),
                    "global_quota": stage.get("global_survivors"),
                    "diversity_quota": stage.get("diversity_survivors"),
                    "max_expansions": stage.get("max_expansions"),
                    "checkpoint": stage.get("checkpoint_behavior", "계획됨"),
                    "resume": stage.get("resume_behavior", "계획됨"),
                    "status": (
                        "내부 검증"
                        if "calibration" in raw_name and current.get("calibration_stage_executed")
                        else "미착수"
                    ),
                }
            )
        if planned_stages:
            merged["beam_stages"] = planned_stages
        elif raw_stages is not None:
            merged["beam_stage_notice"] = (
                "선택 Beam Search 계획 파일의 stages 형식을 해석하지 못해 내장 단계 계획을 표시합니다."
            )

    # Candidate 116 promotes the completed 120-second Beam route to the overall
    # project winner while retaining Guarded PPO 90k as the trained-model winner.
    if isinstance(progress, dict):
        current = progress.get("current_in_progress_task") or {}
        completed = current.get("candidate_116_completed_beam") or {}
        overall = current.get("overall_project_winner") or {}
        trained = current.get("best_trained_model") or {}
        if completed.get("termination_status") == "completed_search":
            beam_damage = float(completed["winning_damage"])
            beam_dps = float(completed["winning_dps"])
            model_damage = float(trained["total_damage"])
            model_dps = float(trained["dps"])
            merged["best_total_damage"] = beam_damage
            merged["best_dps"] = beam_dps
            merged["best_method"] = "Completed Beam route"
            merged["best_model"] = trained["model_path"]
            merged["overall_project_winner"] = overall
            merged["best_trained_model"] = trained
            merged["beam_search"].update(
                {
                    "full_120s_status": "Completed",
                    "has_confirmed_damage_result": True,
                    "has_bc_beating_route": True,
                    "winner_route_id": completed["winning_route_id"],
                    "winner_total_damage": beam_damage,
                    "winner_dps": beam_dps,
                    "completed_route_count": completed["completed_120s_route_count"],
                    "expansions": completed["expansions"],
                    "safety_cap": 6_500_000,
                    "damage_gain_over_best_trained_model": beam_damage - model_damage,
                    "dps_gain_over_best_trained_model": beam_dps - model_dps,
                    "relative_gain_over_best_trained_model_percent": (
                        beam_damage / model_damage - 1.0
                    )
                    * 100.0,
                    "global_optimum_proven": False,
                    "summary": (
                        f"Beam completed with {completed['completed_120s_route_count']} retained "
                        f"120-second routes at {completed['expansions']:,} expansions, before the "
                        "6.5M safety cap. The winning route is now the overall project winner; "
                        "global optimality is not proven."
                    ),
                }
            )
            mcts = current.get("candidate_117_mcts") or {}
            production_plan = current.get("candidate_118_mcts") or {}
            production = current.get("candidate_119_mcts") or {}
            merged["mcts"].update(
                {
                    "status": "20k calibration complete; 3×50k production complete",
                    "summary": (
                        "All three independent 50k MCTS production seeds completed with zero invalid "
                        "rollouts. Seed 118003 is the best MCTS result at 4,647,724.70 damage, "
                        "1,004,167.57 below Beam (-17.7669%). Beam remains the overall winner; "
                        "an MCTS extension is not recommended and global optimality is not proven."
                    ),
                    "infrastructure_ready": bool(mcts.get("infrastructure_implemented")),
                    "calibration_20k_executed": bool(mcts.get("calibration_20k_executed")),
                    "production_search_executed": bool(production.get("production_search_executed")),
                    "calibration_best_damage": mcts.get("best_damage"),
                    "calibration_best_dps": mcts.get("best_dps"),
                    "calibration_vs_beam_percent": -26.960076164770296,
                    "production_3x50k_plan_ready": bool(production_plan.get("production_plan_ready")),
                    "production_seeds": production_plan.get("seeds", []),
                    "production_seeds_completed": production.get("production_seeds_completed", 0),
                    "production_simulations_completed": production.get("production_simulations_completed", 0),
                    "production_invalid_rollouts": production.get("production_invalid_rollouts", 0),
                    "best_production_seed": production.get("best_seed"),
                    "best_production_route_id": production.get("best_route_id"),
                    "best_production_damage": production.get("best_damage"),
                    "best_production_dps": production.get("best_dps"),
                    "mcts_vs_beam_damage_delta": -1004167.5713050179,
                    "mcts_vs_beam_relative_delta_percent": -17.76692694278993,
                    "extension_recommended": False,
                    "global_optimum_proven": False,
                    "independent_complementary_validation": True,
                    "has_confirmed_damage_result": bool(production.get("production_finalized")),
                }
            )
            for stage in merged.get("beam_stages", []):
                if stage.get("duration_seconds") == 120:
                    stage["status"] = "Completed"
            for stage in merged.get("stage_status", []):
                if stage.get("stage") == "Beam Search 120초 탐색":
                    stage["status"] = "내부 검증"
                elif stage.get("stage") == "MCTS":
                    stage["status"] = "내부 검증"

    return merged, source_mode


def render_status_badge(label: str, status: str) -> None:
    status_lower = status.lower()
    if "외부" in status or status_lower == "verified":
        css_class = "badge-verified"
    elif "내부" in status or "구현" in status or "대기" in status:
        css_class = "badge-pending"
    elif "미실행" in status or "계획" in status or "미착수" in status:
        css_class = "badge-muted"
    else:
        css_class = "badge-unresolved"
    st.markdown(f'<span class="badge {css_class}">{label}</span>', unsafe_allow_html=True)


def render_section_header(title: str, caption: str | None = None) -> None:
    st.markdown(f'<h2 class="section-title">{title}</h2>', unsafe_allow_html=True)
    if caption:
        st.caption(caption)


def relative_name(path_name: str) -> str:
    return path_name.replace("\\", "/")


def party_display(party: list[str]) -> str:
    return ", ".join(translate_character_name(name) for name in party)


def status_level_row(stage: dict[str, Any]) -> dict[str, Any]:
    status = stage["status"]
    return {
        "단계": stage["stage"],
        "상태": status,
        "상태 수준": STATUS_LEVELS.get(status, 0),
    }


def performance_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    manual = data.get("manual_baseline", {})
    if manual.get("damage") is not None:
        rows.append(
            {
                "방식": "수동 기준선",
                "총 피해량": float(manual["damage"]),
                "표시 피해량": format_number(manual["damage"]),
                "상태": manual.get("status", "외부 검증 완료"),
            }
        )
    for row in data.get("ppo_results", []):
        damage = row.get("damage")
        if damage is None:
            continue
        rows.append(
            {
                "방식": row["name"],
                "총 피해량": float(damage),
                "표시 피해량": format_number(damage),
                "상태": row.get("status", "확인 불가"),
            }
        )
    return rows


def inject_css() -> None:
    st.markdown(
        """
        <style>
        html, body, [class*="css"], .stApp {
            font-family:
                Arial,
                "Malgun Gothic",
                "맑은 고딕",
                "Apple SD Gothic Neo",
                "Noto Sans KR",
                sans-serif;
        }
        .block-container {
            padding-top: 2.2rem;
            padding-bottom: 3rem;
            max-width: 1320px;
        }
        .hero {
            border: 1px solid #d7dee8;
            background: #f8fafc;
            border-radius: 8px;
            padding: 1.3rem 1.45rem;
            margin-bottom: 1rem;
        }
        .hero h1 {
            font-size: clamp(1.75rem, 3vw, 2.55rem);
            line-height: 1.18;
            margin: 0 0 .35rem 0;
        }
        .hero p {
            margin: 0;
            color: #52606d;
            font-size: 1.02rem;
        }
        .section-title {
            font-size: 1.42rem;
            margin: 1.65rem 0 .55rem 0;
            padding-top: .25rem;
            border-top: 1px solid #e5e7eb;
        }
        .status-card {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: .9rem 1rem;
            background: #ffffff;
            min-height: 12rem;
        }
        .small-card {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: .75rem .85rem;
            background: #ffffff;
            height: 100%;
        }
        .flow-card {
            border: 1px solid #dbe3ed;
            border-radius: 8px;
            padding: .8rem;
            background: #f8fafc;
            min-height: 7rem;
        }
        .badge {
            display: inline-block;
            padding: .18rem .52rem;
            border-radius: 999px;
            font-size: .78rem;
            font-weight: 700;
            border: 1px solid transparent;
            white-space: nowrap;
        }
        .badge-verified { color: #065f46; background: #d1fae5; border-color: #a7f3d0; }
        .badge-pending { color: #854d0e; background: #fef3c7; border-color: #fde68a; }
        .badge-unresolved { color: #991b1b; background: #fee2e2; border-color: #fecaca; }
        .badge-muted { color: #475569; background: #e2e8f0; border-color: #cbd5e1; }
        .note {
            color: #64748b;
            font-size: .92rem;
        }
        div[data-testid="stMetricValue"] {
            font-size: clamp(1.25rem, 2vw, 1.72rem);
        }
        div[data-testid="stDataFrame"] {
            overflow-x: auto;
        }
        @media (max-width: 760px) {
            .hero { padding: 1rem; }
            .status-card { min-height: auto; margin-bottom: .75rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(data: dict[str, Any], source_mode: str) -> None:
    st.markdown(
        f"""
        <div class="hero">
            <h1>{data["project_title"]}</h1>
            <p>{data["project_subtitle"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("외부 검증 기준선", data["externally_verified_baseline"])
    col2.metric("현재 후보", data["current_candidate_version"])
    col3.metric("마지막 갱신", data["last_updated_label"])
    with col4:
        st.markdown("**데이터 모드**")
        render_status_badge(source_mode, source_mode)
    st.markdown("**현재 검토 상태**")
    render_status_badge(data["current_review_status"], data["current_review_status"])
    st.caption(
        "내부 테스트 통과와 외부 검증 완료는 별도 상태입니다. "
        "Beam Search 30초 보정은 완료됐지만 후보 112는 외부 검토 대기 상태이며, "
        "120초 전체 탐색과 MCTS는 아직 실행되지 않았습니다."
    )


def render_project_overview(data: dict[str, Any]) -> None:
    render_section_header("프로젝트 개요")
    st.write(data["project_description"])
    st.write(
        f"현재 주 파티는 {party_display(data['primary_party'])}입니다. "
        "최종 비교 목적은 결정론적 120초 총 피해량이며, 캐릭터 선호도 보너스나 "
        "기존 경로 유사도 보너스는 최종 순위에 사용하지 않습니다."
    )
    st.write(
        "버프, 디버프, 필드, 예약 피해와 예약 치유 같은 scheduled effect는 "
        "해결된 전투 시간 비용을 기준으로 처리합니다. 수동 경로, 학습 정책, "
        "결정론 탐색 방법은 같은 평가 기준 아래에서 비교합니다."
    )


def render_key_metrics(data: dict[str, Any]) -> None:
    render_section_header("핵심 지표")
    cols = st.columns(6)
    cols[0].metric("최고 총 피해량", format_number(data["best_total_damage"]))
    cols[1].metric("최고 DPS", format_number(data["best_dps"]))
    cols[2].metric("현재 최고 방식", data["best_method"])
    cols[3].metric("전투 시간", f"{data['combat_duration_seconds']}초")
    cols[4].metric("외부 검증 기준선", data["externally_verified_baseline"])
    cols[5].metric("현재 후보 상태", data["current_review_status"])
    st.caption(f"현재 최고 모델: {data['best_model']}")


def render_performance_chart(data: dict[str, Any]) -> None:
    render_section_header("검증된 알고리즘 피해량 비교")
    rows = performance_rows(data)
    chart = {
        "data": {"values": rows},
        "mark": {"type": "bar", "cornerRadiusEnd": 4},
        "encoding": {
            "y": {
                "field": "방식",
                "type": "nominal",
                "sort": "-x",
                "title": "방식",
                "axis": {"labelLimit": 240},
            },
            "x": {
                "field": "총 피해량",
                "type": "quantitative",
                "title": "총 피해량",
            },
            "color": {
                "field": "상태",
                "type": "nominal",
                "title": "상태",
                "scale": {
                    "range": ["#2563eb", "#0f766e", "#d97706", "#64748b"],
                },
            },
            "tooltip": [
                {"field": "방식", "title": "방식"},
                {"field": "표시 피해량", "title": "총 피해량"},
                {"field": "상태", "title": "상태"},
            ],
        },
        "height": max(220, 42 * len(rows)),
    }
    st.vega_lite_chart(chart, use_container_width=True)
    st.info(
        "PPO는 검증된 BC 결과를 넘지 못했습니다. Beam Search는 유효한 30초 보정 결과가 있지만 "
        "120초 비교와 시간 지평이 달라 이 차트에 표시하지 않습니다. MCTS는 아직 실행되지 않았습니다."
    )


def render_stage_chart(data: dict[str, Any]) -> None:
    render_section_header("개발 단계별 검증 상태")
    rows = [status_level_row(stage) for stage in data["stage_status"]]
    chart = {
        "data": {"values": rows},
        "mark": {"type": "bar", "cornerRadiusEnd": 4},
        "encoding": {
            "y": {"field": "단계", "type": "nominal", "sort": None, "title": "개발 단계"},
            "x": {
                "field": "상태 수준",
                "type": "quantitative",
                "title": "상태 수준",
                "scale": {"domain": [0, 4]},
                "axis": {"tickMinStep": 1},
            },
            "color": {
                "field": "상태",
                "type": "nominal",
                "title": "상태",
                "scale": {
                    "domain": ["미착수", "계획", "구현 완료", "내부 검증", "외부 검증"],
                    "range": ["#94a3b8", "#60a5fa", "#f59e0b", "#10b981", "#047857"],
                },
            },
            "tooltip": [
                {"field": "단계", "title": "단계"},
                {"field": "상태", "title": "상태"},
                {"field": "상태 수준", "title": "상태 수준"},
            ],
        },
        "height": 360,
    }
    st.vega_lite_chart(chart, use_container_width=True)
    st.caption("상태 수준: 미착수=0, 계획=1, 구현 완료=2, 내부 검증=3, 외부 검증=4. 이 값은 완료율이 아닙니다.")


def render_current_status(data: dict[str, Any]) -> None:
    render_section_header("현재 개발 상태")
    beam = data["beam_search"]
    candidate = "후보 112" if data.get("review_status_key") == "candidate_pending_external_review" else "현재 후보"
    calibration_status = beam["calibration_30s_status"]
    full_search_status = beam["full_120s_status"]
    mcts_status = data["mcts"]["status"]
    done, current, unresolved = st.columns(3)
    with done:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        st.markdown("**완료 또는 외부 검증 완료**")
        st.markdown(
            """
            - 결정론 120초 시뮬레이터 코어
            - 전투 시간 비용 처리
            - 주 파티 캐릭터 메커니즘
            - 검증된 수동 경로
            - 검증된 BC 모델
            - Guarded PPO 실험 실행
            - 자원, 쿨다운, 스왑, 필드, scheduled effect 처리
            """
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with current:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        st.markdown("**현재 진행 중**")
        st.markdown(
            "\n".join(
                [
                    "- 독립 결정론 diverse Beam Search 인프라 외부 검증 완료",
                    "- 동등 미래 상태 deduplication 및 상태 다양성 보존 구현",
                    "- 체크포인트, 재개, 최종 경로 결정론 replay 검증 구현",
                    f"- 30초 보정 {calibration_status} 완료 ({candidate} 외부 검토 대기)",
                    f"- 120초 전체 탐색 {full_search_status}",
                    f"- MCTS {mcts_status}",
                    "- MCTS 20k 보정 및 독립 3×50k production 완료",
                    "- seed 118003이 최고 MCTS 결과, Beam 경로가 전체 최고",
                    "- MCTS 연장 비권장, 전역 최적성 미증명",
                ]
            )
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with unresolved:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        st.markdown("**미해결 또는 제한 사항**")
        for item in data["unresolved_items"][:4]:
            st.markdown(f"- **{item['title']}**: {item['status']}")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("미해결 항목 자세히 보기"):
        cols = st.columns(2)
        for index, item in enumerate(data["unresolved_items"]):
            with cols[index % 2]:
                st.markdown(
                    f"""
                    <div class="small-card">
                    <b>항목명</b>: {item['title']}<br>
                    <b>상태</b>: {item['status']}<br>
                    <b>설명</b>: {item['description']}<br>
                    <b>영향 범위</b>: {item.get('impact', '확인 필요')}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_character_status(data: dict[str, Any]) -> None:
    render_section_header("캐릭터 구현 상태")
    tabs = st.tabs([translate_character_name(name) for name in ("aemeath", "mornye", "lynae")])
    for tab, character_id in zip(tabs, ("aemeath", "mornye", "lynae")):
        info = data["characters"][character_id]
        with tab:
            render_status_badge(info["status"], info["status"])
            st.markdown("\n".join(f"- {item}" for item in info["items"]))
            st.caption(info["limitations"])


def render_learning_methods(data: dict[str, Any]) -> None:
    render_section_header("학습·탐색 방식", "모든 항목이 머신러닝 알고리즘인 것은 아닙니다.")
    tabs = st.tabs(
        [
            "수동 기준선",
            "행동 복제(Behavior Cloning, BC)",
            "근접 정책 최적화(Proximal Policy Optimization, PPO)",
            "빔 탐색(Beam Search)",
            "몬테카를로 트리 탐색(Monte Carlo Tree Search, MCTS)",
        ]
    )
    with tabs[0]:
        st.markdown(
            """
            - 사람이 작성한 합법 120초 경로입니다.
            - 신뢰 가능한 하한 참조로 사용합니다.
            - 자원, 쿨다운, 스왑, 타이밍, 버프, 피해량 검증에 사용합니다.
            - 전역 최적성을 증명하지는 않습니다.
            """
        )
    with tabs[1]:
        st.markdown(
            """
            - 검증된 수동 경로에서 상태별 기대 행동을 배우는 지도 모방학습입니다.
            - 이미 좋은 경로를 효율적으로 재현합니다.
            - 보통 시연 경로와 가까운 행동을 유지합니다.
            - 최적성을 증명하지는 않지만 현재 최고 검증 결과입니다.
            """
        )
    with tabs[2]:
        st.markdown(
            """
            - 환경 상호작용과 보상을 통해 정책을 개선하는 강화학습 방법입니다.
            - 이 프로젝트는 BC 초기화 보수적 PPO, BC 초기화 탐색적 PPO, scratch PPO를 시험했습니다.
            - 현재 PPO 실험은 BC 결과를 넘지 못했습니다.
            - 추가 unguided PPO 훈련은 현재 우선순위가 아닙니다.
            """
        )
    with tabs[3]:
        st.markdown(
            """
            - Beam Search는 학습 알고리즘이 아니라 결정론적 탐색 알고리즘입니다.
            - 각 진행 지점에서 가능한 다음 행동을 확장합니다.
            - 유망하면서도 전략적으로 다른 미래 상태만 제한된 수로 보존합니다.
            - 동등한 미래 상태는 deduplication으로 병합합니다.
            - 목적 함수는 결정론적 120초 총 피해량입니다.
            - 수동 경로, BC/PPO 행동 확률, 경로 유사도 보너스, 학습 가치 함수와 독립적입니다.
            - 시연 정책 밖의 경로를 조사할 수 있지만, pruning이 과격하면 좋은 경로를 놓칠 수 있습니다.
            - 완료된 30초 보정 결과를 외부 검토한 뒤 120초 전체 탐색으로 넘어가야 합니다.
            - 현재 후보는 30초 보정 완료 경로이며, 120초 향상 경로는 아직 확정되지 않았습니다.
            """
        )
        st.info(
            "가능한 다음 행동이 20개라면 완전 탐색은 20개 분기를 모두 계속 확장합니다. "
            "빔 탐색은 각 단계에서 성능과 상태 다양성을 기준으로 일부 후보만 선택해 다음 단계로 진행합니다."
        )
    with tabs[4]:
        st.markdown(
            """
            - 탐색과 활용의 균형을 잡는 트리 탐색 방법입니다.
            - 초반에는 약해 보여도 뒤에서 강해질 수 있는 분기를 다시 살펴볼 수 있습니다.
            - 현재 주 작업으로 실행되지 않았으며 조건부 미래 선택지입니다.
            - Beam Search가 너무 좁거나 근시안적이라고 확인될 때만 검토합니다.
            """
        )


def render_algorithm_comparison() -> None:
    render_section_header("알고리즘 비교표")
    rows = [
        {
            "방식": "수동 기준선",
            "분류": "사람 작성 참조 경로",
            "출발점": "검증 가능한 수동 행동열",
            "강점": "해석 가능하고 법적 경로 검증에 적합",
            "한계": "전역 최적성 증명 불가",
            "현재 결과": "검증된 참조 경로",
            "현재 판단": "비교 기준",
        },
        {
            "방식": "행동 복제",
            "분류": "지도 모방학습",
            "출발점": "검증된 수동 경로",
            "강점": "참조 경로를 빠르게 재현",
            "한계": "시연 밖 탐색이 약함",
            "현재 결과": "현재 최고 검증 결과",
            "현재 판단": "유지",
        },
        {
            "방식": "PPO",
            "분류": "강화학습",
            "출발점": "BC 초기화 또는 scratch",
            "강점": "보상 기반 개선 가능",
            "한계": "비용이 크고 안정성이 낮음",
            "현재 결과": "실행했으나 BC 초과 실패",
            "현재 판단": "우선순위 낮음",
        },
        {
            "방식": "Beam Search",
            "분류": "결정론 탐색",
            "출발점": "시뮬레이터 상태 확장",
            "강점": "학습 정책 밖 경로 탐색",
            "한계": "pruning에 민감",
            "현재 결과": "30초 보정 완료, 120초 전체 탐색 미실행",
            "현재 판단": "후보 112 외부 검토 대기",
        },
        {
            "방식": "MCTS",
            "분류": "트리 탐색",
            "출발점": "미래 조건부 선택지",
            "강점": "탐색과 활용 균형",
            "한계": "아직 실행 근거 없음",
            "현재 결과": "미실행",
            "현재 판단": "미래 선택지",
        },
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_decision_flow(data: dict[str, Any]) -> None:
    render_section_header("개발 의사결정 흐름")
    cols = st.columns(len(data["development_flow"]))
    for col, step in zip(cols, data["development_flow"]):
        with col:
            st.markdown(
                f"""
                <div class="flow-card">
                <b>{step['name']}</b><br>
                <span class="note">{step['reason']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.caption("흐름: 수동 기준선 검증 → 행동 복제 → PPO 실험 → 독립 Beam Search → 필요 시 MCTS")


def render_beam_plan(data: dict[str, Any]) -> None:
    render_section_header("Beam Search 실행 계획")
    if data.get("beam_stage_notice"):
        st.info(data["beam_stage_notice"])
    rows = []
    for stage in data["beam_stages"]:
        rows.append(
            {
                "단계": stage["name"],
                "전투 시간": f"{stage.get('duration_seconds', '확인 불가')}초",
                "Beam 폭": stage.get("beam_width", "확인 불가"),
                "시간 버킷": stage.get("time_bucket_width", "확인 불가"),
                "전역 피해 quota": stage.get("global_quota", "확인 불가"),
                "다양성 quota": stage.get("diversity_quota", "확인 불가"),
                "최대 확장": stage.get("max_expansions", "확인 불가"),
                "체크포인트": stage.get("checkpoint", "계획됨"),
                "재개": stage.get("resume", "계획됨"),
                "실행 상태": stage.get("status", "미실행"),
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.markdown(
        """
        **계획 순서**
        1. 후보 112 외부 검토
        2. 120초 전체 Beam Search 실행
        3. 중단되면 재시작 대신 체크포인트에서 재개
        4. 완료된 120초 경로만 검증된 BC 결과와 비교
        5. 전체 Beam 결과 검토 후 필요할 때만 MCTS 검토
        """
    )


def render_data_notice(
    data: dict[str, Any], source_mode: str, sources: dict[str, dict[str, Any]]
) -> None:
    render_section_header("데이터 출처 및 해석 주의")
    status = get_source_load_status(sources)
    if source_mode == "내장 스냅샷":
        st.info("외부 진행 상태 파일이 없어 내장 프로젝트 스냅샷을 표시하고 있습니다.")
    else:
        st.success("저장소의 진행 상태 파일을 읽어 내장 스냅샷 위에 안전하게 반영했습니다.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**읽은 선택 파일**")
        st.markdown("\n".join(f"- `{relative_name(name)}`" for name in status["loaded"]) or "- 없음")
    with col2:
        st.markdown("**없는 선택 파일**")
        st.markdown("\n".join(f"- `{relative_name(name)}`" for name in status["missing"]) or "- 없음")
    with col3:
        st.markdown("**해석 실패 파일**")
        st.markdown("\n".join(f"- `{relative_name(name)}`" for name in status["failed"]) or "- 없음")

    st.caption(f"마지막 갱신값: {data['last_updated_label']}")
    st.markdown(
        """
        이 페이지는 읽기 전용입니다. 시뮬레이터 실행, 모델 학습, Beam Search 실행, MCTS 실행을 하지 않습니다.
        내부 테스트 통과와 외부 검증 완료는 다른 상태이며, 누락된 값은 미해결로 남겨 둡니다.
        내장 스냅샷 덕분에 이 파일 하나만 공유해도 대시보드가 렌더링됩니다.
        """
    )


def load_optional_sources() -> dict[str, dict[str, Any]]:
    loaded: dict[str, dict[str, Any]] = {}
    for name, path in SOURCE_FILES.items():
        if path.suffix.lower() == ".json":
            data, meta = safe_load_json(str(path))
        else:
            data, meta = safe_load_text(str(path))
        loaded[name] = {"data": data, "meta": meta}
    return loaded


def main() -> None:
    st.set_page_config(
        page_title="명조 DPS 시뮬레이터 진행 현황",
        page_icon="📊",
        layout="wide",
    )
    inject_css()

    sources = load_optional_sources()
    data, source_mode = merge_progress_data(EMBEDDED_PROGRESS_SNAPSHOT, sources)

    render_header(data, source_mode)
    render_project_overview(data)
    render_key_metrics(data)
    render_performance_chart(data)
    render_stage_chart(data)
    render_current_status(data)
    render_character_status(data)
    render_learning_methods(data)
    render_algorithm_comparison()
    render_decision_flow(data)
    render_beam_plan(data)
    render_data_notice(data, source_mode, sources)


if __name__ == "__main__":
    main()
