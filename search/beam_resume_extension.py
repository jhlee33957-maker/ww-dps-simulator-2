from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_REL = "results/beam_search_v114_lowmem_32gb"
DEFAULT_RECEIPT_REL = "results/beam_search_v114_3m_resume_extension_v115_receipt.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as file:
            json.dump(payload, file, indent=2, ensure_ascii=False)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def normalized_entry_digest(entries: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for entry in sorted(entries, key=lambda item: str(item["path"])):
        normalized = {
            "path": str(entry["path"]).replace("\\", "/"),
            "bytes": int(entry["bytes"]),
            "sha256": str(entry["sha256"]).lower(),
        }
        digest.update(json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def inventory_tree(output_root: Path, *, output_root_label: str = DEFAULT_OUTPUT_REL) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    total_bytes = 0
    for path in sorted(item for item in output_root.rglob("*") if item.is_file()):
        entry = {
            "path": path.relative_to(output_root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        entries.append(entry)
        total_bytes += int(entry["bytes"])
    return {
        "schema_version": "beam_search_checkpoint_inventory_v115",
        "output_root": output_root_label,
        "file_count": len(entries),
        "total_bytes": total_bytes,
        "inventory_sha256": normalized_entry_digest(entries),
        "entries": entries,
    }


def load_reviewed_inventory(*, project_root: Path, checkpoint_contract: dict[str, Any]) -> dict[str, Any]:
    path = project_root / str(checkpoint_contract.get("reviewed_inventory_path", ""))
    if not path.is_file():
        raise ValueError(f"Reviewed checkpoint inventory is missing: {path}")
    if sha256_file(path) != checkpoint_contract.get("reviewed_inventory_file_sha256"):
        raise ValueError("Reviewed checkpoint inventory file SHA-256 mismatch")
    inventory = json.loads(path.read_text(encoding="utf-8"))
    digest = normalized_entry_digest(list(inventory.get("entries", [])))
    if digest != checkpoint_contract.get("reviewed_inventory_entry_digest_sha256"):
        raise ValueError("Reviewed checkpoint inventory normalized entry digest mismatch")
    if digest != inventory.get("inventory_sha256"):
        raise ValueError("Reviewed checkpoint inventory internal digest mismatch")
    if int(inventory.get("file_count", -1)) != int(checkpoint_contract.get("file_count", -2)):
        raise ValueError("Reviewed checkpoint inventory file count mismatch")
    if int(inventory.get("total_bytes", -1)) != int(checkpoint_contract.get("total_bytes", -2)):
        raise ValueError("Reviewed checkpoint inventory byte count mismatch")
    if inventory.get("externally_reviewed_inventory_manifest_sha256") != checkpoint_contract.get("external_review_inventory_manifest_sha256"):
        raise ValueError("External review inventory manifest SHA-256 mismatch")
    return inventory


def _compare_inventory(observed: dict[str, Any], reviewed: dict[str, Any]) -> None:
    for key in ("file_count", "total_bytes", "inventory_sha256"):
        if observed.get(key) != reviewed.get(key):
            raise ValueError(f"Heavy checkpoint inventory {key} mismatch")
    observed_entries = {item["path"]: item for item in observed["entries"]}
    reviewed_entries = {item["path"]: item for item in reviewed["entries"]}
    missing = sorted(set(reviewed_entries) - set(observed_entries))
    added = sorted(set(observed_entries) - set(reviewed_entries))
    if missing or added:
        raise ValueError(f"Heavy checkpoint inventory path set mismatch missing={missing[:3]} added={added[:3]}")
    for path, expected in reviewed_entries.items():
        actual = observed_entries[path]
        if int(actual["bytes"]) != int(expected["bytes"]):
            raise ValueError(f"Heavy checkpoint inventory size mismatch: {path}")
        if actual["sha256"] != expected["sha256"]:
            raise ValueError(f"Heavy checkpoint inventory SHA-256 mismatch: {path}")


def extension_stage_compatible(saved: dict[str, Any], current: dict[str, Any], contract: dict[str, Any]) -> bool:
    allowed = set(contract.get("allowed_stage_differences", []))
    if allowed != {"maximum_expansions", "result_scope"}:
        return False
    saved_compare = dict(saved)
    current_compare = dict(current)
    saved_max = int(saved_compare.pop("maximum_expansions", -1))
    current_max = int(current_compare.pop("maximum_expansions", -1))
    saved_compare.pop("result_scope", None)
    current_compare.pop("result_scope", None)
    minimum = int(contract.get("minimum_new_maximum_expansions", 0))
    maximum = int(contract.get("maximum_new_maximum_expansions", 0))
    return saved_compare == current_compare and saved_max < current_max and minimum <= current_max <= maximum


def _resolve_stored_path(project_root: Path, output_root: Path, path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    project_candidate = project_root / path
    if project_candidate.exists():
        return project_candidate
    output_candidate = output_root / path
    if output_candidate.exists():
        return output_candidate
    return project_candidate


def _referenced_files(value: Any, *, project_root: Path, output_root: Path) -> list[tuple[Path, str]]:
    found: dict[Path, str] = {}
    if isinstance(value, dict):
        path_text = value.get("path")
        expected = value.get("sha256")
        if isinstance(path_text, str) and isinstance(expected, str) and len(expected) == 64:
            path = _resolve_stored_path(project_root, output_root, path_text).resolve()
            if output_root.resolve() in path.parents:
                found[path] = expected
        for child in value.values():
            for path, digest in _referenced_files(child, project_root=project_root, output_root=output_root):
                found[path] = digest
    elif isinstance(value, list):
        for child in value:
            for path, digest in _referenced_files(child, project_root=project_root, output_root=output_root):
                found[path] = digest
    return sorted(found.items(), key=lambda item: item[0].as_posix())


def _runtime_data_hashes(plan: dict[str, Any]) -> dict[str, str]:
    from search.beam_plan import V115_RESUME_V114_SCHEMA, resolve_plan_data_hashes

    if plan.get("schema_version") == V115_RESUME_V114_SCHEMA:
        return resolve_plan_data_hashes(plan)
    declared = plan.get("data_contract_hashes", {})
    return {key: str(declared[key]) for key in plan.get("resume_fixture_data_hash_keys", declared.keys()) if key in declared}


def _best_partial(output_root: Path, checkpoint_contract: dict[str, Any]) -> dict[str, Any]:
    source = output_root / str(checkpoint_contract.get("best_partial_source_path", "execution_result.json"))
    if not source.is_file():
        raise ValueError("Hash-pinned best-partial source result is missing")
    result = json.loads(source.read_text(encoding="utf-8"))
    best = result.get("best_partial_frontier_node") or {}
    expected = {
        "combat_time": checkpoint_contract.get("best_partial_combat_time"),
        "current_time": checkpoint_contract.get("best_partial_current_time"),
        "total_damage": checkpoint_contract.get("best_partial_total_damage"),
        "action_count": checkpoint_contract.get("best_partial_action_count"),
    }
    for key, value in expected.items():
        if best.get(key) != value:
            raise ValueError(f"Hash-pinned best-partial {key} mismatch")
    return best


def validate_hash_pinned_extension(
    *,
    project_root: Path,
    plan_path: Path,
    plan: dict[str, Any],
    stage: dict[str, Any],
    output_root: Path,
    write_receipt: bool,
) -> dict[str, Any]:
    project_root = project_root.resolve()
    plan_path = plan_path.resolve()
    output_root = output_root.resolve()
    contract = plan.get("resume_extension_contract") or {}
    checkpoint = plan.get("source_checkpoint_contract") or {}
    state_path = output_root / "search_state.json"
    if not state_path.is_file():
        raise ValueError(f"Missing source search state: {state_path}")
    state_hash_before = sha256_file(state_path)
    if state_hash_before != contract.get("source_search_state_sha256") or state_hash_before != checkpoint.get("search_state_sha256"):
        raise ValueError("Source search-state SHA-256 mismatch")
    source_plan = project_root / str(contract.get("source_plan_path", ""))
    if not source_plan.is_file() or sha256_file(source_plan) != contract.get("source_plan_sha256"):
        raise ValueError("Source plan SHA-256 mismatch")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("plan_sha256") != contract.get("source_plan_sha256"):
        raise ValueError("Source state plan SHA-256 mismatch")
    if state.get("stage", {}).get("stage_id") != contract.get("source_stage_id"):
        raise ValueError("Source stage ID mismatch")
    if int(state.get("expansions", -1)) != int(contract.get("source_checkpoint_expansions", -2)):
        raise ValueError("Source checkpoint expansion count mismatch")
    actual_hashes = _runtime_data_hashes(plan)
    if state.get("actual_data_hashes") != actual_hashes:
        raise ValueError("Source data-contract hashes mismatch")
    if not extension_stage_compatible(state.get("stage", {}), stage, contract):
        raise ValueError("Non-whitelisted search-stage field changed")
    if contract.get("reporting_metadata_affects_future_state_semantics") is not False:
        raise ValueError("Reporting-only result scope must be state-semantics neutral")
    canonical_rel = str(plan.get("output_contract", {}).get("canonical_output_root", ""))
    if output_root != (project_root / canonical_rel).resolve():
        raise ValueError("Canonical output root mismatch")
    referenced = _referenced_files(state, project_root=project_root, output_root=output_root)
    if not referenced:
        raise ValueError("State references no frontier or accumulator files")
    referenced_bytes = 0
    for path, expected in referenced:
        if not path.is_file():
            raise ValueError(f"Required checkpoint file is missing: {path}")
        if sha256_file(path) != expected:
            raise ValueError(f"Required checkpoint file hash mismatch: {path}")
        referenced_bytes += path.stat().st_size
    reviewed_inventory = load_reviewed_inventory(project_root=project_root, checkpoint_contract=checkpoint)
    observed_inventory = inventory_tree(output_root, output_root_label=canonical_rel)
    _compare_inventory(observed_inventory, reviewed_inventory)
    key_files = {
        "best_route.json": "best_route_sha256",
        "execution_result.json": "execution_result_sha256",
        "final_summary.json": "final_summary_sha256",
        "leaderboard.json": "leaderboard_sha256",
        "search_state.json": "search_state_sha256",
        "logs/full_120s_lowmem_32gb_v114.log": "log_sha256",
    }
    for relative, key in key_files.items():
        if sha256_file(output_root / relative) != checkpoint.get(key):
            raise ValueError(f"Reviewed key checkpoint hash mismatch: {relative}")
    best = _best_partial(output_root, checkpoint)
    module_path = Path(__file__).resolve()
    cli_path = project_root / "scripts/validate_beam_v114_3m_resume_extension_v115.py"
    try:
        module_label = module_path.relative_to(project_root).as_posix()
    except ValueError:
        module_label = "search/beam_resume_extension.py"
    state_hash_pre_receipt = sha256_file(state_path)
    if state_hash_pre_receipt != state_hash_before:
        raise ValueError("Source search_state.json changed during read-only preflight")
    receipt = {
        "schema_version": "beam_search_v114_3m_resume_extension_v115_receipt_v2",
        "status": "validated_not_executed",
        "source_output_root": canonical_rel,
        "source_plan_path": contract["source_plan_path"],
        "source_plan_sha256": contract["source_plan_sha256"],
        "source_search_state_path": f"{canonical_rel}/search_state.json",
        "source_search_state_sha256": state_hash_before,
        "source_search_state_sha256_after_validation": state_hash_before,
        "source_checkpoint_expansions": int(state["expansions"]),
        "source_completed_route_count": len(state.get("completed_routes", [])),
        "source_best_partial_combat_time": best["combat_time"],
        "source_best_partial_current_time": best["current_time"],
        "source_best_partial_total_damage": best["total_damage"],
        "source_best_partial_action_count": best["action_count"],
        "new_plan_path": plan_path.relative_to(project_root).as_posix(),
        "new_plan_sha256": sha256_file(plan_path),
        "new_maximum_expansions": int(stage["maximum_expansions"]),
        "allowed_differences": sorted(contract["allowed_stage_differences"]),
        "data_contract_hashes": actual_hashes,
        "referenced_frontier_file_count": len(referenced),
        "referenced_frontier_bytes": referenced_bytes,
        "reviewed_inventory_path": checkpoint["reviewed_inventory_path"],
        "reviewed_inventory_file_sha256": checkpoint["reviewed_inventory_file_sha256"],
        "reviewed_inventory_entry_digest_sha256": observed_inventory["inventory_sha256"],
        "frontier_inventory_file_count": observed_inventory["file_count"],
        "frontier_inventory_total_bytes": observed_inventory["total_bytes"],
        "preflight_module_path": module_label,
        "preflight_module_sha256": sha256_file(module_path),
        "validator_cli_sha256": sha256_file(cli_path) if cli_path.is_file() else None,
        "validation_timestamp": datetime.now(timezone.utc).isoformat(),
        "long_resume_executed": False,
    }
    if write_receipt:
        receipt_path = project_root / str(contract.get("receipt_path", DEFAULT_RECEIPT_REL))
        atomic_json(receipt_path, receipt)
    state_hash_after = sha256_file(state_path)
    if state_hash_after != state_hash_before:
        raise ValueError("Source search_state.json changed during preflight/receipt write")
    receipt["source_search_state_sha256_after_validation"] = state_hash_after
    return {
        "resume_mode": "validated_hash_pinned_extension",
        "state": state,
        "receipt": receipt,
        "inventory": observed_inventory,
        "state_sha256_before": state_hash_before,
        "state_sha256_after": state_hash_after,
    }
