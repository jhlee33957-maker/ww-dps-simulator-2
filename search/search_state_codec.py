from __future__ import annotations

import copy
import ctypes
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from characters.registry import get_mechanics_for_characters
from simulator.models import CombatState
from simulator.resource_system import ensure_concerto_state
from simulator.simulation import Simulation


OBJECTIVE_ONLY_FIELDS = {
    "total_damage", "wasted_resonance_energy", "wasted_concerto_energy",
    "off_tune_accumulated_total", "off_tune_overflow", "tune_break_damage_total",
    "interfered_marker_direct_damage_amp_bonus_damage_total", "tune_response_damage_total",
    "aemeath_starburst_damage_total", "mornye_particle_jet_damage_total",
    "lynae_spectral_analysis_damage_total", "tune_response_events",
    "enemy_mistune_entered_count", "off_tune_accumulation_blocked_by_tune_break_cooldown_count",
    "interfered_marker_applied_count", "interfered_marker_direct_damage_amp_applied_action_count",
    "aemeath_starburst_trigger_count", "mornye_particle_jet_trigger_count",
    "lynae_spectral_analysis_trigger_count", "aemeath_starburst_cooldown_blocked_count",
    "mornye_particle_jet_cooldown_blocked_count", "lynae_spectral_analysis_cooldown_blocked_count",
    "tune_break_action_used_count", "starfield_calibrator_concerto_restored_total",
}
DIAGNOSTIC_ONLY_FIELDS = {
    "action_log", "damage_log", "mechanic_event_log", "scheduled_effect_event_log",
    "off_tune_accumulation_logs", "party_response_scan_logs", "weapon_effect_logs",
    "echo_set_buff_windows", "high_syntony_field_buff_windows", "weapon_effect_buff_windows",
    "rupturous_trail_event_log", "simplified_assumptions", "mapped_off_tune_action_count",
    "unmapped_off_tune_action_ids", "unresolved_off_tune_damaging_action_ids",
    "off_tune_mapping_completeness_status", "off_tune_value_mapping_source_report",
    "enemy_tune_break_cooldown_source_status", "enemy_tune_break_cooldown_source_ref",
    "tune_response_damage_formula_source_status", "tune_response_event_order_source_status",
    "unresolved_response_damage_events",
}
DERIVED_ALIAS_FIELDS = {"character_states"}
FUTURE_AFFECTING_FIELDS = set(CombatState.model_fields) - OBJECTIVE_ONLY_FIELDS - DIAGNOSTIC_ONLY_FIELDS
COMPACT_STATE_FIELDS = (FUTURE_AFFECTING_FIELDS | {"total_damage"}) - DERIVED_ALIAS_FIELDS
COMBAT_STATE_FIELD_CLASSIFICATION = {
    **{name: "future_affecting" for name in sorted(FUTURE_AFFECTING_FIELDS)},
    **{name: "objective_only" for name in sorted(OBJECTIVE_ONLY_FIELDS)},
    **{name: "diagnostic_only" for name in sorted(DIAGNOSTIC_ONLY_FIELDS)},
}
OMITTED_CLONE_FIELDS = {
    "timeline": "Historical timeline rows are omitted from search clones because future simulator behavior is driven by CombatState and immutable action/config data.",
}
OMITTED_STATE_FIELDS = {
    name: "Diagnostic or historical log state is omitted from canonical search-node payloads and restored to CombatState defaults; these fields are excluded from future-state fingerprints."
    for name in sorted(DIAGNOSTIC_ONLY_FIELDS)
}
OMITTED_STATE_FIELDS.update({
    name: "Objective/reporting-only accumulated state is omitted from canonical search-node payloads except total_damage; route summaries replay the selected route from the verified initial state."
    for name in sorted(OBJECTIVE_ONLY_FIELDS - {"total_damage"})
})
OMITTED_STATE_FIELDS["character_states"] = (
    "character_states is not serialized separately because normal Simulation aliases it to "
    "character_mechanics_state; restore reconstructs the alias with the same dictionary object."
)


def canonicalize(value: Any) -> Any:
    if isinstance(value, float):
        return value.hex()
    if isinstance(value, dict):
        return {str(key): canonicalize(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [canonicalize(item) for item in value]
    return value


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(canonicalize(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def state_payload_sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def assert_combat_state_classification_complete() -> None:
    fields = set(CombatState.model_fields)
    classified = set(COMBAT_STATE_FIELD_CLASSIFICATION)
    if fields != classified:
        raise AssertionError(
            f"CombatState field classification mismatch: missing={sorted(fields-classified)}, extra={sorted(classified-fields)}"
        )


def assert_search_state_invariants(state: CombatState) -> None:
    if state.character_states is not state.character_mechanics_state:
        raise AssertionError("CombatState character_states must alias character_mechanics_state")
    for character_id in state.party_members:
        character_state = state.character_mechanics_state.setdefault(character_id, {})
        if character_id in state.concerto_energy:
            ensure_concerto_state(character_state, energy=state.concerto_energy[character_id])
            if abs(float(character_state["concerto_energy"]) - float(state.concerto_energy[character_id])) > 1e-9:
                raise AssertionError(f"Concerto state desynchronized for {character_id}")
        else:
            ensure_concerto_state(character_state)
            state.concerto_energy[character_id] = float(character_state["concerto_energy"])


def compact_combat_state_payload(state: CombatState, *, include_objective: bool) -> dict[str, Any]:
    assert_combat_state_classification_complete()
    raw = state.model_dump(mode="json")
    fields = COMPACT_STATE_FIELDS if include_objective else (COMPACT_STATE_FIELDS - OBJECTIVE_ONLY_FIELDS)
    return {name: raw[name] for name in sorted(fields)}


def restore_combat_state_from_search_payload(payload: dict[str, Any]) -> CombatState:
    state = CombatState.model_validate(payload)
    state.character_states = state.character_mechanics_state
    assert_search_state_invariants(state)
    return state


def clone_simulation_for_search(simulation: Simulation, *, omit_history: bool = True) -> Simulation:
    clone = copy.copy(simulation)
    clone.state = restore_combat_state_from_search_payload(compact_combat_state_payload(simulation.state, include_objective=True))
    clone.character_mechanics = get_mechanics_for_characters(list(simulation.selected_character_ids))
    clone.timeline = [] if omit_history else copy.deepcopy(simulation.timeline)
    return clone


def clear_search_diagnostics(simulation: Simulation) -> None:
    """Reset only fields classified as diagnostic/history for state search."""
    for name in DIAGNOSTIC_ONLY_FIELDS:
        value = getattr(simulation.state, name)
        if isinstance(value, (list, dict, set)):
            value.clear()
    simulation.timeline.clear()


def execute_action_for_search(simulation: Simulation, action_id: str) -> bool:
    """Execute exact mechanics without retaining report-only history."""
    succeeded = bool(simulation.execute_action(action_id, record_diagnostics=False))
    clear_search_diagnostics(simulation)
    return succeeded


def serialize_simulation_state(simulation: Simulation) -> dict[str, Any]:
    return {
        "schema_version": "beam_search_simulation_state_v111_compact",
        "combat_duration": simulation.combat_duration,
        "state": compact_combat_state_payload(simulation.state, include_objective=True),
        "omitted_fields": {**OMITTED_CLONE_FIELDS, **OMITTED_STATE_FIELDS},
    }


def restore_simulation_from_state(template: Simulation, payload: dict[str, Any]) -> Simulation:
    if payload.get("schema_version") not in {"beam_search_simulation_state_v111", "beam_search_simulation_state_v111_compact"}:
        raise ValueError(f"Unsupported serialized simulation schema: {payload.get('schema_version')!r}")
    clone = clone_simulation_for_search(template)
    clone.combat_duration = float(payload["combat_duration"])
    # Snapshot payloads are cached and must remain immutable.  Pydantic may retain
    # references to nested values supplied to model_validate, so a shallow copy
    # here lets a restored Simulation corrupt later restores of the same snapshot.
    state_payload = copy.deepcopy(payload["state"])
    state_payload["combat_duration"] = clone.combat_duration
    clone.state = restore_combat_state_from_search_payload(state_payload)
    clone.timeline = []
    return clone


def future_state_payload(simulation: Simulation) -> dict[str, Any]:
    return compact_combat_state_payload(simulation.state, include_objective=False)


def future_state_fingerprint(simulation: Simulation) -> str:
    return state_payload_sha256(future_state_payload(simulation))


def full_node_state_fingerprint(simulation: Simulation) -> str:
    return state_payload_sha256(compact_combat_state_payload(simulation.state, include_objective=True))


def state_payload_size_bytes(simulation: Simulation) -> int:
    return len(canonical_json_bytes(serialize_simulation_state(simulation)))


def sequence_sha256(sequence: list[str] | tuple[str, ...]) -> str:
    return hashlib.sha256(json.dumps(list(sequence), separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def process_peak_rss_bytes() -> int:
    if os.name == "nt":
        class Counters(ctypes.Structure):
            _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong), ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t)]
        counters = Counters(); counters.cb = ctypes.sizeof(counters)
        try:
            get_current_process = ctypes.windll.kernel32.GetCurrentProcess
            get_current_process.restype = ctypes.c_void_p
            get_process_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
            get_process_memory_info.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
            get_process_memory_info.restype = ctypes.c_int
            handle = get_current_process()
            if get_process_memory_info(handle, ctypes.byref(counters), counters.cb):
                return int(counters.PeakWorkingSetSize)
        except (AttributeError, OSError):
            return 0
    try:
        import resource
        peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        return peak if getattr(os, "uname", lambda: type("U", (), {"sysname": ""})())().sysname == "Darwin" else peak * 1024
    except (AttributeError, ImportError, OSError):
        return 0


def sha256_file(path: Path, *, length: int | None = None) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        remaining = length
        while True:
            size = 1024 * 1024 if remaining is None else min(1024 * 1024, remaining)
            if size <= 0:
                break
            chunk = file.read(size)
            if not chunk:
                break
            digest.update(chunk)
            if remaining is not None:
                remaining -= len(chunk)
    if length is not None and remaining != 0:
        raise ValueError(f"File shorter than committed prefix: {path}")
    return digest.hexdigest()
