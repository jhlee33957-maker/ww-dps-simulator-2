from __future__ import annotations

from typing import Any

from characters.base import CharacterMechanic
from simulator.buff_system import apply_buff
from simulator.models import BuffData


INTERFERED_MARKER_BUFF_ID = "mornye_interfered_marker_damage_amp"
MORNYE_LIBERATION_ACTION_ID = "mornye_liberation_critical_protocol"
MORNYE_HEAVY_INVERSION_ACTION_ID = "mornye_heavy_inversion"
MORNYE_POLICY_SKILL_ACTION_ID = "mornye_resonance_skill"
MORNYE_EXPECTATION_ERROR_ACTION_ID = "mornye_skill_expectation_error"
MORNYE_OPTIMAL_SOLUTION_ACTION_ID = "mornye_skill_optimal_solution"
MORNYE_DISTRIBUTED_ARRAY_ACTION_ID = "mornye_skill_distributed_array"
MORNYE_EXPECTATION_ERROR_MODES = {
    "expectation_error_only",
    "dry_run_success_candidate",
    "always_success",
}


def get_energy_regen(character_state: Any | None = None, character_data: Any | None = None) -> float:
    if character_data is not None:
        return max(0.0, float(getattr(character_data, "energy_regen", 1.0) or 1.0))
    if isinstance(character_state, dict):
        return max(0.0, float(character_state.get("energy_regen", 1.0) or 1.0))
    return 1.0


def get_energy_regen_excess_percent(character_state: Any | None = None, character_data: Any | None = None) -> float:
    return max(0.0, (get_energy_regen(character_state, character_data) - 1.0) * 100.0)


def get_interfered_damage_amp(character_state: Any | None = None, character_data: Any | None = None) -> float:
    return min(get_energy_regen_excess_percent(character_state, character_data) * 0.0025, 0.40)


def get_liberation_crit_bonuses(character_state: Any | None = None, character_data: Any | None = None) -> tuple[float, float]:
    excess_percent = get_energy_regen_excess_percent(character_state, character_data)
    crit_rate_bonus = min(excess_percent * 0.005, 0.80)
    crit_dmg_bonus = min(excess_percent * 0.01, 1.60)
    return crit_rate_bonus, crit_dmg_bonus


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
        "energy_regen": 1.0,
        "mornye_expectation_error_mode": "expectation_error_only",
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
        elif selected_action.id == MORNYE_POLICY_SKILL_ACTION_ID:
            if data["mode"] == "wide_field_observation":
                resolved_id = MORNYE_DISTRIBUTED_ARRAY_ACTION_ID
            else:
                expectation_error_mode = self._expectation_error_mode(state)
                resolved_id = (
                    MORNYE_OPTIMAL_SOLUTION_ACTION_ID
                    if expectation_error_mode == "always_success"
                    else MORNYE_EXPECTATION_ERROR_ACTION_ID
                )
        elif selected_action.id == "mornye_resonance_liberation":
            resolved_id = "mornye_liberation_critical_protocol"

        try:
            return actions_by_id[resolved_id]
        except KeyError as exc:
            raise KeyError(f"Mornye resolved {selected_action.id!r} to missing action {resolved_id!r}.") from exc

    def is_action_available(self, state: Any, action: Any) -> bool:
        data = self._state(state)
        if action.id == MORNYE_HEAVY_INVERSION_ACTION_ID:
            return data["mode"] == "wide_field_observation" and data["relative_momentum"] >= data["relative_momentum_cap"]
        return True

    def get_action_stat_modifiers(self, state: Any, action: Any, characters: dict[str, Any] | None = None) -> dict[str, float]:
        if action.id != MORNYE_LIBERATION_ACTION_ID or not self._energy_regen_scaling_enabled(state):
            return {}
        character_data = (characters or {}).get(self.character_id)
        crit_rate_bonus, crit_dmg_bonus = get_liberation_crit_bonuses(self._state(state), character_data)
        return {
            "crit_rate": crit_rate_bonus,
            "crit_damage": crit_dmg_bonus,
        }

    def get_action_log_fields(self, state: Any, action: Any, characters: dict[str, Any] | None = None) -> dict[str, Any]:
        fields: dict[str, Any] = {}
        if action.id == MORNYE_LIBERATION_ACTION_ID and self._energy_regen_scaling_enabled(state):
            character_data = (characters or {}).get(self.character_id)
            crit_rate_bonus, crit_dmg_bonus = get_liberation_crit_bonuses(self._state(state), character_data)
            fields.update(
                {
                    "mornye_er_excess_percent": get_energy_regen_excess_percent(self._state(state), character_data),
                    "mornye_liberation_crit_rate_bonus": crit_rate_bonus,
                    "mornye_liberation_crit_dmg_bonus": crit_dmg_bonus,
                }
            )
        if action.id in {
            MORNYE_EXPECTATION_ERROR_ACTION_ID,
            MORNYE_OPTIMAL_SOLUTION_ACTION_ID,
            MORNYE_DISTRIBUTED_ARRAY_ACTION_ID,
        }:
            fields.update(self._resonance_skill_route_log_fields(state, action))
        return fields

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
        if action.id == MORNYE_HEAVY_INVERSION_ACTION_ID:
            self._resolve_interfered_marker(state, result)
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
            "energy_regen": data.get("energy_regen", 1.0),
            "expectation_error_mode": self._expectation_error_mode(state),
            "interfered_marker_mode": self._interfered_marker_config(state).get("mode", "disabled"),
            "interfered_marker_active": self._active_interfered_marker(state) is not None,
            "last_resolved_action_id": data["last_resolved_action_id"],
        }

    def get_display_state(self, character_state: Any) -> dict[str, Any]:
        data = dict(character_state) if isinstance(character_state, dict) else {}
        energy_regen = get_energy_regen(data)
        excess_percent = get_energy_regen_excess_percent(data)
        crit_rate_bonus, crit_dmg_bonus = get_liberation_crit_bonuses(data)
        return {
            "Mode": data.get("mode", "baseline"),
            "Energy Regen": f"{energy_regen * 100.0:.0f}%",
            "ER Excess": f"{excess_percent:.0f}%",
            "Interfered Amp Potential": f"{get_interfered_damage_amp(data) * 100.0:.1f}%",
            "Liberation CR Bonus": f"{crit_rate_bonus * 100.0:.1f}%",
            "Liberation CD Bonus": f"{crit_dmg_bonus * 100.0:.1f}%",
            "Interfered Marker Mode": data.get("mornye_interfered_marker_mode", "disabled"),
            "Expectation Error Mode": data.get("mornye_expectation_error_mode", "expectation_error_only"),
            "Active Interfered Marker": bool(data.get("mornye_interfered_marker_active", False)),
            "Rest Mass Energy": f"{float(data.get('rest_mass_energy', 0.0)):.1f}/{float(data.get('rest_mass_energy_cap', 100.0)):.0f}",
            "Relative Momentum": f"{float(data.get('relative_momentum', 0.0)):.1f}/{float(data.get('relative_momentum_cap', 100.0)):.0f}",
            "Wide Field Observation": f"{float(data.get('wide_field_observation_remaining', 0.0)):.1f}s",
            "Syntony Field": f"{float(data.get('syntony_field_remaining', 0.0)):.1f}s",
            "High Syntony Field": f"{float(data.get('high_syntony_field_remaining', 0.0)):.1f}s",
            "Observation Marker": bool(data.get("observation_marker_active", False)),
        }

    def _state(self, state: Any) -> dict[str, Any]:
        self.initialize_state(state)
        data = state.character_mechanics_state[self.character_id]
        character_data = getattr(state, "character_data", {}).get(self.character_id) if hasattr(state, "character_data") else None
        data["mornye_interfered_marker_mode"] = self._interfered_marker_config(state).get("mode", "disabled")
        data["mornye_interfered_marker_active"] = self._active_interfered_marker(state) is not None
        data["mornye_expectation_error_mode"] = self._expectation_error_mode(state)
        if character_data is not None:
            data["energy_regen"] = get_energy_regen(data, character_data)
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
        data["energy_regen"] = get_energy_regen(data)
        data["mornye_expectation_error_mode"] = (
            data["mornye_expectation_error_mode"]
            if data["mornye_expectation_error_mode"] in MORNYE_EXPECTATION_ERROR_MODES
            else "expectation_error_only"
        )

    def _energy_regen_scaling_enabled(self, state: Any) -> bool:
        config = self._mornye_mechanics_config(state)
        return bool((config.get("energy_regen_scaling") or {}).get("enabled", True))

    def _interfered_marker_config(self, state: Any) -> dict[str, Any]:
        config = self._mornye_mechanics_config(state)
        marker_config = dict(config.get("interfered_marker") or {})
        marker_config.setdefault("mode", "disabled")
        marker_config.setdefault("duration", 30.0)
        return marker_config

    def _mornye_mechanics_config(self, state: Any) -> dict[str, Any]:
        mechanics_config = getattr(state, "mechanics_config", {}) or {}
        return dict((mechanics_config.get("mornye") or {}))

    def _expectation_error_mode(self, state: Any) -> str:
        config = self._mornye_mechanics_config(state)
        nested = config.get("expectation_error") or {}
        mode = str(
            config.get(
                "mornye_expectation_error_mode",
                nested.get("mode", "expectation_error_only") if isinstance(nested, dict) else "expectation_error_only",
            )
        )
        return mode if mode in MORNYE_EXPECTATION_ERROR_MODES else "expectation_error_only"

    def _resonance_skill_route_log_fields(self, state: Any, action: Any) -> dict[str, Any]:
        mode = self._expectation_error_mode(state)
        if action.id == MORNYE_DISTRIBUTED_ARRAY_ACTION_ID:
            return {
                "base_policy_action_id": MORNYE_POLICY_SKILL_ACTION_ID,
                "mornye_expectation_error_mode": mode,
                "optimal_solution_triggered": False,
                "optimal_solution_trigger_reason": "wide_field_observation_uses_distributed_array",
                "optimal_solution_candidate_id": None,
                "gp_success_modeled": False,
                "implementation_status": "wfo_distributed_array",
            }
        if action.id == MORNYE_OPTIMAL_SOLUTION_ACTION_ID:
            return {
                "base_policy_action_id": MORNYE_POLICY_SKILL_ACTION_ID,
                "mornye_expectation_error_mode": mode,
                "optimal_solution_triggered": True,
                "optimal_solution_trigger_reason": "simplified_always_success",
                "optimal_solution_candidate_id": MORNYE_OPTIMAL_SOLUTION_ACTION_ID,
                "gp_success_modeled": True,
                "implementation_status": "simplified_always_success",
            }
        reason = "dry_run_success_candidate" if mode == "dry_run_success_candidate" else "gp_success_not_modeled"
        status = "dry_run_success_candidate" if mode == "dry_run_success_candidate" else "conservative_gp_success_not_modeled"
        return {
            "base_policy_action_id": MORNYE_POLICY_SKILL_ACTION_ID,
            "mornye_expectation_error_mode": mode,
            "optimal_solution_triggered": False,
            "optimal_solution_trigger_reason": reason,
            "optimal_solution_candidate_id": MORNYE_OPTIMAL_SOLUTION_ACTION_ID,
            "gp_success_modeled": False,
            "implementation_status": status,
        }

    def _resolve_interfered_marker(self, state: Any, result: Any) -> None:
        config = self._interfered_marker_config(state)
        mode = str(config.get("mode", "disabled"))
        data = self._state(state)
        amp = get_interfered_damage_amp(data)
        result.mornye_interfered_marker_mode = mode
        result.mornye_interfered_amp = amp
        data["mornye_interfered_marker_mode"] = mode
        data["mornye_interfered_marker_active"] = False
        if mode == "disabled":
            return
        if mode == "dry_run":
            return
        if mode != "simplified_on_inversion":
            return
        duration = max(0.001, float(config.get("duration", 30.0) or 30.0))
        buff = BuffData(
            id=INTERFERED_MARKER_BUFF_ID,
            name="Mornye Interfered Marker Damage Amp (Simplified)",
            duration=duration,
            modifier_type="dmg_taken",
            value=amp,
            target="enemy",
            target_scope="enemy",
            metadata={
                "source_character_id": self.character_id,
                "source_action_id": MORNYE_HEAVY_INVERSION_ACTION_ID,
                "dynamic_value": amp,
                "implementation_status": "simplified_v1",
                "source_note": "Simplified optional Mornye Interfered Marker amp applied on Heavy Inversion; full Tune conversion is not implemented.",
            },
        )
        apply_buff(state, buff, self.character_id)
        result.mornye_interfered_marker_applied = True
        if INTERFERED_MARKER_BUFF_ID not in result.applied_buffs:
            result.applied_buffs.append(INTERFERED_MARKER_BUFF_ID)
        result.active_buffs = [buff.buff_id for buff in state.active_buffs if buff.remaining_duration > 0.0]
        data["mornye_interfered_marker_active"] = True

    def _active_interfered_marker(self, state: Any) -> Any | None:
        for active in getattr(state, "active_buffs", []) or []:
            if active.buff_id == INTERFERED_MARKER_BUFF_ID and active.remaining_duration > 0.0:
                return active
        return None
