from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from search.mcts_completed_result import (
    COMPACT_RESULT, EXPECTED_FILE_COUNT, EXPECTED_TOTAL_BYTES, INVENTORY_ENTRY_DIGEST,
    REVIEW_ARCHIVE, REVIEW_INVENTORY_SHA256, load_compact_review_inventory,
)
from scripts.mcts_v117_calibration_cleanup_smoke_test import run_fixture_cleanup_safety


def _expect_failure(callable_, text: str) -> None:
    try: callable_()
    except ValueError as error: assert text in str(error), str(error)
    else: raise AssertionError(f"expected ValueError containing {text!r}")


def _copy_compact(target: Path) -> Path:
    shutil.copytree(ROOT / COMPACT_RESULT, target / COMPACT_RESULT)
    return target


def main() -> None:
    review = ROOT / REVIEW_ARCHIVE
    hidden = review.with_name(review.name + ".self-contained-test-hidden")
    if hidden.exists(): raise AssertionError(f"stale hidden review archive: {hidden}")
    moved = review.is_file()
    if moved: os.replace(review, hidden)
    try:
        inventory = load_compact_review_inventory(ROOT)
        assert inventory["file_count"] == EXPECTED_FILE_COUNT == 111
        assert inventory["total_bytes"] == EXPECTED_TOTAL_BYTES == 38944560
        assert inventory["reviewed_inventory_file_sha256"] == REVIEW_INVENTORY_SHA256
        assert inventory["normalized_entry_digest_sha256"] == INVENTORY_ENTRY_DIGEST
        fixture = run_fixture_cleanup_safety()
        assert fixture["apply_deleted_files"] == fixture["repeat_already_absent"] == 5

        with tempfile.TemporaryDirectory(prefix="mcts-compact-self-contained-") as tmp:
            temporary = Path(tmp)
            content_tamper = _copy_compact(temporary / "content")
            inventory_path = content_tamper / COMPACT_RESULT / "full_result_inventory.json"
            payload = json.loads(inventory_path.read_text(encoding="utf-8"))
            payload["files"][0]["bytes"] += 1
            inventory_path.write_text(json.dumps(payload), encoding="utf-8")
            manifest_path = content_tamper / COMPACT_RESULT / "result_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["artifact_sha256"]["full_result_inventory.json"] = hashlib.sha256(inventory_path.read_bytes()).hexdigest()
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            _expect_failure(lambda: load_compact_review_inventory(content_tamper), "byte count mismatch")

            hash_tamper = _copy_compact(temporary / "manifest_hash")
            manifest_path = hash_tamper / COMPACT_RESULT / "result_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["artifact_sha256"]["full_result_inventory.json"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            _expect_failure(lambda: load_compact_review_inventory(hash_tamper), "artifact SHA mismatch")
    finally:
        if moved: os.replace(hidden, review)
    assert review.is_file() if moved else not review.exists()
    print("mcts_v118_compact_inventory_self_contained_smoke_test ok "
          "review_zip_access=false inventory_files=111 fixture_apply=true tampering_rejected=true")


if __name__ == "__main__": main()
