from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from search.mcts_search import MCTSSearch
from scripts.mcts_v117_test_utils import directory_digest, plan_and_stage


def mutate(root: Path, kind: str) -> None:
    checkpoint = root / "checkpoint"; manifest_path = checkpoint / "latest_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if kind in {"plan", "stage"}:
        manifest["plan_sha256" if kind == "plan" else "stage_contract_sha256"] = "0" * 64
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8"); return
    key = {"tree": "tree", "snapshot_index": "snapshot_index", "rng": "rng", "mast": "mast"}.get(kind)
    if key:
        path = checkpoint / manifest["files"][key]["path"]; data = bytearray(path.read_bytes()); data[len(data)//2] ^= 1; path.write_bytes(data); return
    if kind == "snapshot_prefix":
        path = checkpoint / "snapshots.dat"; data = bytearray(path.read_bytes()); data[0] ^= 1; path.write_bytes(data); return
    raise AssertionError(kind)


def main() -> None:
    plan, stage = plan_and_stage(simulations=20, combat_duration=4.0, checkpoint_interval=10)
    with tempfile.TemporaryDirectory(prefix="mcts-corrupt-") as tmp:
        base = Path(tmp) / "base"; MCTSSearch(plan=plan, stage=stage, output_root=base, allow_test_output_root=True).run()
        for kind in ("plan", "stage", "tree", "snapshot_prefix", "snapshot_index", "rng", "mast"):
            target = Path(tmp) / kind; shutil.copytree(base, target); mutate(target, kind); before = directory_digest(target)
            try: MCTSSearch(plan=plan, stage=stage, output_root=target, allow_test_output_root=True).run(resume=True)
            except ValueError: pass
            else: raise AssertionError(f"corruption accepted: {kind}")
            assert directory_digest(target) == before, kind
    print("mcts_checkpoint_corruption_no_mutation_smoke_test ok variants=7")


if __name__ == "__main__": main()
