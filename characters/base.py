from __future__ import annotations

from typing import Any


class CharacterMechanic:
    character_id: str = "default"

    def initialize_state(self, state: Any) -> None:
        pass

    def resolve_action(self, state: Any, selected_action: Any, actions_by_id: dict[str, Any]) -> Any:
        return selected_action

    def is_action_available(self, state: Any, action: Any) -> bool:
        return True

    def before_action(self, state: Any, action: Any) -> None:
        pass

    def get_action_damage_multiplier(self, state: Any, action: Any) -> float:
        return 1.0

    def after_action(self, state: Any, action: Any, result: Any) -> None:
        pass

    def advance_time(self, state: Any, elapsed_time: float) -> None:
        pass

    def get_observation_values(self, state: Any) -> list[float]:
        return []

    def get_observation_labels(self) -> list[str]:
        return []

    def get_debug_state(self, state: Any) -> dict[str, Any]:
        return {}
