from __future__ import annotations

import tempfile
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.beam_search_destination_bucket_test_utils import STAGE, make_node, retained_ids
from search.beam_search import DestinationBucketAccumulator, _select_retained_batch


def main() -> None:
    stage = STAGE | {"beam_width": 64, "global_damage_quota": 32, "diversity_retention_quota": 32, "destination_accumulator_unique_fingerprint_bound": 16}
    nodes = [
        make_node(index + 1, damage=float((index * 37) % 251), key=f"K{index % 19}", fingerprint=f"fp-{index % 91}")
        for index in range(180)
    ]
    expected = retained_ids(_select_retained_batch(nodes, stage)["retained"])
    with tempfile.TemporaryDirectory(prefix="beam-acc-spill-") as temp_dir:
        root = Path(temp_dir)
        accumulator = DestinationBucketAccumulator(bucket_index=8, stage=stage, spill_root=root, output_root=root)
        for node in nodes:
            accumulator.add(node)
        assert accumulator.spill_chunks
        assert retained_ids(accumulator.retained_nodes()) == expected
        manifest = accumulator.manifest(force_spill=True, retained_view_count=len(expected))
        restored = DestinationBucketAccumulator.from_json(manifest, stage=stage, spill_root=root, output_root=root)
        assert retained_ids(restored.retained_nodes()) == expected
        for chunk in manifest["spill_chunks"]:
            assert Path(chunk["path"]).exists()
            assert chunk["sha256"]
    print("beam_search_destination_accumulator_spill_smoke_test ok")


if __name__ == "__main__":
    main()
