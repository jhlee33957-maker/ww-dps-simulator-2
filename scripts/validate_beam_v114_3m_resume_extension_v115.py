from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_plan import load_plan, stage_by_id, validate_plan  # noqa: E402
from search.beam_resume_extension import atomic_json, validate_hash_pinned_extension  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only validation of the exact v114 3M checkpoint for the v115 extension.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--inventory-output", type=Path, required=True)
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    plan_path = args.plan if args.plan.is_absolute() else project_root / args.plan
    output_root = args.output_root if args.output_root.is_absolute() else project_root / args.output_root
    plan = load_plan(plan_path)
    validate_plan(plan, plan_path=plan_path)
    stage = stage_by_id(plan, str(plan["resume_extension_contract"]["source_stage_id"]))
    result = validate_hash_pinned_extension(
        project_root=project_root,
        plan_path=plan_path,
        plan=plan,
        stage=stage,
        output_root=output_root,
        write_receipt=args.write_receipt,
    )
    inventory_output = args.inventory_output if args.inventory_output.is_absolute() else project_root / args.inventory_output
    observed = dict(result["inventory"])
    observed["externally_reviewed_inventory_manifest_sha256"] = plan["source_checkpoint_contract"]["external_review_inventory_manifest_sha256"]
    atomic_json(inventory_output, observed)
    receipt = result["receipt"]
    print(json.dumps({
        "status": receipt["status"],
        "resume_mode": result["resume_mode"],
        "state_sha256_before": result["state_sha256_before"],
        "state_sha256_after": result["state_sha256_after"],
        "referenced_file_count": receipt["referenced_frontier_file_count"],
        "inventory_file_count": result["inventory"]["file_count"],
        "inventory_total_bytes": result["inventory"]["total_bytes"],
        "receipt_written": args.write_receipt,
    }, separators=(",", ":")))


if __name__ == "__main__":
    main()
