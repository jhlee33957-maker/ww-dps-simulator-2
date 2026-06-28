from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


ActionType = Literal[
    "basic_attack",
    "resonance_skill",
    "resonance_liberation",
    "echo_skill",
    "swap",
    "wait",
]
DamageCategory = Literal["normal", "tune_break", "anomaly"]
AnomalyType = Literal["aero_erosion", "spectro_frazzle", "electro_flare", "havoc_bane"]
BuffModifierType = Literal["attack", "damage_bonus", "boost", "dmg_taken"]
BuffTarget = Literal["self", "active", "team"]


class CharacterData(BaseModel):
    id: str
    name: str
    attack: float = Field(default=0.0, ge=0)
    character_base_atk: float = Field(default=0.0, ge=0)
    weapon_base_atk: float = Field(default=0.0, ge=0)
    atk_percent: float = 0.0
    flat_atk: float = 0.0
    crit_rate: float = Field(default=0.0, ge=0)
    crit_damage: float = Field(default=1.0, ge=0)
    damage_bonus: float = 0.0
    dmg_bonus: float = 0.0
    boost: float = 0.0
    attacker_level: int = Field(default=90, ge=1)
    def_ignore: float = 0.0
    final_dmg_bonus: float = 0.0
    resonance_energy: float = Field(ge=0)
    resonance_energy_max: float = Field(default=125.0, gt=0)
    concerto_energy: float = Field(ge=0)
    active: bool = False

    @model_validator(mode="after")
    def apply_legacy_defaults(self) -> "CharacterData":
        if self.character_base_atk <= 0.0 and self.weapon_base_atk <= 0.0 and self.attack > 0.0:
            self.character_base_atk = self.attack
        if self.attack <= 0.0:
            self.attack = self.character_base_atk + self.weapon_base_atk + self.flat_atk
        if self.dmg_bonus == 0.0 and self.damage_bonus != 0.0:
            self.dmg_bonus = self.damage_bonus
        if self.damage_bonus == 0.0 and self.dmg_bonus != 0.0:
            self.damage_bonus = self.dmg_bonus
        return self


class EnemyData(BaseModel):
    level: int = Field(default=90, ge=1)
    res: float = 0.1
    res_pen: float = 0.0
    def_reduction: float = 0.0
    dmg_taken: float = 0.0
    tune_dmg_bonus: float = 0.0


class ActionData(BaseModel):
    id: str
    name: str
    character_id: str | None
    action_type: ActionType
    duration: float = Field(gt=0)
    cooldown: float = Field(ge=0)
    damage_category: DamageCategory = "normal"
    damage_multiplier: float = Field(default=0.0, ge=0)
    tune_break_multiplier: float = Field(default=0.0, ge=0)
    tune_break_boost_points: float = 0.0
    anomaly_type: AnomalyType | None = None
    anomaly_stacks: int = 0
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
    enemy_level: int = 90
    enemy_res: float = 0.1
    res_pen: float = 0.0
    def_reduction: float = 0.0
    dmg_taken: float = 0.0
    tune_dmg_bonus: float = 0.0
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
    normal_damage: float = 0.0
    tune_break_damage: float = 0.0
    anomaly_damage: float = 0.0
    total_action_damage: float = 0.0
    total_damage_after: float = 0.0
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
    normal_damage: float = 0.0
    tune_break_damage: float = 0.0
    anomaly_damage: float = 0.0
    total_action_damage: float = 0.0
    total_damage_after: float = 0.0
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
