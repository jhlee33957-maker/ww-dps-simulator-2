from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.beam_search_v115_resume_test_utils import build_resume_fixture, tree_snapshot, write_json
from search.beam_search import BeamSearchRunner


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="beam-v115-nomutate-") as temp_dir:
        base = Path(temp_dir) / "base"
        build_resume_fixture(base)
        mutations = ["state_sha", "source_plan", "frontier", "output_root", "stage", "data_hash", "expansions", "inventory"]
        for name in mutations:
            case = Path(temp_dir) / name
            shutil.copytree(base, case)
            plan_path = case / "data/extension_plan.json"
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            output = case / "results/fixture_checkpoint"
            if name == "state_sha":
                plan["resume_extension_contract"]["source_search_state_sha256"] = "0" * 64
            elif name == "source_plan":
                (case / "data/source_plan.json").write_text("mutated", encoding="utf-8")
            elif name == "frontier":
                target = next((output / "frontier").rglob("*.gz")); target.write_bytes(target.read_bytes() + b"x")
            elif name == "output_root":
                plan["output_contract"]["canonical_output_root"] = "results/other"
            elif name == "stage":
                plan["resume_extension_contract"]["source_stage_id"] = "wrong_stage"
            elif name == "data_hash":
                first = next(iter(plan["data_contract_hashes"])); plan["data_contract_hashes"][first] = "0" * 64
            elif name == "expansions":
                plan["resume_extension_contract"]["source_checkpoint_expansions"] += 1
            elif name == "inventory":
                reviewed = case / "results/reviewed_inventory.json"; reviewed.write_text(reviewed.read_text(encoding="utf-8") + " ", encoding="utf-8")
            write_json(plan_path, plan)
            before = tree_snapshot(output)
            try:
                BeamSearchRunner(plan=plan, stage=plan["stages"][0], plan_path=plan_path, output_root=output).run(resume=True)
            except ValueError:
                pass
            else:
                raise AssertionError(f"mutation unexpectedly resumed: {name}")
            assert tree_snapshot(output) == before, name
            assert not (case / "results/fixture_receipt.json").exists(), name
    print("beam_search_v115_resume_preflight_no_mutation_smoke_test ok")


if __name__ == "__main__":
    main()
