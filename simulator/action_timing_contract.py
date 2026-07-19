from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator

from simulator.models import ActionData, CombatState, OngoingActionInstance, ScheduledPacketInstance


FPS = 60.0
TIMING_CONTRACT_SCHEMA_VERSION = "action_timing_contract_v124"


class ScheduledPacketGroupContract(BaseModel):
    packet_group_id: str
    scheduled_frames: list[float] = Field(min_length=1)
    combat_time_resolution_rule: str = "source_action_wall_offset_minus_global_time_stop"
    damage_payload: dict[str, Any] = Field(default_factory=dict)
    resource_payload: dict[str, Any] = Field(default_factory=dict)
    marker_payload: dict[str, Any] = Field(default_factory=dict)
    buff_payload: dict[str, Any] = Field(default_factory=dict)
    detachable: bool = False
    cancel_on_swap: bool = False
    persist_after_swap: bool = False
    source_refs: list[str] = Field(default_factory=list)
    source_type: str | None = None
    confidence: str | None = None

    @model_validator(mode="after")
    def validate_frames(self) -> "ScheduledPacketGroupContract":
        if any(frame < 0 for frame in self.scheduled_frames):
            raise ValueError("scheduled packet frames must be non-negative")
        if self.scheduled_frames != sorted(self.scheduled_frames):
            raise ValueError("scheduled packet frames must be sorted")
        return self


class ActionTimingContract(BaseModel):
    action_id: str
    same_character_input_frame: float = Field(ge=0)
    swap_input_frame: float = Field(ge=0)
    action_end_frame: float = Field(ge=0)
    global_time_stop_frames: float = Field(default=0, ge=0)
    persist_character_after_swap: bool = False
    persist_if_swapped_before_frame: float | None = Field(default=None, ge=0)
    defer_legacy_payload_to_scheduled_packets: bool = False
    scheduled_packet_groups: list[ScheduledPacketGroupContract] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    source_type: str
    confidence: str

    @model_validator(mode="after")
    def validate_timing_order(self) -> "ActionTimingContract":
        if self.action_end_frame < max(self.same_character_input_frame, self.swap_input_frame):
            raise ValueError("action_end_frame must not precede an input unlock")
        if (
            self.persist_if_swapped_before_frame is not None
            and self.persist_if_swapped_before_frame > self.action_end_frame
        ):
            raise ValueError("persistence cutoff must not follow action end")
        group_ids = [group.packet_group_id for group in self.scheduled_packet_groups]
        if len(group_ids) != len(set(group_ids)):
            raise ValueError("packet_group_id values must be unique within an action")
        return self

    @property
    def first_control_frame(self) -> float:
        return min(self.same_character_input_frame, self.swap_input_frame)


def load_action_timing_contracts(data_dir: Path | str) -> dict[str, ActionTimingContract]:
    path = Path(data_dir) / "action_timing_contract_v124.json"
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8-sig") as file:
        payload = json.load(file)
    if payload.get("schema_version") != TIMING_CONTRACT_SCHEMA_VERSION:
        raise ValueError(f"Unsupported action timing contract schema: {payload.get('schema_version')!r}")
    contracts = [ActionTimingContract.model_validate(item) for item in payload.get("actions", [])]
    by_id = {contract.action_id: contract for contract in contracts}
    if len(by_id) != len(contracts):
        raise ValueError("action timing contract action_id values must be unique")
    return by_id


def wall_elapsed_to_combat_elapsed(contract: ActionTimingContract, wall_elapsed: float) -> float:
    elapsed_frames = max(0.0, float(wall_elapsed) * FPS)
    stopped_frames = min(elapsed_frames, contract.global_time_stop_frames)
    return max(0.0, elapsed_frames - stopped_frames) / FPS


def prepare_control_point_action(action: ActionData, contract: ActionTimingContract) -> ActionData:
    """Return a start/control slice without paying deferred packet gains twice."""
    runtime_action = action.model_copy(deep=True)
    control_seconds = contract.first_control_frame / FPS
    runtime_action.duration = control_seconds
    runtime_action.action_time = control_seconds
    runtime_action.combat_time_cost = wall_elapsed_to_combat_elapsed(contract, control_seconds)
    if contract.defer_legacy_payload_to_scheduled_packets:
        runtime_action.hits = []
        runtime_action.damage_multiplier = 0.0
        runtime_action.tune_break_multiplier = 0.0
        runtime_action.off_tune_value = 0.0
        runtime_action.resonance_energy_gain = 0.0
        runtime_action.concerto_energy_gain = 0.0
    else:
        for hit in runtime_action.hits:
            hit.time = min(hit.time, control_seconds)
    runtime_action.mechanic_effects = {
        **runtime_action.mechanic_effects,
        "v124_timing_contract_control_slice": True,
        "v124_deferred_packet_payloads": contract.defer_legacy_payload_to_scheduled_packets,
        "v124_original_action_time": action.effective_action_time,
    }
    return runtime_action


def start_ongoing_action(
    state: CombatState,
    action: ActionData,
    contract: ActionTimingContract,
) -> OngoingActionInstance:
    state.action_instance_next_order += 1
    instance_id = f"action-instance-v124-{state.action_instance_next_order}:{action.id}"
    start_wall = float(state.current_time)
    start_combat = float(state.combat_time)
    instance = OngoingActionInstance(
        action_instance_id=instance_id,
        owner_character_id=str(action.character_id or state.active_character_id),
        source_action_id=action.id,
        start_wall_time=start_wall,
        start_combat_time=start_combat,
        same_character_lock_until_wall_time=start_wall + contract.same_character_input_frame / FPS,
        swap_lock_until_wall_time=start_wall + contract.swap_input_frame / FPS,
        action_end_wall_time=start_wall + contract.action_end_frame / FPS,
        persist_after_swap=contract.persist_character_after_swap,
        persistence_cutoff_wall_time=(
            start_wall + contract.persist_if_swapped_before_frame / FPS
            if contract.persist_if_swapped_before_frame is not None
            else None
        ),
        source_refs=list(contract.source_refs),
        source_type=contract.source_type,
        confidence=contract.confidence,
    )
    state.ongoing_action_instances.append(instance)
    for group in contract.scheduled_packet_groups:
        for occurrence_index, scheduled_frame in enumerate(group.scheduled_frames, start=1):
            state.packet_instance_next_order += 1
            packet_id = (
                f"packet-instance-v124-{state.packet_instance_next_order}:"
                f"{action.id}:{group.packet_group_id}:{occurrence_index}"
            )
            wall_offset = scheduled_frame / FPS
            packet = ScheduledPacketInstance(
                packet_instance_id=packet_id,
                action_instance_id=instance_id,
                owner_character_id=instance.owner_character_id,
                source_action_id=action.id,
                packet_group_id=group.packet_group_id,
                scheduled_wall_time=start_wall + wall_offset,
                scheduled_combat_time=start_combat + wall_elapsed_to_combat_elapsed(contract, wall_offset),
                combat_time_resolution_rule=group.combat_time_resolution_rule,
                damage_payload=dict(group.damage_payload),
                resource_payload=dict(group.resource_payload),
                marker_payload=dict(group.marker_payload),
                buff_payload=dict(group.buff_payload),
                detachable=group.detachable,
                cancel_on_swap=group.cancel_on_swap,
                persist_after_swap=group.persist_after_swap,
                source_refs=list(group.source_refs),
                source_type=group.source_type or contract.source_type,
                confidence=group.confidence or contract.confidence,
            )
            state.scheduled_packet_instances.append(packet)
            instance.scheduled_packet_instances.append(packet_id)
    return instance


def release_prior_owner_input_locks_for_followup(state: CombatState, owner_character_id: str) -> None:
    """A legal same-character follow-up owns subsequent input restrictions.

    The prior action tail and packets remain alive; only its already-crossed control
    branch stops vetoing the newly started action's own swap contract.
    """
    now = float(state.current_time)
    for instance in state.ongoing_action_instances:
        if instance.ended or instance.cancelled or instance.owner_character_id != owner_character_id:
            continue
        if now + 1e-9 >= instance.same_character_lock_until_wall_time:
            instance.same_character_lock_until_wall_time = now
            instance.swap_lock_until_wall_time = now


def same_character_input_locked(state: CombatState, character_id: str) -> bool:
    now = float(state.current_time)
    return any(
        not instance.ended
        and not instance.cancelled
        and instance.owner_character_id == character_id
        and now + 1e-9 < instance.same_character_lock_until_wall_time
        for instance in state.ongoing_action_instances
    )


def swap_input_locked(state: CombatState, outgoing_character_id: str) -> bool:
    now = float(state.current_time)
    return any(
        not instance.ended
        and not instance.cancelled
        and instance.owner_character_id == outgoing_character_id
        and now + 1e-9 < instance.swap_lock_until_wall_time
        for instance in state.ongoing_action_instances
    )


def handle_character_swap(state: CombatState, outgoing_character_id: str) -> None:
    now = float(state.current_time)
    persistent = set(state.persistent_off_field_character_ids)
    for instance in state.ongoing_action_instances:
        if instance.ended or instance.cancelled or instance.owner_character_id != outgoing_character_id:
            continue
        before_cutoff = (
            instance.persistence_cutoff_wall_time is not None
            and now + 1e-9 < instance.persistence_cutoff_wall_time
        )
        if instance.persist_after_swap or before_cutoff:
            instance.owner_character_persistent = True
            instance.owner_character_executing = True
            persistent.add(outgoing_character_id)
            continue
        instance.owner_character_executing = False
        for packet in state.scheduled_packet_instances:
            if packet.action_instance_id != instance.action_instance_id or packet.resolved:
                continue
            if packet.cancel_on_swap or not packet.detachable:
                packet.cancelled = True
    state.persistent_off_field_character_ids = sorted(persistent)


def advance_ongoing_action_runtime(state: CombatState) -> list[dict[str, Any]]:
    now_wall = float(state.current_time)
    now_combat = float(state.combat_time)
    events: list[dict[str, Any]] = []
    for packet in state.scheduled_packet_instances:
        if packet.resolved or packet.cancelled or packet.scheduled_wall_time > now_wall + 1e-9:
            continue
        packet.resolved = True
        packet.resolved_wall_time = packet.scheduled_wall_time
        packet.resolved_combat_time = min(now_combat, packet.scheduled_combat_time or now_combat)
        event = {
            "event_type": "v124_scheduled_packet_placeholder",
            "packet_instance_id": packet.packet_instance_id,
            "action_instance_id": packet.action_instance_id,
            "owner_character_id": packet.owner_character_id,
            "source_action_id": packet.source_action_id,
            "packet_group_id": packet.packet_group_id,
            "scheduled_wall_time": packet.scheduled_wall_time,
            "scheduled_combat_time": packet.scheduled_combat_time,
            "resolved_wall_time": packet.resolved_wall_time,
            "resolved_combat_time": packet.resolved_combat_time,
            "damage_payload": dict(packet.damage_payload),
            "resource_payload": dict(packet.resource_payload),
            "marker_payload": dict(packet.marker_payload),
            "buff_payload": dict(packet.buff_payload),
            "damage_applied": 0.0,
            "resource_applied": 0.0,
            "stage_2_payload_resolution_required": True,
        }
        state.scheduled_packet_event_log.append(event)
        events.append(event)
    for instance in state.ongoing_action_instances:
        if not instance.ended and not instance.cancelled and now_wall + 1e-9 >= instance.action_end_wall_time:
            instance.ended = True
            instance.owner_character_executing = False
            if instance.owner_character_id in state.persistent_off_field_character_ids:
                still_persistent = any(
                    other.action_instance_id != instance.action_instance_id
                    and not other.ended
                    and not other.cancelled
                    and other.owner_character_id == instance.owner_character_id
                    and other.owner_character_persistent
                    for other in state.ongoing_action_instances
                )
                if not still_persistent:
                    state.persistent_off_field_character_ids.remove(instance.owner_character_id)
    return events
