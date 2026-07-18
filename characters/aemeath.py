from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from characters.base import CharacterMechanic
from simulator.generated_damage import GeneratedDamagePacket, packet_from_mapping
from simulator.mechanic_events import (
    FUSION_EFFECT_DURATION_SECONDS,
    apply_aemeath_fusion_effect_event,
    aemeath_resonance_mode_from_config,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORTE_CONFIG_PATH = PROJECT_ROOT / "data" / "character_mechanic_effects" / "aemeath_forte_circuit.json"
RUPTUROUS_TRAIL_SOURCE_REF = "\u89d2\u8272-\u5973!2844"
RUPTUROUS_TRAIL_MAX_STACKS = 30
RUPTUROUS_TRAIL_GAIN_PER_RESPONSE = 10
RUPTUROUS_TRAIL_DURATION = 30.0
RUPTUROUS_TRAIL_BONUS_PER_STACK = 0.04


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
        "heavenfall_unbound_remaining": 0.0,
        "stardust_resonance_remaining": 0.0,
        "starlume_acceleration_remaining": 0.0,
        "instant_response": False,
        "finale_available": False,
        "instant_response_consumed": False,
        "last_resolved_action_id": None,
        "sync_strike_window_type": None,
        "sync_strike_window_remaining": 0,
        "overdrive_form_switch_window_remaining": 0,
        "fusion_trail_stacks": 0,
        "fusion_trail_remaining": 0.0,
        "fusion_trail_max_stacks": 60,
        "fusion_effect_stacks": 0,
        "fusion_effect_remaining": 0.0,
        "fusion_effect_max_stacks": 10,
        "fusion_application_last_trigger_time": {},
        "fusion_trail_event_log": [],
        "forte_enhancement_stacks": 0,
        "forte_enhancement_remaining": 0.0,
        "forte_enhancement_max_stacks": 2,
        "trail_no_cost_remaining": 0.0,
        "last_seraphic_duet_consumed_rupturous_trail_stacks": 0,
        "last_seraphic_duet_consumed_fusion_trail_stacks": 0,
        "last_seraphic_duet_generated_damage": 0.0,
        "last_seraphic_duet_followup_variant": None,
        "last_seraphic_duet_followup_repeat_count": 0,
        "last_seraphic_duet_followup_multiplier": 0.0,
        "last_seraphic_duet_followup_damage": 0.0,
        "last_seraphic_duet_followup_source_rows": [],
        "last_seraphic_duet_followup_source_status": None,
        "last_seraphic_duet_forte_enhancement_stacks_before": 0,
        "last_seraphic_duet_forte_enhancement_stacks_consumed": 0,
        "last_seraphic_duet_forte_enhancement_stacks_after": 0,
        "last_seraphic_duet_trail_no_cost_consumed": False,
        "last_seraphic_duet_trail_stack_snapshot": 0,
        "last_seraphic_duet_trail_stack_factor": 1.0,
        "last_seraphic_duet_trail_preservation_active": False,
        "last_seraphic_duet_trail_preservation_after": False,
        "last_seraphic_duet_trail_consumed": False,
        "last_seraphic_duet_total_extra_tune_multiplier": 0.0,
        "last_seraphic_duet_fusion_effect_stacks_before": 0,
        "last_seraphic_duet_fusion_effect_stacks_after": 0,
        "last_seraphic_duet_fusion_settlement_multiplier": 0.0,
        "forte_unresolved_runtime_notes": [],
    }

    _ARMAMENT_MERGE_WINDOW_ACTIONS = {
        "aemeath_basic_form_stage_2",
        "aemeath_basic_form_stage_3",
        "aemeath_basic_form_stage_4",
        "aemeath_heavy_aemeath_charged_1",
        "aemeath_heavy_aemeath_charged_2",
    }
    _CALL_OF_DAWN_WINDOW_ACTIONS = {
        "aemeath_mech_basic_stage_2",
        "aemeath_mech_basic_stage_3",
        "aemeath_mech_basic_stage_4",
        "aemeath_heavy_mech_charged_1",
        "aemeath_heavy_mech_charged_2",
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

        if selected_action.id in {"aemeath_resonance_skill", "aemeath_resonance_liberation"} and self._is_finale_ready(data):
            resolved_id = "aemeath_heavenfall_finale"
        elif selected_action.id == "aemeath_basic_attack":
            if data["form"] == "mech":
                resolved_id = self._MECH_BASIC_BY_STAGE[int(data["mech_combo_stage"])]
            else:
                resolved_id = self._AEMEATH_BASIC_BY_STAGE[int(data["aemeath_combo_stage"])]
        elif selected_action.id == "aemeath_resonance_skill":
            if data["seraphic_duo_remaining"] > 0.0 and data["synchronization_rate"] >= 100.0:
                resolved_id = "aemeath_seraphic_duet_encore" if data["form"] == "mech" else "aemeath_seraphic_duet_overturn"
            elif data["sync_strike_window_type"] == "armament_merge":
                resolved_id = "aemeath_sync_strike_armament_merge"
            elif data["sync_strike_window_type"] == "call_of_dawn":
                resolved_id = "aemeath_sync_strike_call_of_dawn"
            elif data["overdrive_form_switch_window_remaining"] > 0 and data["form"] == "mech":
                resolved_id = "aemeath_form_switch_to_aemeath_after_overdrive"
            else:
                resolved_id = "aemeath_form_switch_to_aemeath_normal" if data["form"] == "mech" else "aemeath_form_switch_to_mech_normal"
        elif selected_action.id == "aemeath_resonance_liberation":
            if data["heavenfall_unbound"]:
                resolved_id = "aemeath_heavenfall_finale"
            else:
                resolved_id = "aemeath_liberation_overdrive"
        elif selected_action.id == "aemeath_heavy_attack":
            if data["form"] == "mech":
                resolved_id = "aemeath_heavy_mech_charged_2" if data["instant_response"] else "aemeath_heavy_mech_charged_1"
            else:
                resolved_id = "aemeath_heavy_aemeath_charged_2" if data["instant_response"] else "aemeath_heavy_aemeath_charged_1"

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
        if action_id.startswith("aemeath_sync_strike_"):
            return True
        if action_id.startswith("aemeath_heavy_"):
            return True
        if action_id == "aemeath_seraphic_duet_overturn":
            return (
                data["form"] == "aemeath"
                and data["seraphic_duo_remaining"] > 0.0
                and data["synchronization_rate"] >= 100.0
            )
        if action_id == "aemeath_seraphic_duet_encore":
            return (
                data["form"] == "mech"
                and data["seraphic_duo_remaining"] > 0.0
                and data["synchronization_rate"] >= 100.0
            )
        if action_id == "aemeath_heavenfall_finale":
            return self._is_finale_ready(data)
        if action_id == "aemeath_liberation_overdrive":
            return not data["heavenfall_unbound"]
        return True

    def get_action_damage_multiplier(self, state: Any, action: Any) -> float:
        data = self._state(state)
        if action.id in {"aemeath_heavy_aemeath_charged_2", "aemeath_heavy_mech_charged_2"} and data["instant_response"]:
            return 3.0
        return 1.0

    def get_generated_damage_packets(
        self,
        state: Any,
        action: Any,
        *,
        action_time: float,
        combat_time_cost: float,
        combat_start_time: float,
        characters: dict[str, Any],
        buffs: dict[str, Any],
        force_active_buff_ids: set[str],
        mechanic_event_log_fields: dict[str, Any],
        echo_set_log_fields: dict[str, Any],
        weapon_definitions: dict[str, Any],
    ) -> list[GeneratedDamagePacket]:
        data = self._state(state)
        data["last_seraphic_duet_generated_damage"] = 0.0
        data["last_seraphic_duet_followup_variant"] = None
        data["last_seraphic_duet_followup_repeat_count"] = 0
        data["last_seraphic_duet_followup_multiplier"] = 0.0
        data["last_seraphic_duet_followup_damage"] = 0.0
        data["last_seraphic_duet_followup_source_rows"] = []
        data["last_seraphic_duet_followup_source_status"] = None
        data["last_seraphic_duet_consumed_rupturous_trail_stacks"] = 0
        data["last_seraphic_duet_consumed_fusion_trail_stacks"] = 0
        data["last_seraphic_duet_forte_enhancement_stacks_before"] = int(data.get("forte_enhancement_stacks", 0) or 0)
        data["last_seraphic_duet_forte_enhancement_stacks_consumed"] = 0
        data["last_seraphic_duet_forte_enhancement_stacks_after"] = int(data.get("forte_enhancement_stacks", 0) or 0)
        data["last_seraphic_duet_trail_no_cost_consumed"] = False
        data["last_seraphic_duet_trail_stack_snapshot"] = 0
        data["last_seraphic_duet_trail_stack_factor"] = 1.0
        data["last_seraphic_duet_trail_preservation_active"] = False
        data["last_seraphic_duet_trail_preservation_after"] = False
        data["last_seraphic_duet_trail_consumed"] = False
        data["last_seraphic_duet_total_extra_tune_multiplier"] = 0.0
        data["last_seraphic_duet_fusion_effect_stacks_before"] = int(data.get("fusion_effect_stacks", 0) or 0)
        data["last_seraphic_duet_fusion_effect_stacks_after"] = int(data.get("fusion_effect_stacks", 0) or 0)
        data["last_seraphic_duet_fusion_settlement_multiplier"] = 0.0
        if aemeath_resonance_mode_from_config(getattr(state, "mechanics_config", {}) or {}) == "fusion_burst":
            self._ensure_fusion_minimum_effect(state)
        if action.id in {"aemeath_sync_strike_armament_merge", "aemeath_sync_strike_call_of_dawn"}:
            return self._enhanced_skill_generated_packets(state, action)
        if action.id not in {"aemeath_seraphic_duet_overturn", "aemeath_seraphic_duet_encore"}:
            return []

        mode = aemeath_resonance_mode_from_config(getattr(state, "mechanics_config", {}) or {})
        config = self._forte_config()
        mode_config = ((config.get("modes") or {}).get(mode) or {}) if isinstance(config, dict) else {}
        followups = list(mode_config.get("seraphic_duet_followups", []))
        if not followups:
            note = f"aemeath_forte_{mode}_seraphic_duet_followup_unresolved_no_runtime_effect"
            data["forte_unresolved_runtime_notes"] = sorted(set([*data.get("forte_unresolved_runtime_notes", []), note]))
            data["last_seraphic_duet_followup_source_status"] = "unresolved_no_runtime_effect"
            return []

        enhanced_available = int(data.get("forte_enhancement_stacks", 0) or 0) > 0
        wanted_variant = "enhanced" if enhanced_available else "normal"
        packet_def = next((item for item in followups if item.get("variant") == wanted_variant), None)
        if packet_def is None:
            packet_def = next((item for item in followups if item.get("variant") == "normal"), None)
        if packet_def is None:
            return []

        packet_data = dict(packet_def)
        packet_data["source_action_id"] = action.id
        base_per_hit_multiplier = float(packet_data.get("tune_multiplier", packet_data.get("source_multiplier", 0.0)) or 0.0)
        repeat_count = int(packet_data.get("repeat_count", 1) or 1)
        trail_cap = self._rupturous_trail_cap(state)
        trail_stack_snapshot = (
            max(0, min(trail_cap, int(getattr(state, "rupturous_trail_stacks", 0) or 0)))
            if mode == "tune_rupture"
            else 0
        )
        trail_stack_factor = 1.0 + RUPTUROUS_TRAIL_BONUS_PER_STACK * trail_stack_snapshot
        scaled_per_hit_multiplier = base_per_hit_multiplier * trail_stack_factor
        total_extra_tune_multiplier = scaled_per_hit_multiplier * repeat_count
        packet_data["tune_multiplier"] = scaled_per_hit_multiplier
        packet_data["source_multiplier"] = scaled_per_hit_multiplier
        packet = packet_from_mapping(packet_data)
        packets = [packet]
        data["last_seraphic_duet_followup_variant"] = packet.variant
        data["last_seraphic_duet_followup_repeat_count"] = packet.repeat_count
        data["last_seraphic_duet_followup_multiplier"] = float(packet.source_multiplier or packet.tune_multiplier or 0.0)
        data["last_seraphic_duet_followup_source_rows"] = list(packet.source_rows)
        data["last_seraphic_duet_followup_source_status"] = packet.source_status
        data["last_seraphic_duet_trail_stack_snapshot"] = trail_stack_snapshot
        data["last_seraphic_duet_trail_stack_factor"] = trail_stack_factor
        data["last_seraphic_duet_total_extra_tune_multiplier"] = total_extra_tune_multiplier
        if packet.variant == "enhanced" and packet.runtime_applicable:
            before = int(data.get("forte_enhancement_stacks", 0) or 0)
            data["forte_enhancement_stacks"] = max(0, before - 1)
            data["last_seraphic_duet_forte_enhancement_stacks_before"] = before
            data["last_seraphic_duet_forte_enhancement_stacks_consumed"] = 1 if before > 0 else 0
            data["last_seraphic_duet_forte_enhancement_stacks_after"] = int(data.get("forte_enhancement_stacks", 0) or 0)
        preservation_active = float(data.get("trail_no_cost_remaining", 0.0) or 0.0) > 0.0
        data["last_seraphic_duet_trail_preservation_active"] = preservation_active
        if preservation_active:
            data["trail_no_cost_remaining"] = 0.0
            data["last_seraphic_duet_trail_no_cost_consumed"] = True
            data["last_seraphic_duet_trail_preservation_after"] = False
            data["last_seraphic_duet_trail_consumed"] = False
            data["last_seraphic_duet_consumed_rupturous_trail_stacks"] = 0
        elif mode == "tune_rupture":
            data["last_seraphic_duet_trail_preservation_after"] = False
            data["last_seraphic_duet_trail_consumed"] = trail_stack_snapshot > 0
            data["last_seraphic_duet_consumed_rupturous_trail_stacks"] = trail_stack_snapshot
            if trail_stack_snapshot > 0:
                state.rupturous_trail_stacks = 0
                state.rupturous_trail_remaining = 0.0
        if not any(packet.runtime_applicable for packet in packets):
            data["forte_unresolved_runtime_notes"] = sorted(
                set(
                    [
                        *data.get("forte_unresolved_runtime_notes", []),
                        "aemeath_seraphic_duet_followup_damage_unresolved_no_runtime_effect",
                    ]
                )
            )
            data["last_seraphic_duet_followup_source_status"] = "unresolved_no_runtime_effect"
        return packets

    def _enhanced_skill_generated_packets(self, state: Any, action: Any) -> list[GeneratedDamagePacket]:
        """Emit the workbook-backed Tune packet selected by the existing Forte state."""
        data = self._state(state)
        account = state.character_mechanics_state.get("_account_constellation", {})
        sequence = int(account.get("aemeath_sequence", 0) or 0)
        if sequence < 2:
            return []
        mode = aemeath_resonance_mode_from_config(getattr(state, "mechanics_config", {}) or {})
        if mode == "tune_rupture":
            followups = list(
                (((self._forte_config().get("modes") or {}).get(mode) or {}).get("seraphic_duet_followups") or [])
            )
            wanted = "enhanced" if int(data.get("forte_enhancement_stacks", 0) or 0) > 0 else "normal"
            packet_data = next((dict(item) for item in followups if item.get("variant") == wanted), None)
            if packet_data is None:
                return []
            cap = self._rupturous_trail_cap(state)
            snapshot = max(0, min(cap, int(state.rupturous_trail_stacks or 0)))
            preservation = float(data.get("trail_no_cost_remaining", 0.0) or 0.0) > 0.0
            packet_data["source_action_id"] = action.id
            packet_data["tune_multiplier"] = float(packet_data["tune_multiplier"]) * (1.0 + 0.04 * snapshot)
            packet_data["source_multiplier"] = 1.0935
            packet = packet_from_mapping(packet_data)
            data["last_seraphic_duet_trail_stack_snapshot"] = snapshot
            data["last_seraphic_duet_trail_stack_factor"] = 1.0 + 0.04 * snapshot
            data["last_seraphic_duet_consumed_rupturous_trail_stacks"] = 0 if preservation else snapshot
            data["last_seraphic_duet_trail_consumed"] = not preservation and snapshot > 0
            data["last_seraphic_duet_trail_preservation_active"] = preservation
            if preservation:
                data["trail_no_cost_remaining"] = 0.0
            elif snapshot:
                state.rupturous_trail_stacks = 0
                state.rupturous_trail_remaining = 0.0
            if sequence >= 6:
                data["s6_pending_enhanced_trajectory_grant"] = 10
            return [packet]
        if mode == "fusion_burst":
            followups = list(
                (((self._forte_config().get("modes") or {}).get(mode) or {}).get("seraphic_duet_followups") or [])
            )
            packet_data = next((dict(item) for item in followups if item.get("variant") == "settlement"), None)
            if packet_data is None:
                return []
            trail_cap = self._fusion_trail_cap(state)
            trail_snapshot = max(0, min(trail_cap, int(data.get("fusion_trail_stacks", 0) or 0)))
            effect_stacks = max(0, min(int(data.get("fusion_effect_max_stacks", 10) or 10), int(data.get("fusion_effect_stacks", 0) or 0)))
            if trail_snapshot <= 0 or effect_stacks <= 0:
                return []
            preservation = float(data.get("trail_no_cost_remaining", 0.0) or 0.0) > 0.0
            final_damage = self._fusion_final_damage_multiplier(
                removed_trajectory_count=trail_snapshot,
                enhancement_state=sequence >= 2,
            )
            packet_data["source_action_id"] = action.id
            packet_data["additional_tune_boost"] = final_damage
            packet = packet_from_mapping(packet_data)
            data["last_seraphic_duet_trail_stack_snapshot"] = trail_snapshot
            data["last_seraphic_duet_trail_stack_factor"] = final_damage
            data["last_seraphic_duet_fusion_effect_stacks_before"] = effect_stacks
            data["last_seraphic_duet_fusion_effect_stacks_after"] = effect_stacks
            data["last_seraphic_duet_fusion_settlement_multiplier"] = final_damage
            data["last_seraphic_duet_followup_variant"] = packet.variant
            data["last_seraphic_duet_followup_repeat_count"] = 1
            data["last_seraphic_duet_followup_multiplier"] = float(packet.source_multiplier or 0.0)
            data["last_seraphic_duet_followup_source_rows"] = list(packet.source_rows)
            data["last_seraphic_duet_followup_source_status"] = packet.source_status
            data["last_seraphic_duet_consumed_fusion_trail_stacks"] = 0 if preservation else trail_snapshot
            data["last_seraphic_duet_trail_consumed"] = not preservation
            data["last_seraphic_duet_trail_preservation_active"] = preservation
            if preservation:
                data["trail_no_cost_remaining"] = 0.0
                data["last_seraphic_duet_trail_no_cost_consumed"] = True
            else:
                data["fusion_trail_stacks"] = 0
                data["fusion_trail_remaining"] = 0.0
            return [packet]
        return []

    def on_party_tune_response_resolved(
        self,
        state: Any,
        response_context: dict[str, Any],
    ) -> dict[str, Any] | None:
        if aemeath_resonance_mode_from_config(getattr(state, "mechanics_config", {}) or {}) != "tune_rupture":
            return None
        if response_context.get("interfered_state") != "tune_rupture_interfered":
            return None
        if not bool(response_context.get("triggered", False)):
            return None
        response_damage = float(response_context.get("response_damage", 0.0) or 0.0)
        if response_damage <= 0.0:
            return None

        trail_cap = self._rupturous_trail_cap(state)
        gain = self._rupturous_trail_gain(state, source="party_tune_response")
        before = max(0, min(trail_cap, int(getattr(state, "rupturous_trail_stacks", 0) or 0)))
        after = min(trail_cap, before + gain)
        event = {
            "event_type": "rupturous_trail_gain",
            "tune_break_event_id": response_context.get("tune_break_event_id"),
            "host_action_id": response_context.get("host_action_id"),
            "response_id": response_context.get("response_id"),
            "response_source_character_id": response_context.get("source_character_id"),
            "response_action_id": response_context.get("response_action_id") or response_context.get("response_id"),
            "triggered": True,
            "response_damage": response_damage,
            "stacks_before": before,
            "requested_gain": gain,
            "applied_gain": after - before,
            "stack_gain": after - before,
            "stack_gain_requested": gain,
            "stacks_after": after,
            "max_stacks": trail_cap,
            "duration": RUPTUROUS_TRAIL_DURATION,
            "remaining_after": RUPTUROUS_TRAIL_DURATION,
            "duration_refresh_rule": "refresh_aggregate_duration_to_30s_on_each_application",
            "source_status": "workbook_confirmed_c0",
            "source_ref": RUPTUROUS_TRAIL_SOURCE_REF,
        }
        state.rupturous_trail_stacks = after
        state.rupturous_trail_remaining = RUPTUROUS_TRAIL_DURATION
        state.rupturous_trail_event_log.append(event)
        return event

    def resolve_incoming_qte_transition_action(
        self,
        character_state: Any,
        transition_config: dict[str, Any],
    ) -> tuple[str | None, list[str]]:
        warnings: list[str] = []
        intro_config = (
            (transition_config.get("characters") or {})
            .get(self.character_id, {})
            .get("intro_qte", {})
        )
        transition_actions = intro_config.get("transition_actions") or {}
        form = character_state.get("form") if isinstance(character_state, dict) else None
        if form == "mech":
            action_id = transition_actions.get("mech")
        elif form in {"aemeath", "human"}:
            action_id = transition_actions.get("human")
        else:
            action_id = transition_actions.get("human")
            warnings.append("missing_aemeath_form_defaulted_to_human")
        if not action_id:
            warnings.append("aemeath_qte_transition_action_missing")
        return action_id, warnings

    def after_action(self, state: Any, action: Any, result: Any) -> None:
        data = self._state(state)
        effects = action.mechanic_effects
        duration_was_set = "seraphic_duo_duration" in effects
        consumed_instant_response = (
            action.id in {"aemeath_heavy_aemeath_charged_2", "aemeath_heavy_mech_charged_2"}
            and data["instant_response"]
        )

        if "set_form" in effects:
            data["form"] = effects["set_form"]
        if "sync_delta" in effects:
            data["synchronization_rate"] += float(effects["sync_delta"])
        if "instant_response_sync_delta" in effects and consumed_instant_response and data["heavenfall_unbound"]:
            data["synchronization_rate"] += float(effects["instant_response_sync_delta"])
        if "set_synchronization_rate" in effects:
            data["synchronization_rate"] = float(effects["set_synchronization_rate"])
        if "resonance_rate_delta" in effects:
            data["resonance_rate"] += float(effects["resonance_rate_delta"])
            if action.id == "aemeath_liberation_overdrive" and data["starlume_acceleration_remaining"] > 0.0:
                data["resonance_rate"] += 1.0
        if "set_resonance_rate" in effects:
            data["resonance_rate"] = float(effects["set_resonance_rate"])
        if duration_was_set:
            data["seraphic_duo_remaining"] = float(effects["seraphic_duo_duration"])
        if "heavenfall_unbound" in effects:
            data["heavenfall_unbound"] = bool(effects["heavenfall_unbound"])
        if "heavenfall_unbound_duration" in effects:
            data["heavenfall_unbound_remaining"] = float(effects["heavenfall_unbound_duration"])
            data["heavenfall_unbound"] = data["heavenfall_unbound_remaining"] > 0.0
        if "stardust_resonance_duration" in effects:
            data["stardust_resonance_remaining"] = float(effects["stardust_resonance_duration"])
        if "starlume_acceleration_duration" in effects:
            data["starlume_acceleration_remaining"] = float(effects["starlume_acceleration_duration"])
        if "instant_response" in effects:
            data["instant_response"] = bool(effects["instant_response"])
        if "instant_response_consumed" in effects:
            data["instant_response_consumed"] = bool(effects["instant_response_consumed"])
        if "finale_available" in effects:
            data["finale_available"] = bool(effects["finale_available"])
        if "set_aemeath_combo_stage" in effects:
            data["aemeath_combo_stage"] = int(effects["set_aemeath_combo_stage"])
        if "set_mech_combo_stage" in effects:
            data["mech_combo_stage"] = int(effects["set_mech_combo_stage"])
        if "set_sync_strike_window" in effects:
            self._set_sync_strike_window(data, effects["set_sync_strike_window"])
        elif action.id in self._ARMAMENT_MERGE_WINDOW_ACTIONS:
            self._set_sync_strike_window(data, "armament_merge")
        elif action.id in self._CALL_OF_DAWN_WINDOW_ACTIONS:
            self._set_sync_strike_window(data, "call_of_dawn")
        else:
            self._clear_sync_strike_window(data)
        if action.id == "aemeath_liberation_overdrive":
            data["overdrive_form_switch_window_remaining"] = 1
            data["forte_enhancement_stacks"] = int(data.get("forte_enhancement_max_stacks", 2) or 2)
            data["forte_enhancement_remaining"] = 30.0
            data["trail_no_cost_remaining"] = 30.0
        if action.id in {"aemeath_sync_strike_armament_merge", "aemeath_sync_strike_call_of_dawn"}:
            pending = int(data.pop("s6_pending_enhanced_trajectory_grant", 0) or 0)
            if pending:
                self._grant_rupturous_trail(state, pending, source="s6_enhanced_skill_post_action")
            if aemeath_resonance_mode_from_config(getattr(state, "mechanics_config", {}) or {}) == "fusion_burst":
                apply_aemeath_fusion_effect_event(
                    state,
                    source_character_id=action.character_id,
                    source_action_id=action.id,
                    source_event_id=action.id,
                    apply_base_effect=True,
                    counts_as_party_application=True,
                    combat_time=float(getattr(state, "combat_time", 0.0) or 0.0),
                )
        if action.id == "aemeath_form_switch_to_aemeath_after_overdrive":
            data["overdrive_form_switch_window_remaining"] = 0
        if consumed_instant_response:
            data["instant_response"] = False
            data["instant_response_consumed"] = True
        if action.id == "aemeath_liberation_overdrive":
            data["instant_response_consumed"] = False
        if data["heavenfall_unbound_remaining"] <= 0.0:
            data["instant_response_consumed"] = False

        if action.id in {"aemeath_seraphic_duet_overturn", "aemeath_seraphic_duet_encore"}:
            data["last_seraphic_duet_generated_damage"] = float(
                getattr(result, "aemeath_seraphic_duet_followup_damage", 0.0) or 0.0
            )
            data["last_seraphic_duet_followup_damage"] = data["last_seraphic_duet_generated_damage"]
            data["last_seraphic_duet_followup_source_status"] = getattr(
                result, "aemeath_seraphic_duet_followup_source_status", None
            )

        self._clamp(data)
        self._derive_state(data)
        data["last_resolved_action_id"] = action.id

    def advance_time(self, state: Any, combat_elapsed: float, action_elapsed: float | None = None) -> None:
        data = self._state(state)
        if data["seraphic_duo_remaining"] > 0.0:
            data["seraphic_duo_remaining"] = max(0.0, data["seraphic_duo_remaining"] - combat_elapsed)
        if data["heavenfall_unbound_remaining"] > 0.0:
            data["heavenfall_unbound_remaining"] = max(0.0, data["heavenfall_unbound_remaining"] - combat_elapsed)
        if data["stardust_resonance_remaining"] > 0.0:
            data["stardust_resonance_remaining"] = max(0.0, data["stardust_resonance_remaining"] - combat_elapsed)
        if data["starlume_acceleration_remaining"] > 0.0:
            data["starlume_acceleration_remaining"] = max(0.0, data["starlume_acceleration_remaining"] - combat_elapsed)
        if data["forte_enhancement_remaining"] > 0.0:
            data["forte_enhancement_remaining"] = max(0.0, data["forte_enhancement_remaining"] - combat_elapsed)
            if data["forte_enhancement_remaining"] <= 0.0:
                data["forte_enhancement_stacks"] = 0
        if data["trail_no_cost_remaining"] > 0.0:
            data["trail_no_cost_remaining"] = max(0.0, data["trail_no_cost_remaining"] - combat_elapsed)
        if FUSION_EFFECT_DURATION_SECONDS is not None and data["fusion_effect_remaining"] > 0.0:
            data["fusion_effect_remaining"] = max(0.0, data["fusion_effect_remaining"] - combat_elapsed)
            if data["fusion_effect_remaining"] <= 0.0:
                data["fusion_effect_stacks"] = 0
        if (
            aemeath_resonance_mode_from_config(getattr(state, "mechanics_config", {}) or {}) == "fusion_burst"
            and float(getattr(state, "combat_time", 0.0) or 0.0) > 0.0
        ):
            self._ensure_fusion_minimum_effect(state)
        if data["fusion_trail_remaining"] > 0.0:
            data["fusion_trail_remaining"] = max(0.0, data["fusion_trail_remaining"] - combat_elapsed)
            if data["fusion_trail_remaining"] <= 0.0:
                data["fusion_trail_stacks"] = 0
        self._derive_state(data)

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
            float(data["heavenfall_unbound_remaining"]) / 60.0,
            float(data["stardust_resonance_remaining"]) / 30.0,
            float(data["starlume_acceleration_remaining"]) / 30.0,
            1.0 if data["instant_response"] else 0.0,
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
            "aemeath.heavenfall_unbound_remaining",
            "aemeath.stardust_resonance_remaining",
            "aemeath.starlume_acceleration_remaining",
            "aemeath.instant_response",
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
            "heavenfall_unbound_remaining": data["heavenfall_unbound_remaining"],
            "stardust_resonance_remaining": data["stardust_resonance_remaining"],
            "starlume_acceleration_remaining": data["starlume_acceleration_remaining"],
            "instant_response": data["instant_response"],
            "finale_available": data["finale_available"],
            "instant_response_consumed": data["instant_response_consumed"],
            "last_resolved_action_id": data["last_resolved_action_id"],
            "sync_strike_window_type": data["sync_strike_window_type"],
            "sync_strike_window_remaining": data["sync_strike_window_remaining"],
            "next_resonance_skill_variant": data["sync_strike_window_type"],
            "overdrive_form_switch_window_remaining": data["overdrive_form_switch_window_remaining"],
            "target_rupturous_trail_stacks": int(getattr(state, "rupturous_trail_stacks", 0) or 0),
            "target_rupturous_trail_remaining": float(getattr(state, "rupturous_trail_remaining", 0.0) or 0.0),
            "target_rupturous_trail_max_stacks": self._rupturous_trail_cap(state),
            "rupturous_trail_state_source": "CombatState",
            "fusion_trail_stacks": data["fusion_trail_stacks"],
            "fusion_trail_remaining": data["fusion_trail_remaining"],
            "fusion_trail_max_stacks": self._fusion_trail_cap(state),
            "fusion_effect_stacks": data["fusion_effect_stacks"],
            "fusion_effect_remaining": data["fusion_effect_remaining"],
            "fusion_effect_max_stacks": data["fusion_effect_max_stacks"],
            "fusion_application_last_trigger_time": dict(data["fusion_application_last_trigger_time"]),
            "forte_enhancement_stacks": data["forte_enhancement_stacks"],
            "forte_enhancement_remaining": data["forte_enhancement_remaining"],
            "forte_enhancement_max_stacks": data["forte_enhancement_max_stacks"],
            "trail_no_cost_remaining": data["trail_no_cost_remaining"],
            "last_seraphic_duet_consumed_rupturous_trail_stacks": data["last_seraphic_duet_consumed_rupturous_trail_stacks"],
            "last_seraphic_duet_consumed_fusion_trail_stacks": data["last_seraphic_duet_consumed_fusion_trail_stacks"],
            "last_seraphic_duet_generated_damage": data["last_seraphic_duet_generated_damage"],
            "last_seraphic_duet_followup_variant": data["last_seraphic_duet_followup_variant"],
            "last_seraphic_duet_followup_repeat_count": data["last_seraphic_duet_followup_repeat_count"],
            "last_seraphic_duet_followup_multiplier": data["last_seraphic_duet_followup_multiplier"],
            "last_seraphic_duet_followup_damage": data["last_seraphic_duet_followup_damage"],
            "last_seraphic_duet_followup_source_rows": list(data.get("last_seraphic_duet_followup_source_rows", [])),
            "last_seraphic_duet_followup_source_status": data["last_seraphic_duet_followup_source_status"],
            "last_seraphic_duet_forte_enhancement_stacks_before": data["last_seraphic_duet_forte_enhancement_stacks_before"],
            "last_seraphic_duet_forte_enhancement_stacks_consumed": data["last_seraphic_duet_forte_enhancement_stacks_consumed"],
            "last_seraphic_duet_forte_enhancement_stacks_after": data["last_seraphic_duet_forte_enhancement_stacks_after"],
            "last_seraphic_duet_trail_no_cost_consumed": data["last_seraphic_duet_trail_no_cost_consumed"],
            "last_seraphic_duet_trail_stack_snapshot": data["last_seraphic_duet_trail_stack_snapshot"],
            "last_seraphic_duet_trail_stack_factor": data["last_seraphic_duet_trail_stack_factor"],
            "last_seraphic_duet_trail_preservation_active": data["last_seraphic_duet_trail_preservation_active"],
            "last_seraphic_duet_trail_preservation_after": data["last_seraphic_duet_trail_preservation_after"],
            "last_seraphic_duet_trail_consumed": data["last_seraphic_duet_trail_consumed"],
            "last_seraphic_duet_total_extra_tune_multiplier": data["last_seraphic_duet_total_extra_tune_multiplier"],
            "last_seraphic_duet_fusion_effect_stacks_before": data["last_seraphic_duet_fusion_effect_stacks_before"],
            "last_seraphic_duet_fusion_effect_stacks_after": data["last_seraphic_duet_fusion_effect_stacks_after"],
            "last_seraphic_duet_fusion_settlement_multiplier": data["last_seraphic_duet_fusion_settlement_multiplier"],
            "forte_unresolved_runtime_notes": list(data.get("forte_unresolved_runtime_notes", [])),
            "single_target_aemeath_forte_trail_state": True,
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
        data["heavenfall_unbound_remaining"] = max(0.0, float(data["heavenfall_unbound_remaining"]))
        data["stardust_resonance_remaining"] = max(0.0, float(data["stardust_resonance_remaining"]))
        data["starlume_acceleration_remaining"] = max(0.0, float(data["starlume_acceleration_remaining"]))
        data["heavenfall_unbound"] = bool(data["heavenfall_unbound"]) or data["heavenfall_unbound_remaining"] > 0.0
        data["instant_response"] = bool(data["instant_response"])
        data["finale_available"] = bool(data["finale_available"])
        data["instant_response_consumed"] = bool(data["instant_response_consumed"])
        if data["sync_strike_window_type"] not in {"armament_merge", "call_of_dawn"}:
            data["sync_strike_window_type"] = None
        data["sync_strike_window_remaining"] = 1 if data["sync_strike_window_type"] else 0
        data["overdrive_form_switch_window_remaining"] = 1 if int(data["overdrive_form_switch_window_remaining"]) > 0 else 0
        data.pop("rupturous_trail_stacks", None)
        data.pop("rupturous_trail_remaining", None)
        data.pop("rupturous_trail_max_stacks", None)
        data["fusion_trail_max_stacks"] = max(1, int(data.get("fusion_trail_max_stacks", 60) or 60))
        data["fusion_effect_max_stacks"] = max(1, int(data.get("fusion_effect_max_stacks", 10) or 10))
        data["forte_enhancement_max_stacks"] = max(1, int(data.get("forte_enhancement_max_stacks", 2) or 2))
        data["forte_enhancement_stacks"] = max(
            0,
            min(data["forte_enhancement_max_stacks"], int(data.get("forte_enhancement_stacks", 0) or 0)),
        )
        data["forte_enhancement_remaining"] = max(0.0, float(data.get("forte_enhancement_remaining", 0.0) or 0.0))
        if data["forte_enhancement_remaining"] <= 0.0:
            data["forte_enhancement_stacks"] = 0
        data["trail_no_cost_remaining"] = max(0.0, float(data.get("trail_no_cost_remaining", 0.0) or 0.0))
        data["fusion_trail_stacks"] = max(
            0,
            min(data["fusion_trail_max_stacks"], int(data.get("fusion_trail_stacks", 0) or 0)),
        )
        data["fusion_trail_remaining"] = max(0.0, float(data.get("fusion_trail_remaining", 0.0) or 0.0))
        data["fusion_effect_stacks"] = max(
            0,
            min(data["fusion_effect_max_stacks"], int(data.get("fusion_effect_stacks", 0) or 0)),
        )
        data["fusion_effect_remaining"] = max(0.0, float(data.get("fusion_effect_remaining", 0.0) or 0.0))
        if FUSION_EFFECT_DURATION_SECONDS is not None and data["fusion_effect_remaining"] <= 0.0:
            data["fusion_effect_stacks"] = 0
        if not isinstance(data.get("fusion_application_last_trigger_time"), dict):
            data["fusion_application_last_trigger_time"] = {}
        if not isinstance(data.get("fusion_trail_event_log"), list):
            data["fusion_trail_event_log"] = []
        data["last_seraphic_duet_consumed_rupturous_trail_stacks"] = max(
            0, int(data.get("last_seraphic_duet_consumed_rupturous_trail_stacks", 0) or 0)
        )
        data["last_seraphic_duet_consumed_fusion_trail_stacks"] = max(
            0, int(data.get("last_seraphic_duet_consumed_fusion_trail_stacks", 0) or 0)
        )
        data["last_seraphic_duet_generated_damage"] = max(
            0.0, float(data.get("last_seraphic_duet_generated_damage", 0.0) or 0.0)
        )
        data["last_seraphic_duet_followup_repeat_count"] = max(
            0, int(data.get("last_seraphic_duet_followup_repeat_count", 0) or 0)
        )
        data["last_seraphic_duet_followup_multiplier"] = max(
            0.0, float(data.get("last_seraphic_duet_followup_multiplier", 0.0) or 0.0)
        )
        data["last_seraphic_duet_followup_damage"] = max(
            0.0, float(data.get("last_seraphic_duet_followup_damage", 0.0) or 0.0)
        )
        if not isinstance(data.get("last_seraphic_duet_followup_source_rows"), list):
            data["last_seraphic_duet_followup_source_rows"] = []
        data["last_seraphic_duet_forte_enhancement_stacks_before"] = max(
            0, int(data.get("last_seraphic_duet_forte_enhancement_stacks_before", 0) or 0)
        )
        data["last_seraphic_duet_forte_enhancement_stacks_consumed"] = max(
            0, int(data.get("last_seraphic_duet_forte_enhancement_stacks_consumed", 0) or 0)
        )
        data["last_seraphic_duet_forte_enhancement_stacks_after"] = max(
            0, int(data.get("last_seraphic_duet_forte_enhancement_stacks_after", 0) or 0)
        )
        data["last_seraphic_duet_trail_no_cost_consumed"] = bool(
            data.get("last_seraphic_duet_trail_no_cost_consumed", False)
        )
        data["last_seraphic_duet_trail_stack_snapshot"] = max(
            0, int(data.get("last_seraphic_duet_trail_stack_snapshot", 0) or 0)
        )
        data["last_seraphic_duet_trail_stack_factor"] = max(
            1.0, float(data.get("last_seraphic_duet_trail_stack_factor", 1.0) or 1.0)
        )
        data["last_seraphic_duet_fusion_effect_stacks_before"] = max(
            0, int(data.get("last_seraphic_duet_fusion_effect_stacks_before", 0) or 0)
        )
        data["last_seraphic_duet_fusion_effect_stacks_after"] = max(
            0, int(data.get("last_seraphic_duet_fusion_effect_stacks_after", 0) or 0)
        )
        data["last_seraphic_duet_fusion_settlement_multiplier"] = max(
            0.0, float(data.get("last_seraphic_duet_fusion_settlement_multiplier", 0.0) or 0.0)
        )
        data["last_seraphic_duet_trail_preservation_active"] = bool(
            data.get("last_seraphic_duet_trail_preservation_active", False)
        )
        data["last_seraphic_duet_trail_preservation_after"] = bool(
            data.get("last_seraphic_duet_trail_preservation_after", False)
        )
        data["last_seraphic_duet_trail_consumed"] = bool(data.get("last_seraphic_duet_trail_consumed", False))
        data["last_seraphic_duet_total_extra_tune_multiplier"] = max(
            0.0, float(data.get("last_seraphic_duet_total_extra_tune_multiplier", 0.0) or 0.0)
        )
        if not isinstance(data.get("forte_unresolved_runtime_notes"), list):
            data["forte_unresolved_runtime_notes"] = []

    def _derive_state(self, data: dict[str, Any]) -> None:
        data["heavenfall_unbound"] = data["heavenfall_unbound_remaining"] > 0.0
        if not data["heavenfall_unbound"]:
            data["instant_response_consumed"] = False
        data["instant_response"] = (
            data["heavenfall_unbound"]
            and data["resonance_rate"] >= 4.0
            and not data["instant_response_consumed"]
        )
        data["finale_available"] = self._is_finale_ready(data)

    def _set_sync_strike_window(self, data: dict[str, Any], window_type: Any) -> None:
        if window_type in {"armament_merge", "call_of_dawn"}:
            data["sync_strike_window_type"] = window_type
            data["sync_strike_window_remaining"] = 1
        else:
            self._clear_sync_strike_window(data)

    def _clear_sync_strike_window(self, data: dict[str, Any]) -> None:
        data["sync_strike_window_type"] = None
        data["sync_strike_window_remaining"] = 0

    def _rupturous_trail_cap(self, state: Any) -> int:
        account_state = state.character_mechanics_state.get("_account_constellation", {})
        sequence = int(account_state.get("aemeath_sequence", 0) or 0)
        return 60 if sequence >= 6 else RUPTUROUS_TRAIL_MAX_STACKS

    def _fusion_trail_cap(self, state: Any) -> int:
        account_state = state.character_mechanics_state.get("_account_constellation", {})
        return 60 if int(account_state.get("aemeath_sequence", 0) or 0) >= 6 else 30

    def _fusion_final_damage_multiplier(self, *, removed_trajectory_count: int, enhancement_state: bool) -> float:
        stacks = max(0, int(removed_trajectory_count))
        return 1.0 + (4.0 if enhancement_state else 2.0) + (0.15 if enhancement_state else 0.10) * stacks

    def _ensure_fusion_minimum_effect(self, state: Any) -> None:
        """Maintain the workbook's in-combat minimum Fusion Effect without a party application."""
        data = self._state(state)
        if int(data.get("fusion_effect_stacks", 0) or 0) > 0:
            return
        data["fusion_effect_stacks"] = 1
        data["fusion_effect_remaining"] = 0.0
        data["fusion_trail_event_log"].append(
            {
                "event_type": "fusion_effect_in_combat_minimum",
                "fusion_effect_duration_seconds": FUSION_EFFECT_DURATION_SECONDS,
                "fusion_effect_duration_policy": "persistent_while_in_combat_source_duration_not_specified",
                "fusion_effect_stacks_before": 0,
                "fusion_effect_stacks_after": 1,
                "base_trajectory_gain": 0,
                "s6_post_application_gain": 0,
                "source_ref": "\u89d2\u8272-\u5973!D2844",
            }
        )


    def _rupturous_trail_gain(self, state: Any, *, source: str) -> int:
        account_state = state.character_mechanics_state.get("_account_constellation", {})
        sequence = int(account_state.get("aemeath_sequence", 0) or 0)
        if sequence < 6:
            return RUPTUROUS_TRAIL_GAIN_PER_RESPONSE
        gain = RUPTUROUS_TRAIL_GAIN_PER_RESPONSE
        if source == "party_tune_response":
            gain += 10
        return gain

    def _grant_rupturous_trail(self, state: Any, gain: int, *, source: str) -> None:
        cap = self._rupturous_trail_cap(state)
        before = max(0, min(cap, int(getattr(state, "rupturous_trail_stacks", 0) or 0)))
        after = min(cap, before + max(0, int(gain)))
        state.rupturous_trail_stacks = after
        state.rupturous_trail_remaining = RUPTUROUS_TRAIL_DURATION
        state.rupturous_trail_event_log.append(
            {
                "event_type": "rupturous_trail_gain",
                "source": source,
                "stacks_before": before,
                "requested_gain": int(gain),
                "applied_gain": after - before,
                "stacks_after": after,
                "max_stacks": cap,
                "duration": RUPTUROUS_TRAIL_DURATION,
                "remaining_after": RUPTUROUS_TRAIL_DURATION,
                "source_status": "account_s6_workbook_confirmed",
            }
        )

    def _is_finale_ready(self, data: dict[str, Any]) -> bool:
        return (
            data["heavenfall_unbound"]
            and data["synchronization_rate"] >= 200.0
            and data["resonance_rate"] >= 4.0
        )

    def _forte_config(self) -> dict[str, Any]:
        if not FORTE_CONFIG_PATH.exists():
            return {}
        with FORTE_CONFIG_PATH.open("r", encoding="utf-8-sig") as file:
            return json.load(file)
