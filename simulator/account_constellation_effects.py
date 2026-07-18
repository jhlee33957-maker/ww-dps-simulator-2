from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from simulator.models import BuffData
from simulator.resource_system import add_concerto_energy, sync_concerto_state


ACCOUNT_SCOPE_ID = "single_persistent_boss_no_kill_no_survival"
ACCOUNT_OBSERVATION_VERSION = "slot_account_constellation_single_boss_v6"
ACCOUNT_OBSERVATION_EXTRA_LABELS = [
    "account_scope.single_persistent_boss_active",
    "account_scope.enemy_death_disabled",
    "account_scope.player_survival_disabled",
    "account_precombat.elapsed_seconds_scaled",
    "account_precombat.aemeath_radiance_ready",
    "account_precombat.lynae_overflow_restored_scaled",
    "account_aemeath.s2_tune_stack_ratio",
    "account_aemeath.s3_tune_contributor_ratio",
    "account_aemeath.s3_fusion_contributor_ratio",
    "account_aemeath.s4_party_bonus_remaining_ratio",
    "account_aemeath.s6_trajectory_ratio",
    "account_lynae.s1_paint_remaining_ratio",
    "account_lynae.s2_outro_general_deepen_scaled",
    "account_mornye.s1_marker_remaining_ratio",
    "account_mornye.s2_marker_crit_damage_scaled",
    "account_mornye.s3_distributed_array_icd_ratio",
]
ACCOUNT_OBSERVATION_SHAPE = 314 + len(ACCOUNT_OBSERVATION_EXTRA_LABELS)
ACCOUNT_AEMEATH_S4_BUFF_ID = "account_aemeath_s4_party_all_attribute_damage"
ACCOUNT_LYNAE_S2_SELF_BUFF_ID = "account_lynae_s2_self_all_damage_deepen"
ACCOUNT_LYNAE_S2_OUTRO_BUFF_ID = "account_lynae_s2_outro_next_incoming_all_damage_deepen"
AEMEATH_S1_HEAVY_ELIGIBLE_ACTION_IDS = {
    "aemeath_heavy_aemeath_charged_2",
    "aemeath_heavy_mech_charged_2",
}
AEMEATH_CHARGED_ACTION_IDS = {
    "aemeath_heavy_aemeath_charged_1",
    "aemeath_heavy_aemeath_charged_2",
    "aemeath_heavy_mech_charged_1",
    "aemeath_heavy_mech_charged_2",
}
AEMEATH_CHARGED_II_ACTION_IDS = {
    "aemeath_heavy_aemeath_charged_2",
    "aemeath_heavy_mech_charged_2",
}
AEMEATH_S2_ENHANCED_SKILL_IDS = {
    "aemeath_sync_strike_armament_merge",
    "aemeath_sync_strike_call_of_dawn",
}
AEMEATH_S4_TRIGGER_IDS = {
    "aemeath_form_switch_to_mech_normal",
    "aemeath_form_switch_to_aemeath_normal",
    "aemeath_form_switch_to_aemeath_after_overdrive",
    "aemeath_sync_strike_armament_merge",
    "aemeath_sync_strike_call_of_dawn",
    "aemeath_qte_intro_human",
    "aemeath_qte_intro_mech",
}
AEMEATH_FINALE_IDS = {"aemeath_heavenfall_finale"}
AEMEATH_OVERDRIVE_IDS = {"aemeath_liberation_overdrive"}
AEMEATH_LIBERATION_IDS = {"aemeath_liberation_overdrive", "aemeath_heavenfall_finale"}
AEMEATH_S6_FIXED_CRIT_PACKET_IDS = {
    "aemeath_seraphic_duet_tune_rupture_followup",
    "aemeath_seraphic_duet_tune_rupture_enhanced_followup",
    "aemeath_seraphic_duet_fusion_burst_settlement",
}
LYNAE_LIGHT_LEAP_IDS = {
    "lynae_polychrome_leap_stage_1",
    "lynae_polychrome_leap_stage_2",
    "lynae_polychrome_leap_stage_3",
}
MORNYE_DISTRIBUTED_ARRAY_ID = "mornye_skill_distributed_array"
MORNYE_OBSERVATION_MARKER_IDS = {
    "mornye_heavy_inversion",
    "mornye_liberation_critical_protocol",
}


class AccountScopeValidationError(ValueError):
    """Raised when account constellation mechanics are requested outside v121 scope."""


def load_account_constellation_contract(data_dir: Path | str = "data") -> dict[str, Any]:
    path = Path(data_dir) / "account_constellation_mechanics_v121.json"
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def load_account_scope_contract(data_dir: Path | str = "data") -> dict[str, Any]:
    path = Path(data_dir) / "account_simulation_scope_v121.json"
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def validate_account_single_boss_scope(scope: Any) -> dict[str, Any]:
    if isinstance(scope, str):
        scope = {"scope_id": scope}
    if not isinstance(scope, dict):
        raise AccountScopeValidationError("account simulation scope must be a mapping or scope id")
    normalized = copy.deepcopy(scope)
    scope_id = normalized.get("scope_id") or normalized.get("supported_scope")
    enemy_model = normalized.get("enemy_model", "single_persistent_target")
    enemy_count = int(normalized.get("enemy_count", 1))
    disallowed = []
    for key in (
        "enemy_death_enabled",
        "enemy_respawn_enabled",
        "waves_enabled",
        "player_hp_model_enabled",
        "player_death_enabled",
        "player_survival_enabled",
        "target_pull_or_movement_enabled",
    ):
        if bool(normalized.get(key, False)):
            disallowed.append(key)
    if scope_id != ACCOUNT_SCOPE_ID:
        raise AccountScopeValidationError(f"unsupported account scope: {scope_id!r}")
    if enemy_model != "single_persistent_target" or enemy_count != 1 or disallowed:
        raise AccountScopeValidationError(
            "account constellation mechanics require one persistent target with no death, respawn, waves, or survival"
        )
    normalized.setdefault("scope_id", ACCOUNT_SCOPE_ID)
    normalized.setdefault("enemy_model", "single_persistent_target")
    normalized.setdefault("enemy_count", 1)
    normalized.setdefault("enemy_death_enabled", False)
    normalized.setdefault("enemy_respawn_enabled", False)
    normalized.setdefault("waves_enabled", False)
    normalized.setdefault("player_survival_enabled", False)
    normalized.setdefault("player_hp_model_enabled", False)
    normalized.setdefault("player_death_enabled", False)
    normalized.setdefault("target_pull_or_movement_enabled", False)
    return normalized


def initialize_account_runtime_state(simulation: Any) -> None:
    if not _account_runtime_enabled(simulation):
        return
    state = simulation.state
    account_state = state.character_mechanics_state.setdefault("_account_constellation", {})
    account_state.setdefault("dispatch_counts", {"aemeath": 0, "lynae": 0, "mornye": 0})
    account_state.setdefault("events", [])
    account_state.setdefault("precombat_elapsed_seconds", float(simulation.precombat_elapsed_seconds or 0.0))
    account_state.setdefault("scope_id", ACCOUNT_SCOPE_ID)
    account_state["aemeath_sequence"] = _sequence_for(simulation, "aemeath")
    account_state["lynae_sequence"] = _sequence_for(simulation, "lynae")
    account_state["mornye_sequence"] = _sequence_for(simulation, "mornye")
    account_state.setdefault("aemeath_s2_stacks", 0)
    account_state.setdefault("aemeath_s2_remaining", 0.0)
    account_state.setdefault("aemeath_s3_tune_contributors", [])
    account_state.setdefault("aemeath_s3_fusion_contributors", [])
    account_state.setdefault("aemeath_s3_tune_finale_deepen", 0.0)
    account_state.setdefault("aemeath_s3_fusion_finale_deepen", 0.0)
    account_state.setdefault("mornye_s3_icd_remaining", 0.0)
    account_state.setdefault("starfield_icd_remaining", 0.0)
    account_state.setdefault("lynae_s2_outro_remaining", 0.0)
    account_state.setdefault("lynae_s2_outro_target", None)
    elapsed = float(simulation.precombat_elapsed_seconds or 0.0)
    if _sequence_for(simulation, "aemeath") >= 1:
        aemeath_state = state.character_mechanics_state.setdefault("aemeath", {})
        aemeath_state["account_radiance_quick_charge_ready"] = elapsed > 4.0
        account_state["aemeath_radiance_quick_charge_ready"] = elapsed > 4.0
    if _sequence_for(simulation, "lynae") >= 2:
        # Collective Interference is the authoritative target Tune Strain cap.
        simulation.state.mechanics_config.setdefault("lynae", {})["lynae_constellation"] = max(
            int((simulation.state.mechanics_config.get("lynae") or {}).get("lynae_constellation", 0) or 0),
            _sequence_for(simulation, "lynae"),
        )
        state.target_tune_strain_interfered_max_stacks = lynae_s2_collective_interference_cap(1)
    if _sequence_for(simulation, "lynae") >= 1:
        lynae_state = state.character_mechanics_state.setdefault("lynae", {})
        optical = bool(lynae_state.get("optical_sampling_stage_active", True)) or bool(
            getattr(simulation, "account_optical_sampling_active", False)
        )
        restored = lynae_s1_precombat_overflow(elapsed, optical)
        if restored > 0.0:
            before = float(lynae_state.get("overflow", 0.0) or 0.0)
            cap = float(lynae_state.get("overflow_max", 120.0) or 120.0)
            lynae_state["overflow"] = min(cap, before + restored)
            account_state["lynae_precombat_overflow_restored"] = lynae_state["overflow"] - before
        else:
            account_state["lynae_precombat_overflow_restored"] = 0.0


def advance_account_constellation_time(simulation: Any, combat_elapsed: float) -> None:
    if not _account_runtime_enabled(simulation):
        return
    elapsed = max(0.0, float(combat_elapsed or 0.0))
    account_state = simulation.state.character_mechanics_state.setdefault("_account_constellation", {})
    for key in (
        "aemeath_s2_remaining",
        "aemeath_s4_remaining",
        "lynae_s2_outro_remaining",
        "mornye_s3_icd_remaining",
        "mornye_s2_field_remaining",
    ):
        account_state[key] = max(0.0, float(account_state.get(key, 0.0) or 0.0) - elapsed)
    if float(account_state.get("aemeath_s2_remaining", 0.0) or 0.0) <= 0.0:
        account_state["aemeath_s2_stacks"] = 0
    if float(account_state.get("lynae_s2_outro_remaining", 0.0) or 0.0) <= 0.0:
        account_state["lynae_s2_outro_target"] = None


def before_account_action(simulation: Any, selected_action: Any, action: Any) -> None:
    if not _account_runtime_enabled(simulation):
        return
    del selected_action
    account_state = simulation.state.character_mechanics_state.setdefault("_account_constellation", {})
    actor = getattr(action, "character_id", None) or simulation.state.active_character_id
    if actor in {"aemeath", "lynae", "mornye"}:
        counts = account_state.setdefault("dispatch_counts", {"aemeath": 0, "lynae": 0, "mornye": 0})
        counts[actor] = int(counts.get(actor, 0) or 0) + 1
    if actor == "aemeath" and _sequence_for(simulation, "aemeath") >= 4 and str(getattr(action, "id", "")) in AEMEATH_S4_TRIGGER_IDS:
        _apply_aemeath_s4_buff(simulation, None)


def after_account_action(simulation: Any, action: Any, result: Any) -> None:
    if not _account_runtime_enabled(simulation) or result is None or not getattr(result, "valid", False):
        return
    _register_account_runtime_contributors(simulation, action, result)
    character_id = getattr(action, "character_id", None)
    if character_id == "aemeath":
        apply_aemeath_sequence_effects(simulation, action, result)
    elif character_id == "lynae":
        apply_lynae_sequence_effects(simulation, action, result)
    elif character_id == "mornye":
        apply_mornye_sequence_effects(simulation, action, result)
    _sync_last_logs(simulation, result)


def on_account_transition(simulation: Any, transition_resolution: Any, result: Any) -> None:
    if not _account_runtime_enabled(simulation) or transition_resolution is None:
        return
    account_state = simulation.state.character_mechanics_state.setdefault("_account_constellation", {})
    target = getattr(transition_resolution, "incoming_character_id", None) or getattr(transition_resolution, "target_character_id", None)
    outgoing = getattr(transition_resolution, "outgoing_character_id", None)
    if float(account_state.get("lynae_s2_outro_remaining", 0.0) or 0.0) > 0.0 and target:
        if account_state.get("lynae_s2_outro_target") is None:
            account_state["lynae_s2_outro_target"] = target
        elif target != account_state.get("lynae_s2_outro_target"):
            account_state["lynae_s2_outro_remaining"] = 0.0
            account_state["lynae_s2_outro_target"] = None
            _remove_active_buff(simulation.state, ACCOUNT_LYNAE_S2_OUTRO_BUFF_ID)
    if outgoing == "lynae" and _sequence_for(simulation, "lynae") >= 2:
        account_state["lynae_s2_outro_remaining"] = 14.0
        account_state["lynae_s2_outro_target"] = target
        buff = _buff(
            ACCOUNT_LYNAE_S2_OUTRO_BUFF_ID,
            "Lynae S2 Outro next incoming all damage deepen",
            "damage_amp",
            0.25,
            14.0,
            target_scope="specific_character",
            target_character_id=target,
            damage_amp_modifiers={"all": 0.25},
            metadata={"base_outro_all_damage_deepen": 0.15, "s2_additional_all_damage_deepen": 0.25},
        )
        simulation.buffs[buff.id] = buff
        from simulator.buff_system import apply_buff

        apply_buff(simulation.state, buff, "lynae")
        _record_event(simulation, result, "lynae_s2_outro_applied", target_character_id=target, duration_seconds=14.0)


def apply_aemeath_sequence_effects(*args: Any, **kwargs: Any) -> Any:
    if args and hasattr(args[0], "state"):
        return _apply_aemeath_runtime(*args, **kwargs)
    return _apply_aemeath_helper(*args, **kwargs)


def apply_lynae_sequence_effects(*args: Any, **kwargs: Any) -> Any:
    if args and hasattr(args[0], "state"):
        return _apply_lynae_runtime(*args, **kwargs)
    return _apply_lynae_helper(*args, **kwargs)


def apply_mornye_sequence_effects(*args: Any, **kwargs: Any) -> Any:
    if args and hasattr(args[0], "state"):
        return _apply_mornye_runtime(*args, **kwargs)
    return _apply_mornye_helper(*args, **kwargs)


def build_account_direct_damage_context(
    *,
    state: Any,
    characters: dict[str, Any],
    action: Any,
    hit: Any,
) -> dict[str, Any]:
    if not _account_state_enabled_from_parts(state, characters):
        return {}
    action_id = str(getattr(action, "id", ""))
    character_id = str(getattr(action, "character_id", "") or "")
    hit_category = str(getattr(hit, "damage_category", "") or "")
    context: dict[str, Any] = {
        "coefficient_multiplier": 1.0,
        "coefficient_add": 0.0,
        "crit_damage_add": 0.0,
        "crit_rate_override": None,
        "crit_damage_override": None,
        "damage_amp_add": 0.0,
        "damage_bonus_add": 0.0,
        "target_deepen_add": 0.0,
        "events": [],
    }
    account_state = state.character_mechanics_state.setdefault("_account_constellation", {})
    if character_id == "aemeath" and _sequence(characters.get("aemeath")) >= 1 and hit_category == "normal":
        aemeath_state = state.character_mechanics_state.setdefault("aemeath", {})
        instant_response_active = bool(aemeath_state.get("instant_response", False)) or bool(
            aemeath_state.get("account_radiance_quick_charge_ready", False)
        )
        if action_id in AEMEATH_S1_HEAVY_ELIGIBLE_ACTION_IDS and instant_response_active:
            context["crit_damage_add"] += 3.0
            context["events"].append(
                {
                    "event_type": "aemeath_s1_heavy_crit_damage_formula",
                    "crit_damage_add": 3.0,
                    "source_id": "aemeath_s1",
                }
            )
    if character_id == "aemeath" and _sequence(characters.get("aemeath")) >= 2 and action_id in AEMEATH_S2_ENHANCED_SKILL_IDS:
        context["coefficient_multiplier"] *= 2.0
        context["events"].append(
            {
                "event_type": "aemeath_s2_direct_enhanced_skill_coefficient",
                "coefficient_multiplier": 2.0,
                "mechanic_packet_excluded": True,
                "source_id": "aemeath_s2",
            }
        )
    if character_id == "aemeath" and _sequence(characters.get("aemeath")) >= 3 and action_id in AEMEATH_FINALE_IDS:
        context["coefficient_multiplier"] *= 2.0
        context["events"].append(
            {"event_type": "aemeath_s3_finale_coefficient", "coefficient_multiplier": 2.0, "source_id": "aemeath_s3"}
        )
        active_mode = "fusion" if _active_aemeath_mode(state) == "fusion_burst" else "tune"
        deepen = float(account_state.get(f"aemeath_s3_{active_mode}_finale_deepen", 0.0) or 0.0)
        if deepen > 0.0:
            context["damage_amp_add"] += deepen
            context["events"].append(
                {
                    "event_type": "aemeath_s3_finale_deepen_formula",
                    "active_mode": active_mode,
                    "damage_amp_add": deepen,
                    "source_id": "aemeath_s3",
                }
            )
    if character_id == "aemeath" and _sequence(characters.get("aemeath")) >= 3 and action_id in AEMEATH_OVERDRIVE_IDS:
        context["coefficient_multiplier"] *= 1.4
        context["events"].append(
            {"event_type": "aemeath_s3_overdrive_coefficient", "coefficient_multiplier": 1.4, "source_id": "aemeath_s3"}
        )
    if character_id == "aemeath" and _sequence(characters.get("aemeath")) >= 3 and hit_category == "normal":
        active_mode = _active_aemeath_mode(state)
        mode = "fusion" if active_mode == "fusion_burst" else "tune"
        crit_bonus = float(account_state.get(f"aemeath_s3_{mode}_crit_damage_bonus", 0.0) or 0.0)
        if crit_bonus > 0.0:
            context["crit_damage_add"] += crit_bonus
            context["events"].append(
                {
                    "event_type": "aemeath_s3_contributor_crit_damage_formula",
                    "active_mode": active_mode,
                    "crit_damage_add": crit_bonus,
                    "contributors": list(account_state.get(f"aemeath_s3_{mode}_contributors", []) or []),
                    "source_id": "aemeath_s3",
                }
            )
    if character_id == "aemeath" and _sequence(characters.get("aemeath")) >= 6 and action_id in AEMEATH_LIBERATION_IDS:
        context["target_deepen_add"] += 0.40
        context["damage_amp_add"] += 0.40
        context["events"].append(
            {"event_type": "aemeath_s6_liberation_target_deepen", "target_deepen_add": 0.40, "source_id": "aemeath_s6"}
        )
    if character_id == "lynae" and _sequence(characters.get("lynae")) >= 1 and action_id in LYNAE_LIGHT_LEAP_IDS:
        context["coefficient_add"] += 1.20
        context["events"].append(
            {"event_type": "lynae_s1_light_leap_coefficient", "coefficient_add": 1.20, "source_id": "lynae_s1"}
        )
    if character_id == "lynae" and _sequence(characters.get("lynae")) >= 2 and hit_category == "normal":
        context["damage_amp_add"] += 0.25
        context["events"].append(
            {
                "event_type": "lynae_s2_self_deepen_formula",
                "damage_amp_add": 0.25,
                "source_id": "lynae_s2",
            }
        )
    marker_active = (
        float(getattr(state, "interfered_marker_remaining", 0.0) or 0.0) > 0.0
        or bool(state.character_mechanics_state.get("mornye", {}).get("observation_marker_active", False))
    )
    if _sequence(characters.get("mornye")) >= 2 and marker_active and hit_category == "normal":
        crit_bonus = mornye_s2_marker_crit_damage(float(getattr(characters.get("mornye"), "energy_regen", 1.0) or 1.0))
        if crit_bonus > 0.0:
            context["crit_damage_add"] += crit_bonus
            context["events"].append(
                {
                    "event_type": "mornye_s2_marker_crit_damage_formula",
                    "crit_damage_add": crit_bonus,
                    "energy_regen": float(getattr(characters.get("mornye"), "energy_regen", 1.0) or 1.0),
                    "source_id": "mornye_s2",
                }
            )
    return context


def build_account_generated_damage_context(
    *,
    state: Any,
    characters: dict[str, Any],
    packet: Any,
    hit_index: int = 0,
    source_action: Any | None = None,
) -> dict[str, Any]:
    if not _account_state_enabled_from_parts(state, characters):
        return {}
    packet_id = str(getattr(packet, "id", ""))
    source_character_id = str(getattr(packet, "source_character_id", "") or "")
    context: dict[str, Any] = {"damage_amp_add": 0.0, "target_deepen_add": 0.0, "events": []}
    sequence = _sequence(characters.get("aemeath"))
    if source_character_id != "aemeath":
        return context
    account_state = state.character_mechanics_state.setdefault("_account_constellation", {})
    if (
        sequence >= 2
        and packet_id in {"aemeath_seraphic_duet_tune_rupture_followup", "aemeath_seraphic_duet_tune_rupture_enhanced_followup"}
        and str(getattr(source_action, "id", "")) in AEMEATH_S2_ENHANCED_SKILL_IDS
    ):
        before = min(5, max(0, int(account_state.get("aemeath_s2_stacks", 0) or 0)))
        after = min(5, before + 1)
        bonus = before * 0.20
        account_state["aemeath_s2_stacks"] = after
        account_state["aemeath_s2_remaining"] = 1.0
        context["damage_amp_add"] = bonus
        context["events"].append(
            {
                "event_type": "aemeath_s2_tune_stack_generated_hit",
                "hit_index": hit_index,
                "stacks_before": before,
                "stacks_after": after,
                "damage_amp_add": bonus,
                "remaining_seconds": 1.0,
                "source_id": "aemeath_s2",
            }
        )
    action_id = str(getattr(source_action, "id", "") or getattr(packet, "source_action_id", ""))
    if sequence >= 6 and action_id in AEMEATH_LIBERATION_IDS:
        context["target_deepen_add"] += 0.40
        context["damage_amp_add"] += 0.40
        context["events"].append(
            {"event_type": "aemeath_s6_liberation_target_deepen", "target_deepen_add": 0.40, "source_id": "aemeath_s6"}
        )
    if sequence < 6 or packet_id not in AEMEATH_S6_FIXED_CRIT_PACKET_IDS:
        return context
    context.update({
        "crit_rate_override": 0.80,
        "crit_damage_override": 2.75,
        "expected_crit_multiplier": 2.40,
    })
    context["events"].append(
            {
                "event_type": "aemeath_s6_fixed_crit_formula",
                "crit_rate_after_override": 0.80,
                "crit_damage_after_override": 2.75,
                "expected_crit_multiplier": 2.40,
                "source_id": "aemeath_s6",
            }
    )
    return context


def build_account_tune_response_damage_context(
    *,
    state: Any,
    characters: dict[str, Any],
    response_id: str,
    source_character_id: str,
) -> dict[str, Any]:
    """Return source-classified account modifiers for a real Tune response."""
    context: dict[str, Any] = {"events": []}
    if not _account_state_enabled_from_parts(state, characters):
        return context
    if (
        response_id != "aemeath_starburst"
        or source_character_id != "aemeath"
        or _sequence(characters.get("aemeath")) < 6
        or _active_aemeath_mode(state) != "tune_rupture"
    ):
        return context
    context.update(
        {
            "crit_rate_override": 0.80,
            "crit_damage_override": 2.75,
            "expected_crit_multiplier": 2.40,
        }
    )
    context["events"].append(
        {
            "event_type": "aemeath_s6_fixed_crit_real_tune_response",
            "response_id": response_id,
            "crit_rate_after_override": 0.80,
            "crit_damage_after_override": 2.75,
            "expected_crit_multiplier": 2.40,
            "source_id": "aemeath_s6",
        }
    )
    return context


def initialize_account_constellation_state(
    characters: dict[str, Any],
    scope: Any,
    precombat_elapsed_seconds: float,
    *,
    optical_sampling_active: bool = False,
    mode: str = "tune_rupture",
) -> dict[str, Any]:
    normalized_scope = validate_account_single_boss_scope(scope)
    state: dict[str, Any] = {
        "scope": normalized_scope,
        "precombat_elapsed_seconds": float(precombat_elapsed_seconds),
        "unsupported_effects": unsupported_constellation_effects(),
        "aemeath": {
            "sequence": _sequence(characters.get("aemeath")),
            "radiance_quick_charge_ready": False,
            "radiance_precombat_rule_triggered": False,
            "sync_gained": 0.0,
            "s2_tune_stacks": 0,
            "s3_mode": mode,
            "s3_tune_contributors": [],
            "s3_fusion_contributors": [],
            "s4_party_bonus": {"active": False, "value": 0.0, "expires_at": 0.0},
            "s6_trajectories": 0,
        },
        "lynae": {
            "sequence": _sequence(characters.get("lynae")),
            "overflow_restored_precombat": 0.0,
            "optical_sampling_active_precombat": bool(optical_sampling_active),
            "collective_interference_cap_bonus": 0,
            "outro_buff": None,
        },
        "mornye": {
            "sequence": _sequence(characters.get("mornye")),
            "marker_active": False,
            "marker_expires_at": 0.0,
            "distributed_array_last_trigger_at": None,
            "starfield_last_trigger_at": None,
        },
    }
    apply_precombat_constellation_state(
        state,
        precombat_elapsed_seconds,
        optical_sampling_active=optical_sampling_active,
    )
    return state


def apply_precombat_constellation_state(
    state: dict[str, Any],
    precombat_elapsed_seconds: float,
    *,
    optical_sampling_active: bool = False,
) -> dict[str, Any]:
    elapsed = float(precombat_elapsed_seconds)
    state["precombat_elapsed_seconds"] = elapsed
    aemeath = state.setdefault("aemeath", {})
    lynae = state.setdefault("lynae", {})
    if int(aemeath.get("sequence", 0) or 0) >= 1 and elapsed > 4.0:
        aemeath["radiance_quick_charge_ready"] = True
        aemeath["radiance_precombat_rule_triggered"] = True
    else:
        aemeath["radiance_quick_charge_ready"] = False
        aemeath["radiance_precombat_rule_triggered"] = False
    if int(lynae.get("sequence", 0) or 0) >= 1 and elapsed > 2.0 and optical_sampling_active:
        lynae["overflow_restored_precombat"] = 120.0
    else:
        lynae["overflow_restored_precombat"] = 0.0
    lynae["optical_sampling_active_precombat"] = bool(optical_sampling_active)
    return state


def _apply_aemeath_helper(state: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    aemeath = state.setdefault("aemeath", {})
    sequence = int(aemeath.get("sequence", 0) or 0)
    event_type = str(event.get("event_type", ""))
    if sequence >= 1 and event_type == "heavy_crit_damage":
        event["crit_damage"] = aemeath_s1_heavy_crit_damage(
            event.get("crit_damage", 1.0),
            event.get("action_id", ""),
            bool(event.get("instant_response_active", False)),
        )
    if sequence >= 1 and event_type == "charged_ii_sync":
        gained = aemeath_s1_charged_sync_gain(
            bool(aemeath.get("radiance_quick_charge_ready", False)),
            bool(event.get("finale_prereq_absent", True)),
            event.get("action_id", ""),
        )
        aemeath["sync_gained"] = float(aemeath.get("sync_gained", 0.0) or 0.0) + gained
        event["sync_gained"] = gained
    if sequence >= 2 and event_type == "tune_sequential_hit":
        result = aemeath_s2_tune_sequential_multipliers(
            hit_count=int(event.get("hit_count", 1)),
            existing_stacks=int(aemeath.get("s2_tune_stacks", 0) or 0),
        )
        aemeath["s2_tune_stacks"] = result["final_stacks"]
        event.update(result)
    if sequence >= 3 and event_type == "register_contributor":
        event.update(
            aemeath_s3_register_contributor(
                state,
                str(event.get("mode", aemeath.get("s3_mode", "tune_rupture"))),
                str(event.get("character_id", "")),
            )
        )
    if sequence >= 4 and event_type == "party_bonus":
        event.update(aemeath_s4_apply_party_bonus(state, now=float(event.get("now", 0.0) or 0.0)))
    if sequence >= 6 and event_type == "trajectory_gain":
        result = aemeath_s6_trajectory_gain(
            int(aemeath.get("s6_trajectories", 0) or 0),
            base_gain=int(event.get("base_gain", 0) or 0),
            source=str(event.get("source", "normal")),
            enhanced_skill=bool(event.get("enhanced_skill", False)),
            tune_response=bool(event.get("tune_response", False)),
            fusion_application=bool(event.get("fusion_application", False)),
        )
        aemeath["s6_trajectories"] = result["new_total"]
        event.update(result)
    return event


def _apply_lynae_helper(state: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    lynae = state.setdefault("lynae", {})
    sequence = int(lynae.get("sequence", 0) or 0)
    event_type = str(event.get("event_type", ""))
    if sequence >= 1 and event_type == "light_leap_multiplier":
        event["multiplier"] = lynae_s1_light_leap_multiplier(float(event.get("base_multiplier", 1.0) or 1.0))
    if sequence >= 1 and event_type == "paint_schedule":
        event.update(lynae_s1_paint_schedule())
    if sequence >= 2 and event_type == "outro_apply":
        buff = lynae_s2_apply_outro_buff(
            now=float(event.get("now", 0.0) or 0.0),
            source_character_id=str(event.get("source_character_id", "lynae")),
            target_character_id=str(event.get("target_character_id", "")),
        )
        lynae["outro_buff"] = buff
        event.update(buff)
    if sequence >= 2 and event_type == "outro_switch":
        buff = lynae_s2_outro_after_switch(lynae.get("outro_buff"), str(event.get("new_active_character_id", "")))
        lynae["outro_buff"] = buff
        event["outro_buff"] = buff
    return event


def _apply_mornye_helper(state: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    mornye = state.setdefault("mornye", {})
    sequence = int(mornye.get("sequence", 0) or 0)
    event_type = str(event.get("event_type", ""))
    now = float(event.get("now", 0.0) or 0.0)
    if sequence >= 1 and event_type == "marker_apply":
        mornye["marker_active"] = True
        mornye["marker_expires_at"] = now + 20.0
        event["marker_duration_seconds"] = 20.0
    if sequence >= 2 and event_type == "marker_crit":
        marker_active = bool(mornye.get("marker_active", False)) and now < float(mornye.get("marker_expires_at", 0.0) or 0.0)
        event["crit_damage_bonus"] = (
            mornye_s2_marker_crit_damage(float(event.get("energy_regen", 1.0) or 1.0)) if marker_active else 0.0
        )
    if sequence >= 3 and event_type == "distributed_array":
        event.update(mornye_s3_distributed_array(state, now=now))
    if sequence >= 3 and event_type == "same_action_with_starfield":
        event.update(mornye_s3_same_action_with_starfield(state, now=now))
    return event


def collect_constellation_diagnostics(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "scope_id": (state.get("scope") or {}).get("scope_id"),
        "precombat_elapsed_seconds": float(state.get("precombat_elapsed_seconds", 0.0) or 0.0),
        "aemeath_radiance_quick_charge_ready": bool((state.get("aemeath") or {}).get("radiance_quick_charge_ready", False)),
        "lynae_overflow_restored_precombat": float((state.get("lynae") or {}).get("overflow_restored_precombat", 0.0) or 0.0),
        "unsupported_effects": unsupported_constellation_effects(),
        "unsupported_effect_runtime_policy": "not evaluated: unsupported by single-boss no-death scope",
        "account_party_configured": False,
        "account_baseline_configured": False,
        "training_or_search_executed": False,
    }


def build_account_observation_labels() -> list[str]:
    labels = [f"legacy_v5.{index:03d}" for index in range(314)]
    labels.extend(ACCOUNT_OBSERVATION_EXTRA_LABELS)
    assert len(labels) == ACCOUNT_OBSERVATION_SHAPE
    return labels


def build_account_observation_values(simulation_or_state: Any | None = None) -> list[float]:
    if simulation_or_state is not None and hasattr(simulation_or_state, "state"):
        from env.observation_features import build_observation_values as build_v5_observation_values

        simulation = simulation_or_state
        values = list(build_v5_observation_values(simulation))
        state = simulation.state.character_mechanics_state.setdefault("_account_constellation", {})
        current_time = float(simulation.state.combat_time)
        characters = getattr(simulation, "characters", {})
    else:
        values = [0.0] * 314
        state = simulation_or_state or {}
        current_time = 0.0
        characters = {}
    aemeath = state.get("aemeath") or {}
    lynae = state.get("lynae") or {}
    mornye = state.get("mornye") or {}
    account = state if "_account_constellation" not in state else state.get("_account_constellation", {})
    if "scope" not in state and any(key.startswith("aemeath_") or key.startswith("lynae_") or key.startswith("mornye_") for key in state):
        account = state
    precombat = float(state.get("precombat_elapsed_seconds", 0.0) or 0.0)
    if account:
        precombat = float(account.get("precombat_elapsed_seconds", precombat) or 0.0)
    s4 = aemeath.get("s4_party_bonus") or {}
    aemeath_s2_remaining = float(account.get("aemeath_s2_remaining", 0.0) or 0.0)
    aemeath_s2_stacks = int(account.get("aemeath_s2_stacks", aemeath.get("s2_tune_stacks", 0)) or 0)
    mornye_state = getattr(simulation_or_state, "state", None)
    if mornye_state is not None:
        mornye_mech = mornye_state.character_mechanics_state.get("mornye", {})
        marker_remaining = float(mornye_mech.get("observation_marker_remaining", 0.0) or 0.0)
        marker_active = bool(mornye_mech.get("observation_marker_active", False))
        energy_regen = float((characters.get("mornye").energy_regen if "mornye" in characters else 1.0) or 1.0)
    else:
        marker_remaining = max(0.0, float(mornye.get("marker_expires_at", 0.0) or 0.0) - current_time)
        marker_active = bool(mornye.get("marker_active", False))
        energy_regen = 1.0
    s4_remaining = float(account.get("aemeath_s4_remaining", 0.0) or 0.0)
    lynae_mech = getattr(simulation_or_state, "state", None).character_mechanics_state.get("lynae", {}) if hasattr(simulation_or_state, "state") else {}
    paint_remaining = float(lynae_mech.get("spray_paint_window_remaining", 0.0) or 0.0)
    values.extend(
        [
            1.0,
            1.0,
            1.0,
            min(precombat / 10.0, 1.0),
            1.0 if account.get("aemeath_radiance_quick_charge_ready", aemeath.get("radiance_quick_charge_ready")) else 0.0,
            float(account.get("lynae_precombat_overflow_restored", lynae.get("overflow_restored_precombat", 0.0)) or 0.0) / 120.0,
            float(aemeath_s2_stacks) / 5.0,
            len(account.get("aemeath_s3_tune_contributors", aemeath.get("s3_tune_contributors") or []) or []) / 3.0,
            len(account.get("aemeath_s3_fusion_contributors", aemeath.get("s3_fusion_contributors") or []) or []) / 2.0,
            min(s4_remaining / 30.0, 1.0) if s4_remaining else (min(float(s4.get("expires_at", 0.0) or 0.0) / 30.0, 1.0) if s4.get("active") else 0.0),
            _authoritative_trajectory_ratio(simulation_or_state, account, aemeath, characters),
            min(paint_remaining / 10.0, 1.0),
            0.25 if float(account.get("lynae_s2_outro_remaining", 0.0) or 0.0) > 0.0 else float((lynae.get("outro_buff") or {}).get("general_all_damage_deepen", 0.0) or 0.0),
            min(marker_remaining / 20.0, 1.0),
            mornye_s2_marker_crit_damage(energy_regen) if marker_active else 0.0,
            min(float(account.get("mornye_s3_icd_remaining", 0.0) or 0.0) / 25.0, 1.0),
        ]
    )
    assert len(values) == ACCOUNT_OBSERVATION_SHAPE
    return values


def unsupported_constellation_effects() -> list[str]:
    return [
        "aemeath_s1_kill_trajectory_transfer",
        "aemeath_s2_kill_detonation",
        "aemeath_s5_all_effects",
        "enemy_movement_or_pull",
        "player_survival_effects",
    ]


def aemeath_s1_heavy_crit_damage(crit_damage: float, action_id: str, instant_response_active: bool) -> float:
    eligible = str(action_id) in AEMEATH_S1_HEAVY_ELIGIBLE_ACTION_IDS
    return float(crit_damage) + 3.0 if instant_response_active and eligible else float(crit_damage)


def aemeath_s1_charged_sync_gain(
    radiance_quick_charge_ready: bool,
    finale_prereq_absent: bool,
    action_id: str,
) -> float:
    if radiance_quick_charge_ready and finale_prereq_absent and str(action_id) in AEMEATH_CHARGED_II_ACTION_IDS:
        return 100.0
    return 0.0


def aemeath_s2_skill_multiplier(base_multiplier: float, *, enhanced: bool, mechanic_packet: bool = False) -> float:
    return float(base_multiplier) * (2.0 if enhanced and not mechanic_packet else 1.0)


def aemeath_s2_tune_sequential_multipliers(
    *,
    hit_count: int,
    existing_stacks: int = 0,
    per_stack: float = 0.20,
    max_stacks: int = 5,
) -> dict[str, Any]:
    stacks = max(0, min(int(existing_stacks), max_stacks))
    bonuses: list[float] = []
    for _ in range(max(0, int(hit_count))):
        bonuses.append(round(stacks * float(per_stack), 10))
        stacks = min(max_stacks, stacks + 1)
    multipliers = [1.0 + bonus for bonus in bonuses]
    return {
        "per_hit_final_damage_bonuses": bonuses,
        "per_hit_multipliers": multipliers,
        "aggregate_multiplier_sum": sum(multipliers),
        "aggregate_equivalent_multiplier": (sum(multipliers) / len(multipliers)) if multipliers else 1.0,
        "final_stacks": stacks,
        "duration_seconds": 1.0,
        "refreshes_duration": True,
    }


def aemeath_s2_fusion_final_damage_multiplier(
    *,
    removed_trajectory_count: int,
    enhancement_state: bool,
) -> dict[str, float]:
    """Source formula for an existing Fusion-effect settlement, not a damage packet."""
    stacks = max(0, int(removed_trajectory_count))
    enhancement_bonus = 4.0 if enhancement_state else 2.0
    per_trajectory = 0.15 if enhancement_state else 0.10
    final_damage_increase = enhancement_bonus + per_trajectory * stacks
    return {
        "removed_trajectory_count": float(stacks),
        "enhancement_state_final_damage_increase": enhancement_bonus,
        "trajectory_final_damage_increase": per_trajectory * stacks,
        "final_damage_increase": final_damage_increase,
        "final_damage_multiplier": 1.0 + final_damage_increase,
    }


def aemeath_s3_register_contributor(state: dict[str, Any], mode: str, character_id: str) -> dict[str, Any]:
    aemeath = state.setdefault("aemeath", {})
    if mode == "fusion_burst":
        key = "s3_fusion_contributors"
        max_count = 2
        per_contributor = 0.30
    else:
        key = "s3_tune_contributors"
        max_count = 3
        per_contributor = 0.20
    contributors = list(aemeath.get(key) or [])
    if character_id and character_id not in contributors and len(contributors) < max_count:
        contributors.append(character_id)
    aemeath[key] = contributors
    bonus = min(len(contributors) * per_contributor, 0.60)
    return {
        "mode": mode,
        "contributors": contributors,
        "crit_damage_bonus": bonus,
        "finale_deepen": 0.25 if len(contributors) >= max_count else 0.0,
    }


def aemeath_s3_reset_for_mode_switch(state: dict[str, Any], mode: str) -> None:
    aemeath = state.setdefault("aemeath", {})
    aemeath["s3_mode"] = mode
    aemeath["s3_tune_contributors"] = []
    aemeath["s3_fusion_contributors"] = []


def aemeath_s4_apply_party_bonus(state: dict[str, Any], *, now: float) -> dict[str, Any]:
    buff = {"active": True, "value": 0.20, "expires_at": float(now) + 30.0, "stacks": 1}
    state.setdefault("aemeath", {})["s4_party_bonus"] = buff
    return {"party_all_attribute_damage_bonus": 0.20, "duration_seconds": 30.0, "stacks": 1}


def aemeath_s5_unsupported_effects() -> dict[str, Any]:
    return {"implemented": False, "runtime_value": 0.0, "unsupported_effects": ["aemeath_s5_all_effects"]}


def aemeath_s6_liberation_deepen(character_id: str, damage_category: str) -> float:
    return 0.40 if character_id == "aemeath" and damage_category == "resonance_liberation" else 0.0


def aemeath_s6_fixed_crit_expected_multiplier(crit_rate: float = 0.80, crit_damage: float = 2.75) -> float:
    return 1.0 + float(crit_rate) * (float(crit_damage) - 1.0)


def aemeath_s6_trajectory_gain(
    current_total: int,
    *,
    base_gain: int,
    source: str,
    enhanced_skill: bool = False,
    tune_response: bool = False,
    fusion_application: bool = False,
) -> dict[str, Any]:
    gain = max(0, int(base_gain))
    extra_gain = 0
    if enhanced_skill:
        extra_gain += 10
    if tune_response:
        extra_gain += 10
    if fusion_application:
        extra_gain += 1
    new_total = min(60, max(0, int(current_total)) + gain + extra_gain)
    return {"base_gain_after_s6": gain, "extra_gain": extra_gain, "new_total": new_total, "cap": 60}


def lynae_s1_light_leap_multiplier(base_multiplier: float) -> float:
    return float(base_multiplier) + 1.20


def lynae_s1_paint_schedule(
    *,
    duration_frames: int = 600,
    first_check_frames: int = 1,
    tick_interval_frames: int = 120,
) -> dict[str, Any]:
    ticks = list(range(first_check_frames, duration_frames, tick_interval_frames))
    return {
        "duration_frames": duration_frames,
        "duration_seconds": duration_frames / 60.0,
        "first_check_frames": first_check_frames,
        "tick_interval_frames": tick_interval_frames,
        "application_tick_frames": ticks,
        "endpoint_tick_excluded": duration_frames + first_check_frames not in ticks,
        "pull_diagnostic_tick_frames": [360] if duration_frames >= 360 else [],
        "pull_runtime_effect": 0.0,
    }


def lynae_s1_precombat_overflow(precombat_elapsed_seconds: float, optical_sampling_active: bool) -> float:
    return 120.0 if float(precombat_elapsed_seconds) > 2.0 and optical_sampling_active else 0.0


def lynae_s2_self_deepen() -> float:
    return 0.25


def lynae_s2_outro_totals() -> dict[str, float]:
    return {
        "base_general_all_damage_deepen": 0.15,
        "s2_general_all_damage_deepen": 0.25,
        "general_all_damage_deepen_total": 0.40,
        "liberation_specific_deepen": 0.25,
        "liberation_total_deepen": 0.65,
    }


def lynae_s2_apply_outro_buff(
    *,
    now: float,
    source_character_id: str,
    target_character_id: str,
) -> dict[str, Any]:
    totals = lynae_s2_outro_totals()
    return {
        "source_character_id": source_character_id,
        "target_character_id": target_character_id,
        "active": True,
        "expires_at": float(now) + 14.0,
        "ends_early_on_another_switch": True,
        **totals,
    }


def lynae_s2_outro_after_switch(buff: dict[str, Any] | None, new_active_character_id: str) -> dict[str, Any] | None:
    if not buff:
        return None
    if new_active_character_id != buff.get("target_character_id"):
        cleared = dict(buff)
        cleared["active"] = False
        cleared["ended_early_by_switch"] = True
        return cleared
    return dict(buff)


def lynae_s2_collective_interference_cap(base_cap: int) -> int:
    return int(base_cap) + 1


def mornye_s1_marker_duration_seconds() -> float:
    return 20.0


def mornye_s1_observation_marker_applies_interfered_marker() -> dict[str, bool]:
    return {"observation_marker_applied": True, "interfered_marker_applied": True}


def mornye_dynamic_energy_regen_excess_amp(energy_regen: float, *, cap: float = 0.40) -> float:
    excess_percentage_points = max(0.0, (float(energy_regen) - 1.0) * 100.0)
    return min(cap, excess_percentage_points * 0.0025)


def mornye_s2_marker_crit_damage(energy_regen: float, *, cap: float = 0.32) -> float:
    excess_percentage_points = max(0.0, (float(energy_regen) - 1.0) * 100.0)
    return min(cap, excess_percentage_points * 0.002)


def mornye_s2_field_off_tune_efficiency(base_bonus: float = 0.50) -> float:
    return float(base_bonus) + 0.20


def mornye_s3_distributed_array(state: dict[str, Any], *, now: float) -> dict[str, Any]:
    mornye = state.setdefault("mornye", {})
    last = mornye.get("distributed_array_last_trigger_at")
    ready = last is None or float(now) - float(last) >= 25.0
    if ready:
        mornye["distributed_array_last_trigger_at"] = float(now)
    return {
        "triggered": ready,
        "concerto_gain": 25.0 if ready else 0.0,
        "relative_momentum_gain": 100.0 if ready else 0.0,
        "icd_seconds": 25.0,
    }


def mornye_starfield_r5_concerto(state: dict[str, Any], *, now: float) -> dict[str, Any]:
    mornye = state.setdefault("mornye", {})
    last = mornye.get("starfield_last_trigger_at")
    ready = last is None or float(now) - float(last) >= 20.0
    if ready:
        mornye["starfield_last_trigger_at"] = float(now)
    return {"triggered": ready, "concerto_gain": 16.0 if ready else 0.0, "icd_seconds": 20.0}


def mornye_s3_same_action_with_starfield(state: dict[str, Any], *, now: float) -> dict[str, Any]:
    distributed = mornye_s3_distributed_array(state, now=now)
    starfield = mornye_starfield_r5_concerto(state, now=now)
    return {
        "distributed_array": distributed,
        "starfield_r5": starfield,
        "concerto_gain_total": distributed["concerto_gain"] + starfield["concerto_gain"],
        "relative_momentum_gain_total": distributed["relative_momentum_gain"],
    }


def _sequence(character: Any) -> int:
    if character is None:
        return 0
    get = character.get if isinstance(character, dict) else lambda key, default=None: getattr(character, key, default)
    sequence = get("sequence", None)
    constellation = get("constellation", {}) or {}
    if sequence is None and isinstance(constellation, dict):
        sequence = constellation.get("sequence")
    return int(sequence or 0)


def _apply_aemeath_runtime(simulation: Any, action: Any, result: Any) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    sequence = _sequence_for(simulation, "aemeath")
    if sequence <= 0:
        return events
    account_state = simulation.state.character_mechanics_state.setdefault("_account_constellation", {})
    aemeath_state = simulation.state.character_mechanics_state.setdefault("aemeath", {})
    action_id = str(action.id)
    radiance_quick_charge_ready = bool(aemeath_state.get("account_radiance_quick_charge_ready", False))
    finale_prereq_absent = not bool(aemeath_state.get("heavenfall_unbound", False))
    sync_gain = aemeath_s1_charged_sync_gain(
        radiance_quick_charge_ready,
        finale_prereq_absent,
        action_id,
    )
    if sequence >= 1 and sync_gain > 0.0:
        before = float(aemeath_state.get("synchronization_rate", 0.0) or 0.0)
        after = min(200.0, before + sync_gain)
        aemeath_state["synchronization_rate"] = after
        events.append({"event_type": "aemeath_s1_charged_ii_sync", "sync_before": before, "sync_after": after, "sync_gained": after - before, "finale_prereq_absent": finale_prereq_absent})
    if radiance_quick_charge_ready and action_id in AEMEATH_S1_HEAVY_ELIGIBLE_ACTION_IDS:
        aemeath_state["account_radiance_quick_charge_ready"] = False
        events.append(
            {
                "event_type": "aemeath_s1_radiance_quick_charge_consumed",
                "action_id": action_id,
            }
        )
    if sequence >= 4 and action_id in AEMEATH_S4_TRIGGER_IDS:
        events.append({"event_type": "aemeath_s4_party_buff_confirmed", "buff_id": ACCOUNT_AEMEATH_S4_BUFF_ID})
    for event in events:
        _record_event(simulation, result, **event)
    return events


def _apply_lynae_runtime(simulation: Any, action: Any, result: Any) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    sequence = _sequence_for(simulation, "lynae")
    if sequence <= 0:
        return events
    action_id = str(action.id)
    if sequence >= 2:
        events.append({"event_type": "lynae_s2_self_deepen_intrinsic", "value": 0.25})
    for event in events:
        _record_event(simulation, result, **event)
    return events


def _apply_mornye_runtime(simulation: Any, action: Any, result: Any) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    sequence = _sequence_for(simulation, "mornye")
    if sequence <= 0:
        return events
    account_state = simulation.state.character_mechanics_state.setdefault("_account_constellation", {})
    mornye_state = simulation.state.character_mechanics_state.setdefault("mornye", {})
    action_id = str(action.id)
    if sequence >= 1 and action_id in MORNYE_OBSERVATION_MARKER_IDS:
        mornye_state["observation_marker_active"] = True
        mornye_state["observation_marker_remaining"] = 20.0
        simulation.state.interfered_marker_remaining = 20.0
        simulation.state.interfered_marker_applied_count += 1
        amp = mornye_dynamic_energy_regen_excess_amp(simulation.characters["mornye"].energy_regen)
        simulation.state.interfered_marker_damage_taken_amp = amp
        buff = _buff(
            "mornye_interfered_marker_damage_amp",
            "Mornye Interfered Marker dynamic damage amp",
            "dmg_taken",
            amp,
            20.0,
            target_scope="enemy",
            metadata={"dynamic_value": amp, "account_s1_direct_application": True},
        )
        simulation.buffs[buff.id] = buff
        from simulator.buff_system import apply_buff

        apply_buff(simulation.state, buff, "mornye")
        events.append({"event_type": "mornye_s1_marker", "remaining_seconds": 20.0, "damage_amp": amp})
    if sequence >= 2 and bool(mornye_state.get("observation_marker_active", False)):
        crit = mornye_s2_marker_crit_damage(simulation.characters["mornye"].energy_regen)
        events.append({"event_type": "mornye_s2_marker_crit_damage_runtime_active", "crit_damage_bonus": crit})
    if sequence >= 2 and action_id in {"mornye_heavy_geopotential_shift", "mornye_skill_optimal_solution", MORNYE_DISTRIBUTED_ARRAY_ID}:
        account_state["mornye_s2_field_remaining"] = max(
            float(account_state.get("mornye_s2_field_remaining", 0.0) or 0.0),
            float(mornye_state.get("syntony_field_remaining", 0.0) or 0.0),
            25.0 if action_id in {"mornye_heavy_geopotential_shift", MORNYE_DISTRIBUTED_ARRAY_ID} else 0.0,
        )
        events.append({"event_type": "mornye_s2_field_off_tune_efficiency", "base_bonus": 0.50, "s2_bonus": 0.20, "total_rate": 1.70})
    if sequence >= 3 and action_id == MORNYE_DISTRIBUTED_ARRAY_ID:
        ready = float(account_state.get("mornye_s3_icd_remaining", 0.0) or 0.0) <= 0.0
        if ready:
            mstate = simulation.state.character_states.setdefault("mornye", {})
            before, gained, after, ready_after, wasted = add_concerto_energy(sync_concerto_state(simulation.state, "mornye"), 25.0)
            simulation.state.concerto_energy["mornye"] = after
            before_momentum = float(mornye_state.get("relative_momentum", 0.0) or 0.0)
            cap = float(mornye_state.get("relative_momentum_cap", 100.0) or 100.0)
            mornye_state["relative_momentum"] = min(cap, before_momentum + 100.0)
            account_state["mornye_s3_icd_remaining"] = 25.0
            result.concerto_energy_gained += gained
            result.concerto_gain += gained
            result.concerto_after = after
            result.concerto_ready_after = ready_after
            result.relative_momentum_gain += mornye_state["relative_momentum"] - before_momentum
            events.append(
                {
                    "event_type": "mornye_s3_distributed_array",
                    "concerto_before": before,
                    "concerto_gain": gained,
                    "concerto_after": after,
                    "concerto_wasted": wasted,
                    "relative_momentum_gain": mornye_state["relative_momentum"] - before_momentum,
                    "icd_seconds": 25.0,
                }
            )
    for event in events:
        _record_event(simulation, result, **event)
    return events


def _apply_result_damage_multiplier(simulation: Any, result: Any, multiplier: float, event_type: str) -> dict[str, Any]:
    base = float(result.normal_damage or result.total_action_damage or 0.0)
    delta = base * (float(multiplier) - 1.0)
    event = _apply_result_damage_delta(simulation, result, delta, event_type)
    event["multiplier"] = float(multiplier)
    return event


def _apply_result_damage_delta(simulation: Any, result: Any, delta: float, event_type: str) -> dict[str, Any]:
    delta = max(0.0, float(delta or 0.0))
    if delta <= 0.0:
        return {"event_type": event_type, "damage_delta": 0.0}
    result.normal_damage += delta
    result.damage += delta
    result.direct_action_damage += delta
    result.total_action_damage += delta
    result.damage_before_cutoff += delta
    result.total_damage_after += delta
    simulation.state.total_damage += delta
    if simulation.state.damage_log:
        log = simulation.state.damage_log[-1]
        for key in ("normal_damage", "direct_action_damage", "total_action_damage", "damage"):
            if key in log:
                log[key] = float(log.get(key, 0.0) or 0.0) + delta
        log.setdefault("account_constellation_damage_delta", 0.0)
        log["account_constellation_damage_delta"] += delta
    return {"event_type": event_type, "damage_delta": delta}


def _record_event(simulation: Any, result: Any | None = None, event_type: str | None = None, **payload: Any) -> None:
    event = {"event_type": event_type, **payload} if event_type else dict(payload)
    account_state = simulation.state.character_mechanics_state.setdefault("_account_constellation", {})
    account_state.setdefault("events", []).append(event)
    if result is not None:
        result.account_constellation_events.append(event)


def _apply_aemeath_s4_buff(simulation: Any, result: Any | None) -> None:
    account_state = simulation.state.character_mechanics_state.setdefault("_account_constellation", {})
    buff = _buff(
        ACCOUNT_AEMEATH_S4_BUFF_ID,
        "Aemeath S4 party all attribute damage",
        "damage_bonus",
        0.20,
        30.0,
        target_scope="party",
        stat_modifiers={},
        metadata={"all_attribute_damage_bonus": 0.20, "source_id": "aemeath_s4"},
    )
    simulation.buffs[buff.id] = buff
    from simulator.buff_system import apply_buff

    apply_buff(simulation.state, buff, "aemeath")
    account_state["aemeath_s4_remaining"] = 30.0
    _record_event(
        simulation,
        result,
        "aemeath_s4_party_buff",
        buff_id=buff.id,
        remaining_seconds=30.0,
        value=0.20,
    )


def _register_account_runtime_contributors(simulation: Any, action: Any, result: Any) -> None:
    if _sequence_for(simulation, "aemeath") < 3:
        return
    actor = str(getattr(action, "character_id", "") or getattr(result, "actor_character_id", "") or "")
    if actor not in {"aemeath", "lynae", "mornye"}:
        return
    account_state = simulation.state.character_mechanics_state.setdefault("_account_constellation", {})
    mode = _active_aemeath_mode(simulation.state)
    prior_mode = account_state.get("aemeath_s3_active_mode")
    if prior_mode not in {None, mode}:
        _reset_runtime_contributors(account_state)
    account_state["aemeath_s3_active_mode"] = mode
    tags = set(getattr(result, "emitted_mechanic_event_tags", []) or [])
    if "tune_rupture_shifting" in tags:
        _register_contributor_list(account_state, "tune", actor, max_count=3, crit_per=0.20)
        _record_event(simulation, result, "aemeath_s3_tune_contributor_registered", character_id=actor)
    elif (
        str(getattr(action, "action_type", "") or "") == "tune_break"
        and float(getattr(result, "tune_break_damage", 0.0) or 0.0) > 0.0
    ):
        _register_contributor_list(account_state, "tune", actor, max_count=3, crit_per=0.20)
        _record_event(simulation, result, "aemeath_s3_tune_contributor_registered", character_id=actor)
    if "fusion_burst" in tags:
        _register_contributor_list(account_state, "fusion", actor, max_count=2, crit_per=0.30)
        _record_event(simulation, result, "aemeath_s3_fusion_contributor_registered", character_id=actor)


def _register_contributor_list(
    account_state: dict[str, Any],
    mode: str,
    character_id: str,
    *,
    max_count: int,
    crit_per: float,
) -> None:
    key = f"aemeath_s3_{mode}_contributors"
    contributors = list(account_state.get(key, []) or [])
    if character_id not in contributors and len(contributors) < max_count:
        contributors.append(character_id)
    account_state[key] = contributors
    account_state[f"aemeath_s3_{mode}_crit_damage_bonus"] = min(max_count, len(contributors)) * crit_per
    account_state[f"aemeath_s3_{mode}_finale_deepen"] = 0.25 if len(contributors) >= max_count else 0.0


def _active_aemeath_mode(state: Any) -> str:
    config = getattr(state, "mechanics_config", {}) or {}
    mode = str(((config.get("aemeath") or {}).get("aemeath_resonance_mode") or "tune_rupture"))
    return mode if mode in {"tune_rupture", "fusion_burst"} else "tune_rupture"


def _reset_runtime_contributors(account_state: dict[str, Any]) -> None:
    for mode in ("tune", "fusion"):
        account_state[f"aemeath_s3_{mode}_contributors"] = []
        account_state[f"aemeath_s3_{mode}_crit_damage_bonus"] = 0.0
        account_state[f"aemeath_s3_{mode}_finale_deepen"] = 0.0


def _authoritative_trajectory_ratio(
    simulation_or_state: Any | None,
    account: dict[str, Any],
    aemeath: dict[str, Any],
    characters: dict[str, Any],
) -> float:
    if simulation_or_state is not None and hasattr(simulation_or_state, "state"):
        if _active_aemeath_mode(simulation_or_state.state) == "fusion_burst":
            fusion_state = simulation_or_state.state.character_mechanics_state.get("aemeath", {})
            cap = 60 if _sequence(characters.get("aemeath")) >= 6 else 30
            return min(1.0, max(0.0, float(fusion_state.get("fusion_trail_stacks", 0) or 0) / cap))
        cap = 60 if _sequence(characters.get("aemeath")) >= 6 else 30
        return min(1.0, max(0.0, float(getattr(simulation_or_state.state, "rupturous_trail_stacks", 0) or 0) / cap))
    # Helper fixtures predating CombatState keep their legacy value only when no
    # authoritative state object is available.
    return min(1.0, max(0.0, float(aemeath.get("s6_trajectories", account.get("aemeath_s6_trajectories", 0)) or 0) / 60.0))


def _sync_last_logs(simulation: Any, result: Any) -> None:
    if simulation.state.action_log:
        simulation.state.action_log[-1] = result.model_dump(mode="json")


def _remove_active_buff(state: Any, buff_id: str) -> None:
    state.active_buffs = [buff for buff in state.active_buffs if buff.buff_id != buff_id]
    state.team_buffs = list(state.active_buffs)


def _buff(
    buff_id: str,
    name: str,
    modifier_type: str,
    value: float,
    duration: float,
    *,
    target_scope: str = "party",
    target_character_id: str | None = None,
    stat_modifiers: dict[str, float] | None = None,
    damage_amp_modifiers: dict[str, float] | None = None,
    metadata: dict[str, Any] | None = None,
) -> BuffData:
    return BuffData(
        id=buff_id,
        name=name,
        modifier_type=modifier_type,
        value=float(value),
        duration=float(duration),
        target="party" if target_scope in {"party", "team"} else target_scope,
        target_scope=target_scope,
        target_character_id=target_character_id,
        stat_modifiers=stat_modifiers or {},
        damage_amp_modifiers=damage_amp_modifiers or {},
        metadata=metadata or {},
    )


def _account_runtime_enabled(simulation: Any) -> bool:
    return bool(getattr(simulation, "account_simulation_scope", None)) and any(
        getattr(character, "account_profile", False) for character in getattr(simulation, "characters", {}).values()
    )


def _account_state_enabled_from_parts(state: Any, characters: dict[str, Any]) -> bool:
    if not getattr(state, "character_mechanics_state", None):
        return False
    if "_account_constellation" not in state.character_mechanics_state:
        return False
    return any(getattr(character, "account_profile", False) for character in characters.values())


def _sequence_for(simulation: Any, character_id: str) -> int:
    character = getattr(simulation, "characters", {}).get(character_id)
    return _sequence(character)
