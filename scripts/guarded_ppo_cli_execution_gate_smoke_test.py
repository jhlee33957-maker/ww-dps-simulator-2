from __future__ import annotations

import contextlib
import hashlib
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

    canonical_before = _snapshot_canonical_outputs()
    _assert_rejected(parse_and_validate_guarded_ppo_args, [], "No mode selected")
    _assert_rejected(parse_and_validate_guarded_ppo_args, ["--resume"], "--resume requires --execute")

    dry_run_args = parse_and_validate_guarded_ppo_args(["--dry-run-plan", "--plan", str(PLAN)])
    result = run_dry_run_plan(dry_run_args.plan_path, output_root=dry_run_args.output_root)
    assert result["status"] == "dry_run_plan_ok"
    assert _snapshot_canonical_outputs() == canonical_before

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
    assert _snapshot_canonical_outputs() == canonical_before
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


def _snapshot_canonical_outputs() -> dict[str, tuple[str, int]]:
    roots = [ROOT / "models" / "guarded_ppo_v109", ROOT / "results" / "guarded_ppo_v109"]
    snapshot: dict[str, tuple[str, int]] = {}
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            snapshot[path.relative_to(ROOT).as_posix()] = (_sha256(path), path.stat().st_mtime_ns)
    return snapshot


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    main()
