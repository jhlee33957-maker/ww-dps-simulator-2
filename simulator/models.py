from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


ActionType = Literal[
    "basic_attack",
    "heavy_attack",
    "resonance_skill",
    "resonance_liberation",
    "echo_skill",
    "swap",
    "wait",
]
DamageCategory = Literal["normal", "tune_break", "anomaly"]
AnomalyType = Literal["aero_erosion", "spectro_frazzle", "electro_flare", "havoc_bane"]
BuffModifierType = Literal["attack", "damage_bonus", "boost", "dmg_taken", "damage_amp"]
BuffTarget = Literal["self", "active", "team", "party", "next_active", "specific_character", "enemy"]


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
    damage_bonuses: dict[str, Any] = Field(default_factory=dict)
    element: str | None = None
    damage_attribute: str | None = None
    build_profile_id: str | None = None
    build_profile_display_name: str | None = None
    build_profile_description: str | None = None
    boost: float = 0.0
    attacker_level: int = Field(default=90, ge=1)
    def_ignore: float = 0.0
    final_dmg_bonus: float = 0.0
    resonance_energy: float = Field(ge=0)
    resonance_energy_max: float = Field(default=125.0, gt=0)
    energy_regen: float = Field(default=1.0, ge=0)
    concerto_energy: float = Field(ge=0)
    active: bool = False
    data_status: str | None = None
    is_dummy_sample: bool = False
    notes: str | None = None

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


class AnomalyState(BaseModel):
    # Temporary simulator assumptions: durations and tick intervals are not game-verified.
    anomaly_type: AnomalyType
    stacks: int = Field(default=0, ge=0)
    remaining_duration: float = Field(default=6.0, ge=0)
    tick_interval: float = Field(default=1.0, gt=0)
    tick_timer: float = Field(default=1.0, gt=0)


class HitData(BaseModel):
    time: float = Field(ge=0)
    damage_category: DamageCategory = "normal"
    damage_multiplier: float = Field(default=0.0, ge=0)
    tune_break_multiplier: float = Field(default=0.0, ge=0)
    tags: list[str] = Field(default_factory=list)
    name: str | None = None


class ActionData(BaseModel):
    id: str
    name: str
    character_id: str | None
    action_type: ActionType
    duration: float = Field(gt=0)
    action_time: float | None = Field(default=None, gt=0)
    combat_time_cost: float | None = Field(default=None, ge=0)
    cooldown: float = Field(ge=0)
    damage_category: DamageCategory = "normal"
    damage_bonus_category: str | None = None
    damage_element: str | None = None
    raw_skill_category: str | None = None
    raw_damage_type: str | None = None
    damage_bonus_category_source: str | None = None
    damage_multiplier: float = Field(default=0.0, ge=0)
    tune_break_multiplier: float = Field(default=0.0, ge=0)
    tune_break_boost_points: float = 0.0
    hits: list[HitData] = Field(default_factory=list)
    anomaly_type: AnomalyType | None = None
    anomaly_stacks: int = 0
    applies_anomaly_type: AnomalyType | None = None
    applies_anomaly_stacks: int = 0
    anomaly_duration: float = Field(default=6.0, gt=0)
    anomaly_tick_interval: float = Field(default=1.0, gt=0)
    resonance_energy_gain: float = 0.0
    concerto_energy_gain: float = 0.0
    resonance_energy_cost: float = Field(ge=0)
    applies_buffs: list[str] = Field(default_factory=list)
    required_buffs: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    policy_selectable: bool = True
    cooldown_group: str | None = None
    mechanic_effects: dict[str, Any] = Field(default_factory=dict)
    timing_overrides: dict[str, dict[str, float]] = Field(default_factory=dict)
    data_status: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def apply_legacy_fields(self) -> "ActionData":
        if self.applies_anomaly_type is None and self.anomaly_type is not None:
            self.applies_anomaly_type = self.anomaly_type
        if self.applies_anomaly_stacks <= 0 and self.anomaly_stacks > 0:
            self.applies_anomaly_stacks = self.anomaly_stacks
        return self

    @property
    def effective_action_time(self) -> float:
        return self.action_time if self.action_time is not None else self.duration

    @property
    def effective_combat_time_cost(self) -> float:
        return self.combat_time_cost if self.combat_time_cost is not None else self.effective_action_time

    def effective_hits(self) -> list[HitData]:
        if self.hits:
            return self.hits
        fallback_hits: list[HitData] = []
        if self.damage_multiplier > 0.0:
            fallback_hits.append(
                HitData(
                    time=0.0,
                    damage_category="normal",
                    damage_multiplier=self.damage_multiplier,
                    tags=self.tags,
                    name=f"{self.name} hit",
                )
            )
        if self.tune_break_multiplier > 0.0:
            fallback_hits.append(
                HitData(
                    time=0.0,
                    damage_category="tune_break",
                    tune_break_multiplier=self.tune_break_multiplier,
                    tags=self.tags,
                    name=f"{self.name} tune break",
                )
            )
        return fallback_hits


class BuffData(BaseModel):
    id: str
    name: str
    duration: float = Field(gt=0)
    modifier_type: BuffModifierType
    value: float
    target: BuffTarget
    target_scope: BuffTarget | None = None
    target_character_id: str | None = None
    affected_tags: list[str] = Field(default_factory=list)
    stat_modifiers: dict[str, float] = Field(default_factory=dict)
    damage_amp_modifiers: dict[str, float] = Field(default_factory=dict)
    stack_count: int = Field(default=1, ge=1)
    max_stacks: int = Field(default=1, ge=1)
    is_off_field: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ActiveBuff(BaseModel):
    buff_id: str
    source_character_id: str | None
    remaining_duration: float
    stack_count: int = Field(default=1, ge=1)
    target_character_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResourceChange(BaseModel):
    base_resonance_energy_gain: float = 0.0
    energy_regen: float = 1.0
    final_resonance_energy_gain: float = 0.0
    resonance_gained: float = 0.0
    resonance_wasted: float = 0.0
    concerto_before: float = 0.0
    concerto_gained: float = 0.0
    concerto_wasted: float = 0.0
    concerto_after: float = 0.0
    concerto_ready_after: bool = False


class CombatState(BaseModel):
    current_time: float = 0.0
    combat_time: float = 0.0
    combat_duration: float = 120.0
    total_damage: float = 0.0
    party_members: list[str] = Field(default_factory=list)
    active_character_id: str
    character_states: dict[str, dict[str, Any]] = Field(default_factory=dict)
    enemy_level: int = 90
    enemy_res: float = 0.1
    res_pen: float = 0.0
    def_reduction: float = 0.0
    dmg_taken: float = 0.0
    tune_dmg_bonus: float = 0.0
    cooldowns: dict[str, float] = Field(default_factory=dict)
    active_buffs: list[ActiveBuff] = Field(default_factory=list)
    team_buffs: list[ActiveBuff] = Field(default_factory=list)
    active_anomalies: dict[str, AnomalyState] = Field(default_factory=dict)
    character_mechanics_state: dict[str, dict] = Field(default_factory=dict)
    mechanics_config: dict[str, Any] = Field(default_factory=dict)
    action_log: list[dict[str, Any]] = Field(default_factory=list)
    damage_log: list[dict[str, Any]] = Field(default_factory=list)
    resonance_energy: dict[str, float] = Field(default_factory=dict)
    concerto_energy: dict[str, float] = Field(default_factory=dict)
    wasted_resonance_energy: dict[str, float] = Field(default_factory=dict)
    wasted_concerto_energy: dict[str, float] = Field(default_factory=dict)


class ActionResult(BaseModel):
    selected_action_id: str | None = None
    selected_action_name: str | None = None
    resolved_action_id: str | None = None
    resolved_action_name: str | None = None
    action_id: str
    action_name: str
    character_id: str | None
    actor_character_id: str | None = None
    active_character_before: str | None = None
    active_character_after: str | None = None
    start_time: float
    end_time: float
    action_time: float = 0.0
    combat_time_start: float = 0.0
    combat_time_end: float = 0.0
    combat_time_cost: float = 0.0
    effective_combat_time_cost: float = 0.0
    truncated_by_combat_limit: bool = False
    damage_before_cutoff: float = 0.0
    damage_after_cutoff_excluded: float = 0.0
    damage: float
    normal_damage: float = 0.0
    tune_break_damage: float = 0.0
    direct_anomaly_damage: float = 0.0
    anomaly_tick_damage: float = 0.0
    anomaly_damage: float = 0.0
    anomaly_damage_by_type: dict[str, float] = Field(default_factory=dict)
    total_action_damage: float = 0.0
    total_damage_after: float = 0.0
    hit_count: int = 0
    hit_damage_by_category: dict[str, float] = Field(default_factory=dict)
    hit_details: list[dict[str, Any]] = Field(default_factory=list)
    action_type: str | None = None
    damage_category: str = "other"
    damage_bonus_category: str = "other"
    damage_element: str = "generic"
    raw_skill_category: str | None = None
    raw_damage_type: str | None = None
    all_dmg_bonus: float = 0.0
    category_dmg_bonus: float = 0.0
    element_dmg_bonus: float = 0.0
    effective_damage_bonus: float = 0.0
    build_profile_id: str | None = None
    active_anomalies_after: dict[str, int] = Field(default_factory=dict)
    active_buffs: list[str] = Field(default_factory=list)
    applied_buffs: list[str] = Field(default_factory=list)
    outgoing_character_id: str | None = None
    incoming_character_id: str | None = None
    transition_type: str | None = None
    transition_reason: str | None = None
    outgoing_concerto_before: float = 0.0
    outgoing_concerto_ready: bool = False
    outgoing_concerto_consumed: bool = False
    outgoing_concerto_after: float = 0.0
    incoming_qte_candidate_id: str | None = None
    incoming_qte_mode: str | None = None
    incoming_qte_applied: bool = False
    incoming_qte_damage_bonus_category: str | None = None
    incoming_qte_trigger_classification: str | None = None
    incoming_qte_source_damage_label: str | None = None
    incoming_qte_previous_outro_trigger_frame: float | None = None
    incoming_qte_flow_light_metadata_present: bool = False
    incoming_qte_flow_light_applied: bool = False
    incoming_intro_candidate_id: str | None = None
    incoming_intro_mode: str | None = None
    incoming_intro_applied: bool = False
    incoming_intro_damage_bonus_category: str | None = None
    incoming_intro_trigger_classification: str | None = None
    incoming_intro_source_damage_label: str | None = None
    outgoing_outro_applied: bool = False
    transition_events: list[dict[str, Any]] = Field(default_factory=list)
    transition_event_details: list[dict[str, Any]] = Field(default_factory=list)
    outgoing_outro_event_id: str | None = None
    incoming_intro_event_id: str | None = None
    fallback_swap_used: bool = False
    swap_timing_is_placeholder: bool = False
    swap_timing_source: str | None = None
    transition_warnings: list[str] = Field(default_factory=list)
    valid: bool
    base_resonance_energy_gain: float = 0.0
    energy_regen: float = 1.0
    final_resonance_energy_gain: float = 0.0
    resonance_energy_gained: float = 0.0
    resonance_energy_wasted: float = 0.0
    concerto_before: float = 0.0
    concerto_gain: float = 0.0
    concerto_after: float = 0.0
    concerto_ready_after: bool = False
    concerto_energy_gained: float = 0.0
    concerto_energy_wasted: float = 0.0
    mechanic_debug_after: dict[str, Any] = Field(default_factory=dict)
    mornye_mode_after: str | None = None
    mornye_rest_mass_after: float | None = None
    mornye_wfo_remaining_after: float | None = None
    mornye_syntony_field_remaining_after: float | None = None
    mornye_er_excess_percent: float | None = None
    mornye_liberation_crit_rate_bonus: float | None = None
    mornye_liberation_crit_dmg_bonus: float | None = None
    mornye_interfered_marker_mode: str | None = None
    mornye_interfered_amp: float | None = None
    mornye_interfered_marker_applied: bool = False
    mornye_expectation_error_mode: str | None = None
    base_policy_action_id: str | None = None
    optimal_solution_triggered: bool = False
    optimal_solution_trigger_reason: str | None = None
    optimal_solution_candidate_id: str | None = None
    gp_success_modeled: bool = False
    implementation_status: str | None = None
    reason: str | None = None


class TimelineEntry(BaseModel):
    selected_action_id: str | None = None
    selected_action_name: str | None = None
    resolved_action_id: str | None = None
    resolved_action_name: str | None = None
    time_start: float
    time_end: float
    action_id: str
    action_name: str
    character_id: str | None
    actor_character_id: str | None = None
    active_character_before: str | None = None
    active_character_after: str | None = None
    action_time: float = 0.0
    combat_time_start: float = 0.0
    combat_time_end: float = 0.0
    combat_time_cost: float = 0.0
    effective_combat_time_cost: float = 0.0
    truncated_by_combat_limit: bool = False
    damage_before_cutoff: float = 0.0
    damage_after_cutoff_excluded: float = 0.0
    damage: float
    normal_damage: float = 0.0
    tune_break_damage: float = 0.0
    direct_anomaly_damage: float = 0.0
    anomaly_tick_damage: float = 0.0
    anomaly_damage: float = 0.0
    anomaly_damage_by_type: dict[str, float] = Field(default_factory=dict)
    total_action_damage: float = 0.0
    total_damage_after: float = 0.0
    hit_count: int = 0
    hit_damage_by_category: dict[str, float] = Field(default_factory=dict)
    hit_details: list[dict[str, Any]] = Field(default_factory=list)
    action_type: str | None = None
    damage_category: str = "other"
    damage_bonus_category: str = "other"
    damage_element: str = "generic"
    raw_skill_category: str | None = None
    raw_damage_type: str | None = None
    all_dmg_bonus: float = 0.0
    category_dmg_bonus: float = 0.0
    element_dmg_bonus: float = 0.0
    effective_damage_bonus: float = 0.0
    build_profile_id: str | None = None
    active_anomalies_after: dict[str, int] = Field(default_factory=dict)
    active_buffs: list[str] = Field(default_factory=list)
    applied_buffs: list[str] = Field(default_factory=list)
    outgoing_character_id: str | None = None
    incoming_character_id: str | None = None
    transition_type: str | None = None
    transition_reason: str | None = None
    outgoing_concerto_before: float = 0.0
    outgoing_concerto_ready: bool = False
    outgoing_concerto_consumed: bool = False
    outgoing_concerto_after: float = 0.0
    incoming_qte_candidate_id: str | None = None
    incoming_qte_mode: str | None = None
    incoming_qte_applied: bool = False
    incoming_qte_damage_bonus_category: str | None = None
    incoming_qte_trigger_classification: str | None = None
    incoming_qte_source_damage_label: str | None = None
    incoming_qte_previous_outro_trigger_frame: float | None = None
    incoming_qte_flow_light_metadata_present: bool = False
    incoming_qte_flow_light_applied: bool = False
    incoming_intro_candidate_id: str | None = None
    incoming_intro_mode: str | None = None
    incoming_intro_applied: bool = False
    incoming_intro_damage_bonus_category: str | None = None
    incoming_intro_trigger_classification: str | None = None
    incoming_intro_source_damage_label: str | None = None
    outgoing_outro_applied: bool = False
    transition_events: list[dict[str, Any]] = Field(default_factory=list)
    transition_event_details: list[dict[str, Any]] = Field(default_factory=list)
    outgoing_outro_event_id: str | None = None
    incoming_intro_event_id: str | None = None
    fallback_swap_used: bool = False
    swap_timing_is_placeholder: bool = False
    swap_timing_source: str | None = None
    transition_warnings: list[str] = Field(default_factory=list)
    active_character: str
    base_resonance_energy_gain: float = 0.0
    energy_regen: float = 1.0
    final_resonance_energy_gain: float = 0.0
    resonance_energy_gained: float = 0.0
    resonance_energy_wasted: float = 0.0
    concerto_before: float = 0.0
    concerto_gain: float = 0.0
    concerto_after: float = 0.0
    concerto_ready_after: bool = False
    concerto_energy_gained: float = 0.0
    concerto_energy_wasted: float = 0.0
    mechanic_debug_after: dict[str, Any] = Field(default_factory=dict)
    mornye_mode_after: str | None = None
    mornye_rest_mass_after: float | None = None
    mornye_wfo_remaining_after: float | None = None
    mornye_syntony_field_remaining_after: float | None = None
    mornye_er_excess_percent: float | None = None
    mornye_liberation_crit_rate_bonus: float | None = None
    mornye_liberation_crit_dmg_bonus: float | None = None
    mornye_interfered_marker_mode: str | None = None
    mornye_interfered_amp: float | None = None
    mornye_interfered_marker_applied: bool = False
    mornye_expectation_error_mode: str | None = None
    base_policy_action_id: str | None = None
    optimal_solution_triggered: bool = False
    optimal_solution_trigger_reason: str | None = None
    optimal_solution_candidate_id: str | None = None
    gp_success_modeled: bool = False
    implementation_status: str | None = None


class PartyState(BaseModel):
    party_members: list[str]
    active_character_id: str
    character_states: dict[str, dict[str, Any]]
    team_buffs: list[ActiveBuff] = Field(default_factory=list)
    enemy_state: dict[str, float] = Field(default_factory=dict)
    current_time: float = 0.0
    combat_time: float = 0.0
    combat_duration: float = 120.0
    total_damage: float = 0.0
    damage_log: list[dict[str, Any]] = Field(default_factory=list)
    action_log: list[dict[str, Any]] = Field(default_factory=list)
    cooldowns: dict[str, float] = Field(default_factory=dict)


class SimulationSummary(BaseModel):
    total_damage: float
    dps: float
    final_time: float
    final_action_time: float = 0.0
    active_character: str
    timeline: list[TimelineEntry]
    resources: dict[str, dict[str, float]]
    damage_by_selected_action: dict[str, float] = Field(default_factory=dict)
    damage_by_resolved_action: dict[str, float] = Field(default_factory=dict)
    damage_by_action_type: dict[str, float] = Field(default_factory=dict)
    damage_by_damage_bonus_category: dict[str, float] = Field(default_factory=dict)
