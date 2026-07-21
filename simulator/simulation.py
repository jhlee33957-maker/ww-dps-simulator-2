from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from characters.base import CharacterMechanic
from characters.registry import get_mechanic, get_mechanics_for_characters
from simulator.action_executor import (
    execute_action,
    execute_scheduled_action_packet,
    execute_scheduled_damage_event,
    is_action_valid,
    reduce_cooldowns,
    timeline_entry,
)
from simulator.action_timing_contract import (
    ActionTimingContract,
    advance_ongoing_action_runtime,
    handle_character_swap,
    load_action_timing_contracts,
    prepare_control_point_action,
    release_prior_owner_input_locks_for_followup,
    select_action_timing,
    start_ongoing_action,
)
from simulator.account_profile_gate import (
    AccountProfileSimulationBlocked,
    blocked_account_profile_messages,
    validate_simulation_readiness_for_characters,
)
from simulator.account_constellation_effects import (
    ACCOUNT_OBSERVATION_SHAPE,
    ACCOUNT_OBSERVATION_VERSION,
    after_account_action,
    advance_account_constellation_time,
    before_account_action,
    build_account_tune_response_damage_context,
    build_account_observation_labels,
    build_account_observation_values,
    apply_mornye_s1_interfered_marker,
    initialize_account_constellation_state,
    initialize_account_runtime_state,
    collect_constellation_diagnostics,
    on_account_transition,
)
from simulator.build_profiles import (
    build_action_scaling_summary,
    effective_build_stats_summary,
    load_build_profiles,
    resolve_character_build_stats,
    resolve_party_build_profiles,
    validate_effective_build_profiles,
)
from simulator.buff_system import add_team_buff, apply_buff, buffed_combat_stats, support_stat_context
from simulator.echo_sets import (
    AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID,
    HIGH_SYNTONY_SAME_ACTION_TIMING_MODE,
    MORNYE_HIGH_SYNTONY_FIELD_DEF_BUFF_ID,
    MORNYE_HIGH_SYNTONY_FIELD_OFF_TUNE_BUFF_ID,
    MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID,
    TEAM_HEAL_EVENT_TAG,
    active_echo_sets_for_characters,
    apply_pact_neonlight_outro_incoming_buff,
    apply_high_syntony_field_support_buffs,
    apply_mornye_halo_of_starry_radiance_5set_event_buff,
    apply_syntony_field_off_tune_buff,
    echo_set_active_buff_ids,
    merge_echo_set_logs,
    halo_of_starry_radiance_config,
    halo_of_starry_radiance_enabled,
    halo_of_starry_radiance_uptime_seconds,
    trailblazing_star_config,
    trailblazing_star_enabled,
    trailblazing_star_uptime_seconds,
)
from simulator.lynae_tune_strain import (
    apply_lynae_tune_strain_damage_amp,
    clear_lynae_tune_strain_state,
    lynae_tune_strain_max_stacks,
    refresh_lynae_tune_strain_amp,
)
from simulator.mechanic_events import aemeath_resonance_mode_from_config, mechanic_event_metadata_for_config
from simulator.models import (
    ActionData,
    BuffData,
    CharacterData,
    CombatState,
    EnemyData,
    PartyState,
    ScheduledPacketInstance,
    SimulationSummary,
    TimelineEntry,
)
from simulator.party_transition import (
    GENERIC_SWAP_SOURCE_STATUS,
    SWAP_REENTRY_COOLDOWN_SECONDS,
    build_transition_swap_action,
    default_transition_config,
    fallback_swap_timing,
    resolve_party_transition,
    swap_reentry_key,
)
from simulator.resource_system import apply_source_confirmed_scheduled_resource_gains, initialize_concerto_states
from simulator.roster import (
    get_initial_active_character,
    get_swap_target_character_id,
    is_swap_action,
    parse_party_character_ids,
    read_party_presets,
    resolve_party_preset,
)
from simulator.state import create_initial_state
from simulator.scheduled_effects import (
    advance_scheduled_effects as advance_scheduled_effect_states,
    remove_scheduled_effect as remove_scheduled_effect_state,
    schedule_effect as schedule_effect_state,
    scheduled_effect_by_instance_id as scheduled_effect_state_by_instance_id,
)
from simulator.transition_config import build_effective_transition_config, load_transition_config, mechanics_mode_summary
from simulator.tune_break import calculate_tune_response_damage_detail, current_interfered_damage_taken_amp
from simulator.weapon_effects import (
    STARFIELD_CALIBRATOR_BUFF_ID,
    active_weapons_for_characters,
    advance_weapon_effect_cooldowns,
    apply_weapon_mechanic_event_effects,
    apply_weapon_buff_effects,
    load_weapon_definition,
    process_weapon_effects_before_or_after_action,
    resolve_weapon_rank_value,
    weapon_effect_uptime_seconds,
    weapon_effects_enabled,
)


class Simulation:
    ROLE_FEMALE_SHEET = "\u89d2\u8272-\u5973"
    SKILL_TYPE_SHEET = "\u89d2\u8272\u6280\u80fd\u7c7b\u578b"
    MORNYE_SYNTONY_FIELD_DAMAGE_1_ACTION_REF = f"{ROLE_FEMALE_SHEET}!4126"
    MORNYE_SYNTONY_FIELD_DAMAGE_2_ACTION_REF = f"{ROLE_FEMALE_SHEET}!4127"
    MORNYE_SYNTONY_FIELD_DAMAGE_1_SKILL_REF = f"dmg/{SKILL_TYPE_SHEET}!2655"
    MORNYE_SYNTONY_FIELD_DAMAGE_2_SKILL_REF = f"dmg/{SKILL_TYPE_SHEET}!2656"
    MORNYE_SYNTONY_FIELD_DAMAGE_1_SOURCE_REF = (
        f"{MORNYE_SYNTONY_FIELD_DAMAGE_1_ACTION_REF} / {MORNYE_SYNTONY_FIELD_DAMAGE_1_SKILL_REF}"
    )
    MORNYE_SYNTONY_FIELD_DAMAGE_2_SOURCE_REF = (
        f"{MORNYE_SYNTONY_FIELD_DAMAGE_2_ACTION_REF} / {MORNYE_SYNTONY_FIELD_DAMAGE_2_SKILL_REF}"
    )
    MORNYE_SYNTONY_FIELD_DAMAGE_1_INSTANCE_ID = "mornye_syntony_field_damage_1:mornye"
    MORNYE_SYNTONY_FIELD_DAMAGE_2_INSTANCE_ID = "mornye_syntony_field_damage_2:mornye"
    MORNYE_SYNTONY_FIELD_HEAL_INSTANCE_ID = "mornye_syntony_field_heal:mornye"
    MORNYE_HIGH_SYNTONY_FIELD_HEAL_INSTANCE_ID = "mornye_high_syntony_field_heal:mornye"
    MORNYE_SYNTONY_FIELD_DAMAGE_1_ACTION_ID = "mornye_syntony_field_damage"
    MORNYE_SYNTONY_FIELD_DAMAGE_2_ACTION_ID = "mornye_syntony_field_target_damage"
    MORNYE_SYNTONY_FIELD_HEAL_ACTION_ID = "mornye_syntony_field_heal"
    MORNYE_HIGH_SYNTONY_FIELD_HEAL_ACTION_ID = "mornye_high_syntony_field_heal"
    LYNAE_SPRAY_PAINT_INSTANCE_ID = "lynae_spray_paint_flux:lynae"
    LYNAE_SPRAY_PAINT_PAYLOAD_ACTION_ID = "lynae_spray_paint_flux_application"
    AEMEATH_SIGILLUM_ACTION_ID = "aemeath_echo_sigillum"
    AEMEATH_SIGILLUM_HIT_1_ACTION_ID = "aemeath_echo_sigillum_hit_1"
    AEMEATH_SIGILLUM_HIT_2_ACTION_ID = "aemeath_echo_sigillum_hit_2"
    AEMEATH_SIGILLUM_SOURCE_REF = "\u58f0\u9ab8!410:411 / dmg!2632:2633"
    AEMEATH_SIGILLUM_HIT_SOURCE_REFS = {
        1: "\u58f0\u9ab8!410 / dmg!2632",
        2: "\u58f0\u9ab8!411 / dmg!2633",
    }

    def __init__(
        self,
        characters: dict[str, CharacterData],
        actions: dict[str, ActionData],
        buffs: dict[str, BuffData],
        combat_duration: float = 120.0,
        enemy: EnemyData | None = None,
        selected_character_ids: list[str] | str | None = None,
        initial_active_character: str | None = None,
        transition_config: dict | None = None,
        party_preset_config: dict | None = None,
        active_build_profiles: dict[str, str] | None = None,
        stat_overrides: dict[str, dict[str, float]] | None = None,
        tune_response_defs: dict[str, dict[str, Any]] | None = None,
        weapon_definitions: dict[str, Any] | None = None,
        account_simulation_scope: dict[str, Any] | str | None = None,
        precombat_elapsed_seconds: float | None = None,
        account_optical_sampling_active: bool = False,
        action_timing_contracts: dict[str, ActionTimingContract] | None = None,
        timing_runtime_config: dict[str, Any] | None = None,
    ) -> None:
        self.all_characters = characters
        self.selected_character_ids = parse_party_character_ids(selected_character_ids, characters)
        self.selected_party_character_ids = self.selected_character_ids
        self.party_character_ids = self.selected_character_ids
        self.selected_party = self.selected_character_ids
        self.initial_active_character = get_initial_active_character(self.selected_character_ids, initial_active_character)
        self.transition_config = transition_config or default_transition_config()
        self.party_preset_config = party_preset_config or {}
        self.active_build_profiles = active_build_profiles or {
            character_id: character.build_profile_id
            for character_id, character in characters.items()
            if character.build_profile_id is not None
        }
        self.stat_overrides = stat_overrides or {}
        self.account_simulation_scope = account_simulation_scope
        self.precombat_elapsed_seconds = precombat_elapsed_seconds
        self.account_optical_sampling_active = bool(account_optical_sampling_active)
        self.account_constellation_state: dict[str, Any] | None = None
        self.account_constellation_diagnostics: dict[str, Any] = {}
        self.tune_response_defs = dict(tune_response_defs or self._default_tune_response_defs())
        self.weapon_definitions = dict(weapon_definitions or {})
        self.preset_generic_swap = self.party_preset_config.get("generic_swap", {})
        self.characters = {
            character_id: characters[character_id]
            for character_id in self.selected_character_ids
        }
        self.actions = dict(actions)
        self.action_timing_contracts = dict(action_timing_contracts or {})
        self._ensure_party_swap_actions()
        self.actions_by_id = self.actions
        self.policy_actions = self._build_policy_actions()
        self.action_scaling_summary = build_action_scaling_summary(self.actions.values(), self.selected_character_ids)
        self.effective_build_stats_summary = effective_build_stats_summary(self.characters, self.action_scaling_summary)
        self.build_profile_validation = validate_effective_build_profiles(self.effective_build_stats_summary)
        self.account_profile_gate_errors = blocked_account_profile_messages(
            self.characters,
            account_scope=self.account_simulation_scope,
            precombat_elapsed_seconds=self.precombat_elapsed_seconds,
        )
        self.buffs = buffs
        self.weapon_effects_enabled = weapon_effects_enabled(self.characters, self.weapon_definitions)
        self.combat_duration = combat_duration
        self.enemy = enemy or EnemyData()
        self.state: CombatState = create_initial_state(self.characters, self.enemy, self.initial_active_character)
        # The live result is intentionally not serialized. Search-mode callers
        # use it for exact selected/resolved parity and performance diagnostics.
        self.last_action_result = None
        self.state.combat_duration = self.combat_duration
        self.state.mechanics_config = dict(self.transition_config.get("mechanics") or {})
        if timing_runtime_config and bool(timing_runtime_config.get("timing_runtime_enabled", False)):
            self.state.mechanics_config["timing_runtime"] = {
                "swap_reentry_cooldown_clock": str(
                    timing_runtime_config.get("effective_swap_reentry_clock", "combat_time")
                ),
                "swap_reentry_cooldown_clock_source": timing_runtime_config.get(
                    "effective_swap_reentry_clock_source"
                ),
                "historical_swap_reentry_clock": str(
                    timing_runtime_config.get("historical_swap_reentry_clock", "combat_time")
                ),
            }
        tune_break_config = self._tune_break_system_config()
        self.state.enemy_off_tune_max = float(tune_break_config.get("enemy_off_tune_max", 3920.0) or 3920.0)
        self.state.enemy_tune_break_cooldown_seconds = float(
            tune_break_config.get("enemy_tune_break_cooldown_seconds", 3.0) or 3.0
        )
        self.state.enemy_tune_break_cooldown_source_status = str(
            tune_break_config.get(
                "enemy_tune_break_cooldown_source_status",
                "workbook_confirmed_cost4_red_name_boss_default",
            )
        )
        self.state.enemy_tune_break_cooldown_source_ref = str(
            tune_break_config.get("enemy_tune_break_cooldown_source_ref", "\u9644\u98752!B227")
        )
        self.state.off_tune_value_mapping_source_report = "reports/off_tune_value_mapping_audit.md"
        self._refresh_off_tune_mapping_metadata()
        if not self.account_profile_gate_errors and any(character.account_profile for character in self.characters.values()):
            self.account_constellation_state = initialize_account_constellation_state(
                self.characters,
                self.account_simulation_scope,
                float(self.precombat_elapsed_seconds or 0.0),
                optical_sampling_active=self.account_optical_sampling_active,
            )
            self.account_constellation_diagnostics = collect_constellation_diagnostics(self.account_constellation_state)
        self.state.simplified_assumptions.append(
            "single_target_enemy_off_tune_state"
        )
        self.character_mechanics = get_mechanics_for_characters(self.selected_character_ids)
        for mechanic in self.character_mechanics.values():
            mechanic.initialize_state(self.state)
        for character_id in self.selected_character_ids:
            self.state.character_mechanics_state.setdefault(character_id, {})
        self.state.character_states = self.state.character_mechanics_state
        for character_id, character in self.characters.items():
            self.state.character_states.setdefault(character_id, {})["energy_regen"] = character.energy_regen
        initialize_concerto_states(
            self.state,
            self.selected_character_ids,
            default_cap=float(
                (self.transition_config.get("concerto_transition") or {}).get("default_concerto_cap", 100.0)
            ),
        )
        initialize_account_runtime_state(self)
        self.timeline: list[TimelineEntry] = []

    @classmethod
    def from_json(
        cls,
        data_dir: Path | str,
        selected_character_ids: list[str] | str | None = None,
        selected_party_character_ids: list[str] | str | None = None,
        party_character_ids: list[str] | str | None = None,
        party: list[str] | str | None = None,
        initial_active_character: str | None = None,
        transition_config: dict | None = None,
        build_profile_overrides: dict[str, str] | None = None,
        stat_overrides: dict[str, dict[str, float]] | None = None,
        account_simulation_scope: dict[str, Any] | str | None = None,
        precombat_elapsed_seconds: float | None = None,
        account_optical_sampling_active: bool = False,
    ) -> "Simulation":
        data_path = Path(data_dir)
        characters = {
            item["id"]: CharacterData.model_validate(item)
            for item in _read_json(data_path / "characters.json")
        }
        actions = {
            item["id"]: ActionData.model_validate(item)
            for item in _read_json(data_path / "actions.json")
        }
        buffs = {
            item["id"]: BuffData.model_validate(item)
            for item in _read_json(data_path / "buffs.json")
        }
        weapon_definitions = load_weapon_definition(data_path)
        tune_response_path = data_path / "tune_responses.json"
        tune_response_defs = (
            {item["id"]: item for item in _read_json(tune_response_path)}
            if tune_response_path.exists()
            else cls._default_tune_response_defs()
        )
        enemy_path = data_path / "enemy.json"
        enemy = EnemyData.model_validate(_read_json_object(enemy_path)) if enemy_path.exists() else EnemyData()
        party_presets = read_party_presets(data_path)
        selection_value = (
            selected_character_ids
            if selected_character_ids is not None
            else selected_party_character_ids
            if selected_party_character_ids is not None
            else party_character_ids
            if party_character_ids is not None
            else party
        )
        party_preset_config = (
            party_presets.get(selection_value)
            if isinstance(selection_value, str)
            else None
        )
        content_start = _account_content_start_for_party(data_path, party_preset_config)
        if account_simulation_scope is None and party_preset_config and party_preset_config.get("account_scope"):
            account_simulation_scope = party_preset_config["account_scope"]
        if content_start:
            if precombat_elapsed_seconds is None:
                precombat_elapsed_seconds = float(content_start["precombat_elapsed_seconds"])
            if not account_optical_sampling_active:
                account_optical_sampling_active = bool(content_start["account_optical_sampling_active"])
            if initial_active_character is None:
                initial_active_character = str(content_start["initial_active_character"])
        selection_value, preset_initial_active = resolve_party_preset(selection_value, party_presets)
        selected_ids = parse_party_character_ids(selection_value, characters)
        build_profiles = load_build_profiles(data_path)
        active_build_profiles = resolve_party_build_profiles(
            party_preset_config,
            cli_overrides=build_profile_overrides,
            selected_character_ids=selected_ids,
            build_profiles=build_profiles,
        )
        characters = {
            character_id: (
                resolve_character_build_stats(
                    character,
                    active_build_profiles.get(character_id),
                    build_profiles,
                    stat_overrides=(stat_overrides or {}).get(character_id),
                )
                if character_id in selected_ids
                else character
            )
            for character_id, character in characters.items()
        }
        base_transition_config = transition_config or load_transition_config(data_path)
        effective_transition_config = (
            base_transition_config
            if transition_config is not None
            else build_effective_transition_config(base_transition_config, party_preset_config)
        )
        return cls(
            characters=characters,
            actions=actions,
            buffs=buffs,
            enemy=enemy,
            selected_character_ids=selection_value,
            initial_active_character=initial_active_character or preset_initial_active,
            transition_config=effective_transition_config,
            party_preset_config=party_preset_config,
            active_build_profiles={
                character_id: profile_id
                for character_id, profile_id in active_build_profiles.items()
                if character_id in selected_ids
            },
            stat_overrides={
                character_id: overrides
                for character_id, overrides in (stat_overrides or {}).items()
                if character_id in selected_ids
            },
            tune_response_defs=tune_response_defs,
            weapon_definitions=weapon_definitions,
            account_simulation_scope=account_simulation_scope,
            precombat_elapsed_seconds=precombat_elapsed_seconds,
            account_optical_sampling_active=account_optical_sampling_active,
            action_timing_contracts=load_action_timing_contracts(data_path),
            timing_runtime_config=(
                _read_json_object(data_path / "timing_runtime_gate_v124.json")
                if (data_path / "timing_runtime_gate_v124.json").exists()
                else None
            ),
        )
    def validate_build_profiles(self) -> dict[str, object]:
        self.action_scaling_summary = build_action_scaling_summary(self.actions.values(), self.selected_character_ids)
        self.effective_build_stats_summary = effective_build_stats_summary(self.characters, self.action_scaling_summary)
        self.build_profile_validation = validate_effective_build_profiles(self.effective_build_stats_summary)
        self.account_profile_gate_errors = blocked_account_profile_messages(
            self.characters,
            account_scope=self.account_simulation_scope,
            precombat_elapsed_seconds=self.precombat_elapsed_seconds,
        )
        return dict(self.build_profile_validation)

    def validate_simulation_readiness(self, *, entry_point: str = "simulator execution") -> None:
        validate_simulation_readiness_for_characters(
            self.characters,
            entry_point=entry_point,
            account_scope=self.account_simulation_scope,
            precombat_elapsed_seconds=self.precombat_elapsed_seconds,
        )
        aemeath = self.characters.get("aemeath")
        if aemeath is not None and bool(getattr(aemeath, "account_profile", False)) and int(getattr(aemeath, "sequence", 0) or 0) >= 6:
            mode = aemeath_resonance_mode_from_config(self.state.mechanics_config)
            if mode not in {"tune_rupture", "fusion_burst"}:
                raise AccountProfileSimulationBlocked(
                    f"{entry_point} rejected: Aemeath Sequence 6 account profile requires an explicit "
                    "aemeath_resonance_mode of 'tune_rupture' or 'fusion_burst'; unresolved is not executable."
                )

    def account_observation_labels(self) -> list[str]:
        return build_account_observation_labels()

    def account_observation_values(self) -> list[float]:
        return build_account_observation_values(self)

    def account_observation_metadata(self) -> dict[str, Any]:
        return {
            "observation_version": ACCOUNT_OBSERVATION_VERSION,
            "observation_shape": ACCOUNT_OBSERVATION_SHAPE,
            "legacy_v5_prefix_shape": 314,
            "policy_action_count": len(self.get_policy_action_ids()),
        }

    def set_enemy_context(
        self,
        *,
        enemy_level: int | None = None,
        enemy_res: float | None = None,
        res_pen: float | None = None,
        def_reduction: float | None = None,
        dmg_taken: float | None = None,
        tune_dmg_bonus: float | None = None,
    ) -> None:
        if enemy_level is not None:
            self.state.enemy_level = enemy_level
        if enemy_res is not None:
            self.state.enemy_res = enemy_res
        if res_pen is not None:
            self.state.res_pen = res_pen
        if def_reduction is not None:
            self.state.def_reduction = def_reduction
        if dmg_taken is not None:
            self.state.dmg_taken = dmg_taken
        if tune_dmg_bonus is not None:
            self.state.tune_dmg_bonus = tune_dmg_bonus

    def schedule_effect(
        self,
        *,
        instance_id: str,
        effect_id: str,
        source_character_id: str,
        payload_action_id: str,
        remaining_duration: float,
        tick_interval: float,
        time_until_next_tick: float | None = None,
        source_action_id: str | None = None,
        trigger_count: int = 0,
        max_trigger_count: int | None = None,
        refresh_rule: str = "replace",
        payload_event_type: str = "damage",
        scheduled_resource_policy: str = "none",
        source_status: str = "scheduler_test_fixture",
        source_ref: str | None = None,
        metadata: dict[str, Any] | None = None,
        trigger_on_apply: bool = False,
        activation_combat_time: float | None = None,
    ) -> dict[str, Any]:
        activation_time = (
            float(self.state.combat_time)
            if activation_combat_time is None
            else max(0.0, float(activation_combat_time))
        )
        result = schedule_effect_state(
            self.state,
            actions=self.actions,
            selected_character_ids=set(self.selected_character_ids),
            instance_id=instance_id,
            effect_id=effect_id,
            source_character_id=source_character_id,
            source_action_id=source_action_id,
            payload_action_id=payload_action_id,
            remaining_duration=remaining_duration,
            tick_interval=tick_interval,
            time_until_next_tick=time_until_next_tick,
            activation_combat_time=activation_time,
            trigger_on_apply=trigger_on_apply,
            trigger_count=trigger_count,
            max_trigger_count=max_trigger_count,
            refresh_rule=refresh_rule,
            payload_event_type=payload_event_type,
            scheduled_resource_policy=scheduled_resource_policy,
            source_status=source_status,
            source_ref=source_ref,
            metadata=metadata,
        )
        effect = result["effect"]
        if (
            trigger_on_apply
            and result.get("operation") in {"created", "replaced"}
            and activation_time <= float(self.state.combat_time) + 1e-9
        ):
            trigger_index = int(effect.trigger_count) + 1
            event = self.execute_scheduled_effect_event(
                effect=effect,
                host_action_id=source_action_id or "__schedule_effect__",
                host_actor_character_id=source_character_id,
                host_combat_start_time=activation_time,
                host_combat_end_time=activation_time,
                combat_time=activation_time,
                host_action_combat_offset=0.0,
                trigger_index=trigger_index,
            )
            effect.trigger_count = trigger_index
            effect.trigger_on_apply_pending = False
            effect.time_until_next_tick = float(effect.tick_interval)
            self.state.total_damage += float(event.get("damage", 0.0) or 0.0)
            result["trigger_on_apply_event"] = event
            result["immediate_trigger_executed"] = True
            result["immediate_trigger_pending"] = False
            if effect.max_trigger_count is not None and effect.trigger_count >= effect.max_trigger_count:
                remove_scheduled_effect_state(self.state, effect.instance_id)
        elif result.get("operation") in {"created", "replaced"}:
            result["immediate_trigger_pending"] = bool(effect.trigger_on_apply_pending)
            result["immediate_trigger_executed"] = False
        return result

    def remove_scheduled_effect(self, instance_id: str):
        return remove_scheduled_effect_state(self.state, instance_id)

    def scheduled_effect_by_instance_id(self, instance_id: str):
        return scheduled_effect_state_by_instance_id(self.state, instance_id)

    def advance_scheduled_effects(
        self,
        *,
        host_action: ActionData,
        combat_start_time: float,
        combat_elapsed: float,
        action_start_snapshot: Any | None = None,
        force_active_buff_ids: set[str] | None = None,
    ) -> dict[str, Any]:
        transition_actor_character_id = (host_action.mechanic_effects or {}).get("transition_actor_character_id")
        outgoing_character_id = self.state.active_character_id
        incoming_character_id = (
            str(transition_actor_character_id)
            if transition_actor_character_id
            else str(host_action.character_id)
            if host_action.action_type == "swap" and host_action.character_id
            else None
        )
        host_actor_character_id = (
            str(transition_actor_character_id)
            if transition_actor_character_id
            else incoming_character_id
            if incoming_character_id
            else self.state.active_character_id
            if host_action.action_type == "wait"
            else host_action.character_id
        )
        host_actor_character_id = host_actor_character_id or self.state.active_character_id
        return advance_scheduled_effect_states(
            self.state,
            combat_start_time=combat_start_time,
            combat_elapsed=combat_elapsed,
            host_action_id=host_action.id,
            execute_tick=lambda effect, combat_time, offset, trigger_index: self.execute_scheduled_effect_event(
                effect=effect,
                host_action_id=host_action.id,
                host_actor_character_id=host_actor_character_id,
                host_action_type=host_action.action_type,
                outgoing_character_id=outgoing_character_id,
                incoming_character_id=incoming_character_id,
                host_combat_start_time=combat_start_time,
                host_combat_end_time=combat_start_time + combat_elapsed,
                combat_time=combat_time,
                host_action_combat_offset=offset,
                trigger_index=trigger_index,
                action_start_snapshot=action_start_snapshot,
                force_active_buff_ids=force_active_buff_ids,
            ),
        )

    def execute_scheduled_effect_event(
        self,
        *,
        effect,
        host_action_id: str,
        combat_time: float,
        host_action_combat_offset: float,
        trigger_index: int,
        host_actor_character_id: str | None = None,
        host_action_type: str | None = None,
        outgoing_character_id: str | None = None,
        incoming_character_id: str | None = None,
        host_combat_start_time: float | None = None,
        host_combat_end_time: float | None = None,
        action_start_snapshot: Any | None = None,
        force_active_buff_ids: set[str] | None = None,
    ) -> dict[str, Any]:
        if getattr(effect, "payload_event_type", "damage") == "healing":
            return self.execute_scheduled_healing_event(
                effect=effect,
                host_action_id=host_action_id,
                host_actor_character_id=host_actor_character_id,
                host_action_type=host_action_type,
                outgoing_character_id=outgoing_character_id,
                incoming_character_id=incoming_character_id,
                host_combat_start_time=host_combat_start_time,
                host_combat_end_time=host_combat_end_time,
                combat_time=combat_time,
                host_action_combat_offset=host_action_combat_offset,
                trigger_index=trigger_index,
            )
        if getattr(effect, "payload_event_type", "damage") == "status_application":
            return self.execute_scheduled_status_application_event(
                effect=effect,
                host_action_id=host_action_id,
                host_actor_character_id=host_actor_character_id,
                host_action_type=host_action_type,
                outgoing_character_id=outgoing_character_id,
                incoming_character_id=incoming_character_id,
                host_combat_start_time=host_combat_start_time,
                host_combat_end_time=host_combat_end_time,
                combat_time=combat_time,
                host_action_combat_offset=host_action_combat_offset,
                trigger_index=trigger_index,
            )
        return self.execute_scheduled_damage_event(
            effect=effect,
            host_action_id=host_action_id,
            combat_time=combat_time,
            host_action_combat_offset=host_action_combat_offset,
            trigger_index=trigger_index,
            action_start_snapshot=action_start_snapshot,
            force_active_buff_ids=force_active_buff_ids,
        )

    def execute_scheduled_damage_event(
        self,
        *,
        effect,
        host_action_id: str,
        combat_time: float,
        host_action_combat_offset: float,
        trigger_index: int,
        action_start_snapshot: Any | None = None,
        force_active_buff_ids: set[str] | None = None,
    ) -> dict[str, Any]:
        payload = self.actions.get(effect.payload_action_id)
        if payload is None:
            raise ValueError(f"Unknown scheduled-effect payload action {effect.payload_action_id!r}")
        event = execute_scheduled_damage_event(
            effect=effect,
            payload_action=payload,
            state=self.state,
            characters=self.characters,
            buffs=self.buffs,
            host_action_id=host_action_id,
            combat_time=combat_time,
            host_action_combat_offset=host_action_combat_offset,
            trigger_index=trigger_index,
            action_start_snapshot=action_start_snapshot,
            force_active_buff_ids=force_active_buff_ids,
            weapon_definitions=self.weapon_definitions,
        )
        self._apply_scheduled_off_tune_accumulation(payload, event, effect.source_character_id)
        self._apply_scheduled_resource_policy(payload, event, effect.source_character_id, effect.scheduled_resource_policy)
        metadata = dict(getattr(effect, "metadata", {}) or {})
        sigillum_fields = {
            key: metadata[key]
            for key in (
                "hit_index",
                "due_combat_time",
                "relative_due_frames",
                "relative_due_seconds",
                "base_resonance_energy_gain",
                "source_end_frame",
                "toughness",
                "source_ref",
            )
            if key in metadata
        }
        if sigillum_fields:
            event.update(sigillum_fields)
            if self.state.scheduled_effect_event_log:
                self.state.scheduled_effect_event_log[-1].update(event)
        return event

    def _schedule_aemeath_sigillum_hits(self, action: ActionData, result) -> None:
        if action.id != self.AEMEATH_SIGILLUM_ACTION_ID:
            return
        if result.truncated_by_combat_limit:
            return
        activation_time = float(result.combat_time_start)
        hit_specs = [
            {
                "hit_index": 1,
                "payload_action_id": self.AEMEATH_SIGILLUM_HIT_1_ACTION_ID,
                "due_frames": 25.0,
                "base_resonance_energy_gain": 0.23,
                "multiplier": 0.684,
                "toughness": 38,
            },
            {
                "hit_index": 2,
                "payload_action_id": self.AEMEATH_SIGILLUM_HIT_2_ACTION_ID,
                "due_frames": 55.0,
                "base_resonance_energy_gain": 2.13,
                "multiplier": 2.052,
                "toughness": 114,
            },
        ]
        schedule_events: list[dict[str, Any]] = []
        for spec in hit_specs:
            hit_index = int(spec["hit_index"])
            due_seconds = float(spec["due_frames"]) / 60.0
            due_combat_time = activation_time + due_seconds
            instance_order = int(self.state.scheduled_effect_next_order)
            instance_id = f"aemeath_echo_sigillum_hit_{hit_index}:aemeath:{instance_order}"
            metadata = {
                "active_echo_id": "sigillum",
                "hit_index": hit_index,
                "relative_due_frames": spec["due_frames"],
                "relative_due_seconds": due_seconds,
                "due_combat_time": due_combat_time,
                "activation_combat_time": activation_time,
                "source_end_frame": 80,
                "source_end_frame_metadata_only": True,
                "base_resonance_energy_gain": spec["base_resonance_energy_gain"],
                "damage_multiplier": spec["multiplier"],
                "toughness": spec["toughness"],
                "off_tune_value": 0.0,
                "off_tune_value_source_status": "unresolved_echo_off_tune",
                "source_ref": self.AEMEATH_SIGILLUM_HIT_SOURCE_REFS[hit_index],
                "scheduled_resource_policy": "source_confirmed_positive_gains",
                "survives_swap": True,
            }
            scheduled = self.schedule_effect(
                instance_id=instance_id,
                effect_id=f"aemeath_echo_sigillum_hit_{hit_index}",
                source_character_id="aemeath",
                source_action_id=action.id,
                payload_action_id=str(spec["payload_action_id"]),
                activation_combat_time=activation_time,
                remaining_duration=due_seconds,
                tick_interval=due_seconds,
                time_until_next_tick=due_seconds,
                max_trigger_count=1,
                refresh_rule="replace",
                scheduled_resource_policy="source_confirmed_positive_gains",
                source_status="workbook_confirmed_active_echo_scheduled_hit",
                source_ref=self.AEMEATH_SIGILLUM_HIT_SOURCE_REFS[hit_index],
                metadata=metadata,
            )
            schedule_events.append(
                {
                    "hit_index": hit_index,
                    "payload_action_id": spec["payload_action_id"],
                    "scheduled_effect_instance_id": instance_id,
                    "operation": scheduled.get("operation"),
                    "activation_combat_time": activation_time,
                    "due_combat_time": due_combat_time,
                    "relative_due_frames": spec["due_frames"],
                    "source_status": "workbook_confirmed_active_echo_scheduled_hit",
                    "source_ref": self.AEMEATH_SIGILLUM_HIT_SOURCE_REFS[hit_index],
                    "base_resonance_energy_gain": spec["base_resonance_energy_gain"],
                    "scheduled_resource_policy": "source_confirmed_positive_gains",
                }
            )
        result.aemeath_sigillum_activation_scheduled = True
        result.aemeath_sigillum_activation_combat_time = activation_time
        result.aemeath_sigillum_source_end_frame = 80
        result.aemeath_sigillum_hit_schedule_events = schedule_events

    def execute_scheduled_healing_event(
        self,
        *,
        effect,
        host_action_id: str,
        combat_time: float,
        host_action_combat_offset: float,
        trigger_index: int,
        host_actor_character_id: str | None = None,
        host_action_type: str | None = None,
        outgoing_character_id: str | None = None,
        incoming_character_id: str | None = None,
        host_combat_start_time: float | None = None,
        host_combat_end_time: float | None = None,
    ) -> dict[str, Any]:
        payload = self.actions.get(effect.payload_action_id)
        if payload is None:
            raise ValueError(f"Unknown scheduled-effect payload action {effect.payload_action_id!r}")
        if effect.source_character_id not in self.characters:
            raise ValueError(f"Scheduled healing source character {effect.source_character_id!r} is unavailable")
        metadata = dict(effect.metadata or {})
        healing = dict((payload.mechanic_effects or {}).get("healing_metadata") or {})
        source_character = self.characters[effect.source_character_id]
        stats = buffed_combat_stats(source_character, self.state, self.buffs)
        source_runtime_def = float(stats.get("effective_def", source_character.effective_def) or 0.0)
        base_heal = float(healing.get("base_heal", metadata.get("base_heal", 0.0)) or 0.0)
        scaling_multiplier = float(
            healing.get("scaling_multiplier", metadata.get("scaling_multiplier", 0.0)) or 0.0
        )
        field_multiplier = float(
            healing.get("field_healing_multiplier", metadata.get("field_healing_multiplier", 1.0)) or 1.0
        )
        healing_bonus_applied = float(metadata.get("healing_bonus_applied", 0.0) or 0.0)
        calculated = (base_heal + source_runtime_def * scaling_multiplier) * field_multiplier
        calculated *= 1.0 + healing_bonus_applied
        target_character_id = host_actor_character_id or self.state.active_character_id
        if not target_character_id or target_character_id not in self.characters:
            raise ValueError(
                "Scheduled healing could not resolve a valid target character "
                f"for host action {host_action_id!r}"
            )
        halo_log = apply_mornye_halo_of_starry_radiance_5set_event_buff(
            source_character_id=effect.source_character_id,
            emitted_event_tags=[TEAM_HEAL_EVENT_TAG],
            characters=self.characters,
            state=self.state,
            buffs=self.buffs,
            application_time=combat_time,
            event_source="scheduled_180f_exact",
        )
        weapon_log = self._apply_team_heal_weapon_effects(
            halo_log,
            source_character_id=effect.source_character_id,
            application_time=combat_time,
            event_source="scheduled_180f_exact",
        )
        halo_log.update(weapon_log)
        event = {
            "event_type": "scheduled_heal",
            "scheduled_effect_instance_id": effect.instance_id,
            "scheduled_effect_id": effect.effect_id,
            "source_character_id": effect.source_character_id,
            "source_action_id": effect.source_action_id,
            "payload_event_type": getattr(effect, "payload_event_type", "status_application"),
            "payload_action_id": payload.id,
            "payload_action_name": payload.name,
            "host_action_id": host_action_id,
            "host_action_type": host_action_type,
            "outgoing_character_id": outgoing_character_id,
            "incoming_character_id": incoming_character_id,
            "host_actor_character_id": target_character_id,
            "host_combat_start_time": host_combat_start_time,
            "host_combat_end_time": host_combat_end_time,
            "trigger_index": trigger_index,
            "combat_time": combat_time,
            "host_action_combat_offset": host_action_combat_offset,
            "damage": 0.0,
            "off_tune_value": 0.0,
            "off_tune_gain": 0.0,
            "resonance_energy_gain": 0.0,
            "concerto_energy_gain": 0.0,
            "target_character_id": target_character_id,
            "base_heal": base_heal,
            "source_runtime_def": source_runtime_def,
            "def_scaling_multiplier": scaling_multiplier,
            "field_healing_multiplier": field_multiplier,
            "healing_bonus_applied": healing_bonus_applied,
            "healing_bonus_source_status": metadata.get("healing_bonus_source_status", "metadata_only_not_applied"),
            "calculated_heal_amount": calculated,
            "hp_application_mode": "diagnostic_no_hp_state",
            "effective_hp_restored": None,
            "source_status": effect.source_status,
            "source_ref": effect.source_ref,
            "metadata": metadata,
            "team_heal_event_emitted": bool(halo_log.get("team_heal_event_triggered", False)),
            "applied_echo_set_effect_ids": list(halo_log.get("echo_set_triggered_buff_ids", [])),
            "applied_weapon_effect_ids": [
                str(log.get("weapon_effect_id"))
                for log in halo_log.get("weapon_effect_logs", [])
                if log.get("weapon_effect_id")
            ],
            **halo_log,
        }
        self.state.scheduled_effect_event_log.append(event)
        return event

    def execute_scheduled_status_application_event(
        self,
        *,
        effect,
        host_action_id: str,
        combat_time: float,
        host_action_combat_offset: float,
        trigger_index: int,
        host_actor_character_id: str | None = None,
        host_action_type: str | None = None,
        outgoing_character_id: str | None = None,
        incoming_character_id: str | None = None,
        host_combat_start_time: float | None = None,
        host_combat_end_time: float | None = None,
    ) -> dict[str, Any]:
        payload = self.actions.get(effect.payload_action_id)
        if payload is None:
            raise ValueError(f"Unknown scheduled-effect payload action {effect.payload_action_id!r}")
        mechanic = self._mechanic_for_character(effect.source_character_id)
        metadata = dict(effect.metadata or {})
        event_context = {
            "host_action_id": host_action_id,
            "host_action_type": host_action_type,
            "host_actor_character_id": host_actor_character_id,
            "outgoing_character_id": outgoing_character_id,
            "incoming_character_id": incoming_character_id,
            "host_combat_start_time": host_combat_start_time,
            "host_combat_end_time": host_combat_end_time,
            "combat_time": combat_time,
            "host_action_combat_offset": host_action_combat_offset,
            "trigger_index": trigger_index,
        }
        application_log = mechanic.apply_scheduled_status_effect(
            self.state,
            payload,
            metadata,
            event_context,
        )
        event = {
            "event_type": "scheduled_status_application",
            "scheduled_effect_instance_id": effect.instance_id,
            "scheduled_effect_id": effect.effect_id,
            "source_character_id": effect.source_character_id,
            "source_action_id": effect.source_action_id,
            "payload_event_type": getattr(effect, "payload_event_type", "status_application"),
            "payload_action_id": payload.id,
            "payload_action_name": payload.name,
            "host_action_id": host_action_id,
            "host_action_type": host_action_type,
            "host_actor_character_id": host_actor_character_id,
            "outgoing_character_id": outgoing_character_id,
            "incoming_character_id": incoming_character_id,
            "host_combat_start_time": host_combat_start_time,
            "host_combat_end_time": host_combat_end_time,
            "trigger_index": trigger_index,
            "combat_time": combat_time,
            "host_action_combat_offset": host_action_combat_offset,
            "damage": 0.0,
            "normal_damage": 0.0,
            "off_tune_value": 0.0,
            "off_tune_gain": 0.0,
            "resonance_energy_gain": 0.0,
            "concerto_energy_gain": 0.0,
            "reward_contribution": 0.0,
            "resource_cost_applied": False,
            "cooldown_applied": False,
            "combo_state_changed": False,
            "ordinary_player_action_side_effects_applied": False,
            "source_status": application_log.get("source_status", effect.source_status),
            "source_ref": application_log.get("source_ref", effect.source_ref),
            "metadata": metadata,
            **application_log,
        }
        self.state.scheduled_effect_event_log.append(event)
        return event

    def _apply_scheduled_resource_policy(
        self,
        action: ActionData,
        event: dict[str, Any],
        recipient_character_id: str,
        scheduled_resource_policy: str,
    ) -> None:
        event["scheduled_resource_policy"] = scheduled_resource_policy
        if scheduled_resource_policy == "none":
            event.update(
                {
                    "base_resonance_energy_gain": 0.0,
                    "energy_regen": 1.0,
                    "final_resonance_energy_gain": 0.0,
                    "resonance_energy_gained": 0.0,
                    "resonance_energy_wasted": 0.0,
                    "concerto_before": self.state.concerto_energy.get(recipient_character_id, 0.0),
                    "concerto_energy_gained": 0.0,
                    "concerto_after": self.state.concerto_energy.get(recipient_character_id, 0.0),
                    "concerto_energy_wasted": 0.0,
                }
            )
            if self.state.scheduled_effect_event_log:
                self.state.scheduled_effect_event_log[-1].update(event)
            return
        if scheduled_resource_policy != "source_confirmed_positive_gains":
            raise ValueError(f"Unsupported scheduled_resource_policy {scheduled_resource_policy!r}")

        change = apply_source_confirmed_scheduled_resource_gains(
            self.state,
            action,
            self.characters,
            recipient_character_id=recipient_character_id,
        )
        event.update(
            {
                "base_resonance_energy_gain": change.base_resonance_energy_gain,
                "energy_regen": change.energy_regen,
                "final_resonance_energy_gain": change.final_resonance_energy_gain,
                "resonance_energy_gained": change.resonance_gained,
                "resonance_energy_wasted": change.resonance_wasted,
                "concerto_before": change.concerto_before,
                "concerto_energy_gained": change.concerto_gained,
                "concerto_after": change.concerto_after,
                "concerto_energy_wasted": change.concerto_wasted,
                "concerto_ready_after": change.concerto_ready_after,
                "resource_recipient_character_id": recipient_character_id,
                "resource_cost_applied": False,
                "cooldown_applied": False,
                "combo_state_changed": False,
                "ordinary_player_action_side_effects_applied": False,
            }
        )
        if self.state.scheduled_effect_event_log:
            self.state.scheduled_effect_event_log[-1].update(event)

    def _apply_scheduled_off_tune_accumulation(
        self,
        action: ActionData,
        event: dict[str, Any],
        source_character_id: str,
    ) -> None:
        event["off_tune_value"] = float(action.off_tune_value or 0.0)
        event["off_tune_value_source_status"] = action.off_tune_value_source_status or "not_found_or_non_damaging"
        event["off_tune_value_source_ref"] = action.off_tune_value_source_ref
        event["off_tune_gain"] = 0.0
        if action.action_type == "tune_break" or float(event.get("normal_damage", 0.0) or 0.0) <= 0.0:
            return
        source_character = self.characters[source_character_id]
        rate = float(support_stat_context(source_character, self.state, self.buffs)["current_off_tune_buildup_rate"])
        before = self.state.enemy_off_tune_current
        if self.state.enemy_tune_break_cooldown_remaining > 0.0:
            added = 0.0
            after = before
            behavior = "blocked_by_tune_break_cooldown"
            self.state.off_tune_accumulation_blocked_by_tune_break_cooldown_count += 1
            blocked = True
            value_before_block = event["off_tune_value"]
            entered = False
        else:
            added = max(0.0, event["off_tune_value"]) * rate
            after = before + added
            behavior = "accumulated"
            blocked = False
            value_before_block = 0.0
            entered = False
            if after >= self.state.enemy_off_tune_max:
                self.state.off_tune_overflow += max(0.0, after - self.state.enemy_off_tune_max)
                after = self.state.enemy_off_tune_max
                if not self.state.enemy_mistune_active:
                    self.state.enemy_mistune_entered_count += 1
                    entered = True
                self.state.enemy_mistune_active = True
                self.state.enemy_tune_break_available = True
                behavior = "mistune_entered"
        self.state.enemy_off_tune_current = after
        self.state.off_tune_accumulated_total += added
        self.state.off_tune_buildup_rate_used = rate
        log = {
            "event_type": "scheduled_damage",
            "action_id": action.id,
            "scheduled_effect_instance_id": event.get("scheduled_effect_instance_id"),
            "scheduled_effect_id": event.get("scheduled_effect_id"),
            "host_action_id": event.get("host_action_id"),
            "source_character_id": source_character_id,
            "off_tune_value": event["off_tune_value"],
            "off_tune_value_source_status": event["off_tune_value_source_status"],
            "off_tune_value_source_ref": event["off_tune_value_source_ref"],
            "off_tune_buildup_rate_used": rate,
            "off_tune_added": added,
            "off_tune_accumulation_blocked_by_tune_break_cooldown": blocked,
            "off_tune_value_before_block": value_before_block,
            "enemy_tune_break_cooldown_remaining": self.state.enemy_tune_break_cooldown_remaining,
            "enemy_off_tune_current_before": before,
            "enemy_off_tune_current_after": after,
            "enemy_off_tune_max": self.state.enemy_off_tune_max,
            "enemy_mistune_active": self.state.enemy_mistune_active,
            "enemy_tune_break_available": self.state.enemy_tune_break_available,
            "enemy_mistune_entered_this_action": entered,
            "behavior": behavior,
        }
        self.state.off_tune_accumulation_logs.append(log)
        event["off_tune_gain"] = added
        event["off_tune_buildup_rate_used"] = rate
        event["enemy_off_tune_current_before"] = before
        event["enemy_off_tune_current_after"] = after
        event["off_tune_accumulation_log"] = log
        if self.state.scheduled_effect_event_log:
            self.state.scheduled_effect_event_log[-1].update(event)

    def _resolve_scheduled_action_packet(self, packet: ScheduledPacketInstance) -> dict[str, Any]:
        if packet.healing_payload:
            application_time = float(self.state.event_cursor_combat_time)
            halo_log = apply_mornye_halo_of_starry_radiance_5set_event_buff(
                source_character_id=packet.owner_character_id,
                emitted_event_tags=[TEAM_HEAL_EVENT_TAG],
                characters=self.characters,
                state=self.state,
                buffs=self.buffs,
                application_time=application_time,
                event_source="v124_distributed_array_frame_1_diagnostic_heal",
            )
            halo_log.update(
                self._apply_team_heal_weapon_effects(
                    halo_log,
                    source_character_id=packet.owner_character_id,
                    application_time=application_time,
                    event_source="v124_distributed_array_frame_1_diagnostic_heal",
                )
            )
            event = {
                "event_type": "scheduled_heal",
                "packet_instance_id": packet.packet_instance_id,
                "packet_creation_order": packet.packet_creation_order,
                "packet_occurrence_index": packet.packet_occurrence_index,
                "action_instance_id": packet.action_instance_id,
                "packet_group_id": packet.packet_group_id,
                "source_character_id": packet.owner_character_id,
                "source_action_id": packet.source_action_id,
                "scheduled_wall_time": packet.scheduled_wall_time,
                "scheduled_combat_time": packet.scheduled_combat_time,
                "processed_wall_time": self.state.event_cursor_wall_time,
                "processed_combat_time": application_time,
                "source_frame_row_ref": packet.source_refs[0] if packet.source_refs else None,
                "diagnostic_only": True,
                "healing_amount": 0.0,
                "numerical_healing_status": "source_amount_not_available_diagnostic_team_heal_event",
                **halo_log,
            }
            self.state.scheduled_effect_event_log.append(event)
            return event
        source_action = self.actions.get(packet.source_action_id)
        if source_action is None:
            raise ValueError(f"Unknown scheduled packet source action {packet.source_action_id!r}")
        packet_action, event = execute_scheduled_action_packet(
            packet=packet,
            source_action=source_action,
            state=self.state,
            characters=self.characters,
            buffs=self.buffs,
            weapon_definitions=self.weapon_definitions,
        )
        packet_action.off_tune_value_source_status = "workbook_confirmed_packet_payload"
        packet_action.off_tune_value_source_ref = packet.source_refs[0] if packet.source_refs else None
        self.state.scheduled_effect_event_log.append(event)
        self._apply_scheduled_off_tune_accumulation(packet_action, event, packet.owner_character_id)
        self._apply_scheduled_resource_policy(
            packet_action,
            event,
            packet.owner_character_id,
            "source_confirmed_positive_gains",
        )
        momentum_delta = float(packet.resource_payload.get("relative_momentum_gain", 0.0) or 0.0)
        if momentum_delta:
            owner_state = self.state.character_mechanics_state.setdefault(packet.owner_character_id, {})
            before = float(owner_state.get("relative_momentum", 0.0) or 0.0)
            cap = float(owner_state.get("relative_momentum_cap", 100.0) or 100.0)
            after = max(0.0, min(cap, before + momentum_delta))
            owner_state["relative_momentum"] = after
            event.update(
                {
                    "relative_momentum_before": before,
                    "relative_momentum_payload": momentum_delta,
                    "relative_momentum_gained": after - before,
                    "relative_momentum_after": after,
                }
            )
        marker_duration = float(packet.marker_payload.get("observation_marker_duration", 0.0) or 0.0)
        if marker_duration:
            owner_state = self.state.character_mechanics_state.setdefault(packet.owner_character_id, {})
            owner_state["observation_marker_remaining"] = marker_duration
            owner_state["observation_marker_remaining_application_combat_time"] = float(
                self.state.event_cursor_combat_time
            )
            owner_state["observation_marker_active"] = True
            event.update(
                {
                    "observation_marker_applied": True,
                    "observation_marker_duration": marker_duration,
                    "observation_marker_source": packet.marker_payload.get("observation_marker_source"),
                }
            )
            marker_event = apply_mornye_s1_interfered_marker(
                self,
                application_combat_time=float(self.state.event_cursor_combat_time),
            )
            if marker_event is not None:
                event["account_constellation_marker_event"] = marker_event
        if self.state.scheduled_effect_event_log:
            self.state.scheduled_effect_event_log[-1].update(event)
        return event

    @staticmethod
    def _add_scheduled_packet_to_damage_summary(summary: Any, event: dict[str, Any]) -> None:
        damage = float(event.get("damage_applied", 0.0) or 0.0)
        if isinstance(summary, dict):
            summary["scheduled_damage"] = float(summary.get("scheduled_damage", 0.0) or 0.0) + damage
            summary.setdefault("scheduled_damage_events", []).append(event)
            for key in ("damage_before_cutoff", "damage", "total_action_damage"):
                summary[key] = float(summary.get(key, 0.0) or 0.0) + damage
            return
        summary.scheduled_damage += damage
        summary.scheduled_damage_events.append(event)
        summary.damage_before_cutoff += damage
        summary.damage += damage
        summary.total_action_damage += damage

    def _attribute_scheduled_packet_to_source(self, event: dict[str, Any]) -> None:
        action_instance_id = str(event["action_instance_id"])
        ledger = self.state.scheduled_packet_source_ledger.setdefault(
            action_instance_id,
            {"scheduled_damage": 0.0, "events": [], "healing_events": [], "materialized": False},
        )
        if event.get("resource_event_only"):
            ledger.setdefault("resource_events", []).append(event)
            return
        if event.get("event_type") == "scheduled_heal":
            ledger.setdefault("healing_events", []).append(event)
            for entry in self.timeline:
                if entry.action_instance_id == action_instance_id:
                    entry.scheduled_healing_events.append(event)
                    break
            for action_log_entry in self.state.action_log:
                if action_log_entry.get("action_instance_id") == action_instance_id:
                    action_log_entry.setdefault("scheduled_healing_events", []).append(event)
                    break
            return
        ledger["scheduled_damage"] = float(ledger.get("scheduled_damage", 0.0) or 0.0) + float(
            event.get("damage_applied", 0.0) or 0.0
        )
        ledger.setdefault("events", []).append(event)

        for entry in self.timeline:
            if entry.action_instance_id == action_instance_id:
                self._add_scheduled_packet_to_damage_summary(entry, event)
                entry.total_damage_after = self.state.total_damage
                break
        for action_log_entry in self.state.action_log:
            if action_log_entry.get("action_instance_id") == action_instance_id:
                self._add_scheduled_packet_to_damage_summary(action_log_entry, event)
                action_log_entry["total_damage_after"] = self.state.total_damage
                break
        self._sync_outgoing_transition_source_summary(action_instance_id)

    def _build_outgoing_transition_source_summary(self, action_instance_id: str) -> dict[str, Any]:
        ledger = self.state.scheduled_packet_source_ledger.get(action_instance_id, {})
        instance = next(
            (item for item in self.state.ongoing_action_instances if item.action_instance_id == action_instance_id),
            None,
        )
        return {
            "auxiliary_transition_source_action": True,
            "policy_step": False,
            "action_time": 0.0,
            "combat_time_cost": 0.0,
            "action_instance_id": action_instance_id,
            "source_action_id": instance.source_action_id if instance is not None else None,
            "owner_character_id": instance.owner_character_id if instance is not None else None,
            "start_wall_time": instance.start_wall_time if instance is not None else None,
            "start_combat_time": instance.start_combat_time if instance is not None else None,
            "scheduled_damage": float(ledger.get("scheduled_damage", 0.0) or 0.0),
            "scheduled_damage_events": list(ledger.get("events", [])),
            "scheduled_packet_count": len(ledger.get("events", [])),
        }

    def _sync_outgoing_transition_source_summary(self, action_instance_id: str) -> None:
        summary = self._build_outgoing_transition_source_summary(action_instance_id)
        for entry in self.timeline:
            if entry.outgoing_scheduled_action_instance_id == action_instance_id:
                entry.outgoing_scheduled_source_summary = summary
        for action_log_entry in self.state.action_log:
            if action_log_entry.get("outgoing_scheduled_action_instance_id") == action_instance_id:
                action_log_entry["outgoing_scheduled_source_summary"] = summary

    def _start_outgoing_transition_scheduled_action(self, transition_resolution: Any) -> None:
        action_id = transition_resolution.outgoing_scheduled_action_id
        if not action_id or transition_resolution.outgoing_scheduled_action_started:
            return
        action = self.actions.get(action_id)
        contract = self.action_timing_contracts.get(action_id)
        if action is None or contract is None:
            raise ValueError(f"Outgoing transition source {action_id!r} requires an action and timing contract")
        selected_timing = select_action_timing(self.state, action, contract)
        instance = start_ongoing_action(self.state, action, contract, selected_timing)
        transition_resolution.outgoing_scheduled_action_started = True
        transition_resolution.outgoing_scheduled_action_instance_id = instance.action_instance_id
        self.state.scheduled_packet_source_ledger.setdefault(
            instance.action_instance_id,
            {"scheduled_damage": 0.0, "events": [], "healing_events": [], "materialized": True},
        )
        transition_resolution.outgoing_scheduled_source_summary = (
            self._build_outgoing_transition_source_summary(instance.action_instance_id)
        )

    def _apply_source_packet_ledger_to_result(self, result: Any) -> None:
        if not result.action_instance_id:
            result.total_damage_after = self.state.total_damage
            return
        ledger = self.state.scheduled_packet_source_ledger.get(result.action_instance_id)
        if not ledger or ledger.get("materialized"):
            result.total_damage_after = self.state.total_damage
            return
        for event in ledger.get("events", []):
            self._add_scheduled_packet_to_damage_summary(result, event)
        result.scheduled_healing_events.extend(ledger.get("healing_events", []))
        ledger["materialized"] = True
        result.total_damage_after = self.state.total_damage

    def _advance_scheduled_packets_to(self, *, event_wall_time: float, event_combat_time: float) -> list[dict[str, Any]]:
        events = advance_ongoing_action_runtime(
            self.state,
            self._resolve_scheduled_action_packet,
            through_wall_time=event_wall_time,
            through_combat_time=event_combat_time,
        )
        for event in events:
            self._attribute_scheduled_packet_to_source(event)
        return events

    def _record_chronological_action_event(
        self,
        *,
        event_wall_time: float,
        event_combat_time: float,
        event_type: str,
        owner_character_id: str,
        source_action_id: str,
        action_instance_id: str,
        **extra: Any,
    ) -> dict[str, Any]:
        self.state.event_cursor_wall_time = max(self.state.event_cursor_wall_time, float(event_wall_time))
        self.state.event_cursor_combat_time = max(self.state.event_cursor_combat_time, float(event_combat_time))
        self.state.chronological_event_next_sequence += 1
        event = {
            "event_sequence": self.state.chronological_event_next_sequence,
            "event_wall_time": float(event_wall_time),
            "event_combat_time": float(event_combat_time),
            "event_type": event_type,
            "owner_character_id": owner_character_id,
            "source_action_id": source_action_id,
            "action_instance_id": action_instance_id,
            "enemy_off_tune_current": self.state.enemy_off_tune_current,
            "enemy_mistune_active": self.state.enemy_mistune_active,
            "enemy_tune_break_available": self.state.enemy_tune_break_available,
            **extra,
        }
        self.state.chronological_event_log.append(event)
        return event

    def execute_action(self, action_id: str, *, record_diagnostics: bool = True) -> bool:
        self.validate_simulation_readiness(entry_point=f"combat action {action_id}")
        self._advance_scheduled_packets_to(
            event_wall_time=self.state.current_time,
            event_combat_time=self.state.combat_time,
        )
        if self.state.combat_time >= self.combat_duration:
            return False
        if (
            self.state.mechanics_config.get("aemeath", {}).get("aemeath_resonance_mode") == "fusion_burst"
            and "aemeath" in self.character_mechanics
        ):
            self.character_mechanics["aemeath"]._ensure_fusion_minimum_effect(self.state)

        selected_action = self.actions[action_id]
        if selected_action.policy_selectable and action_id not in self.policy_actions:
            return False
        transition_resolution = None
        if is_swap_action(selected_action):
            # Check the policy-visible target re-entry cooldown before transition
            # resolution can consume Concerto or otherwise mutate state.
            if not self.is_resolved_action_available(selected_action):
                return False
            transition_resolution = resolve_party_transition(
                selected_action,
                self.state,
                self.actions,
                self.transition_config,
                self.preset_generic_swap,
            )
            action = build_transition_swap_action(
                selected_action,
                self.transition_config,
                self.preset_generic_swap,
            )
            if transition_resolution.transition_action is not None:
                action = transition_resolution.transition_action
            action.action_time = transition_resolution.action_time
            action.duration = transition_resolution.action_time
            action.combat_time_cost = max(transition_resolution.combat_time_cost, 0.0)
        else:
            action = self.resolve_action(selected_action)
        if not self.is_resolved_action_available(action):
            return False

        if transition_resolution is not None:
            # The Lynae Outro is an auxiliary outgoing source.  Starting it here
            # schedules packets at the shared transition timestamp without creating
            # a policy action or delaying the incoming transition host action.
            self._start_outgoing_transition_scheduled_action(transition_resolution)

        timing_contract = self.action_timing_contracts.get(action.id)
        action_instance_id: str
        if timing_contract is not None:
            release_prior_owner_input_locks_for_followup(
                self.state,
                str(action.character_id or self.state.active_character_id),
            )
            selected_timing = select_action_timing(self.state, action, timing_contract)
            ongoing_action = start_ongoing_action(self.state, action, timing_contract, selected_timing)
            action_instance_id = ongoing_action.action_instance_id
            action = prepare_control_point_action(action, timing_contract, selected_timing)
        else:
            self.state.action_instance_next_order += 1
            action_instance_id = f"action-instance-v124-{self.state.action_instance_next_order}:{action.id}"
        action = action.model_copy(deep=True)
        action.mechanic_effects = {
            **(action.mechanic_effects or {}),
            "v124_action_instance_id": action_instance_id,
        }

        if transition_resolution is not None:
            outgoing_key = swap_reentry_key(transition_resolution.outgoing_character_id)
            transition_resolution.outgoing_swap_reentry_key = outgoing_key
            transition_resolution.outgoing_swap_reentry_before = float(
                self.state.cooldowns.get(outgoing_key, 0.0) or 0.0
            )
            transition_resolution.outgoing_swap_reentry_after_set = SWAP_REENTRY_COOLDOWN_SECONDS
            self.state.cooldowns[outgoing_key] = SWAP_REENTRY_COOLDOWN_SECONDS

        self._apply_pre_transition_events(transition_resolution)
        zero_time_transition = bool((action.mechanic_effects or {}).get("zero_time_transition_action", False))
        pre_action_echo_set_log_fields = (
            {} if zero_time_transition else self._apply_mornye_syntony_field_uptime_heal_proxy(action)
        )
        pre_action_echo_set_log_fields = merge_echo_set_logs(
            pre_action_echo_set_log_fields,
            self._apply_mornye_same_action_high_syntony_field(action),
        )
        pre_action_echo_set_log_fields = merge_echo_set_logs(
            pre_action_echo_set_log_fields,
            self._apply_mornye_same_action_field_creation_halo(action),
        )
        pre_action_echo_set_log_fields = merge_echo_set_logs(
            pre_action_echo_set_log_fields,
            self._schedule_mornye_syntony_field_deployment_damage(action),
        )
        transition_actor_character_id = (action.mechanic_effects or {}).get("transition_actor_character_id")
        actor_character_id = (
            str(transition_actor_character_id)
            if transition_actor_character_id
            else self.state.active_character_id
            if action.action_type in {"swap", "wait"}
            else action.character_id
        )
        actor_character_id = actor_character_id or self.state.active_character_id
        actor_mechanic = self._mechanic_for_character(actor_character_id)
        before_account_action(self, selected_action, action)
        event_owner_character_id = str(action.character_id or actor_character_id)
        self._record_chronological_action_event(
            event_wall_time=self.state.current_time,
            event_combat_time=self.state.combat_time,
            event_type="action_start",
            owner_character_id=event_owner_character_id,
            source_action_id=action.id,
            action_instance_id=action_instance_id,
        )
        scheduled_effect_runner = None if zero_time_transition else lambda **kwargs: self.advance_scheduled_effects(
            host_action=action,
            **kwargs,
        )
        chronological_event_runner = lambda **kwargs: self._advance_scheduled_packets_to(**kwargs)
        record_hit_event = lambda **kwargs: self._record_chronological_action_event(
            event_type="action_hit",
            owner_character_id=event_owner_character_id,
            source_action_id=action.id,
            action_instance_id=action_instance_id,
            hit_name=kwargs.pop("hit").name,
            **kwargs,
        )
        result = execute_action(
            action,
            self.state,
            self.characters,
            self.buffs,
            mechanic=actor_mechanic,
            combat_duration=self.combat_duration,
            pre_action_echo_set_log_fields=pre_action_echo_set_log_fields,
            weapon_definitions=self.weapon_definitions,
            scheduled_effect_runner=scheduled_effect_runner,
            chronological_event_runner=chronological_event_runner,
            record_hit_event=record_hit_event,
            record_diagnostics=record_diagnostics,
        )
        self._apply_source_packet_ledger_to_result(result)
        if any(event.get("observation_marker_applied") for event in result.scheduled_damage_events):
            result.observation_marker_applied = True
            result.observation_marker_active = True
            result.observation_marker_remaining = self._mornye_observation_marker_remaining()
        self.last_action_result = result
        if not result.valid:
            return False
        self._record_chronological_action_event(
            event_wall_time=result.end_time,
            event_combat_time=result.combat_time_end,
            event_type="action_end",
            owner_character_id=event_owner_character_id,
            source_action_id=action.id,
            action_instance_id=action_instance_id,
        )
        result.selected_action_id = selected_action.id
        result.selected_action_name = selected_action.name
        result.resolved_action_id = action.id
        result.resolved_action_name = action.name
        if transition_resolution is not None:
            transition_resolution.outgoing_swap_reentry_after_action = float(
                self.state.cooldowns.get(transition_resolution.outgoing_swap_reentry_key or "", 0.0) or 0.0
            )
            self._apply_transition_resolution(result, transition_resolution)
            self._apply_lynae_transition_buffs(result, transition_resolution)
            self._apply_lynae_incoming_intro_mechanics(result, transition_resolution)
            on_account_transition(self, transition_resolution, result)
            handle_character_swap(self.state, transition_resolution.outgoing_character_id)
        self._apply_aemeath_outro_upgrade(result, actor_character_id)

        weapon_action_log = {}
        if not result.truncated_by_combat_limit:
            mechanic_weapon_log = apply_weapon_mechanic_event_effects(
                emitted_event_tags=list(result.emitted_mechanic_event_tags),
                source_character_id=actor_character_id,
                state=self.state,
                characters=self.characters,
                buffs=self.buffs,
                weapon_definitions=self.weapon_definitions,
                application_time=result.combat_time_end,
                event_source=f"mechanic_event:{action.id}",
            )
            self._sync_weapon_result_fields(result, mechanic_weapon_log)
            weapon_action_log = process_weapon_effects_before_or_after_action(
                action=action,
                state=self.state,
                characters=self.characters,
                buffs=self.buffs,
                weapon_definitions=self.weapon_definitions,
                application_time=result.combat_time_end,
            )
            self._sync_weapon_result_fields(result, weapon_action_log)
        if not bool(weapon_action_log.get("weapon_effect_triggered", False)):
            advance_weapon_effect_cooldowns(self.state, result.action_time)

        self._advance_tune_break_runtime(
            action_elapsed=result.action_time,
            combat_elapsed=result.effective_combat_time_cost,
        )
        self._apply_off_tune_accumulation(action, result)
        if action.action_type == "tune_break":
            self._apply_tune_break_after_effects(action, result)
        self._sync_tune_break_result_fields(result)
        if result.interfered_marker_direct_damage_amp_applied_count > 0:
            self.state.interfered_marker_direct_damage_amp_applied_action_count += 1
            self.state.interfered_marker_direct_damage_amp_bonus_damage_total += (
                result.interfered_marker_direct_damage_amp_bonus_damage
            )

        for mechanic in self.character_mechanics.values():
            mechanic.advance_time(
                self.state,
                result.effective_combat_time_cost,
                action_elapsed=result.action_time,
            )
        advance_account_constellation_time(self, result.effective_combat_time_cost)
        skip_after_action = bool((action.mechanic_effects or {}).get("skip_character_after_action"))
        auxiliary_zero_time_action = bool((action.mechanic_effects or {}).get("auxiliary_zero_time_action"))
        if (
            not result.truncated_by_combat_limit
            and not skip_after_action
            and not auxiliary_zero_time_action
            and not zero_time_transition
        ):
            actor_mechanic.after_action(self.state, action, result)
            self._schedule_lynae_spray_paint_status_field(action, result)
        if not result.truncated_by_combat_limit:
            self._apply_mornye_post_action_support_events(action, result)
            self._schedule_aemeath_sigillum_hits(action, result)
            after_account_action(self, action, result)
        if transition_resolution is not None:
            self._apply_aemeath_incoming_intro_mechanics(result, transition_resolution)
        self._sync_weapon_result_fields(result)
        self._sync_lynae_spray_paint_window_mirror(result)
        if record_diagnostics:
            result.mechanic_debug_after = {
                character_id: mechanic.get_debug_state(self.state)
                for character_id, mechanic in self.character_mechanics.items()
                if mechanic.get_debug_state(self.state)
            }
            self._apply_post_mechanic_transition_debug(result)
        if record_diagnostics and self.state.action_log:
            self.state.action_log[-1] = result.model_dump(mode="json")

        if record_diagnostics:
            active_name = self.characters[self.state.active_character_id].name
            self.timeline.append(timeline_entry(result, active_name))
        return True

    def run_sequence(self, action_ids: list[str]) -> "Simulation":
        self.validate_simulation_readiness(entry_point="diagnostic route replay")
        for action_id in action_ids:
            if self.state.combat_time >= self.combat_duration:
                break
            self.execute_action(action_id)
        return self

    def advance_timing_runtime(self, wall_elapsed: float, *, combat_elapsed: float | None = None) -> None:
        """Advance the two clocks without inserting a policy action.

        This is the deterministic Stage-1 timing-core hook used for action tails,
        packet deadlines, and exact frame-boundary proofs. It is not a policy wait.
        """
        wall_elapsed = max(0.0, float(wall_elapsed))
        resolved_combat_elapsed = wall_elapsed if combat_elapsed is None else max(0.0, float(combat_elapsed))
        target_wall_time = self.state.current_time + wall_elapsed
        target_combat_time = self.state.combat_time + resolved_combat_elapsed
        self._advance_scheduled_packets_to(
            event_wall_time=target_wall_time,
            event_combat_time=target_combat_time,
        )
        self.state.current_time = target_wall_time
        self.state.combat_time = target_combat_time
        self.state.event_cursor_wall_time = max(self.state.event_cursor_wall_time, target_wall_time)
        self.state.event_cursor_combat_time = max(self.state.event_cursor_combat_time, target_combat_time)
        reduce_cooldowns(
            self.state,
            resolved_combat_elapsed,
            action_elapsed=wall_elapsed,
        )

    def valid_action_ids(self) -> list[str]:
        if self.account_profile_gate_errors or not self._account_aemeath_mode_is_executable():
            return []
        return [
            action_id
            for action_id, action in self.policy_actions.items()
            if action.policy_selectable and self.is_action_available(action)
        ]

    def is_action_available(self, action: ActionData) -> bool:
        if self.account_profile_gate_errors or not self._account_aemeath_mode_is_executable():
            return False
        if self.state.combat_time >= self.combat_duration:
            return False
        if action.policy_selectable and not is_swap_action(action):
            action = self.resolve_action(action)
        return self.is_resolved_action_available(action)

    def _account_aemeath_mode_is_executable(self) -> bool:
        aemeath = self.characters.get("aemeath")
        if aemeath is None or not bool(getattr(aemeath, "account_profile", False)):
            return True
        if int(getattr(aemeath, "sequence", 0) or 0) < 6:
            return True
        return aemeath_resonance_mode_from_config(self.state.mechanics_config) in {"tune_rupture", "fusion_burst"}

    def is_resolved_action_available(self, action: ActionData) -> bool:
        valid, _reason = is_action_valid(action, self.state)
        if not valid:
            return False
        if action.action_type == "tune_break":
            if not self.state.enemy_tune_break_available:
                return False
            if self.state.enemy_tune_break_cooldown_remaining > 0.0:
                return False
        if action.action_type in {"swap", "wait"} or action.character_id is None:
            return True
        return self._mechanic_for_character(action.character_id).is_action_available(self.state, action)

    def _tune_break_system_config(self) -> dict[str, Any]:
        return dict((self.state.mechanics_config.get("tune_break_system") if hasattr(self, "state") else None) or {})

    @staticmethod
    def _default_tune_response_defs() -> dict[str, dict[str, Any]]:
        return {
            "aemeath_starburst": {
                "id": "aemeath_starburst",
                "name": "Aemeath Starburst",
                "source_character_id": "aemeath",
                "trigger_interfered_state": "tune_rupture_interfered",
                "element": "fusion",
                "raw_damage_type": "tune_break_response",
                "multiplier": 5.9643,
                "cooldown_seconds": 8.0,
                "base_value": 10000.0,
                "source_status": "workbook_confirmed",
            },
            "mornye_particle_jet": {
                "id": "mornye_particle_jet",
                "name": "Mornye Particle Jet",
                "source_character_id": "mornye",
                "trigger_interfered_state": "tune_rupture_interfered",
                "element": "fusion",
                "raw_damage_type": "tune_break_response",
                "multiplier": 2.9822,
                "c5_multiplier": 7.7536,
                "c5_enabled_constellation": 5,
                "cooldown_seconds": 8.0,
                "base_value": 10000.0,
                "source_status": "workbook_confirmed",
            },
            "lynae_spectral_analysis": {
                "id": "lynae_spectral_analysis",
                "name": "Lynae Spectral Analysis",
                "source_character_id": "lynae",
                "trigger_interfered_state": "tune_rupture_interfered",
                "supported_interfered_states": ["tune_rupture_interfered", "tune_strain_interfered"],
                "element": "spectro",
                "raw_damage_type": "tune_break_response",
                "multiplier": 18.8075,
                "c2_multiplier": 31.9727,
                "c2_enabled_constellation": 2,
                "c2_enabled_by_default": False,
                "cooldown_seconds": 8.0,
                "base_value": 10000.0,
                "source_status": "workbook_confirmed",
            },
        }

    def _current_off_tune_buildup_rate(self) -> float:
        mornye = self.characters.get("mornye")
        if mornye is None:
            return 1.0
        return float(support_stat_context(mornye, self.state, self.buffs)["current_off_tune_buildup_rate"])

    def _refresh_off_tune_mapping_metadata(self) -> None:
        mapped_status_prefixes = ("workbook_confirmed", "excel_cell", "excel_summed")
        unresolved_status_prefixes = ("unresolved_",)
        mapped_count = 0
        unmapped: list[str] = []
        unresolved: list[str] = []
        selected = set(self.selected_character_ids)
        covered_characters = {"aemeath", "mornye", "lynae"} & selected
        if "lynae" in covered_characters:
            self.state.off_tune_value_mapping_source_report = (
                "reports/off_tune_value_mapping_audit.md; reports/lynae_off_tune_direct_mapping_audit.md"
            )
        for action in self.actions.values():
            if action.character_id not in covered_characters:
                continue
            if action.character_id is not None and action.character_id not in selected:
                continue
            has_normal_damage = any(hit.damage_category == "normal" and hit.damage_multiplier > 0.0 for hit in action.effective_hits())
            if not has_normal_damage:
                continue
            if action.action_type == "tune_break":
                continue
            source_status = str(action.off_tune_value_source_status or "")
            has_value_metadata = action.off_tune_value is not None
            if source_status == "non_damaging_selector":
                continue
            if has_value_metadata and source_status.startswith(mapped_status_prefixes):
                mapped_count += 1
            elif source_status.startswith(unresolved_status_prefixes):
                unresolved.append(action.id)
            elif not has_value_metadata or not source_status:
                unmapped.append(action.id)
            elif action.off_tune_value <= 0.0 and source_status not in {"not_found_or_non_damaging", "non_damaging_selector"}:
                unmapped.append(action.id)
        self.state.mapped_off_tune_action_count = mapped_count
        self.state.unmapped_off_tune_action_ids = sorted(set(unmapped))
        self.state.unresolved_off_tune_damaging_action_ids = sorted(set(unresolved))
        self.state.off_tune_mapping_completeness_status = (
            "complete" if not self.state.unmapped_off_tune_action_ids and not self.state.unresolved_off_tune_damaging_action_ids else "incomplete"
        )

    def _advance_tune_break_runtime(self, *, action_elapsed: float, combat_elapsed: float) -> None:
        action_elapsed = max(0.0, float(action_elapsed or 0.0))
        combat_elapsed = max(0.0, float(combat_elapsed or 0.0))
        self.state.enemy_tune_break_cooldown_remaining = max(
            0.0,
            self.state.enemy_tune_break_cooldown_remaining - action_elapsed,
        )
        self.state.target_tune_shift_remaining = max(0.0, self.state.target_tune_shift_remaining - combat_elapsed)
        if self.state.target_tune_shift_remaining <= 0.0:
            self.state.target_tune_shift_state = None
        self.state.target_interfered_remaining = max(0.0, self.state.target_interfered_remaining - combat_elapsed)
        if self.state.target_interfered_remaining <= 0.0:
            self.state.target_interfered_state = None
        self.state.rupturous_trail_remaining = max(0.0, self.state.rupturous_trail_remaining - combat_elapsed)
        if self.state.rupturous_trail_remaining <= 0.0:
            self.state.rupturous_trail_stacks = 0
        self.state.target_tune_strain_interfered_remaining = max(
            0.0,
            self.state.target_tune_strain_interfered_remaining - combat_elapsed,
        )
        if self.state.target_interfered_state != "tune_strain_interfered":
            clear_lynae_tune_strain_state(self.state)
            self.state.target_tune_strain_interfered_max_stacks = lynae_tune_strain_max_stacks(
                self.state.mechanics_config
            )
        elif self.state.target_tune_strain_interfered_remaining <= 0.0:
            self.state.target_interfered_state = None
            clear_lynae_tune_strain_state(self.state)
            self.state.target_tune_strain_interfered_max_stacks = lynae_tune_strain_max_stacks(
                self.state.mechanics_config
            )
        marker_tick_start = max(0.0, self.state.combat_time - combat_elapsed)
        marker_elapsed = combat_elapsed
        if self.state.interfered_marker_application_combat_time is not None:
            marker_elapsed = max(
                0.0,
                self.state.combat_time - max(marker_tick_start, self.state.interfered_marker_application_combat_time),
            )
        self.state.interfered_marker_remaining = max(0.0, self.state.interfered_marker_remaining - marker_elapsed)
        if self.state.interfered_marker_remaining <= 0.0:
            self.state.interfered_marker_damage_taken_amp = 0.0
        self.state.aemeath_starburst_response_cooldown_remaining = max(
            0.0,
            self.state.aemeath_starburst_response_cooldown_remaining - action_elapsed,
        )
        self.state.mornye_particle_jet_response_cooldown_remaining = max(
            0.0,
            self.state.mornye_particle_jet_response_cooldown_remaining - action_elapsed,
        )
        self.state.lynae_spectral_analysis_response_cooldown_remaining = max(
            0.0,
            self.state.lynae_spectral_analysis_response_cooldown_remaining - action_elapsed,
        )

    def _apply_off_tune_accumulation(self, action: ActionData, result: Any) -> None:
        result.enemy_off_tune_current_before = self.state.enemy_off_tune_current
        result.enemy_off_tune_max = self.state.enemy_off_tune_max
        result.off_tune_value = float(action.off_tune_value or 0.0)
        result.off_tune_value_source_status = action.off_tune_value_source_status or "not_found_or_non_damaging"
        result.off_tune_value_source_ref = action.off_tune_value_source_ref
        if action.action_type == "tune_break" or result.normal_damage <= 0.0:
            return
        rate = self._current_off_tune_buildup_rate()
        before = self.state.enemy_off_tune_current
        if self.state.enemy_tune_break_cooldown_remaining > 0.0:
            added = 0.0
            after = before
            entered = False
            behavior = "blocked_by_tune_break_cooldown"
            self.state.off_tune_accumulation_blocked_by_tune_break_cooldown_count += 1
            result.off_tune_accumulation_blocked_by_tune_break_cooldown = True
            result.off_tune_value_before_block = result.off_tune_value
        else:
            added = max(0.0, result.off_tune_value) * rate
            after = before + added
            entered = False
            behavior = "accumulated"
            if after >= self.state.enemy_off_tune_max:
                self.state.off_tune_overflow += max(0.0, after - self.state.enemy_off_tune_max)
                after = self.state.enemy_off_tune_max
                if not self.state.enemy_mistune_active:
                    self.state.enemy_mistune_entered_count += 1
                    entered = True
                self.state.enemy_mistune_active = True
                self.state.enemy_tune_break_available = True
                behavior = "mistune_entered"
        self.state.enemy_off_tune_current = after
        self.state.off_tune_accumulated_total += added
        self.state.off_tune_buildup_rate_used = rate
        log = {
            "action_id": action.id,
            "off_tune_value": result.off_tune_value,
            "off_tune_value_source_status": action.off_tune_value_source_status or "not_found_or_non_damaging",
            "off_tune_value_source_ref": action.off_tune_value_source_ref,
            "off_tune_buildup_rate_used": rate,
            "off_tune_added": added,
            "off_tune_accumulation_blocked_by_tune_break_cooldown": (
                result.off_tune_accumulation_blocked_by_tune_break_cooldown
            ),
            "off_tune_value_before_block": result.off_tune_value_before_block,
            "enemy_tune_break_cooldown_remaining": self.state.enemy_tune_break_cooldown_remaining,
            "enemy_off_tune_current_before": before,
            "enemy_off_tune_current_after": after,
            "enemy_off_tune_max": self.state.enemy_off_tune_max,
            "enemy_mistune_active": self.state.enemy_mistune_active,
            "enemy_tune_break_available": self.state.enemy_tune_break_available,
            "enemy_mistune_entered_this_action": entered,
            "behavior": behavior,
        }
        self.state.off_tune_accumulation_logs.append(log)
        result.off_tune_buildup_rate_used = rate
        result.off_tune_added = added
        result.enemy_off_tune_current_before = before
        result.enemy_off_tune_current_after = after
        result.enemy_mistune_entered_this_action = entered
        result.off_tune_accumulation_log = log

    def _apply_tune_break_after_effects(self, action: ActionData, result: Any) -> None:
        if result.tune_break_damage <= 0.0:
            return
        self.state.tune_break_action_used_count += 1
        self.state.tune_break_damage_total += result.tune_break_damage
        prior_shift_state = self.state.target_tune_shift_state
        interfered_state = None
        if prior_shift_state == "tune_rupture_shifting":
            interfered_state = "tune_rupture_interfered"
            self.state.target_interfered_state = interfered_state
            self.state.target_interfered_remaining = 8.0
            clear_lynae_tune_strain_state(self.state)
            self.state.target_tune_strain_interfered_max_stacks = lynae_tune_strain_max_stacks(
                self.state.mechanics_config
            )
        elif prior_shift_state == "tune_strain_shifting":
            interfered_state = "tune_strain_interfered"
            self.state.target_interfered_state = interfered_state
            self.state.target_interfered_remaining = 30.0
            max_stacks = lynae_tune_strain_max_stacks(self.state.mechanics_config)
            self.state.target_tune_strain_interfered_max_stacks = max_stacks
            self.state.target_tune_strain_interfered_stacks = min(
                max_stacks,
                int(self.state.target_tune_strain_interfered_stacks or 0) + 1,
            )
            self.state.target_tune_strain_interfered_remaining = 30.0
            refresh_lynae_tune_strain_amp(self.state, self.characters, self.buffs)
        else:
            result.interfered_unavailable_reason = "missing_target_shift_state"

        self.state.enemy_mistune_active = False
        self.state.enemy_tune_break_available = False
        self.state.enemy_off_tune_current = 0.0
        self.state.target_tune_shift_state = None
        self.state.target_tune_shift_remaining = 0.0
        cooldown = float(self.state.enemy_tune_break_cooldown_seconds or 3.0)
        self.state.enemy_tune_break_cooldown_remaining = cooldown
        result.enemy_off_tune_current_after_tune_break = self.state.enemy_off_tune_current
        result.enemy_tune_break_cooldown_started = True
        result.enemy_tune_break_cooldown_seconds = cooldown
        result.enemy_tune_break_cooldown_source_status = self.state.enemy_tune_break_cooldown_source_status
        result.enemy_tune_break_cooldown_source_ref = self.state.enemy_tune_break_cooldown_source_ref
        self._sync_lynae_tune_strain_result_fields(result)

        if interfered_state is not None:
            result.previous_interfered_marker_active_before_response = (
                self.state.interfered_marker_remaining > 0.0
                and self.state.interfered_marker_damage_taken_amp > 0.0
            )
            self._apply_observation_marker_interfered_marker(result, interfered_state)
            self._scan_party_responses(result, interfered_state)

    def _mornye_observation_marker_remaining(self) -> float:
        return float(
            self.state.character_mechanics_state.get("mornye", {}).get("observation_marker_remaining", 0.0)
            or 0.0
        )

    def _apply_observation_marker_interfered_marker(self, result: Any, interfered_state: str) -> None:
        remaining = self._mornye_observation_marker_remaining()
        result.observation_marker_active = remaining > 0.0
        result.observation_marker_remaining = remaining
        if remaining <= 0.0 or "mornye" not in self.characters:
            return
        mornye = self.characters["mornye"]
        energy_regen = float(self.state.character_states.get("mornye", {}).get("energy_regen", mornye.energy_regen))
        excess = max(energy_regen - 1.0, 0.0)
        uncapped_amp = excess * 0.25
        amp = min(uncapped_amp, 0.40)
        duration = 8.0 if interfered_state == "tune_rupture_interfered" else 20.0
        buff = BuffData(
            id="mornye_interfered_marker_damage_amp",
            name="Mornye Interfered Marker Damage Taken Amp",
            duration=duration,
            modifier_type="damage_amp",
            value=amp,
            target="enemy",
            target_scope="enemy",
            metadata={
                "source_character_id": "mornye",
                "source": "observation_marker_tune_break",
                "dynamic_value": amp,
                "source_ref": "角色-女!D4164",
                "implementation_status": "excel_tune_break_triggered_single_target",
            },
        )
        self.buffs[buff.id] = buff
        apply_buff(self.state, buff, "mornye")
        self.state.interfered_marker_remaining = duration
        self.state.interfered_marker_applied_count += 1
        self.state.interfered_marker_damage_taken_amp = amp
        result.mornye_interfered_marker_applied = True
        result.interfered_marker_active = True
        result.interfered_marker_remaining = duration
        result.interfered_marker_applied_count = self.state.interfered_marker_applied_count
        result.interfered_marker_damage_taken_amp = amp
        result.interfered_marker_damage_taken_multiplier = 1.0 + amp
        result.mornye_energy_regen_for_interfered_marker = energy_regen
        result.energy_regen_excess_for_interfered_marker = excess
        result.interfered_marker_cap_applied = uncapped_amp > amp
        result.interfered_marker_source = "observation_marker_tune_break"
        result.interfered_marker_newly_applied_this_action = True
        result.mornye_interfered_marker_mode = "tune_break_triggered"
        result.interfered_marker_mode = "tune_break_triggered"
        result.mornye_interfered_amp = amp
        if buff.id not in result.applied_buffs:
            result.applied_buffs.append(buff.id)

    def _scan_party_responses(self, result: Any, interfered_state: str) -> None:
        if interfered_state not in {"tune_rupture_interfered", "tune_strain_interfered"}:
            return
        log = {
            "target_interfered_state": interfered_state,
            "response_source_status": "workbook_confirmed",
            "tune_response_damage_formula_source_status": "workbook_confirmed",
            "tune_response_event_order_source_status": "excel_event_order_derived",
            "tune_break_damage_receives_new_interfered_marker_amp": False,
            "response_damage_receives_interfered_marker_amp": False,
            "response_damage_receives_newly_applied_interfered_marker_amp": False,
            "response_damage_receives_existing_interfered_marker_amp": False,
            "response_damage_receives_new_interfered_marker_amp": False,
            "aemeath_starburst_triggered": False,
            "aemeath_starburst_cooldown_blocked": False,
            "mornye_particle_jet_triggered": False,
            "mornye_particle_jet_cooldown_blocked": False,
            "lynae_spectral_analysis_triggered": False,
            "lynae_spectral_analysis_cooldown_blocked": False,
            "unresolved_response_damage_events": [],
            "tune_response_events": [],
        }
        result.party_response_scan_triggered = True
        result.response_source_status = log["response_source_status"]
        result.tune_response_damage_formula_source_status = log["tune_response_damage_formula_source_status"]
        result.tune_response_event_order_source_status = log["tune_response_event_order_source_status"]
        result.tune_break_damage_receives_new_interfered_marker_amp = False
        result.tune_break_response_event_tags = []
        if interfered_state == "tune_rupture_interfered" and "aemeath" in self.characters:
            self._trigger_tune_response(
                result=result,
                log=log,
                response_id="aemeath_starburst",
                cooldown_attr="aemeath_starburst_response_cooldown_remaining",
                trigger_count_attr="aemeath_starburst_trigger_count",
                blocked_count_attr="aemeath_starburst_cooldown_blocked_count",
                triggered_field="aemeath_starburst_triggered",
                blocked_field="aemeath_starburst_cooldown_blocked",
                cooldown_started_field="aemeath_starburst_cooldown_started",
                response_damage_field="aemeath_starburst_response_damage",
                damage_total_attr="aemeath_starburst_damage_total",
                damage_total_field="aemeath_starburst_damage_total",
                event_tag="aemeath_tune_rupture_response_starburst",
            )
        if interfered_state == "tune_rupture_interfered" and "mornye" in self.characters:
            self._trigger_tune_response(
                result=result,
                log=log,
                response_id="mornye_particle_jet",
                cooldown_attr="mornye_particle_jet_response_cooldown_remaining",
                trigger_count_attr="mornye_particle_jet_trigger_count",
                blocked_count_attr="mornye_particle_jet_cooldown_blocked_count",
                triggered_field="mornye_particle_jet_triggered",
                blocked_field="mornye_particle_jet_cooldown_blocked",
                cooldown_started_field="mornye_particle_jet_cooldown_started",
                response_damage_field="mornye_particle_jet_response_damage",
                damage_total_attr="mornye_particle_jet_damage_total",
                damage_total_field="mornye_particle_jet_damage_total",
                event_tag="mornye_tune_rupture_response_particle_jet",
            )
        if "lynae" in self.characters:
            response_def = self.tune_response_defs.get("lynae_spectral_analysis", {})
            supported_states = set(response_def.get("supported_interfered_states") or ["tune_rupture_interfered"])
            if interfered_state in supported_states:
                self._trigger_tune_response(
                    result=result,
                    log=log,
                    response_id="lynae_spectral_analysis",
                    cooldown_attr="lynae_spectral_analysis_response_cooldown_remaining",
                    trigger_count_attr="lynae_spectral_analysis_trigger_count",
                    blocked_count_attr="lynae_spectral_analysis_cooldown_blocked_count",
                    triggered_field="lynae_spectral_analysis_triggered",
                    blocked_field="lynae_spectral_analysis_cooldown_blocked",
                    cooldown_started_field="lynae_spectral_analysis_cooldown_started",
                    response_damage_field="lynae_spectral_analysis_response_damage",
                    damage_total_attr="lynae_spectral_analysis_damage_total",
                    damage_total_field="lynae_spectral_analysis_damage_total",
                    event_tag="lynae_tune_response_spectral_analysis",
                )
        for event_id in log["unresolved_response_damage_events"]:
            if event_id not in self.state.unresolved_response_damage_events:
                self.state.unresolved_response_damage_events.append(event_id)
        result.unresolved_response_damage_events = list(self.state.unresolved_response_damage_events)
        result.response_damage_receives_new_interfered_marker_amp = bool(
            result.response_damage_receives_newly_applied_interfered_marker_amp
        )
        log["response_damage_receives_interfered_marker_amp"] = result.response_damage_receives_interfered_marker_amp
        log["response_damage_receives_newly_applied_interfered_marker_amp"] = (
            result.response_damage_receives_newly_applied_interfered_marker_amp
        )
        log["response_damage_receives_existing_interfered_marker_amp"] = (
            result.response_damage_receives_existing_interfered_marker_amp
        )
        log["response_damage_receives_new_interfered_marker_amp"] = result.response_damage_receives_new_interfered_marker_amp
        self.state.response_damage_receives_interfered_marker_amp = (
            self.state.response_damage_receives_interfered_marker_amp
            or result.response_damage_receives_interfered_marker_amp
        )
        self.state.response_damage_receives_newly_applied_interfered_marker_amp = (
            self.state.response_damage_receives_newly_applied_interfered_marker_amp
            or result.response_damage_receives_newly_applied_interfered_marker_amp
        )
        self.state.response_damage_receives_existing_interfered_marker_amp = (
            self.state.response_damage_receives_existing_interfered_marker_amp
            or result.response_damage_receives_existing_interfered_marker_amp
        )
        self.state.response_damage_receives_new_interfered_marker_amp = (
            self.state.response_damage_receives_newly_applied_interfered_marker_amp
        )
        self.state.party_response_scan_logs.append(log)

    def _trigger_tune_response(
        self,
        *,
        result: Any,
        log: dict[str, Any],
        response_id: str,
        cooldown_attr: str,
        trigger_count_attr: str,
        blocked_count_attr: str,
        triggered_field: str,
        blocked_field: str,
        cooldown_started_field: str,
        response_damage_field: str,
        damage_total_attr: str,
        damage_total_field: str,
        event_tag: str,
    ) -> None:
        response_def = self.tune_response_defs.get(response_id, {})
        source_character_id = str(response_def.get("source_character_id") or "")
        if source_character_id not in self.characters:
            return
        if float(getattr(self.state, cooldown_attr, 0.0) or 0.0) > 0.0:
            setattr(result, blocked_field, True)
            log[blocked_field] = True
            setattr(self.state, blocked_count_attr, int(getattr(self.state, blocked_count_attr, 0) or 0) + 1)
            return

        character = self.characters[source_character_id]
        multiplier = float(response_def.get("multiplier", 0.0) or 0.0)
        constellation_variant = "c0"
        if response_id == "mornye_particle_jet":
            constellation = self._mornye_constellation()
            c5_threshold = int(response_def.get("c5_enabled_constellation", 5) or 5)
            if constellation >= c5_threshold:
                multiplier = float(response_def.get("c5_multiplier", multiplier) or multiplier)
                constellation_variant = "c5"
            result.mornye_particle_jet_multiplier_used = multiplier
            result.mornye_particle_jet_constellation_variant = constellation_variant
        if response_id == "lynae_spectral_analysis":
            constellation = self._lynae_constellation()
            c2_threshold = int(response_def.get("c2_enabled_constellation", 2) or 2)
            c2_enabled = bool(response_def.get("c2_enabled_by_default", False)) and constellation >= c2_threshold
            if c2_enabled:
                multiplier = float(response_def.get("c2_multiplier", multiplier) or multiplier)
                constellation_variant = "c2"
            result.lynae_spectral_analysis_multiplier_used = multiplier
            result.lynae_spectral_analysis_constellation_variant = constellation_variant
            result.lynae_spectral_analysis_c2_disabled_by_default = not c2_enabled
        applied_amp = current_interfered_damage_taken_amp(self.state)
        receives_marker_amp = applied_amp > 0.0
        receives_new_marker_amp = receives_marker_amp and bool(result.interfered_marker_newly_applied_this_action)
        receives_existing_marker_amp = (
            receives_marker_amp
            and not receives_new_marker_amp
            and bool(result.previous_interfered_marker_active_before_response)
        )
        detail = calculate_tune_response_damage_detail(
            tune_response_id=response_id,
            tune_response_hit_id=f"{response_id}_1",
            tune_response_multiplier=multiplier,
            additional_tune_response_boost=float(response_def.get("additional_tune_response_boost", 0.0) or 0.0),
            tune_dmg_bonus=self.state.tune_dmg_bonus,
            enemy_res=self.state.enemy_res,
            res_pen=self.state.res_pen,
            attacker_level=character.attacker_level,
            enemy_level=self.state.enemy_level,
            def_ignore=character.def_ignore,
            def_reduction=self.state.def_reduction,
            applied_damage_taken_amp=applied_amp,
            tune_response_base_value=float(response_def.get("base_value", 10000.0) or 10000.0),
            tune_response_raw_damage_type=str(response_def.get("raw_damage_type", "tune_break_response")),
            tune_response_element=str(response_def.get("element", "fusion")),
            source_status=str(response_def.get("source_status", "workbook_confirmed")),
        )
        detail["response_damage_receives_interfered_marker_amp"] = receives_marker_amp
        detail["response_damage_receives_newly_applied_interfered_marker_amp"] = receives_new_marker_amp
        detail["response_damage_receives_existing_interfered_marker_amp"] = receives_existing_marker_amp
        detail["response_damage_receives_new_interfered_marker_amp"] = receives_new_marker_amp
        detail["response_amp_timing_source_status"] = "excel_event_order_derived"
        if response_id == "mornye_particle_jet":
            detail["mornye_constellation"] = self._mornye_constellation()
            detail["mornye_particle_jet_constellation_variant"] = constellation_variant
        if response_id == "lynae_spectral_analysis":
            detail["lynae_constellation"] = self._lynae_constellation()
            detail["lynae_spectral_analysis_constellation_variant"] = constellation_variant
            detail["lynae_spectral_analysis_c2_disabled_by_default"] = result.lynae_spectral_analysis_c2_disabled_by_default
        damage = float(detail["tune_response_damage"])
        account_response_context = build_account_tune_response_damage_context(
            state=self.state,
            characters=self.characters,
            response_id=response_id,
            source_character_id=source_character_id,
        )
        expected_crit_multiplier = float(account_response_context.get("expected_crit_multiplier", 1.0) or 1.0)
        if expected_crit_multiplier != 1.0:
            detail["damage_before_account_fixed_crit"] = damage
            detail["crit_rate_before_override"] = float(getattr(character, "crit_rate", 0.0) or 0.0)
            detail["crit_damage_before_override"] = float(getattr(character, "crit_damage", 0.0) or 0.0)
            detail["crit_rate_after_override"] = account_response_context["crit_rate_override"]
            detail["crit_damage_after_override"] = account_response_context["crit_damage_override"]
            detail["expected_crit_multiplier"] = expected_crit_multiplier
            detail["account_constellation_damage_context"] = list(account_response_context.get("events", []))
            damage *= expected_crit_multiplier
        damage, lynae_tune_strain_log = apply_lynae_tune_strain_damage_amp(
            damage,
            source_character_id=source_character_id,
            state=self.state,
            characters=self.characters,
            buffs=self.buffs,
        )
        detail.update(lynae_tune_strain_log)
        detail["damage"] = damage
        detail["tune_response_damage"] = damage
        if lynae_tune_strain_log["lynae_tune_strain_damage_amp_bonus_damage"] > 0.0:
            detail["tune_response_damage_before_lynae_tune_strain_amp"] = (
                damage - lynae_tune_strain_log["lynae_tune_strain_damage_amp_bonus_damage"]
            )
            detail["tune_response_damage_after_lynae_tune_strain_amp"] = damage
        cooldown = float(response_def.get("cooldown_seconds", 8.0) or 8.0)

        setattr(self.state, trigger_count_attr, int(getattr(self.state, trigger_count_attr, 0) or 0) + 1)
        setattr(self.state, cooldown_attr, cooldown)
        setattr(result, triggered_field, True)
        setattr(result, cooldown_started_field, True)
        setattr(result, response_damage_field, damage)
        setattr(result, damage_total_field, float(getattr(self.state, damage_total_attr, 0.0) or 0.0) + damage)
        setattr(result, f"{cooldown_attr}", cooldown)
        result.lynae_tune_strain_damage_amp_bonus_damage += float(
            lynae_tune_strain_log.get("lynae_tune_strain_damage_amp_bonus_damage", 0.0) or 0.0
        )
        self._sync_lynae_tune_strain_result_fields(result)
        result.tune_response_damage += damage
        result.tune_response_damage_total = self.state.tune_response_damage_total + damage
        result.damage += damage
        result.total_action_damage += damage
        result.hit_count += 1
        result.hit_damage_by_category["tune_response"] = result.hit_damage_by_category.get("tune_response", 0.0) + damage
        result.tune_response_hit_details.append(detail)
        result.hit_details.append(detail)
        result.response_damage_receives_interfered_marker_amp = (
            bool(result.response_damage_receives_interfered_marker_amp) or receives_marker_amp
        )
        result.response_damage_receives_newly_applied_interfered_marker_amp = (
            bool(result.response_damage_receives_newly_applied_interfered_marker_amp) or receives_new_marker_amp
        )
        result.response_damage_receives_existing_interfered_marker_amp = (
            bool(result.response_damage_receives_existing_interfered_marker_amp) or receives_existing_marker_amp
        )
        result.response_damage_receives_new_interfered_marker_amp = (
            bool(result.response_damage_receives_newly_applied_interfered_marker_amp)
        )
        self.state.total_damage += damage
        self.state.tune_response_damage_total += damage
        setattr(self.state, damage_total_attr, float(getattr(self.state, damage_total_attr, 0.0) or 0.0) + damage)
        result.total_damage_after = self.state.total_damage

        tune_break_event_id = f"{result.action_id}:{response_id}:{len(result.tune_response_events) + 1}"
        event = {
            "event_id": tune_break_event_id,
            "response_id": response_id,
            "source_character_id": source_character_id,
            "damage": damage,
            "cooldown_seconds": cooldown,
            "applied_damage_taken_amp": applied_amp,
            "response_damage_receives_interfered_marker_amp": receives_marker_amp,
            "response_damage_receives_newly_applied_interfered_marker_amp": receives_new_marker_amp,
            "response_damage_receives_existing_interfered_marker_amp": receives_existing_marker_amp,
            "response_damage_receives_new_interfered_marker_amp": receives_new_marker_amp,
            "response_amp_timing_source_status": "excel_event_order_derived",
            "source_status": detail["source_status"],
            **lynae_tune_strain_log,
        }
        response_context = {
            "tune_break_event_id": tune_break_event_id,
            "host_action_id": result.action_id,
            "response_id": response_id,
            "response_action_id": response_id,
            "source_character_id": source_character_id,
            "interfered_state": self.state.target_interfered_state,
            "triggered": True,
            "response_damage": damage,
            "cooldown_seconds": cooldown,
            "source_status": detail["source_status"],
        }
        mechanic_followup_events = []
        for mechanic in self.character_mechanics.values():
            hook = getattr(mechanic, "on_party_tune_response_resolved", None)
            if hook is None:
                continue
            followup_event = hook(self.state, response_context)
            if followup_event:
                mechanic_followup_events.append(followup_event)
        if mechanic_followup_events:
            event["mechanic_followup_events"] = mechanic_followup_events
            result.aemeath_rupturous_trail_gain_events.extend(
                followup_event
                for followup_event in mechanic_followup_events
                if followup_event.get("event_type") == "rupturous_trail_gain"
            )
        result.tune_response_events.append(event)
        self.state.tune_response_events.append(event)
        log["tune_response_events"].append(event)
        log[triggered_field] = True
        result.tune_break_response_event_tags.append(event_tag)

    def _available_tune_break_action_ids(self) -> list[str]:
        return [
            action_id
            for action_id, action in self.policy_actions.items()
            if action.action_type == "tune_break" and self.is_resolved_action_available(action)
        ]

    def _sync_lynae_tune_strain_result_fields(self, result: Any) -> None:
        result.target_tune_strain_interfered_stacks = self.state.target_tune_strain_interfered_stacks
        result.target_tune_strain_interfered_max_stacks = self.state.target_tune_strain_interfered_max_stacks
        result.target_tune_strain_interfered_remaining = self.state.target_tune_strain_interfered_remaining
        result.lynae_tune_strain_damage_amp = self.state.lynae_tune_strain_damage_amp
        result.lynae_tune_strain_damage_multiplier = self.state.lynae_tune_strain_damage_multiplier
        result.lynae_tune_strain_source_status = self.state.lynae_tune_strain_source_status
        result.lynae_tune_strain_source_ref = self.state.lynae_tune_strain_source_ref

    def _sync_tune_break_result_fields(self, result: Any) -> None:
        result.enemy_off_tune_current_after = self.state.enemy_off_tune_current
        result.enemy_off_tune_max = self.state.enemy_off_tune_max
        result.enemy_mistune_active = self.state.enemy_mistune_active
        result.enemy_tune_break_available = self.state.enemy_tune_break_available
        result.enemy_tune_break_cooldown_seconds = self.state.enemy_tune_break_cooldown_seconds
        result.enemy_tune_break_cooldown_source_status = self.state.enemy_tune_break_cooldown_source_status
        result.enemy_tune_break_cooldown_source_ref = self.state.enemy_tune_break_cooldown_source_ref
        result.enemy_tune_break_cooldown_remaining = self.state.enemy_tune_break_cooldown_remaining
        result.tune_break_action_available_ids = self._available_tune_break_action_ids()
        result.tune_break_action_used_count = self.state.tune_break_action_used_count
        result.tune_break_damage_total = self.state.tune_break_damage_total
        result.tune_response_damage_total = self.state.tune_response_damage_total
        result.aemeath_starburst_damage_total = self.state.aemeath_starburst_damage_total
        result.mornye_particle_jet_damage_total = self.state.mornye_particle_jet_damage_total
        result.lynae_spectral_analysis_damage_total = self.state.lynae_spectral_analysis_damage_total
        result.aemeath_starburst_response_cooldown_remaining = (
            self.state.aemeath_starburst_response_cooldown_remaining
        )
        result.mornye_particle_jet_response_cooldown_remaining = (
            self.state.mornye_particle_jet_response_cooldown_remaining
        )
        result.lynae_spectral_analysis_response_cooldown_remaining = (
            self.state.lynae_spectral_analysis_response_cooldown_remaining
        )
        result.aemeath_starburst_cooldown_blocked_count = self.state.aemeath_starburst_cooldown_blocked_count
        result.mornye_particle_jet_cooldown_blocked_count = self.state.mornye_particle_jet_cooldown_blocked_count
        result.lynae_spectral_analysis_cooldown_blocked_count = (
            self.state.lynae_spectral_analysis_cooldown_blocked_count
        )
        result.tune_response_events = list(result.tune_response_events or [])
        if not result.tune_response_damage_formula_source_status:
            result.tune_response_damage_formula_source_status = self.state.tune_response_damage_formula_source_status
        if not result.tune_response_event_order_source_status:
            result.tune_response_event_order_source_status = self.state.tune_response_event_order_source_status
        result.response_damage_receives_new_interfered_marker_amp = (
            result.response_damage_receives_newly_applied_interfered_marker_amp
        )
        result.target_tune_shift_state = self.state.target_tune_shift_state
        result.target_tune_shift_remaining = self.state.target_tune_shift_remaining
        result.target_interfered_state = self.state.target_interfered_state
        result.target_interfered_remaining = self.state.target_interfered_remaining
        self._sync_lynae_tune_strain_result_fields(result)
        result.observation_marker_remaining = self._mornye_observation_marker_remaining()
        result.observation_marker_active = result.observation_marker_remaining > 0.0
        result.interfered_marker_remaining = self.state.interfered_marker_remaining
        result.interfered_marker_active = self.state.interfered_marker_remaining > 0.0
        result.interfered_marker_applied_count = self.state.interfered_marker_applied_count
        result.interfered_marker_damage_taken_amp = self.state.interfered_marker_damage_taken_amp
        result.interfered_marker_damage_taken_multiplier = 1.0 + self.state.interfered_marker_damage_taken_amp
        result.party_response_scan_triggered = bool(result.party_response_scan_triggered)
        result.unresolved_response_damage_events = list(self.state.unresolved_response_damage_events)

    def resolve_action_for_character(
        self,
        selected_action: ActionData,
        character_id: str | None = None,
    ) -> ActionData:
        resolver_character_id = character_id or selected_action.character_id or self.state.active_character_id
        mechanic = self._mechanic_for_character(resolver_character_id)
        return mechanic.resolve_action(self.state, selected_action, self.actions)

    def resolve_action(self, selected_action: ActionData) -> ActionData:
        return self.resolve_action_for_character(selected_action, self.state.active_character_id)

    def resolve_action_id(self, action_id: str) -> str:
        return self.resolve_action(self.actions[action_id]).id

    def get_policy_action_ids(self) -> list[str]:
        return list(self.policy_actions)

    @property
    def has_placeholder_swap_timing(self) -> bool:
        fallback = fallback_swap_timing(self.transition_config, self.preset_generic_swap)
        if bool(fallback.get("is_placeholder", True)):
            return True
        return any(row.swap_timing_is_placeholder for row in self.timeline)

    def _build_policy_actions(self) -> dict[str, ActionData]:
        policy_actions: dict[str, ActionData] = {}
        appended_policy_actions: list[tuple[str, ActionData]] = []
        selected = set(self.selected_character_ids)
        for action_id, action in self.actions.items():
            if not action.policy_selectable:
                continue
            if is_swap_action(action):
                target = get_swap_target_character_id(action)
                if len(selected) <= 1 or target not in selected:
                    continue
            if action.character_id is not None and action.character_id not in selected:
                continue
            if bool((action.mechanic_effects or {}).get("policy_order_append", False)):
                appended_policy_actions.append((action_id, action))
            else:
                policy_actions[action_id] = action
        for action_id, action in appended_policy_actions:
            policy_actions[action_id] = action
        return policy_actions

    def _ensure_party_swap_actions(self) -> None:
        fallback = fallback_swap_timing(self.transition_config, self.preset_generic_swap)
        action_time = float(fallback["action_time"])
        combat_time_cost = float(fallback.get("combat_time_cost", action_time))
        for character_id in self.selected_character_ids:
            action_id = f"swap_to_{character_id}"
            character_name = self.all_characters[character_id].name
            self.actions[action_id] = ActionData(
                id=action_id,
                name=f"Swap to {character_name}",
                character_id=character_id,
                action_type="swap",
                duration=action_time,
                action_time=action_time,
                combat_time_cost=max(combat_time_cost, 0.0),
                cooldown=SWAP_REENTRY_COOLDOWN_SECONDS,
                cooldown_group=swap_reentry_key(character_id),
                damage_multiplier=0.0,
                resonance_energy_cost=0.0,
                tags=["swap", "party-foundation", "party-transition"],
                mechanic_effects={
                    "zero_time_transition_action": action_time == 0.0 and combat_time_cost == 0.0,
                    "swap_contract_source_status": str(
                        fallback.get("source_status") or GENERIC_SWAP_SOURCE_STATUS
                    ),
                },
                data_status="transition_request",
                notes="Generated party swap transition request using the v114 zero-time/re-entry contract.",
            )

    def _apply_transition_resolution(self, result, transition_resolution) -> None:
        result.outgoing_character_id = transition_resolution.outgoing_character_id
        result.incoming_character_id = transition_resolution.incoming_character_id
        result.transition_type = transition_resolution.transition_type
        result.transition_reason = transition_resolution.transition_reason
        result.outgoing_concerto_before = transition_resolution.outgoing_concerto_before
        result.outgoing_concerto_ready = transition_resolution.outgoing_concerto_ready
        result.outgoing_concerto_consumed = transition_resolution.outgoing_concerto_consumed
        result.outgoing_concerto_after = transition_resolution.outgoing_concerto_after
        result.incoming_qte_candidate_id = transition_resolution.incoming_qte_candidate_id
        result.incoming_qte_mode = transition_resolution.incoming_qte_mode
        result.incoming_qte_applied = transition_resolution.incoming_qte_applied
        result.incoming_qte_damage_bonus_category = transition_resolution.incoming_qte_damage_bonus_category
        result.incoming_qte_trigger_classification = transition_resolution.incoming_qte_trigger_classification
        result.incoming_qte_source_damage_label = transition_resolution.incoming_qte_source_damage_label
        result.incoming_qte_previous_outro_trigger_frame = transition_resolution.incoming_qte_previous_outro_trigger_frame
        result.incoming_qte_flow_light_metadata_present = transition_resolution.incoming_qte_flow_light_metadata_present
        result.incoming_qte_flow_light_applied = transition_resolution.incoming_qte_flow_light_applied
        result.incoming_intro_candidate_id = transition_resolution.incoming_intro_candidate_id
        result.incoming_intro_mode = transition_resolution.incoming_intro_mode
        result.incoming_intro_applied = transition_resolution.incoming_intro_applied
        result.incoming_intro_damage_bonus_category = transition_resolution.incoming_intro_damage_bonus_category
        result.incoming_intro_trigger_classification = transition_resolution.incoming_intro_trigger_classification
        result.incoming_intro_source_damage_label = transition_resolution.incoming_intro_source_damage_label
        result.outgoing_outro_applied = transition_resolution.outgoing_outro_applied
        result.outgoing_scheduled_action_id = transition_resolution.outgoing_scheduled_action_id
        result.outgoing_scheduled_action_started = transition_resolution.outgoing_scheduled_action_started
        result.outgoing_scheduled_action_instance_id = transition_resolution.outgoing_scheduled_action_instance_id
        result.outgoing_scheduled_source_summary = (
            self._build_outgoing_transition_source_summary(transition_resolution.outgoing_scheduled_action_instance_id)
            if transition_resolution.outgoing_scheduled_action_instance_id
            else dict(transition_resolution.outgoing_scheduled_source_summary)
        )
        result.transition_events = transition_resolution.transition_events
        result.transition_event_details = transition_resolution.transition_events
        result.outgoing_outro_event_id = transition_resolution.outgoing_outro_event_id
        result.incoming_intro_event_id = transition_resolution.incoming_intro_event_id
        result.fallback_swap_used = transition_resolution.fallback_swap_used
        result.swap_timing_is_placeholder = transition_resolution.swap_timing_is_placeholder
        result.swap_timing_source = transition_resolution.swap_timing_source
        result.generic_swap_zero_time = transition_resolution.generic_swap_zero_time
        result.swap_reentry_cooldown_seconds = transition_resolution.swap_reentry_cooldown_seconds
        result.outgoing_swap_reentry_key = transition_resolution.outgoing_swap_reentry_key
        result.outgoing_swap_reentry_before = transition_resolution.outgoing_swap_reentry_before
        result.outgoing_swap_reentry_after_set = transition_resolution.outgoing_swap_reentry_after_set
        result.outgoing_swap_reentry_after_action = transition_resolution.outgoing_swap_reentry_after_action
        result.incoming_swap_reentry_key = transition_resolution.incoming_swap_reentry_key
        result.incoming_swap_reentry_before = transition_resolution.incoming_swap_reentry_before
        result.incoming_swap_reentry_blocked = transition_resolution.incoming_swap_reentry_blocked
        result.swap_contract_source_status = transition_resolution.swap_contract_source_status
        result.transition_warnings = transition_resolution.warnings

        for event in transition_resolution.transition_events:
            if event.get("action_id") != "aemeath_outro_unseen_guard":
                continue
            result.aemeath_outro_applied = bool(event.get("aemeath_outro_applied", False))
            result.aemeath_outro_mode_snapshot = event.get("mode_snapshot")
            result.aemeath_outro_base_amp = float(event.get("base_amp", 0.0) or 0.0)
            result.aemeath_outro_duration = float(event.get("duration", 0.0) or 0.0)
            result.aemeath_outro_recipient_values_before = dict(event.get("recipient_values_before") or {})
            result.aemeath_outro_recipient_values_after = dict(event.get("recipient_values_after") or {})
            result.aemeath_outro_unresolved_reason = event.get("unresolved_reason")

        applied_buffs = list(result.applied_buffs)
        for event in transition_resolution.transition_events:
            if event.get("applied_before_action"):
                for buff_id in event.get("applies_buffs", []):
                    applied_buffs.append(buff_id)
        result.applied_buffs = applied_buffs

        if not result.truncated_by_combat_limit:
            for event in transition_resolution.transition_events:
                for buff_id in event.get("applies_buffs", []):
                    if buff_id not in self.buffs:
                        result.transition_warnings.append(f"Transition buff {buff_id!r} is not registered.")
                        continue
                    if event.get("applied_before_action"):
                        continue
                    add_team_buff(self.state, self.buffs[buff_id], event.get("character_id"))
                    applied_buffs.append(buff_id)
            result.applied_buffs = applied_buffs
        result.active_buffs = [
            buff.buff_id
            for buff in self.state.active_buffs
            if buff.remaining_duration > 0.0
        ]
        if self.state.action_log:
            self.state.action_log[-1] = result.model_dump(mode="json")

    def _apply_lynae_transition_buffs(self, result, transition_resolution) -> None:
        if transition_resolution.outgoing_character_id != "lynae":
            return
        if not transition_resolution.outgoing_outro_applied:
            return
        if "lynae" not in self.characters:
            return
        incoming_character_id = transition_resolution.incoming_character_id
        if incoming_character_id not in self.characters:
            return
        application_time = float(result.combat_time_end)
        applied: list[str] = []

        for buff_id in ("lynae_outro_all_damage_amp", "lynae_outro_liberation_damage_amp"):
            if self._apply_specific_character_buff(
                buff_id=buff_id,
                source_character_id="lynae",
                target_character_id=incoming_character_id,
                application_time=application_time,
                metadata={"event_source": "lynae_outro"},
            ):
                applied.append(buff_id)
        result.lynae_outro_all_damage_amp_value = 0.15 if "lynae_outro_all_damage_amp" in applied else 0.0
        result.lynae_outro_liberation_damage_amp_value = (
            0.25 if "lynae_outro_liberation_damage_amp" in applied else 0.0
        )

        lynae_weapon_profile = self.characters["lynae"].weapon or {}
        lynae_weapon = lynae_weapon_profile.get("weapon_id")
        if lynae_weapon == "static_mist":
            static_mist = (self.weapon_definitions.get("weapons") or {}).get("static_mist") or {}
            static_mist_rank = int(lynae_weapon_profile.get("rank", 1) or 1)
            static_mist_value = resolve_weapon_rank_value(
                static_mist,
                static_mist_rank,
                "incoming_atk_percent_after_outro",
            )
            if self._apply_specific_character_buff(
                buff_id="static_mist_incoming_atk",
                source_character_id="lynae",
                target_character_id=incoming_character_id,
                application_time=application_time,
                dynamic_buff_value=static_mist_value,
                metadata={
                    "event_source": "lynae_outro",
                    "weapon_id": "static_mist",
                    "weapon_rank": static_mist_rank,
                },
            ):
                applied.append("static_mist_incoming_atk")
                result.lynae_static_mist_incoming_atk_buff = True
                result.lynae_static_mist_incoming_atk_value = static_mist_value

        pact_log = apply_pact_neonlight_outro_incoming_buff(
            source_character_id="lynae",
            incoming_character_id=incoming_character_id,
            characters=self.characters,
            state=self.state,
            buffs=self.buffs,
            application_time=application_time,
            event_source="lynae_outro",
        )
        if pact_log.get("pact_neonlight_incoming_atk_buff"):
            applied.extend(pact_log.get("echo_set_triggered_buff_ids", []))
            result.pact_neonlight_incoming_atk_buff = True
            result.pact_neonlight_incoming_atk_base = float(pact_log.get("pact_neonlight_incoming_atk_base", 0.0))
            result.pact_neonlight_incoming_atk_from_tune_break_boost = float(
                pact_log.get("pact_neonlight_incoming_atk_from_tune_break_boost", 0.0)
            )
            result.pact_neonlight_incoming_atk_total = float(pact_log.get("pact_neonlight_incoming_atk_total", 0.0))
            result.pact_neonlight_source_status = pact_log.get("pact_neonlight_source_status")

        lynae_state = self.state.character_mechanics_state.get("lynae", {})
        lynae_state["kaleidoscopic_parade_remaining"] = 0.0
        lynae_state["lumiflow"] = 0.0
        lynae_state["true_color"] = 0.0
        lynae_state["kaleidoscopic_combo_stage"] = 1
        lynae_state["next_basic_forced_stage"] = None
        lynae_state["optical_sampling_stage_active"] = True
        result.lynae_kaleidoscopic_parade_remaining = 0.0
        result.lynae_lumiflow = 0.0
        result.lynae_true_color = 0.0
        result.lynae_optical_sampling_stage_active = True
        if float(lynae_state.get("hyvatia_outro_window_remaining", 0.0) or 0.0) > 0.0:
            if self._apply_specific_character_buff(
                buff_id="hyvatia_incoming_all_attribute_damage_bonus",
                source_character_id="lynae",
                target_character_id=incoming_character_id,
                application_time=application_time,
                metadata={"event_source": "lynae_outro_after_hyvatia", "main_echo_id": "hyvatia"},
            ):
                applied.append("hyvatia_incoming_all_attribute_damage_bonus")
                result.lynae_hyvatia_incoming_all_attribute_buff = True
                result.lynae_hyvatia_incoming_all_attribute_value = 0.10

        for buff_id in applied:
            if buff_id not in result.applied_buffs:
                result.applied_buffs.append(buff_id)
        result.active_buffs = [buff.buff_id for buff in self.state.active_buffs if buff.remaining_duration > 0.0]
        if self.state.action_log:
            self.state.action_log[-1] = result.model_dump(mode="json")

    def _apply_lynae_incoming_intro_mechanics(self, result, transition_resolution) -> None:
        if transition_resolution.incoming_character_id != "lynae":
            return
        if not transition_resolution.incoming_intro_applied:
            return
        intro_applied = any(
            event.get("event_type") == "intro_qte"
            and event.get("character_id") == "lynae"
            and event.get("action_id") == "lynae_intro_time_to_show_some_colors"
            and event.get("applied")
            for event in transition_resolution.transition_events
        )
        if not intro_applied:
            return
        lynae_state = self.state.character_mechanics_state.setdefault("lynae", {})
        overflow_max = float(lynae_state.get("overflow_max", 120.0) or 120.0)
        lynae_state["overflow"] = min(overflow_max, float(lynae_state.get("overflow", 0.0) or 0.0) + 100.0)
        lynae_state["photocromic_flux_active"] = True
        lynae_state["photocromic_flux_remaining"] = 25.0
        lynae_state["photocromic_flux_source_action_id"] = "lynae_intro_time_to_show_some_colors"
        mode = str(lynae_state.get("lynae_resonance_mode", "tune_rupture") or "tune_rupture")
        if mode == "tune_strain":
            shift_state = "tune_strain_shifting"
        elif mode == "tune_rupture":
            shift_state = "tune_rupture_shifting"
        else:
            shift_state = None
            result.lynae_photocromic_flux_unresolved_reason = "lynae_resonance_mode_unresolved_no_shift_state"
        lynae_state["target_tune_shift_state"] = shift_state
        lynae_state["target_tune_shift_remaining"] = 25.0 if shift_state else 0.0
        if shift_state:
            self.state.target_tune_shift_state = shift_state
            self.state.target_tune_shift_remaining = 25.0
            result.target_tune_shift_state = shift_state
            result.target_tune_shift_remaining = 25.0
            if shift_state == "tune_rupture_shifting":
                if shift_state not in result.emitted_mechanic_event_tags:
                    result.emitted_mechanic_event_tags.append(shift_state)
                self.state.mechanic_event_emitted_counts[shift_state] = (
                    self.state.mechanic_event_emitted_counts.get(shift_state, 0) + 1
                )
                self.state.mechanic_event_log.append(
                    {
                        "event_tag": shift_state,
                        "trigger_id": "lynae_intro_photocromic_flux",
                        "action_id": "lynae_intro_time_to_show_some_colors",
                        "character_id": "lynae",
                        "combat_time": result.combat_time_end,
                        "source_status": "user_tooltip_confirmed",
                        "damage_added": 0.0,
                    }
                )
        result.lynae_overflow = float(lynae_state["overflow"])
        result.lynae_photocromic_flux_active = True
        result.lynae_photocromic_flux_applied = True
        result.lynae_photocromic_flux_remaining = 25.0
        result.lynae_photocromic_flux_mode = mode
        result.lynae_photocromic_flux_source_status = "user_tooltip_confirmed"
        result.lynae_target_tune_shift_state = shift_state
        result.lynae_target_tune_shift_remaining = 25.0 if shift_state else 0.0
        if self.state.action_log:
            self.state.action_log[-1] = result.model_dump(mode="json")

    def _apply_aemeath_incoming_intro_mechanics(self, result, transition_resolution) -> None:
        if not self.account_simulation_scope or not any(
            character.account_profile for character in self.characters.values()
        ):
            return
        if transition_resolution.incoming_character_id != "aemeath":
            return
        if not transition_resolution.incoming_intro_applied:
            return
        intro_action_id = transition_resolution.incoming_intro_candidate_id
        if intro_action_id not in {"aemeath_qte_intro_human", "aemeath_qte_intro_mech"}:
            return
        intro_event = next(
            (
                event
                for event in transition_resolution.transition_events
                if event.get("action_id") == intro_action_id
                and event.get("applied")
            ),
            None,
        )
        if intro_event is None:
            return
        aemeath_state = self.state.character_mechanics_state.setdefault("aemeath", {})
        before = float(aemeath_state.get("starlume_acceleration_remaining", 0.0) or 0.0)
        aemeath_state["starlume_acceleration_remaining"] = 15.0
        intro_event["starlume_acceleration_applied"] = True
        intro_event["starlume_acceleration_remaining_before"] = before
        intro_event["starlume_acceleration_remaining_after"] = 15.0

    def _apply_specific_character_buff(
        self,
        *,
        buff_id: str,
        source_character_id: str,
        target_character_id: str,
        application_time: float,
        dynamic_damage_amp_value: float | None = None,
        dynamic_buff_value: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        buff = self.buffs.get(buff_id)
        if buff is None:
            return False
        runtime_buff = buff.model_copy(deep=True)
        resolved_dynamic_value = (
            float(dynamic_buff_value)
            if dynamic_buff_value is not None
            else float(dynamic_damage_amp_value)
            if dynamic_damage_amp_value is not None
            else float(runtime_buff.value)
        )
        runtime_buff.value = resolved_dynamic_value
        runtime_buff.target_scope = "specific_character"
        runtime_buff.target_character_id = target_character_id
        runtime_buff.source_character_id = source_character_id
        runtime_buff.metadata = {
            **runtime_buff.metadata,
            **(metadata or {}),
            "source_character_id": source_character_id,
            "target_character_id": target_character_id,
            "dynamic_value": resolved_dynamic_value,
            "application_time": application_time,
        }
        if runtime_buff.modifier_type == "attack":
            runtime_buff.stat_modifiers = {**runtime_buff.stat_modifiers, "atk_percent": resolved_dynamic_value}
        apply_buff(self.state, runtime_buff, source_character_id)
        return True

    def _apply_pre_transition_events(self, transition_resolution) -> None:
        if transition_resolution is None:
            return
        self._apply_aemeath_outro_base(transition_resolution)
        for event in transition_resolution.transition_events:
            if not event.get("apply_before_action"):
                continue
            applied_buffs = event.setdefault("applied_before_action_buffs", [])
            for buff_id in event.get("applies_buffs", []):
                if buff_id not in self.buffs:
                    continue
                add_team_buff(self.state, self.buffs[buff_id], event.get("character_id"))
                applied_buffs.append(buff_id)
            event["applied_before_action"] = True

    def _aemeath_outro_recipient_values(self) -> dict[str, float]:
        values: dict[str, float] = {}
        for active in self.state.active_buffs:
            if active.buff_id != "aemeath_outro_unseen_guard_all_damage_amp":
                continue
            if active.remaining_duration <= 0.0 or not active.target_character_id:
                continue
            values[active.target_character_id] = float(active.metadata.get("dynamic_value", 0.10) or 0.0)
        return values

    def _apply_aemeath_outro_base(self, transition_resolution) -> None:
        event = next(
            (
                item
                for item in transition_resolution.transition_events
                if item.get("action_id") == "aemeath_outro_unseen_guard" and item.get("applied")
            ),
            None,
        )
        if event is None:
            return
        before = self._aemeath_outro_recipient_values()
        self.state.active_buffs = [
            active
            for active in self.state.active_buffs
            if active.buff_id != "aemeath_outro_unseen_guard_all_damage_amp"
        ]
        self.state.team_buffs = list(self.state.active_buffs)
        mode = aemeath_resonance_mode_from_config(self.state.mechanics_config)
        unresolved_reason = (
            "aemeath_outro_mode_snapshot_unresolved_no_mode_specific_upgrade"
            if mode == "unresolved"
            else None
        )
        recipients = [character_id for character_id in self.selected_character_ids if character_id != "aemeath"]
        for recipient in recipients:
            self._apply_specific_character_buff(
                buff_id="aemeath_outro_unseen_guard_all_damage_amp",
                source_character_id="aemeath",
                target_character_id=recipient,
                application_time=float(self.state.combat_time),
                dynamic_damage_amp_value=0.10,
                metadata={
                    "event_source": "aemeath_outro_unseen_guard",
                    "mode_snapshot": mode,
                    "upgraded": False,
                    "upgrade_event_tag": None,
                    "unresolved_reason": unresolved_reason,
                },
            )
        after = self._aemeath_outro_recipient_values()
        event.update(
            {
                "apply_before_action": True,
                "applied_before_action": True,
                "aemeath_outro_applied": True,
                "mode_snapshot": mode,
                "base_amp": 0.10,
                "duration": 20.0,
                "recipient_values_before": before,
                "recipient_values_after": after,
                "unresolved_reason": unresolved_reason,
            }
        )

    def _apply_aemeath_outro_upgrade(self, result, actor_character_id: str | None) -> None:
        if not actor_character_id or actor_character_id == "aemeath":
            return
        active = next(
            (
                buff
                for buff in self.state.active_buffs
                if buff.buff_id == "aemeath_outro_unseen_guard_all_damage_amp"
                and buff.target_character_id == actor_character_id
                and buff.remaining_duration > 0.0
            ),
            None,
        )
        if active is None:
            return
        mode = str(active.metadata.get("mode_snapshot") or "unresolved")
        expected_tag = {
            "tune_rupture": "tune_rupture_shifting",
            "fusion_burst": "fusion_burst",
        }.get(mode)
        if expected_tag is None or expected_tag not in result.emitted_mechanic_event_tags:
            if mode == "unresolved":
                result.aemeath_outro_unresolved_reason = (
                    "aemeath_outro_mode_snapshot_unresolved_no_mode_specific_upgrade"
                )
            return
        before = self._aemeath_outro_recipient_values()
        already_upgraded = bool(active.metadata.get("upgraded", False))
        remaining_before = float(active.remaining_duration)
        active.metadata = {
            **active.metadata,
            "dynamic_value": 0.20,
            "upgraded": True,
            "upgrade_event_tag": expected_tag,
            "upgrade_combat_time": float(result.combat_time_end),
        }
        after = self._aemeath_outro_recipient_values()
        result.aemeath_outro_upgrade_applied = True
        result.aemeath_outro_mode_snapshot = mode
        result.aemeath_outro_base_amp = 0.10
        result.aemeath_outro_duration = 20.0
        result.aemeath_outro_recipient_values_before = before
        result.aemeath_outro_recipient_values_after = after
        result.aemeath_outro_upgrade_event_tag = expected_tag
        result.aemeath_outro_upgrade_duration_refreshed = False
        if not already_upgraded:
            result.aemeath_outro_upgraded_character_ids = [actor_character_id]
        # The triggering action used its action-start snapshot. Mutating the
        # live instance here only affects later actions and preserves duration.
        active.remaining_duration = remaining_before

    def _apply_post_mechanic_transition_debug(self, result) -> None:
        data = self.state.character_mechanics_state.get("mornye")
        if not isinstance(data, dict):
            return
        result.mornye_mode_after = data.get("mode")
        result.mornye_rest_mass_after = float(data.get("rest_mass_energy", 0.0))
        result.mornye_wfo_remaining_after = float(data.get("wide_field_observation_remaining", 0.0))
        result.mornye_syntony_field_remaining_after = float(data.get("syntony_field_remaining", 0.0))
        result.mornye_high_syntony_field_remaining_after = float(data.get("high_syntony_field_remaining", 0.0))
        result.high_syntony_field_active = result.mornye_high_syntony_field_remaining_after > 0.0
        result.high_syntony_field_remaining = result.mornye_high_syntony_field_remaining_after

    def _mornye_mechanics_config(self) -> dict[str, Any]:
        return dict(((self.state.mechanics_config or {}).get("mornye") or {}))

    def _mornye_constellation(self) -> int:
        mornye = self.characters.get("mornye")
        if mornye is not None and getattr(mornye, "account_profile", False):
            return max(0, int(getattr(mornye, "sequence", 0) or 0))
        return max(0, int(self._mornye_mechanics_config().get("mornye_constellation", 0) or 0))

    def _lynae_mechanics_config(self) -> dict[str, Any]:
        return dict(((self.state.mechanics_config or {}).get("lynae") or {}))

    def _lynae_constellation(self) -> int:
        return max(0, int(self._lynae_mechanics_config().get("lynae_constellation", 0) or 0))

    def _mornye_heal_event_mode(self) -> str:
        mode = str(self._mornye_mechanics_config().get("mornye_heal_event_mode", "scheduled_180f_exact"))
        return (
            mode
            if mode in {"disabled", "field_creation_only", "simplified_syntony_field_uptime", "scheduled_180f_exact"}
            else "disabled"
        )

    def _apply_mornye_syntony_field_uptime_heal_proxy(self, action: ActionData) -> dict[str, Any]:
        if "mornye" not in self.characters:
            return {}
        mode = self._mornye_heal_event_mode()
        if mode == "scheduled_180f_exact":
            return {}
        if mode != "simplified_syntony_field_uptime":
            return {}
        data = self.state.character_mechanics_state.get("mornye") or {}
        syntony_remaining = float(data.get("syntony_field_remaining", 0.0) or 0.0)
        high_syntony_remaining = float(data.get("high_syntony_field_remaining", 0.0) or 0.0)
        if syntony_remaining <= 0.0 and high_syntony_remaining <= 0.0:
            return {}
        log = apply_mornye_halo_of_starry_radiance_5set_event_buff(
            source_character_id="mornye",
            emitted_event_tags=[TEAM_HEAL_EVENT_TAG],
            characters=self.characters,
            state=self.state,
            buffs=self.buffs,
            application_time=self.state.combat_time,
            event_source="simplified_syntony_field_uptime_action_boundary",
        )
        log["mornye_heal_proxy_implementation_status"] = "simplified_field_uptime_heal_proxy"
        if high_syntony_remaining > 0.0:
            log.update(
                {
                    "high_syntony_field_active": True,
                    "high_syntony_field_remaining": high_syntony_remaining,
                    "high_syntony_field_def_bonus_active": any(
                        buff.buff_id == MORNYE_HIGH_SYNTONY_FIELD_DEF_BUFF_ID and buff.remaining_duration > 0.0
                        for buff in self.state.active_buffs
                    ),
                    "high_syntony_field_def_percent_bonus": 0.20,
                    "high_syntony_field_off_tune_inherited": any(
                        buff.buff_id == MORNYE_HIGH_SYNTONY_FIELD_OFF_TUNE_BUFF_ID and buff.remaining_duration > 0.0
                        for buff in self.state.active_buffs
                    ),
                    "high_syntony_field_heal_proxy_active": True,
                    "high_syntony_field_healing_multiplier_bonus": 0.40,
                    "high_syntony_field_healing_multiplier_metadata_only": True,
                }
            )
        log.update(
            self._apply_team_heal_weapon_effects(
                log,
                source_character_id="mornye",
                application_time=self.state.combat_time,
                event_source="simplified_syntony_field_uptime_action_boundary",
            )
        )
        return log

    def _apply_mornye_same_action_high_syntony_field(self, action: ActionData) -> dict[str, Any]:
        effects = action.mechanic_effects or {}
        actor_character_id = str(effects.get("transition_actor_character_id") or action.character_id or "")
        if actor_character_id != "mornye" or action.id != "mornye_liberation_critical_protocol":
            return {}
        if not effects.get("upgrade_syntony_to_high"):
            return {}

        data = self.state.character_mechanics_state.setdefault("mornye", {})
        syntony_remaining = float(data.get("syntony_field_remaining", 0.0) or 0.0)
        if syntony_remaining <= 0.0:
            return {
                "mornye_constellation": self._mornye_constellation(),
                "mornye_heal_event_mode": self._mornye_heal_event_mode(),
                "high_syntony_field_active": False,
                "high_syntony_field_remaining": 0.0,
                "high_syntony_field_unavailable_reason": "requires_active_syntony_field",
            }

        duration = float(effects.get("high_syntony_field_duration", 25.0) or 25.0)
        data["syntony_field_remaining"] = 0.0
        data["high_syntony_field_remaining"] = duration
        data["high_syntony_field_source_action_id"] = action.id
        data["high_syntony_field_created_count"] = int(data.get("high_syntony_field_created_count", 0) or 0) + 1
        cancelled_effect_ids = self._cancel_mornye_normal_syntony_deployment_damage()
        cancelled_heal_ids = self._cancel_mornye_normal_syntony_healing()

        window = {
            "field_id": "high_syntony_field",
            "source_action_id": action.id,
            "character_id": "mornye",
            "start_time": self.state.combat_time,
            "end_time": self.state.combat_time + duration,
            "duration": duration,
            "implementation_timing_mode": HIGH_SYNTONY_SAME_ACTION_TIMING_MODE,
        }
        self.state.high_syntony_field_buff_windows.append(window)
        data.setdefault("high_syntony_field_buff_windows", []).append(dict(window))

        log_updates = apply_high_syntony_field_support_buffs(
            state=self.state,
            buffs=self.buffs,
            source_character_id="mornye",
            duration=duration,
            constellation=self._mornye_constellation(),
            application_time=self.state.combat_time,
        )
        high_syntony_log_fields = {
            "mornye_constellation": self._mornye_constellation(),
            "mornye_heal_event_mode": self._mornye_heal_event_mode(),
            "high_syntony_field_active": True,
            "high_syntony_field_remaining": duration,
            "high_syntony_field_def_bonus_active": True,
            "high_syntony_field_def_percent_bonus": 0.20,
            "high_syntony_field_off_tune_inherited": True,
            "high_syntony_field_healing_multiplier_bonus": 0.40,
            "high_syntony_field_healing_multiplier_metadata_only": True,
            "high_syntony_field_source_action_id": action.id,
            "high_syntony_field_created_count": int(data.get("high_syntony_field_created_count", 0) or 0),
            "critical_protocol_high_syntony_created_before_damage": True,
            "high_syntony_field_same_action_application": True,
            "high_syntony_field_application_timing": HIGH_SYNTONY_SAME_ACTION_TIMING_MODE,
            "high_syntony_field_unavailable_reason": None,
            "normal_syntony_field_deployment_damage_cancelled": bool(cancelled_effect_ids),
            "normal_syntony_field_deployment_damage_cancelled_instance_ids": cancelled_effect_ids,
            "normal_syntony_field_healing_cancelled": bool(cancelled_heal_ids),
            "normal_syntony_field_healing_cancelled_instance_ids": cancelled_heal_ids,
            "high_syntony_field_deployment_damage_scheduled": False,
            "halo_atk_buff_does_not_affect_mornye_def_damage": True,
        }
        log_updates.update(high_syntony_log_fields)

        if self._mornye_heal_event_mode() == "scheduled_180f_exact":
            heal_schedule = self._schedule_mornye_high_syntony_field_healing(action, self.state.combat_time)
            log_updates.update(heal_schedule)
            log_updates["high_syntony_field_heal_proxy_active"] = False
            return log_updates

        mode = self._mornye_heal_event_mode()
        if mode == "disabled":
            log_updates.update(
                {
                    "high_syntony_field_heal_proxy_active": False,
                    "halo_of_starry_radiance_5set_unavailable_reason": "mornye_heal_event_mode_disabled",
                }
            )
            return log_updates

        if mode in {"field_creation_only", "simplified_syntony_field_uptime"}:
            halo_log = apply_mornye_halo_of_starry_radiance_5set_event_buff(
                source_character_id="mornye",
                emitted_event_tags=[TEAM_HEAL_EVENT_TAG],
                characters=self.characters,
                state=self.state,
                buffs=self.buffs,
                application_time=self.state.combat_time,
                event_source=(
                    "high_syntony_field_creation_only"
                    if mode == "field_creation_only"
                    else "simplified_high_syntony_field_creation_proxy"
                ),
                applied_before_field_creation_damage=True,
            )
            halo_log.update(
                self._apply_team_heal_weapon_effects(
                    halo_log,
                    source_character_id="mornye",
                    application_time=self.state.combat_time,
                    event_source=(
                        "high_syntony_field_creation_only"
                        if mode == "field_creation_only"
                        else "simplified_high_syntony_field_creation_proxy"
                    ),
                )
            )
            log_updates.update(halo_log)
            log_updates.update(high_syntony_log_fields)
            log_updates["high_syntony_field_heal_proxy_active"] = True
        return log_updates

    def _cancel_mornye_normal_syntony_deployment_damage(self) -> list[str]:
        cancelled: list[str] = []
        for instance_id in (
            self.MORNYE_SYNTONY_FIELD_DAMAGE_1_INSTANCE_ID,
            self.MORNYE_SYNTONY_FIELD_DAMAGE_2_INSTANCE_ID,
        ):
            removed = self.remove_scheduled_effect(instance_id)
            if removed is not None:
                cancelled.append(instance_id)
        return cancelled

    def _cancel_mornye_normal_syntony_healing(self) -> list[str]:
        removed = self.remove_scheduled_effect(self.MORNYE_SYNTONY_FIELD_HEAL_INSTANCE_ID)
        return [self.MORNYE_SYNTONY_FIELD_HEAL_INSTANCE_ID] if removed is not None else []

    def _schedule_mornye_normal_syntony_field_healing(
        self,
        action: ActionData,
        activation_time: float,
        activation_timing_status: str,
    ) -> dict[str, Any]:
        if self._mornye_heal_event_mode() != "scheduled_180f_exact":
            return {}
        self.remove_scheduled_effect(self.MORNYE_HIGH_SYNTONY_FIELD_HEAL_INSTANCE_ID)
        result = self.schedule_effect(
            instance_id=self.MORNYE_SYNTONY_FIELD_HEAL_INSTANCE_ID,
            effect_id="mornye_syntony_field_heal",
            source_character_id="mornye",
            source_action_id=action.id,
            payload_action_id=self.MORNYE_SYNTONY_FIELD_HEAL_ACTION_ID,
            activation_combat_time=activation_time,
            remaining_duration=1500.0 / 60.0,
            tick_interval=180.0 / 60.0,
            time_until_next_tick=1.0 / 60.0,
            max_trigger_count=9,
            refresh_rule="replace",
            payload_event_type="healing",
            scheduled_resource_policy="none",
            source_status="workbook_confirmed_scheduled_heal",
            source_ref="角色-女!4120 / 角色技能类型!533",
            metadata={
                "field_id": "normal_syntony_field",
                "activation_timing_status": activation_timing_status,
                "relative_tick_frames": [1, 181, 361, 541, 721, 901, 1081, 1261, 1441],
                "base_heal": 1805.0,
                "scaling_stat": "def",
                "scaling_multiplier": 0.945,
                "field_healing_multiplier": 1.0,
                "target_scope": "host_action_actor_else_active_character",
                "healing_bonus_applied": 0.0,
                "healing_bonus_source_status": "metadata_only_not_applied",
            },
        )
        return {
            "mornye_syntony_field_healing_scheduled": True,
            "mornye_syntony_field_healing_schedule_operation": result.get("operation"),
            "mornye_syntony_field_healing_implementation_status": "scheduled_180f_exact",
            "mornye_syntony_field_healing_relative_tick_frames": [1, 181, 361, 541, 721, 901, 1081, 1261, 1441],
        }

    def _schedule_mornye_high_syntony_field_healing(self, action: ActionData, activation_time: float) -> dict[str, Any]:
        result = self.schedule_effect(
            instance_id=self.MORNYE_HIGH_SYNTONY_FIELD_HEAL_INSTANCE_ID,
            effect_id="mornye_high_syntony_field_heal",
            source_character_id="mornye",
            source_action_id=action.id,
            payload_action_id=self.MORNYE_HIGH_SYNTONY_FIELD_HEAL_ACTION_ID,
            activation_combat_time=activation_time,
            remaining_duration=1500.0 / 60.0,
            tick_interval=180.0 / 60.0,
            time_until_next_tick=1.0 / 60.0,
            max_trigger_count=9,
            refresh_rule="replace",
            payload_event_type="healing",
            scheduled_resource_policy="none",
            source_status="workbook_confirmed_scheduled_heal",
            source_ref="角色-女!4121 / 角色技能类型!533",
            metadata={
                "field_id": "high_syntony_field",
                "relative_tick_frames": [1, 181, 361, 541, 721, 901, 1081, 1261, 1441],
                "base_heal": 1805.0,
                "scaling_stat": "def",
                "scaling_multiplier": 0.945,
                "field_healing_multiplier": 1.4,
                "target_scope": "host_action_actor_else_active_character",
                "healing_bonus_applied": 0.0,
                "healing_bonus_source_status": "metadata_only_not_applied",
                "c4_healing_bonus_status": "excluded_c0_task",
            },
        )
        return {
            "mornye_high_syntony_field_healing_scheduled": True,
            "mornye_high_syntony_field_healing_schedule_operation": result.get("operation"),
            "mornye_high_syntony_field_healing_implementation_status": "scheduled_180f_exact",
            "mornye_high_syntony_field_healing_relative_tick_frames": [1, 181, 361, 541, 721, 901, 1081, 1261, 1441],
            "high_syntony_field_healing_multiplier_metadata_only": False,
        }

    def _lynae_spray_paint_snapshot_metadata(self) -> dict[str, Any]:
        lynae_state = self.state.character_mechanics_state.setdefault("lynae", {})
        mode = str(lynae_state.get("lynae_resonance_mode", "tune_rupture") or "tune_rupture")
        if mode == "tune_strain":
            shift_state = "tune_strain_shifting"
            source_row = "角色-女!2683"
        elif mode == "tune_rupture":
            shift_state = "tune_rupture_shifting"
            source_row = "角色-女!2684"
        else:
            raise ValueError(f"Unsupported Lynae Spray Paint resonance mode snapshot {mode!r}")
        return {
            "paint_mode_snapshot": mode,
            "target_shift_state_snapshot": shift_state,
            "source_row": source_row,
            "source_ref": source_row,
            "source_status": "workbook_confirmed_scheduled_status_application",
            "scheduled_status_effect_id": "lynae_photocromic_flux",
            "effect_duration": 25.0,
            "target_scope": "current_single_enemy",
            "mode_source": "scheduled_effect_metadata_snapshot",
            "target_presence_assumption": "single_target_remains_inside_paint_area",
            "activation_timing_status": [
                "source_confirmed_field_generation",
                "activation_timing_approximation_action_end",
            ],
            "first_check_frames": 1,
            "check_interval_frames": 120,
            "field_duration_frames": 300,
            "relative_application_frames": [1, 121, 241],
            "max_application_count": 3,
            "remove_on_max_trigger_count": False,
            "zero_damage_resources_off_tune": True,
            "c1_rows_excluded": ["角色-女!2685", "角色-女!2686", "角色-女!2687", "角色-女!2688"],
        }

    def _schedule_lynae_spray_paint_status_field(self, action: ActionData, result: Any) -> dict[str, Any]:
        if action.id != "lynae_visual_impact" or "lynae" not in self.characters:
            return {}
        metadata = self._lynae_spray_paint_snapshot_metadata()
        lynae_character = self.characters.get("lynae")
        lynae_sequence = int(getattr(lynae_character, "sequence", 0) or 0)
        account_sequence_active = bool(self.account_simulation_scope) and bool(
            getattr(lynae_character, "account_profile", False)
        ) and lynae_sequence >= 1
        field_duration_frames = 600 if account_sequence_active else 300
        relative_application_frames = (
            [1, 121, 241, 361, 481] if account_sequence_active else [1, 121, 241]
        )
        max_application_count = len(relative_application_frames)
        field_duration_seconds = field_duration_frames / 60.0
        metadata.update(
            {
                "field_duration_frames": field_duration_frames,
                "relative_application_frames": relative_application_frames,
                "max_application_count": max_application_count,
                "sequence_extension_applied": account_sequence_active,
                "pull_diagnostic_frames": [360] if account_sequence_active else [],
                "movement_effect_value": 0.0,
            }
        )
        schedule_result = self.schedule_effect(
            instance_id=self.LYNAE_SPRAY_PAINT_INSTANCE_ID,
            effect_id="lynae_spray_paint",
            source_character_id="lynae",
            source_action_id="lynae_visual_impact",
            payload_action_id=self.LYNAE_SPRAY_PAINT_PAYLOAD_ACTION_ID,
            activation_combat_time=float(result.combat_time_end),
            remaining_duration=field_duration_seconds,
            tick_interval=120.0 / 60.0,
            time_until_next_tick=1.0 / 60.0,
            max_trigger_count=max_application_count,
            trigger_on_apply=False,
            refresh_rule="replace",
            payload_event_type="status_application",
            scheduled_resource_policy="none",
            source_status="workbook_confirmed_scheduled_status_application",
            source_ref=metadata["source_ref"],
            metadata=metadata,
        )
        lynae_state = self.state.character_mechanics_state.setdefault("lynae", {})
        lynae_state["spray_paint_window_remaining"] = field_duration_seconds
        result.lynae_spray_paint_window_remaining = field_duration_seconds
        result.lynae_spray_paint_scheduled = True
        result.lynae_spray_paint_schedule_operation = schedule_result.get("operation")
        result.lynae_spray_paint_mode_snapshot = metadata["paint_mode_snapshot"]
        result.lynae_spray_paint_target_shift_state_snapshot = metadata["target_shift_state_snapshot"]
        result.lynae_spray_paint_source_ref = metadata["source_ref"]
        return dict(schedule_result)

    def _sync_lynae_spray_paint_window_mirror(self, result: Any | None = None) -> None:
        lynae_state = self.state.character_mechanics_state.get("lynae")
        if lynae_state is None:
            return
        effect = self.scheduled_effect_by_instance_id(self.LYNAE_SPRAY_PAINT_INSTANCE_ID)
        remaining = float(effect.remaining_duration) if effect is not None else 0.0
        lynae_state["spray_paint_window_remaining"] = max(0.0, remaining)
        if result is not None:
            result.lynae_spray_paint_window_remaining = lynae_state["spray_paint_window_remaining"]

    def _schedule_mornye_syntony_field_deployment_damage(self, action: ActionData) -> dict[str, Any]:
        effects = action.mechanic_effects or {}
        actor_character_id = str(effects.get("transition_actor_character_id") or action.character_id or "")
        if actor_character_id != "mornye" or "mornye" not in self.characters:
            return {}
        if action.id == "mornye_heavy_geopotential_shift":
            activation_time = float(self.state.combat_time) + 48.0 / 60.0
            schedule_damage_2 = True
            activation_timing_status = "source_confirmed_frame_48"
            timing_note = "Wide Field Observation is obtained at action frame 48."
        elif action.id == "transition:mornye_intro_convergence":
            activation_time = float(self.state.combat_time) + action.effective_combat_time_cost
            schedule_damage_2 = False
            activation_timing_status = "source_confirmed_creation;activation_timing_approximation_action_end"
            timing_note = "Intro creates Syntony Field, but supplied frame rows do not isolate field creation; use transition combat end."
        else:
            return {}

        common_metadata = {
            "field_id": "normal_syntony_field",
            "field_duration": 25.0,
            "activation_timing_status": activation_timing_status,
            "activation_timing_note": timing_note,
            "healing_implementation_status": "scheduled_180f_exact"
            if self._mornye_heal_event_mode() == "scheduled_180f_exact"
            else "simplified_action_boundary_proxy_unchanged",
        }
        heal_schedule = self._schedule_mornye_normal_syntony_field_healing(
            action,
            activation_time,
            activation_timing_status,
        )
        damage_1 = self.schedule_effect(
            instance_id=self.MORNYE_SYNTONY_FIELD_DAMAGE_1_INSTANCE_ID,
            effect_id="mornye_syntony_field_damage_1",
            source_character_id="mornye",
            source_action_id=action.id,
            payload_action_id=self.MORNYE_SYNTONY_FIELD_DAMAGE_1_ACTION_ID,
            activation_combat_time=activation_time,
            remaining_duration=120.0 / 60.0,
            tick_interval=27.0 / 60.0,
            time_until_next_tick=1.0 / 60.0,
            max_trigger_count=5,
            refresh_rule="replace",
            scheduled_resource_policy="none",
            source_status="workbook_confirmed_scheduled_tick",
            source_ref=self.MORNYE_SYNTONY_FIELD_DAMAGE_1_SOURCE_REF,
            metadata={
                **common_metadata,
                "relative_tick_frames": [1, 28, 55, 82, 109],
                "qte_allowed": True,
                "scheduled_resource_policy": "none",
            },
        )
        damage_2 = None
        if schedule_damage_2:
            damage_2 = self.schedule_effect(
                instance_id=self.MORNYE_SYNTONY_FIELD_DAMAGE_2_INSTANCE_ID,
                effect_id="mornye_syntony_field_damage_2",
                source_character_id="mornye",
                source_action_id=action.id,
                payload_action_id=self.MORNYE_SYNTONY_FIELD_DAMAGE_2_ACTION_ID,
                activation_combat_time=activation_time,
                remaining_duration=23.0 / 60.0,
                tick_interval=23.0 / 60.0,
                time_until_next_tick=23.0 / 60.0,
                max_trigger_count=1,
                refresh_rule="replace",
                scheduled_resource_policy="source_confirmed_positive_gains",
                source_status="workbook_confirmed_scheduled_target_damage",
                source_ref=self.MORNYE_SYNTONY_FIELD_DAMAGE_2_SOURCE_REF,
                metadata={
                    **common_metadata,
                    "relative_tick_frames": [23],
                    "qte_allowed": False,
                    "qte_restriction_source": self.MORNYE_SYNTONY_FIELD_DAMAGE_2_ACTION_REF,
                    "scheduled_resource_policy": "source_confirmed_positive_gains",
                },
            )

        return {
            "mornye_syntony_field_deployment_damage_scheduled": True,
            "mornye_syntony_field_activation_combat_time": activation_time,
            "mornye_syntony_field_activation_timing_status": activation_timing_status,
            "mornye_syntony_field_damage_1_schedule_operation": damage_1.get("operation"),
            "mornye_syntony_field_damage_2_schedule_operation": damage_2.get("operation") if damage_2 else None,
            "mornye_syntony_field_damage_2_qte_restricted": not schedule_damage_2,
            "mornye_syntony_field_damage_1_relative_tick_frames": [1, 28, 55, 82, 109],
            "mornye_syntony_field_damage_2_relative_tick_frames": [23] if schedule_damage_2 else [],
            "mornye_syntony_field_healing_implementation_status": common_metadata["healing_implementation_status"],
            **heal_schedule,
        }

    def _apply_mornye_same_action_field_creation_halo(self, action: ActionData) -> dict[str, Any]:
        effects = action.mechanic_effects or {}
        actor_character_id = str(effects.get("transition_actor_character_id") or action.character_id or "")
        if actor_character_id != "mornye" or "mornye" not in self.characters:
            return {}
        if not self._action_deals_damage(action):
            return {}
        mode = self._mornye_heal_event_mode()
        if mode == "scheduled_180f_exact":
            log_updates: dict[str, Any] = {
                "mornye_heal_event_mode": mode,
                "halo_of_starry_radiance_5set_unavailable_reason": "scheduled_heal_pending_first_1f_tick",
                "mornye_syntony_field_proxy_heal_suppressed": True,
            }
            syntony_duration = effects.get("syntony_field_duration", effects.get("set_syntony_field_remaining"))
            if syntony_duration is not None:
                log_updates.update(
                    apply_syntony_field_off_tune_buff(
                        state=self.state,
                        source_character_id="mornye",
                        duration=float(syntony_duration),
                        constellation=self._mornye_constellation(),
                        application_time=self.state.combat_time,
                    )
                )
            return log_updates
        if mode not in {"field_creation_only", "simplified_syntony_field_uptime"}:
            return {
                "mornye_heal_event_mode": mode,
                "halo_of_starry_radiance_5set_unavailable_reason": "mornye_heal_event_mode_disabled",
            }
        heal_mode_support = set(str(item) for item in effects.get("heal_event_mode_support", []))
        if heal_mode_support and mode not in heal_mode_support:
            return {}
        if not halo_of_starry_radiance_enabled(self.characters.get("mornye")):
            log_updates = {
                "mornye_heal_event_mode": mode,
                "team_heal_event_triggered": True,
                "halo_of_starry_radiance_5set_unavailable_reason": "mornye_halo_5set_not_enabled",
            }
            log_updates.update(
                self._apply_team_heal_weapon_effects(
                    log_updates,
                    source_character_id="mornye",
                    application_time=self.state.combat_time,
                    event_source="field_creation_halo_disabled_team_heal",
                )
            )
            return log_updates

        syntony_duration = effects.get("syntony_field_duration", effects.get("set_syntony_field_remaining"))
        emits_team_heal_proxy = syntony_duration is not None
        if not emits_team_heal_proxy:
            return {}

        log_updates: dict[str, Any] = {
            "mornye_constellation": self._mornye_constellation(),
            "mornye_heal_event_mode": mode,
        }
        if syntony_duration is not None:
            log_updates.update(
                apply_syntony_field_off_tune_buff(
                    state=self.state,
                    source_character_id="mornye",
                    duration=float(syntony_duration),
                    constellation=self._mornye_constellation(),
                    application_time=self.state.combat_time,
                )
            )
        log_updates.update(
            apply_mornye_halo_of_starry_radiance_5set_event_buff(
                source_character_id="mornye",
                emitted_event_tags=[TEAM_HEAL_EVENT_TAG],
                characters=self.characters,
                state=self.state,
                buffs=self.buffs,
                application_time=self.state.combat_time,
                event_source=(
                    "field_creation_only"
                    if mode == "field_creation_only"
                    else "simplified_syntony_field_creation_proxy"
                ),
                applied_before_field_creation_damage=True,
            )
        )
        log_updates.update(
            self._apply_team_heal_weapon_effects(
                log_updates,
                source_character_id="mornye",
                application_time=self.state.combat_time,
                event_source=(
                    "field_creation_only"
                    if mode == "field_creation_only"
                    else "simplified_syntony_field_creation_proxy"
                ),
            )
        )
        return log_updates

    def _action_deals_damage(self, action: ActionData) -> bool:
        for hit in action.effective_hits():
            if hit.damage_category == "normal" and hit.damage_multiplier > 0.0:
                return True
            if hit.damage_category == "tune_break" and hit.tune_break_multiplier > 0.0:
                return True
        return False

    def _apply_mornye_post_action_support_events(self, action: ActionData, result) -> None:
        if action.character_id != "mornye" and (action.mechanic_effects or {}).get("transition_actor_character_id") != "mornye":
            return
        effects = action.mechanic_effects or {}
        mode = self._mornye_heal_event_mode()
        same_action_halo_applied = bool(result.halo_of_starry_radiance_5set_same_action_application)
        log_updates: dict[str, Any] = {
            "mornye_constellation": self._mornye_constellation(),
            "mornye_heal_event_mode": mode,
        }
        syntony_duration = effects.get("syntony_field_duration", effects.get("set_syntony_field_remaining"))
        same_action_syntony_off_tune_applied = bool(
            getattr(result, "syntony_field_off_tune_bonus_active", False)
            and getattr(result, "syntony_field_off_tune_bonus_application_time", None) == result.combat_time_start
        )
        if syntony_duration is not None and not same_action_halo_applied and not same_action_syntony_off_tune_applied:
            syntony_log = apply_syntony_field_off_tune_buff(
                state=self.state,
                source_character_id="mornye",
                duration=float(syntony_duration),
                constellation=self._mornye_constellation(),
                application_time=result.combat_time_end,
            )
            log_updates.update(syntony_log)
        high_syntony_heal_metadata = bool(effects.get("upgrade_syntony_to_high") or effects.get("high_syntony_field_duration"))
        emits_creation_heal = (
            mode in {"field_creation_only", "simplified_syntony_field_uptime"}
            and syntony_duration is not None
        )
        if mode == "scheduled_180f_exact":
            emits_creation_heal = False
        if mode == "disabled":
            log_updates["halo_of_starry_radiance_5set_unavailable_reason"] = "mornye_heal_event_mode_disabled"
        elif emits_creation_heal and not same_action_halo_applied:
            halo_log = apply_mornye_halo_of_starry_radiance_5set_event_buff(
                source_character_id="mornye",
                emitted_event_tags=[TEAM_HEAL_EVENT_TAG],
                characters=self.characters,
                state=self.state,
                buffs=self.buffs,
                application_time=result.combat_time_end,
                event_source="field_creation_only" if mode == "field_creation_only" else "simplified_syntony_field_creation_proxy",
            )
            halo_log.update(
                self._apply_team_heal_weapon_effects(
                    halo_log,
                    source_character_id="mornye",
                    application_time=result.combat_time_end,
                    event_source=(
                        "field_creation_only"
                        if mode == "field_creation_only"
                        else "simplified_syntony_field_creation_proxy"
                    ),
                )
            )
            log_updates.update(halo_log)
        if high_syntony_heal_metadata:
            log_updates["high_syntony_field_healing_multiplier_bonus"] = 0.40
            log_updates["high_syntony_field_healing_multiplier_metadata_only"] = True

        active_buff_ids = [buff.buff_id for buff in self.state.active_buffs if buff.remaining_duration > 0.0]
        result.active_buffs = active_buff_ids
        result.applied_buffs = list(dict.fromkeys([*result.applied_buffs, *log_updates.get("echo_set_triggered_buff_ids", [])]))
        for key, value in log_updates.items():
            if hasattr(result, key):
                setattr(result, key, value)
        result.halo_of_starry_radiance_5set_active = (
            bool(result.halo_of_starry_radiance_5set_same_action_application)
            or MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID in active_buff_ids
        )
        if self.state.action_log:
            self.state.action_log[-1].update(result.model_dump(mode="json"))
        if self.state.damage_log and self.state.damage_log[-1].get("action_id") == action.id:
            self.state.damage_log[-1].update(log_updates)

    def _apply_team_heal_weapon_effects(
        self,
        event_log: dict[str, Any],
        *,
        source_character_id: str,
        application_time: float,
        event_source: str,
    ) -> dict[str, Any]:
        if not event_log.get("team_heal_event_triggered", False):
            return {}
        return apply_weapon_buff_effects(
            trigger=TEAM_HEAL_EVENT_TAG,
            source_character_id=source_character_id,
            state=self.state,
            characters=self.characters,
            buffs=self.buffs,
            weapon_definitions=self.weapon_definitions,
            application_time=application_time,
            event_source=event_source,
        )

    def _sync_weapon_result_fields(self, result, log_updates: dict[str, Any] | None = None) -> None:
        log = log_updates or {}
        result.weapon_effects_enabled = bool(
            result.weapon_effects_enabled or self.weapon_effects_enabled or log.get("weapon_effects_enabled", False)
        )
        result.weapon_effect_triggered = bool(result.weapon_effect_triggered or log.get("weapon_effect_triggered", False))
        result.weapon_effect_cooldown_blocked = bool(
            result.weapon_effect_cooldown_blocked or log.get("weapon_effect_cooldown_blocked", False)
        )
        if log.get("weapon_effect_logs"):
            result.weapon_effect_logs = [*result.weapon_effect_logs, *list(log.get("weapon_effect_logs") or [])]
        for field in (
            "weapon_id",
            "weapon_rank",
            "weapon_effect_id",
            "weapon_effect_type",
            "weapon_effect_resource",
            "weapon_effect_source_status",
            "concerto_energy_before_weapon_effect",
            "concerto_energy_restored_by_weapon",
            "concerto_energy_after_weapon_effect",
            "concerto_energy_wasted_by_weapon",
            "weapon_effect_cooldown_seconds",
            "weapon_effect_cooldown_remaining",
            "weapon_effect_buff_refreshed",
            "weapon_effect_duration_seconds",
            "starfield_calibrator_party_crit_damage_active",
            "starfield_calibrator_party_crit_damage_bonus",
        ):
            if field in log:
                value = log[field]
                if value in (None, "", [], {}) and getattr(result, field, None) not in (None, "", [], {}):
                    continue
                if isinstance(value, (int, float)) and value == 0 and getattr(result, field, None) not in (0, 0.0, None):
                    continue
                setattr(result, field, value)
        result.weapon_effect_trigger_counts = dict(self.state.weapon_effect_trigger_counts)
        result.weapon_effect_cooldown_blocked_counts = dict(self.state.weapon_effect_cooldown_blocked_counts)
        result.starfield_calibrator_concerto_restore_trigger_count = sum(
            count
            for key, count in self.state.weapon_effect_trigger_counts.items()
            if ":starfield_calibrator:resonance_skill_concerto_restore" in key
        )
        result.starfield_calibrator_party_crit_damage_trigger_count = sum(
            count
            for key, count in self.state.weapon_effect_trigger_counts.items()
            if ":starfield_calibrator:heal_party_crit_damage_buff" in key
        )
        result.active_buffs = [buff.buff_id for buff in self.state.active_buffs if buff.remaining_duration > 0.0]

    def _mechanic_for_character(self, character_id: str) -> CharacterMechanic:
        mechanic = self.character_mechanics.get(character_id)
        if mechanic is None:
            mechanic = get_mechanic(character_id)
            mechanic.initialize_state(self.state)
            self.character_mechanics[character_id] = mechanic
        return mechanic

    def summary(self) -> SimulationSummary:
        active_character = self.characters[self.state.active_character_id].name
        mechanic_event_metadata = mechanic_event_metadata_for_config(self.state.mechanics_config)
        mechanic_modes = mechanics_mode_summary({"mechanics": self.state.mechanics_config})
        resources = {
            char_id: {
                "resonance_energy": self.state.resonance_energy.get(char_id, 0.0),
                "resonance_energy_max": self.characters[char_id].resonance_energy_max,
                "wasted_resonance_energy": self.state.wasted_resonance_energy.get(char_id, 0.0),
                "concerto_energy": self.state.concerto_energy.get(char_id, 0.0),
                "concerto_energy_cap": self.state.character_states.get(char_id, {}).get("concerto_energy_cap", 100.0),
                "concerto_ready": bool(self.state.character_states.get(char_id, {}).get("concerto_ready", False)),
                "wasted_concerto_energy": self.state.wasted_concerto_energy.get(char_id, 0.0),
            }
            for char_id in self.characters
        }
        damage_by_selected_action: Counter[str] = Counter()
        damage_by_resolved_action: Counter[str] = Counter()
        damage_by_action_type: Counter[str] = Counter()
        damage_by_damage_bonus_category: Counter[str] = Counter()
        for row in self.timeline:
            damage = float(row.total_action_damage)
            damage_by_selected_action[row.selected_action_id or row.action_id] += damage
            damage_by_resolved_action[row.resolved_action_id or row.action_id] += damage
            damage_by_action_type[row.action_type or "other"] += damage
            damage_by_damage_bonus_category[row.damage_bonus_category or row.damage_category or "other"] += damage
        aemeath_character = self.characters.get("aemeath")
        trailblazing_config = trailblazing_star_config(aemeath_character)
        trailblazing_windows = [
            dict(window)
            for window in self.state.echo_set_buff_windows
            if window.get("buff_id") == AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID
        ]
        mornye_character = self.characters.get("mornye")
        halo_config = halo_of_starry_radiance_config(mornye_character)
        active_halo = next(
            (
                buff
                for buff in self.state.active_buffs
                if buff.buff_id == MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID and buff.remaining_duration > 0.0
            ),
            None,
        )
        mornye_state = self.state.character_mechanics_state.get("mornye", {})
        syntony_active = float(mornye_state.get("syntony_field_remaining", 0.0) or 0.0) > 0.0
        high_syntony_remaining = float(mornye_state.get("high_syntony_field_remaining", 0.0) or 0.0)
        high_syntony_active = high_syntony_remaining > 0.0
        base_off_tune = 1.0
        runtime_off_tune_bonus = 0.0
        current_off_tune = 1.0
        base_tune_break_boost = 0.0
        runtime_tune_break_boost_bonus = 0.0
        current_tune_break_boost = 0.0
        c2_active = False
        syntony_bonus_value = 0.0
        lynae_character = self.characters.get("lynae")
        if lynae_character is not None:
            lynae_support_context = support_stat_context(lynae_character, self.state, self.buffs)
            base_tune_break_boost = float(lynae_support_context["base_tune_break_boost_points"])
            runtime_tune_break_boost_bonus = float(lynae_support_context["runtime_tune_break_boost_points_bonus"])
            current_tune_break_boost = float(lynae_support_context["current_tune_break_boost_points"])
        if mornye_character is not None:
            support_context = support_stat_context(mornye_character, self.state, self.buffs)
            base_off_tune = float(support_context["base_off_tune_buildup_rate"])
            runtime_off_tune_bonus = float(support_context["runtime_off_tune_buildup_rate_bonus"])
            current_off_tune = float(support_context["current_off_tune_buildup_rate"])
            c2_active = bool(support_context["c2_off_tune_bonus_active"])
            syntony_bonus_value = float(support_context["syntony_field_off_tune_bonus_value"])
            from simulator.buff_system import buffed_combat_stats

            mornye_runtime_stats = buffed_combat_stats(mornye_character, self.state, self.buffs)
            high_syntony_def_active = bool(mornye_runtime_stats.get("high_syntony_field_def_bonus_active", False))
            high_syntony_def_percent = float(mornye_runtime_stats.get("high_syntony_field_def_percent_bonus", 0.0))
            runtime_def_percent_bonus = float(mornye_runtime_stats.get("runtime_def_percent_bonus", 0.0))
        else:
            high_syntony_def_active = False
            high_syntony_def_percent = 0.0
            runtime_def_percent_bonus = 0.0
        halo_unavailable_reason = None
        if mornye_character is not None and halo_of_starry_radiance_enabled(mornye_character):
            if self.state.mechanic_event_emitted_counts.get(TEAM_HEAL_EVENT_TAG, 0) <= 0:
                halo_unavailable_reason = "no_team_heal_event_occurred"
        elif mornye_character is not None:
            halo_unavailable_reason = "mornye_halo_5set_not_enabled"
        active_weapons = active_weapons_for_characters(self.characters)
        starfield_concerto_key = ":starfield_calibrator:resonance_skill_concerto_restore"
        starfield_crit_key = ":starfield_calibrator:heal_party_crit_damage_buff"
        starfield_crit_buff = next(
            (
                buff
                for buff in self.state.active_buffs
                if buff.buff_id == STARFIELD_CALIBRATOR_BUFF_ID and buff.remaining_duration > 0.0
            ),
            None,
        )
        everbright_weapon = (active_weapons.get("aemeath") or {})
        everbright_equipped = everbright_weapon.get("weapon_id") == "everbright_polestar"
        everbright_rank = min(5, max(1, int(everbright_weapon.get("rank", 1) or 1))) if everbright_equipped else 0
        everbright_values = (
            ((self.weapon_definitions.get("weapons") or {}).get("everbright_polestar") or {})
            .get("rank_values", {})
            .get(str(everbright_rank), {})
            if everbright_equipped
            else {}
        )
        everbright_penetration_buff = next(
            (
                buff
                for buff in self.state.active_buffs
                if buff.buff_id == "everbright_polestar_liberation_penetration" and buff.remaining_duration > 0.0
            ),
            None,
        )
        everbright_windows = [
            dict(window)
            for window in self.state.weapon_effect_buff_windows
            if window.get("buff_id") == "everbright_polestar_liberation_penetration"
        ]

        return SimulationSummary(
            total_damage=self.state.total_damage,
            dps=self.state.total_damage / self.combat_duration,
            final_time=self.state.combat_time,
            final_action_time=self.state.current_time,
            active_character=active_character,
            selected_party_id=self.party_preset_config.get("party_id"),
            active_party_build_profiles=dict(self.active_build_profiles),
            timeline=self.timeline,
            resources=resources,
            damage_by_selected_action=dict(damage_by_selected_action),
            damage_by_resolved_action=dict(damage_by_resolved_action),
            damage_by_action_type=dict(damage_by_action_type),
            damage_by_damage_bonus_category=dict(damage_by_damage_bonus_category),
            enemy_off_tune_current=self.state.enemy_off_tune_current,
            enemy_off_tune_max=self.state.enemy_off_tune_max,
            enemy_mistune_active=self.state.enemy_mistune_active,
            enemy_tune_break_available=self.state.enemy_tune_break_available,
            enemy_tune_break_cooldown_seconds=self.state.enemy_tune_break_cooldown_seconds,
            enemy_tune_break_cooldown_source_status=self.state.enemy_tune_break_cooldown_source_status,
            enemy_tune_break_cooldown_source_ref=self.state.enemy_tune_break_cooldown_source_ref,
            enemy_tune_break_cooldown_remaining=self.state.enemy_tune_break_cooldown_remaining,
            off_tune_accumulated_total=self.state.off_tune_accumulated_total,
            off_tune_overflow=self.state.off_tune_overflow,
            off_tune_accumulation_blocked_by_tune_break_cooldown_count=(
                self.state.off_tune_accumulation_blocked_by_tune_break_cooldown_count
            ),
            off_tune_accumulation_logs=list(self.state.off_tune_accumulation_logs),
            mapped_off_tune_action_count=self.state.mapped_off_tune_action_count,
            unmapped_off_tune_action_ids=list(self.state.unmapped_off_tune_action_ids),
            unresolved_off_tune_damaging_action_ids=list(self.state.unresolved_off_tune_damaging_action_ids),
            off_tune_mapping_completeness_status=self.state.off_tune_mapping_completeness_status,
            off_tune_value_mapping_source_report=self.state.off_tune_value_mapping_source_report,
            tune_break_action_available_ids=self._available_tune_break_action_ids(),
            tune_break_action_used_count=self.state.tune_break_action_used_count,
            tune_break_damage_total=self.state.tune_break_damage_total,
            interfered_marker_direct_damage_amp_bonus_damage_total=(
                self.state.interfered_marker_direct_damage_amp_bonus_damage_total
            ),
            interfered_marker_direct_damage_amp_applied_action_count=(
                self.state.interfered_marker_direct_damage_amp_applied_action_count
            ),
            target_tune_shift_state=self.state.target_tune_shift_state,
            target_interfered_state=self.state.target_interfered_state,
            target_tune_strain_interfered_stacks=self.state.target_tune_strain_interfered_stacks,
            target_tune_strain_interfered_max_stacks=self.state.target_tune_strain_interfered_max_stacks,
            target_tune_strain_interfered_remaining=self.state.target_tune_strain_interfered_remaining,
            lynae_tune_strain_damage_amp=self.state.lynae_tune_strain_damage_amp,
            lynae_tune_strain_damage_multiplier=self.state.lynae_tune_strain_damage_multiplier,
            lynae_tune_strain_damage_amp_bonus_damage=self.state.lynae_tune_strain_damage_amp_bonus_damage,
            lynae_tune_strain_source_status=self.state.lynae_tune_strain_source_status,
            lynae_tune_strain_source_ref=self.state.lynae_tune_strain_source_ref,
            observation_marker_remaining=self._mornye_observation_marker_remaining(),
            interfered_marker_remaining=self.state.interfered_marker_remaining,
            interfered_marker_damage_taken_amp=self.state.interfered_marker_damage_taken_amp,
            party_response_scan_triggered=bool(self.state.party_response_scan_logs),
            aemeath_starburst_trigger_count=self.state.aemeath_starburst_trigger_count,
            mornye_particle_jet_trigger_count=self.state.mornye_particle_jet_trigger_count,
            lynae_spectral_analysis_trigger_count=self.state.lynae_spectral_analysis_trigger_count,
            aemeath_starburst_cooldown_blocked_count=self.state.aemeath_starburst_cooldown_blocked_count,
            mornye_particle_jet_cooldown_blocked_count=self.state.mornye_particle_jet_cooldown_blocked_count,
            lynae_spectral_analysis_cooldown_blocked_count=(
                self.state.lynae_spectral_analysis_cooldown_blocked_count
            ),
            aemeath_starburst_response_cooldown_remaining=(
                self.state.aemeath_starburst_response_cooldown_remaining
            ),
            mornye_particle_jet_response_cooldown_remaining=(
                self.state.mornye_particle_jet_response_cooldown_remaining
            ),
            lynae_spectral_analysis_response_cooldown_remaining=(
                self.state.lynae_spectral_analysis_response_cooldown_remaining
            ),
            tune_response_damage_total=self.state.tune_response_damage_total,
            aemeath_starburst_damage_total=self.state.aemeath_starburst_damage_total,
            mornye_particle_jet_damage_total=self.state.mornye_particle_jet_damage_total,
            lynae_spectral_analysis_damage_total=self.state.lynae_spectral_analysis_damage_total,
            tune_response_events=list(self.state.tune_response_events),
            tune_response_damage_formula_source_status=self.state.tune_response_damage_formula_source_status,
            tune_response_event_order_source_status=self.state.tune_response_event_order_source_status,
            tune_break_damage_receives_new_interfered_marker_amp=(
                self.state.tune_break_damage_receives_new_interfered_marker_amp
            ),
            response_damage_receives_interfered_marker_amp=(
                self.state.response_damage_receives_interfered_marker_amp
            ),
            response_damage_receives_newly_applied_interfered_marker_amp=(
                self.state.response_damage_receives_newly_applied_interfered_marker_amp
            ),
            response_damage_receives_existing_interfered_marker_amp=(
                self.state.response_damage_receives_existing_interfered_marker_amp
            ),
            response_damage_receives_new_interfered_marker_amp=(
                self.state.response_damage_receives_new_interfered_marker_amp
            ),
            unresolved_response_damage_events=list(self.state.unresolved_response_damage_events),
            simplified_assumptions=list(self.state.simplified_assumptions),
            aemeath_resonance_mode=mechanic_event_metadata["aemeath_resonance_mode"],
            aemeath_resonance_mode_source=mechanic_event_metadata["aemeath_resonance_mode_source"],
            mechanic_event_trigger_action_ids=mechanic_event_metadata["mechanic_event_trigger_action_ids"],
            mechanic_event_transition_trigger_action_ids=mechanic_event_metadata[
                "mechanic_event_transition_trigger_action_ids"
            ],
            mechanic_event_emitted_counts=dict(self.state.mechanic_event_emitted_counts),
            fusion_burst_event_count=int(self.state.mechanic_event_emitted_counts.get("fusion_burst", 0)),
            tune_rupture_shifting_event_count=int(
                self.state.mechanic_event_emitted_counts.get("tune_rupture_shifting", 0)
            ),
            mechanic_event_unresolved_reason=mechanic_event_metadata["mechanic_event_unresolved_reason"],
            unsupported_aemeath_followup_mechanics=mechanic_event_metadata["unsupported_aemeath_followup_mechanics"],
            active_echo_sets=active_echo_sets_for_characters(self.characters),
            active_weapons=active_weapons,
            weapon_effects_enabled=self.weapon_effects_enabled,
            weapon_effect_trigger_counts=dict(self.state.weapon_effect_trigger_counts),
            weapon_effect_cooldown_blocked_counts=dict(self.state.weapon_effect_cooldown_blocked_counts),
            weapon_effect_logs=list(self.state.weapon_effect_logs),
            weapon_effect_source_status=next(
                (
                    log.get("weapon_effect_source_status")
                    for log in reversed(self.state.weapon_effect_logs)
                    if log.get("weapon_effect_source_status")
                ),
                None,
            ),
            starfield_calibrator_concerto_restore_trigger_count=sum(
                count for key, count in self.state.weapon_effect_trigger_counts.items() if starfield_concerto_key in key
            ),
            starfield_calibrator_concerto_restored_total=self.state.starfield_calibrator_concerto_restored_total,
            starfield_calibrator_party_crit_damage_trigger_count=sum(
                count for key, count in self.state.weapon_effect_trigger_counts.items() if starfield_crit_key in key
            ),
            starfield_calibrator_party_crit_damage_uptime_seconds=weapon_effect_uptime_seconds(
                self.state,
                STARFIELD_CALIBRATOR_BUFF_ID,
                self.state.combat_time,
            ),
            starfield_calibrator_party_crit_damage_bonus=float(
                (starfield_crit_buff.metadata or {}).get("dynamic_value", 0.0)
                if starfield_crit_buff is not None
                else 0.0
            ),
            everbright_polestar_equipped=everbright_equipped,
            everbright_polestar_rank=everbright_rank,
            everbright_polestar_all_attribute_damage_bonus=float(
                everbright_values.get("all_attribute_damage_bonus", 0.0) or 0.0
            ),
            everbright_polestar_liberation_penetration_trigger_count=sum(
                count
                for key, count in self.state.weapon_effect_trigger_counts.items()
                if ":everbright_polestar:liberation_def_res_ignore_after_tune_event" in key
            ),
            everbright_polestar_liberation_penetration_uptime_seconds=weapon_effect_uptime_seconds(
                self.state,
                "everbright_polestar_liberation_penetration",
                self.state.combat_time,
            ),
            everbright_polestar_def_ignore_bonus=float(
                (everbright_penetration_buff.metadata or {}).get("dynamic_def_ignore", 0.0)
                if everbright_penetration_buff is not None
                else 0.0
            ),
            everbright_polestar_fusion_res_ignore_bonus=float(
                (everbright_penetration_buff.metadata or {}).get("dynamic_fusion_res_ignore", 0.0)
                if everbright_penetration_buff is not None
                else 0.0
            ),
            everbright_polestar_buff_windows=everbright_windows,
            discord_concerto_restore_support_status=(
                "implemented_data_driven"
                if "discord" in ((self.weapon_definitions.get("weapons") or {}).keys())
                else "weapon_definition_missing"
            ),
            echo_set_active_buffs=echo_set_active_buff_ids(self.state, self.buffs),
            aemeath_trailblazing_star_5set_enabled=trailblazing_star_enabled(aemeath_character),
            aemeath_trailblazing_star_5set_trigger_event_tags=list(
                trailblazing_config.get("trigger_event_tags", [])
            ),
            aemeath_trailblazing_star_5set_trigger_count=int(
                self.state.echo_set_trigger_counts.get(AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID, 0)
            ),
            aemeath_trailblazing_star_5set_uptime_seconds=trailblazing_star_uptime_seconds(
                self.state,
                self.state.combat_time,
            ),
            aemeath_trailblazing_star_5set_buff_windows=trailblazing_windows,
            base_off_tune_buildup_rate=base_off_tune,
            runtime_off_tune_buildup_rate_bonus=runtime_off_tune_bonus,
            current_off_tune_buildup_rate=current_off_tune,
            base_tune_break_boost_points=base_tune_break_boost,
            runtime_tune_break_boost_points_bonus=runtime_tune_break_boost_bonus,
            current_tune_break_boost_points=current_tune_break_boost,
            syntony_field_off_tune_bonus_active=syntony_active and syntony_bonus_value > 0.0,
            syntony_field_off_tune_bonus_value=syntony_bonus_value,
            c2_off_tune_bonus_active=c2_active,
            mornye_constellation=self._mornye_constellation(),
            mornye_heal_event_mode=self._mornye_heal_event_mode(),
            mornye_heal_event_mode_source=mechanic_modes["mornye"]["heal_event_mode_source"],
            team_heal_event_count=int(self.state.mechanic_event_emitted_counts.get(TEAM_HEAL_EVENT_TAG, 0)),
            mornye_halo_of_starry_radiance_5set_enabled=halo_of_starry_radiance_enabled(mornye_character),
            mornye_halo_of_starry_radiance_5set_trigger_count=int(
                self.state.echo_set_trigger_counts.get(MORNYE_HALO_OF_STARRY_RADIANCE_5SET_BUFF_ID, 0)
            ),
            mornye_halo_of_starry_radiance_5set_atk_percent_bonus=float(
                (active_halo.metadata or {}).get("dynamic_value", 0.0) if active_halo is not None else 0.0
            ),
            mornye_halo_of_starry_radiance_5set_uptime_seconds=halo_of_starry_radiance_uptime_seconds(
                self.state,
                self.state.combat_time,
            ),
            halo_of_starry_radiance_5set_unavailable_reason=halo_unavailable_reason,
            high_syntony_field_active=high_syntony_active,
            high_syntony_field_remaining=high_syntony_remaining,
            high_syntony_field_created_count=int(mornye_state.get("high_syntony_field_created_count", 0) or 0),
            high_syntony_field_def_bonus_active=high_syntony_def_active,
            high_syntony_field_def_percent_bonus=high_syntony_def_percent,
            high_syntony_field_off_tune_inherited=high_syntony_active and syntony_bonus_value > 0.0,
            high_syntony_field_heal_proxy_active=high_syntony_active and self._mornye_heal_event_mode() == "simplified_syntony_field_uptime",
            high_syntony_field_healing_multiplier_bonus=0.40 if high_syntony_active else 0.0,
            critical_protocol_high_syntony_created_before_damage=any(
                bool(row.critical_protocol_high_syntony_created_before_damage) for row in self.timeline
            ),
            high_syntony_field_same_action_application=any(
                bool(row.high_syntony_field_same_action_application) for row in self.timeline
            ),
            high_syntony_field_application_timing=(
                HIGH_SYNTONY_SAME_ACTION_TIMING_MODE
                if any(bool(row.high_syntony_field_same_action_application) for row in self.timeline)
                else None
            ),
            runtime_def_percent_bonus=runtime_def_percent_bonus,
            halo_of_starry_radiance_5set_active=active_halo is not None,
            halo_of_starry_radiance_5set_atk_percent_bonus=float(
                (active_halo.metadata or {}).get("dynamic_value", 0.0) if active_halo is not None else 0.0
            ),
            halo_atk_buff_does_not_affect_mornye_def_damage=True,
            high_syntony_field_unavailable_reason=next(
                (
                    row.high_syntony_field_unavailable_reason
                    for row in reversed(self.timeline)
                    if row.high_syntony_field_unavailable_reason
                ),
                None,
            ),
        )

    @property
    def party_state(self) -> PartyState:
        return self.get_party_state()

    def get_party_state(self) -> PartyState:
        enemy_state = {
            "enemy_level": float(self.state.enemy_level),
            "enemy_res": self.state.enemy_res,
            "res_pen": self.state.res_pen,
            "def_reduction": self.state.def_reduction,
            "dmg_taken": self.state.dmg_taken,
            "tune_dmg_bonus": self.state.tune_dmg_bonus,
            "enemy_off_tune_current": self.state.enemy_off_tune_current,
            "enemy_off_tune_max": self.state.enemy_off_tune_max,
            "enemy_mistune_active": float(self.state.enemy_mistune_active),
            "enemy_tune_break_available": float(self.state.enemy_tune_break_available),
            "enemy_tune_break_cooldown_remaining": self.state.enemy_tune_break_cooldown_remaining,
        }
        return PartyState(
            party_members=list(self.selected_character_ids),
            active_character_id=self.state.active_character_id,
            character_states=self.state.character_mechanics_state,
            team_buffs=list(self.state.active_buffs),
            enemy_state=enemy_state,
            current_time=self.state.current_time,
            combat_time=self.state.combat_time,
            combat_duration=self.combat_duration,
            total_damage=self.state.total_damage,
            damage_log=list(self.state.damage_log),
            action_log=list(self.state.action_log),
            cooldowns=dict(self.state.cooldowns),
        )


def _account_content_start_for_party(data_path: Path, party_preset: dict[str, Any] | None) -> dict[str, Any] | None:
    relative_path = (party_preset or {}).get("content_start_contract_path")
    if not relative_path:
        return None
    path = data_path.parent / str(relative_path)
    if not path.is_file():
        raise ValueError(f"Account content-start contract is missing: {path}")
    payload = _read_json_object(path)
    if payload.get("party_id") != party_preset.get("party_id"):
        raise ValueError("Account content-start contract party_id does not match the party preset")
    return payload


def _read_json(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def _read_json_object(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)
