from __future__ import annotations

from copy import deepcopy
from typing import Any

from characters.base import CharacterMechanic


LYNAE_LIBERATION_ACTION_ID = "lynae_resonance_liberation_prismatic_overblast"
LYNAE_ECHO_HYVATIA_ACTION_ID = "lynae_echo_hyvatia"
LYNAE_OUTRO_ACTION_ID = "lynae_outro_lets_hit_the_road"
LYNAE_POLICY_BASIC_ACTION_ID = "lynae_basic_attack"
LYNAE_POLICY_SKILL_ACTION_ID = "lynae_resonance_skill"
LYNAE_SPARK_SELECTOR_ACTION_ID = "lynae_spark_collision"
LYNAE_POLYCHROME_LEAP_SELECTOR_ACTION_ID = "lynae_polychrome_leap"
LYNAE_VIVID_TOMORROW_ACTION_ID = "lynae_to_a_vivid_tomorrow"
LYNAE_VISUAL_IMPACT_ACTION_ID = "lynae_visual_impact"
LYNAE_IRIDESCENT_SPLASH_ACTION_ID = "lynae_iridescent_splash"
LYNAE_INTRO_ACTION_ID = "lynae_intro_time_to_show_some_colors"

KP_DURATION_SECONDS = 15.0
PHOTOCROMIC_FLUX_DURATION_SECONDS = 25.0
SPRAY_PAINT_DURATION_SECONDS = 5.0
VIVID_TOMORROW_WINDOW_SECONDS = 8.0


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
        "photocromic_flux_source_action_id": None,
        "target_tune_shift_state": None,
        "target_tune_shift_remaining": 0.0,
        "lynae_resonance_mode": "tune_rupture",
        "hyvatia_outro_window_remaining": 0.0,
        "spray_paint_window_remaining": 0.0,
        "visual_impact_cooldown_remaining": 0.0,
        "to_vivid_tomorrow_window_remaining": 0.0,
        "next_basic_forced_stage": None,
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
    _KP_BASIC_BY_STAGE = {
        1: "lynae_kaleidoscopic_basic_stage_1",
        2: "lynae_kaleidoscopic_basic_stage_2",
        3: "lynae_kaleidoscopic_basic_stage_3",
        4: "lynae_kaleidoscopic_basic_stage_4",
        5: "lynae_kaleidoscopic_basic_stage_5",
    }
    _POLYCHROME_LEAP_BY_STAGE = {
        1: "lynae_polychrome_leap_stage_1",
        2: "lynae_polychrome_leap_stage_2",
        3: "lynae_polychrome_leap_stage_3",
    }
    _OPTICAL_OVERFLOW_GAINS = {
        "lynae_basic_stage_1": 12.0,
        "lynae_basic_stage_2": 21.0,
        "lynae_basic_stage_3": 17.0,
        "lynae_dodge_counter": 19.0,
        "lynae_mid_air_attack": 20.0,
        "lynae_resonance_skill_palette": 25.0,
        LYNAE_INTRO_ACTION_ID: 100.0,
    }
    _FLUX_ACTIONS = {
        "lynae_polychrome_leap_stage_1",
        "lynae_polychrome_leap_stage_2",
        "lynae_polychrome_leap_stage_3",
        LYNAE_IRIDESCENT_SPLASH_ACTION_ID,
        LYNAE_VISUAL_IMPACT_ACTION_ID,
        LYNAE_INTRO_ACTION_ID,
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
            if data.get("to_vivid_tomorrow_window_remaining", 0.0) > 0.0:
                resolved_id = (
                    "lynae_kaleidoscopic_basic_stage_2"
                    if self._in_kaleidoscopic_parade(data)
                    else LYNAE_VIVID_TOMORROW_ACTION_ID
                )
            elif self._in_kaleidoscopic_parade(data):
                forced_stage = data.get("next_basic_forced_stage")
                stage = int(forced_stage or data.get("kaleidoscopic_combo_stage", 1) or 1)
                resolved_id = self._KP_BASIC_BY_STAGE.get(max(1, min(5, stage)), "lynae_kaleidoscopic_basic_stage_1")
            else:
                stage = int(data.get("basic_combo_stage", 1) or 1)
                resolved_id = self._BASIC_BY_STAGE.get(max(1, min(3, stage)), "lynae_basic_stage_1")
        elif selected_action.id == LYNAE_POLICY_SKILL_ACTION_ID:
            resolved_id = (
                "lynae_resonance_skill_additive_color"
                if self._in_kaleidoscopic_parade(data)
                else "lynae_resonance_skill_palette"
            )
        elif selected_action.id == "lynae_resonance_liberation":
            resolved_id = LYNAE_LIBERATION_ACTION_ID
        elif selected_action.id == LYNAE_SPARK_SELECTOR_ACTION_ID and self._overflow_full(data):
            resolved_id = "lynae_spark_collision_lv3"
        elif selected_action.id == LYNAE_POLYCHROME_LEAP_SELECTOR_ACTION_ID:
            stage = int(float(data.get("true_color", 0.0) or 0.0)) + 1
            resolved_id = self._POLYCHROME_LEAP_BY_STAGE.get(max(1, min(3, stage)), "lynae_polychrome_leap_stage_1")

        try:
            return actions_by_id[resolved_id]
        except KeyError as exc:
            raise KeyError(f"Lynae resolved {selected_action.id!r} to missing action {resolved_id!r}.") from exc

    def get_policy_actions(self, character_state: Any, party_state: Any) -> list[str]:
        return [
            LYNAE_POLICY_BASIC_ACTION_ID,
            LYNAE_POLICY_SKILL_ACTION_ID,
            "lynae_resonance_liberation",
            LYNAE_SPARK_SELECTOR_ACTION_ID,
            LYNAE_POLYCHROME_LEAP_SELECTOR_ACTION_ID,
            LYNAE_IRIDESCENT_SPLASH_ACTION_ID,
            LYNAE_VISUAL_IMPACT_ACTION_ID,
            LYNAE_ECHO_HYVATIA_ACTION_ID,
            "lynae_tune_break",
        ]

    def is_action_available(self, state: Any, action: Any) -> bool:
        data = self._state(state)
        action_id = action.id
        if action_id == LYNAE_SPARK_SELECTOR_ACTION_ID:
            return bool(data.get("optical_sampling_stage_active", True)) and self._overflow_full(data)
        if action_id == LYNAE_POLYCHROME_LEAP_SELECTOR_ACTION_ID:
            return self._in_kaleidoscopic_parade(data) and float(data.get("lumiflow", 0.0) or 0.0) >= 40.0
        if action_id.startswith("lynae_spark_collision_lv"):
            return True
        if action_id == "lynae_resonance_skill_additive_color":
            return self._in_kaleidoscopic_parade(data)
        if action_id.startswith("lynae_kaleidoscopic_"):
            return self._in_kaleidoscopic_parade(data)
        if action_id.startswith("lynae_polychrome_leap_stage_"):
            return self._in_kaleidoscopic_parade(data) and float(data.get("lumiflow", 0.0) or 0.0) >= 40.0
        if action_id in {LYNAE_IRIDESCENT_SPLASH_ACTION_ID, LYNAE_VISUAL_IMPACT_ACTION_ID}:
            if not self._in_kaleidoscopic_parade(data):
                return False
            if float(data.get("true_color", 0.0) or 0.0) < 3.0:
                return False
            if action_id == LYNAE_VISUAL_IMPACT_ACTION_ID:
                return float(data.get("visual_impact_cooldown_remaining", 0.0) or 0.0) <= 0.0
            return float(data.get("visual_impact_cooldown_remaining", 0.0) or 0.0) > 0.0
        return True

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
            "lynae_photocromic_flux_active": bool(data.get("photocromic_flux_active", False)),
            "lynae_photocromic_flux_remaining": float(data.get("photocromic_flux_remaining", 0.0) or 0.0),
            "lynae_target_tune_shift_state": data.get("target_tune_shift_state"),
            "lynae_target_tune_shift_remaining": float(data.get("target_tune_shift_remaining", 0.0) or 0.0),
            "lynae_spray_paint_window_remaining": float(data.get("spray_paint_window_remaining", 0.0) or 0.0),
            "lynae_visual_impact_cooldown_remaining": float(
                data.get("visual_impact_cooldown_remaining", 0.0) or 0.0
            ),
            "lynae_to_vivid_tomorrow_window_remaining": float(
                data.get("to_vivid_tomorrow_window_remaining", 0.0) or 0.0
            ),
            "hyvatia_outro_window_remaining": float(data.get("hyvatia_outro_window_remaining", 0.0) or 0.0),
            "lynae_liberation_party_damage_buff_active": action.id == LYNAE_LIBERATION_ACTION_ID,
            "lynae_liberation_party_damage_buff_value": 0.24 if action.id == LYNAE_LIBERATION_ACTION_ID else 0.0,
            "lynae_visual_impact_tune_break_boost_buff_active": action.id == LYNAE_VISUAL_IMPACT_ACTION_ID,
            "lynae_visual_impact_tune_break_boost_value": 40.0 if action.id == LYNAE_VISUAL_IMPACT_ACTION_ID else 0.0,
        }

    def after_action(self, state: Any, action: Any, result: Any) -> None:
        data = self._state(state)
        data["last_resolved_action_id"] = action.id
        if bool(data.get("optical_sampling_stage_active", True)):
            data["overflow"] = float(data.get("overflow", 0.0) or 0.0) + self._OPTICAL_OVERFLOW_GAINS.get(action.id, 0.0)
        if action.id == LYNAE_ECHO_HYVATIA_ACTION_ID:
            data["hyvatia_outro_window_remaining"] = 15.0
        if action.id.startswith("lynae_spark_collision_lv"):
            data["overflow"] = 0.0
            if action.id == "lynae_spark_collision_lv1":
                data["lumiflow"] = max(float(data.get("lumiflow", 0.0) or 0.0), 40.0)
            elif action.id == "lynae_spark_collision_lv2":
                data["lumiflow"] = max(float(data.get("lumiflow", 0.0) or 0.0), 80.0)
            else:
                data["lumiflow"] = float(data.get("lumiflow_max", 120.0) or 120.0)
            data["kaleidoscopic_parade_remaining"] = KP_DURATION_SECONDS
            data["optical_sampling_stage_active"] = False
        if action.id in self._BASIC_BY_STAGE.values():
            stage = int(data.get("basic_combo_stage", 1) or 1)
            data["basic_combo_stage"] = 1 if stage >= 3 else stage + 1
        if action.id.startswith("lynae_kaleidoscopic_basic_stage_"):
            data["next_basic_forced_stage"] = None
            data["to_vivid_tomorrow_window_remaining"] = 0.0
            stage = int(data.get("kaleidoscopic_combo_stage", 1) or 1)
            data["kaleidoscopic_combo_stage"] = 1 if stage >= 5 else stage + 1
        if action.id == LYNAE_VIVID_TOMORROW_ACTION_ID:
            data["to_vivid_tomorrow_window_remaining"] = 0.0
        if action.id == "lynae_kaleidoscopic_dodge_counter":
            data["next_basic_forced_stage"] = 2
        if action.id in {"lynae_resonance_skill_additive_color", LYNAE_OUTRO_ACTION_ID}:
            self._exit_kaleidoscopic_parade(data)
        if action.id == LYNAE_LIBERATION_ACTION_ID:
            data["to_vivid_tomorrow_window_remaining"] = VIVID_TOMORROW_WINDOW_SECONDS
        if action.id.startswith("lynae_polychrome_leap_stage_"):
            data["lumiflow"] = float(data.get("lumiflow", 0.0) or 0.0) - 40.0
            data["true_color"] = float(data.get("true_color", 0.0) or 0.0) + 1.0
            if action.id == "lynae_polychrome_leap_stage_1":
                data["next_basic_forced_stage"] = 2
        if action.id in {LYNAE_IRIDESCENT_SPLASH_ACTION_ID, LYNAE_VISUAL_IMPACT_ACTION_ID}:
            data["true_color"] = 0.0
        if action.id == LYNAE_VISUAL_IMPACT_ACTION_ID:
            data["spray_paint_window_remaining"] = SPRAY_PAINT_DURATION_SECONDS
            data["visual_impact_cooldown_remaining"] = 25.0
            if hasattr(result, "lynae_visual_impact_tune_break_boost_buff_active"):
                result.lynae_visual_impact_tune_break_boost_buff_active = True
                result.lynae_visual_impact_tune_break_boost_value = 40.0
        if action.id in self._FLUX_ACTIONS:
            self._apply_photocromic_flux(state, data, result, action.id)
        self._clamp(data)
        self._sync_result_state(result, data)

    def advance_time(self, state: Any, elapsed_time: float) -> None:
        data = self._state(state)
        for key in (
            "kaleidoscopic_parade_remaining",
            "photocromic_flux_remaining",
            "target_tune_shift_remaining",
            "hyvatia_outro_window_remaining",
            "spray_paint_window_remaining",
            "visual_impact_cooldown_remaining",
            "to_vivid_tomorrow_window_remaining",
            "spectral_analysis_cooldown_remaining",
        ):
            data[key] = max(0.0, float(data.get(key, 0.0) or 0.0) - max(0.0, elapsed_time))
        data["photocromic_flux_active"] = data["photocromic_flux_remaining"] > 0.0
        if data["target_tune_shift_remaining"] <= 0.0:
            data["target_tune_shift_state"] = None
        if data["kaleidoscopic_parade_remaining"] <= 0.0 and not bool(data.get("optical_sampling_stage_active", True)):
            self._exit_kaleidoscopic_parade(data)

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
            "photocromic_flux_active": bool(data.get("photocromic_flux_active", False)),
            "target_tune_shift_state": data.get("target_tune_shift_state"),
            "spray_paint_window_remaining": float(data.get("spray_paint_window_remaining", 0.0) or 0.0),
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

    def _in_kaleidoscopic_parade(self, data: dict[str, Any]) -> bool:
        return float(data.get("kaleidoscopic_parade_remaining", 0.0) or 0.0) > 0.0

    def _overflow_full(self, data: dict[str, Any]) -> bool:
        return float(data.get("overflow", 0.0) or 0.0) >= float(data.get("overflow_max", 120.0) or 120.0)

    def _exit_kaleidoscopic_parade(self, data: dict[str, Any]) -> None:
        data["kaleidoscopic_parade_remaining"] = 0.0
        data["lumiflow"] = 0.0
        data["true_color"] = 0.0
        data["kaleidoscopic_combo_stage"] = 1
        data["next_basic_forced_stage"] = None
        data["optical_sampling_stage_active"] = True

    def _apply_photocromic_flux(self, state: Any, data: dict[str, Any], result: Any, action_id: str) -> None:
        mode = data.get("lynae_resonance_mode", "tune_rupture")
        data["photocromic_flux_active"] = True
        data["photocromic_flux_remaining"] = PHOTOCROMIC_FLUX_DURATION_SECONDS
        data["photocromic_flux_source_action_id"] = action_id
        if hasattr(result, "lynae_photocromic_flux_applied"):
            result.lynae_photocromic_flux_applied = True
            result.lynae_photocromic_flux_mode = mode
            result.lynae_photocromic_flux_source_status = "user_tooltip_confirmed"
        if mode == "tune_rupture":
            shift_state = "tune_rupture_shifting"
        elif mode == "tune_strain":
            shift_state = "tune_strain_shifting"
        else:
            shift_state = None
            if hasattr(result, "lynae_photocromic_flux_unresolved_reason"):
                result.lynae_photocromic_flux_unresolved_reason = "lynae_resonance_mode_unresolved_no_shift_state"
        data["target_tune_shift_state"] = shift_state
        data["target_tune_shift_remaining"] = PHOTOCROMIC_FLUX_DURATION_SECONDS if shift_state else 0.0
        if shift_state:
            state.target_tune_shift_state = shift_state
            state.target_tune_shift_remaining = PHOTOCROMIC_FLUX_DURATION_SECONDS
            if hasattr(result, "target_tune_shift_state"):
                result.target_tune_shift_state = shift_state
                result.target_tune_shift_remaining = PHOTOCROMIC_FLUX_DURATION_SECONDS

    def _sync_result_state(self, result: Any, data: dict[str, Any]) -> None:
        fields = {
            "lynae_overflow": float(data.get("overflow", 0.0) or 0.0),
            "lynae_lumiflow": float(data.get("lumiflow", 0.0) or 0.0),
            "lynae_true_color": float(data.get("true_color", 0.0) or 0.0),
            "lynae_kaleidoscopic_parade_remaining": float(data.get("kaleidoscopic_parade_remaining", 0.0) or 0.0),
            "lynae_optical_sampling_stage_active": bool(data.get("optical_sampling_stage_active", True)),
            "lynae_photocromic_flux_active": bool(data.get("photocromic_flux_active", False)),
            "lynae_photocromic_flux_remaining": float(data.get("photocromic_flux_remaining", 0.0) or 0.0),
            "lynae_target_tune_shift_state": data.get("target_tune_shift_state"),
            "lynae_target_tune_shift_remaining": float(data.get("target_tune_shift_remaining", 0.0) or 0.0),
            "lynae_spray_paint_window_remaining": float(data.get("spray_paint_window_remaining", 0.0) or 0.0),
            "lynae_visual_impact_cooldown_remaining": float(data.get("visual_impact_cooldown_remaining", 0.0) or 0.0),
            "lynae_to_vivid_tomorrow_window_remaining": float(
                data.get("to_vivid_tomorrow_window_remaining", 0.0) or 0.0
            ),
        }
        for field, value in fields.items():
            if hasattr(result, field):
                setattr(result, field, value)
