from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mcts_v117_test_utils import PLAN_PATH, directory_digest, plan_and_stage
from search.mcts_plan import load_mcts_plan
from search.mcts_search import MCTSSearch
from search.run_mcts import parser


def _expect_value_error(callable_, contains: str) -> None:
    try:
        callable_()
    except ValueError as error:
        assert contains in str(error), str(error)
    else:
        raise AssertionError(f"expected ValueError containing {contains!r}")


def main() -> None:
    production_plan = load_mcts_plan(PLAN_PATH)
    production_stage = production_plan["stages"][0]
    canonical = ROOT / production_stage["canonical_output_root"]
    canonical_existed = canonical.is_dir()
    canonical_before = directory_digest(canonical) if canonical_existed else None
    assert "--force" not in parser().format_help()

    with tempfile.TemporaryDirectory(prefix="mcts-output-isolation-") as tmp:
        temporary = Path(tmp)
        arbitrary = temporary / "arbitrary_production"
        _expect_value_error(
            lambda: MCTSSearch(
                plan=production_plan,
                stage=production_stage,
                output_root=arbitrary,
                max_simulations=1,
            ),
            "canonical plan output root",
        )
        assert not arbitrary.exists()

        cli_root = temporary / "cli_arbitrary"
        child = subprocess.run(
            [
                sys.executable,
                str(ROOT / "search" / "run_mcts.py"),
                "--plan",
                str(PLAN_PATH),
                "--execute",
                "--max-simulations",
                "1",
                "--output-root",
                str(cli_root),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
        assert child.returncode != 0
        assert "canonical plan output root" in child.stderr
        assert not cli_root.exists()

        plan, stage = plan_and_stage(simulations=2, combat_duration=1.0, checkpoint_interval=1)
        fixture_root = temporary / "fixture_canonical"
        stage["canonical_output_root"] = str(fixture_root)
        first = MCTSSearch(plan=plan, stage=stage, output_root=fixture_root).run()
        assert first["simulations_completed"] == 2
        before = directory_digest(fixture_root)
        _expect_value_error(
            lambda: MCTSSearch(plan=plan, stage=stage, output_root=fixture_root).run(),
            "refuses a nonempty output root",
        )
        assert directory_digest(fixture_root) == before

        stale = temporary / "stale_snapshots"
        (stale / "checkpoint").mkdir(parents=True)
        snapshots = stale / "checkpoint" / "snapshots.dat"
        snapshots.write_bytes(b"old-snapshot-prefix")
        stale_stage = dict(stage)
        stale_stage["canonical_output_root"] = str(stale)
        stale_before = snapshots.read_bytes()
        _expect_value_error(
            lambda: MCTSSearch(plan=plan, stage=stale_stage, output_root=stale).run(),
            "refuses a nonempty output root",
        )
        assert snapshots.read_bytes() == stale_before

        empty_resume = temporary / "empty_resume"
        empty_resume.mkdir()
        resume_stage = dict(stage)
        resume_stage["canonical_output_root"] = str(empty_resume)
        before_resume = directory_digest(empty_resume)
        _expect_value_error(
            lambda: MCTSSearch(plan=plan, stage=resume_stage, output_root=empty_resume).run(resume=True),
            "previous checkpoint is unusable",
        )
        assert directory_digest(empty_resume) == before_resume

    if canonical_existed: assert directory_digest(canonical) == canonical_before
    else: assert not canonical.exists()
    print(
        "mcts_output_root_isolation_smoke_test ok arbitrary_rejected=true "
        "nonempty_fresh_rejected=true resume_requires_checkpoint=true stale_snapshot_unchanged=true"
    )


if __name__ == "__main__":
    main()
