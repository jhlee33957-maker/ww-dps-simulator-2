from __future__ import annotations

from typing import Any

from characters.base import CharacterMechanic


class MornyeMechanic(CharacterMechanic):
    character_id = "mornye"

    _DEFAULT_STATE: dict[str, Any] = {
        "mode": "baseline",
        "baseline_combo_stage": 1,
        "wfo_combo_stage": 1,
        "rest_mass_energy": 0.0,
        "rest_mass_energy_cap": 100.0,
        "relative_momentum": 0.0,
        "relative_momentum_cap": 100.0,
        "wide_field_observation_remaining": 0.0,
        "syntony_field_remaining": 0.0,
        "high_syntony_field_remaining": 0.0,
        "observation_marker_active": False,
        "observation_marker_remaining": 0.0,
        "last_resolved_action_id": None,
    }

    _BASELINE_BASIC_BY_STAGE = {
        1: "mornye_basic_stage_1",
        2: "mornye_basic_stage_2",
        3: "mornye_basic_stage_3",
        4: "mornye_basic_stage_4",
    }
    _WFO_BASIC_BY_STAGE = {
        1: "mornye_wfo_basic_stage_1",
        2: "mornye_wfo_basic_stage_2",
        3: "mornye_wfo_basic_stage_3",
    }

    def initialize_state(self, state: Any) -> None:
        data = state.character_mechanics_state.setdefault(self.character_id, dict(self._DEFAULT_STATE))
        for key, value in self._DEFAULT_STATE.items():
            data.setdefault(key, value)
        self._clamp(data)

    def resolve_action(self, state: Any, selected_action: Any, actions_by_id: dict[str, Any]) -> Any:
        data = self._state(state)
        resolved_id = selected_action.id

        if selected_action.id == "mornye_basic_attack":
            if data["mode"] == "wide_field_observation":
                resolved_id = self._WFO_BASIC_BY_STAGE[int(data["wfo_combo_stage"])]
            else:
                resolved_id = self._BASELINE_BASIC_BY_STAGE[int(data["baseline_combo_stage"])]
        elif selected_action.id == "mornye_heavy_attack":
            if data["mode"] == "wide_field_observation":
                resolved_id = "mornye_heavy_inversion"
            elif data["rest_mass_energy"] >= data["rest_mass_energy_cap"]:
                resolved_id = "mornye_heavy_geopotential_shift"
            else:
                resolved_id = "mornye_heavy_attack_normal"
        elif selected_action.id == "mornye_resonance_skill":
            resolved_id = (
                "mornye_skill_distributed_array"
                if data["mode"] == "wide_field_observation"
                else "mornye_skill_optimal_solution"
            )
        elif selected_action.id == "mornye_resonance_liberation":
            resolved_id = "mornye_liberation_critical_protocol"

        try:
            return actions_by_id[resolved_id]
        except KeyError as exc:
            raise KeyError(f"Mornye resolved {selected_action.id!r} to missing action {resolved_id!r}.") from exc

    def is_action_available(self, state: Any, action: Any) -> bool:
        data = self._state(state)
        if action.id == "mornye_heavy_inversion":
            return data["mode"] == "wide_field_observation" and data["relative_momentum"] >= data["relative_momentum_cap"]
        return True

    def resolve_incoming_qte_transition_action(
        self,
        character_state: Any,
        transition_config: dict[str, Any],
    ) -> tuple[str | None, list[str]]:
        intro_config = (
            (transition_config.get("characters") or {})
            .get(self.character_id, {})
            .get("intro_qte", {})
        )
        transition_actions = intro_config.get("transition_actions") or {}
        action_id = transition_actions.get("default") or transition_actions.get("intro")
        return action_id, [] if action_id else ["mornye_intro_transition_action_missing"]

    def after_action(self, state: Any, action: Any, result: Any) -> None:
        data = self._state(state)
        effects = action.mechanic_effects or {}

        if "rest_mass_energy_delta" in effects:
            data["rest_mass_energy"] += float(effects["rest_mass_energy_delta"])
        if "relative_momentum_delta" in effects:
            data["relative_momentum"] += float(effects["relative_momentum_delta"])
        if effects.get("consume_rest_mass_energy") or effects.get("clear_rest_mass_energy"):
            data["rest_mass_energy"] = 0.0
        if effects.get("consume_relative_momentum"):
            data["relative_momentum"] = 0.0
        if "set_mode" in effects:
            data["mode"] = str(effects["set_mode"])
        if "wide_field_observation_duration" in effects:
            data["wide_field_observation_remaining"] = float(effects["wide_field_observation_duration"])
            data["mode"] = "wide_field_observation" if data["wide_field_observation_remaining"] > 0.0 else "baseline"
        if "set_wide_field_observation_remaining" in effects:
            data["wide_field_observation_remaining"] = float(effects["set_wide_field_observation_remaining"])
            data["mode"] = "wide_field_observation" if data["wide_field_observation_remaining"] > 0.0 else "baseline"
        if "syntony_field_duration" in effects:
            data["syntony_field_remaining"] = float(effects["syntony_field_duration"])
        if "set_syntony_field_remaining" in effects:
            data["syntony_field_remaining"] = float(effects["set_syntony_field_remaining"])
        if effects.get("upgrade_syntony_to_high") and data["syntony_field_remaining"] > 0.0:
            data["syntony_field_remaining"] = 0.0
            data["high_syntony_field_remaining"] = float(effects.get("high_syntony_field_duration", 25.0))
        elif "high_syntony_field_duration" in effects and effects.get("force_high_syntony_field"):
            data["high_syntony_field_remaining"] = float(effects["high_syntony_field_duration"])
        if "observation_marker_duration" in effects:
            data["observation_marker_remaining"] = float(effects["observation_marker_duration"])
            data["observation_marker_active"] = data["observation_marker_remaining"] > 0.0
        if "set_baseline_combo_stage" in effects:
            data["baseline_combo_stage"] = int(effects["set_baseline_combo_stage"])
        if "set_wfo_combo_stage" in effects:
            data["wfo_combo_stage"] = int(effects["set_wfo_combo_stage"])

        self._clamp(data)
        data["last_resolved_action_id"] = action.id

    def advance_time(self, state: Any, elapsed_time: float) -> None:
        data = self._state(state)
        for key in (
            "wide_field_observation_remaining",
            "syntony_field_remaining",
            "high_syntony_field_remaining",
            "observation_marker_remaining",
        ):
            if data[key] > 0.0:
                data[key] = max(0.0, float(data[key]) - elapsed_time)
        if data["wide_field_observation_remaining"] <= 0.0 and data["mode"] == "wide_field_observation":
            data["mode"] = "baseline"
            data["relative_momentum"] = 0.0
            data["wfo_combo_stage"] = 1
        data["observation_marker_active"] = data["observation_marker_remaining"] > 0.0
        self._clamp(data)

    def get_observation_values(self, state: Any) -> list[float]:
        data = self._state(state)
        return [
            1.0 if data["mode"] == "wide_field_observation" else 0.0,
            float(data["rest_mass_energy"]) / float(data["rest_mass_energy_cap"]),
            float(data["relative_momentum"]) / float(data["relative_momentum_cap"]),
            float(data["wide_field_observation_remaining"]) / 30.0,
            float(data["syntony_field_remaining"]) / 25.0,
            float(data["high_syntony_field_remaining"]) / 25.0,
            1.0 if data["observation_marker_active"] else 0.0,
        ]

    def get_observation_labels(self) -> list[str]:
        return [
            "mornye.mode_is_wide_field_observation",
            "mornye.rest_mass_energy",
            "mornye.relative_momentum",
            "mornye.wide_field_observation_remaining",
            "mornye.syntony_field_remaining",
            "mornye.high_syntony_field_remaining",
            "mornye.observation_marker_active",
        ]

    def get_debug_state(self, state: Any) -> dict[str, Any]:
        data = self._state(state)
        return {
            "mode": data["mode"],
            "baseline_combo_stage": data["baseline_combo_stage"],
            "wfo_combo_stage": data["wfo_combo_stage"],
            "rest_mass_energy": data["rest_mass_energy"],
            "relative_momentum": data["relative_momentum"],
            "wide_field_observation_remaining": data["wide_field_observation_remaining"],
            "syntony_field_remaining": data["syntony_field_remaining"],
            "high_syntony_field_remaining": data["high_syntony_field_remaining"],
            "observation_marker_active": data["observation_marker_active"],
            "observation_marker_remaining": data["observation_marker_remaining"],
            "last_resolved_action_id": data["last_resolved_action_id"],
        }

    def get_display_state(self, character_state: Any) -> dict[str, Any]:
        data = dict(character_state) if isinstance(character_state, dict) else {}
        return {
            "Mode": data.get("mode", "baseline"),
            "Rest Mass Energy": f"{float(data.get('rest_mass_energy', 0.0)):.1f}/{float(data.get('rest_mass_energy_cap', 100.0)):.0f}",
            "Relative Momentum": f"{float(data.get('relative_momentum', 0.0)):.1f}/{float(data.get('relative_momentum_cap', 100.0)):.0f}",
            "Wide Field Observation": f"{float(data.get('wide_field_observation_remaining', 0.0)):.1f}s",
            "Syntony Field": f"{float(data.get('syntony_field_remaining', 0.0)):.1f}s",
            "High Syntony Field": f"{float(data.get('high_syntony_field_remaining', 0.0)):.1f}s",
            "Observation Marker": bool(data.get("observation_marker_active", False)),
        }

    def _state(self, state: Any) -> dict[str, Any]:
        self.initialize_state(state)
        return state.character_mechanics_state[self.character_id]

    def _clamp(self, data: dict[str, Any]) -> None:
        data["mode"] = "wide_field_observation" if data["mode"] == "wide_field_observation" else "baseline"
        data["baseline_combo_stage"] = max(1, min(4, int(data["baseline_combo_stage"])))
        data["wfo_combo_stage"] = max(1, min(3, int(data["wfo_combo_stage"])))
        data["rest_mass_energy_cap"] = max(1.0, float(data["rest_mass_energy_cap"]))
        data["relative_momentum_cap"] = max(1.0, float(data["relative_momentum_cap"]))
        data["rest_mass_energy"] = max(0.0, min(float(data["rest_mass_energy_cap"]), float(data["rest_mass_energy"])))
        data["relative_momentum"] = max(0.0, min(float(data["relative_momentum_cap"]), float(data["relative_momentum"])))
        for key in (
            "wide_field_observation_remaining",
            "syntony_field_remaining",
            "high_syntony_field_remaining",
            "observation_marker_remaining",
        ):
            data[key] = max(0.0, float(data[key]))
        data["observation_marker_active"] = bool(data["observation_marker_active"]) and data["observation_marker_remaining"] > 0.0
