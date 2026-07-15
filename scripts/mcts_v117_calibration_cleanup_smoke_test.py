from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from scripts.cleanup_mcts_v117_calibration_payload_v118 import (
    REQUIRED_CORE_FILES,
    apply_cleanup,
    apply_validated_cleanup_plan,
    build_validated_cleanup_plan,
    cleanup_plan,
    validate_cleanup_preconditions,
)
from scripts.mcts_v117_test_utils import directory_digest
from search.mcts_completed_result import COMPACT_RESULT, load_compact_review_inventory


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expect_failure(callable_, text: str) -> None:
    try: callable_()
    except ValueError as error: assert text in str(error), str(error)
    else: raise AssertionError(f"expected ValueError containing {text!r}")


def _fixture_inventory(output: Path) -> dict:
    files = []
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        files.append({"path": path.relative_to(output).as_posix(), "bytes": path.stat().st_size,
                      "sha256": _sha(path)})
    return {"file_count": len(files), "total_bytes": sum(item["bytes"] for item in files),
            "normalized_entry_digest_sha256": hashlib.sha256(b"fixture-cleanup-inventory").hexdigest(),
            "files": files}


def _make_completed_fixture(root: Path) -> tuple[Path, dict]:
    output = root / "raw_fixture"
    for relative in REQUIRED_CORE_FILES:
        path = output / relative; path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "checkpoint/latest_manifest.json":
            payload = {"simulation_count": 20000, "node_count": 20001}
        elif relative == "checkpoint/previous_manifest.json":
            payload = {"simulation_count": 19000, "node_count": 19001}
        else:
            payload = {"fixture_core": relative, "preserved": True}
        path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    checkpoint = output / "checkpoint"
    for generation in (18000, 19000, 20000):
        for prefix, suffix in (("tree", ".npz"), ("mast", ".npz"), ("rng", ".json"),
                               ("completed", ".json"), ("snapshot_index", ".json")):
            (checkpoint / f"{prefix}_{generation:08d}{suffix}").write_bytes(
                f"fixture:{prefix}:{generation}".encode()
            )
    return output, _fixture_inventory(output)


def run_fixture_cleanup_safety() -> dict:
    with tempfile.TemporaryDirectory(prefix="mcts-cleanup-fixture-") as tmp:
        temporary = Path(tmp); output, inventory = _make_completed_fixture(temporary)
        preconditions = validate_cleanup_preconditions(
            output_root=output, inventory=inventory, calibration_complete=True,
            winning_route_replay_valid=True,
        )
        dry = build_validated_cleanup_plan(
            output_root=output, preconditions=preconditions,
            candidate_archive={"built": False, "path": "missing.zip", "sha256": None},
            compact_manifest_sha256="1" * 64,
        )
        assert dry["mode"] == "dry_run" and dry["reclaimable_file_count"] == 5
        assert dry["retained_generations"] == [19000, 20000] and not dry["cleanup_applied"]
        _expect_failure(lambda: apply_validated_cleanup_plan(dry), "must exist")
        _expect_failure(lambda: validate_cleanup_preconditions(
            output_root=output, inventory=inventory, calibration_complete=False,
            winning_route_replay_valid=True), "completed 20k")
        _expect_failure(lambda: validate_cleanup_preconditions(
            output_root=output, inventory=inventory, calibration_complete=True,
            winning_route_replay_valid=False), "winning-route replay")

        core = output / REQUIRED_CORE_FILES[0]; original = core.read_bytes(); core.write_bytes(original + b"tamper")
        _expect_failure(lambda: validate_cleanup_preconditions(
            output_root=output, inventory=inventory, calibration_complete=True,
            winning_route_replay_valid=True), "inventory mismatch")
        core.write_bytes(original)

        compact_project = temporary / "compact_project"
        shutil.copytree(ROOT / COMPACT_RESULT, compact_project / COMPACT_RESULT)
        manifest_path = compact_project / COMPACT_RESULT / "result_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")); manifest["ingestion_candidate"] = 999
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        _expect_failure(lambda: load_compact_review_inventory(compact_project), "ingestion_candidate")

        core_before = {relative: _sha(output / relative) for relative in REQUIRED_CORE_FILES}
        approved = dict(dry); approved["candidate_archive"] = {"built": True, "path": "fixture.zip", "sha256": "2" * 64}
        applied = apply_validated_cleanup_plan(approved)
        assert applied["deleted_file_count"] == 5 and applied["already_absent_file_count"] == 0
        assert all(not (output / "checkpoint" / f"{prefix}_00018000{suffix}").exists()
                   for prefix, suffix in (("tree", ".npz"), ("mast", ".npz"), ("rng", ".json"),
                                          ("completed", ".json"), ("snapshot_index", ".json")))
        assert all(_sha(output / relative) == digest for relative, digest in core_before.items())
        repeated = apply_validated_cleanup_plan(approved)
        assert repeated["deleted_file_count"] == 0 and repeated["already_absent_file_count"] == 5
        return {"fixture_reclaimable_files": 5, "apply_deleted_files": 5,
                "repeat_already_absent": 5, "core_files_preserved": len(core_before)}


def main() -> None:
    raw = ROOT / "results/mcts_v117_32gb/calibration_20k_seed_117001"
    integration = None
    if raw.is_dir():
        before = directory_digest(raw)
        with tempfile.TemporaryDirectory(prefix="mcts-cleanup-integration-") as tmp:
            missing = Path(tmp) / "missing-118.zip"
            integration = cleanup_plan(project_root=ROOT, output_root=raw, candidate_archive=missing)
            assert integration["reclaimable_file_count"] == 90 and integration["reclaimable_bytes"] == 29939946
            assert integration["retained_generations"] == [19000, 20000]
            validated = integration["full_inventory_validated"]
            assert validated["file_count"] == 111 and validated["total_bytes"] == 38944560
            assert validated["validated_existing_file_count"] == 111
            _expect_failure(lambda: apply_cleanup(project_root=ROOT, output_root=raw,
                                                  candidate_archive=missing), "must exist")
        assert directory_digest(raw) == before
    fixture = run_fixture_cleanup_safety()
    print("mcts_v117_calibration_cleanup_smoke_test ok " + json.dumps(
        {"raw_integration": integration is not None, "raw_files": 111 if integration else None,
         "raw_reclaimable_files": 90 if integration else None,
         "raw_reclaimable_bytes": 29939946 if integration else None, **fixture}, sort_keys=True))


if __name__ == "__main__": main()
