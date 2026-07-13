from __future__ import annotations

from typing import Iterable

from search.beam_search import DestinationBucketAccumulator, _select_retained_batch
from search.beam_state import BeamNode, lineage_tie_sha256


STAGE = {
    "stage_id": "unit",
    "combat_duration": 30.0,
    "time_bucket_width": 0.5,
    "beam_width": 1024,
    "global_damage_quota": 512,
    "diversity_retention_quota": 512,
    "max_states_per_diversity_key": 8,
    "maximum_expansions": 1,
    "destination_accumulator_unique_fingerprint_bound": 4096,
}


def make_node(node_id: int, *, damage: float, key: str, fingerprint: str | None = None, parent_id: int | None = 0) -> BeamNode:
    action_id = f"unit_action_{node_id}"
    return BeamNode(
        node_id=node_id,
        parent_id=parent_id,
        selected_action_id=action_id,
        resolved_action_id=action_id,
        action_count=1,
        total_damage=float(damage),
        combat_time=1.0,
        current_time=1.0,
        state_payload={"schema_version": "unit", "state": {}, "combat_duration": 30.0},
        future_fingerprint=fingerprint or f"fp-{node_id}",
        diversity_key=key,
        complete=False,
        lineage_tie_key=lineage_tie_sha256("unit-root", action_id, action_id),
        payload_size_bytes=256,
    )


def counterexample_nodes() -> dict[str, list[BeamNode] | BeamNode]:
    node_id = 1
    global_nodes: list[BeamNode] = []
    for index in range(512):
        global_nodes.append(make_node(node_id, damage=10_000.0 - index, key="G"))
        node_id += 1
    diversity_nodes: list[BeamNode] = []
    for key_index in range(64):
        key = f"D{key_index}"
        for slot in range(8):
            diversity_nodes.append(make_node(node_id, damage=5_000.0 - key_index - (slot / 100.0), key=key))
            node_id += 1
    rare = make_node(node_id, damage=1.0, key="R")
    node_id += 1
    late_global: list[BeamNode] = []
    for index in range(8):
        late_global.append(make_node(node_id, damage=20_000.0 - index, key="D0"))
        node_id += 1
    return {"global": global_nodes, "diversity": diversity_nodes, "rare": rare, "late_global": late_global}


def retained_ids(nodes: Iterable[BeamNode]) -> list[int]:
    return [node.node_id for node in nodes]


def one_shot_ids(nodes: list[BeamNode]) -> list[int]:
    return retained_ids(_select_retained_batch(nodes, STAGE)["retained"])


def accumulator_ids(nodes: list[BeamNode]) -> list[int]:
    accumulator = DestinationBucketAccumulator(bucket_index=1, stage=STAGE)
    for node in nodes:
        accumulator.add(node)
    return retained_ids(accumulator.retained_nodes())
