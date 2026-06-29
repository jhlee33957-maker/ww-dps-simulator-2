from __future__ import annotations

from typing import Any

from characters.base import CharacterMechanic


class AemeathMechanic(CharacterMechanic):
    character_id = "aemeath"

    _DEFAULT_STATE: dict[str, Any] = {
        "form": "aemeath",
        "aemeath_combo_stage": 1,
        "mech_combo_stage": 1,
        "synchronization_rate": 0,
        "resonance_rate": 0,
        "seraphic_duo_remaining": 0.0,
        "heavenfall_unbound": False,
        "finale_available": False,
    }

    def initialize_state(self, state: Any) -> None:
        state.character_mechanics_state.setdefault(self.character_id, dict(self._DEFAULT_STATE))

    def get_observation_values(self, state: Any) -> list[float]:
        data = self._state(state)
        return [
            1.0 if data["form"] == "mech" else 0.0,
            float(data["aemeath_combo_stage"]) / 4.0,
            float(data["mech_combo_stage"]) / 4.0,
            float(data["synchronization_rate"]) / 200.0,
            float(data["resonance_rate"]) / 4.0,
            float(data["seraphic_duo_remaining"]) / 5.0,
            1.0 if data["heavenfall_unbound"] else 0.0,
            1.0 if data["finale_available"] else 0.0,
        ]

    def get_observation_labels(self) -> list[str]:
        return [
            "aemeath.form_is_mech",
            "aemeath.aemeath_combo_stage",
            "aemeath.mech_combo_stage",
            "aemeath.synchronization_rate",
            "aemeath.resonance_rate",
            "aemeath.seraphic_duo_remaining",
            "aemeath.heavenfall_unbound",
            "aemeath.finale_available",
        ]

    def get_debug_state(self, state: Any) -> dict[str, Any]:
        return dict(self._state(state))

    def _state(self, state: Any) -> dict[str, Any]:
        self.initialize_state(state)
        return state.character_mechanics_state[self.character_id]
