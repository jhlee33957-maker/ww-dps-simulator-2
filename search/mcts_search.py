from __future__ import annotations

import hashlib
import json
import math
import os
import time
from pathlib import Path
from typing import Any

import numpy as np

from search.mcts_checkpoint import CheckpointManager, SnapshotStore
from search.mcts_plan import lowered_memory_budget, stage_contract_hash
from search.mcts_state import create_initial_simulation, execute_policy_slot, legal_policy_slots, node_metrics, policy_action_ids
from search.mcts_tree import MCTSTree, allowed_children, deterministic_action_rank, mask_to_slots
from search.search_state_codec import DIAGNOSTIC_ONLY_FIELDS, canonical_json_bytes, process_peak_rss_bytes, sequence_sha256


TERMINATION_STATUSES = {
    "simulation_budget_exhausted", "memory_budget_exhausted", "wall_clock_budget_exhausted",
    "node_capacity_exhausted",
}


class MASTTable:
    def __init__(self, character_ids: tuple[str, ...], action_ids: tuple[str, ...]) -> None:
        self.character_ids = character_ids; self.action_ids = action_ids
        self.character_index = {name: index for index, name in enumerate(character_ids)}
        self.counts = np.zeros((len(character_ids), len(action_ids)), dtype=np.uint32)
        self.value_sums = np.zeros((len(character_ids), len(action_ids)), dtype=np.float64)
        self.uniform_choices = 0; self.random_choices = 0; self.exploitation_choices = 0

    def choose(self, *, active_character: str, legal_slots: list[int], simulation_index: int,
               rng: np.random.Generator, warmup: int, epsilon: float, minimum_visits: int) -> int:
        row = self.character_index[active_character]
        if simulation_index < warmup:
            self.uniform_choices += 1
            return int(legal_slots[int(rng.integers(len(legal_slots)))])
        if float(rng.random()) < epsilon:
            self.random_choices += 1
            return int(legal_slots[int(rng.integers(len(legal_slots)))])
        eligible = [slot for slot in legal_slots if int(self.counts[row, slot]) >= minimum_visits]
        if not eligible:
            self.random_choices += 1
            return int(legal_slots[int(rng.integers(len(legal_slots)))])
        means = [float(self.value_sums[row, slot]) / int(self.counts[row, slot]) for slot in eligible]
        best = max(means); ties = [slot for slot, mean in zip(eligible, means) if abs(mean - best) <= 1e-15]
        self.exploitation_choices += 1
        return int(ties[int(rng.integers(len(ties)))])

    def update(self, contexts: list[tuple[str, int]], reward: float) -> None:
        for character_id, slot in contexts:
            row = self.character_index[character_id]
            self.counts[row, slot] += 1; self.value_sums[row, slot] += float(reward)

    def metrics(self) -> dict[str, int]:
        return {
            "mast_context_count": int(np.count_nonzero(self.counts)), "mast_uniform_choice_count": self.uniform_choices,
            "mast_random_choice_count": self.random_choices, "mast_exploitation_choice_count": self.exploitation_choices,
        }


class MCTSSearch:
    def __init__(self, *, plan: dict[str, Any], stage: dict[str, Any], output_root: Path,
                 max_simulations: int | None = None, memory_budget_bytes: int | None = None,
                 allow_test_output_root: bool = False) -> None:
        self.plan = plan; self.stage = dict(stage); self.output_root = output_root
        project_root = Path(__file__).resolve().parents[1]
        canonical_output = (project_root / str(stage["canonical_output_root"])).resolve()
        if output_root.resolve() != canonical_output and not allow_test_output_root:
            raise ValueError("MCTS production output root must exactly match the canonical plan output root")
        self.allow_test_output_root = bool(allow_test_output_root)
        configured_max = int(stage["maximum_simulations"])
        self.target_simulations = configured_max if max_simulations is None else int(max_simulations)
        if self.target_simulations > configured_max: raise ValueError("MCTS simulation override may not exceed the stage cap")
        self.memory_budget_bytes = lowered_memory_budget(int(stage["memory_budget_bytes"]), memory_budget_bytes)
        self.plan_sha256 = str(plan.get("_plan_sha256") or hashlib.sha256(canonical_json_bytes({k: v for k, v in plan.items() if not k.startswith("_")})).hexdigest())
        self.plan_path = str(plan.get("_plan_path") or "data/mcts_plan_v117_32gb.json")
        self.stage_hash = stage_contract_hash(plan, self.stage)
        self.template = create_initial_simulation(combat_duration=float(stage["combat_duration"]))
        self.action_ids = policy_action_ids(self.template)
        self.tree = MCTSTree(int(stage["maximum_nodes"]))
        self.rng = np.random.Generator(np.random.PCG64(int(stage["seed"])))
        characters = tuple(self.template.selected_character_ids)
        self.mast = MASTTable(characters, self.action_ids)
        self.snapshots: SnapshotStore | None = None
        retention = stage.get("checkpoint_retention_generations")
        self.checkpoints = CheckpointManager(
            output_root,
            retain_generations=None if retention is None else int(retention),
            allow_corrupt_latest_fallback=bool(stage.get("allow_corrupt_latest_fallback", False)),
        )
        self.simulations = 0; self.completed_rollout_count = 0; self.completed_routes: list[dict[str, Any]] = []
        self.first_completed_rollout_simulation_index: int | None = None
        self.invalid_rollout_counts: dict[str, int] = {}
        self.total_action_executions = 0; self.exact_full_state_duplicate_count = 0
        self.future_only_fingerprint_collision_count = 0; self.checkpoint_count = 0
        self.selection_depths: list[int] = []; self.rollout_action_counts: list[int] = []
        self.progressive_widening_expansions = 0; self.max_reconstruction_replay_length = 0
        self.peak_checkpoint_serialization_buffer = 0
        self.phase_seconds = {name: 0.0 for name in ("selection", "expansion", "rollout", "backpropagation", "checkpoint")}
        self.invocation_phase_seconds = {name: 0.0 for name in self.phase_seconds}
        self.full_seen: set[str] = set(); self.future_damage_seen: dict[str, float] = {}
        self.started_at = 0.0; self.peak_rss = process_peak_rss_bytes()
        self.last_checkpoint_simulations = -1
        self.resume_checkpoint_source: str | None = None
        self.resume_checkpoint_fallback_reason: str | None = None
        self.simulation_runtime_seconds: list[float] = []
        self.slowest_simulation_index: int | None = None
        self.slowest_simulation_selection_depth = 0
        self.slowest_simulation_rollout_action_count = 0
        self.maximum_individual_action_execution_seconds = 0.0
        self.slowest_action_id: str | None = None
        self.slowest_action_active_character: str | None = None
        self.lightweight_diagnostic_log_rows = 0
        self.lightweight_diagnostic_bytes = 0
        self._current_max_action_seconds = 0.0
        self._current_slowest_action_id: str | None = None
        self._current_slowest_action_active: str | None = None

    def run(self, *, resume: bool = False) -> dict[str, Any]:
        self.started_at = time.perf_counter()
        if resume:
            self._load_resume_preflight()
        else:
            if self.output_root.exists() and any(self.output_root.iterdir()):
                raise ValueError("MCTS fresh execution refuses a nonempty output root; use validated --resume")
            self._initialize_new()
        self.output_root.mkdir(parents=True, exist_ok=True)
        self._log(f"stage start resume={resume} target={self.target_simulations}")
        status = "simulation_budget_exhausted"
        while self.simulations < self.target_simulations:
            if self.tree.node_count >= self.tree.max_nodes:
                status = "node_capacity_exhausted"; break
            simulation_started = time.perf_counter()
            self._current_max_action_seconds = 0.0
            self._current_slowest_action_id = None
            self._current_slowest_action_active = None
            self._simulate_once()
            simulation_elapsed = time.perf_counter() - simulation_started
            self.simulation_runtime_seconds.append(simulation_elapsed)
            if self.slowest_simulation_index is None or simulation_elapsed > self.simulation_runtime_seconds[self.slowest_simulation_index - 1]:
                self.slowest_simulation_index = self.simulations + 1
                self.slowest_simulation_selection_depth = self.selection_depths[-1] if self.selection_depths else 0
                self.slowest_simulation_rollout_action_count = self.rollout_action_counts[-1] if self.rollout_action_counts else 0
            if self._current_max_action_seconds > self.maximum_individual_action_execution_seconds:
                self.maximum_individual_action_execution_seconds = self._current_max_action_seconds
                self.slowest_action_id = self._current_slowest_action_id
                self.slowest_action_active_character = self._current_slowest_action_active
            self.simulations += 1
            if self.simulations % int(self.stage["checkpoint_interval_simulations"]) == 0:
                self._save_checkpoint()
            if self.simulations % int(self.stage["limit_check_interval_simulations"]) == 0:
                self.peak_rss = max(self.peak_rss, process_peak_rss_bytes())
                if max(self.peak_rss, self.memory_breakdown()["conservative_total_estimate_bytes"]) >= self.memory_budget_bytes:
                    status = "memory_budget_exhausted"; break
                if time.perf_counter() - self.started_at >= float(self.stage["wall_clock_budget_seconds"]):
                    status = "wall_clock_budget_exhausted"; break
        if self.last_checkpoint_simulations != self.simulations:
            self._save_checkpoint()
        elapsed = time.perf_counter() - self.started_at
        result = self._result(status, elapsed)
        self._log(f"stage stop status={status} simulations={self.simulations}")
        return result

    def _initialize_new(self) -> None:
        self.snapshots = SnapshotStore(self.output_root / "checkpoint", cache_entries=int(self.stage["decoded_snapshot_cache_entries"]),
                                       cache_max_bytes=int(self.stage["decoded_snapshot_cache_maximum_bytes"]), create=True)
        root_metrics = node_metrics(self.template); legal = legal_policy_slots(self.template, self.action_ids)
        snapshot_ref = self.snapshots.add(self.template)
        self.tree.add_node(parent_id=-1, action_slot=-1, legal_slots=legal, terminal=False, invalid=False,
                           snapshot_ref=snapshot_ref, total_damage=float(root_metrics["total_damage"]),
                           combat_time=float(root_metrics["combat_time"]), current_time=float(root_metrics["current_time"]),
                           full_fingerprint=str(root_metrics["full_fingerprint"]), future_fingerprint=str(root_metrics["future_fingerprint"]))
        self.full_seen.add(str(root_metrics["full_fingerprint"])); self.future_damage_seen[str(root_metrics["future_fingerprint"])] = 0.0

    def _load_resume_preflight(self) -> None:
        loaded = self.checkpoints.load_preflight(plan_sha256=self.plan_sha256, stage_hash=self.stage_hash,
            max_nodes=int(self.stage["maximum_nodes"]), cache_entries=int(self.stage["decoded_snapshot_cache_entries"]),
            cache_max_bytes=int(self.stage["decoded_snapshot_cache_maximum_bytes"]))
        self.tree = loaded["tree"]; self.snapshots = loaded["snapshots"]
        self.resume_checkpoint_source = str(loaded["checkpoint_source"])
        self.resume_checkpoint_fallback_reason = loaded.get("fallback_reason")
        self.rng.bit_generator.state = loaded["rng_state"]
        self.mast.counts = loaded["mast_counts"]; self.mast.value_sums = loaded["mast_value_sums"]
        self.completed_routes = loaded["completed_routes"]
        counters = loaded["manifest"].get("counters", {})
        self.simulations = int(loaded["manifest"]["simulation_count"])
        self.last_checkpoint_simulations = self.simulations
        for name in ("completed_rollout_count", "total_action_executions", "exact_full_state_duplicate_count",
                     "future_only_fingerprint_collision_count", "progressive_widening_expansions", "checkpoint_count"):
            setattr(self, name, int(counters.get(name, getattr(self, name))))
        self.first_completed_rollout_simulation_index = counters.get("first_completed_rollout_simulation_index")
        self.invalid_rollout_counts = {str(k): int(v) for k, v in counters.get("invalid_rollout_counts", {}).items()}
        self.selection_depths = [int(v) for v in counters.get("selection_depths", [])]
        self.rollout_action_counts = [int(v) for v in counters.get("rollout_action_counts", [])]
        self.simulation_runtime_seconds = [float(v) for v in counters.get("simulation_runtime_seconds", [])]
        self.slowest_simulation_index = counters.get("slowest_simulation_index")
        self.slowest_simulation_selection_depth = int(counters.get("slowest_simulation_selection_depth", 0))
        self.slowest_simulation_rollout_action_count = int(counters.get("slowest_simulation_rollout_action_count", 0))
        self.maximum_individual_action_execution_seconds = float(counters.get("maximum_individual_action_execution_seconds", 0.0))
        self.slowest_action_id = counters.get("slowest_action_id")
        self.slowest_action_active_character = counters.get("slowest_action_active_character")
        self.lightweight_diagnostic_log_rows = int(counters.get("lightweight_diagnostic_log_rows", 0))
        self.lightweight_diagnostic_bytes = int(counters.get("lightweight_diagnostic_bytes", 0))
        self.max_reconstruction_replay_length = int(counters.get("max_reconstruction_replay_length", 0))
        for key in self.phase_seconds: self.phase_seconds[key] = float(counters.get("phase_seconds", {}).get(key, 0.0))
        mast_metrics = counters.get("mast_choice_counters", {})
        self.mast.uniform_choices = int(mast_metrics.get("mast_uniform_choice_count", 0)); self.mast.random_choices = int(mast_metrics.get("mast_random_choice_count", 0)); self.mast.exploitation_choices = int(mast_metrics.get("mast_exploitation_choice_count", 0))
        self.full_seen = {self.tree.full_state_fingerprint[i].decode("ascii") for i in range(self.tree.node_count)}
        self.future_damage_seen = {self.tree.future_state_fingerprint[i].decode("ascii"): float(self.tree.total_damage[i]) for i in range(self.tree.node_count)}

    def _simulate_once(self) -> None:
        assert self.snapshots is not None
        select_started = time.perf_counter(); node = 0; path = [0]; expanded = False
        maximum_actions = int(self.stage["maximum_actions_per_simulation"])
        maximum_zero = int(self.stage["maximum_consecutive_zero_time_actions"])
        zero_count = 0
        while True:
            selected_actions = len(path) - 1
            zero_count = self._selection_zero_tail(path)
            if selected_actions > maximum_actions:
                self._abort_selection(path, "maximum_actions_exceeded_during_selection", select_started); return
            if zero_count > maximum_zero:
                self._abort_selection(path, "consecutive_zero_combat_time_actions_exceeded_during_selection", select_started); return
            if bool(self.tree.terminal[node]):
                break
            legal = mask_to_slots(int(self.tree.legal_action_mask[node])); expanded_slots = [s for s in legal if self.tree.children[node, s] >= 0]
            if not legal:
                self._abort_selection(path, "no_legal_policy_action_at_tree_node", select_started); return
            limit = allowed_children(int(self.tree.visits[node]), len(legal))
            unexpanded = [s for s in legal if self.tree.children[node, s] < 0]
            if unexpanded and len(expanded_slots) < limit:
                if selected_actions >= maximum_actions:
                    self._abort_selection(path, "maximum_actions_exceeded_before_expansion", select_started); return
                fp = self.tree.full_state_fingerprint[node].decode("ascii")
                slot = min(unexpanded, key=lambda s: deterministic_action_rank(int(self.stage["seed"]), fp, self.action_ids[s]))
                simulation, replay_length = self.snapshots.restore_node(tree=self.tree, node_id=node, template=self.template, action_ids=self.action_ids,
                    action_executor=self._execute_slot)
                self.max_reconstruction_replay_length = max(self.max_reconstruction_replay_length, replay_length)
                self._record_phase("selection", time.perf_counter() - select_started)
                expansion_started = time.perf_counter(); before = float(simulation.state.combat_time)
                if not self._execute_slot(simulation, slot):
                    self._record_phase("expansion", time.perf_counter() - expansion_started)
                    self._abort_selection(path, "expansion_action_failed", None); return
                expanded_zero_count = zero_count + 1 if float(simulation.state.combat_time) <= before + 1e-12 else 0
                if expanded_zero_count > maximum_zero:
                    self._record_phase("expansion", time.perf_counter() - expansion_started)
                    self._abort_selection(path, "consecutive_zero_combat_time_actions_exceeded_after_expansion", None); return
                metrics = node_metrics(simulation); child_depth = int(self.tree.depth[node]) + 1
                snapshot_ref = self.snapshots.add(simulation) if child_depth % int(self.stage["snapshot_stride"]) == 0 else -1
                child = self.tree.add_node(parent_id=node, action_slot=slot, legal_slots=legal_policy_slots(simulation, self.action_ids),
                    terminal=_is_terminal(simulation, float(self.stage["combat_duration"])), invalid=False, snapshot_ref=snapshot_ref,
                    total_damage=float(metrics["total_damage"]), combat_time=float(metrics["combat_time"]), current_time=float(metrics["current_time"]),
                    full_fingerprint=str(metrics["full_fingerprint"]), future_fingerprint=str(metrics["future_fingerprint"]))
                self._record_fingerprint(str(metrics["full_fingerprint"]), str(metrics["future_fingerprint"]), float(metrics["total_damage"]))
                path.append(child); node = child; expanded = True; self.progressive_widening_expansions += 1
                self._record_phase("expansion", time.perf_counter() - expansion_started)
                zero_count = expanded_zero_count
                break
            node = self.tree.choose_child(node, legal, seed=int(self.stage["seed"]), action_ids=self.action_ids); path.append(node)
        self.selection_depths.append(len(path) - 1)
        if not expanded:
            simulation, replay_length = self.snapshots.restore_node(tree=self.tree, node_id=node, template=self.template, action_ids=self.action_ids,
                action_executor=self._execute_slot)
            self.max_reconstruction_replay_length = max(self.max_reconstruction_replay_length, replay_length)
            zero_count = self._selection_zero_tail(path)
            self._record_phase("selection", time.perf_counter() - select_started)
        action_count = len(path) - 1; rollout_slots: list[int] = []; contexts: list[tuple[str, int]] = []
        invalid_reason: str | None = None; rollout_started = time.perf_counter()
        while not _is_terminal(simulation, float(self.stage["combat_duration"])):
            if action_count >= maximum_actions: invalid_reason = "maximum_actions_exceeded"; break
            legal = legal_policy_slots(simulation, self.action_ids)
            if not legal: invalid_reason = "no_legal_policy_action"; break
            active = str(simulation.state.active_character_id)
            slot = self.mast.choose(active_character=active, legal_slots=legal, simulation_index=self.simulations, rng=self.rng,
                warmup=int(self.plan["mast"]["uniform_warmup_simulations"]), epsilon=float(self.plan["mast"]["epsilon"]),
                minimum_visits=int(self.plan["mast"]["minimum_visits"]))
            before = float(simulation.state.combat_time)
            if not self._execute_slot(simulation, slot): invalid_reason = "rollout_action_failed"; break
            action_count += 1; rollout_slots.append(slot); contexts.append((active, slot))
            zero_count = zero_count + 1 if float(simulation.state.combat_time) <= before + 1e-12 else 0
            if zero_count > maximum_zero: invalid_reason = "consecutive_zero_combat_time_actions_exceeded"; break
        self._record_phase("rollout", time.perf_counter() - rollout_started)
        self.rollout_action_counts.append(len(rollout_slots))
        completed = invalid_reason is None and _is_terminal(simulation, float(self.stage["combat_duration"]))
        reward = float(simulation.state.total_damage) / float(self.plan["reward"]["terminal_scale"]) if completed else 0.0
        back_started = time.perf_counter(); self.tree.backpropagate(path, reward, completed=completed)
        if completed:
            self.mast.update(contexts, reward); self._record_completed(node, rollout_slots, simulation)
        else: self._invalid(invalid_reason or "safety_stopped")
        self._record_phase("backpropagation", time.perf_counter() - back_started)

    def _abort_selection(self, path: list[int], reason: str, select_started: float | None) -> None:
        if select_started is not None:
            self._record_phase("selection", time.perf_counter() - select_started)
        self.selection_depths.append(len(path) - 1)
        self.rollout_action_counts.append(0)
        back_started = time.perf_counter()
        self.tree.backpropagate(path, 0.0, completed=False)
        self._invalid(reason)
        self._record_phase("backpropagation", time.perf_counter() - back_started)

    def _record_phase(self, name: str, seconds: float) -> None:
        elapsed = float(seconds)
        self.phase_seconds[name] += elapsed
        self.invocation_phase_seconds[name] += elapsed

    def _execute_slot(self, simulation: Any, slot: int) -> bool:
        action_id = self.action_ids[int(slot)]
        active = str(simulation.state.active_character_id)
        started = time.perf_counter()
        succeeded = execute_policy_slot(simulation, self.action_ids, int(slot))
        elapsed = time.perf_counter() - started
        self.total_action_executions += 1
        if elapsed > self._current_max_action_seconds:
            self._current_max_action_seconds = elapsed
            self._current_slowest_action_id = action_id
            self._current_slowest_action_active = active
        # Measure the retained diagnostic payload after the shared classifier's
        # lightweight cleanup.  The expected value is exactly zero; keeping this
        # as a measured invariant makes probe regressions visible.
        diagnostic_payload: dict[str, Any] = {}
        rows = 0
        for field in DIAGNOSTIC_ONLY_FIELDS:
            value = getattr(simulation.state, field)
            if isinstance(value, (list, dict, set)) and value:
                rows += len(value)
                diagnostic_payload[field] = value
        self.lightweight_diagnostic_log_rows = max(self.lightweight_diagnostic_log_rows, rows)
        if diagnostic_payload:
            self.lightweight_diagnostic_bytes = max(
                self.lightweight_diagnostic_bytes, len(canonical_json_bytes(diagnostic_payload))
            )
        return succeeded

    def _record_completed(self, node: int, rollout_slots: list[int], simulation: Any) -> None:
        selected_slots = self.tree.selected_slots(node) + rollout_slots
        selected = [self.action_ids[slot] for slot in selected_slots]; selected_hash = sequence_sha256(selected)
        record = {"route_id": selected_hash[:16], "total_damage": float(simulation.state.total_damage),
                  "dps": float(simulation.state.total_damage) / float(self.stage["combat_duration"]),
                  "combat_time": float(simulation.state.combat_time), "current_time": float(simulation.state.current_time),
                  "action_count": len(selected), "selected_sequence_sha256": selected_hash, "selected_sequence": selected,
                  "completion_simulation_index": self.simulations + 1}
        self.completed_rollout_count += 1
        if self.first_completed_rollout_simulation_index is None: self.first_completed_rollout_simulation_index = self.simulations + 1
        # Keep the leaderboard route-unique while retaining the independent
        # completed-rollout counter used by diagnostics and checkpoint resume.
        existing = next((item for item in self.completed_routes if item["selected_sequence_sha256"] == selected_hash), None)
        if existing is None:
            self.completed_routes.append(record)
        elif float(record["total_damage"]) > float(existing["total_damage"]):
            self.completed_routes[self.completed_routes.index(existing)] = record
        self.completed_routes.sort(key=lambda item: (-float(item["total_damage"]), item["selected_sequence_sha256"]))
        self.completed_routes = self.completed_routes[: int(self.stage["completed_route_leaderboard_size"])]

    def _record_fingerprint(self, full: str, future: str, damage: float) -> None:
        if full in self.full_seen: self.exact_full_state_duplicate_count += 1
        self.full_seen.add(full)
        if future in self.future_damage_seen and abs(self.future_damage_seen[future] - damage) > 1e-9:
            self.future_only_fingerprint_collision_count += 1
        self.future_damage_seen.setdefault(future, damage)

    def _selection_zero_tail(self, path: list[int]) -> int:
        count = 0
        for child in reversed(path[1:]):
            parent = int(self.tree.parent_id[child])
            if float(self.tree.combat_time[child]) <= float(self.tree.combat_time[parent]) + 1e-12: count += 1
            else: break
        return count

    def _invalid(self, reason: str) -> None:
        self.invalid_rollout_counts[reason] = self.invalid_rollout_counts.get(reason, 0) + 1

    def _save_checkpoint(self) -> None:
        assert self.snapshots is not None
        started = time.perf_counter(); self.checkpoint_count += 1
        counters = self._checkpoint_counters()
        invocation_elapsed = max(time.perf_counter() - self.started_at, 1e-9)
        counters["checkpoint_simulations_per_second"] = self.simulations / invocation_elapsed
        self.checkpoints.save(plan_path=self.plan_path, plan_sha256=self.plan_sha256, stage_hash=self.stage_hash,
            simulations=self.simulations, tree=self.tree, snapshots=self.snapshots, rng_state=self.rng.bit_generator.state,
            mast_counts=self.mast.counts, mast_value_sums=self.mast.value_sums, completed_routes=self.completed_routes,
            counters=counters)
        self.last_checkpoint_simulations = self.simulations
        self._record_phase("checkpoint", time.perf_counter() - started)

    def _checkpoint_counters(self) -> dict[str, Any]:
        return {"completed_rollout_count": self.completed_rollout_count, "first_completed_rollout_simulation_index": self.first_completed_rollout_simulation_index,
                "invalid_rollout_counts": self.invalid_rollout_counts, "total_action_executions": self.total_action_executions,
                "exact_full_state_duplicate_count": self.exact_full_state_duplicate_count, "future_only_fingerprint_collision_count": self.future_only_fingerprint_collision_count,
                "progressive_widening_expansions": self.progressive_widening_expansions, "checkpoint_count": self.checkpoint_count,
                "selection_depths": self.selection_depths, "rollout_action_counts": self.rollout_action_counts,
                "simulation_runtime_seconds": self.simulation_runtime_seconds,
                "slowest_simulation_index": self.slowest_simulation_index,
                "slowest_simulation_selection_depth": self.slowest_simulation_selection_depth,
                "slowest_simulation_rollout_action_count": self.slowest_simulation_rollout_action_count,
                "maximum_individual_action_execution_seconds": self.maximum_individual_action_execution_seconds,
                "slowest_action_id": self.slowest_action_id,
                "slowest_action_active_character": self.slowest_action_active_character,
                "lightweight_diagnostic_log_rows": self.lightweight_diagnostic_log_rows,
                "lightweight_diagnostic_bytes": self.lightweight_diagnostic_bytes,
                "max_reconstruction_replay_length": self.max_reconstruction_replay_length, "phase_seconds": self.phase_seconds,
                "memory": self.memory_breakdown(),
                "mast_choice_counters": self.mast.metrics()}

    def logical_result_sha256(self) -> str:
        digest = hashlib.sha256()
        for name, array in sorted(self.tree.arrays(used_only=True).items()):
            digest.update(name.encode()); digest.update(array.dtype.str.encode()); digest.update(array.shape.__repr__().encode()); digest.update(array.tobytes())
        digest.update(canonical_json_bytes(self.rng.bit_generator.state)); digest.update(self.mast.counts.tobytes()); digest.update(self.mast.value_sums.tobytes())
        compact_routes = [{k: v for k, v in route.items() if k != "completion_simulation_index"} for route in self.completed_routes]
        digest.update(canonical_json_bytes({"simulations": self.simulations, "completed_rollout_count": self.completed_rollout_count,
            "invalid_rollout_counts": self.invalid_rollout_counts, "routes": compact_routes, "mast_choices": self.mast.metrics()}))
        return digest.hexdigest()

    def memory_breakdown(self) -> dict[str, int]:
        assert self.snapshots is not None
        tree_bytes = self.tree.allocated_bytes(); snapshot_index = len(canonical_json_bytes(self.snapshots.index_payload()))
        mast = int(self.mast.counts.nbytes + self.mast.value_sums.nbytes); routes = len(canonical_json_bytes(self.completed_routes))
        scratch = int(self.stage["maximum_actions_per_simulation"]) * 4096
        tracked = sum(tree_bytes.values()) + snapshot_index + self.snapshots.compressed_bytes + self.snapshots.cache_bytes + mast + routes + scratch + self.peak_checkpoint_serialization_buffer
        return {**tree_bytes, "snapshot_index_bytes": snapshot_index, "snapshot_compressed_bytes": self.snapshots.compressed_bytes,
                "snapshot_decoded_cache_bytes": self.snapshots.cache_bytes, "mast_table_bytes": mast, "completed_route_bytes": routes,
                "selection_replay_rollout_scratch_bytes": scratch, "checkpoint_serialization_peak_buffer": self.peak_checkpoint_serialization_buffer,
                "process_peak_rss_bytes": max(self.peak_rss, process_peak_rss_bytes()), "tracked_bytes": tracked,
                "conservative_total_estimate_bytes": tracked * 2 + 64 * 1024 * 1024}

    def _result(self, status: str, elapsed: float) -> dict[str, Any]:
        self.peak_rss = max(self.peak_rss, process_peak_rss_bytes()); best = self.completed_routes[0] if self.completed_routes else None
        selection = _distribution(self.selection_depths); rollout = _distribution(self.rollout_action_counts)
        simulation_runtime = _runtime_distribution(self.simulation_runtime_seconds)
        invocation_phase_sum = sum(self.invocation_phase_seconds.values())
        return {"schema_version": "mcts_execution_result_v117", "algorithm": self.plan["algorithm"], "stage_id": self.stage["stage_id"],
            "seed": int(self.stage["seed"]), "termination_status": status, "simulations_requested": self.target_simulations,
            "simulations_completed": self.simulations, "first_completed_rollout_simulation_index": self.first_completed_rollout_simulation_index,
            "completed_rollout_count": self.completed_rollout_count, "invalid_rollout_count": sum(self.invalid_rollout_counts.values()),
            "invalid_rollout_counts": self.invalid_rollout_counts, "best_completed_route": best, "node_count": self.tree.node_count,
            "tree_maximum_depth": int(self.tree.depth[:self.tree.node_count].max(initial=0)), "tree_mean_depth": float(self.tree.depth[:self.tree.node_count].mean()),
            "selection_depth": selection, "rollout_action_count": rollout, "total_action_executions": self.total_action_executions,
            "elapsed_seconds": elapsed, "simulations_per_second": self.simulations / max(elapsed, 1e-9),
            "action_executions_per_second": self.total_action_executions / max(elapsed, 1e-9),
            "phase_seconds": self.phase_seconds, "cumulative_phase_seconds": self.phase_seconds,
            "invocation_phase_seconds": self.invocation_phase_seconds,
            "invocation_other_overhead_seconds": max(0.0, elapsed - invocation_phase_sum),
            "phase_time_accounting": "mutually_exclusive_v118",
            "simulation_runtime_seconds": simulation_runtime,
            "slowest_simulation_index": self.slowest_simulation_index,
            "slowest_simulation_selection_depth": self.slowest_simulation_selection_depth,
            "slowest_simulation_rollout_action_count": self.slowest_simulation_rollout_action_count,
            "maximum_individual_action_execution_seconds": self.maximum_individual_action_execution_seconds,
            "slowest_action_id": self.slowest_action_id,
            "slowest_action_active_character": self.slowest_action_active_character,
            "lightweight_diagnostic_log_rows": self.lightweight_diagnostic_log_rows,
            "lightweight_diagnostic_bytes": self.lightweight_diagnostic_bytes,
            "uct_root_child_coverage": int(np.count_nonzero(self.tree.children[0] >= 0)), "progressive_widening_expansions": self.progressive_widening_expansions,
            **self.mast.metrics(), "exact_full_state_duplicate_count": self.exact_full_state_duplicate_count,
            "future_only_fingerprint_collision_diagnostic_count": self.future_only_fingerprint_collision_count,
            "snapshot_metrics": self.snapshots.index_payload() if self.snapshots else {}, "checkpoint_count": self.checkpoint_count,
            "memory": self.memory_breakdown(), "max_snapshot_reconstruction_replay_length": self.max_reconstruction_replay_length,
            "logical_result_sha256": self.logical_result_sha256(), "rng_final_state_sha256": hashlib.sha256(canonical_json_bytes(self.rng.bit_generator.state)).hexdigest(),
            "mast_logical_sha256": hashlib.sha256(self.mast.counts.tobytes() + self.mast.value_sums.tobytes()).hexdigest(),
            "resume_checkpoint_source": self.resume_checkpoint_source,
            "resume_checkpoint_fallback_reason": self.resume_checkpoint_fallback_reason,
            "normal_process_exit": True, "global_optimum_proven": False}

    def _log(self, message: str) -> None:
        log = self.output_root / "logs" / f"{self.stage['stage_id']}.log"; log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as file: file.write(message + "\n")


def _is_terminal(simulation: Any, duration: float) -> bool:
    return abs(float(simulation.state.combat_time) - float(duration)) <= 1e-9


def _distribution(values: list[int]) -> dict[str, float | int]:
    if not values: return {"mean": 0.0, "p50": 0.0, "p95": 0.0, "max": 0}
    array = np.asarray(values, dtype=np.float64)
    return {"mean": float(array.mean()), "p50": float(np.percentile(array, 50)), "p95": float(np.percentile(array, 95)), "max": int(array.max())}


def _runtime_distribution(values: list[float]) -> dict[str, float]:
    if not values: return {"mean": 0.0, "p50": 0.0, "p95": 0.0, "max": 0.0}
    array = np.asarray(values, dtype=np.float64)
    return {"mean": float(array.mean()), "p50": float(np.percentile(array, 50)),
            "p95": float(np.percentile(array, 95)), "max": float(array.max())}
