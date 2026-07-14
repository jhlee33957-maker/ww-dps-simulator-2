from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import search.beam_search as beam_search
from scripts.beam_search_v115_resume_test_utils import build_resume_fixture, frontier_content_signature, retained_signature
from search.beam_resume_extension import sha256_file


def args_for(plan: Path, output: Path, *, resume: bool) -> argparse.Namespace:
    return argparse.Namespace(
        plan=plan, dry_run_plan=False, execute=True, resume=resume, only_stage="full_120s_lowmem_32gb_v114",
        max_expansions=None, output_root=output, smoke_run=False, wall_clock_limit_seconds=None,
        memory_budget_bytes=None,
    )


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="beam-v115-runner-") as temp_dir:
        fixture = build_resume_fixture(Path(temp_dir))
        source_state_hash = sha256_file(fixture["output_root"] / "search_state.json")
        assert beam_search._resume_extension_plan_compatible(fixture["source_state"], fixture["plan"]) is True
        assert beam_search._resume_stage_compatible(fixture["source_state"]["stage"], fixture["stage"]) is False
        original_validate = beam_search.validate_plan
        beam_search.validate_plan = lambda plan, plan_path: {"status": "fixture_ok"}
        try:
            resumed = beam_search.run_search_from_args(args_for(fixture["extension_plan_path"], fixture["output_root"], resume=True))
            uninterrupted_root = fixture["root"] / "results/uninterrupted"
            uninterrupted = beam_search.run_search_from_args(args_for(fixture["extension_plan_path"], uninterrupted_root, resume=False))
        finally:
            beam_search.validate_plan = original_validate
        resumed_state = json.loads((fixture["output_root"] / "search_state.json").read_text(encoding="utf-8"))
        uninterrupted_state = json.loads((uninterrupted_root / "search_state.json").read_text(encoding="utf-8"))
        assert resumed["status"] == uninterrupted["status"]
        assert resumed["best_completed_search_route"] == uninterrupted["best_completed_search_route"]
        assert resumed.get("completed_routes") == uninterrupted.get("completed_routes")
        assert retained_signature(resumed_state) == retained_signature(uninterrupted_state)
        assert frontier_content_signature(fixture["output_root"], resumed_state) == frontier_content_signature(uninterrupted_root, uninterrupted_state)
        assert resumed_state["plan_sha256"] == sha256_file(fixture["extension_plan_path"])
        assert source_state_hash == fixture["plan"]["resume_extension_contract"]["source_search_state_sha256"]
        receipt = json.loads((fixture["root"] / "results/fixture_receipt.json").read_text(encoding="utf-8"))
        assert receipt["status"] == "validated_not_executed"
        assert receipt["source_search_state_sha256"] == source_state_hash
        assert receipt["source_search_state_sha256_after_validation"] == source_state_hash
    print("beam_search_v115_actual_runner_resume_extension_smoke_test ok")


if __name__ == "__main__":
    main()
