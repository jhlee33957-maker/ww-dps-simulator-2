from __future__ import annotations

import copy
import gzip
import hashlib
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from characters.registry import get_mechanics_for_characters
from simulator.models import CombatState
from simulator.resource_system import ensure_concerto_state
from simulator.simulation import Simulation


OBJECTIVE_ONLY_FIELDS = {
    "total_damage",
    "wasted_resonance_energy",
    "wasted_concerto_energy",
    "off_tune_accumulated_total",
    "off_tune_overflow",
    "tune_break_damage_total",
    "interfered_marker_direct_damage_amp_bonus_damage_total",
    "tune_response_damage_total",
    "aemeath_starburst_damage_total",
    "mornye_particle_jet_damage_total",
    "lynae_spectral_analysis_damage_total",
    "tune_response_events",
    "enemy_mistune_entered_count",
    "off_tune_accumulation_blocked_by_tune_break_cooldown_count",
    "interfered_marker_applied_count",
    "interfered_marker_direct_damage_amp_applied_action_count",
    "aemeath_starburst_trigger_count",
    "mornye_particle_jet_trigger_count",
    "lynae_spectral_analysis_trigger_count",
    "aemeath_starburst_cooldown_blocked_count",
    "mornye_particle_jet_cooldown_blocked_count",
    "lynae_spectral_analysis_cooldown_blocked_count",
    "tune_break_action_used_count",
    "starfield_calibrator_concerto_restored_total",
}
DIAGNOSTIC_ONLY_FIELDS = {
    "action_log",
    "damage_log",
    "mechanic_event_log",
    "scheduled_effect_event_log",
    "off_tune_accumulation_logs",
    "party_response_scan_logs",
    "weapon_effect_logs",
    "echo_set_buff_windows",
    "high_syntony_field_buff_windows",
    "weapon_effect_buff_windows",
    "rupturous_trail_event_log",
    "simplified_assumptions",
    "mapped_off_tune_action_count",
    "unmapped_off_tune_action_ids",
    "unresolved_off_tune_damaging_action_ids",
    "off_tune_mapping_completeness_status",
    "off_tune_value_mapping_source_report",
    "enemy_tune_break_cooldown_source_status",
    "enemy_tune_break_cooldown_source_ref",
    "tune_response_damage_formula_source_status",
    "tune_response_event_order_source_status",
    "unresolved_response_damage_events",
}

# character_states is a runtime alias of character_mechanics_state. It is classified
# as future-affecting but persisted once through character_mechanics_state, then
# reconstructed as the identical dictionary object on clone/restore.
DERIVED_ALIAS_FIELDS = {"character_states"}
FUTURE_AFFECTING_FIELDS = set(CombatState.model_fields) - OBJECTIVE_ONLY_FIELDS - DIAGNOSTIC_ONLY_FIELDS
COMPACT_STATE_FIELDS = (FUTURE_AFFECTING_FIELDS | {"total_damage"}) - DERIVED_ALIAS_FIELDS

COMBAT_STATE_FIELD_CLASSIFICATION: dict[str, str] = {
    **{field_name: "future_affecting" for field_name in sorted(FUTURE_AFFECTING_FIELDS)},
    **{field_name: "objective_only" for field_name in sorted(OBJECTIVE_ONLY_FIELDS)},
    **{field_name: "diagnostic_only" for field_name in sorted(DIAGNOSTIC_ONLY_FIELDS)},
}

COMBAT_STATE_FIELD_AUDIT: dict[str, dict[str, Any]] = {
    field_name: {
        "classification": COMBAT_STATE_FIELD_CLASSIFICATION[field_name],
        "future_input_source_read_audit": (
            "writes_or_final_summary_reads_only"
            if field_name in OBJECTIVE_ONLY_FIELDS - {"total_damage"}
            else "diagnostic_log_or_metadata_only"
            if field_name in DIAGNOSTIC_ONLY_FIELDS
            else "retained_future_input_or_unproven_reporting_only"
        ),
        "action_availability_input": field_name in FUTURE_AFFECTING_FIELDS,
        "transition_selection_input": field_name in FUTURE_AFFECTING_FIELDS,
        "damage_formula_input": field_name in FUTURE_AFFECTING_FIELDS,
        "cooldown_resource_update_input": field_name in FUTURE_AFFECTING_FIELDS,
        "scheduled_effect_behavior_input": field_name in FUTURE_AFFECTING_FIELDS,
        "mechanic_hook_input": field_name in FUTURE_AFFECTING_FIELDS,
    }
    for field_name in sorted(COMBAT_STATE_FIELD_CLASSIFICATION)
}

OMITTED_CLONE_FIELDS = {
    "timeline": "Historical timeline rows are omitted from search clones because future simulator behavior is driven by CombatState and immutable action/config data.",
}
OMITTED_STATE_FIELDS = {
    field_name: "Diagnostic or historical log state is omitted from canonical search-node payloads and restored to CombatState defaults; these fields are excluded from future-state fingerprints."
    for field_name in sorted(DIAGNOSTIC_ONLY_FIELDS)
}
OMITTED_STATE_FIELDS.update(
    {
        field_name: "Objective/reporting-only accumulated state is omitted from canonical search-node payloads except total_damage; route summaries replay the selected route from the verified initial state."
        for field_name in sorted(OBJECTIVE_ONLY_FIELDS - {"total_damage"})
    }
)
OMITTED_STATE_FIELDS["character_states"] = (
    "character_states is not serialized separately because normal Simulation aliases it to "
    "character_mechanics_state; restore reconstructs the alias with the same dictionary object."
)


def assert_combat_state_classification_complete() -> None:
    fields = set(CombatState.model_fields)
    classified = set(COMBAT_STATE_FIELD_CLASSIFICATION)
    missing = sorted(fields - classified)
    extra = sorted(classified - fields)
    if missing or extra:
        raise AssertionError(f"CombatState field classification mismatch: missing={missing}, extra={extra}")


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


def _restore_alias_and_invariants(state: CombatState) -> CombatState:
    state.character_states = state.character_mechanics_state
    assert_search_state_invariants(state)
    return state


def clone_simulation_for_search(simulation: Simulation, *, omit_history: bool = True) -> Simulation:
    clone = copy.copy(simulation)
    clone.state = restore_combat_state_from_search_payload(
        compact_combat_state_payload(simulation.state, include_objective=True)
    )
    clone.character_mechanics = get_mechanics_for_characters(list(simulation.selected_character_ids))
    clone.timeline = [] if omit_history else copy.deepcopy(simulation.timeline)
    assert_search_state_invariants(clone.state)
    return clone


def compact_combat_state_payload(state: CombatState, *, include_objective: bool) -> dict[str, Any]:
    assert_combat_state_classification_complete()
    raw = state.model_dump(mode="json")
    fields = COMPACT_STATE_FIELDS if include_objective else (COMPACT_STATE_FIELDS - OBJECTIVE_ONLY_FIELDS)
    payload = {field_name: raw[field_name] for field_name in sorted(fields)}
    return payload


def restore_combat_state_from_search_payload(payload: dict[str, Any]) -> CombatState:
    state = CombatState.model_validate(payload)
    return _restore_alias_and_invariants(state)


def serialize_simulation_state(simulation: Simulation) -> dict[str, Any]:
    return {
        "schema_version": "beam_search_simulation_state_v111_compact",
        "combat_duration": simulation.combat_duration,
        "state": compact_combat_state_payload(simulation.state, include_objective=True),
        "omitted_fields": {**OMITTED_CLONE_FIELDS, **OMITTED_STATE_FIELDS},
    }


def restore_simulation_from_state(template: Simulation, payload: dict[str, Any]) -> Simulation:
    if payload.get("schema_version") not in {
        "beam_search_simulation_state_v111",
        "beam_search_simulation_state_v111_compact",
    }:
        raise ValueError(f"Unsupported serialized simulation schema: {payload.get('schema_version')!r}")
    clone = clone_simulation_for_search(template)
    clone.combat_duration = float(payload["combat_duration"])
    state_payload = dict(payload["state"])
    state_payload["combat_duration"] = clone.combat_duration
    clone.state = restore_combat_state_from_search_payload(state_payload)
    clone.timeline = []
    return clone


def write_json_gz(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    temp = path.with_name(path.name + ".tmp")
    with gzip.open(temp, "wb") as file:
        file.write(data)
    os.replace(temp, path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json_gz(path: Path, expected_sha256: str | None = None) -> dict[str, Any]:
    if expected_sha256 is not None and hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError(f"Frontier checkpoint hash mismatch: {path}")
    with gzip.open(path, "rb") as file:
        return json.loads(file.read().decode("utf-8"))


def future_state_payload(simulation: Simulation) -> dict[str, Any]:
    return compact_combat_state_payload(simulation.state, include_objective=False)


def future_state_fingerprint(simulation: Simulation) -> str:
    payload = future_state_payload(simulation)
    canonical = json.dumps(_canonicalize(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def state_payload_sha256(payload: dict[str, Any]) -> str:
    data = json.dumps(_canonicalize(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def state_payload_size_bytes(simulation: Simulation) -> int:
    return len(
        json.dumps(
            _canonicalize(serialize_simulation_state(simulation)),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    )


def diversity_key(simulation: Simulation) -> str:
    state = simulation.state
    parts = [
        f"active={state.active_character_id}",
        f"combat={_band(state.combat_time, 5.0)}",
        f"offtune={_band(state.enemy_off_tune_current / max(state.enemy_off_tune_max, 1.0), 0.25)}",
        f"mistune={int(state.enemy_mistune_active)}",
        f"tbreak={int(state.enemy_tune_break_available)}",
        f"tbreak_cd_ready={int(state.enemy_tune_break_cooldown_remaining <= 1e-9)}",
        f"interfered={_band(state.interfered_marker_remaining, 5.0)}",
        f"strain={state.target_tune_strain_interfered_stacks}:{_band(state.target_tune_strain_interfered_remaining, 5.0)}",
        f"trail={_band(float(state.rupturous_trail_stacks), 10.0)}",
        f"sched={_scheduled_effect_signature(state.scheduled_effects)}",
        f"buffs={_active_buff_signature(state.active_buffs, state.team_buffs)}",
        f"cooldowns={_cooldown_ready_signature(state.cooldowns)}",
    ]
    for character_id in sorted(state.party_members):
        parts.append(f"{character_id}:res={_band(state.resonance_energy.get(character_id, 0.0), 25.0)}")
        parts.append(f"{character_id}:conc={_band(state.concerto_energy.get(character_id, 0.0), 25.0)}")
        mech = state.character_mechanics_state.get(character_id, {})
        for key in _declared_mechanic_keys(character_id):
            if key in mech:
                parts.append(f"{character_id}:{key}={_mechanic_value(character_id, key, mech[key])}")
    return "|".join(parts)


def diversity_quantization_contract() -> dict[str, Any]:
    mechanic_field_encoders = _declared_mechanic_field_encoders()
    return {
        "combat_time_bucket_seconds": 5.0,
        "resonance_energy_band_points": 25.0,
        "concerto_energy_band_points": 25.0,
        "enemy_off_tune_ratio_band": 0.25,
        "rupturous_trail_stack_band": 10.0,
        "mechanic_remaining_seconds_band": 5.0,
        "mechanic_stack_band": 5.0,
        "cooldown_ready_boundary_seconds": 0.0,
        "scheduled_effect_phase_band_seconds": 0.5,
        "scheduled_effect_remaining_band_seconds": 1.0,
        "active_buff_remaining_band_seconds": 1.0,
        "scheduled_effect_signature_cap": 8,
        "buff_signature_cap": 12,
        "combo_and_forced_stage_encoding": "exact_categorical",
        "route_blind": True,
        "declared_character_mechanic_fields": {
            "aemeath": [
                "form",
                "aemeath_combo_stage",
                "mech_combo_stage",
                "synchronization_rate",
                "resonance_rate",
                "instant_response",
                "finale_available",
                "sync_strike_window_remaining",
                "overdrive_form_switch_window_remaining",
                "forte_enhancement_stacks",
                "forte_enhancement_remaining",
                "trail_no_cost_remaining",
            ],
            "mornye": [
                "mode",
                "baseline_combo_stage",
                "wfo_combo_stage",
                "rest_mass_energy",
                "relative_momentum",
                "syntony_field_remaining",
                "high_syntony_field_remaining",
                "observation_marker_active",
                "observation_marker_remaining",
            ],
            "lynae": [
                "overflow",
                "lumiflow",
                "true_color",
                "basic_combo_stage",
                "kaleidoscopic_combo_stage",
                "lynae_resonance_mode",
                "next_basic_forced_stage",
                "spray_paint_window_remaining",
                "visual_impact_cooldown_remaining",
                "to_vivid_tomorrow_window_remaining",
                "target_tune_shift_remaining",
            ],
        },
        "declared_mechanic_field_encoders": mechanic_field_encoders,
    }


def _declared_mechanic_field_encoders() -> dict[str, dict[str, dict[str, Any]]]:
    return {
        "aemeath": {
            "form": {"encoder": "categorical_exact"},
            "aemeath_combo_stage": {"encoder": "integer_exact"},
            "mech_combo_stage": {"encoder": "integer_exact"},
            "synchronization_rate": {"encoder": "resource_band", "band": 25.0},
            "resonance_rate": {"encoder": "resource_band", "band": 25.0},
            "instant_response": {"encoder": "boolean_exact"},
            "finale_available": {"encoder": "boolean_exact"},
            "sync_strike_window_remaining": {"encoder": "active_remaining_band", "band": 0.5},
            "overdrive_form_switch_window_remaining": {"encoder": "active_remaining_band", "band": 0.5},
            "forte_enhancement_stacks": {"encoder": "integer_exact"},
            "forte_enhancement_remaining": {"encoder": "active_remaining_band", "band": 1.0},
            "trail_no_cost_remaining": {"encoder": "active_remaining_band", "band": 1.0},
        },
        "mornye": {
            "mode": {"encoder": "categorical_exact"},
            "baseline_combo_stage": {"encoder": "integer_exact"},
            "wfo_combo_stage": {"encoder": "integer_exact"},
            "rest_mass_energy": {"encoder": "resource_band", "band": 25.0},
            "relative_momentum": {"encoder": "resource_band", "band": 25.0},
            "syntony_field_remaining": {"encoder": "active_remaining_band", "band": 5.0},
            "high_syntony_field_remaining": {"encoder": "active_remaining_band", "band": 5.0},
            "observation_marker_active": {"encoder": "boolean_exact"},
            "observation_marker_remaining": {"encoder": "active_remaining_band", "band": 1.0},
        },
        "lynae": {
            "overflow": {"encoder": "resource_band", "band": 25.0},
            "lumiflow": {"encoder": "resource_band", "band": 25.0},
            "true_color": {"encoder": "integer_exact"},
            "basic_combo_stage": {"encoder": "integer_exact"},
            "kaleidoscopic_combo_stage": {"encoder": "integer_exact"},
            "lynae_resonance_mode": {"encoder": "categorical_exact"},
            "next_basic_forced_stage": {"encoder": "categorical_exact"},
            "spray_paint_window_remaining": {"encoder": "active_remaining_band", "band": 1.0},
            "visual_impact_cooldown_remaining": {"encoder": "cooldown_ready_remaining_band", "band": 1.0},
            "to_vivid_tomorrow_window_remaining": {"encoder": "active_remaining_band", "band": 1.0},
            "target_tune_shift_remaining": {"encoder": "active_remaining_band", "band": 1.0},
        },
    }


# Candidate 117 neutralizes the generic simulator codec while preserving every
# Beam schema/fingerprint through these backward-compatible re-exports.
from search.search_state_codec import (  # noqa: E402
    COMBAT_STATE_FIELD_CLASSIFICATION,
    COMPACT_STATE_FIELDS,
    DIAGNOSTIC_ONLY_FIELDS,
    FUTURE_AFFECTING_FIELDS,
    OBJECTIVE_ONLY_FIELDS,
    assert_combat_state_classification_complete,
    assert_search_state_invariants,
    clone_simulation_for_search,
    compact_combat_state_payload,
    future_state_fingerprint,
    future_state_payload,
    restore_combat_state_from_search_payload,
    restore_simulation_from_state,
    serialize_simulation_state,
    state_payload_sha256,
    state_payload_size_bytes,
)


@dataclass(slots=True)
class BeamNode:
    node_id: int
    parent_id: int | None
    selected_action_id: str | None
    resolved_action_id: str | None
    action_count: int
    total_damage: float
    combat_time: float
    current_time: float
    state_payload: dict[str, Any]
    future_fingerprint: str
    diversity_key: str
    complete: bool = False
    route_id: str | None = None
    selected_sequence_sha256: str | None = None
    resolved_sequence_sha256: str | None = None
    lineage_tie_key: str | None = None
    payload_size_bytes: int = 0

    def to_json(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "parent_id": self.parent_id,
            "selected_action_id": self.selected_action_id,
            "resolved_action_id": self.resolved_action_id,
            "action_count": self.action_count,
            "total_damage": self.total_damage,
            "combat_time": self.combat_time,
            "current_time": self.current_time,
            "state_payload": self.state_payload,
            "future_fingerprint": self.future_fingerprint,
            "diversity_key": self.diversity_key,
            "complete": self.complete,
            "route_id": self.route_id,
            "selected_sequence_sha256": self.selected_sequence_sha256,
            "resolved_sequence_sha256": self.resolved_sequence_sha256,
            "lineage_tie_key": self.lineage_tie_key,
            "payload_size_bytes": self.payload_size_bytes,
        }

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> "BeamNode":
        return cls(
            node_id=int(payload["node_id"]),
            parent_id=payload.get("parent_id"),
            selected_action_id=payload.get("selected_action_id"),
            resolved_action_id=payload.get("resolved_action_id"),
            action_count=int(payload["action_count"]),
            total_damage=float(payload["total_damage"]),
            combat_time=float(payload["combat_time"]),
            current_time=float(payload["current_time"]),
            state_payload=payload["state_payload"],
            future_fingerprint=payload["future_fingerprint"],
            diversity_key=payload["diversity_key"],
            complete=bool(payload.get("complete", False)),
            route_id=payload.get("route_id"),
            selected_sequence_sha256=payload.get("selected_sequence_sha256"),
            resolved_sequence_sha256=payload.get("resolved_sequence_sha256"),
            lineage_tie_key=payload.get("lineage_tie_key"),
            payload_size_bytes=int(payload.get("payload_size_bytes", 0)),
        )


def make_node(
    *,
    simulation: Simulation,
    node_id: int,
    parent: BeamNode | None = None,
    selected_action_id: str | None = None,
    resolved_action_id: str | None = None,
) -> BeamNode:
    action_count = 0 if parent is None else parent.action_count + (1 if selected_action_id is not None else 0)
    complete = simulation.state.combat_time >= simulation.combat_duration
    state_payload = serialize_simulation_state(simulation)
    payload_size = len(
        json.dumps(
            _canonicalize(state_payload),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    )
    node = BeamNode(
        node_id=node_id,
        parent_id=None if parent is None else parent.node_id,
        selected_action_id=selected_action_id,
        resolved_action_id=resolved_action_id,
        action_count=action_count,
        total_damage=float(simulation.state.total_damage),
        combat_time=float(simulation.state.combat_time),
        current_time=float(simulation.state.current_time),
        state_payload=state_payload,
        future_fingerprint=future_state_fingerprint(simulation),
        diversity_key=diversity_key(simulation),
        complete=complete,
        lineage_tie_key=lineage_tie_sha256(
            None if parent is None else parent.lineage_tie_key,
            selected_action_id,
            resolved_action_id,
        ),
        payload_size_bytes=payload_size,
    )
    return node


def sequence_sha256(sequence: tuple[str, ...] | list[str]) -> str:
    return hashlib.sha256(json.dumps(list(sequence), separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def lineage_tie_sha256(parent_lineage_tie_key: str | None, selected_action_id: str | None, resolved_action_id: str | None) -> str:
    payload = {
        "parent": parent_lineage_tie_key or "root",
        "selected_action_id": selected_action_id or "",
        "resolved_action_id": resolved_action_id or "",
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _declared_mechanic_keys(character_id: str) -> list[str]:
    return diversity_quantization_contract()["declared_character_mechanic_fields"].get(character_id, [])


def _scheduled_effect_signature(effects: list[Any]) -> str:
    items: list[str] = []
    for effect in effects:
        data = effect.model_dump(mode="json") if hasattr(effect, "model_dump") else dict(effect)
        identity = data.get("effect_id") or "unknown"
        source = data.get("source_character_id") or "none"
        payload = data.get("payload_action_id") or "none"
        remaining = data.get("remaining_duration", 0.0)
        phase = data.get("time_until_next_tick", 0.0)
        interval = data.get("tick_interval", 0.0)
        trigger_count = data.get("trigger_count", 0)
        max_count = data.get("max_trigger_count")
        event_type = data.get("payload_event_type", "damage")
        resource_policy = data.get("scheduled_resource_policy", "none")
        items.append(
            f"{identity}:{source}:{payload}:rem={_band(float(remaining or 0.0), 1.0)}:"
            f"phase={_band(float(phase or 0.0), 0.5)}:interval={_band(float(interval or 0.0), 0.5)}:count={trigger_count}/{max_count}:"
            f"type={event_type}:resource={resource_policy}"
        )
    return ",".join(sorted(items)[:8])


def _active_buff_signature(*buff_groups: list[Any]) -> str:
    ids: set[str] = set()
    for group in buff_groups:
        for buff in group:
            data = buff.model_dump(mode="json") if hasattr(buff, "model_dump") else dict(buff)
            buff_id = data.get("buff_id") or data.get("id") or data.get("name")
            source = data.get("source_character_id") or "none"
            target = data.get("target_character_id") or "party"
            remaining = data.get("remaining_duration", 0.0)
            stack_count = data.get("stack_count", 1)
            ids.add(f"{buff_id}:{source}:{target}:rem={_band(float(remaining or 0.0), 1.0)}:stack={stack_count}")
    return ",".join(sorted(ids)[:12])


def _cooldown_ready_signature(cooldowns: dict[str, float]) -> str:
    return ",".join(f"{key}:{int(float(value) <= 1e-9)}" for key, value in sorted(cooldowns.items()))


def _band(value: float, width: float) -> int:
    return int(math.floor(float(value) / float(width)))


def _coarse_value(value: Any) -> str:
    if isinstance(value, bool):
        return str(int(value))
    if isinstance(value, (int, float)):
        return str(_band(float(value), 5.0))
    if value is None:
        return "none"
    return str(value)


def _mechanic_value(character_id: str, key: str, value: Any) -> str:
    if value is None:
        return "none"
    spec = diversity_quantization_contract()["declared_mechanic_field_encoders"].get(character_id, {}).get(key)
    if spec is None:
        raise KeyError(f"Missing Beam diversity mechanic encoder for {character_id}.{key}")
    encoder = spec["encoder"]
    if encoder == "boolean_exact":
        return str(int(bool(value)))
    if encoder == "categorical_exact":
        return str(value)
    if encoder == "integer_exact":
        return str(int(float(value)))
    if encoder == "resource_band":
        return str(_band(float(value), float(spec["band"])))
    if encoder == "active_remaining_band":
        remaining = max(0.0, float(value))
        return f"active={int(remaining > 1e-9)}:band={_band(remaining, float(spec['band']))}"
    if encoder == "cooldown_ready_remaining_band":
        remaining = max(0.0, float(value))
        return f"ready={int(remaining <= 1e-9)}:band={_band(remaining, float(spec['band']))}"
    raise ValueError(f"Unsupported Beam diversity mechanic encoder for {character_id}.{key}: {encoder}")


def _canonicalize(value: Any) -> Any:
    if isinstance(value, float):
        return value.hex()
    if isinstance(value, dict):
        return {str(key): _canonicalize(val) for key, val in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, list):
        return [_canonicalize(item) for item in value]
    return value
