from __future__ import annotations

import math
from typing import Any

from simulator.buff_system import buffed_combat_stats, support_stat_context
from simulator.mechanic_events import aemeath_resonance_mode_from_config


OBSERVATION_VERSION = "slot_generic_mechanics_v1"
DEPRECATED_OBSERVATION_VERSION = "off_tune_tune_break_weapon_state_v1"
MAX_PARTY_SLOTS = 3

GLOBAL_SCHEMA = [
    "global.time_ratio",
    "global.time_remaining_ratio",
    "global.total_damage_scaled",
    "global.active_slot_index_scaled",
    "global.enemy_off_tune_ratio",
    "global.enemy_off_tune_current_scaled",
    "global.enemy_mistune_active",
    "global.enemy_tune_break_available",
    "global.enemy_tune_break_cooldown_ratio",
    "global.off_tune_accumulation_blocked_by_tune_break_cooldown",
    "global.current_off_tune_buildup_rate_scaled",
    "global.target_tune_shift_state_rupture_active",
    "global.target_tune_shift_state_rupture_remaining_ratio",
    "global.target_tune_shift_state_strain_active",
    "global.target_tune_shift_state_strain_remaining_ratio",
    "global.target_interfered_state_rupture_active",
    "global.target_interfered_state_rupture_remaining_ratio",
    "global.target_interfered_state_strain_active",
    "global.target_interfered_state_strain_remaining_ratio",
    "global.target_marker_0_active",
    "global.target_marker_0_remaining_ratio",
    "global.target_marker_0_value_scaled",
    "global.target_marker_1_active",
    "global.target_marker_1_remaining_ratio",
    "global.target_marker_1_value_scaled",
    "global.anomaly_0_stacks_ratio",
    "global.anomaly_0_duration_ratio",
    "global.anomaly_1_stacks_ratio",
    "global.anomaly_1_duration_ratio",
    "global.anomaly_2_stacks_ratio",
    "global.anomaly_2_duration_ratio",
    "global.anomaly_3_stacks_ratio",
    "global.anomaly_3_duration_ratio",
]

SLOT_SCHEMA = [
    "present",
    "is_active",
    "character_id_code_scaled",
    "role_code_scaled",
    "resonance_energy_ratio",
    "concerto_energy_ratio",
    "primary_resource_ratio",
    "secondary_resource_ratio",
    "tertiary_resource_ratio",
    "runtime_atk_percent_bonus_scaled",
    "runtime_def_percent_bonus_scaled",
    "runtime_hp_percent_bonus_scaled",
    "runtime_crit_rate_bonus_scaled",
    "runtime_crit_damage_bonus_scaled",
    "runtime_damage_taken_amp_outgoing_scaled",
    "mechanic_state_0_active",
    "mechanic_state_0_remaining_ratio",
    "mechanic_state_0_value_scaled",
    "mechanic_state_1_active",
    "mechanic_state_1_remaining_ratio",
    "mechanic_state_1_value_scaled",
    "mechanic_state_2_active",
    "mechanic_state_2_remaining_ratio",
    "mechanic_state_2_value_scaled",
    "mechanic_state_3_active",
    "mechanic_state_3_remaining_ratio",
    "mechanic_state_3_value_scaled",
    "echo_effect_0_active",
    "echo_effect_0_remaining_ratio",
    "echo_effect_0_value_scaled",
    "echo_effect_1_active",
    "echo_effect_1_remaining_ratio",
    "echo_effect_1_value_scaled",
    "weapon_effect_0_active",
    "weapon_effect_0_remaining_ratio",
    "weapon_effect_0_value_scaled",
    "weapon_effect_0_cooldown_ratio",
    "weapon_effect_1_active",
    "weapon_effect_1_remaining_ratio",
    "weapon_effect_1_value_scaled",
    "weapon_effect_1_cooldown_ratio",
    "tune_response_0_cooldown_ratio",
    "tune_response_0_available",
    "tune_response_1_cooldown_ratio",
    "tune_response_1_available",
]

ANOMALY_CHANNEL_MAPPING = {
    "global.anomaly_0": "aero_erosion",
    "global.anomaly_1": "spectro_frazzle",
    "global.anomaly_2": "electro_flare",
    "global.anomaly_3": "havoc_bane",
}


def build_observation_labels(max_party_slots: int = MAX_PARTY_SLOTS) -> list[str]:
    labels = list(GLOBAL_SCHEMA)
    for slot_index in range(max_party_slots):
        labels.extend(f"slot_{slot_index}.{name}" for name in SLOT_SCHEMA)
    return labels


def build_observation_values(simulation: Any, max_party_slots: int = MAX_PARTY_SLOTS) -> list[float]:
    values = _global_values(simulation, max_party_slots=max_party_slots)
    slot_ids = _slot_character_ids(simulation, max_party_slots=max_party_slots)
    for character_id in slot_ids:
        values.extend(_slot_values(simulation, character_id))
    labels = build_observation_labels(max_party_slots=max_party_slots)
    assert len(values) == len(labels), f"Observation value/label mismatch: {len(values)} != {len(labels)}"
    return [_finite_nonnegative(value) for value in values]


def build_observation_channel_mapping(simulation: Any, max_party_slots: int = MAX_PARTY_SLOTS) -> dict[str, str]:
    mapping = {
        "global.target_marker_0": "observation_marker",
        "global.target_marker_1": "interfered_marker",
        **ANOMALY_CHANNEL_MAPPING,
    }
    for slot_index, character_id in enumerate(_slot_character_ids(simulation, max_party_slots=max_party_slots)):
        if character_id == "aemeath":
            mapping.update(
                {
                    f"slot_{slot_index}.mechanic_state_0": "aemeath_resonance_mode",
                    f"slot_{slot_index}.mechanic_state_1": "aemeath_form_state",
                    f"slot_{slot_index}.mechanic_state_2": "aemeath_seraphic_duo",
                    f"slot_{slot_index}.mechanic_state_3": "aemeath_heavenfall_unbound",
                    f"slot_{slot_index}.echo_effect_0": "aemeath_trailblazing_star_5set",
                    f"slot_{slot_index}.tune_response_0": "aemeath_starburst",
                }
            )
        elif character_id == "mornye":
            mapping.update(
                {
                    f"slot_{slot_index}.mechanic_state_0": "mornye_syntony_field",
                    f"slot_{slot_index}.mechanic_state_1": "mornye_high_syntony_field",
                    f"slot_{slot_index}.mechanic_state_2": "mornye_relative_momentum",
                    f"slot_{slot_index}.mechanic_state_3": "mornye_rest_mass_energy_wide_field_observation",
                    f"slot_{slot_index}.echo_effect_0": "mornye_halo_of_starry_radiance_5set",
                    f"slot_{slot_index}.weapon_effect_0": "starfield_calibrator_concerto_restore",
                    f"slot_{slot_index}.weapon_effect_1": "starfield_calibrator_party_crit_damage",
                    f"slot_{slot_index}.tune_response_0": "mornye_particle_jet",
                }
            )
    return mapping


def build_observation_slot_mapping(simulation: Any, max_party_slots: int = MAX_PARTY_SLOTS) -> dict[str, str | None]:
    return {
        f"slot_{slot_index}": character_id
        for slot_index, character_id in enumerate(_slot_character_ids(simulation, max_party_slots=max_party_slots))
    }


def observation_metadata(env: Any) -> dict[str, Any]:
    return {
        "observation_version": OBSERVATION_VERSION,
        "deprecated_observation_version": DEPRECATED_OBSERVATION_VERSION,
        "observation_shape": list(env.observation_space.shape),
        "observation_labels": env.observation_labels(),
        "observation_channel_mapping": env.observation_channel_mapping(),
        "observation_slot_mapping": env.observation_slot_mapping(),
        "max_party_slots": MAX_PARTY_SLOTS,
    }


def global_mechanic_observation_labels() -> list[str]:
    return list(GLOBAL_SCHEMA)


def global_mechanic_observation_values(simulation: Any) -> list[float]:
    return _global_values(simulation, max_party_slots=MAX_PARTY_SLOTS)


def _global_values(simulation: Any, *, max_party_slots: int) -> list[float]:
    state = simulation.state
    duration = float(getattr(simulation, "combat_duration", getattr(state, "combat_duration", 120.0)) or 120.0)
    target_shift = str(getattr(state, "target_tune_shift_state", "") or "")
    target_interfered = str(getattr(state, "target_interfered_state", "") or "")
    marker_0_remaining = _observation_marker_remaining(state)
    marker_1_remaining = float(getattr(state, "interfered_marker_remaining", 0.0) or 0.0)
    active_slot = _active_slot_index(simulation, max_party_slots=max_party_slots)

    values = [
        _ratio(float(getattr(state, "combat_time", 0.0) or 0.0), duration),
        _ratio(max(0.0, duration - float(getattr(state, "combat_time", 0.0) or 0.0)), duration),
        _ratio(float(getattr(state, "total_damage", 0.0) or 0.0), 1_000_000.0),
        _ratio(float(active_slot), float(max(max_party_slots - 1, 1))) if active_slot >= 0 else 0.0,
        _ratio(float(getattr(state, "enemy_off_tune_current", 0.0) or 0.0), float(getattr(state, "enemy_off_tune_max", 0.0) or 0.0)),
        _ratio(float(getattr(state, "enemy_off_tune_current", 0.0) or 0.0), 3920.0),
        _bool(getattr(state, "enemy_mistune_active", False)),
        _bool(getattr(state, "enemy_tune_break_available", False)),
        _ratio(
            float(getattr(state, "enemy_tune_break_cooldown_remaining", 0.0) or 0.0),
            float(getattr(state, "enemy_tune_break_cooldown_seconds", 0.0) or 0.0),
        ),
        _bool(float(getattr(state, "enemy_tune_break_cooldown_remaining", 0.0) or 0.0) > 0.0),
        _ratio(_current_off_tune_buildup_rate(simulation), 1.7),
        _bool(target_shift == "tune_rupture_shifting"),
        _ratio(float(getattr(state, "target_tune_shift_remaining", 0.0) or 0.0), 8.0)
        if target_shift == "tune_rupture_shifting"
        else 0.0,
        _bool(target_shift == "tune_strain_shifting"),
        _ratio(float(getattr(state, "target_tune_shift_remaining", 0.0) or 0.0), 30.0)
        if target_shift == "tune_strain_shifting"
        else 0.0,
        _bool(target_interfered == "tune_rupture_interfered"),
        _ratio(float(getattr(state, "target_interfered_remaining", 0.0) or 0.0), 8.0)
        if target_interfered == "tune_rupture_interfered"
        else 0.0,
        _bool(target_interfered == "tune_strain_interfered"),
        _ratio(float(getattr(state, "target_interfered_remaining", 0.0) or 0.0), 30.0)
        if target_interfered == "tune_strain_interfered"
        else 0.0,
        _bool(marker_0_remaining > 0.0),
        _ratio(marker_0_remaining, 30.0),
        _bool(marker_0_remaining > 0.0),
        _bool(marker_1_remaining > 0.0 and float(getattr(state, "interfered_marker_damage_taken_amp", 0.0) or 0.0) > 0.0),
        _ratio(marker_1_remaining, 20.0 if marker_1_remaining > 8.0 else 8.0),
        _ratio(float(getattr(state, "interfered_marker_damage_taken_amp", 0.0) or 0.0), 0.40),
    ]
    for anomaly_type in ("aero_erosion", "spectro_frazzle", "electro_flare", "havoc_bane"):
        anomaly = getattr(state, "active_anomalies", {}).get(anomaly_type)
        values.append(_ratio(float(getattr(anomaly, "stacks", 0.0) or 0.0), 99.0) if anomaly else 0.0)
        values.append(_ratio(float(getattr(anomaly, "remaining_duration", 0.0) or 0.0), 6.0) if anomaly else 0.0)
    return values


def _slot_values(simulation: Any, character_id: str | None) -> list[float]:
    if not character_id or character_id not in simulation.characters:
        return [0.0 for _ in SLOT_SCHEMA]

    state = simulation.state
    character = simulation.characters[character_id]
    character_state = state.character_mechanics_state.get(character_id, {})
    runtime_stats = buffed_combat_stats(character, state, simulation.buffs)
    values = [
        1.0,
        _bool(getattr(state, "active_character_id", None) == character_id),
        _character_code(character_id),
        _role_code(character),
        _ratio(float(state.resonance_energy.get(character_id, 0.0) or 0.0), float(character.resonance_energy_max or 0.0)),
        _ratio(float(state.concerto_energy.get(character_id, 0.0) or 0.0), 100.0),
        *_resource_values(character_id, character_state),
        _ratio(float(runtime_stats.get("runtime_atk_percent_bonus", 0.0) or 0.0), 0.50),
        _ratio(float(runtime_stats.get("runtime_def_percent_bonus", 0.0) or 0.0), 0.50),
        _ratio(float(runtime_stats.get("runtime_hp_percent_bonus", 0.0) or 0.0), 0.50),
        _ratio(
            max(
                0.0,
                float(runtime_stats.get("crit_rate_after_buffs", 0.0) or 0.0)
                - float(runtime_stats.get("crit_rate_before_buffs", 0.0) or 0.0),
            ),
            0.20,
        ),
        _ratio(float(runtime_stats.get("runtime_crit_damage_bonus", 0.0) or 0.0), 0.40),
        0.0,
    ]
    values.extend(_mechanic_channel_values(simulation, character_id, character_state, runtime_stats))
    values.extend(_echo_channel_values(simulation, character_id))
    values.extend(_weapon_channel_values(simulation, character_id))
    values.extend(_tune_response_channel_values(simulation, character_id))
    assert len(values) == len(SLOT_SCHEMA), f"Slot value mismatch for {character_id}: {len(values)} != {len(SLOT_SCHEMA)}"
    return values


def _resource_values(character_id: str, character_state: dict[str, Any]) -> list[float]:
    if character_id == "aemeath":
        return [
            _ratio(float(character_state.get("synchronization_rate", 0.0) or 0.0), 200.0),
            _ratio(float(character_state.get("resonance_rate", 0.0) or 0.0), 4.0),
            _bool(character_state.get("form") == "mech"),
        ]
    if character_id == "mornye":
        return [
            _ratio(float(character_state.get("rest_mass_energy", 0.0) or 0.0), float(character_state.get("rest_mass_energy_cap", 100.0) or 100.0)),
            _ratio(float(character_state.get("relative_momentum", 0.0) or 0.0), float(character_state.get("relative_momentum_cap", 100.0) or 100.0)),
            _bool(character_state.get("mode") == "wide_field_observation"),
        ]
    return [0.0, 0.0, 0.0]


def _mechanic_channel_values(
    simulation: Any,
    character_id: str,
    character_state: dict[str, Any],
    runtime_stats: dict[str, Any],
) -> list[float]:
    if character_id == "aemeath":
        mode = aemeath_resonance_mode_from_config(getattr(simulation.state, "mechanics_config", {}) or {})
        mode_value = 1.0 if mode == "tune_rupture" else 0.5 if mode == "fusion_burst" else 0.0
        seraphic_remaining = float(character_state.get("seraphic_duo_remaining", 0.0) or 0.0)
        heavenfall_remaining = float(character_state.get("heavenfall_unbound_remaining", 0.0) or 0.0)
        return [
            _bool(mode != "unresolved"),
            0.0,
            mode_value,
            1.0,
            0.0,
            _bool(character_state.get("form") == "mech"),
            _bool(seraphic_remaining > 0.0),
            _ratio(seraphic_remaining, 5.0),
            _ratio(float(character_state.get("synchronization_rate", 0.0) or 0.0), 200.0),
            _bool(character_state.get("heavenfall_unbound", False)),
            _ratio(heavenfall_remaining, 60.0),
            _ratio(float(character_state.get("resonance_rate", 0.0) or 0.0), 4.0),
        ]
    if character_id == "mornye":
        syntony_remaining = float(character_state.get("syntony_field_remaining", 0.0) or 0.0)
        high_remaining = float(character_state.get("high_syntony_field_remaining", 0.0) or 0.0)
        relative_momentum = float(character_state.get("relative_momentum", 0.0) or 0.0)
        rest_mass = float(character_state.get("rest_mass_energy", 0.0) or 0.0)
        rest_mass_ratio = _ratio(rest_mass, float(character_state.get("rest_mass_energy_cap", 100.0) or 100.0))
        return [
            _bool(syntony_remaining > 0.0),
            _ratio(syntony_remaining, 25.0),
            _ratio(float(runtime_stats.get("syntony_field_off_tune_bonus_value", 0.0) or 0.0), 0.50),
            _bool(high_remaining > 0.0),
            _ratio(high_remaining, 25.0),
            _ratio(float(runtime_stats.get("high_syntony_field_def_percent_bonus", 0.0) or 0.0), 0.20),
            _bool(relative_momentum > 0.0),
            _ratio(relative_momentum, float(character_state.get("relative_momentum_cap", 100.0) or 100.0)),
            _ratio(relative_momentum, float(character_state.get("relative_momentum_cap", 100.0) or 100.0)),
            _bool(rest_mass > 0.0 or character_state.get("mode") == "wide_field_observation"),
            _ratio(float(character_state.get("wide_field_observation_remaining", 0.0) or 0.0), 30.0),
            rest_mass_ratio if rest_mass_ratio > 0.0 else _bool(character_state.get("mode") == "wide_field_observation"),
        ]
    return [0.0 for _ in range(12)]


def _echo_channel_values(simulation: Any, character_id: str) -> list[float]:
    if character_id == "aemeath":
        active = _active_buff(simulation.state, "aemeath_trailblazing_star_5set")
        return [
            _bool(active is not None),
            _ratio(_remaining(active), 8.0),
            _ratio(_trailblazing_value(active, simulation.buffs), 0.20),
            0.0,
            0.0,
            0.0,
        ]
    if character_id == "mornye":
        active = _active_buff(simulation.state, "mornye_halo_of_starry_radiance_5set")
        return [
            _bool(active is not None),
            _ratio(_remaining(active), 4.0),
            _ratio(_dynamic_value(active), 0.25),
            0.0,
            0.0,
            0.0,
        ]
    return [0.0 for _ in range(6)]


def _weapon_channel_values(simulation: Any, character_id: str) -> list[float]:
    if character_id != "mornye":
        return [0.0 for _ in range(8)]
    weapon = getattr(simulation.characters.get(character_id), "weapon", {}) or {}
    weapon_id = weapon.get("weapon_id")
    starfield_equipped = weapon_id == "starfield_calibrator"
    restore_amount = _weapon_rank_value(simulation, weapon_id, int(weapon.get("rank", 1) or 1), "concerto_restore_on_resonance_skill")
    active_starfield = _active_buff(simulation.state, "starfield_calibrator_party_crit_damage")
    return [
        _bool(starfield_equipped),
        0.0,
        _ratio(restore_amount, 16.0),
        _ratio(_starfield_concerto_restore_cooldown(simulation.state), 20.0),
        _bool(active_starfield is not None),
        _ratio(_remaining(active_starfield), 4.0),
        _ratio(_dynamic_value(active_starfield), 0.40),
        0.0,
    ]


def _tune_response_channel_values(simulation: Any, character_id: str) -> list[float]:
    state = simulation.state
    if character_id == "aemeath":
        cooldown = float(getattr(state, "aemeath_starburst_response_cooldown_remaining", 0.0) or 0.0)
        return [_ratio(cooldown, 8.0), _bool(cooldown <= 0.0), 0.0, 0.0]
    if character_id == "mornye":
        cooldown = float(getattr(state, "mornye_particle_jet_response_cooldown_remaining", 0.0) or 0.0)
        return [_ratio(cooldown, 8.0), _bool(cooldown <= 0.0), 0.0, 0.0]
    return [0.0, 0.0, 0.0, 0.0]


def _slot_character_ids(simulation: Any, *, max_party_slots: int) -> list[str | None]:
    selected = list(getattr(simulation, "selected_party_character_ids", []) or getattr(simulation, "selected_character_ids", []) or [])
    return (selected[:max_party_slots] + [None] * max_party_slots)[:max_party_slots]


def _active_slot_index(simulation: Any, *, max_party_slots: int) -> int:
    active_id = getattr(simulation.state, "active_character_id", None)
    for index, character_id in enumerate(_slot_character_ids(simulation, max_party_slots=max_party_slots)):
        if character_id == active_id:
            return index
    return -1


def _observation_marker_remaining(state: Any) -> float:
    return float(
        (getattr(state, "character_mechanics_state", {}) or {})
        .get("mornye", {})
        .get("observation_marker_remaining", 0.0)
        or 0.0
    )


def _active_buff(state: Any, buff_id: str) -> Any | None:
    for active in getattr(state, "active_buffs", []) or []:
        if active.buff_id == buff_id and active.remaining_duration > 0.0:
            return active
    return None


def _remaining(active_buff: Any | None) -> float:
    return float(getattr(active_buff, "remaining_duration", 0.0) or 0.0) if active_buff is not None else 0.0


def _dynamic_value(active_buff: Any | None) -> float:
    if active_buff is None:
        return 0.0
    metadata = getattr(active_buff, "metadata", {}) or {}
    return float(metadata.get("dynamic_value", 0.0) or 0.0)


def _trailblazing_value(active_buff: Any | None, buffs: dict[str, Any]) -> float:
    if active_buff is None:
        return 0.0
    buff = buffs.get(active_buff.buff_id)
    if buff is None:
        return 0.0
    element_bonus = max((float(value or 0.0) for value in getattr(buff, "damage_bonus_by_element", {}).values()), default=0.0)
    crit_bonus = float(getattr(buff, "stat_modifiers", {}).get("crit_rate", 0.0) or 0.0)
    return max(element_bonus, crit_bonus)


def _weapon_rank_value(simulation: Any, weapon_id: str | None, rank: int, key: str) -> float:
    weapon_def = (getattr(simulation, "weapon_definitions", {}) or {}).get(weapon_id or "")
    rank_values = (weapon_def or {}).get("rank_values", {})
    return float((rank_values.get(str(rank)) or {}).get(key, 0.0) or 0.0)


def _starfield_concerto_restore_cooldown(state: Any) -> float:
    return max(
        (
            float(remaining or 0.0)
            for key, remaining in (getattr(state, "weapon_effect_cooldowns", {}) or {}).items()
            if ":starfield_calibrator:resonance_skill_concerto_restore" in str(key)
        ),
        default=0.0,
    )


def _current_off_tune_buildup_rate(simulation: Any) -> float:
    mornye = simulation.characters.get("mornye")
    if mornye is None:
        return 0.0
    return float(support_stat_context(mornye, simulation.state, simulation.buffs).get("current_off_tune_buildup_rate", 0.0) or 0.0)


def _role_code(character: Any) -> float:
    tags = {str(tag).lower() for tag in getattr(character, "role_tags", []) or []}
    if "main_dps" in tags:
        return 0.75
    if "sub_dps" in tags or "dummy_sub_dps" in tags:
        return 0.50
    if "support" in tags or "party_buffer" in tags:
        return 0.25
    return 0.0


def _character_code(character_id: str) -> float:
    checksum = sum((index + 1) * ord(char) for index, char in enumerate(character_id))
    return _ratio(float(checksum % 1000), 999.0)


def _ratio(value: float, denominator: float) -> float:
    if denominator <= 0.0:
        return 0.0
    return min(max(float(value) / float(denominator), 0.0), 1.0)


def _bool(value: Any) -> float:
    return 1.0 if bool(value) else 0.0


def _finite_nonnegative(value: float) -> float:
    value = float(value or 0.0)
    if not math.isfinite(value):
        return 0.0
    return max(0.0, value)
