from __future__ import annotations

import json
from pathlib import Path


class TimingObservationAuditRequired(RuntimeError):
    pass


def load_timing_runtime_gate(project_root: Path | str | None = None) -> dict:
    root = Path(project_root) if project_root is not None else Path(__file__).resolve().parents[1]
    with (root / "data" / "timing_runtime_gate_v124.json").open("r", encoding="utf-8") as file:
        return json.load(file)


def assert_timing_runtime_workload_allowed(workload: str, project_root: Path | str | None = None) -> None:
    gate = load_timing_runtime_gate(project_root)
    normalized = str(workload).upper()
    allowed_key = "search_allowed_after_timing_patch" if normalized in {"BEAM", "MCTS"} else "training_allowed_after_timing_patch"
    if not bool(gate.get(allowed_key, False)):
        raise TimingObservationAuditRequired(
            f"{normalized} is blocked for timing-core-1 until observation v7 is implemented after the Markov-state audit."
        )
