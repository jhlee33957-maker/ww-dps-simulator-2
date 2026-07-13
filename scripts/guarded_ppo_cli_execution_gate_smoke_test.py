from __future__ import annotations

import contextlib
import io
import tempfile
import time
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PLAN = ROOT / "data" / "guarded_ppo_experiment_plan_v109.json"


def main() -> None:
    started = time.perf_counter()
    from rl.guarded_ppo import parse_and_validate_guarded_ppo_args, run_dry_run_plan

    _assert_rejected(parse_and_validate_guarded_ppo_args, [], "No mode selected")
    _assert_rejected(parse_and_validate_guarded_ppo_args, ["--resume"], "--resume requires --execute")

    dry_run_args = parse_and_validate_guarded_ppo_args(["--dry-run-plan", "--plan", str(PLAN)])
    result = run_dry_run_plan(dry_run_args.plan_path, output_root=dry_run_args.output_root)
    assert result["status"] == "dry_run_plan_ok"
    assert result["canonical_models_created"] is False
    assert result["canonical_results_created"] is False
    _assert_no_canonical_outputs()

    with tempfile.TemporaryDirectory(prefix="guarded-cli-gate-") as temp_dir:
        _assert_rejected(
            parse_and_validate_guarded_ppo_args,
            ["--execute", "--only-branch", "missing", "--output-root", temp_dir],
            "Unknown branch",
        )

    with tempfile.TemporaryDirectory(prefix="guarded-cli-gate-") as temp_dir:
        _assert_rejected(
            parse_and_validate_guarded_ppo_args,
            ["--execute", "--max-chunks", "0", "--output-root", temp_dir],
            "--max-chunks must be positive",
        )

    _assert_rejected(
        parse_and_validate_guarded_ppo_args,
        ["--execute", "--smoke-run", "--output-root", str(ROOT)],
        "--smoke-run cannot target",
    )
    _assert_no_canonical_outputs()
    elapsed = time.perf_counter() - started
    print(f"guarded_ppo_cli_execution_gate_smoke_test ok ({elapsed:.3f}s)")


def _assert_rejected(callable_object, args: list[str], expected: str) -> None:
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        try:
            callable_object(args)
        except SystemExit as exc:
            assert exc.code != 0
            assert expected in stderr.getvalue()
            return
    raise AssertionError(f"CLI args unexpectedly accepted: {args}")


def _assert_no_canonical_outputs() -> None:
    assert not (ROOT / "models" / "guarded_ppo_v109").exists()
    assert not (ROOT / "results" / "guarded_ppo_v109").exists()


if __name__ == "__main__":
    main()
