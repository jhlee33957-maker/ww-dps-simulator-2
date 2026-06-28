from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ActionType = Literal[
    "basic_attack",
    "resonance_skill",
    "resonance_liberation",
    "echo_skill",
    "swap",
    "wait",
]
BuffModifierType = Literal["attack", "damage_bonus"]
BuffTarget = Literal["self", "active", "team"]


class CharacterData(BaseModel):
    id: str
    name: str
    attack: float = Field(ge=0)
    crit_rate: float = Field(ge=0)
    crit_damage: float = Field(ge=0)
    damage_bonus: float = 0.0
    resonance_energy: float = Field(ge=0)
    resonance_energy_max: float = Field(default=125.0, gt=0)
    concerto_energy: float = Field(ge=0)
    active: bool = False


class ActionData(BaseModel):
    id: str
    name: str
    character_id: str | None
    action_type: ActionType
    duration: float = Field(gt=0)
    cooldown: float = Field(ge=0)
    damage_multiplier: float = Field(ge=0)
    resonance_energy_gain: float = 0.0
    concerto_energy_gain: float = 0.0
    resonance_energy_cost: float = Field(ge=0)
    applies_buffs: list[str] = Field(default_factory=list)
    required_buffs: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class BuffData(BaseModel):
    id: str
    name: str
    duration: float = Field(gt=0)
    modifier_type: BuffModifierType
    value: float
    target: BuffTarget


class ActiveBuff(BaseModel):
    buff_id: str
    source_character_id: str | None
    remaining_duration: float


class ResourceChange(BaseModel):
    resonance_gained: float = 0.0
    resonance_wasted: float = 0.0
    concerto_gained: float = 0.0
    concerto_wasted: float = 0.0


class CombatState(BaseModel):
    current_time: float = 0.0
    total_damage: float = 0.0
    active_character_id: str
    cooldowns: dict[str, float] = Field(default_factory=dict)
    active_buffs: list[ActiveBuff] = Field(default_factory=list)
    resonance_energy: dict[str, float] = Field(default_factory=dict)
    concerto_energy: dict[str, float] = Field(default_factory=dict)
    wasted_resonance_energy: dict[str, float] = Field(default_factory=dict)
    wasted_concerto_energy: dict[str, float] = Field(default_factory=dict)


class ActionResult(BaseModel):
    action_id: str
    action_name: str
    character_id: str | None
    start_time: float
    end_time: float
    damage: float
    valid: bool
    resonance_energy_gained: float = 0.0
    resonance_energy_wasted: float = 0.0
    concerto_energy_gained: float = 0.0
    concerto_energy_wasted: float = 0.0
    reason: str | None = None


class TimelineEntry(BaseModel):
    time_start: float
    time_end: float
    action_id: str
    action_name: str
    character_id: str | None
    damage: float
    active_character: str
    resonance_energy_gained: float = 0.0
    resonance_energy_wasted: float = 0.0
    concerto_energy_gained: float = 0.0
    concerto_energy_wasted: float = 0.0


class SimulationSummary(BaseModel):
    total_damage: float
    dps: float
    final_time: float
    active_character: str
    timeline: list[TimelineEntry]
    resources: dict[str, dict[str, float]]
