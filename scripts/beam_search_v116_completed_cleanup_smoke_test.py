from __future__ import annotations

import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.cleanup_completed_beam_payload_v116 import apply_cleanup, cleanup_plan, sha256_file


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build_fixture(root: Path) -> tuple[Path, Path]:
    output = root / "heavy"
    state = {
        "termination_status": "completed_search",
        "completed_buckets": list(range(240)),
        "pending_buckets": [],
        "destination_bucket_accumulators": {},
        "completed_routes": [{} for _ in range(128)],
    }
    write_json(output / "search_state.json", state)
    for name in ["best_route.json", "execution_result.json", "final_summary.json", "leaderboard.json"]:
        write_json(output / name, {"core": name})
    (output / "frontier/accumulators/a.bin").parent.mkdir(parents=True, exist_ok=True)
    (output / "frontier/accumulators/a.bin").write_bytes(b"accumulator")
    nested = output / "results/beam_search_v114_lowmem_32gb/frontier/b.bin"
    nested.parent.mkdir(parents=True, exist_ok=True)
    nested.write_bytes(b"nested")
    entries = [
        {"path": path.relative_to(output).as_posix(), "bytes": path.stat().st_size, "sha256": sha256_file(path)}
        for path in sorted(item for item in output.rglob("*") if item.is_file())
    ]
    inventory_path = root / "inventory.json"
    write_json(inventory_path, {"files": entries})
    compact = root / "results/beam_search_v114_completed_v116"
    manifest = {
        "schema_version": "beam_search_v114_completed_result_manifest_v116",
        "termination_status": "completed_search",
        "completed_search": {
            "completed_bucket_count": 240,
            "pending_buckets": [],
            "destination_bucket_accumulators": {},
            "completed_retained_route_count": 128,
        },
        "heavy_output_mutated_by_ingestion": False,
        "full_inventory": {"before_validation": {"ok": True}, "after_validation": {"ok": True}},
        "artifact_sha256": {},
        "external_inventory_artifact_path": "inventory.json",
        "external_inventory_artifact_sha256": sha256_file(inventory_path),
    }
    manifest_path = compact / "result_manifest.json"
    write_json(manifest_path, manifest)
    archive = root / "candidate.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.write(manifest_path, "results/beam_search_v114_completed_v116/result_manifest.json")
    return output, archive


def expect_failure(callable_object) -> None:
    try:
        callable_object()
    except (ValueError, FileNotFoundError):
        return
    raise AssertionError("Expected cleanup validation failure")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="beam-v116-cleanup-") as temporary:
        root = Path(temporary)
        output, archive = build_fixture(root)
        plan = cleanup_plan(project_root=root, output_root=output, candidate_archive=archive)
        assert plan["mode"] == "dry_run" and plan["cleanup_applied"] is False
        assert plan["eligible_file_count"] == 2 and plan["reclaimable_bytes"] == len(b"accumulator") + len(b"nested")
        receipt = apply_cleanup(project_root=root, output_root=output, candidate_archive=archive)
        assert receipt["deleted_file_count"] == 2
        assert not (output / "frontier/accumulators/a.bin").exists()
        for core in ["best_route.json", "execution_result.json", "final_summary.json", "leaderboard.json", "search_state.json"]:
            assert (output / core).is_file()
        repeated = apply_cleanup(project_root=root, output_root=output, candidate_archive=archive)
        assert repeated["idempotent_repeat"] is True and repeated["reclaimed_bytes"] == receipt["reclaimed_bytes"]
    with tempfile.TemporaryDirectory(prefix="beam-v116-cleanup-negative-") as temporary:
        root = Path(temporary)
        output, archive = build_fixture(root)
        state_path = output / "search_state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["termination_status"] = "expansion_budget_exhausted"
        write_json(state_path, state)
        expect_failure(lambda: cleanup_plan(project_root=root, output_root=output, candidate_archive=archive))
    with tempfile.TemporaryDirectory(prefix="beam-v116-cleanup-missing-") as temporary:
        root = Path(temporary)
        output = root / "heavy"
        output.mkdir()
        expect_failure(lambda: cleanup_plan(project_root=root, output_root=output))
    with tempfile.TemporaryDirectory(prefix="beam-v116-cleanup-hash-") as temporary:
        root = Path(temporary)
        output, archive = build_fixture(root)
        (output / "frontier/accumulators/a.bin").write_bytes(b"changed")
        expect_failure(lambda: cleanup_plan(project_root=root, output_root=output, candidate_archive=archive))
    print("beam_search_v116_completed_cleanup_smoke_test ok")


if __name__ == "__main__":
    main()
