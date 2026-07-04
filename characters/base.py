from __future__ import annotations

from typing import Any


class CharacterMechanic:
    character_id: str = "default"

    def initialize_state(self, state: Any) -> None:
        pass

    def initialize_character_state(self, character_id: str, data: Any) -> None:
        self.character_id = character_id

    def resolve_action(self, state: Any, selected_action: Any, actions_by_id: dict[str, Any]) -> Any:
        return selected_action

    def get_policy_actions(self, character_state: Any, party_state: Any) -> list[str]:
        return []

    def get_action_mask(self, character_state: Any, party_state: Any) -> dict[str, bool]:
        return {}

    def is_action_available(self, state: Any, action: Any) -> bool:
        return True

    def before_action(self, state: Any, action: Any) -> None:
        pass

    def get_action_damage_multiplier(self, state: Any, action: Any) -> float:
        return 1.0

    def get_action_stat_modifiers(self, state: Any, action: Any, characters: dict[str, Any] | None = None) -> dict[str, float]:
        return {}

    def get_action_log_fields(self, state: Any, action: Any, characters: dict[str, Any] | None = None) -> dict[str, Any]:
        return {}

    def after_action(self, state: Any, action: Any, result: Any) -> None:
        pass

    def apply_character_mechanics(self, resolved_action: Any, character_state: Any, party_state: Any) -> None:
        pass

    def resolve_incoming_qte_transition_action(
        self,
        character_state: Any,
        transition_config: dict[str, Any],
    ) -> tuple[str | None, list[str]]:
        return None, []

    def advance_time(self, state: Any, elapsed_time: float) -> None:
        pass

    def get_observation_values(self, state: Any) -> list[float]:
        return []

    def get_observation_labels(self) -> list[str]:
        return []

    def get_debug_state(self, state: Any) -> dict[str, Any]:
        return {}

    def get_display_state(self, character_state: Any) -> dict[str, Any]:
        return dict(character_state) if isinstance(character_state, dict) else {}
