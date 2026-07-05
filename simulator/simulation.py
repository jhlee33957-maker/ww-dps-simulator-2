from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from characters.base import CharacterMechanic
from characters.registry import get_mechanic, get_mechanics_for_characters
from simulator.action_executor import execute_action, is_action_valid, timeline_entry
from simulator.build_profiles import (
    build_action_scaling_summary,
    effective_build_stats_summary,
    load_build_profiles,
    resolve_character_build_stats,
    resolve_party_build_profiles,
    validate_effective_build_profiles,
)
from simulator.buff_system import add_team_buff
from simulator.echo_sets import (
    AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID,
    active_echo_sets_for_characters,
    echo_set_active_buff_ids,
    trailblazing_star_config,
    trailblazing_star_enabled,
    trailblazing_star_uptime_seconds,
)
from simulator.mechanic_events import mechanic_event_metadata_for_config
from simulator.models import ActionData, BuffData, CharacterData, CombatState, EnemyData, PartyState, SimulationSummary, TimelineEntry
from simulator.party_transition import (
    build_transition_swap_action,
    default_transition_config,
    fallback_swap_timing,
    resolve_party_transition,
)
from simulator.resource_system import initialize_concerto_states
from simulator.roster import (
    get_initial_active_character,
    get_swap_target_character_id,
    is_swap_action,
    parse_party_character_ids,
    read_party_presets,
    resolve_party_preset,
)
from simulator.state import create_initial_state
from simulator.transition_config import build_effective_transition_config, load_transition_config


class Simulation:
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
        self.preset_generic_swap = self.party_preset_config.get("generic_swap", {})
        self.characters = {
            character_id: characters[character_id]
            for character_id in self.selected_character_ids
        }
        self.actions = dict(actions)
        self._ensure_party_swap_actions()
        self.actions_by_id = self.actions
        self.policy_actions = self._build_policy_actions()
        self.action_scaling_summary = build_action_scaling_summary(self.actions.values(), self.selected_character_ids)
        self.effective_build_stats_summary = effective_build_stats_summary(self.characters, self.action_scaling_summary)
        self.build_profile_validation = validate_effective_build_profiles(self.effective_build_stats_summary)
        self.buffs = buffs
        self.combat_duration = combat_duration
        self.enemy = enemy or EnemyData()
        self.state: CombatState = create_initial_state(self.characters, self.enemy, self.initial_active_character)
        self.state.combat_duration = self.combat_duration
        self.state.mechanics_config = dict(self.transition_config.get("mechanics") or {})
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
        )

    def validate_build_profiles(self) -> dict[str, object]:
        self.action_scaling_summary = build_action_scaling_summary(self.actions.values(), self.selected_character_ids)
        self.effective_build_stats_summary = effective_build_stats_summary(self.characters, self.action_scaling_summary)
        self.build_profile_validation = validate_effective_build_profiles(self.effective_build_stats_summary)
        return dict(self.build_profile_validation)

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

    def execute_action(self, action_id: str) -> bool:
        if self.state.combat_time >= self.combat_duration:
            return False

        selected_action = self.actions[action_id]
        if selected_action.policy_selectable and action_id not in self.policy_actions:
            return False
        transition_resolution = None
        if is_swap_action(selected_action):
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
            action.action_time = max(transition_resolution.action_time, 0.001)
            action.duration = max(transition_resolution.action_time, 0.001)
            action.combat_time_cost = max(transition_resolution.combat_time_cost, 0.0)
        else:
            action = self.resolve_action(selected_action)
        if not self.is_resolved_action_available(action):
            return False

        self._apply_pre_transition_events(transition_resolution)
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
        result = execute_action(
            action,
            self.state,
            self.characters,
            self.buffs,
            mechanic=actor_mechanic,
            combat_duration=self.combat_duration,
        )
        if not result.valid:
            return False
        result.selected_action_id = selected_action.id
        result.selected_action_name = selected_action.name
        result.resolved_action_id = action.id
        result.resolved_action_name = action.name
        if transition_resolution is not None:
            self._apply_transition_resolution(result, transition_resolution)

        for mechanic in self.character_mechanics.values():
            mechanic.advance_time(self.state, result.action_time)
        if not result.truncated_by_combat_limit and not (action.mechanic_effects or {}).get("skip_character_after_action"):
            actor_mechanic.after_action(self.state, action, result)
        result.mechanic_debug_after = {
            character_id: mechanic.get_debug_state(self.state)
            for character_id, mechanic in self.character_mechanics.items()
            if mechanic.get_debug_state(self.state)
        }
        self._apply_post_mechanic_transition_debug(result)
        if self.state.action_log:
            self.state.action_log[-1] = result.model_dump(mode="json")

        active_name = self.characters[self.state.active_character_id].name
        self.timeline.append(timeline_entry(result, active_name))
        return True

    def run_sequence(self, action_ids: list[str]) -> "Simulation":
        for action_id in action_ids:
            if self.state.combat_time >= self.combat_duration:
                break
            self.execute_action(action_id)
        return self

    def valid_action_ids(self) -> list[str]:
        return [
            action_id
            for action_id, action in self.policy_actions.items()
            if action.policy_selectable and self.is_action_available(action)
        ]

    def is_action_available(self, action: ActionData) -> bool:
        if self.state.combat_time >= self.combat_duration:
            return False
        if action.policy_selectable:
            action = self.resolve_action(action)
        return self.is_resolved_action_available(action)

    def is_resolved_action_available(self, action: ActionData) -> bool:
        valid, _reason = is_action_valid(action, self.state)
        if not valid:
            return False
        if action.action_type in {"swap", "wait"} or action.character_id is None:
            return True
        return self._mechanic_for_character(action.character_id).is_action_available(self.state, action)

    def resolve_action(self, selected_action: ActionData) -> ActionData:
        mechanic = self._mechanic_for_character(self.state.active_character_id)
        return mechanic.resolve_action(self.state, selected_action, self.actions)

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
                duration=max(action_time, 0.001),
                action_time=max(action_time, 0.001),
                combat_time_cost=max(combat_time_cost, 0.0),
                cooldown=0.0,
                damage_multiplier=0.0,
                resonance_energy_cost=0.0,
                tags=["swap", "party-foundation", "party-transition"],
                data_status="transition_request",
                notes="Generated generic party swap transition request with placeholder fallback timing.",
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
        result.transition_events = transition_resolution.transition_events
        result.transition_event_details = transition_resolution.transition_events
        result.outgoing_outro_event_id = transition_resolution.outgoing_outro_event_id
        result.incoming_intro_event_id = transition_resolution.incoming_intro_event_id
        result.fallback_swap_used = transition_resolution.fallback_swap_used
        result.swap_timing_is_placeholder = transition_resolution.swap_timing_is_placeholder
        result.swap_timing_source = transition_resolution.swap_timing_source
        result.transition_warnings = transition_resolution.warnings

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

    def _apply_pre_transition_events(self, transition_resolution) -> None:
        if transition_resolution is None:
            return
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

    def _apply_post_mechanic_transition_debug(self, result) -> None:
        data = self.state.character_mechanics_state.get("mornye")
        if not isinstance(data, dict):
            return
        result.mornye_mode_after = data.get("mode")
        result.mornye_rest_mass_after = float(data.get("rest_mass_energy", 0.0))
        result.mornye_wfo_remaining_after = float(data.get("wide_field_observation_remaining", 0.0))
        result.mornye_syntony_field_remaining_after = float(data.get("syntony_field_remaining", 0.0))

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

        return SimulationSummary(
            total_damage=self.state.total_damage,
            dps=self.state.total_damage / self.combat_duration,
            final_time=self.state.combat_time,
            final_action_time=self.state.current_time,
            active_character=active_character,
            timeline=self.timeline,
            resources=resources,
            damage_by_selected_action=dict(damage_by_selected_action),
            damage_by_resolved_action=dict(damage_by_resolved_action),
            damage_by_action_type=dict(damage_by_action_type),
            damage_by_damage_bonus_category=dict(damage_by_damage_bonus_category),
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
                self.state.current_time,
            ),
            aemeath_trailblazing_star_5set_buff_windows=trailblazing_windows,
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


def _read_json(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def _read_json_object(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)
