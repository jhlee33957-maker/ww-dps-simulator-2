from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from search.mcts_checkpoint import atomic_json
from search.mcts_state import create_initial_simulation
from search.search_state_codec import sequence_sha256
from search.search_state_codec import sha256_file


ROOT = Path(__file__).resolve().parents[1]
BEAM_MANIFEST = Path("results/beam_search_v114_completed_v116/result_manifest.json")
BEAM_MANIFEST_SHA256 = "247f2a912d05bd4d89a3a7bbcb16c0877515427a8b46f7dc1795501b255b03ef"
MODEL_REFERENCE = {"kind": "best_trained_model", "total_damage": 5276844.358692044, "dps": 43973.70298910037,
                   "model_path": "models/guarded_ppo_v109/bc_conservative_seed_11/step_000090000.zip"}
MANUAL_REFERENCE = {"kind": "manual_v114", "total_damage": 5268418.084869607, "dps": 43903.484040580064}
BC_REFERENCE = {"kind": "historical_bc", "total_damage": 5165134.682363356, "dps": 43042.78901969464}


def replay_completed_route(route: dict[str, Any], *, write_root: Path | None = None) -> dict[str, Any]:
    simulation = create_initial_simulation(combat_duration=120.0)
    selected = list(route["selected_sequence"]); attempted: list[dict[str, Any]] = []
    for index, action_id in enumerate(selected, 1):
        available = action_id in simulation.valid_action_ids()
        success = simulation.execute_action(action_id) if available else False
        row = simulation.timeline[-1] if success and simulation.timeline else None
        attempted.append({"step": index, "selected_action_id": action_id, "available_before_execution": available,
                          "executed": success, "resolved_action_id": None if row is None else row.resolved_action_id})
        if not success: raise RuntimeError(f"MCTS route replay failed at step {index}: {action_id}")
    resolved = [row.resolved_action_id for row in simulation.timeline]
    rows = [row.model_dump(mode="json") for row in simulation.timeline]
    summary = {"schema_version": "mcts_route_replay_summary_v117", "route_id": route["route_id"],
               "selected_action_count": len(selected), "resolved_action_count": len(resolved),
               "executed_action_count": len(simulation.timeline), "selected_sequence_sha256": sequence_sha256(selected),
               "resolved_sequence_sha256": sequence_sha256(resolved), "total_damage": float(simulation.state.total_damage),
               "dps": float(simulation.state.total_damage) / 120.0, "final_combat_time": float(simulation.state.combat_time),
               "final_current_time": float(simulation.state.current_time), "timeline_damage_sum": sum(float(row.get("damage", 0.0)) for row in rows),
               "attempted_actions": attempted, "global_optimum_proven": False}
    if summary["selected_sequence_sha256"] != route["selected_sequence_sha256"]: raise RuntimeError("MCTS replay selected-route hash mismatch")
    if abs(summary["total_damage"] - float(route["total_damage"])) > 1e-9: raise RuntimeError("MCTS replay damage mismatch")
    if summary["final_combat_time"] != 120.0 or len(selected) != len(resolved): raise RuntimeError("MCTS replay did not complete exactly")
    if abs(summary["timeline_damage_sum"] - summary["total_damage"]) > 1e-6: raise RuntimeError("MCTS replay timeline damage mismatch")
    if write_root is not None:
        route_dir = write_root / "routes"; route_dir.mkdir(parents=True, exist_ok=True)
        atomic_json(route_dir / f"{route['route_id']}_summary.json", summary)
        _write_timeline(route_dir / f"{route['route_id']}_timeline.csv", rows)
    return summary


def comparison_for_completed_route(route: dict[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    manifest_path = root / BEAM_MANIFEST
    if not manifest_path.is_file():
        return {"status": "unavailable", "reason": "compact Beam winner manifest unavailable", "search_result_valid": True}
    actual_sha256 = sha256_file(manifest_path)
    if actual_sha256 != BEAM_MANIFEST_SHA256:
        return {"status": "unavailable", "reason": "compact Beam winner manifest integrity error",
                "expected_sha256": BEAM_MANIFEST_SHA256, "actual_sha256": actual_sha256,
                "search_result_valid": True}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")); beam = manifest.get("winning_route")
    if manifest.get("termination_status") != "completed_search" or not isinstance(beam, dict):
        return {"status": "unavailable", "reason": "compact Beam winner manifest invalid", "search_result_valid": True}
    candidates = [{"kind": "mcts_completed_route", **{k: route[k] for k in ("route_id", "total_damage", "dps", "selected_sequence_sha256")}},
                  {"kind": "beam_search_route", **beam}, MODEL_REFERENCE, MANUAL_REFERENCE, BC_REFERENCE]
    winner = max(candidates, key=lambda item: (float(item["total_damage"]), item.get("selected_sequence_sha256", "")))
    return {"status": "available", "selection": "maximum_completed_120s_total_damage_only", "candidates": candidates,
            "overall_project_winner": winner, "delta_mcts_vs_beam": float(route["total_damage"]) - float(beam["total_damage"]),
            "global_optimum_proven": False}


def write_mcts_results(output_root: Path, result: dict[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    routes = list(result.pop("_completed_routes")) if "_completed_routes" in result else []
    validated: list[dict[str, Any]] = []
    for route in routes:
        replay = replay_completed_route(route, write_root=output_root if route is routes[0] else None)
        enriched = dict(route); enriched["resolved_sequence_sha256"] = replay["resolved_sequence_sha256"]
        validated.append(enriched)
    validated.sort(key=lambda item: (-float(item["total_damage"]), item["selected_sequence_sha256"]))
    best = validated[0] if validated else None
    comparison = comparison_for_completed_route(best, root=root) if best else {"status": "unavailable", "reason": "no completed MCTS route", "search_result_valid": True}
    result["best_completed_route"] = best; result["comparison"] = comparison
    atomic_json(output_root / "execution_result.json", result)
    leaderboard = {"schema_version": "mcts_leaderboard_v117", "objective": "deterministic_completed_120s_total_damage",
                   "completed_route_count": int(result["completed_rollout_count"]), "retained_route_count": len(validated),
                   "sort": "total_damage_desc_then_selected_sha_asc", "routes": validated, "winner": best,
                   "partial_routes_compete": False, "global_optimum_proven": False}
    atomic_json(output_root / "leaderboard.json", leaderboard)
    atomic_json(output_root / "completed_routes_compact.json", leaderboard)
    atomic_json(output_root / "best_route.json", {"winner": best, "comparison": comparison, "global_optimum_proven": False})
    final = {"schema_version": "mcts_final_summary_v117", "termination_status": result["termination_status"],
             "simulations_completed": result["simulations_completed"], "winner": best, "comparison": comparison,
             "calibration_only": True, "global_optimum_proven": False}
    atomic_json(output_root / "final_summary.json", final)
    return {"result": result, "leaderboard": leaderboard, "final_summary": final}


def _write_timeline(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = ["selected_action_id", "resolved_action_id", "character_id", "actor_character_id", "time_start", "time_end",
              "combat_time_start", "combat_time_end", "combat_time_cost", "effective_combat_time_cost", "damage",
              "total_damage_after", "scheduled_damage", "generated_mechanic_damage", "truncated_by_combat_limit"]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields); writer.writeheader()
        for row in rows: writer.writerow({field: _csv(row.get(field)) for field in fields})


def _csv(value: Any) -> Any:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) if isinstance(value, (dict, list)) else value
