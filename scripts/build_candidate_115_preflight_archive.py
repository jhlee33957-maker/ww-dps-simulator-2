from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT.parent / "ww-dps-simulator-2-115-preflight.zip"
EXACT_FILES = {
    "PROJECT_PROGRESS_STATE.json",
    "direct_action_data_patch_manifest_v61.json",
    "data/beam_search_plan_v111.json",
    "data/beam_search_plan_v114_32gb.json",
    "data/beam_search_plan_v115_32gb_resume_v114.json",
    "models/guarded_ppo_v109/bc_conservative_seed_11/step_000090000.zip",
    "models/maskable_ppo_bc_v105.zip",
    "models/maskable_ppo_candidate_after_bc_v105.zip",
    "results/manual_model_comparison_v114.json",
    "results/transition_contract_v114_model_reevaluation/evaluations/guarded_ppo_v109__bc_conservative_seed_11__step_000090000.zip.json",
    "results/beam_search_v114_3m_checkpoint_review_v115.json",
    "results/beam_search_v114_3m_reviewed_file_inventory_v115.json",
    "results/beam_search_v114_3m_resume_extension_v115_receipt.json",
    "reports/beam_search_v114_3m_checkpoint_review_v115.md",
}
PREFIXES = ("search/", "simulator/", "characters/", "rl/", "data/", "scripts/beam_search_v115_", "scripts/beam_search_v114_", "scripts/project_progress_beam_v115_", "scripts/validate_beam_v114_3m_resume_extension_v115.py")
EXCLUDED_PREFIXES = ("data/extracted/", "results/beam_search_v114_lowmem_32gb/")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_archive(output: Path) -> dict[str, object]:
    output = output.resolve()
    included: list[tuple[str, bytes]] = []
    for path in sorted(item for item in ROOT.rglob("*") if item.is_file()):
        relative = path.relative_to(ROOT).as_posix()
        if any(relative.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
            continue
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo", ".zip"} and relative not in EXACT_FILES:
            continue
        if relative in EXACT_FILES or any(relative.startswith(prefix) for prefix in PREFIXES):
            included.append((relative, path.read_bytes()))
    missing = sorted(EXACT_FILES - {name for name, _ in included})
    if missing:
        raise ValueError(f"Missing required preflight files: {missing}")
    manifest = {
        "schema_version": "beam_search_v115_compact_preflight_archive_manifest",
        "heavy_checkpoint_included": False,
        "entries": [
            {"path": name, "bytes": len(data), "sha256": sha256_bytes(data)}
            for name, data in included
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in included:
            archive.writestr(name, data)
        archive.writestr("PREFLIGHT_MANIFEST.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return {
        "archive_path": output.as_posix(),
        "archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "entry_count": len(included) + 1,
        "cache_entry_count": 0,
        "heavy_checkpoint_included": False,
        "uncompressed_bytes": sum(len(data) for _, data in included),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(build_archive(args.output), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
