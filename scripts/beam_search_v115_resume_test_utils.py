from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from search.beam_plan import V114_LOWMEM_32GB_PLAN_PATH, load_plan, resolve_plan_data_hashes
from search.beam_resume_extension import inventory_tree, normalized_entry_digest, sha256_file
from search.beam_search import BeamSearchRunner


STAGE_ID = "full_120s_lowmem_32gb_v114"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def fixture_stage(maximum_expansions: int) -> dict[str, Any]:
    stage = copy.deepcopy(load_plan(V114_LOWMEM_32GB_PLAN_PATH)["stages"][0])
    stage.update({
        "combat_duration": 3.0,
        "beam_width": 64,
        "global_damage_quota": 32,
        "diversity_retention_quota": 32,
        "max_states_per_diversity_key": 4,
        "maximum_expansions": maximum_expansions,
        "checkpoint_interval_expansions": 10,
        "memory_budget_bytes": 536870912,
        "max_unique_fingerprints_per_destination_bucket": 1024,
        "destination_accumulator_unique_fingerprint_bound": 1024,
        "in_memory_accumulator_candidate_limit": 256,
    })
    return stage


def build_resume_fixture(root: Path, *, source_budget: int = 20, final_budget: int = 300) -> dict[str, Any]:
    source_plan_path = root / "data/source_plan.json"
    output_root = root / "results/fixture_checkpoint"
    old_plan = load_plan(V114_LOWMEM_32GB_PLAN_PATH)
    old_plan = copy.deepcopy(old_plan)
    old_plan["output_contract"]["canonical_output_root"] = "results/fixture_checkpoint"
    old_stage = fixture_stage(source_budget)
    old_plan["stages"] = [old_stage]
    write_json(source_plan_path, old_plan)
    source_result = BeamSearchRunner(
        plan=old_plan,
        stage=old_stage,
        plan_path=source_plan_path,
        output_root=output_root,
    ).run()
    source_state = json.loads((output_root / "search_state.json").read_text(encoding="utf-8"))
    best = json.loads((output_root / "execution_result.json").read_text(encoding="utf-8"))["best_partial_frontier_node"]
    if not best:
        raise AssertionError("Fixture source budget must retain a diagnostic partial node")
    inventory = inventory_tree(output_root, output_root_label="results/fixture_checkpoint")
    inventory["externally_reviewed_inventory_manifest_sha256"] = "fixture_review_manifest_sha256"
    reviewed_inventory_path = root / "results/reviewed_inventory.json"
    write_json(reviewed_inventory_path, inventory)
    new_plan = copy.deepcopy(old_plan)
    new_plan["schema_version"] = "beam_search_plan_v115_fixture"
    new_plan["candidate"] = 115
    new_stage = fixture_stage(final_budget)
    new_stage["result_scope"] = "completed_120s_project_comparison"
    new_plan["stages"] = [new_stage]
    new_plan["execution_contract"] = {
        "low_memory_32gb": True,
        "hard_memory_budget_required": True,
        "canonical_output_root_required_for_resume": True,
        "reviewed_memory_budget_bytes": 536870912,
        "memory_budget_cli_policy": "may_lower_never_raise",
        "safety_gates_plan_capability_driven": True,
    }
    state_hashes = source_state["actual_data_hashes"]
    new_plan["data_contract_hashes"] = dict(state_hashes)
    new_plan["resume_fixture_data_hash_keys"] = list(state_hashes)
    new_plan["resume_extension_contract"] = {
        "enabled": True,
        "source_plan_path": "data/source_plan.json",
        "source_plan_sha256": sha256_file(source_plan_path),
        "source_stage_id": STAGE_ID,
        "source_checkpoint_expansions": source_budget,
        "source_search_state_sha256": sha256_file(output_root / "search_state.json"),
        "receipt_path": "results/fixture_receipt.json",
        "allowed_stage_differences": ["maximum_expansions", "result_scope"],
        "minimum_new_maximum_expansions": source_budget + 1,
        "maximum_new_maximum_expansions": final_budget,
        "reporting_metadata_affects_future_state_semantics": False,
    }
    new_plan["source_checkpoint_contract"] = {
        "reviewed_inventory_path": "results/reviewed_inventory.json",
        "reviewed_inventory_file_sha256": sha256_file(reviewed_inventory_path),
        "reviewed_inventory_entry_digest_sha256": normalized_entry_digest(inventory["entries"]),
        "external_review_inventory_manifest_sha256": "fixture_review_manifest_sha256",
        "file_count": inventory["file_count"],
        "total_bytes": inventory["total_bytes"],
        "best_route_sha256": sha256_file(output_root / "best_route.json"),
        "execution_result_sha256": sha256_file(output_root / "execution_result.json"),
        "final_summary_sha256": sha256_file(output_root / "final_summary.json"),
        "leaderboard_sha256": sha256_file(output_root / "leaderboard.json"),
        "search_state_sha256": sha256_file(output_root / "search_state.json"),
        "log_sha256": sha256_file(output_root / f"logs/{STAGE_ID}.log"),
        "best_partial_source_path": "execution_result.json",
        "best_partial_combat_time": best["combat_time"],
        "best_partial_current_time": best["current_time"],
        "best_partial_total_damage": best["total_damage"],
        "best_partial_action_count": best["action_count"],
    }
    reviewed = load_plan(Path("data/beam_search_plan_v115_32gb_resume_v114.json"))
    new_plan["comparison_reference"] = reviewed["comparison_reference"]
    new_plan["comparison_incumbent_contract"] = reviewed["comparison_incumbent_contract"]
    extension_plan_path = root / "data/extension_plan.json"
    write_json(extension_plan_path, new_plan)
    return {
        "root": root,
        "source_plan_path": source_plan_path,
        "extension_plan_path": extension_plan_path,
        "output_root": output_root,
        "source_result": source_result,
        "source_state": source_state,
        "plan": new_plan,
        "stage": new_stage,
        "final_budget": final_budget,
    }


def tree_snapshot(root: Path) -> dict[str, tuple[int, int, str]]:
    return {
        path.relative_to(root).as_posix(): (path.stat().st_size, path.stat().st_mtime_ns, sha256_file(path))
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    }


def retained_signature(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "expansions": state["expansions"],
        "completed_routes": state.get("completed_routes", []),
        "completed_buckets": state.get("completed_buckets", []),
        "pending_buckets": [
            (item["bucket_index"], item["node_count"])
            for item in state.get("pending_buckets", [])
        ],
        "route_store": state.get("route_store", {}),
        "best_completed_search_route": state.get("best_completed_search_route"),
    }


def frontier_content_signature(output_root: Path, state: dict[str, Any]) -> list[tuple[int, list[tuple[int, str, float, float]]]]:
    import gzip

    signature = []
    for item in state.get("pending_buckets", []):
        stored = Path(str(item["path"]))
        path = output_root.parent.parent / stored
        if not path.exists():
            path = output_root / stored
        with gzip.open(path, "rt", encoding="utf-8") as file:
            payload = json.load(file)
        nodes = [
            (int(node["node_id"]), str(node["future_fingerprint"]), float(node["combat_time"]), float(node["total_damage"]))
            for node in payload.get("nodes", [])
        ]
        signature.append((int(item["bucket_index"]), nodes))
    return signature
