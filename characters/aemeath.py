from __future__ import annotations

from typing import Any

from characters.base import CharacterMechanic


class AemeathMechanic(CharacterMechanic):
    character_id = "aemeath"

    _DEFAULT_STATE: dict[str, Any] = {
        "form": "aemeath",
        "aemeath_combo_stage": 1,
        "mech_combo_stage": 1,
        "synchronization_rate": 0.0,
        "resonance_rate": 0.0,
        "seraphic_duo_remaining": 0.0,
        "heavenfall_unbound": False,
        "finale_available": False,
    }

    _AEMEATH_BASIC_BY_STAGE = {
        1: "aemeath_basic_form_stage_1",
        2: "aemeath_basic_form_stage_2",
        3: "aemeath_basic_form_stage_3",
        4: "aemeath_basic_form_stage_4",
    }
    _MECH_BASIC_BY_STAGE = {
        1: "aemeath_mech_basic_stage_1",
        2: "aemeath_mech_basic_stage_2",
        3: "aemeath_mech_basic_stage_3",
        4: "aemeath_mech_basic_stage_4",
    }

    def initialize_state(self, state: Any) -> None:
        data = state.character_mechanics_state.setdefault(self.character_id, dict(self._DEFAULT_STATE))
        for key, value in self._DEFAULT_STATE.items():
            data.setdefault(key, value)
        self._clamp(data)

    def resolve_action(self, state: Any, selected_action: Any, actions_by_id: dict[str, Any]) -> Any:
        data = self._state(state)
        resolved_id = selected_action.id

        if selected_action.id == "aemeath_basic_attack":
            if data["form"] == "mech":
                resolved_id = self._MECH_BASIC_BY_STAGE[int(data["mech_combo_stage"])]
            else:
                resolved_id = self._AEMEATH_BASIC_BY_STAGE[int(data["aemeath_combo_stage"])]
        elif selected_action.id == "aemeath_resonance_skill":
            if data["seraphic_duo_remaining"] > 0.0:
                resolved_id = (
                    "aemeath_seraphic_duet_encore"
                    if data["synchronization_rate"] >= 100.0
                    else "aemeath_seraphic_duet_overturn"
                )
            else:
                resolved_id = "aemeath_form_switch_to_aemeath" if data["form"] == "mech" else "aemeath_form_switch_to_mech"
        elif selected_action.id == "aemeath_resonance_liberation":
            if data["finale_available"] or (data["heavenfall_unbound"] and data["resonance_rate"] >= 4.0):
                resolved_id = "aemeath_heavenfall_finale"
            else:
                resolved_id = "aemeath_liberation_overdrive"

        try:
            return actions_by_id[resolved_id]
        except KeyError as exc:
            raise KeyError(f"Aemeath resolved {selected_action.id!r} to missing action {resolved_id!r}.") from exc

    def is_action_available(self, state: Any, action: Any) -> bool:
        data = self._state(state)
        action_id = action.id
        if action_id.startswith("aemeath_basic_form_stage_") or action_id.startswith("aemeath_mech_basic_stage_"):
            return True
        if action_id.startswith("aemeath_form_switch_"):
            return True
        if action_id == "aemeath_seraphic_duet_overturn":
            return data["seraphic_duo_remaining"] > 0.0
        if action_id == "aemeath_seraphic_duet_encore":
            return data["seraphic_duo_remaining"] > 0.0 and data["synchronization_rate"] >= 100.0
        if action_id == "aemeath_heavenfall_finale":
            return data["finale_available"] or (data["heavenfall_unbound"] and data["resonance_rate"] >= 4.0)
        if action_id == "aemeath_liberation_overdrive":
            return True
        return True

    def after_action(self, state: Any, action: Any, result: Any) -> None:
        data = self._state(state)
        effects = action.mechanic_effects
        duration_was_set = "seraphic_duo_duration" in effects

        if data["seraphic_duo_remaining"] > 0.0:
            data["seraphic_duo_remaining"] = max(0.0, data["seraphic_duo_remaining"] - result.action_time)

        if "set_form" in effects:
            data["form"] = effects["set_form"]
        if "sync_delta" in effects:
            data["synchronization_rate"] += float(effects["sync_delta"])
        if "set_synchronization_rate" in effects:
            data["synchronization_rate"] = float(effects["set_synchronization_rate"])
        if "resonance_rate_delta" in effects:
            data["resonance_rate"] += float(effects["resonance_rate_delta"])
        if "set_resonance_rate" in effects:
            data["resonance_rate"] = float(effects["set_resonance_rate"])
        if duration_was_set:
            data["seraphic_duo_remaining"] = float(effects["seraphic_duo_duration"])
        if "heavenfall_unbound" in effects:
            data["heavenfall_unbound"] = bool(effects["heavenfall_unbound"])
        if "finale_available" in effects:
            data["finale_available"] = bool(effects["finale_available"])
        if "set_aemeath_combo_stage" in effects:
            data["aemeath_combo_stage"] = int(effects["set_aemeath_combo_stage"])
        if "set_mech_combo_stage" in effects:
            data["mech_combo_stage"] = int(effects["set_mech_combo_stage"])

        self._clamp(data)
        if data["heavenfall_unbound"] and data["resonance_rate"] >= 4.0:
            data["finale_available"] = True

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
        data = self._state(state)
        return {
            "form": data["form"],
            "aemeath_combo_stage": data["aemeath_combo_stage"],
            "mech_combo_stage": data["mech_combo_stage"],
            "synchronization_rate": data["synchronization_rate"],
            "resonance_rate": data["resonance_rate"],
            "seraphic_duo_remaining": data["seraphic_duo_remaining"],
            "heavenfall_unbound": data["heavenfall_unbound"],
            "finale_available": data["finale_available"],
        }

    def _state(self, state: Any) -> dict[str, Any]:
        self.initialize_state(state)
        return state.character_mechanics_state[self.character_id]

    def _clamp(self, data: dict[str, Any]) -> None:
        data["form"] = "mech" if data["form"] == "mech" else "aemeath"
        data["aemeath_combo_stage"] = max(1, min(4, int(data["aemeath_combo_stage"])))
        data["mech_combo_stage"] = max(1, min(4, int(data["mech_combo_stage"])))
        data["synchronization_rate"] = max(0.0, min(200.0, float(data["synchronization_rate"])))
        data["resonance_rate"] = max(0.0, min(4.0, float(data["resonance_rate"])))
        data["seraphic_duo_remaining"] = max(0.0, float(data["seraphic_duo_remaining"]))
        data["heavenfall_unbound"] = bool(data["heavenfall_unbound"])
        data["finale_available"] = bool(data["finale_available"])
