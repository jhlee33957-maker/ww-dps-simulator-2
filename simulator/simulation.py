from __future__ import annotations

import json
from pathlib import Path

from characters.base import CharacterMechanic
from characters.registry import get_mechanic, get_mechanics_for_characters
from simulator.action_executor import execute_action, is_action_valid, timeline_entry
from simulator.buff_system import add_team_buff
from simulator.models import ActionData, BuffData, CharacterData, CombatState, EnemyData, PartyState, SimulationSummary, TimelineEntry
from simulator.party_transition import (
    build_transition_swap_action,
    default_transition_config,
    fallback_swap_timing,
    load_transition_config,
    resolve_party_transition,
)
from simulator.roster import (
    get_initial_active_character,
    get_swap_target_character_id,
    is_swap_action,
    parse_party_character_ids,
    read_party_presets,
    resolve_party_preset,
)
from simulator.state import create_initial_state


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
    ) -> None:
        self.all_characters = characters
        self.selected_character_ids = parse_party_character_ids(selected_character_ids, characters)
        self.selected_party_character_ids = self.selected_character_ids
        self.party_character_ids = self.selected_character_ids
        self.selected_party = self.selected_character_ids
        self.initial_active_character = get_initial_active_character(self.selected_character_ids, initial_active_character)
        self.transition_config = transition_config or default_transition_config()
        self.party_preset_config = party_preset_config or {}
        self.preset_generic_swap = self.party_preset_config.get("generic_swap", {})
        self.characters = {
            character_id: characters[character_id]
            for character_id in self.selected_character_ids
        }
        self.actions = dict(actions)
        self._ensure_party_swap_actions()
        self.actions_by_id = self.actions
        self.policy_actions = self._build_policy_actions()
        self.buffs = buffs
        self.combat_duration = combat_duration
        self.enemy = enemy or EnemyData()
        self.state: CombatState = create_initial_state(self.characters, self.enemy, self.initial_active_character)
        self.state.combat_duration = self.combat_duration
        self.character_mechanics = get_mechanics_for_characters(self.selected_character_ids)
        for mechanic in self.character_mechanics.values():
            mechanic.initialize_state(self.state)
        for character_id in self.selected_character_ids:
            self.state.character_mechanics_state.setdefault(character_id, {})
        self.state.character_states = self.state.character_mechanics_state
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
        return cls(
            characters=characters,
            actions=actions,
            buffs=buffs,
            enemy=enemy,
            selected_character_ids=selection_value,
            initial_active_character=initial_active_character or preset_initial_active,
            transition_config=load_transition_config(data_path),
            party_preset_config=party_preset_config,
        )

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
            action.action_time = max(transition_resolution.action_time, 0.001)
            action.duration = max(transition_resolution.action_time, 0.001)
            action.combat_time_cost = max(transition_resolution.combat_time_cost, 0.0)
        else:
            action = self.resolve_action(selected_action)
        if not self.is_resolved_action_available(action):
            return False

        actor_character_id = self.state.active_character_id if action.action_type in {"swap", "wait"} else action.character_id
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
        if not result.truncated_by_combat_limit:
            actor_mechanic.after_action(self.state, action, result)
        result.mechanic_debug_after = {
            character_id: mechanic.get_debug_state(self.state)
            for character_id, mechanic in self.character_mechanics.items()
            if mechanic.get_debug_state(self.state)
        }

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
        result.transition_events = transition_resolution.transition_events
        result.outgoing_outro_event_id = transition_resolution.outgoing_outro_event_id
        result.incoming_intro_event_id = transition_resolution.incoming_intro_event_id
        result.fallback_swap_used = transition_resolution.fallback_swap_used
        result.swap_timing_is_placeholder = transition_resolution.swap_timing_is_placeholder
        result.swap_timing_source = transition_resolution.swap_timing_source
        result.transition_warnings = transition_resolution.warnings

        if not result.truncated_by_combat_limit:
            applied_buffs = list(result.applied_buffs)
            for event in transition_resolution.transition_events:
                for buff_id in event.get("applies_buffs", []):
                    if buff_id not in self.buffs:
                        result.transition_warnings.append(f"Transition buff {buff_id!r} is not registered.")
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

    def _mechanic_for_character(self, character_id: str) -> CharacterMechanic:
        mechanic = self.character_mechanics.get(character_id)
        if mechanic is None:
            mechanic = get_mechanic(character_id)
            mechanic.initialize_state(self.state)
            self.character_mechanics[character_id] = mechanic
        return mechanic

    def summary(self) -> SimulationSummary:
        active_character = self.characters[self.state.active_character_id].name
        resources = {
            char_id: {
                "resonance_energy": self.state.resonance_energy.get(char_id, 0.0),
                "resonance_energy_max": self.characters[char_id].resonance_energy_max,
                "wasted_resonance_energy": self.state.wasted_resonance_energy.get(char_id, 0.0),
                "concerto_energy": self.state.concerto_energy.get(char_id, 0.0),
                "wasted_concerto_energy": self.state.wasted_concerto_energy.get(char_id, 0.0),
            }
            for char_id in self.characters
        }
        return SimulationSummary(
            total_damage=self.state.total_damage,
            dps=self.state.total_damage / self.combat_duration,
            final_time=self.state.combat_time,
            final_action_time=self.state.current_time,
            active_character=active_character,
            timeline=self.timeline,
            resources=resources,
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
