from __future__ import annotations

import json
from pathlib import Path

from simulator.action_executor import execute_action, timeline_entry
from simulator.models import ActionData, BuffData, CharacterData, CombatState, SimulationSummary, TimelineEntry
from simulator.state import create_initial_state


class Simulation:
    def __init__(
        self,
        characters: dict[str, CharacterData],
        actions: dict[str, ActionData],
        buffs: dict[str, BuffData],
        combat_duration: float = 120.0,
    ) -> None:
        self.characters = characters
        self.actions = actions
        self.buffs = buffs
        self.combat_duration = combat_duration
        self.state: CombatState = create_initial_state(characters)
        self.timeline: list[TimelineEntry] = []

    @classmethod
    def from_json(cls, data_dir: Path | str) -> "Simulation":
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
        return cls(characters=characters, actions=actions, buffs=buffs)

    def execute_action(self, action_id: str) -> bool:
        if self.state.current_time >= self.combat_duration:
            return False

        action = self.actions[action_id]
        result = execute_action(action, self.state, self.characters, self.buffs)
        if not result.valid:
            return False

        active_name = self.characters[self.state.active_character_id].name
        self.timeline.append(timeline_entry(result, active_name))
        return True

    def run_sequence(self, action_ids: list[str]) -> "Simulation":
        for action_id in action_ids:
            if self.state.current_time >= self.combat_duration:
                break
            self.execute_action(action_id)
        return self

    def valid_action_ids(self) -> list[str]:
        from simulator.action_executor import is_action_valid

        return [
            action_id
            for action_id, action in self.actions.items()
            if is_action_valid(action, self.state)[0]
        ]

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
            final_time=self.state.current_time,
            active_character=active_character,
            timeline=self.timeline,
            resources=resources,
        )


def _read_json(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)
