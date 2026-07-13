from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_search import DestinationBucketAccumulator, read_json_gz, write_json_gz  # noqa: E402
from scripts.beam_search_destination_bucket_test_utils import STAGE, counterexample_nodes, one_shot_ids, retained_ids  # noqa: E402


def main() -> None:
    parts = counterexample_nodes()
    nodes = [*parts["global"], *parts["diversity"], parts["rare"], *parts["late_global"]]
    expected = one_shot_ids(nodes)
    uninterrupted = DestinationBucketAccumulator(bucket_index=3, stage=STAGE)
    for node in nodes:
        uninterrupted.add(node)
    with tempfile.TemporaryDirectory(prefix="beam-acc-resume-") as temp_dir:
        path = Path(temp_dir) / "accumulator.json.gz"
        interrupted = DestinationBucketAccumulator(bucket_index=3, stage=STAGE)
        for node in nodes[:700]:
            interrupted.add(node)
        sha = write_json_gz(path, interrupted.to_json())
        restored = DestinationBucketAccumulator.from_json(read_json_gz(path, sha), stage=STAGE)
        for node in nodes[700:]:
            restored.add(node)
    assert restored.to_json()["nodes"] == uninterrupted.to_json()["nodes"]
    assert restored.metrics() == uninterrupted.metrics()
    assert retained_ids(restored.retained_nodes()) == expected
    route_store = {0: {"node_id": 0, "parent_id": None}}
    for node in restored.best_by_fingerprint.values():
        route_store[node.node_id] = {
            "node_id": node.node_id,
            "parent_id": node.parent_id,
            "selected_action_id": node.selected_action_id,
            "resolved_action_id": node.resolved_action_id,
        }
    retained_ancestors = {node.node_id for node in restored.retained_nodes()}
    retained_ancestors.add(0)
    assert retained_ancestors <= set(route_store)
    json.dumps(restored.to_json(), sort_keys=True)
    print("beam_search_destination_bucket_resume_equivalence_smoke_test ok")


if __name__ == "__main__":
    main()
