from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any

import numpy as np


SENTINEL = -1
ACTION_COUNT = 25


def allowed_children(visits: int, legal_action_count: int, *, coefficient: float = 2.0, exponent: float = 0.5) -> int:
    return min(int(legal_action_count), max(1, int(math.ceil(coefficient * (max(int(visits), 0) ** exponent)))))


def uct_score(parent_visits: int, child_visits: int, child_value_sum: float) -> float:
    if child_visits <= 0:
        return math.inf
    return child_value_sum / child_visits + math.sqrt(2.0) * math.sqrt(math.log(max(parent_visits, 1)) / child_visits)


def deterministic_action_rank(seed: int, fingerprint: str, action_id: str) -> str:
    return hashlib.sha256(f"{int(seed)}\0{fingerprint}\0{action_id}".encode("utf-8")).hexdigest()


class MCTSTree:
    def __init__(self, max_nodes: int) -> None:
        self.max_nodes = int(max_nodes)
        self.node_count = 0
        self.node_id = np.arange(self.max_nodes, dtype=np.int32)
        self.parent_id = np.full(self.max_nodes, SENTINEL, dtype=np.int32)
        self.incoming_policy_action_slot = np.full(self.max_nodes, SENTINEL, dtype=np.int8)
        self.depth = np.zeros(self.max_nodes, dtype=np.uint16)
        self.visits = np.zeros(self.max_nodes, dtype=np.uint32)
        self.value_sum = np.zeros(self.max_nodes, dtype=np.float64)
        self.value_max = np.full(self.max_nodes, -np.inf, dtype=np.float64)
        self.legal_action_mask = np.zeros(self.max_nodes, dtype=np.uint32)
        self.expanded_action_mask = np.zeros(self.max_nodes, dtype=np.uint32)
        self.terminal = np.zeros(self.max_nodes, dtype=np.bool_)
        self.invalid = np.zeros(self.max_nodes, dtype=np.bool_)
        self.snapshot_ref = np.full(self.max_nodes, SENTINEL, dtype=np.int32)
        self.total_damage = np.zeros(self.max_nodes, dtype=np.float64)
        self.combat_time = np.zeros(self.max_nodes, dtype=np.float64)
        self.current_time = np.zeros(self.max_nodes, dtype=np.float64)
        self.full_state_fingerprint = np.zeros(self.max_nodes, dtype="S64")
        self.future_state_fingerprint = np.zeros(self.max_nodes, dtype="S64")
        self.children = np.full((self.max_nodes, ACTION_COUNT), SENTINEL, dtype=np.int32)

    def add_node(self, *, parent_id: int, action_slot: int, legal_slots: list[int], terminal: bool,
                 invalid: bool, snapshot_ref: int, total_damage: float, combat_time: float,
                 current_time: float, full_fingerprint: str, future_fingerprint: str) -> int:
        if self.node_count >= self.max_nodes:
            raise MemoryError("MCTS maximum node capacity exhausted")
        node = self.node_count; self.node_count += 1
        self.parent_id[node] = int(parent_id)
        self.incoming_policy_action_slot[node] = int(action_slot)
        self.depth[node] = 0 if parent_id < 0 else int(self.depth[parent_id]) + 1
        self.legal_action_mask[node] = slots_to_mask(legal_slots)
        self.terminal[node] = bool(terminal); self.invalid[node] = bool(invalid)
        self.snapshot_ref[node] = int(snapshot_ref)
        self.total_damage[node] = float(total_damage); self.combat_time[node] = float(combat_time)
        self.current_time[node] = float(current_time)
        self.full_state_fingerprint[node] = full_fingerprint.encode("ascii")
        self.future_state_fingerprint[node] = future_fingerprint.encode("ascii")
        if parent_id >= 0:
            self.children[parent_id, action_slot] = node
            self.expanded_action_mask[parent_id] |= np.uint32(1 << action_slot)
        return node

    def selected_slots(self, node_id: int) -> list[int]:
        slots: list[int] = []
        current = int(node_id)
        while current > 0:
            slots.append(int(self.incoming_policy_action_slot[current]))
            current = int(self.parent_id[current])
        slots.reverse()
        return slots

    def choose_child(self, node_id: int, legal_slots: list[int], *, seed: int, action_ids: tuple[str, ...]) -> int:
        children = [(slot, int(self.children[node_id, slot])) for slot in legal_slots if self.children[node_id, slot] >= 0]
        unvisited = [(slot, child) for slot, child in children if int(self.visits[child]) == 0]
        candidates = unvisited or children
        if not candidates:
            raise ValueError("No expanded child available")
        fp = self.full_state_fingerprint[node_id].decode("ascii")
        return min(
            candidates,
            key=lambda item: (
                -uct_score(int(self.visits[node_id]), int(self.visits[item[1]]), float(self.value_sum[item[1]])),
                deterministic_action_rank(seed, fp, action_ids[item[0]]),
            ),
        )[1]

    def backpropagate(self, path: list[int], reward: float, *, completed: bool) -> None:
        for node in path:
            self.visits[node] += 1
            if completed:
                self.value_sum[node] += float(reward)
                self.value_max[node] = max(float(self.value_max[node]), float(reward))

    def arrays(self, *, used_only: bool = False) -> dict[str, np.ndarray]:
        end = self.node_count if used_only else self.max_nodes
        names = ("node_id", "parent_id", "incoming_policy_action_slot", "depth", "visits", "value_sum", "value_max",
                 "legal_action_mask", "expanded_action_mask", "terminal", "invalid", "snapshot_ref", "total_damage",
                 "combat_time", "current_time", "full_state_fingerprint", "future_state_fingerprint", "children")
        return {name: getattr(self, name)[:end].copy() for name in names}

    def load_arrays(self, arrays: dict[str, np.ndarray], node_count: int) -> None:
        self.node_count = int(node_count)
        for name, source in arrays.items():
            target = getattr(self, name)
            if name == "children": target[:self.node_count, :] = source
            else: target[:self.node_count] = source

    def allocated_bytes(self) -> dict[str, int]:
        arrays = self.arrays(used_only=False)
        child = int(arrays.pop("children").nbytes)
        fingerprint = int(arrays.pop("full_state_fingerprint").nbytes + arrays.pop("future_state_fingerprint").nbytes)
        return {"typed_node_array_bytes": sum(int(a.nbytes) for a in arrays.values()), "child_table_bytes": child, "fingerprint_bytes": fingerprint}


def slots_to_mask(slots: list[int]) -> int:
    mask = 0
    for slot in slots: mask |= 1 << int(slot)
    return mask


def mask_to_slots(mask: int) -> list[int]:
    return [slot for slot in range(ACTION_COUNT) if int(mask) & (1 << slot)]


def save_tree_npz(path: Path, tree: MCTSTree) -> None:
    temp = path.with_name(path.name + ".tmp")
    with temp.open("wb") as file:
        np.savez_compressed(file, **tree.arrays(used_only=True))
    temp.replace(path)


def load_tree_npz(path: Path, *, max_nodes: int) -> MCTSTree:
    with np.load(path, allow_pickle=False) as payload:
        arrays = {name: payload[name] for name in payload.files}
    count = int(len(arrays["parent_id"]))
    if count > max_nodes:
        raise ValueError("Checkpoint node count exceeds plan capacity")
    tree = MCTSTree(max_nodes)
    tree.load_arrays(arrays, count)
    return tree
