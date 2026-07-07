from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from simulator.buff_system import buffed_combat_stats
from simulator.models import ActionData, CharacterData, CombatState
from simulator.tune_break import (
    calculate_tune_break_damage_detail,
    calculate_tune_response_damage_detail,
    current_interfered_damage_taken_amp,
)


FormulaType = Literal["normal", "tune_break", "tune_response"]
ScalingStat = Literal["atk", "def", "hp", "none", "unresolved"]
DamageTakenAmpMode = Literal["current_target_marker", "none"]


@dataclass
class GeneratedDamagePacket:
    id: str
    source_character_id: str
    source_action_id: str
    name: str
    formula_type: FormulaType
    damage_element: str
    damage_bonus_category: str | None
    scaling_stat: ScalingStat
    normal_damage_multiplier: float = 0.0
    tune_multiplier: float = 0.0
    repeat_count: int = 1
    base_value: float = 10000.0
    additional_tune_boost: float = 0.0
    applied_damage_taken_amp_mode: DamageTakenAmpMode = "current_target_marker"
    time_offset: float = 0.0
    tags: list[str] = field(default_factory=list)
    source_status: str = "unresolved_no_runtime_effect"
    source_ref: str | None = None
    source_rows: list[int] = field(default_factory=list)
    notes: str | None = None
    label: str | None = None
    variant: str | None = None
    source_multiplier: float | None = None
    hit_interval_frames: int | None = None

    @property
    def runtime_applicable(self) -> bool:
        if self.source_status not in {"workbook_confirmed", "excel_event_order_derived"}:
            return False
        if self.repeat_count <= 0:
            return False
        if self.formula_type == "normal":
            return False
        return self.tune_multiplier > 0.0


def packet_from_mapping(data: dict[str, Any]) -> GeneratedDamagePacket:
    return GeneratedDamagePacket(
        id=str(data["id"]),
        source_character_id=str(data["source_character_id"]),
        source_action_id=str(data["source_action_id"]),
        name=str(data["name"]),
        formula_type=str(data["formula_type"]),  # type: ignore[arg-type]
        damage_element=str(data.get("damage_element") or "unresolved"),
        damage_bonus_category=data.get("damage_bonus_category"),
        scaling_stat=str(data.get("scaling_stat") or "unresolved"),  # type: ignore[arg-type]
        normal_damage_multiplier=float(data.get("normal_damage_multiplier", 0.0) or 0.0),
        tune_multiplier=float(data.get("tune_multiplier", 0.0) or 0.0),
        repeat_count=int(data.get("repeat_count", 1) or 1),
        base_value=float(data.get("base_value", 10000.0) or 10000.0),
        additional_tune_boost=float(data.get("additional_tune_boost", 0.0) or 0.0),
        applied_damage_taken_amp_mode=str(
            data.get("applied_damage_taken_amp_mode") or "current_target_marker"
        ),  # type: ignore[arg-type]
        time_offset=float(data.get("time_offset", 0.0) or 0.0),
        tags=[str(tag) for tag in data.get("tags", [])],
        source_status=str(data.get("source_status") or data.get("implementation_status") or "unresolved_no_runtime_effect"),
        source_ref=data.get("source_ref"),
        source_rows=[int(row) for row in data.get("source_rows", [])],
        notes=data.get("notes"),
        label=data.get("label"),
        variant=data.get("variant"),
        source_multiplier=float(data["source_multiplier"]) if data.get("source_multiplier") is not None else None,
        hit_interval_frames=int(data["hit_interval_frames"]) if data.get("hit_interval_frames") is not None else None,
    )


def calculate_generated_damage_packet(
    packet: GeneratedDamagePacket,
    *,
    source_action: ActionData,
    state: CombatState,
    characters: dict[str, CharacterData],
    buffs: dict[str, Any],
    force_active_buff_ids: set[str] | None = None,
) -> tuple[float, list[dict[str, Any]]]:
    if not packet.runtime_applicable:
        return 0.0, []

    character = characters[packet.source_character_id]
    stats = buffed_combat_stats(
        character,
        state,
        buffs,
        time_offset=packet.time_offset,
        force_active_buff_ids=force_active_buff_ids,
    )
    total_damage = 0.0
    details: list[dict[str, Any]] = []
    for hit_index in range(packet.repeat_count):
        damage, detail = _calculate_single_generated_hit(
            packet,
            hit_index=hit_index,
            source_action=source_action,
            state=state,
            stats=stats,
            character=character,
        )
        total_damage += damage
        details.append(detail)
    return total_damage, details


def _calculate_single_generated_hit(
    packet: GeneratedDamagePacket,
    *,
    hit_index: int,
    source_action: ActionData,
    state: CombatState,
    stats: dict[str, Any],
    character: CharacterData,
) -> tuple[float, dict[str, Any]]:
    applied_amp = (
        current_interfered_damage_taken_amp(state)
        if packet.applied_damage_taken_amp_mode == "current_target_marker"
        else 0.0
    )
    detail: dict[str, Any] = {
        "name": f"{packet.name} {hit_index + 1}",
        "is_generated_mechanic_damage": True,
        "generated_damage_packet_id": packet.id,
        "source_character_id": packet.source_character_id,
        "source_action_id": packet.source_action_id,
        "source_status": packet.source_status,
        "source_ref": packet.source_ref,
        "source_rows": list(packet.source_rows),
        "formula_type": packet.formula_type,
        "damage_element": packet.damage_element,
        "damage_bonus_category": packet.damage_bonus_category or packet.formula_type,
        "scaling_stat": packet.scaling_stat,
        "repeat_count": packet.repeat_count,
        "hit_index": hit_index,
        "time_offset": packet.time_offset,
        "tags": list(packet.tags),
        "notes": packet.notes,
        "label": packet.label,
        "variant": packet.variant,
        "source_multiplier": packet.source_multiplier if packet.source_multiplier is not None else packet.tune_multiplier,
        "hit_interval_frames": packet.hit_interval_frames,
        "everbright_applied": False,
        "normal_damage_bonuses_applied": False,
    }
    if packet.formula_type == "normal":
        detail.update(
            {
                "damage": 0.0,
                "damage_multiplier": packet.normal_damage_multiplier,
                "hit_damage_category": "unsupported_normal_generated_damage",
                "damage_category": "unsupported_normal_generated_damage",
                "unsupported_reason": "normal_generated_damage_blocked_until_bonus_routing_is_source_safe",
            }
        )
        return 0.0, detail
    if packet.formula_type == "tune_break":
        tune_detail = calculate_tune_break_damage_detail(
            tune_break_multiplier=packet.tune_multiplier,
            additional_tune_break_boost=packet.additional_tune_boost,
            tune_dmg_bonus=state.tune_dmg_bonus,
            enemy_res=state.enemy_res,
            res_pen=state.res_pen,
            attacker_level=int(stats["attacker_level"]),
            enemy_level=state.enemy_level,
            def_ignore=0.0,
            def_reduction=state.def_reduction,
            tune_break_base_value=packet.base_value,
            tune_break_damage_type="generated_tune_break",
            tune_break_element=packet.damage_element,
            hit_id=packet.id,
        )
        damage = float(tune_detail["tune_break_damage"])
        detail.update(tune_detail)
        detail.update({"damage": damage, "hit_damage_category": "tune_break", "damage_category": "tune_break"})
        return damage, detail

    response_detail = calculate_tune_response_damage_detail(
        tune_response_id=packet.id,
        tune_response_hit_id=f"{packet.id}_{hit_index + 1}",
        tune_response_multiplier=packet.tune_multiplier,
        additional_tune_response_boost=packet.additional_tune_boost,
        tune_dmg_bonus=state.tune_dmg_bonus,
        enemy_res=state.enemy_res,
        res_pen=state.res_pen,
        attacker_level=int(stats["attacker_level"]),
        enemy_level=state.enemy_level,
        def_ignore=0.0,
        def_reduction=state.def_reduction,
        applied_damage_taken_amp=applied_amp,
        tune_response_base_value=packet.base_value,
        tune_response_element=packet.damage_element,
        source_status=packet.source_status,
    )
    damage = float(response_detail["tune_response_damage"])
    detail.update(response_detail)
    detail.update(
        {
            "damage": damage,
            "hit_damage_category": "tune_response",
            "damage_category": "tune_response",
            "source_multiplier": packet.source_multiplier if packet.source_multiplier is not None else packet.tune_multiplier,
            "effective_damage_taken_amp": applied_amp,
        }
    )
    return damage, detail


def _scaling_value(stats: dict[str, Any], scaling_stat: str) -> float:
    if scaling_stat == "def":
        return float(stats.get("effective_def", 0.0) or 0.0)
    if scaling_stat == "hp":
        return float(stats.get("effective_hp", 0.0) or 0.0)
    if scaling_stat == "atk":
        return float(stats.get("effective_attack", 0.0) or 0.0)
    return 0.0
