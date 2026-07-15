from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mcts_v117_test_utils import directory_digest, plan_and_stage
from search.mcts_search import MCTSSearch


def _resume(plan, stage, root: Path):
    return MCTSSearch(
        plan=plan,
        stage=stage,
        output_root=root,
        max_simulations=30,
        allow_test_output_root=True,
    ).run(resume=True)


def main() -> None:
    plan, stage = plan_and_stage(simulations=30, combat_duration=4.0, checkpoint_interval=10)
    with tempfile.TemporaryDirectory(prefix="mcts-previous-fallback-") as tmp:
        temporary = Path(tmp)
        full = MCTSSearch(
            plan=plan, stage=stage, output_root=temporary / "full", allow_test_output_root=True
        ).run()
        base = temporary / "base"
        partial = MCTSSearch(
            plan=plan,
            stage=stage,
            output_root=base,
            max_simulations=20,
            allow_test_output_root=True,
        ).run()
        assert partial["simulations_completed"] == 20
        checkpoint = base / "checkpoint"
        latest = json.loads((checkpoint / "latest_manifest.json").read_text(encoding="utf-8"))
        previous = json.loads((checkpoint / "previous_manifest.json").read_text(encoding="utf-8"))
        assert latest["simulation_count"] == 20 and previous["simulation_count"] == 10

        variants = ("missing_manifest", "truncated_manifest", "missing_generation_file")
        for kind in variants:
            target = temporary / kind
            shutil.copytree(base, target)
            target_checkpoint = target / "checkpoint"
            manifest_path = target_checkpoint / "latest_manifest.json"
            if kind == "missing_manifest":
                manifest_path.unlink()
            elif kind == "truncated_manifest":
                manifest_path.write_text('{"schema_version":', encoding="utf-8")
            else:
                target_latest = json.loads(manifest_path.read_text(encoding="utf-8"))
                (target_checkpoint / target_latest["files"]["tree"]["path"]).unlink()
            resumed = _resume(plan, stage, target)
            assert resumed["resume_checkpoint_source"] == "previous", kind
            assert resumed["resume_checkpoint_fallback_reason"], kind
            assert resumed["logical_result_sha256"] == full["logical_result_sha256"], kind
            assert resumed["rng_final_state_sha256"] == full["rng_final_state_sha256"], kind
            assert resumed["mast_logical_sha256"] == full["mast_logical_sha256"], kind

        invalid = temporary / "both_invalid"
        shutil.copytree(base, invalid)
        (invalid / "checkpoint" / "latest_manifest.json").unlink()
        (invalid / "checkpoint" / "previous_manifest.json").unlink()
        before = directory_digest(invalid)
        try:
            _resume(plan, stage, invalid)
        except ValueError as error:
            assert "previous checkpoint is unusable" in str(error)
        else:
            raise AssertionError("resume accepted two invalid checkpoint generations")
        assert directory_digest(invalid) == before

    print(
        "mcts_previous_checkpoint_fallback_smoke_test ok "
        "variants=3 source=previous both_invalid_no_mutation=true"
    )


if __name__ == "__main__":
    main()
