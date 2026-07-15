from __future__ import annotations

import copy
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from search.mcts_checkpoint import SnapshotStore
from search.mcts_state import create_initial_simulation, legal_policy_slots, node_metrics, policy_action_ids
from search.mcts_tree import MCTSTree
from search.search_state_codec import clone_simulation_for_search


def main() -> None:
    template = create_initial_simulation(combat_duration=120.0); actions = policy_action_ids(template); simulation = clone_simulation_for_search(template)
    with tempfile.TemporaryDirectory(prefix="mcts-snapshot-") as tmp:
        store = SnapshotStore(Path(tmp), cache_entries=8, cache_max_bytes=10_000_000, create=True); tree = MCTSTree(32)
        metrics = node_metrics(simulation); root_ref = store.add(simulation)
        tree.add_node(parent_id=-1, action_slot=-1, legal_slots=legal_policy_slots(simulation, actions), terminal=False, invalid=False,
                      snapshot_ref=root_ref, total_damage=0.0, combat_time=0.0, current_time=0.0,
                      full_fingerprint=str(metrics["full_fingerprint"]), future_fingerprint=str(metrics["future_fingerprint"]))
        parent = 0
        for depth in range(1, 18):
            chosen = None
            for slot in legal_policy_slots(simulation, actions):
                probe = clone_simulation_for_search(simulation); before = probe.state.combat_time
                if probe.execute_action(actions[slot]) and probe.state.combat_time > before + 1e-12: chosen = slot; break
            assert chosen is not None and simulation.execute_action(actions[chosen])
            metrics = node_metrics(simulation); ref = store.add(simulation) if depth % 8 == 0 else -1
            parent = tree.add_node(parent_id=parent, action_slot=chosen, legal_slots=legal_policy_slots(simulation, actions), terminal=False,
                invalid=False, snapshot_ref=ref, total_damage=float(metrics["total_damage"]), combat_time=float(metrics["combat_time"]),
                current_time=float(metrics["current_time"]), full_fingerprint=str(metrics["full_fingerprint"]), future_fingerprint=str(metrics["future_fingerprint"]))
        maximum = 0
        for node in range(tree.node_count):
            _, replay = store.restore_node(tree=tree, node_id=node, template=template, action_ids=actions); maximum = max(maximum, replay)
        assert maximum == 7
        original = copy.deepcopy(store.records[1]); store.cache.clear(); store.records[1]["compressed_sha256"] = "0" * 64
        try: store.get_payload(1)
        except ValueError: pass
        else: raise AssertionError("corrupt snapshot hash accepted")
        store.records[1] = original; store.records[1]["uncompressed_bytes"] += 1
        try: store.get_payload(1)
        except ValueError: pass
        else: raise AssertionError("corrupt snapshot length accepted")
    print("mcts_snapshot_reconstruction_smoke_test ok max_replay=7")


if __name__ == "__main__": main()
