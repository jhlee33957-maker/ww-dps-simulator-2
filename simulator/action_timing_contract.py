from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from simulator.models import ActionData, CombatState, OngoingActionInstance, ScheduledPacketInstance


FPS = 60.0
TIMING_CONTRACT_SCHEMA_VERSION = "action_timing_contract_v124"
ROLE_FEMALE_SHEET = "角色-女"
SKILL_TYPE_SHEET = "角色技能类型"


def _validate_v124_stage2c_source_refs(contract: "ActionTimingContract") -> None:
    """Reject lossy/shifted workbook joins instead of accepting display text."""
    expected_groups = {
        "mornye_heavy_inversion": {
            "mornye_heavy_inversion_impact": (
                f"{ROLE_FEMALE_SHEET}!A4136:AT4136",
                f"{SKILL_TYPE_SHEET}!A2664:AH2664",
            ),
        },
        "mornye_skill_distributed_array": {
            "mornye_distributed_array_frame_1_heal": (f"{ROLE_FEMALE_SHEET}!A4143:AT4143", None),
            "mornye_distributed_array_e2_1": (f"{ROLE_FEMALE_SHEET}!A4144:AT4144", f"{SKILL_TYPE_SHEET}!A2666:AH2666"),
            "mornye_distributed_array_e2_2": (f"{ROLE_FEMALE_SHEET}!A4145:AT4145", f"{SKILL_TYPE_SHEET}!A2667:AH2667"),
            "mornye_distributed_array_e2_3": (f"{ROLE_FEMALE_SHEET}!A4146:AT4146", f"{SKILL_TYPE_SHEET}!A2668:AH2668"),
            "mornye_distributed_array_e2_4": (f"{ROLE_FEMALE_SHEET}!A4147:AT4147", f"{SKILL_TYPE_SHEET}!A2669:AH2669"),
        },
    }.get(contract.action_id)
    if expected_groups is None:
        return
    for group in contract.scheduled_packet_groups:
        expected = expected_groups.get(group.packet_group_id)
        if expected is None:
            raise ValueError(f"Unexpected Stage-2C packet group {group.packet_group_id!r}")
        expected_frame_ref, expected_coefficient_ref = expected
        if group.source_frame_row_ref != expected_frame_ref:
            raise ValueError(f"Invalid UTF-8/source row join for {group.packet_group_id!r}")
        if group.source_coefficient_resource_row_ref != expected_coefficient_ref:
            raise ValueError(f"Invalid UTF-8/coefficient row join for {group.packet_group_id!r}")
        refs = [*group.source_refs, *contract.source_refs]
        for ref in refs:
            if any(ord(char) < 32 or ord(char) == 0xFFFD for char in ref) or "\ufeff" in ref:
                raise ValueError(f"Invalid control/replacement/BOM character in source ref {ref!r}")
        if expected_frame_ref not in group.source_refs or (
            expected_coefficient_ref is not None and expected_coefficient_ref not in group.source_refs
        ):
            raise ValueError(f"Missing exact source refs for {group.packet_group_id!r}")


class ScheduledPacketGroupContract(BaseModel):
    packet_group_id: str
    scheduled_frames: list[float] = Field(min_length=1)
    combat_time_resolution_rule: str = "source_action_wall_offset_minus_global_time_stop"
    damage_payload: dict[str, Any] = Field(default_factory=dict)
    resource_payload: dict[str, Any] = Field(default_factory=dict)
    healing_payload: dict[str, Any] = Field(default_factory=dict)
    marker_payload: dict[str, Any] = Field(default_factory=dict)
    buff_payload: dict[str, Any] = Field(default_factory=dict)
    detachable: bool = False
    cancel_on_swap: bool = False
    persist_after_swap: bool = False
    source_refs: list[str] = Field(default_factory=list)
    source_frame_row_ref: str | None = None
    source_coefficient_resource_row_ref: str | None = None
    packet_count: int | None = Field(default=None, gt=0)
    payload_partition_rules: dict[str, str] = Field(default_factory=dict)
    source_type: str | None = None
    confidence: str | None = None

    @model_validator(mode="after")
    def validate_frames(self) -> "ScheduledPacketGroupContract":
        if any(frame < 0 for frame in self.scheduled_frames):
            raise ValueError("scheduled packet frames must be non-negative")
        if self.scheduled_frames != sorted(self.scheduled_frames):
            raise ValueError("scheduled packet frames must be sorted")
        if self.packet_count is not None and self.packet_count != len(self.scheduled_frames):
            raise ValueError("packet_count must match scheduled_frames")
        return self


class TimingVariantCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation_state_active: bool


class ActionTimingVariant(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_id: str = Field(min_length=1)
    condition: TimingVariantCondition
    same_character_input_frame: float = Field(ge=0)
    swap_input_frame: float = Field(ge=0)
    source_action_end_frame: float = Field(ge=0)
    lifecycle_end_frame: float = Field(ge=0)
    global_time_stop_frames: float = Field(default=0, ge=0)
    legacy_hit_frame_overrides: list[float] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_lifecycle(self) -> "ActionTimingVariant":
        required_end = max(
            self.source_action_end_frame,
            self.same_character_input_frame,
            self.swap_input_frame,
        )
        if self.lifecycle_end_frame < required_end:
            raise ValueError("lifecycle_end_frame must cover source end and both input unlocks")
        if any(frame < 0 for frame in self.legacy_hit_frame_overrides):
            raise ValueError("legacy hit frame overrides must be non-negative")
        return self


class SelectedActionTiming(BaseModel):
    variant_id: str | None = None
    variant_source: str
    same_character_input_frame: float = Field(ge=0)
    swap_input_frame: float = Field(ge=0)
    source_action_end_frame: float = Field(ge=0)
    lifecycle_end_frame: float = Field(ge=0)
    global_time_stop_frames: float = Field(default=0, ge=0)
    legacy_hit_frame_overrides: list[float] = Field(default_factory=list)

    @property
    def first_control_frame(self) -> float:
        return min(self.same_character_input_frame, self.swap_input_frame)


class ActionTimingContract(BaseModel):
    action_id: str
    same_character_input_frame: float | None = Field(default=None, ge=0)
    swap_input_frame: float | None = Field(default=None, ge=0)
    source_action_end_frame: float | None = Field(default=None, ge=0)
    action_end_frame: float | None = Field(default=None, ge=0)
    global_time_stop_frames: float = Field(default=0, ge=0)
    timing_variants: list[ActionTimingVariant] = Field(default_factory=list)
    persist_character_after_swap: bool = False
    persist_if_swapped_before_frame: float | None = Field(default=None, ge=0)
    defer_legacy_payload_to_scheduled_packets: bool = False
    scheduled_packet_groups: list[ScheduledPacketGroupContract] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    source_type: str
    confidence: str

    @model_validator(mode="after")
    def validate_timing_order(self) -> "ActionTimingContract":
        static_values = (
            self.same_character_input_frame,
            self.swap_input_frame,
            self.action_end_frame,
        )
        if self.timing_variants:
            if any(value is not None for value in static_values):
                raise ValueError("variant timing contracts must not also define static timing frames")
            variant_ids = [variant.variant_id for variant in self.timing_variants]
            if len(variant_ids) != len(set(variant_ids)):
                raise ValueError("timing variant IDs must be unique within an action")
            conditions = [variant.condition.model_dump_json() for variant in self.timing_variants]
            if len(conditions) != len(set(conditions)):
                raise ValueError("timing variant conditions must be deterministic and unique")
        else:
            if any(value is None for value in static_values):
                raise ValueError("static timing contracts require input unlock and action end frames")
            if float(self.action_end_frame) < max(
                float(self.same_character_input_frame),
                float(self.swap_input_frame),
                float(self.source_action_end_frame or self.action_end_frame),
            ):
                raise ValueError("action_end_frame must not precede an input unlock")
        if (
            self.persist_if_swapped_before_frame is not None
            and not self.timing_variants
            and self.persist_if_swapped_before_frame > float(self.action_end_frame)
        ):
            raise ValueError("persistence cutoff must not follow action end")
        group_ids = [group.packet_group_id for group in self.scheduled_packet_groups]
        if len(group_ids) != len(set(group_ids)):
            raise ValueError("packet_group_id values must be unique within an action")
        if self.defer_legacy_payload_to_scheduled_packets:
            for group in self.scheduled_packet_groups:
                if group.healing_payload:
                    if not group.source_frame_row_ref or group.packet_count != len(group.scheduled_frames):
                        raise ValueError("scheduled healing groups require an exact source row and packet count")
                    continue
                if group.damage_payload.get("placeholder"):
                    continue
                if not group.source_frame_row_ref or not group.source_coefficient_resource_row_ref:
                    raise ValueError("resolved packet groups require frame and coefficient/resource source refs")
                if group.packet_count != len(group.scheduled_frames):
                    raise ValueError("resolved packet groups require an exact packet_count")
                allowed_rules = {
                    "source_row_per_occurrence",
                    "source_row_total_first_occurrence",
                    "source_row_total_final_occurrence",
                    "action_start_frame_1_once",
                    "none",
                }
                required_payloads = {"damage", "off_tune", "resonance_energy", "concerto", "rest_mass"}
                if set(group.payload_partition_rules) != required_payloads:
                    raise ValueError("resolved packet groups require partition rules for every payload class")
                if not set(group.payload_partition_rules.values()) <= allowed_rules:
                    raise ValueError("equal or unsupported packet payload splitting is not source-backed")
        last_packet_frame = max(
            (max(group.scheduled_frames) for group in self.scheduled_packet_groups),
            default=0.0,
        )
        if self.timing_variants:
            for variant in self.timing_variants:
                if variant.lifecycle_end_frame < last_packet_frame:
                    raise ValueError("lifecycle_end_frame must cover the last scheduled packet")
        elif float(self.action_end_frame) < last_packet_frame:
            raise ValueError("action_end_frame must cover the last scheduled packet")
        if self.action_id == "mornye_heavy_inversion":
            if (
                self.same_character_input_frame != 86
                or self.swap_input_frame != 86
                or self.source_action_end_frame != 78
                or self.action_end_frame != 86
                or len(self.scheduled_packet_groups) != 1
                or self.scheduled_packet_groups[0].scheduled_frames != [66]
            ):
                raise ValueError("Mornye Heavy Inversion requires its audited 66F packet and 86F lifecycle")
        if self.action_id == "mornye_skill_distributed_array":
            expected = ["mornye_distributed_array_frame_1_heal", "mornye_distributed_array_e2_1", "mornye_distributed_array_e2_2", "mornye_distributed_array_e2_3", "mornye_distributed_array_e2_4"]
            if (
                self.same_character_input_frame != 60
                or self.swap_input_frame != 60
                or self.action_end_frame != 60
                or [group.packet_group_id for group in self.scheduled_packet_groups] != expected
                or [group.scheduled_frames for group in self.scheduled_packet_groups] != [[1], [22], [22], [36], [36]]
            ):
                raise ValueError("Mornye Distributed Array requires its 1F heal and ordered 22F/22F/36F/36F source packets")
        _validate_v124_stage2c_source_refs(self)
        return self

    @property
    def first_control_frame(self) -> float:
        if self.timing_variants:
            raise ValueError("state-dependent timing requires variant selection")
        return min(float(self.same_character_input_frame), float(self.swap_input_frame))


def select_action_timing(
    state: CombatState,
    action: ActionData,
    contract: ActionTimingContract,
) -> SelectedActionTiming:
    if not contract.timing_variants:
        action_end_frame = float(contract.action_end_frame)
        return SelectedActionTiming(
            variant_source="static_action_timing_contract",
            same_character_input_frame=float(contract.same_character_input_frame),
            swap_input_frame=float(contract.swap_input_frame),
            source_action_end_frame=float(contract.source_action_end_frame or action_end_frame),
            lifecycle_end_frame=action_end_frame,
            global_time_stop_frames=contract.global_time_stop_frames,
        )

    owner_character_id = str(action.character_id or state.active_character_id)
    marker_state = state.character_mechanics_state.get(owner_character_id, {})
    observation_state_active = bool(marker_state.get("observation_marker_active", False))
    matching = [
        variant
        for variant in contract.timing_variants
        if variant.condition.observation_state_active is observation_state_active
    ]
    if len(matching) != 1:
        raise ValueError(
            f"Expected exactly one timing variant for {action.id!r} and "
            f"observation_state_active={observation_state_active}, got {len(matching)}"
        )
    variant = matching[0]
    return SelectedActionTiming(
        variant_id=variant.variant_id,
        variant_source=f"character_mechanics_state.{owner_character_id}.observation_marker_active",
        same_character_input_frame=variant.same_character_input_frame,
        swap_input_frame=variant.swap_input_frame,
        source_action_end_frame=variant.source_action_end_frame,
        lifecycle_end_frame=variant.lifecycle_end_frame,
        global_time_stop_frames=variant.global_time_stop_frames,
        legacy_hit_frame_overrides=list(variant.legacy_hit_frame_overrides),
    )


def load_action_timing_contracts(data_dir: Path | str) -> dict[str, ActionTimingContract]:
    path = Path(data_dir) / "action_timing_contract_v124.json"
    if not path.is_file():
        return {}
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("action timing contract must be UTF-8 without a BOM")
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if payload.get("schema_version") != TIMING_CONTRACT_SCHEMA_VERSION:
        raise ValueError(f"Unsupported action timing contract schema: {payload.get('schema_version')!r}")
    contracts = [ActionTimingContract.model_validate(item) for item in payload.get("actions", [])]
    by_id = {contract.action_id: contract for contract in contracts}
    if len(by_id) != len(contracts):
        raise ValueError("action timing contract action_id values must be unique")
    return by_id


def wall_elapsed_to_combat_elapsed(
    timing: ActionTimingContract | SelectedActionTiming,
    wall_elapsed: float,
) -> float:
    elapsed_frames = max(0.0, float(wall_elapsed) * FPS)
    stopped_frames = min(elapsed_frames, timing.global_time_stop_frames)
    return max(0.0, elapsed_frames - stopped_frames) / FPS


def prepare_control_point_action(
    action: ActionData,
    contract: ActionTimingContract,
    selected_timing: SelectedActionTiming | None = None,
) -> ActionData:
    """Return a start/control slice without paying deferred packet gains twice."""
    if selected_timing is None:
        if contract.timing_variants:
            raise ValueError("state-dependent timing must be selected before preparing the action")
        action_end_frame = float(contract.action_end_frame)
        selected_timing = SelectedActionTiming(
            variant_source="static_action_timing_contract",
            same_character_input_frame=float(contract.same_character_input_frame),
            swap_input_frame=float(contract.swap_input_frame),
            source_action_end_frame=float(contract.source_action_end_frame or action_end_frame),
            lifecycle_end_frame=action_end_frame,
            global_time_stop_frames=contract.global_time_stop_frames,
        )
    runtime_action = action.model_copy(deep=True)
    control_seconds = selected_timing.first_control_frame / FPS
    runtime_action.duration = control_seconds
    runtime_action.action_time = control_seconds
    runtime_action.combat_time_cost = wall_elapsed_to_combat_elapsed(selected_timing, control_seconds)
    runtime_action.timing_overrides = {}
    if contract.defer_legacy_payload_to_scheduled_packets:
        runtime_action.hits = []
        runtime_action.damage_multiplier = 0.0
        runtime_action.tune_break_multiplier = 0.0
        runtime_action.off_tune_value = 0.0
        runtime_action.resonance_energy_gain = 0.0
        runtime_action.concerto_energy_gain = 0.0
        # These two actions historically carried their complete payload in the
        # aggregate action.  Their source-backed packet contracts now own the
        # Momentum and Observation Marker mutations as well as damage/resources.
        for key in (
            "relative_momentum_delta",
            "consume_relative_momentum",
            "observation_marker_duration",
        ):
            runtime_action.mechanic_effects.pop(key, None)
        if any(
            group.resource_payload.get("rest_mass_application") == "action_start_frame_1_once"
            for group in contract.scheduled_packet_groups
        ):
            runtime_action.mechanic_effects.pop("rest_mass_energy_delta", None)
    else:
        if selected_timing.legacy_hit_frame_overrides:
            if len(selected_timing.legacy_hit_frame_overrides) != len(runtime_action.hits):
                raise ValueError("legacy hit frame override count must match the action's legacy hit count")
            for hit, frame in zip(runtime_action.hits, selected_timing.legacy_hit_frame_overrides):
                hit.time = frame / FPS
        else:
            for hit in runtime_action.hits:
                hit.time = min(hit.time, control_seconds)
    runtime_action.mechanic_effects = {
        **runtime_action.mechanic_effects,
        "v124_timing_contract_control_slice": True,
        "v124_deferred_packet_payloads": contract.defer_legacy_payload_to_scheduled_packets,
        "v124_original_action_time": action.effective_action_time,
        "selected_timing_variant_id": selected_timing.variant_id,
        "selected_timing_variant_source": selected_timing.variant_source,
        "selected_source_action_end_frame": selected_timing.source_action_end_frame,
        "selected_lifecycle_end_frame": selected_timing.lifecycle_end_frame,
    }
    return runtime_action


def start_ongoing_action(
    state: CombatState,
    action: ActionData,
    contract: ActionTimingContract,
    selected_timing: SelectedActionTiming | None = None,
) -> OngoingActionInstance:
    selected_timing = selected_timing or select_action_timing(state, action, contract)
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
        same_character_lock_until_wall_time=start_wall + selected_timing.same_character_input_frame / FPS,
        swap_lock_until_wall_time=start_wall + selected_timing.swap_input_frame / FPS,
        action_end_wall_time=start_wall + selected_timing.lifecycle_end_frame / FPS,
        source_action_end_wall_time=start_wall + selected_timing.source_action_end_frame / FPS,
        lifecycle_end_wall_time=start_wall + selected_timing.lifecycle_end_frame / FPS,
        selected_timing_variant_id=selected_timing.variant_id,
        selected_timing_variant_source=selected_timing.variant_source,
        selected_same_character_input_frame=selected_timing.same_character_input_frame,
        selected_swap_input_frame=selected_timing.swap_input_frame,
        selected_source_action_end_frame=selected_timing.source_action_end_frame,
        selected_lifecycle_end_frame=selected_timing.lifecycle_end_frame,
        selected_global_time_stop_frames=selected_timing.global_time_stop_frames,
        selected_legacy_hit_frame_overrides=list(selected_timing.legacy_hit_frame_overrides),
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
    rest_mass_payloads = [
        float(group.resource_payload.get("rest_mass_total", 0.0) or 0.0)
        for group in contract.scheduled_packet_groups
        if group.resource_payload.get("rest_mass_application") == "action_start_frame_1_once"
    ]
    nonzero_rest_mass_payloads = [value for value in rest_mass_payloads if abs(value) > 1e-12]
    if len(nonzero_rest_mass_payloads) > 1:
        raise ValueError(f"{action.id!r} has more than one frame-1 Rest Mass payload")
    if nonzero_rest_mass_payloads:
        owner_state = state.character_mechanics_state.setdefault(instance.owner_character_id, {})
        cap = float(owner_state.get("rest_mass_energy_cap", 100.0) or 100.0)
        before = float(owner_state.get("rest_mass_energy", 0.0) or 0.0)
        delta = nonzero_rest_mass_payloads[0]
        after = max(0.0, min(cap, before + delta))
        owner_state["rest_mass_energy"] = after
        state.scheduled_packet_event_log.append(
            {
                "event_type": "v124_action_start_payload",
                "action_instance_id": instance_id,
                "owner_character_id": instance.owner_character_id,
                "source_action_id": action.id,
                "scheduled_frame": 1.0,
                "scheduled_wall_time": start_wall + 1.0 / FPS,
                "resolved_wall_time": start_wall + 1.0 / FPS,
                "rest_mass_before": before,
                "rest_mass_payload": delta,
                "rest_mass_applied": after - before,
                "rest_mass_after": after,
            }
        )
    momentum_consumptions = [
        group.resource_payload
        for group in contract.scheduled_packet_groups
        if group.resource_payload.get("relative_momentum_application") == "action_start_consume_once"
    ]
    if len(momentum_consumptions) > 1:
        raise ValueError(f"{action.id!r} has more than one action-start Relative Momentum consumption")
    if momentum_consumptions:
        owner_state = state.character_mechanics_state.setdefault(instance.owner_character_id, {})
        before = float(owner_state.get("relative_momentum", 0.0) or 0.0)
        owner_state["relative_momentum"] = 0.0
        state.scheduled_packet_event_log.append(
            {
                "event_type": "v124_action_start_payload",
                "action_instance_id": instance_id,
                "owner_character_id": instance.owner_character_id,
                "source_action_id": action.id,
                "scheduled_frame": 0.0,
                "scheduled_wall_time": start_wall,
                "resolved_wall_time": start_wall,
                "relative_momentum_before": before,
                "relative_momentum_consumed": before,
                "relative_momentum_after": 0.0,
            }
        )
    for group in contract.scheduled_packet_groups:
        for occurrence_index, scheduled_frame in enumerate(group.scheduled_frames, start=1):
            state.packet_instance_next_order += 1
            packet_id = (
                f"packet-instance-v124-{state.packet_instance_next_order}:"
                f"{action.id}:{group.packet_group_id}:{occurrence_index}"
            )
            wall_offset = scheduled_frame / FPS
            damage_payload = dict(group.damage_payload)
            resource_payload = dict(group.resource_payload)
            damage_payload["damage_multiplier"] = float(
                damage_payload.get("damage_multiplier_per_packet", 0.0) or 0.0
            )
            resource_payload["resonance_energy_gain"] = float(
                resource_payload.get("resonance_energy_per_packet", 0.0) or 0.0
            )
            resource_payload["concerto_energy_gain"] = float(
                resource_payload.get("concerto_per_packet", 0.0) or 0.0
            )
            off_tune_total = float(resource_payload.get("off_tune_total", 0.0) or 0.0)
            off_tune_application = resource_payload.get("off_tune_application", "none")
            resource_payload["off_tune_value"] = (
                off_tune_total
                if off_tune_application == "source_row_total_first_occurrence" and occurrence_index == 1
                else off_tune_total
                if (
                    off_tune_application == "source_row_total_final_occurrence"
                    and occurrence_index == len(group.scheduled_frames)
                )
                else float(resource_payload.get("off_tune_per_packet", 0.0) or 0.0)
                if off_tune_application == "source_row_per_occurrence"
                else 0.0
            )
            packet = ScheduledPacketInstance(
                packet_instance_id=packet_id,
                action_instance_id=instance_id,
                owner_character_id=instance.owner_character_id,
                source_action_id=action.id,
                packet_group_id=group.packet_group_id,
                scheduled_wall_time=start_wall + wall_offset,
                scheduled_combat_time=start_combat + wall_elapsed_to_combat_elapsed(selected_timing, wall_offset),
                combat_time_resolution_rule=group.combat_time_resolution_rule,
                damage_payload=damage_payload,
                resource_payload=resource_payload,
                healing_payload=dict(group.healing_payload),
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


def advance_ongoing_action_runtime(
    state: CombatState,
    packet_resolver: Callable[[ScheduledPacketInstance], dict[str, Any]] | None = None,
    *,
    through_wall_time: float | None = None,
    through_combat_time: float | None = None,
) -> list[dict[str, Any]]:
    now_wall = float(state.current_time if through_wall_time is None else through_wall_time)
    now_combat = float(state.combat_time if through_combat_time is None else through_combat_time)
    events: list[dict[str, Any]] = []
    for packet in sorted(
        state.scheduled_packet_instances,
        key=lambda item: (item.scheduled_wall_time, item.packet_instance_id),
    ):
        if packet.resolved or packet.cancelled or packet.scheduled_wall_time > now_wall + 1e-9:
            continue
        cursor_floor_wall = max(float(state.current_time), float(state.event_cursor_wall_time))
        cursor_floor_combat = max(float(state.combat_time), float(state.event_cursor_combat_time))
        processed_wall_time = max(float(packet.scheduled_wall_time), cursor_floor_wall)
        scheduled_combat_time = float(packet.scheduled_combat_time or now_combat)
        processed_combat_time = (
            scheduled_combat_time
            if processed_wall_time <= float(packet.scheduled_wall_time) + 1e-9
            else max(scheduled_combat_time, cursor_floor_combat)
        )
        state.event_cursor_wall_time = processed_wall_time
        state.event_cursor_combat_time = processed_combat_time
        placeholder = bool(packet.damage_payload.get("placeholder"))
        if not placeholder and packet_resolver is None:
            raise ValueError(f"Scheduled packet {packet.packet_instance_id!r} requires a payload resolver")
        resolved_payload = {} if placeholder else dict(packet_resolver(packet))
        packet.resolved = True
        packet.processed_wall_time = processed_wall_time
        packet.processed_combat_time = processed_combat_time
        packet.resolved_wall_time = processed_wall_time
        packet.resolved_combat_time = processed_combat_time
        state.chronological_event_next_sequence += 1
        event = {
            "event_type": "v124_scheduled_packet_placeholder" if placeholder else "v124_scheduled_action_packet",
            "event_sequence": state.chronological_event_next_sequence,
            "event_wall_time": processed_wall_time,
            "event_combat_time": processed_combat_time,
            "packet_instance_id": packet.packet_instance_id,
            "action_instance_id": packet.action_instance_id,
            "owner_character_id": packet.owner_character_id,
            "source_action_id": packet.source_action_id,
            "packet_group_id": packet.packet_group_id,
            "scheduled_wall_time": packet.scheduled_wall_time,
            "scheduled_combat_time": packet.scheduled_combat_time,
            "processed_wall_time": packet.processed_wall_time,
            "processed_combat_time": packet.processed_combat_time,
            "resolved_wall_time": packet.resolved_wall_time,
            "resolved_combat_time": packet.resolved_combat_time,
            "damage_payload": dict(packet.damage_payload),
            "resource_payload": dict(packet.resource_payload),
            "marker_payload": dict(packet.marker_payload),
            "buff_payload": dict(packet.buff_payload),
            "damage_applied": float(resolved_payload.get("damage", 0.0) or 0.0),
            "resource_applied": float(resolved_payload.get("resonance_energy_gained", 0.0) or 0.0),
            "stage_2_payload_resolution_required": placeholder,
            **resolved_payload,
        }
        state.scheduled_packet_event_log.append(event)
        state.chronological_event_log.append(event)
        events.append(event)
    for instance in state.ongoing_action_instances:
        source_end = instance.source_action_end_wall_time or instance.action_end_wall_time
        if not instance.source_action_ended and now_wall + 1e-9 >= source_end:
            instance.source_action_ended = True
        lifecycle_end = instance.lifecycle_end_wall_time or instance.action_end_wall_time
        if not instance.ended and not instance.cancelled and now_wall + 1e-9 >= lifecycle_end:
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
