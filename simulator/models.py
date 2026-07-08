from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


ActionType = Literal[
    "basic_attack",
    "heavy_attack",
    "resonance_skill",
    "resonance_liberation",
    "echo_skill",
    "tune_break",
    "swap",
    "wait",
]
DamageCategory = Literal["normal", "tune_break", "anomaly"]
AnomalyType = Literal["aero_erosion", "spectro_frazzle", "electro_flare", "havoc_bane"]
BuffModifierType = Literal["attack", "damage_bonus", "boost", "dmg_taken", "damage_amp"]
BuffTarget = Literal["self", "active", "team", "party", "next_active", "specific_character", "enemy"]
ScalingStat = Literal["atk", "def", "hp", "none", "unresolved"]


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
    echo_sets: dict[str, Any] = Field(default_factory=dict)
    weapon: dict[str, Any] = Field(default_factory=dict)
    support_stats: dict[str, Any] = Field(default_factory=dict)
    element: str | None = None
    damage_attribute: str | None = None
    build_profile_id: str | None = None
    build_profile_display_name: str | None = None
    build_profile_description: str | None = None
    implementation_status: str | None = None
    profile_completeness_status: str = "fallback_character_stats"
    missing_required_fields: list[str] = Field(default_factory=list)
    profile_warnings: list[str] = Field(default_factory=list)
    stat_components: dict[str, Any] = Field(default_factory=dict)
    runtime_bonuses: dict[str, Any] = Field(default_factory=dict)
    default_scaling_stat: str = "atk"
    character_base_def: float = 0.0
    weapon_base_def: float = 0.0
    static_def_percent: float = 0.0
    static_flat_def: float = 0.0
    runtime_def_percent_bonus: float = 0.0
    runtime_def_flat_bonus: float = 0.0
    base_def_total: float = 0.0
    static_def: float = 0.0
    effective_def: float = 0.0
    final_def_reference: float | None = None
    def_reference_delta: float | None = None
    def_reference_delta_percent: float | None = None
    character_base_hp: float = 0.0
    weapon_base_hp: float = 0.0
    static_hp_percent: float = 0.0
    static_flat_hp: float = 0.0
    runtime_hp_percent_bonus: float = 0.0
    runtime_hp_flat_bonus: float = 0.0
    base_hp_total: float = 0.0
    static_hp: float = 0.0
    effective_hp: float = 0.0
    final_hp_reference: float | None = None
    hp_reference_delta: float | None = None
    hp_reference_delta_percent: float | None = None
    base_attack_total: float = 0.0
    base_atk_total: float = 0.0
    static_atk_percent: float = 0.0
    static_flat_atk: float = 0.0
    runtime_atk_percent_bonus: float = 0.0
    runtime_flat_atk_bonus: float = 0.0
    runtime_atk_flat_bonus: float = 0.0
    static_attack: float = 0.0
    static_atk: float = 0.0
    effective_attack: float = 0.0
    effective_atk: float = 0.0
    final_attack_reference: float | None = None
    final_atk_reference: float | None = None
    attack_reference_delta: float | None = None
    attack_reference_delta_percent: float | None = None
    atk_reference_delta: float | None = None
    atk_reference_delta_percent: float | None = None
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
        if self.static_atk_percent == 0.0 and self.atk_percent != 0.0:
            self.static_atk_percent = self.atk_percent
        if self.static_flat_atk == 0.0 and self.flat_atk != 0.0:
            self.static_flat_atk = self.flat_atk
        if self.base_attack_total <= 0.0:
            self.base_attack_total = self.character_base_atk + self.weapon_base_atk
        if self.base_atk_total <= 0.0:
            self.base_atk_total = self.base_attack_total
        if self.static_attack <= 0.0:
            self.static_attack = self.base_attack_total * (1.0 + self.static_atk_percent) + self.static_flat_atk
        if self.static_atk <= 0.0:
            self.static_atk = self.static_attack
        if self.runtime_atk_flat_bonus == 0.0 and self.runtime_flat_atk_bonus != 0.0:
            self.runtime_atk_flat_bonus = self.runtime_flat_atk_bonus
        if self.effective_attack <= 0.0:
            self.effective_attack = (
                self.static_attack
                + self.base_attack_total * self.runtime_atk_percent_bonus
                + self.runtime_flat_atk_bonus
            )
        if self.effective_atk <= 0.0:
            self.effective_atk = self.effective_attack
        if self.final_atk_reference is None and self.final_attack_reference is not None:
            self.final_atk_reference = self.final_attack_reference
        if self.atk_reference_delta is None:
            self.atk_reference_delta = self.attack_reference_delta
        if self.atk_reference_delta_percent is None:
            self.atk_reference_delta_percent = self.attack_reference_delta_percent
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
    scaling_stat: ScalingStat | None = None
    scaling_stat_source: str | None = None
    scaling_stat_source_status: str | None = None
    scaling_stat_note: str | None = None
    raw_skill_category: str | None = None
    raw_damage_type: str | None = None
    damage_bonus_category_source: str | None = None
    damage_multiplier: float = Field(default=0.0, ge=0)
    tune_break_multiplier: float = Field(default=0.0, ge=0)
    tune_break_boost_points: float = 0.0
    off_tune_value: float = 0.0
    off_tune_value_source_status: str | None = None
    off_tune_value_source_ref: str | None = None
    off_tune_value_alias_of: str | None = None
    off_tune_value_alias_note: str | None = None
    tune_break_action_time_source_status: str | None = None
    tune_break_element_source_status: str | None = None
    hits: list[HitData] = Field(default_factory=list)
    mechanic_event_tags: list[str] = Field(default_factory=list)
    mechanic_event_triggers: list[dict[str, Any]] = Field(default_factory=list)
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
    support_stat_modifiers: dict[str, float] = Field(default_factory=dict)
    damage_amp_modifiers: dict[str, float] = Field(default_factory=dict)
    damage_bonus_by_element: dict[str, float] = Field(default_factory=dict)
    source_character_id: str | None = None
    stacking_rule: str = "refresh_duration"
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
    mechanic_event_last_trigger_time: dict[str, float] = Field(default_factory=dict)
    mechanic_event_emitted_counts: dict[str, int] = Field(default_factory=dict)
    mechanic_event_log: list[dict[str, Any]] = Field(default_factory=list)
    echo_set_trigger_counts: dict[str, int] = Field(default_factory=dict)
    echo_set_buff_windows: list[dict[str, Any]] = Field(default_factory=list)
    high_syntony_field_buff_windows: list[dict[str, Any]] = Field(default_factory=list)
    action_log: list[dict[str, Any]] = Field(default_factory=list)
    damage_log: list[dict[str, Any]] = Field(default_factory=list)
    resonance_energy: dict[str, float] = Field(default_factory=dict)
    concerto_energy: dict[str, float] = Field(default_factory=dict)
    wasted_resonance_energy: dict[str, float] = Field(default_factory=dict)
    wasted_concerto_energy: dict[str, float] = Field(default_factory=dict)
    weapon_effect_cooldowns: dict[str, float] = Field(default_factory=dict)
    weapon_effect_trigger_counts: dict[str, int] = Field(default_factory=dict)
    weapon_effect_cooldown_blocked_counts: dict[str, int] = Field(default_factory=dict)
    weapon_effect_logs: list[dict[str, Any]] = Field(default_factory=list)
    weapon_effect_buff_windows: list[dict[str, Any]] = Field(default_factory=list)
    starfield_calibrator_concerto_restored_total: float = 0.0
    enemy_off_tune_max: float = 3920.0
    enemy_off_tune_current: float = 0.0
    enemy_mistune_active: bool = False
    enemy_mistune_entered_count: int = 0
    enemy_tune_break_available: bool = False
    enemy_tune_break_cooldown_seconds: float = 3.0
    enemy_tune_break_cooldown_source_status: str | None = "workbook_confirmed_cost4_red_name_boss_default"
    enemy_tune_break_cooldown_source_ref: str | None = "\u9644\u98752!B227"
    enemy_tune_break_cooldown_remaining: float = 0.0
    off_tune_accumulated_total: float = 0.0
    off_tune_overflow: float = 0.0
    off_tune_buildup_rate_used: float = 1.0
    off_tune_accumulation_blocked_by_tune_break_cooldown_count: int = 0
    off_tune_accumulation_logs: list[dict[str, Any]] = Field(default_factory=list)
    mapped_off_tune_action_count: int = 0
    unmapped_off_tune_action_ids: list[str] = Field(default_factory=list)
    unresolved_off_tune_damaging_action_ids: list[str] = Field(default_factory=list)
    off_tune_mapping_completeness_status: str = "not_checked"
    off_tune_value_mapping_source_report: str = "reports/off_tune_value_mapping_audit.md"
    target_tune_shift_state: str | None = None
    target_tune_shift_remaining: float = 0.0
    target_interfered_state: str | None = None
    target_interfered_remaining: float = 0.0
    target_tune_strain_interfered_stacks: int = 0
    target_tune_strain_interfered_max_stacks: int = 1
    target_tune_strain_interfered_remaining: float = 0.0
    lynae_tune_strain_damage_amp: float = 0.0
    lynae_tune_strain_damage_multiplier: float = 1.0
    lynae_tune_strain_damage_amp_bonus_damage: float = 0.0
    lynae_tune_strain_source_status: str | None = None
    lynae_tune_strain_source_ref: str | None = None
    interfered_marker_remaining: float = 0.0
    interfered_marker_applied_count: int = 0
    interfered_marker_damage_taken_amp: float = 0.0
    party_response_scan_logs: list[dict[str, Any]] = Field(default_factory=list)
    aemeath_starburst_response_cooldown_remaining: float = 0.0
    mornye_particle_jet_response_cooldown_remaining: float = 0.0
    lynae_spectral_analysis_response_cooldown_remaining: float = 0.0
    aemeath_starburst_trigger_count: int = 0
    mornye_particle_jet_trigger_count: int = 0
    lynae_spectral_analysis_trigger_count: int = 0
    aemeath_starburst_cooldown_blocked_count: int = 0
    mornye_particle_jet_cooldown_blocked_count: int = 0
    lynae_spectral_analysis_cooldown_blocked_count: int = 0
    tune_break_action_used_count: int = 0
    tune_break_damage_total: float = 0.0
    interfered_marker_direct_damage_amp_bonus_damage_total: float = 0.0
    interfered_marker_direct_damage_amp_applied_action_count: int = 0
    tune_response_damage_total: float = 0.0
    aemeath_starburst_damage_total: float = 0.0
    mornye_particle_jet_damage_total: float = 0.0
    lynae_spectral_analysis_damage_total: float = 0.0
    tune_response_events: list[dict[str, Any]] = Field(default_factory=list)
    tune_response_damage_formula_source_status: str = "workbook_confirmed"
    tune_response_event_order_source_status: str = "excel_event_order_derived"
    tune_break_damage_receives_new_interfered_marker_amp: bool = False
    response_damage_receives_interfered_marker_amp: bool = False
    response_damage_receives_newly_applied_interfered_marker_amp: bool = False
    response_damage_receives_existing_interfered_marker_amp: bool = False
    response_damage_receives_new_interfered_marker_amp: bool = False
    unresolved_response_damage_events: list[str] = Field(default_factory=list)
    simplified_assumptions: list[str] = Field(default_factory=list)


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
    combat_time_cost_source: str | None = None
    has_global_time_stop: bool = False
    global_time_stop_frames: float | None = None
    source_sheet: str | None = None
    source_rows: list[int] = Field(default_factory=list)
    truncated_by_combat_limit: bool = False
    damage_before_cutoff: float = 0.0
    damage_after_cutoff_excluded: float = 0.0
    damage: float
    normal_damage: float = 0.0
    tune_break_damage: float = 0.0
    direct_damage_taken_amp_total_bonus_damage: float = 0.0
    interfered_marker_direct_damage_amp_applied_count: int = 0
    interfered_marker_direct_damage_amp_bonus_damage: float = 0.0
    interfered_marker_direct_damage_amp_source_ref: str | None = None
    tune_break_damage_receives_existing_interfered_marker_amp: bool = False
    tune_break_damage_receives_newly_applied_interfered_marker_amp: bool = False
    tune_break_damage_before_target_amp: float = 0.0
    tune_break_damage_after_target_amp: float = 0.0
    generated_mechanic_damage: float = 0.0
    generated_mechanic_damage_total: float = 0.0
    generated_mechanic_hit_count: int = 0
    generated_mechanic_damage_events: list[dict[str, Any]] = Field(default_factory=list)
    aemeath_forte_generated_damage: float = 0.0
    aemeath_forte_generated_damage_total: float = 0.0
    aemeath_seraphic_duet_followup_triggered: bool = False
    aemeath_seraphic_duet_followup_damage: float = 0.0
    aemeath_seraphic_duet_followup_source_status: str | None = None
    aemeath_seraphic_duet_followup_mode: str | None = None
    aemeath_seraphic_duet_followup_variant: str | None = None
    aemeath_seraphic_duet_followup_repeat_count: int = 0
    aemeath_seraphic_duet_followup_multiplier: float = 0.0
    aemeath_rupturous_trail_stacks_before: int = 0
    aemeath_rupturous_trail_stacks_consumed: int = 0
    aemeath_rupturous_trail_stacks_after: int = 0
    aemeath_forte_enhancement_stacks_before: int = 0
    aemeath_forte_enhancement_stacks_consumed: int = 0
    aemeath_forte_enhancement_stacks_after: int = 0
    aemeath_trail_no_cost_consumed: bool = False
    aemeath_stardust_resonance_active_for_followup: bool = False
    aemeath_seraphic_duet_followup_source_rows: list[int] = Field(default_factory=list)
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
    runtime_element_damage_bonus: float = 0.0
    echo_set_damage_bonus: float = 0.0
    effective_damage_bonus: float = 0.0
    crit_rate_before_buffs: float = 0.0
    crit_rate_after_buffs: float = 0.0
    crit_damage_before_buffs: float = 0.0
    crit_damage_after_buffs: float = 0.0
    runtime_crit_damage_bonus: float = 0.0
    everbright_polestar_all_attribute_bonus_active: bool = False
    everbright_polestar_all_attribute_damage_bonus: float = 0.0
    runtime_all_attribute_damage_bonus: float = 0.0
    element_damage_bonus_before_weapon: float = 0.0
    element_damage_bonus_after_weapon: float = 0.0
    everbright_polestar_liberation_penetration_active: bool = False
    everbright_polestar_liberation_penetration_remaining: float = 0.0
    def_ignore_before_weapon: float = 0.0
    everbright_polestar_def_ignore_bonus: float = 0.0
    total_def_ignore: float = 0.0
    def_multiplier_before_weapon: float = 0.0
    def_multiplier_after_weapon: float = 0.0
    enemy_res_before_weapon: float = 0.0
    everbright_polestar_fusion_res_ignore_bonus: float = 0.0
    enemy_res_after_weapon: float = 0.0
    res_multiplier_before_weapon: float = 0.0
    res_multiplier_after_weapon: float = 0.0
    damage_element_fallback_used_for_weapon_res_ignore: bool = False
    build_profile_id: str | None = None
    scaling_stat: str | None = None
    scaling_value: float = 0.0
    stat_component_source: str | None = None
    unresolved_scaling_actions: list[str] = Field(default_factory=list)
    character_base_atk: float = 0.0
    weapon_base_atk: float = 0.0
    base_attack_total: float = 0.0
    base_atk_total: float = 0.0
    static_atk_percent: float = 0.0
    static_flat_atk: float = 0.0
    runtime_atk_percent_bonus: float = 0.0
    runtime_flat_atk_bonus: float = 0.0
    runtime_atk_flat_bonus: float = 0.0
    static_attack: float = 0.0
    static_atk: float = 0.0
    effective_attack: float = 0.0
    effective_atk: float = 0.0
    final_attack_reference: float | None = None
    final_atk_reference: float | None = None
    attack_reference_delta: float | None = None
    attack_reference_delta_percent: float | None = None
    atk_reference_delta: float | None = None
    atk_reference_delta_percent: float | None = None
    character_base_def: float = 0.0
    weapon_base_def: float = 0.0
    base_def_total: float = 0.0
    static_def_percent: float = 0.0
    static_flat_def: float = 0.0
    runtime_def_percent_bonus: float = 0.0
    runtime_def_flat_bonus: float = 0.0
    static_def: float = 0.0
    effective_def: float = 0.0
    final_def_reference: float | None = None
    def_reference_delta: float | None = None
    def_reference_delta_percent: float | None = None
    character_base_hp: float = 0.0
    weapon_base_hp: float = 0.0
    base_hp_total: float = 0.0
    static_hp_percent: float = 0.0
    static_flat_hp: float = 0.0
    runtime_hp_percent_bonus: float = 0.0
    runtime_hp_flat_bonus: float = 0.0
    static_hp: float = 0.0
    effective_hp: float = 0.0
    final_hp_reference: float | None = None
    hp_reference_delta: float | None = None
    hp_reference_delta_percent: float | None = None
    profile_completeness_status: str | None = None
    implementation_status: str | None = None
    base_off_tune_buildup_rate: float = 1.0
    runtime_off_tune_buildup_rate_bonus: float = 0.0
    current_off_tune_buildup_rate: float = 1.0
    base_tune_break_boost_points: float = 0.0
    runtime_tune_break_boost_points_bonus: float = 0.0
    current_tune_break_boost_points: float = 0.0
    syntony_field_off_tune_bonus_active: bool = False
    syntony_field_off_tune_bonus_value: float = 0.0
    c2_off_tune_bonus_active: bool = False
    mornye_constellation: int = 0
    mornye_heal_event_mode: str | None = None
    team_heal_event_triggered: bool = False
    high_syntony_field_active: bool = False
    high_syntony_field_remaining: float = 0.0
    high_syntony_field_created_count: int = 0
    high_syntony_field_def_bonus_active: bool = False
    high_syntony_field_def_percent_bonus: float = 0.0
    high_syntony_field_off_tune_inherited: bool = False
    high_syntony_field_heal_proxy_active: bool = False
    high_syntony_field_healing_multiplier_bonus: float = 0.0
    high_syntony_field_healing_multiplier_metadata_only: bool = True
    critical_protocol_high_syntony_created_before_damage: bool = False
    high_syntony_field_same_action_application: bool = False
    high_syntony_field_application_timing: str | None = None
    high_syntony_field_unavailable_reason: str | None = None
    off_tune_value: float = 0.0
    off_tune_value_source_status: str | None = None
    off_tune_value_source_ref: str | None = None
    off_tune_buildup_rate_used: float = 1.0
    off_tune_added: float = 0.0
    enemy_off_tune_current_before: float = 0.0
    enemy_off_tune_current_after: float = 0.0
    off_tune_accumulation_blocked_by_tune_break_cooldown: bool = False
    off_tune_value_before_block: float = 0.0
    enemy_off_tune_max: float = 3920.0
    enemy_mistune_active: bool = False
    enemy_tune_break_available: bool = False
    enemy_off_tune_current_after_tune_break: float = 0.0
    enemy_tune_break_cooldown_started: bool = False
    enemy_tune_break_cooldown_seconds: float = 3.0
    enemy_tune_break_cooldown_source_status: str | None = "workbook_confirmed_cost4_red_name_boss_default"
    enemy_tune_break_cooldown_source_ref: str | None = "\u9644\u98752!B227"
    enemy_tune_break_cooldown_remaining: float = 0.0
    enemy_mistune_entered_this_action: bool = False
    off_tune_accumulation_log: dict[str, Any] = Field(default_factory=dict)
    tune_break_action_available_ids: list[str] = Field(default_factory=list)
    tune_break_action_used_count: int = 0
    tune_break_damage_total: float = 0.0
    interfered_marker_direct_damage_amp_bonus_damage_total: float = 0.0
    interfered_marker_direct_damage_amp_applied_action_count: int = 0
    target_tune_shift_state: str | None = None
    target_tune_shift_remaining: float = 0.0
    target_interfered_state: str | None = None
    target_interfered_remaining: float = 0.0
    target_tune_strain_interfered_stacks: int = 0
    target_tune_strain_interfered_max_stacks: int = 1
    target_tune_strain_interfered_remaining: float = 0.0
    lynae_tune_strain_damage_amp: float = 0.0
    lynae_tune_strain_damage_multiplier: float = 1.0
    lynae_tune_strain_damage_amp_bonus_damage: float = 0.0
    lynae_tune_strain_source_status: str | None = None
    lynae_tune_strain_source_ref: str | None = None
    interfered_unavailable_reason: str | None = None
    observation_marker_active: bool = False
    observation_marker_remaining: float = 0.0
    interfered_marker_active: bool = False
    interfered_marker_remaining: float = 0.0
    interfered_marker_applied_count: int = 0
    interfered_marker_damage_taken_amp: float = 0.0
    interfered_marker_damage_taken_multiplier: float = 1.0
    mornye_energy_regen_for_interfered_marker: float = 1.0
    energy_regen_excess_for_interfered_marker: float = 0.0
    interfered_marker_cap_applied: bool = False
    interfered_marker_source: str | None = None
    interfered_marker_newly_applied_this_action: bool = False
    previous_interfered_marker_active_before_response: bool = False
    party_response_scan_triggered: bool = False
    tune_break_response_event_tags: list[str] = Field(default_factory=list)
    aemeath_starburst_triggered: bool = False
    aemeath_starburst_cooldown_blocked: bool = False
    aemeath_starburst_cooldown_started: bool = False
    aemeath_starburst_response_cooldown_remaining: float = 0.0
    aemeath_starburst_response_damage: float = 0.0
    aemeath_starburst_damage_total: float = 0.0
    aemeath_starburst_cooldown_blocked_count: int = 0
    aemeath_starburst_damage_unresolved: bool = False
    mornye_particle_jet_triggered: bool = False
    mornye_particle_jet_cooldown_blocked: bool = False
    mornye_particle_jet_cooldown_started: bool = False
    mornye_particle_jet_response_cooldown_remaining: float = 0.0
    mornye_particle_jet_response_damage: float = 0.0
    mornye_particle_jet_damage_total: float = 0.0
    mornye_particle_jet_cooldown_blocked_count: int = 0
    mornye_particle_jet_multiplier_used: float = 0.0
    mornye_particle_jet_constellation_variant: str | None = None
    mornye_particle_jet_damage_unresolved: bool = False
    lynae_spectral_analysis_triggered: bool = False
    lynae_spectral_analysis_cooldown_blocked: bool = False
    lynae_spectral_analysis_cooldown_started: bool = False
    lynae_spectral_analysis_response_cooldown_remaining: float = 0.0
    lynae_spectral_analysis_response_damage: float = 0.0
    lynae_spectral_analysis_damage_total: float = 0.0
    lynae_spectral_analysis_cooldown_blocked_count: int = 0
    lynae_spectral_analysis_multiplier_used: float = 0.0
    lynae_spectral_analysis_constellation_variant: str | None = None
    lynae_spectral_analysis_c2_disabled_by_default: bool = True
    response_source_status: str | None = None
    tune_response_damage: float = 0.0
    tune_response_damage_total: float = 0.0
    tune_response_hit_details: list[dict[str, Any]] = Field(default_factory=list)
    tune_response_events: list[dict[str, Any]] = Field(default_factory=list)
    tune_response_damage_formula_source_status: str | None = None
    tune_response_event_order_source_status: str | None = None
    tune_break_damage_receives_new_interfered_marker_amp: bool = False
    response_damage_receives_interfered_marker_amp: bool = False
    response_damage_receives_newly_applied_interfered_marker_amp: bool = False
    response_damage_receives_existing_interfered_marker_amp: bool = False
    response_damage_receives_new_interfered_marker_amp: bool = False
    unresolved_response_damage_events: list[str] = Field(default_factory=list)
    halo_atk_buff_does_not_affect_mornye_def_damage: bool = False
    halo_of_starry_radiance_5set_active: bool = False
    halo_of_starry_radiance_5set_atk_percent_bonus: float = 0.0
    halo_of_starry_radiance_5set_applied_before_field_creation_damage: bool = False
    halo_of_starry_radiance_5set_same_action_application: bool = False
    halo_of_starry_radiance_5set_application_timing: str | None = None
    halo_of_starry_radiance_5set_unavailable_reason: str | None = None
    pact_neonlight_incoming_atk_buff: bool = False
    pact_neonlight_incoming_atk_base: float = 0.0
    pact_neonlight_incoming_atk_from_tune_break_boost: float = 0.0
    pact_neonlight_incoming_atk_total: float = 0.0
    pact_neonlight_source_status: str | None = None
    lynae_static_mist_incoming_atk_buff: bool = False
    lynae_static_mist_incoming_atk_value: float = 0.0
    lynae_hyvatia_incoming_all_attribute_buff: bool = False
    lynae_hyvatia_incoming_all_attribute_value: float = 0.0
    lynae_outro_all_damage_amp_value: float = 0.0
    lynae_outro_liberation_damage_amp_value: float = 0.0
    lynae_liberation_party_damage_buff_active: bool = False
    lynae_liberation_party_damage_buff_value: float = 0.0
    lynae_overflow: float = 0.0
    lynae_overflow_max: float = 120.0
    lynae_lumiflow: float = 0.0
    lynae_true_color: float = 0.0
    lynae_kaleidoscopic_parade_remaining: float = 0.0
    lynae_optical_sampling_stage_active: bool = True
    lynae_resonance_mode: str | None = None
    lynae_photocromic_flux_active: bool = False
    lynae_photocromic_flux_applied: bool = False
    lynae_photocromic_flux_remaining: float = 0.0
    lynae_photocromic_flux_mode: str | None = None
    lynae_photocromic_flux_source_status: str | None = None
    lynae_photocromic_flux_unresolved_reason: str | None = None
    lynae_target_tune_shift_state: str | None = None
    lynae_target_tune_shift_remaining: float = 0.0
    lynae_spray_paint_window_remaining: float = 0.0
    lynae_visual_impact_cooldown_remaining: float = 0.0
    lynae_visual_impact_tune_break_boost_buff_active: bool = False
    lynae_visual_impact_tune_break_boost_value: float = 0.0
    lynae_to_vivid_tomorrow_window_remaining: float = 0.0
    emitted_mechanic_event_tags: list[str] = Field(default_factory=list)
    mechanic_event_triggered: bool = False
    mechanic_event_trigger_id: str | None = None
    mechanic_event_cooldown_blocked: bool = False
    aemeath_resonance_mode: str | None = None
    mechanic_event_source_status: str | None = None
    mechanic_event_unresolved_reason: str | None = None
    echo_set_triggered_buff_ids: list[str] = Field(default_factory=list)
    echo_set_buff_refreshed: bool = False
    weapon_effects_enabled: bool = False
    weapon_effect_triggered: bool = False
    weapon_effect_logs: list[dict[str, Any]] = Field(default_factory=list)
    weapon_effect_trigger_counts: dict[str, int] = Field(default_factory=dict)
    weapon_effect_cooldown_blocked_counts: dict[str, int] = Field(default_factory=dict)
    weapon_id: str | None = None
    weapon_rank: int = 0
    weapon_effect_id: str | None = None
    weapon_effect_type: str | None = None
    weapon_effect_resource: str | None = None
    weapon_effect_source_status: str | None = None
    concerto_energy_before_weapon_effect: float = 0.0
    concerto_energy_restored_by_weapon: float = 0.0
    concerto_energy_after_weapon_effect: float = 0.0
    concerto_energy_wasted_by_weapon: float = 0.0
    weapon_effect_cooldown_seconds: float = 0.0
    weapon_effect_cooldown_remaining: float = 0.0
    weapon_effect_cooldown_blocked: bool = False
    weapon_effect_buff_refreshed: bool = False
    weapon_effect_duration_seconds: float = 0.0
    starfield_calibrator_party_crit_damage_active: bool = False
    starfield_calibrator_party_crit_damage_bonus: float = 0.0
    starfield_calibrator_concerto_restore_trigger_count: int = 0
    starfield_calibrator_party_crit_damage_trigger_count: int = 0
    aemeath_trailblazing_star_5set_active: bool = False
    aemeath_trailblazing_star_5set_applied_before_triggering_damage: bool = False
    trailblazing_star_5set_same_action_application: bool = False
    trailblazing_star_5set_application_timing: str | None = None
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
    base_concerto_gain: float = 0.0
    passive_concerto_gain: float = 0.0
    final_concerto_gain: float = 0.0
    passive_concerto_source: str | None = None
    relative_momentum_gain: float = 0.0
    relative_momentum_gain_source_rows: list[int] = Field(default_factory=list)
    distributed_array_base_concerto_gain: float = 0.0
    distributed_array_relative_momentum_gain_per_hit: list[float] = Field(default_factory=list)
    distributed_array_relative_momentum_gain_total: float = 0.0
    time_dilation_type: str | None = None
    source_status: str | None = None
    mechanic_debug_after: dict[str, Any] = Field(default_factory=dict)
    mornye_mode_after: str | None = None
    mornye_rest_mass_after: float | None = None
    mornye_wfo_remaining_after: float | None = None
    mornye_syntony_field_remaining_after: float | None = None
    mornye_high_syntony_field_remaining_after: float | None = None
    mornye_er_excess_percent: float | None = None
    mornye_liberation_crit_rate_bonus: float | None = None
    mornye_liberation_crit_dmg_bonus: float | None = None
    mornye_interfered_marker_mode: str | None = None
    mornye_interfered_amp: float | None = None
    mornye_interfered_marker_applied: bool = False
    observation_marker_applied: bool = False
    interfered_marker_mode: str | None = None
    interfered_marker_applied_by_simplified_inversion: bool = False
    mornye_expectation_error_mode: str | None = None
    base_policy_action_id: str | None = None
    optimal_solution_triggered: bool = False
    optimal_solution_trigger_reason: str | None = None
    optimal_solution_candidate_id: str | None = None
    gp_success_modeled: bool = False
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
    combat_time_cost_source: str | None = None
    has_global_time_stop: bool = False
    global_time_stop_frames: float | None = None
    source_sheet: str | None = None
    source_rows: list[int] = Field(default_factory=list)
    truncated_by_combat_limit: bool = False
    damage_before_cutoff: float = 0.0
    damage_after_cutoff_excluded: float = 0.0
    damage: float
    normal_damage: float = 0.0
    tune_break_damage: float = 0.0
    direct_damage_taken_amp_total_bonus_damage: float = 0.0
    interfered_marker_direct_damage_amp_applied_count: int = 0
    interfered_marker_direct_damage_amp_bonus_damage: float = 0.0
    interfered_marker_direct_damage_amp_source_ref: str | None = None
    tune_break_damage_receives_existing_interfered_marker_amp: bool = False
    tune_break_damage_receives_newly_applied_interfered_marker_amp: bool = False
    tune_break_damage_before_target_amp: float = 0.0
    tune_break_damage_after_target_amp: float = 0.0
    generated_mechanic_damage: float = 0.0
    generated_mechanic_damage_total: float = 0.0
    generated_mechanic_hit_count: int = 0
    generated_mechanic_damage_events: list[dict[str, Any]] = Field(default_factory=list)
    aemeath_forte_generated_damage: float = 0.0
    aemeath_forte_generated_damage_total: float = 0.0
    aemeath_seraphic_duet_followup_triggered: bool = False
    aemeath_seraphic_duet_followup_damage: float = 0.0
    aemeath_seraphic_duet_followup_source_status: str | None = None
    aemeath_seraphic_duet_followup_mode: str | None = None
    aemeath_seraphic_duet_followup_variant: str | None = None
    aemeath_seraphic_duet_followup_repeat_count: int = 0
    aemeath_seraphic_duet_followup_multiplier: float = 0.0
    aemeath_rupturous_trail_stacks_before: int = 0
    aemeath_rupturous_trail_stacks_consumed: int = 0
    aemeath_rupturous_trail_stacks_after: int = 0
    aemeath_forte_enhancement_stacks_before: int = 0
    aemeath_forte_enhancement_stacks_consumed: int = 0
    aemeath_forte_enhancement_stacks_after: int = 0
    aemeath_trail_no_cost_consumed: bool = False
    aemeath_stardust_resonance_active_for_followup: bool = False
    aemeath_seraphic_duet_followup_source_rows: list[int] = Field(default_factory=list)
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
    runtime_element_damage_bonus: float = 0.0
    echo_set_damage_bonus: float = 0.0
    effective_damage_bonus: float = 0.0
    crit_rate_before_buffs: float = 0.0
    crit_rate_after_buffs: float = 0.0
    crit_damage_before_buffs: float = 0.0
    crit_damage_after_buffs: float = 0.0
    runtime_crit_damage_bonus: float = 0.0
    everbright_polestar_all_attribute_bonus_active: bool = False
    everbright_polestar_all_attribute_damage_bonus: float = 0.0
    runtime_all_attribute_damage_bonus: float = 0.0
    element_damage_bonus_before_weapon: float = 0.0
    element_damage_bonus_after_weapon: float = 0.0
    everbright_polestar_liberation_penetration_active: bool = False
    everbright_polestar_liberation_penetration_remaining: float = 0.0
    def_ignore_before_weapon: float = 0.0
    everbright_polestar_def_ignore_bonus: float = 0.0
    total_def_ignore: float = 0.0
    def_multiplier_before_weapon: float = 0.0
    def_multiplier_after_weapon: float = 0.0
    enemy_res_before_weapon: float = 0.0
    everbright_polestar_fusion_res_ignore_bonus: float = 0.0
    enemy_res_after_weapon: float = 0.0
    res_multiplier_before_weapon: float = 0.0
    res_multiplier_after_weapon: float = 0.0
    damage_element_fallback_used_for_weapon_res_ignore: bool = False
    build_profile_id: str | None = None
    scaling_stat: str | None = None
    scaling_value: float = 0.0
    stat_component_source: str | None = None
    unresolved_scaling_actions: list[str] = Field(default_factory=list)
    character_base_atk: float = 0.0
    weapon_base_atk: float = 0.0
    base_attack_total: float = 0.0
    base_atk_total: float = 0.0
    static_atk_percent: float = 0.0
    static_flat_atk: float = 0.0
    runtime_atk_percent_bonus: float = 0.0
    runtime_flat_atk_bonus: float = 0.0
    runtime_atk_flat_bonus: float = 0.0
    static_attack: float = 0.0
    static_atk: float = 0.0
    effective_attack: float = 0.0
    effective_atk: float = 0.0
    final_attack_reference: float | None = None
    final_atk_reference: float | None = None
    attack_reference_delta: float | None = None
    attack_reference_delta_percent: float | None = None
    atk_reference_delta: float | None = None
    atk_reference_delta_percent: float | None = None
    character_base_def: float = 0.0
    weapon_base_def: float = 0.0
    base_def_total: float = 0.0
    static_def_percent: float = 0.0
    static_flat_def: float = 0.0
    runtime_def_percent_bonus: float = 0.0
    runtime_def_flat_bonus: float = 0.0
    static_def: float = 0.0
    effective_def: float = 0.0
    final_def_reference: float | None = None
    def_reference_delta: float | None = None
    def_reference_delta_percent: float | None = None
    character_base_hp: float = 0.0
    weapon_base_hp: float = 0.0
    base_hp_total: float = 0.0
    static_hp_percent: float = 0.0
    static_flat_hp: float = 0.0
    runtime_hp_percent_bonus: float = 0.0
    runtime_hp_flat_bonus: float = 0.0
    static_hp: float = 0.0
    effective_hp: float = 0.0
    final_hp_reference: float | None = None
    hp_reference_delta: float | None = None
    hp_reference_delta_percent: float | None = None
    profile_completeness_status: str | None = None
    implementation_status: str | None = None
    base_off_tune_buildup_rate: float = 1.0
    runtime_off_tune_buildup_rate_bonus: float = 0.0
    current_off_tune_buildup_rate: float = 1.0
    base_tune_break_boost_points: float = 0.0
    runtime_tune_break_boost_points_bonus: float = 0.0
    current_tune_break_boost_points: float = 0.0
    syntony_field_off_tune_bonus_active: bool = False
    syntony_field_off_tune_bonus_value: float = 0.0
    c2_off_tune_bonus_active: bool = False
    mornye_constellation: int = 0
    mornye_heal_event_mode: str | None = None
    team_heal_event_triggered: bool = False
    high_syntony_field_active: bool = False
    high_syntony_field_remaining: float = 0.0
    high_syntony_field_created_count: int = 0
    high_syntony_field_def_bonus_active: bool = False
    high_syntony_field_def_percent_bonus: float = 0.0
    high_syntony_field_off_tune_inherited: bool = False
    high_syntony_field_heal_proxy_active: bool = False
    high_syntony_field_healing_multiplier_bonus: float = 0.0
    high_syntony_field_healing_multiplier_metadata_only: bool = True
    critical_protocol_high_syntony_created_before_damage: bool = False
    high_syntony_field_same_action_application: bool = False
    high_syntony_field_application_timing: str | None = None
    high_syntony_field_unavailable_reason: str | None = None
    off_tune_value: float = 0.0
    off_tune_value_source_status: str | None = None
    off_tune_value_source_ref: str | None = None
    off_tune_buildup_rate_used: float = 1.0
    off_tune_added: float = 0.0
    enemy_off_tune_current_before: float = 0.0
    enemy_off_tune_current_after: float = 0.0
    off_tune_accumulation_blocked_by_tune_break_cooldown: bool = False
    off_tune_value_before_block: float = 0.0
    enemy_off_tune_max: float = 3920.0
    enemy_mistune_active: bool = False
    enemy_tune_break_available: bool = False
    enemy_off_tune_current_after_tune_break: float = 0.0
    enemy_tune_break_cooldown_started: bool = False
    enemy_tune_break_cooldown_seconds: float = 3.0
    enemy_tune_break_cooldown_source_status: str | None = "workbook_confirmed_cost4_red_name_boss_default"
    enemy_tune_break_cooldown_source_ref: str | None = "\u9644\u98752!B227"
    enemy_tune_break_cooldown_remaining: float = 0.0
    enemy_mistune_entered_this_action: bool = False
    off_tune_accumulation_log: dict[str, Any] = Field(default_factory=dict)
    tune_break_action_available_ids: list[str] = Field(default_factory=list)
    tune_break_action_used_count: int = 0
    tune_break_damage_total: float = 0.0
    target_tune_shift_state: str | None = None
    target_tune_shift_remaining: float = 0.0
    target_interfered_state: str | None = None
    target_interfered_remaining: float = 0.0
    target_tune_strain_interfered_stacks: int = 0
    target_tune_strain_interfered_max_stacks: int = 1
    target_tune_strain_interfered_remaining: float = 0.0
    lynae_tune_strain_damage_amp: float = 0.0
    lynae_tune_strain_damage_multiplier: float = 1.0
    lynae_tune_strain_damage_amp_bonus_damage: float = 0.0
    lynae_tune_strain_source_status: str | None = None
    lynae_tune_strain_source_ref: str | None = None
    interfered_unavailable_reason: str | None = None
    observation_marker_active: bool = False
    observation_marker_remaining: float = 0.0
    interfered_marker_active: bool = False
    interfered_marker_remaining: float = 0.0
    interfered_marker_applied_count: int = 0
    interfered_marker_damage_taken_amp: float = 0.0
    interfered_marker_damage_taken_multiplier: float = 1.0
    mornye_energy_regen_for_interfered_marker: float = 1.0
    energy_regen_excess_for_interfered_marker: float = 0.0
    interfered_marker_cap_applied: bool = False
    interfered_marker_source: str | None = None
    interfered_marker_newly_applied_this_action: bool = False
    previous_interfered_marker_active_before_response: bool = False
    party_response_scan_triggered: bool = False
    tune_break_response_event_tags: list[str] = Field(default_factory=list)
    aemeath_starburst_triggered: bool = False
    aemeath_starburst_cooldown_blocked: bool = False
    aemeath_starburst_cooldown_started: bool = False
    aemeath_starburst_response_cooldown_remaining: float = 0.0
    aemeath_starburst_response_damage: float = 0.0
    aemeath_starburst_damage_total: float = 0.0
    aemeath_starburst_cooldown_blocked_count: int = 0
    aemeath_starburst_damage_unresolved: bool = False
    mornye_particle_jet_triggered: bool = False
    mornye_particle_jet_cooldown_blocked: bool = False
    mornye_particle_jet_cooldown_started: bool = False
    mornye_particle_jet_response_cooldown_remaining: float = 0.0
    mornye_particle_jet_response_damage: float = 0.0
    mornye_particle_jet_damage_total: float = 0.0
    mornye_particle_jet_cooldown_blocked_count: int = 0
    mornye_particle_jet_multiplier_used: float = 0.0
    mornye_particle_jet_constellation_variant: str | None = None
    mornye_particle_jet_damage_unresolved: bool = False
    lynae_spectral_analysis_triggered: bool = False
    lynae_spectral_analysis_cooldown_blocked: bool = False
    lynae_spectral_analysis_cooldown_started: bool = False
    lynae_spectral_analysis_response_cooldown_remaining: float = 0.0
    lynae_spectral_analysis_response_damage: float = 0.0
    lynae_spectral_analysis_damage_total: float = 0.0
    lynae_spectral_analysis_cooldown_blocked_count: int = 0
    lynae_spectral_analysis_multiplier_used: float = 0.0
    lynae_spectral_analysis_constellation_variant: str | None = None
    lynae_spectral_analysis_c2_disabled_by_default: bool = True
    response_source_status: str | None = None
    tune_response_damage: float = 0.0
    tune_response_damage_total: float = 0.0
    tune_response_hit_details: list[dict[str, Any]] = Field(default_factory=list)
    tune_response_events: list[dict[str, Any]] = Field(default_factory=list)
    tune_response_damage_formula_source_status: str | None = None
    tune_response_event_order_source_status: str | None = None
    tune_break_damage_receives_new_interfered_marker_amp: bool = False
    response_damage_receives_interfered_marker_amp: bool = False
    response_damage_receives_newly_applied_interfered_marker_amp: bool = False
    response_damage_receives_existing_interfered_marker_amp: bool = False
    response_damage_receives_new_interfered_marker_amp: bool = False
    unresolved_response_damage_events: list[str] = Field(default_factory=list)
    halo_atk_buff_does_not_affect_mornye_def_damage: bool = False
    halo_of_starry_radiance_5set_active: bool = False
    halo_of_starry_radiance_5set_atk_percent_bonus: float = 0.0
    halo_of_starry_radiance_5set_applied_before_field_creation_damage: bool = False
    halo_of_starry_radiance_5set_same_action_application: bool = False
    halo_of_starry_radiance_5set_application_timing: str | None = None
    halo_of_starry_radiance_5set_unavailable_reason: str | None = None
    pact_neonlight_incoming_atk_buff: bool = False
    pact_neonlight_incoming_atk_base: float = 0.0
    pact_neonlight_incoming_atk_from_tune_break_boost: float = 0.0
    pact_neonlight_incoming_atk_total: float = 0.0
    pact_neonlight_source_status: str | None = None
    lynae_static_mist_incoming_atk_buff: bool = False
    lynae_static_mist_incoming_atk_value: float = 0.0
    lynae_hyvatia_incoming_all_attribute_buff: bool = False
    lynae_hyvatia_incoming_all_attribute_value: float = 0.0
    lynae_outro_all_damage_amp_value: float = 0.0
    lynae_outro_liberation_damage_amp_value: float = 0.0
    lynae_liberation_party_damage_buff_active: bool = False
    lynae_liberation_party_damage_buff_value: float = 0.0
    lynae_overflow: float = 0.0
    lynae_overflow_max: float = 120.0
    lynae_lumiflow: float = 0.0
    lynae_true_color: float = 0.0
    lynae_kaleidoscopic_parade_remaining: float = 0.0
    lynae_optical_sampling_stage_active: bool = True
    lynae_resonance_mode: str | None = None
    lynae_photocromic_flux_active: bool = False
    lynae_photocromic_flux_applied: bool = False
    lynae_photocromic_flux_remaining: float = 0.0
    lynae_photocromic_flux_mode: str | None = None
    lynae_photocromic_flux_source_status: str | None = None
    lynae_photocromic_flux_unresolved_reason: str | None = None
    lynae_target_tune_shift_state: str | None = None
    lynae_target_tune_shift_remaining: float = 0.0
    lynae_spray_paint_window_remaining: float = 0.0
    lynae_visual_impact_cooldown_remaining: float = 0.0
    lynae_visual_impact_tune_break_boost_buff_active: bool = False
    lynae_visual_impact_tune_break_boost_value: float = 0.0
    lynae_to_vivid_tomorrow_window_remaining: float = 0.0
    emitted_mechanic_event_tags: list[str] = Field(default_factory=list)
    mechanic_event_triggered: bool = False
    mechanic_event_trigger_id: str | None = None
    mechanic_event_cooldown_blocked: bool = False
    aemeath_resonance_mode: str | None = None
    mechanic_event_source_status: str | None = None
    mechanic_event_unresolved_reason: str | None = None
    echo_set_triggered_buff_ids: list[str] = Field(default_factory=list)
    echo_set_buff_refreshed: bool = False
    weapon_effects_enabled: bool = False
    weapon_effect_triggered: bool = False
    weapon_effect_logs: list[dict[str, Any]] = Field(default_factory=list)
    weapon_effect_trigger_counts: dict[str, int] = Field(default_factory=dict)
    weapon_effect_cooldown_blocked_counts: dict[str, int] = Field(default_factory=dict)
    weapon_id: str | None = None
    weapon_rank: int = 0
    weapon_effect_id: str | None = None
    weapon_effect_type: str | None = None
    weapon_effect_resource: str | None = None
    weapon_effect_source_status: str | None = None
    concerto_energy_before_weapon_effect: float = 0.0
    concerto_energy_restored_by_weapon: float = 0.0
    concerto_energy_after_weapon_effect: float = 0.0
    concerto_energy_wasted_by_weapon: float = 0.0
    weapon_effect_cooldown_seconds: float = 0.0
    weapon_effect_cooldown_remaining: float = 0.0
    weapon_effect_cooldown_blocked: bool = False
    weapon_effect_buff_refreshed: bool = False
    weapon_effect_duration_seconds: float = 0.0
    starfield_calibrator_party_crit_damage_active: bool = False
    starfield_calibrator_party_crit_damage_bonus: float = 0.0
    starfield_calibrator_concerto_restore_trigger_count: int = 0
    starfield_calibrator_party_crit_damage_trigger_count: int = 0
    aemeath_trailblazing_star_5set_active: bool = False
    aemeath_trailblazing_star_5set_applied_before_triggering_damage: bool = False
    trailblazing_star_5set_same_action_application: bool = False
    trailblazing_star_5set_application_timing: str | None = None
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
    base_concerto_gain: float = 0.0
    passive_concerto_gain: float = 0.0
    final_concerto_gain: float = 0.0
    passive_concerto_source: str | None = None
    relative_momentum_gain: float = 0.0
    relative_momentum_gain_source_rows: list[int] = Field(default_factory=list)
    distributed_array_base_concerto_gain: float = 0.0
    distributed_array_relative_momentum_gain_per_hit: list[float] = Field(default_factory=list)
    distributed_array_relative_momentum_gain_total: float = 0.0
    time_dilation_type: str | None = None
    source_status: str | None = None
    mechanic_debug_after: dict[str, Any] = Field(default_factory=dict)
    mornye_mode_after: str | None = None
    mornye_rest_mass_after: float | None = None
    mornye_wfo_remaining_after: float | None = None
    mornye_syntony_field_remaining_after: float | None = None
    mornye_high_syntony_field_remaining_after: float | None = None
    mornye_er_excess_percent: float | None = None
    mornye_liberation_crit_rate_bonus: float | None = None
    mornye_liberation_crit_dmg_bonus: float | None = None
    mornye_interfered_marker_mode: str | None = None
    mornye_interfered_amp: float | None = None
    mornye_interfered_marker_applied: bool = False
    observation_marker_applied: bool = False
    interfered_marker_mode: str | None = None
    interfered_marker_applied_by_simplified_inversion: bool = False
    mornye_expectation_error_mode: str | None = None
    base_policy_action_id: str | None = None
    optimal_solution_triggered: bool = False
    optimal_solution_trigger_reason: str | None = None
    optimal_solution_candidate_id: str | None = None
    gp_success_modeled: bool = False


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
    selected_party_id: str | None = None
    active_party_build_profiles: dict[str, str] = Field(default_factory=dict)
    timeline: list[TimelineEntry]
    resources: dict[str, dict[str, float]]
    damage_by_selected_action: dict[str, float] = Field(default_factory=dict)
    damage_by_resolved_action: dict[str, float] = Field(default_factory=dict)
    damage_by_action_type: dict[str, float] = Field(default_factory=dict)
    damage_by_damage_bonus_category: dict[str, float] = Field(default_factory=dict)
    enemy_off_tune_current: float = 0.0
    enemy_off_tune_max: float = 3920.0
    enemy_mistune_active: bool = False
    enemy_tune_break_available: bool = False
    enemy_tune_break_cooldown_seconds: float = 3.0
    enemy_tune_break_cooldown_source_status: str | None = "workbook_confirmed_cost4_red_name_boss_default"
    enemy_tune_break_cooldown_source_ref: str | None = "\u9644\u98752!B227"
    enemy_tune_break_cooldown_remaining: float = 0.0
    off_tune_accumulated_total: float = 0.0
    off_tune_overflow: float = 0.0
    off_tune_accumulation_blocked_by_tune_break_cooldown_count: int = 0
    off_tune_accumulation_logs: list[dict[str, Any]] = Field(default_factory=list)
    mapped_off_tune_action_count: int = 0
    unmapped_off_tune_action_ids: list[str] = Field(default_factory=list)
    unresolved_off_tune_damaging_action_ids: list[str] = Field(default_factory=list)
    off_tune_mapping_completeness_status: str = "not_checked"
    off_tune_value_mapping_source_report: str = "reports/off_tune_value_mapping_audit.md"
    tune_break_action_available_ids: list[str] = Field(default_factory=list)
    tune_break_action_used_count: int = 0
    tune_break_damage_total: float = 0.0
    target_tune_shift_state: str | None = None
    target_interfered_state: str | None = None
    target_tune_strain_interfered_stacks: int = 0
    target_tune_strain_interfered_max_stacks: int = 1
    target_tune_strain_interfered_remaining: float = 0.0
    lynae_tune_strain_damage_amp: float = 0.0
    lynae_tune_strain_damage_multiplier: float = 1.0
    lynae_tune_strain_damage_amp_bonus_damage: float = 0.0
    lynae_tune_strain_source_status: str | None = None
    lynae_tune_strain_source_ref: str | None = None
    observation_marker_remaining: float = 0.0
    interfered_marker_remaining: float = 0.0
    interfered_marker_damage_taken_amp: float = 0.0
    party_response_scan_triggered: bool = False
    aemeath_starburst_trigger_count: int = 0
    mornye_particle_jet_trigger_count: int = 0
    lynae_spectral_analysis_trigger_count: int = 0
    aemeath_starburst_cooldown_blocked_count: int = 0
    mornye_particle_jet_cooldown_blocked_count: int = 0
    lynae_spectral_analysis_cooldown_blocked_count: int = 0
    aemeath_starburst_response_cooldown_remaining: float = 0.0
    mornye_particle_jet_response_cooldown_remaining: float = 0.0
    lynae_spectral_analysis_response_cooldown_remaining: float = 0.0
    tune_response_damage_total: float = 0.0
    aemeath_starburst_damage_total: float = 0.0
    mornye_particle_jet_damage_total: float = 0.0
    lynae_spectral_analysis_damage_total: float = 0.0
    tune_response_events: list[dict[str, Any]] = Field(default_factory=list)
    tune_response_damage_formula_source_status: str | None = None
    tune_response_event_order_source_status: str | None = None
    tune_break_damage_receives_new_interfered_marker_amp: bool = False
    response_damage_receives_interfered_marker_amp: bool = False
    response_damage_receives_newly_applied_interfered_marker_amp: bool = False
    response_damage_receives_existing_interfered_marker_amp: bool = False
    response_damage_receives_new_interfered_marker_amp: bool = False
    unresolved_response_damage_events: list[str] = Field(default_factory=list)
    simplified_assumptions: list[str] = Field(default_factory=list)
    aemeath_resonance_mode: str = "unresolved"
    aemeath_resonance_mode_source: str | None = None
    mechanic_event_trigger_action_ids: list[str] = Field(default_factory=list)
    mechanic_event_transition_trigger_action_ids: list[str] = Field(default_factory=list)
    mechanic_event_emitted_counts: dict[str, int] = Field(default_factory=dict)
    fusion_burst_event_count: int = 0
    tune_rupture_shifting_event_count: int = 0
    mechanic_event_unresolved_reason: str | None = None
    unsupported_aemeath_followup_mechanics: list[str] = Field(default_factory=list)
    active_echo_sets: dict[str, dict[str, Any]] = Field(default_factory=dict)
    active_weapons: dict[str, dict[str, Any]] = Field(default_factory=dict)
    weapon_effects_enabled: bool = False
    weapon_effect_trigger_counts: dict[str, int] = Field(default_factory=dict)
    weapon_effect_cooldown_blocked_counts: dict[str, int] = Field(default_factory=dict)
    weapon_effect_logs: list[dict[str, Any]] = Field(default_factory=list)
    weapon_effect_source_status: str | None = None
    starfield_calibrator_concerto_restore_trigger_count: int = 0
    starfield_calibrator_concerto_restored_total: float = 0.0
    starfield_calibrator_party_crit_damage_trigger_count: int = 0
    starfield_calibrator_party_crit_damage_uptime_seconds: float = 0.0
    starfield_calibrator_party_crit_damage_bonus: float = 0.0
    everbright_polestar_equipped: bool = False
    everbright_polestar_rank: int = 0
    everbright_polestar_all_attribute_damage_bonus: float = 0.0
    everbright_polestar_liberation_penetration_trigger_count: int = 0
    everbright_polestar_liberation_penetration_uptime_seconds: float = 0.0
    everbright_polestar_def_ignore_bonus: float = 0.0
    everbright_polestar_fusion_res_ignore_bonus: float = 0.0
    everbright_polestar_buff_windows: list[dict[str, Any]] = Field(default_factory=list)
    discord_concerto_restore_support_status: str | None = None
    echo_set_active_buffs: list[str] = Field(default_factory=list)
    aemeath_trailblazing_star_5set_enabled: bool = False
    aemeath_trailblazing_star_5set_trigger_event_tags: list[str] = Field(default_factory=list)
    aemeath_trailblazing_star_5set_trigger_count: int = 0
    aemeath_trailblazing_star_5set_uptime_seconds: float = 0.0
    aemeath_trailblazing_star_5set_buff_windows: list[dict[str, Any]] = Field(default_factory=list)
    base_off_tune_buildup_rate: float = 1.0
    runtime_off_tune_buildup_rate_bonus: float = 0.0
    current_off_tune_buildup_rate: float = 1.0
    base_tune_break_boost_points: float = 0.0
    runtime_tune_break_boost_points_bonus: float = 0.0
    current_tune_break_boost_points: float = 0.0
    syntony_field_off_tune_bonus_active: bool = False
    syntony_field_off_tune_bonus_value: float = 0.0
    c2_off_tune_bonus_active: bool = False
    mornye_constellation: int = 0
    mornye_heal_event_mode: str = "simplified_syntony_field_uptime"
    mornye_heal_event_mode_source: str | None = None
    team_heal_event_count: int = 0
    mornye_halo_of_starry_radiance_5set_enabled: bool = False
    mornye_halo_of_starry_radiance_5set_trigger_count: int = 0
    mornye_halo_of_starry_radiance_5set_atk_percent_bonus: float = 0.0
    mornye_halo_of_starry_radiance_5set_uptime_seconds: float = 0.0
    halo_of_starry_radiance_5set_unavailable_reason: str | None = None
    high_syntony_field_active: bool = False
    high_syntony_field_remaining: float = 0.0
    high_syntony_field_created_count: int = 0
    high_syntony_field_def_bonus_active: bool = False
    high_syntony_field_def_percent_bonus: float = 0.0
    high_syntony_field_off_tune_inherited: bool = False
    high_syntony_field_heal_proxy_active: bool = False
    high_syntony_field_healing_multiplier_bonus: float = 0.0
    critical_protocol_high_syntony_created_before_damage: bool = False
    high_syntony_field_same_action_application: bool = False
    high_syntony_field_application_timing: str | None = None
    runtime_def_percent_bonus: float = 0.0
    halo_of_starry_radiance_5set_active: bool = False
    halo_of_starry_radiance_5set_atk_percent_bonus: float = 0.0
    halo_atk_buff_does_not_affect_mornye_def_damage: bool = False
    high_syntony_field_unavailable_reason: str | None = None
