from __future__ import annotations

from copy import deepcopy
from typing import Any

from characters.base import CharacterMechanic


LYNAE_LIBERATION_ACTION_ID = "lynae_resonance_liberation_prismatic_overblast"
LYNAE_ECHO_HYVATIA_ACTION_ID = "lynae_echo_hyvatia"
LYNAE_OUTRO_ACTION_ID = "lynae_outro_lets_hit_the_road"
LYNAE_POLICY_BASIC_ACTION_ID = "lynae_basic_attack"
LYNAE_POLICY_SKILL_ACTION_ID = "lynae_resonance_skill"


class LynaeMechanic(CharacterMechanic):
    character_id = "lynae"

    _DEFAULT_STATE: dict[str, Any] = {
        "overflow": 0.0,
        "overflow_max": 120.0,
        "lumiflow": 0.0,
        "lumiflow_max": 120.0,
        "true_color": 0.0,
        "true_color_max": 3.0,
        "basic_combo_stage": 1,
        "kaleidoscopic_combo_stage": 1,
        "kaleidoscopic_parade_remaining": 0.0,
        "optical_sampling_stage_active": True,
        "photocromic_flux_active": False,
        "photocromic_flux_remaining": 0.0,
        "lynae_resonance_mode": "tune_rupture",
        "hyvatia_outro_window_remaining": 0.0,
        "spectral_analysis_cooldown_remaining": 0.0,
        "last_spectral_analysis_damage": 0.0,
        "last_lynae_buff_events": [],
        "last_resolved_action_id": None,
    }

    _BASIC_BY_STAGE = {
        1: "lynae_basic_stage_1",
        2: "lynae_basic_stage_2",
        3: "lynae_basic_stage_3",
    }

    def initialize_state(self, state: Any) -> None:
        data = state.character_mechanics_state.setdefault(self.character_id, deepcopy(self._DEFAULT_STATE))
        for key, value in self._DEFAULT_STATE.items():
            data.setdefault(key, deepcopy(value))
        mode = ((state.mechanics_config or {}).get("lynae") or {}).get("lynae_resonance_mode")
        if mode in {"tune_rupture", "tune_strain", "unresolved"}:
            data["lynae_resonance_mode"] = mode
        self._clamp(data)

    def resolve_action(self, state: Any, selected_action: Any, actions_by_id: dict[str, Any]) -> Any:
        data = self._state(state)
        resolved_id = selected_action.id
        if selected_action.id == LYNAE_POLICY_BASIC_ACTION_ID:
            if data.get("kaleidoscopic_parade_remaining", 0.0) > 0.0:
                stage = int(data.get("kaleidoscopic_combo_stage", 1) or 1)
                resolved_id = f"lynae_kaleidoscopic_basic_stage_{max(1, min(5, stage))}"
            else:
                stage = int(data.get("basic_combo_stage", 1) or 1)
                resolved_id = self._BASIC_BY_STAGE.get(max(1, min(3, stage)), "lynae_basic_stage_1")
        elif selected_action.id == LYNAE_POLICY_SKILL_ACTION_ID:
            resolved_id = "lynae_resonance_skill_palette"
        elif selected_action.id == "lynae_resonance_liberation":
            resolved_id = LYNAE_LIBERATION_ACTION_ID
        try:
            return actions_by_id[resolved_id]
        except KeyError as exc:
            raise KeyError(f"Lynae resolved {selected_action.id!r} to missing action {resolved_id!r}.") from exc

    def get_policy_actions(self, character_state: Any, party_state: Any) -> list[str]:
        return [
            LYNAE_POLICY_BASIC_ACTION_ID,
            LYNAE_POLICY_SKILL_ACTION_ID,
            "lynae_resonance_liberation",
            LYNAE_ECHO_HYVATIA_ACTION_ID,
            "lynae_tune_break",
        ]

    def get_action_log_fields(self, state: Any, action: Any, characters: dict[str, Any] | None = None) -> dict[str, Any]:
        data = self._state(state)
        return {
            "lynae_overflow": float(data.get("overflow", 0.0) or 0.0),
            "lynae_overflow_max": float(data.get("overflow_max", 120.0) or 120.0),
            "lynae_lumiflow": float(data.get("lumiflow", 0.0) or 0.0),
            "lynae_true_color": float(data.get("true_color", 0.0) or 0.0),
            "lynae_kaleidoscopic_parade_remaining": float(
                data.get("kaleidoscopic_parade_remaining", 0.0) or 0.0
            ),
            "lynae_optical_sampling_stage_active": bool(data.get("optical_sampling_stage_active", True)),
            "lynae_resonance_mode": data.get("lynae_resonance_mode", "tune_rupture"),
            "hyvatia_outro_window_remaining": float(data.get("hyvatia_outro_window_remaining", 0.0) or 0.0),
            "lynae_liberation_party_damage_buff_active": action.id == LYNAE_LIBERATION_ACTION_ID,
            "lynae_liberation_party_damage_buff_value": 0.24 if action.id == LYNAE_LIBERATION_ACTION_ID else 0.0,
        }

    def after_action(self, state: Any, action: Any, result: Any) -> None:
        data = self._state(state)
        data["last_resolved_action_id"] = action.id
        if action.id == LYNAE_ECHO_HYVATIA_ACTION_ID:
            data["hyvatia_outro_window_remaining"] = 15.0
        if action.id == "lynae_spark_collision":
            data["overflow"] = 0.0
            data["kaleidoscopic_parade_remaining"] = 15.0
        if action.id in self._BASIC_BY_STAGE.values():
            data["basic_combo_stage"] = 1 if int(data.get("basic_combo_stage", 1) or 1) >= 3 else int(data.get("basic_combo_stage", 1) or 1) + 1
        if action.id.startswith("lynae_kaleidoscopic_basic_stage_"):
            data["kaleidoscopic_combo_stage"] = 1 if int(data.get("kaleidoscopic_combo_stage", 1) or 1) >= 5 else int(data.get("kaleidoscopic_combo_stage", 1) or 1) + 1
        self._clamp(data)

    def advance_time(self, state: Any, elapsed_time: float) -> None:
        data = self._state(state)
        for key in (
            "kaleidoscopic_parade_remaining",
            "photocromic_flux_remaining",
            "hyvatia_outro_window_remaining",
            "spectral_analysis_cooldown_remaining",
        ):
            data[key] = max(0.0, float(data.get(key, 0.0) or 0.0) - max(0.0, elapsed_time))
        data["photocromic_flux_active"] = data["photocromic_flux_remaining"] > 0.0

    def get_observation_values(self, state: Any) -> list[float]:
        return []

    def get_observation_labels(self) -> list[str]:
        return []

    def get_debug_state(self, state: Any) -> dict[str, Any]:
        data = self._state(state)
        return {
            "mode": data.get("lynae_resonance_mode"),
            "overflow": float(data.get("overflow", 0.0) or 0.0),
            "lumiflow": float(data.get("lumiflow", 0.0) or 0.0),
            "true_color": float(data.get("true_color", 0.0) or 0.0),
            "hyvatia_outro_window_remaining": float(data.get("hyvatia_outro_window_remaining", 0.0) or 0.0),
        }

    def _state(self, state: Any) -> dict[str, Any]:
        data = state.character_mechanics_state.setdefault(self.character_id, deepcopy(self._DEFAULT_STATE))
        for key, value in self._DEFAULT_STATE.items():
            data.setdefault(key, deepcopy(value))
        return data

    def _clamp(self, data: dict[str, Any]) -> None:
        data["overflow"] = min(max(0.0, float(data.get("overflow", 0.0) or 0.0)), float(data["overflow_max"]))
        data["lumiflow"] = min(max(0.0, float(data.get("lumiflow", 0.0) or 0.0)), float(data["lumiflow_max"]))
        data["true_color"] = min(max(0.0, float(data.get("true_color", 0.0) or 0.0)), float(data["true_color_max"]))
