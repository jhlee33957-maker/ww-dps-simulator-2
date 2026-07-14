from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.beam_search_lowmem_workspace_builder_smoke_test import fixture
from scripts.build_lowmem_beam_workspace import IMMUTABLE_HASHES, SCHEMA, build_workspace, sha256_file


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        source = base / "source"
        source.mkdir()
        fixture(source)
        output = base / "output"
        result = build_workspace(source, output, apply=True)
        manifest_path = output / "LOWMEM_WORKSPACE_MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest == result["manifest"]
        assert manifest["schema_version"] == SCHEMA
        assert manifest["verified_immutable_artifact_hashes"] == IMMUTABLE_HASHES
        assert "generated_at" not in json.dumps(manifest)
        for entry in manifest["included_files"]:
            assert sha256_file(output / entry["path"]) == entry["sha256"]
        excluded = {entry["path"]: entry for entry in manifest["excluded_files"]}
        assert excluded["models/guarded_ppo_v109/checkpoint_1.zip"]["sha256"]
        assert manifest["global_optimum_claimed"] is False
    print("beam_search_lowmem_workspace_manifest_smoke_test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
