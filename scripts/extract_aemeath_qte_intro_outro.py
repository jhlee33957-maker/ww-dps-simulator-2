from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "data" / "source"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "extracted" / "aemeath_qte_intro_outro_candidates.json"
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "aemeath_qte_intro_outro_review.md"

MOJIBAKE_HINTS = ["?\uc107\uca95", "\uf978\ub739\uca95"]
KEYWORDS = [
    "QTE",
    "INTRO",
    "OUTRO",
    "\u5165\u573a",
    "\u767b\u573a",
    "\u9000\u573a",
    "\u53d8\u594f",
    "\u8b8a\u594f",
    "\u5ef6\u594f",
    "\u534f\u594f",
]


def resolve_workbook_path(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)
    workbooks = sorted(SOURCE_DIR.glob("*.xlsx"))
    if not workbooks:
        raise FileNotFoundError(f"No .xlsx workbook found in {SOURCE_DIR}")
    return workbooks[0]


def extract(
    workbook_path: str | Path | None = None,
    output_path: str | Path = DEFAULT_OUTPUT,
    report_path: str | Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    workbook = load_workbook(resolve_workbook_path(workbook_path), data_only=False, read_only=True)
    candidates: list[dict[str, Any]] = []
    for sheet_name in workbook.sheetnames:
        sheet = workbook[sheet_name]
        for row_number, row in enumerate(sheet.iter_rows(values_only=True), start=1):
            values = [cell for cell in row if cell is not None]
            if not values:
                continue
            raw_text = " | ".join(_cell_text(value) for value in values)
            if not _is_candidate(raw_text):
                continue
            candidates.append(_candidate(sheet_name, row_number, values, raw_text))

    artifact = {
        "review_status": "review_only_not_executable",
        "notice": (
            "Aemeath QTE / Intro / Outro candidates are extracted for review only. "
            "They are not applied to simulator actions, rewards, PPO training, or party DPS."
        ),
        "candidate_count": len(candidates),
        "keywords": KEYWORDS,
        "mojibake_hints": MOJIBAKE_HINTS,
        "candidates": candidates,
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")

    report = Path(report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(_report_markdown(artifact), encoding="utf-8")
    return artifact


def _cell_text(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:g}"
    return str(value).strip()


def _is_candidate(text: str) -> bool:
    upper = text.upper()
    return any(keyword in upper or keyword in text for keyword in KEYWORDS)


def _candidate(sheet_name: str, row_number: int, values: list[Any], raw_text: str) -> dict[str, Any]:
    source_action_name = _cell_text(values[0]) if values else None
    coefficient_candidates = _coefficient_candidates(raw_text)
    frame_candidates = _frame_candidates(raw_text)
    action_time_candidates = _action_time_candidates(raw_text)
    warnings: list[str] = [
        "Review-only extraction; candidate is not executable.",
        "Mapping to Intro/Outro/QTE behavior requires manual validation.",
    ]
    if not coefficient_candidates:
        warnings.append("No coefficient-like value detected in row text.")
    if not frame_candidates and not action_time_candidates:
        warnings.append("No frame/action-time candidate detected in row text.")

    return {
        "sheet": sheet_name,
        "row_number": row_number,
        "source_action_name": source_action_name,
        "raw_row_text": raw_text,
        "coefficients": coefficient_candidates,
        "frame_candidates": frame_candidates,
        "action_time_candidates": action_time_candidates,
        "notice_text": raw_text,
        "previous_character_outro_trigger_frame": _outro_trigger_frame(raw_text),
        "state_grant_notes_15s": _state_grant_notes(raw_text),
        "confidence": _confidence(raw_text, coefficient_candidates, frame_candidates, action_time_candidates),
        "warnings": warnings,
    }


def _coefficient_candidates(text: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for match in re.finditer(r"(?<![\w.])(\d+(?:\.\d+)?)\s*%", text):
        candidates.append({"raw": match.group(0), "value": float(match.group(1)) / 100.0})
    for match in re.finditer(r"(?<![\w.])(\d+\.\d{2,})(?![\w.%])", text):
        value = float(match.group(1))
        if value > 0.0:
            candidates.append({"raw": match.group(0), "value": value})
    return candidates


def _frame_candidates(text: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:F|f|\u5e27|\u5e40)", text):
        frames = float(match.group(1))
        candidates.append({"raw": match.group(0), "frames": frames, "seconds_at_60fps": round(frames / 60.0, 4)})
    return candidates


def _action_time_candidates(text: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:s|S|\u79d2)", text):
        candidates.append({"raw": match.group(0), "seconds": float(match.group(1))})
    return candidates


def _outro_trigger_frame(text: str) -> float | None:
    if not any(keyword in text for keyword in ("\u4e0a\u4e00", "\u524d\u4e00", "previous", "outro", "OUTRO")):
        return None
    frames = _frame_candidates(text)
    return frames[0]["frames"] if frames else None


def _state_grant_notes(text: str) -> list[str]:
    if "15" not in text:
        return []
    if any(token in text for token in ("15s", "15S", "15\u79d2")):
        return [text]
    return []


def _confidence(
    text: str,
    coefficients: list[dict[str, Any]],
    frames: list[dict[str, Any]],
    action_times: list[dict[str, Any]],
) -> str:
    score = 0
    upper = text.upper()
    if any(keyword in upper or keyword in text for keyword in ("QTE", "INTRO", "OUTRO", "\u53d8\u594f", "\u5ef6\u594f")):
        score += 2
    if coefficients:
        score += 1
    if frames or action_times:
        score += 1
    if score >= 4:
        return "medium"
    if score >= 2:
        return "low"
    return "very_low"


def _report_markdown(artifact: dict[str, Any]) -> str:
    lines = [
        "# Aemeath QTE / Intro / Outro Review",
        "",
        "Status: review-only, not applied, not executable.",
        "",
        f"Mojibake hints retained for reviewer search: {', '.join(MOJIBAKE_HINTS)}",
        "",
        f"Candidate rows: {artifact['candidate_count']}",
        "",
        "## Review Notes",
        "",
        "- These rows are not mapped into simulator actions.",
        "- Aemeath QTE/Intro/Outro remains disabled in transition_config.json.",
        "- Generic party swap fallback timing remains placeholder-only.",
        "",
        "## Candidates",
        "",
    ]
    for item in artifact["candidates"][:80]:
        lines.extend(
            [
                f"### {item['sheet']} row {item['row_number']}",
                "",
                f"- Source action: `{item.get('source_action_name')}`",
                f"- Confidence: {item['confidence']}",
                f"- Coefficients: `{item['coefficients']}`",
                f"- Frame candidates: `{item['frame_candidates']}`",
                f"- Action-time candidates: `{item['action_time_candidates']}`",
                f"- 15s state notes: `{item['state_grant_notes_15s']}`",
                f"- Raw row: {item['raw_row_text']}",
                "",
            ]
        )
    if artifact["candidate_count"] > 80:
        lines.append(f"... {artifact['candidate_count'] - 80} additional candidates omitted from report preview.")
    return "\n".join(lines) + "\n"


def main() -> int:
    artifact = extract()
    print(f"Wrote {artifact['candidate_count']} review-only QTE/Intro/Outro candidates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
