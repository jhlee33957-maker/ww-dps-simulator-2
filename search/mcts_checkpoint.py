from __future__ import annotations

import copy
import hashlib
import json
import os
import zlib
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable

import numpy as np

from search.mcts_tree import MCTSTree, load_tree_npz, save_tree_npz
from search.search_state_codec import (
    canonical_json_bytes,
    full_node_state_fingerprint,
    execute_action_for_search,
    restore_simulation_from_state,
    serialize_simulation_state,
    sha256_file,
)


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(temp, path)


class SnapshotStore:
    def __init__(self, root: Path, *, cache_entries: int, cache_max_bytes: int, create: bool) -> None:
        self.root = root
        self.data_path = root / "snapshots.dat"
        self.records: list[dict[str, Any]] = []
        self.by_payload_sha: dict[str, int] = {}
        self.dedup_hits = 0
        self.uncompressed_bytes = 0
        self.compressed_bytes = 0
        self.cache_entries = int(cache_entries)
        self.cache_max_bytes = int(cache_max_bytes)
        self.cache: OrderedDict[int, tuple[dict[str, Any], int]] = OrderedDict()
        self.cache_bytes = 0
        if create:
            root.mkdir(parents=True, exist_ok=True)
            self.data_path.touch(exist_ok=True)

    def add(self, simulation: Any) -> int:
        payload = serialize_simulation_state(simulation)
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        raw_sha = hashlib.sha256(raw).hexdigest()
        if raw_sha in self.by_payload_sha:
            self.dedup_hits += 1
            return self.by_payload_sha[raw_sha]
        compressed = zlib.compress(raw, level=9)
        offset = self.data_path.stat().st_size
        with self.data_path.open("ab") as file:
            file.write(compressed)
            file.flush()
            os.fsync(file.fileno())
        ref = len(self.records)
        record = {
            "snapshot_ref": ref, "offset": offset, "compressed_bytes": len(compressed),
            "uncompressed_bytes": len(raw), "compressed_sha256": hashlib.sha256(compressed).hexdigest(),
            "payload_sha256": raw_sha,
        }
        self.records.append(record); self.by_payload_sha[raw_sha] = ref
        self.uncompressed_bytes += len(raw); self.compressed_bytes += len(compressed)
        self._cache_put(ref, payload, len(raw))
        return ref

    def get_payload(self, ref: int) -> dict[str, Any]:
        ref = int(ref)
        if ref in self.cache:
            payload, size = self.cache.pop(ref); self.cache[ref] = (payload, size)
            return copy.deepcopy(payload)
        record = self.records[ref]
        with self.data_path.open("rb") as file:
            file.seek(int(record["offset"])); compressed = file.read(int(record["compressed_bytes"]))
        if hashlib.sha256(compressed).hexdigest() != record["compressed_sha256"]:
            raise ValueError("MCTS snapshot compressed hash mismatch")
        raw = zlib.decompress(compressed)
        if len(raw) != int(record["uncompressed_bytes"]) or hashlib.sha256(raw).hexdigest() != record["payload_sha256"]:
            raise ValueError("MCTS snapshot payload hash/length mismatch")
        payload = json.loads(raw.decode("utf-8"))
        self._cache_put(ref, payload, len(raw))
        return copy.deepcopy(payload)

    def restore_node(self, *, tree: MCTSTree, node_id: int, template: Any, action_ids: tuple[str, ...],
                     action_executor: Callable[[Any, int], bool] | None = None) -> tuple[Any, int]:
        lineage: list[int] = []
        ancestor = int(node_id)
        while int(tree.snapshot_ref[ancestor]) < 0:
            lineage.append(ancestor); ancestor = int(tree.parent_id[ancestor])
            if ancestor < 0: raise ValueError("MCTS node has no snapshot ancestor")
        if len(lineage) > 7:
            raise ValueError("MCTS snapshot reconstruction exceeds the stride-8 maximum replay length")
        simulation = restore_simulation_from_state(template, self.get_payload(int(tree.snapshot_ref[ancestor])))
        for current in reversed(lineage):
            slot = int(tree.incoming_policy_action_slot[current])
            succeeded = (action_executor(simulation, slot) if action_executor is not None
                         else execute_action_for_search(simulation, action_ids[slot]))
            if not succeeded:
                raise ValueError("MCTS snapshot reconstruction action failed")
        expected = tree.full_state_fingerprint[node_id].decode("ascii")
        actual_fingerprint = full_node_state_fingerprint(simulation)
        if actual_fingerprint != expected:
            raise ValueError(
                f"MCTS reconstructed node fingerprint mismatch: node={node_id} ancestor={ancestor} "
                f"replay={len(lineage)} expected={expected} actual={actual_fingerprint}"
            )
        checks = ((simulation.state.total_damage, tree.total_damage[node_id], "damage"),
                  (simulation.state.combat_time, tree.combat_time[node_id], "combat_time"),
                  (simulation.state.current_time, tree.current_time[node_id], "current_time"))
        for actual, stored, label in checks:
            if abs(float(actual) - float(stored)) > 1e-9:
                raise ValueError(f"MCTS reconstructed node {label} mismatch")
        return simulation, len(lineage)

    def index_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "mcts_snapshot_index_v117", "records": self.records,
            "snapshot_dedup_hits": self.dedup_hits, "unique_snapshot_count": len(self.records),
            "uncompressed_bytes": self.uncompressed_bytes, "compressed_bytes": self.compressed_bytes,
            "compression_ratio": self.compressed_bytes / max(self.uncompressed_bytes, 1),
        }

    def committed_prefix(self) -> dict[str, Any]:
        length = self.data_path.stat().st_size
        return {"committed_length": length, "committed_sha256": sha256_file(self.data_path, length=length)}

    def load_index(self, payload: dict[str, Any]) -> None:
        if payload.get("schema_version") != "mcts_snapshot_index_v117": raise ValueError("MCTS snapshot index schema mismatch")
        self.records = list(payload["records"])
        self.by_payload_sha = {record["payload_sha256"]: int(record["snapshot_ref"]) for record in self.records}
        self.dedup_hits = int(payload.get("snapshot_dedup_hits", 0))
        self.uncompressed_bytes = int(payload.get("uncompressed_bytes", 0)); self.compressed_bytes = int(payload.get("compressed_bytes", 0))

    def validate_committed_prefix(self, *, length: int, sha256: str) -> None:
        if not self.data_path.is_file() or self.data_path.stat().st_size < int(length):
            raise ValueError("MCTS snapshot store is shorter than the committed prefix")
        if sha256_file(self.data_path, length=int(length)) != sha256:
            raise ValueError("MCTS snapshot committed-prefix hash mismatch")
        for record in self.records:
            if int(record["offset"]) + int(record["compressed_bytes"]) > int(length):
                raise ValueError("MCTS snapshot index references uncommitted bytes")

    def truncate_uncommitted_tail(self, committed_length: int) -> None:
        """Discard crash residue only after every checkpoint hash has validated."""
        length = int(committed_length)
        if self.data_path.stat().st_size > length:
            with self.data_path.open("r+b") as file:
                file.truncate(length)
                file.flush()
                os.fsync(file.fileno())

    def _cache_put(self, ref: int, payload: dict[str, Any], size: int) -> None:
        if size > self.cache_max_bytes or self.cache_entries <= 0: return
        if ref in self.cache:
            _, old = self.cache.pop(ref); self.cache_bytes -= old
        self.cache[ref] = (payload, size); self.cache_bytes += size
        while len(self.cache) > self.cache_entries or self.cache_bytes > self.cache_max_bytes:
            _, (_, removed) = self.cache.popitem(last=False); self.cache_bytes -= removed


class CheckpointManager:
    def __init__(self, output_root: Path, *, retain_generations: int | None = None,
                 allow_corrupt_latest_fallback: bool = False) -> None:
        self.root = output_root / "checkpoint"
        self.retain_generations = retain_generations
        self.allow_corrupt_latest_fallback = bool(allow_corrupt_latest_fallback)

    def save(self, *, plan_path: str, plan_sha256: str, stage_hash: str, simulations: int,
             tree: MCTSTree, snapshots: SnapshotStore, rng_state: dict[str, Any], mast_counts: np.ndarray,
             mast_value_sums: np.ndarray, completed_routes: list[dict[str, Any]], counters: dict[str, Any]) -> dict[str, Any]:
        self.root.mkdir(parents=True, exist_ok=True)
        generation = f"{int(simulations):08d}"
        tree_path = self.root / f"tree_{generation}.npz"; save_tree_npz(tree_path, tree)
        mast_path = self.root / f"mast_{generation}.npz"; temp = mast_path.with_name(mast_path.name + ".tmp")
        with temp.open("wb") as file: np.savez_compressed(file, counts=mast_counts, value_sums=mast_value_sums)
        os.replace(temp, mast_path)
        rng_path = self.root / f"rng_{generation}.json"; atomic_json(rng_path, rng_state)
        routes_path = self.root / f"completed_{generation}.json"; atomic_json(routes_path, completed_routes)
        index_path = self.root / f"snapshot_index_{generation}.json"; atomic_json(index_path, snapshots.index_payload())
        prefix = snapshots.committed_prefix()
        manifest = {
            "schema_version": "mcts_checkpoint_manifest_v117", "plan_path": plan_path, "plan_sha256": plan_sha256,
            "stage_contract_sha256": stage_hash, "simulation_count": int(simulations), "node_count": tree.node_count,
            "root_node": 0, "completed_route_count": int(counters.get("completed_rollout_count", 0)),
            "best_completed_route": completed_routes[0] if completed_routes else None, "files": {
                "tree": _entry(tree_path), "mast": _entry(mast_path), "rng": _entry(rng_path),
                "completed_routes": _entry(routes_path), "snapshot_index": _entry(index_path),
            }, "snapshot_store": prefix, "counters": counters,
        }
        latest = self.root / "latest_manifest.json"; previous = self.root / "previous_manifest.json"
        if latest.is_file(): os.replace(latest, previous)
        atomic_json(latest, manifest)
        if self.retain_generations is not None:
            if int(self.retain_generations) != 2:
                raise ValueError("MCTS rolling retention supports exactly latest+previous generations")
            self._commit_progression_and_prune(latest, previous, manifest)
        return manifest

    def _commit_progression_and_prune(self, latest: Path, previous: Path, manifest: dict[str, Any]) -> None:
        retained: list[dict[str, Any]] = []
        for path in (latest, previous):
            if not path.is_file():
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            for entry in payload["files"].values():
                source = self.root / entry["path"]
                if not source.is_file() or source.stat().st_size != int(entry["bytes"]) or sha256_file(source) != entry["sha256"]:
                    raise ValueError("MCTS retained checkpoint validation failed before pruning")
            retained.append(payload)
        if not retained or retained[0]["simulation_count"] != manifest["simulation_count"]:
            raise ValueError("MCTS latest checkpoint was not committed before pruning")
        progression_path = self.root / "progression.json"
        progression = {"schema_version": "mcts_checkpoint_progression_v118", "checkpoints": []}
        if progression_path.is_file():
            progression = json.loads(progression_path.read_text(encoding="utf-8"))
        counters = manifest.get("counters", {})
        memory = counters.get("memory", {})
        row = {"simulation_count": int(manifest["simulation_count"]), "node_count": int(manifest["node_count"]),
               "best_damage": None if manifest.get("best_completed_route") is None else float(manifest["best_completed_route"]["total_damage"]),
               "simulations_per_second": counters.get("checkpoint_simulations_per_second"),
               "process_peak_rss_bytes": memory.get("process_peak_rss_bytes"),
               "tracked_bytes": memory.get("tracked_bytes"),
               "conservative_total_estimate_bytes": memory.get("conservative_total_estimate_bytes")}
        rows = [item for item in progression.get("checkpoints", []) if int(item["simulation_count"]) != row["simulation_count"]]
        rows.append(row); rows.sort(key=lambda item: int(item["simulation_count"]))
        progression["checkpoints"] = rows
        atomic_json(progression_path, progression)
        keep = {entry["path"] for payload in retained for entry in payload["files"].values()}
        prefixes = ("tree_", "mast_", "rng_", "completed_", "snapshot_index_")
        for path in self.root.iterdir():
            if path.is_file() and path.name.startswith(prefixes) and path.name not in keep:
                path.unlink()

    def load_preflight(self, *, plan_sha256: str, stage_hash: str, max_nodes: int,
                       cache_entries: int, cache_max_bytes: int) -> dict[str, Any]:
        latest = self.root / "latest_manifest.json"
        previous = self.root / "previous_manifest.json"
        try:
            return self._load_manifest_preflight(latest, source="latest", plan_sha256=plan_sha256,
                stage_hash=stage_hash, max_nodes=max_nodes, cache_entries=cache_entries,
                cache_max_bytes=cache_max_bytes)
        except (IncompleteCheckpointError, CorruptCheckpointError) as latest_error:
            if isinstance(latest_error, CorruptCheckpointError) and not self.allow_corrupt_latest_fallback:
                raise
            try:
                loaded = self._load_manifest_preflight(previous, source="previous", plan_sha256=plan_sha256,
                    stage_hash=stage_hash, max_nodes=max_nodes, cache_entries=cache_entries,
                    cache_max_bytes=cache_max_bytes)
            except (IncompleteCheckpointError, CorruptCheckpointError, ValueError) as previous_error:
                raise ValueError(
                    f"MCTS latest checkpoint is incomplete ({latest_error}); previous checkpoint is unusable ({previous_error})"
                ) from previous_error
            loaded["fallback_reason"] = str(latest_error)
            return loaded

    def _load_manifest_preflight(self, manifest_path: Path, *, source: str, plan_sha256: str,
                                 stage_hash: str, max_nodes: int, cache_entries: int,
                                 cache_max_bytes: int) -> dict[str, Any]:
        if not manifest_path.is_file():
            raise IncompleteCheckpointError(f"{source} manifest is missing")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise IncompleteCheckpointError(f"{source} manifest is truncated/unreadable") from error
        if manifest.get("schema_version") != "mcts_checkpoint_manifest_v117": raise CorruptCheckpointError("MCTS checkpoint schema mismatch")
        if manifest.get("plan_sha256") != plan_sha256: raise CorruptCheckpointError("MCTS checkpoint plan SHA mismatch")
        if manifest.get("stage_contract_sha256") != stage_hash: raise CorruptCheckpointError("MCTS checkpoint stage hash mismatch")
        paths: dict[str, Path] = {}
        try:
            file_entries = manifest["files"].items()
        except (KeyError, AttributeError) as error:
            raise IncompleteCheckpointError(f"{source} manifest has no complete file table") from error
        for key, entry in file_entries:
            path = self.root / entry["path"]
            if not path.is_file() or path.stat().st_size < int(entry["bytes"]):
                raise IncompleteCheckpointError(f"{source} checkpoint {key} file is missing/truncated")
            if path.stat().st_size != int(entry["bytes"]) or sha256_file(path) != entry["sha256"]:
                raise CorruptCheckpointError(f"MCTS checkpoint {key} hash/length mismatch")
            paths[key] = path
        try:
            tree = load_tree_npz(paths["tree"], max_nodes=max_nodes)
            if tree.node_count != int(manifest["node_count"]): raise CorruptCheckpointError("MCTS checkpoint node count mismatch")
            with np.load(paths["mast"], allow_pickle=False) as payload:
                mast_counts = payload["counts"].copy(); mast_sums = payload["value_sums"].copy()
            rng_state = json.loads(paths["rng"].read_text(encoding="utf-8"))
            routes = json.loads(paths["completed_routes"].read_text(encoding="utf-8"))
            index = json.loads(paths["snapshot_index"].read_text(encoding="utf-8"))
        except CorruptCheckpointError:
            raise
        except Exception as error:
            raise CorruptCheckpointError(f"MCTS {source} checkpoint payload is invalid") from error
        snapshots = SnapshotStore(self.root, cache_entries=cache_entries, cache_max_bytes=cache_max_bytes, create=False)
        try:
            snapshots.load_index(index)
            committed_length = int(manifest["snapshot_store"]["committed_length"])
            snapshots.validate_committed_prefix(length=committed_length, sha256=manifest["snapshot_store"]["committed_sha256"])
        except Exception as error:
            raise CorruptCheckpointError(f"MCTS {source} snapshot checkpoint is invalid") from error
        # This is the first permitted output mutation in resume: all manifest,
        # array, RNG, MAST, route, index, and committed-prefix hashes passed.
        snapshots.truncate_uncommitted_tail(committed_length)
        return {"manifest": manifest, "tree": tree, "mast_counts": mast_counts, "mast_value_sums": mast_sums,
                "rng_state": rng_state, "completed_routes": routes, "snapshots": snapshots,
                "checkpoint_source": source}


class IncompleteCheckpointError(ValueError):
    pass


class CorruptCheckpointError(ValueError):
    pass


def _entry(path: Path) -> dict[str, Any]:
    return {"path": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)}
