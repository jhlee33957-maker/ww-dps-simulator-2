from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "direct_action_data_patch_manifest_v61.json"
SOURCE_MANIFEST_PATH = ROOT / "data" / "source" / "direct_action_data_patch_manifest_v61.json"
APPLY_SCRIPT_PATH = ROOT / "scripts" / "apply_direct_action_data_v61.py"


def load_apply_module():
    spec = importlib.util.spec_from_file_location("apply_direct_action_data_v61", APPLY_SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    assert MANIFEST_PATH.exists()
    assert SOURCE_MANIFEST_PATH.exists()

    manifest_bytes = MANIFEST_PATH.read_bytes()
    source_manifest_bytes = SOURCE_MANIFEST_PATH.read_bytes()
    original_manifest_bytes = bytes(manifest_bytes)
    original_source_manifest_bytes = bytes(source_manifest_bytes)

    assert not manifest_bytes.startswith(b"\xef\xbb\xbf")
    assert not source_manifest_bytes.startswith(b"\xef\xbb\xbf")
    assert manifest_bytes == source_manifest_bytes
    json.loads(manifest_bytes.decode("utf-8"))
    json.loads(source_manifest_bytes.decode("utf-8"))
    apply_module = load_apply_module()
    expected_manifest_sha256 = apply_module.EXPECTED_MANIFEST_SHA256
    actual_hash = hashlib.sha256(manifest_bytes).hexdigest()
    assert actual_hash == expected_manifest_sha256

    result = subprocess.run(
        [sys.executable, str(APPLY_SCRIPT_PATH), "--check", "--fail-on-diff"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert '"field_level_change_count": 0' in result.stdout

    with tempfile.TemporaryDirectory() as tmpdir:
        corrupt_manifest = Path(tmpdir) / "direct_action_data_patch_manifest_v61.json"
        corrupt_manifest.write_bytes(manifest_bytes[:-1] + (b"0" if manifest_bytes[-1:] != b"0" else b"1"))

        apply_module.MANIFEST_PATH = corrupt_manifest
        try:
            apply_module.apply_manifest()
        except apply_module.AlignmentError as exc:
            assert "manifest hash mismatch" in str(exc)
        else:
            raise AssertionError("corrupt temporary manifest did not fail hash guard")

    assert MANIFEST_PATH.read_bytes() == original_manifest_bytes
    assert SOURCE_MANIFEST_PATH.read_bytes() == original_source_manifest_bytes
    print("direct_action_manifest_hash_guard_smoke_test ok")


if __name__ == "__main__":
    main()
