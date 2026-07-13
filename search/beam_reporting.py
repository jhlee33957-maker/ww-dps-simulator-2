from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from rl.damage_attribution import damage_by_character
from rl.demo_contract import action_data_hash, party_config_hash
from rl.evaluation_report import build_generated_damage_summary
from simulator.simulation import Simulation


ROOT = Path(__file__).resolve().parents[1]

BC_TOTAL_DAMAGE = 5165134.682363356
BC_DPS = 43042.78901969464
BC_SELECTED_SEQUENCE_SHA256 = "e3ddea873cb5059bd29a8a9eb7165ea0e45a9a9e4fa4f68e5e229db2f622daf1"
BC_RESOLVED_SEQUENCE_SHA256 = "3edca6f6f258999a9c915a9ec32ee88c0db570d2303846e0fb8b6da367970229"
BC_MODEL_PATH = "models/maskable_ppo_bc_v105.zip"
EXPECTED_BC_MODEL_SHA256 = "7b5ef151b7ac9299a8134032e58f1d75919832a3823c8715653852393045461e"
PPO_MODEL_SHA256 = "9b62faa610c3710bf4e17603a92baf8e8c657b51e8fba22d8525a1e33a257513"
BC_NPZ_SHA256 = "b020a1b9309b46bd87eb3fff4837aead53035c4c84620962f47feb9fc11846ff"
MANUAL_ROUTE_SHA256 = "c510204b78fc547e2ba1224e82193cbaf43728d9a4107eb1090b6ebaab59a90a"


def select_damage_only_winner(candidates: list[dict[str, Any]], *, tolerance: float = 1e-6) -> dict[str, Any] | None:
    incumbent = verified_bc_incumbent_manifest()
    all_candidates = [incumbent, *candidates]
    best = all_candidates[0]
    for candidate in all_candidates[1:]:
        delta = float(candidate["total_damage"]) - float(best["total_damage"])
        if delta > tolerance:
            best = candidate
        elif abs(delta) <= tolerance:
            if _tie_rank(candidate) > _tie_rank(best):
                best = candidate
    return best


def _tie_rank(candidate: dict[str, Any]) -> tuple[int, int]:
    verified = int(bool(candidate.get("externally_verified_immutable")) or candidate.get("winner_kind") == "verified_bc_model")
    earlier = -int(candidate.get("declared_order", 10_000_000))
    return (verified, earlier)


def verified_bc_incumbent_manifest() -> dict[str, Any]:
    return {
        "schema_version": "beam_search_verified_bc_incumbent_v111",
        "winner_kind": "verified_bc_model",
        "model_path": BC_MODEL_PATH,
        "model_sha256": EXPECTED_BC_MODEL_SHA256,
        "total_damage": BC_TOTAL_DAMAGE,
        "dps": BC_DPS,
        "selected_sequence_sha256": BC_SELECTED_SEQUENCE_SHA256,
        "resolved_sequence_sha256": BC_RESOLVED_SEQUENCE_SHA256,
        "externally_verified_immutable": True,
        "declared_order": 0,
        "manual_bc_ratio": 1.0,
        "manual_bc_delta": 0.0,
        "selection_reason": "externally verified BC incumbent is the damage-only incumbent until a completed 120s Beam route exceeds it",
        "objective": "deterministic_120s_total_damage_only",
        "global_optimum_proven": False,
    }


def replay_selected_route_to_files(
    *,
    selected_sequence: list[str],
    output_root: Path,
    route_id: str | None = None,
    combat_duration: float = 120.0,
    party: str | list[str] = "aemeath_mornye_lynae_enabled_test_party",
    initial_active_character: str = "aemeath",
    terminal_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if party != "aemeath_mornye_lynae_enabled_test_party":
        raise ValueError(f"Unsupported Beam Search replay party: {party!r}")
    route_id = route_id or _sequence_sha256(selected_sequence)[:16]
    route_dir = output_root / "routes"
    route_dir.mkdir(parents=True, exist_ok=True)
    simulation = Simulation.from_json(
        ROOT / "data",
        selected_character_ids=party,
        initial_active_character=initial_active_character,
        transition_config=None,
    )
    simulation.combat_duration = float(combat_duration)
    simulation.state.combat_duration = simulation.combat_duration
    attempted: list[dict[str, Any]] = []
    for index, selected_action_id in enumerate(selected_sequence, start=1):
        available = selected_action_id in simulation.valid_action_ids()
        success = simulation.execute_action(selected_action_id) if available else False
        row = simulation.timeline[-1] if success and simulation.timeline else None
        attempted.append(
            {
                "step": index,
                "selected_action_id": selected_action_id,
                "available_before_execution": available,
                "executed": success,
                "resolved_action_id": None if row is None else row.resolved_action_id,
                "combat_time_after": float(simulation.state.combat_time),
                "total_damage_after": float(simulation.state.total_damage),
            }
        )
        if not success:
            raise RuntimeError(f"Beam route replay failed at step {index}: selected action unavailable or failed: {selected_action_id}")
    if len(simulation.timeline) != len(selected_sequence):
        raise RuntimeError(
            f"Beam route replay did not execute every action: executed={len(simulation.timeline)} selected={len(selected_sequence)}"
        )
    resolved_sequence = [row.resolved_action_id for row in simulation.timeline]
    total_damage = float(simulation.state.total_damage)
    rows = [row.model_dump(mode="json") for row in simulation.timeline]
    generated_summary = build_generated_damage_summary(rows, total_damage=total_damage)
    character_damage = damage_by_character(rows, total_damage=total_damage)
    action_counts = _counts(selected_sequence)
    resolved_counts = _counts(resolved_sequence)
    damage_by_action_id = _damage_by(rows, "resolved_action_id")
    damage_by_category = _damage_by(rows, "damage_bonus_category")
    manual = _manual_route_reference()
    comparison = _route_comparison(selected_sequence, resolved_sequence, total_damage, manual, combat_duration=float(combat_duration))
    summary = {
        "schema_version": "beam_search_route_replay_summary_v111",
        "route_id": route_id,
        "combat_duration": float(combat_duration),
        "reference_horizon_seconds": 120.0,
        "reference_damage_comparison_status": (
            "comparable_120s_completed_route"
            if _is_120s_horizon(float(combat_duration))
            else "horizon_mismatch_not_comparable"
        ),
        "party": party,
        "initial_active_character": initial_active_character,
        "active_build_profiles": _active_build_profiles(simulation),
        "selected_action_count": len(selected_sequence),
        "resolved_action_count": len(resolved_sequence),
        "executed_action_count": len(simulation.timeline),
        "selected_sequence_sha256": _sequence_sha256(selected_sequence),
        "resolved_sequence_sha256": _sequence_sha256(resolved_sequence),
        "total_damage": total_damage,
        "dps": total_damage / max(float(combat_duration), 1e-9),
        "final_combat_time": float(simulation.state.combat_time),
        "final_current_time": float(simulation.state.current_time),
        "damage_by_character": character_damage,
        "damage_by_character_sum": sum(character_damage.values()),
        "damage_by_character_and_source": generated_summary["damage_by_character_and_source"],
        "effective_damage_role_breakdown": generated_summary["effective_damage_role_breakdown"],
        "damage_by_action_id": damage_by_action_id,
        "damage_by_category": damage_by_category,
        "action_use_counts": action_counts,
        "resolved_action_use_counts": resolved_counts,
        "scheduled_damage": generated_summary["effective_damage_role_breakdown"]["scheduled_damage"],
        "route_comparison": comparison,
        "comparison_against_references": _reference_comparisons(total_damage, combat_duration=float(combat_duration)),
        "metadata_model_space_mismatch_status": "none_party_preset_replay_uses_project_model_space",
        "data_contract_hashes": {
            "action_data_hash": action_data_hash(root=ROOT),
            "party_config_hash": party_config_hash(root=ROOT),
            "manual_route_raw_sha256": MANUAL_ROUTE_SHA256,
            "bc_npz_sha256": BC_NPZ_SHA256,
            "bc_model_sha256": EXPECTED_BC_MODEL_SHA256,
            "prior_ppo_model_sha256": PPO_MODEL_SHA256,
        },
        "attempted_actions": attempted,
        "summary_path": f"routes/{route_id}_summary.json",
        "timeline_csv_path": f"routes/{route_id}_timeline.csv",
    }
    summary.update({key: value for key, value in generated_summary.items() if key not in summary})
    if terminal_record is not None:
        _assert_replay_matches_terminal(summary, terminal_record)
    summary_path = route_dir / f"{route_id}_summary.json"
    timeline_path = route_dir / f"{route_id}_timeline.csv"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_timeline_csv(timeline_path, simulation.timeline)
    return summary


def _write_timeline_csv(path: Path, rows: list[Any]) -> None:
    fields = [
        "selected_action_id",
        "resolved_action_id",
        "character_id",
        "actor_character_id",
        "time_start",
        "time_end",
        "combat_time_start",
        "combat_time_end",
        "combat_time_cost",
        "effective_combat_time_cost",
        "damage",
        "total_damage_after",
        "scheduled_damage",
        "generated_mechanic_damage",
        "truncated_by_combat_limit",
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            data = row.model_dump(mode="json") if hasattr(row, "model_dump") else dict(row)
            writer.writerow({field: _csv_value(data.get(field)) for field in fields})


def _csv_value(value: Any) -> str | int | float | bool | None:
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return value


def _sequence_sha256(sequence: list[str]) -> str:
    return hashlib.sha256(json.dumps(list(sequence), separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _assert_replay_matches_terminal(summary: dict[str, Any], terminal: dict[str, Any]) -> None:
    checks = [
        ("total_damage", 1e-9),
        ("combat_time", 1e-9),
        ("current_time", 1e-9),
    ]
    aliases = {"combat_time": "final_combat_time", "current_time": "final_current_time"}
    for key, tolerance in checks:
        summary_key = aliases.get(key, key)
        if abs(float(summary[summary_key]) - float(terminal[key])) > tolerance:
            raise RuntimeError(f"Beam route replay parity failed for {key}: replay={summary[summary_key]} terminal={terminal[key]}")
    for key in ("selected_sequence_sha256", "resolved_sequence_sha256"):
        if summary[key] != terminal[key]:
            raise RuntimeError(f"Beam route replay hash mismatch for {key}: replay={summary[key]} terminal={terminal[key]}")
    if int(summary["selected_action_count"]) != int(terminal["action_count"]):
        raise RuntimeError("Beam route replay action-count mismatch")


def _active_build_profiles(simulation: Simulation) -> dict[str, dict[str, Any]]:
    return {
        character_id: {
            "build_profile_id": getattr(character, "build_profile_id", None),
            "weapon": getattr(character, "weapon", None),
            "echo_sets": getattr(character, "echo_sets", None),
            "profile_completeness_status": getattr(character, "profile_completeness_status", None),
            "default_scaling_stat": getattr(character, "default_scaling_stat", None),
        }
        for character_id, character in sorted(simulation.characters.items())
    }


def _counts(items: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return dict(sorted(counts.items()))


def _damage_by(rows: list[dict[str, Any]], key: str) -> dict[str, float]:
    totals: dict[str, float] = {}
    for row in rows:
        label = str(row.get(key) or "unknown")
        totals[label] = totals.get(label, 0.0) + float(row.get("total_action_damage", row.get("damage", 0.0)) or 0.0)
    return dict(sorted(totals.items()))


def _manual_route_reference() -> dict[str, Any]:
    path = ROOT / "data" / "manual_120s_baseline_routes_v104.json"
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    primary = data["routes"]["primary"]
    return {
        "selected": list(primary["selected_policy_actions"]),
        "resolved": list(primary["expected_resolved_actions"]),
        "selected_sequence_sha256": BC_SELECTED_SEQUENCE_SHA256,
        "resolved_sequence_sha256": BC_RESOLVED_SEQUENCE_SHA256,
        "total_damage": BC_TOTAL_DAMAGE,
    }


def _route_comparison(selected: list[str], resolved: list[str], total_damage: float, manual: dict[str, Any], *, combat_duration: float) -> dict[str, Any]:
    selected_prefix = _common_prefix_length(selected, manual["selected"])
    resolved_prefix = _common_prefix_length(resolved, manual["resolved"])
    payload = {
        "manual_bc_selected_common_prefix": selected_prefix,
        "manual_bc_resolved_common_prefix": resolved_prefix,
        "first_selected_divergence": _first_divergence(selected, manual["selected"]),
        "first_resolved_divergence": _first_divergence(resolved, manual["resolved"]),
        "selected_positional_agreement_count": _positional_agreement(selected, manual["selected"]),
        "resolved_positional_agreement_count": _positional_agreement(resolved, manual["resolved"]),
        "route_horizon_seconds": float(combat_duration),
        "reference_horizon_seconds": 120.0,
        "reference_damage_comparison_status": (
            "comparable_120s_completed_route"
            if _is_120s_horizon(float(combat_duration))
            else "horizon_mismatch_not_comparable"
        ),
    }
    if _is_120s_horizon(float(combat_duration)):
        payload["manual_bc_damage_delta"] = total_damage - float(manual["total_damage"])
        payload["manual_bc_damage_ratio"] = total_damage / float(manual["total_damage"]) if manual["total_damage"] else None
    return payload


def _reference_comparisons(total_damage: float, *, combat_duration: float) -> dict[str, Any]:
    if not _is_120s_horizon(float(combat_duration)):
        return {
            "reference_damage_comparison_status": "horizon_mismatch_not_comparable",
            "route_horizon_seconds": float(combat_duration),
            "reference_horizon_seconds": 120.0,
            "numeric_total_damage_ranking": None,
        }
    ppo = _load_json_if_exists(ROOT / "results" / "ppo_100k_evaluation_summary.json")
    guarded = _load_json_if_exists(ROOT / "results" / "guarded_ppo_v109" / "experiment_state.json")
    return {
        "reference_damage_comparison_status": "comparable_120s_completed_route",
        "route_horizon_seconds": float(combat_duration),
        "reference_horizon_seconds": 120.0,
        "manual_baseline": {"total_damage": BC_TOTAL_DAMAGE, "delta": total_damage - BC_TOTAL_DAMAGE},
        "verified_bc": verified_bc_incumbent_manifest() | {"delta": total_damage - BC_TOTAL_DAMAGE},
        "prior_ppo_100k": _comparison_from_summary(total_damage, ppo),
        "guarded_ppo_v109": _guarded_comparison(total_damage, guarded),
    }


def _is_120s_horizon(combat_duration: float) -> bool:
    return abs(float(combat_duration) - 120.0) <= 1e-9


def _comparison_from_summary(total_damage: float, summary: dict[str, Any] | None) -> dict[str, Any] | None:
    if not summary:
        return None
    reference = float(summary.get("total_damage", summary.get("deterministic_total_damage", 0.0)) or 0.0)
    return {"total_damage": reference, "delta": total_damage - reference}


def _guarded_comparison(total_damage: float, state: dict[str, Any] | None) -> dict[str, Any] | None:
    if not state:
        return None
    best = state.get("best_result") or state.get("winner") or {}
    reference = float(best.get("total_damage", BC_TOTAL_DAMAGE) or BC_TOTAL_DAMAGE)
    return {
        "checkpoint_count": sum(len(branch.get("chunks", [])) for branch in state.get("branches", {}).values()),
        "best_total_damage": reference,
        "delta": total_damage - reference,
    }


def _load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _common_prefix_length(left: list[str], right: list[str]) -> int:
    count = 0
    for left_item, right_item in zip(left, right):
        if left_item != right_item:
            break
        count += 1
    return count


def _first_divergence(left: list[str], right: list[str]) -> dict[str, Any] | None:
    for index, (left_item, right_item) in enumerate(zip(left, right), start=1):
        if left_item != right_item:
            return {"position": index, "route_action": left_item, "manual_bc_action": right_item}
    if len(left) != len(right):
        return {"position": min(len(left), len(right)) + 1, "route_action": left[min(len(left), len(right))] if len(left) > len(right) else None, "manual_bc_action": right[min(len(left), len(right))] if len(right) > len(left) else None}
    return None


def _positional_agreement(left: list[str], right: list[str]) -> int:
    return sum(1 for left_item, right_item in zip(left, right) if left_item == right_item)
