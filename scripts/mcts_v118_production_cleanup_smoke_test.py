from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from scripts.cleanup_mcts_v118_production_payloads_v119 import ELIGIBLE, EXPECTED_RECLAIMABLE, REQUIRED_CORE, apply_cleanup_plan, validate_seed_cleanup_preconditions


def expect_failure(callable_, text: str) -> None:
    try: callable_()
    except ValueError as error: assert text in str(error), str(error)
    else: raise AssertionError("expected cleanup safety failure")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(root: Path) -> tuple[Path, dict]:
    raw = root / "raw"; (raw / "checkpoint").mkdir(parents=True)
    for relative in REQUIRED_CORE:
        path = raw / relative; path.parent.mkdir(parents=True, exist_ok=True)
        if relative.endswith("latest_manifest.json"):
            path.write_text(json.dumps({"simulation_count": 50000, "node_count": 50001}), encoding="utf-8")
        elif relative.endswith("previous_manifest.json"):
            path.write_text(json.dumps({"simulation_count": 49000, "node_count": 49001}), encoding="utf-8")
        else: path.write_text("{}", encoding="utf-8")
    sizes = [5_000_000, 5_000_000, 100, 100, EXPECTED_RECLAIMABLE[118001] - 10_000_200]
    for relative, size in zip(ELIGIBLE, sizes):
        path = raw / relative; path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as file: file.truncate(size)
    files = [
        {"path": path.relative_to(raw).as_posix(), "bytes": path.stat().st_size, "sha256": digest(path)}
        for path in sorted(raw.rglob("*")) if path.is_file()
    ]
    return raw, {"files": files}


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="mcts-v119-cleanup-") as temporary:
        raw, inventory = fixture(Path(temporary))
        checked = validate_seed_cleanup_preconditions(raw, 118001, inventory)
        assert len(checked["eligible"]) == 5 and checked["reviewed_reclaimable_bytes"] == 10078176
        plan = {
            "schema_version": "mcts_v118_production_cleanup_plan_v119", "mode": "dry_run",
            "candidate_archive": {"valid": False},
            "eligible_files": [dict(row, raw_root=raw.as_posix(), seed=118001) for row in checked["eligible"]],
            "cleanup_applied": False,
        }
        assert plan["mode"] == "dry_run" and not plan["cleanup_applied"]
        expect_failure(lambda: apply_cleanup_plan(plan, externally_verified=True), "valid candidate")
        plan["candidate_archive"] = {"valid": True}
        expect_failure(lambda: apply_cleanup_plan(plan, externally_verified=False), "externally verified")
        changed = raw / ELIGIBLE[0]; changed.write_bytes(b"changed")
        expect_failure(lambda: apply_cleanup_plan(plan, externally_verified=True), "changed after validation")
        raw, inventory = fixture(Path(temporary) / "second")
        checked = validate_seed_cleanup_preconditions(raw, 118001, inventory)
        plan["eligible_files"] = [dict(row, raw_root=raw.as_posix(), seed=118001) for row in checked["eligible"]]
        result = apply_cleanup_plan(plan, externally_verified=True)
        assert result["deleted_file_count"] == 5 and all(not (raw / relative).exists() for relative in ELIGIBLE)
        repeat = apply_cleanup_plan(plan, externally_verified=True)
        assert repeat["deleted_file_count"] == 0 and repeat["already_absent_file_count"] == 5
        assert all((raw / relative).is_file() for relative in REQUIRED_CORE)
        incomplete, inv = fixture(Path(temporary) / "incomplete")
        (incomplete / "execution_result.json").unlink()
        expect_failure(lambda: validate_seed_cleanup_preconditions(incomplete, 118001, inv), "missing a non-eligible")
        mismatch, inv = fixture(Path(temporary) / "mismatch")
        (mismatch / "best_route.json").write_text("changed", encoding="utf-8")
        expect_failure(lambda: validate_seed_cleanup_preconditions(mismatch, 118001, inv), "inventory mismatch")
    print("mcts_v118_production_cleanup_smoke_test ok default=dry_run allowlist=15 apply=fixture_only idempotent=true")


if __name__ == "__main__": main()
