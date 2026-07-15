from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMPATIBILITY_PATH = Path("data/mcts_result_role_compatibility_v119.json")
VALID_ROLES = {"calibration", "production"}


def resolve_mcts_result_role(
    plan_path: Path,
    plan_sha256: str,
    stage_id: str,
    stage: dict[str, Any],
    *,
    root: Path = ROOT,
) -> str:
    """Resolve a stage result role without name/count inference."""
    explicit = stage.get("result_role")
    if explicit is not None:
        if explicit not in VALID_ROLES:
            raise ValueError(f"Unknown explicit MCTS result_role: {explicit!r}")
        return str(explicit)

    path = plan_path if plan_path.is_absolute() else root / plan_path
    if not path.is_file():
        raise ValueError(f"MCTS result-role plan does not exist: {path}")
    actual_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_sha256 != plan_sha256:
        raise ValueError(
            f"MCTS result-role plan SHA mismatch: declared={plan_sha256} actual={actual_sha256}"
        )

    contract = json.loads((root / COMPATIBILITY_PATH).read_text(encoding="utf-8"))
    if contract.get("schema_version") != "mcts_result_role_compatibility_v119":
        raise ValueError("MCTS result-role compatibility schema mismatch")
    if set(contract.get("valid_result_roles", [])) != VALID_ROLES:
        raise ValueError("MCTS result-role compatibility valid-role set mismatch")
    plan_entry = (contract.get("plans") or {}).get(plan_sha256)
    if not isinstance(plan_entry, dict):
        raise ValueError(f"Unknown hash-pinned MCTS result-role plan: {plan_sha256}")
    expected_path = str(plan_entry.get("plan_path", "")).replace("\\", "/")
    try:
        actual_relative = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as error:
        raise ValueError("MCTS result-role plan is outside the project root") from error
    if actual_relative != expected_path:
        raise ValueError(
            f"MCTS result-role plan path mismatch: {actual_relative!r} != {expected_path!r}"
        )
    role = (plan_entry.get("stages") or {}).get(stage_id)
    if role not in VALID_ROLES:
        raise ValueError(
            f"Unknown hash-pinned MCTS result-role stage: plan={plan_sha256} stage={stage_id}"
        )
    return str(role)


def result_role_fields(role: str) -> dict[str, bool | str]:
    if role not in VALID_ROLES:
        raise ValueError(f"Unknown MCTS result role: {role!r}")
    return {
        "result_role": role,
        "calibration_only": role == "calibration",
        "production_search_result": role == "production",
        "global_optimum_proven": False,
    }
