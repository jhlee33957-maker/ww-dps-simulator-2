from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import json
import pandas as pd
import plotly.express as px
import streamlit as st

from env.observation_features import (
    OBSERVATION_VERSION,
    build_observation_channel_mapping,
    build_observation_labels,
    build_observation_slot_mapping,
    build_observation_values,
)
from simulator.models import CharacterData
from simulator.build_profiles import (
    effective_build_stats_summary,
    get_available_build_profiles,
    load_build_profiles,
    resolve_character_build_stats,
    resolve_party_build_profiles,
    validate_effective_build_profiles,
)
from simulator.roster import is_dummy_character, parse_character_ids, read_party_presets
from simulator.simulation import Simulation
from simulator.transition_config import (
    build_aemeath_resonance_mode_override,
    build_effective_transition_config,
    build_mornye_expectation_error_mode_override,
    build_mornye_heal_event_mode_override,
    build_transition_mode_overrides,
    load_transition_config,
    mechanics_mode_summary,
    transition_mode_summary,
)
from rl.evaluation_report import build_generated_damage_summary
from ui.mechanics_reference import render_mechanics_reference


DATA_DIR = Path(__file__).parent / "data"
DEFAULT_PPO_MODEL_PATH = Path(__file__).parent / "models" / "maskable_ppo_wuwa.zip"


def simulation_observation_shape(simulation: Simulation) -> list[int]:
    return [len(build_observation_labels())]


def merge_override_blocks(*blocks: dict[str, Any] | None) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for block in blocks:
        if not block:
            continue
        _merge_nested_dict(merged, block)
    return merged


def _merge_nested_dict(target: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _merge_nested_dict(target[key], value)
        else:
            target[key] = value
    return target

def enemy_settings() -> dict[str, float | int]:
    st.sidebar.header("Damage Formula Settings")
    settings = {
        "enemy_level": st.sidebar.number_input("Enemy level", min_value=1, max_value=120, value=90, step=1),
        "enemy_res": st.sidebar.number_input("Enemy RES", min_value=-1.0, max_value=2.0, value=0.1, step=0.01),
        "res_pen": st.sidebar.number_input("RES Penetration", min_value=0.0, max_value=1.0, value=0.0, step=0.01),
        "def_reduction": st.sidebar.number_input("DEF Reduction", min_value=0.0, max_value=1.0, value=0.0, step=0.01),
        "dmg_taken": st.sidebar.number_input("DMG Taken", min_value=-0.9, max_value=3.0, value=0.0, step=0.01),
        "tune_dmg_bonus": st.sidebar.number_input("Tune DMG Bonus", min_value=0.0, max_value=3.0, value=0.0, step=0.01),
    }
    with st.sidebar.expander("Formula notes"):
        st.write("Normal damage uses attack, damage bonus, expected crit, boost, RES, DEF, DMG taken, and final damage multipliers.")
        st.write("Tune Break damage uses a fixed base, tune multiplier, tune boost, RES, DEF, and tune damage bonus.")
        st.write("Attribute anomalies are stored on the enemy. Aero, Spectro, and Electro tick while active; Havoc Bane adds defense reduction.")
    return settings


def load_available_characters() -> dict[str, CharacterData]:
    with (DATA_DIR / "characters.json").open("r", encoding="utf-8-sig") as file:
        return {
            item["id"]: CharacterData.model_validate(item)
            for item in json.load(file)
        }


def character_label(character: CharacterData) -> str:
    suffix = " (Dummy Sample)" if is_dummy_character(character) else ""
    return f"{character.name}{suffix}"


def build_profile_controls(
    selected_character_ids: list[str],
    party_preset_config: dict[str, Any] | None,
) -> dict[str, str]:
    characters = load_available_characters()
    build_profiles = load_build_profiles(DATA_DIR)
    ui_overrides: dict[str, str] = {}
    with st.sidebar.expander("Build Profiles"):
        for character_id in selected_character_ids:
            available = get_available_build_profiles(character_id, build_profiles)
            if not available:
                continue
            options = ["Use Party Preset / Default", *available.keys()]
            choice = st.selectbox(
                f"{characters[character_id].name} Build",
                options=options,
                index=0,
                key=f"build-profile-{character_id}",
                format_func=lambda profile_id: (
                    profile_id
                    if profile_id == "Use Party Preset / Default"
                    else f"{profile_id} - {available[profile_id].get('display_name', profile_id)}"
                ),
            )
            if choice != "Use Party Preset / Default":
                ui_overrides[character_id] = choice

        effective_profiles = resolve_party_build_profiles(
            party_preset_config,
            ui_overrides=ui_overrides,
            selected_character_ids=selected_character_ids,
            build_profiles=build_profiles,
        )
        effective_characters = {
            character_id: resolve_character_build_stats(
                characters[character_id],
                effective_profiles.get(character_id),
                build_profiles,
            )
            for character_id in selected_character_ids
        }
        st.write("Effective profiles")
        st.write(effective_profiles)
        with (DATA_DIR / "actions.json").open("r", encoding="utf-8-sig") as file:
            from simulator.models import ActionData
            from simulator.build_profiles import build_action_scaling_summary

            all_actions = [ActionData.model_validate(item) for item in json.load(file)]
        scaling_summary = build_action_scaling_summary(all_actions, selected_character_ids)
        stats_summary = effective_build_stats_summary(effective_characters, scaling_summary)
        validation = validate_effective_build_profiles(stats_summary)
        for error in validation.get("errors", []):
            st.error(f"This real/manual profile is incomplete. Fill required stats before training/evaluation. {error}")
        for warning in validation.get("warnings", []):
            st.warning(str(warning))
        for character_id, summary in stats_summary.items():
            with st.expander(f"{character_id} Effective Stat Components"):
                st.write(
                    {
                        "Build Profile ID": summary.get("build_profile_id"),
                        "implementation_status": summary.get("implementation_status"),
                        "profile_completeness_status": summary.get("profile_completeness_status"),
                        "missing_required_fields": summary.get("missing_required_fields"),
                        "scaling_stat_distribution": summary.get("scaling_stat_distribution"),
                        "unresolved_scaling_actions": summary.get("unresolved_scaling_actions"),
                        "crit_rate": summary.get("crit_rate"),
                        "crit_damage": summary.get("crit_damage"),
                        "energy_regen": summary.get("energy_regen"),
                        "weapon": summary.get("weapon"),
                        "support_stats": summary.get("support_stats"),
                        "damage_bonuses": summary.get("damage_bonuses"),
                    }
                )
                for stat in ("atk", "def", "hp"):
                    st.write(
                        {
                            f"{stat.upper()} character_base": summary.get(f"character_base_{stat}"),
                            f"{stat.upper()} weapon_base": summary.get(f"weapon_base_{stat}"),
                            f"{stat.upper()} base_total": summary.get(f"base_{stat}_total"),
                            f"{stat.upper()} percent": summary.get(f"static_{stat}_percent"),
                            f"{stat.upper()} flat": summary.get(f"static_flat_{stat}"),
                            f"{stat.upper()} static_value": summary.get(f"static_{stat}"),
                            f"{stat.upper()} runtime_percent_bonus": summary.get(f"runtime_{stat}_percent_bonus"),
                            f"{stat.upper()} runtime_flat_bonus": summary.get(f"runtime_{stat}_flat_bonus"),
                            f"{stat.upper()} effective_value": summary.get(f"effective_{stat}"),
                            f"{stat.upper()} final_reference": summary.get(f"final_{stat}_reference"),
                            f"{stat.upper()} reference_delta": summary.get(f"{stat}_reference_delta"),
                            f"{stat.upper()} reference_delta_percent": summary.get(f"{stat}_reference_delta_percent"),
                        }
                    )
                if character_id == "aemeath":
                    st.write({"Aemeath ATK effective stat": summary.get("effective_atk")})
                    st.write(
                        {
                            "Resonance Liberation DMG Bonus": (
                                (summary.get("damage_bonuses") or {}).get("by_category") or {}
                            ).get("resonance_liberation", 0.0)
                        }
                    )
                if character_id == "mornye":
                    er = float(summary.get("energy_regen") or 1.0)
                    excess = max(0.0, (er - 1.0) * 100.0)
                    if summary.get("actions_requiring_def_stats") and summary.get("effective_def", 0.0) <= 0:
                        st.warning("Mornye has DEF-scaling actions but the selected profile lacks usable DEF fields.")
                    st.write(
                        {
                            "Mornye DEF effective stat": summary.get("effective_def"),
                            "Energy Regen": er,
                            "Base Off-Tune Buildup Rate": (summary.get("support_stats") or {}).get("off_tune_buildup_rate", 1.0),
                            "ER Excess Percent": excess,
                            "Interfered Amp Potential": min(excess * 0.0025, 0.40),
                            "Liberation Crit Rate Bonus": min(excess * 0.005, 0.80),
                            "Liberation Crit Damage Bonus": min(excess * 0.01, 1.60),
                        }
                    )
        if effective_profiles.get("aemeath") == "liberation_focus_test":
            st.warning(
                "Aemeath liberation_focus_test is a configurable test assumption, "
                "not verified final real-game build data."
            )
            profile = (build_profiles.get("profiles") or {}).get("aemeath", {}).get("liberation_focus_test", {})
            liberation_bonus = float(((profile.get("damage_bonuses") or {}).get("by_category") or {}).get("resonance_liberation", 0.0))
            st.write({"Resonance Liberation DMG Bonus": liberation_bonus})
            with (DATA_DIR / "actions.json").open("r", encoding="utf-8-sig") as file:
                actions = [item for item in json.load(file) if item.get("character_id") == "aemeath"]
            missing = [
                item["id"]
                for item in actions
                if item.get("raw_damage_type") == "共鸣解放伤害"
                and item.get("damage_bonus_category") != "resonance_liberation"
            ]
            if missing:
                st.warning(
                    "Some Aemeath source Resonance Liberation damage rows are missing "
                    f"damage_bonus_category=resonance_liberation: {missing}"
                )
    return ui_overrides


def party_selection() -> tuple[list[str], dict[str, Any] | None, str | None]:
    characters = load_available_characters()
    presets = read_party_presets(DATA_DIR)
    if presets:
        preset_ids = list(presets)
        selected_preset_id = st.sidebar.selectbox(
            "Party Preset",
            options=preset_ids,
            index=0,
            format_func=lambda preset_id: presets[preset_id].get("display_name", preset_id),
        )
        selected = list(presets[selected_preset_id]["members"])
        if any(is_dummy_character(characters[character_id]) for character_id in selected):
            st.sidebar.warning("Dummy sample characters are test-only and are not intended for real DPS analysis.")
        return parse_character_ids(selected, list(characters)), presets[selected_preset_id], selected_preset_id

    default_ids = parse_character_ids(None, list(characters))
    options = list(characters)
    selected = st.sidebar.multiselect(
        "Party Selection",
        options=options,
        default=default_ids,
        format_func=lambda character_id: character_label(characters[character_id]),
    )
    if not selected:
        selected = default_ids
        st.sidebar.info("Using default party selection.")
    if len(selected) > 3:
        selected = selected[:3]
        st.sidebar.warning("A party can currently contain 1 to 3 characters. Using the first three selected characters.")
    if any(is_dummy_character(characters[character_id]) for character_id in selected):
        st.sidebar.warning("Dummy sample characters use intentionally low placeholder coefficients and are not intended for real DPS analysis.")
    return parse_character_ids(selected, options), None, None


def apply_enemy_settings(sim: Simulation, settings: dict[str, float | int]) -> None:
    sim.set_enemy_context(
        enemy_level=int(settings["enemy_level"]),
        enemy_res=float(settings["enemy_res"]),
        res_pen=float(settings["res_pen"]),
        def_reduction=float(settings["def_reduction"]),
        dmg_taken=float(settings["dmg_taken"]),
        tune_dmg_bonus=float(settings["tune_dmg_bonus"]),
    )


def run_repeating_sequence(
    sequence: list[str],
    settings: dict[str, float | int],
    selected_character_ids: list[str],
    transition_config: dict[str, Any] | None = None,
    party_id: str | None = None,
    build_profile_overrides: dict[str, str] | None = None,
) -> Simulation:
    sim = Simulation.from_json(
        DATA_DIR,
        selected_character_ids=None if party_id else selected_character_ids,
        party=party_id,
        transition_config=transition_config,
        build_profile_overrides=build_profile_overrides,
    )
    apply_enemy_settings(sim, settings)
    index = 0

    while sim.state.combat_time < sim.combat_duration:
        action_id = sequence[index % len(sequence)]
        if not sim.execute_action(action_id):
            sim.execute_action("short_wait")
        index += 1

    return sim


def evaluate_ppo_model(
    model_path: Path,
    settings: dict[str, float | int],
    selected_character_ids: list[str],
    transition_config: dict[str, Any] | None = None,
    party_id: str | None = None,
    build_profile_overrides: dict[str, str] | None = None,
) -> tuple[Any, list[str], Simulation]:
    try:
        from sb3_contrib import MaskablePPO
        from env.wuwa_env import WuwaDpsEnv
    except ModuleNotFoundError as exc:
        raise RuntimeError("Missing RL dependency. Run: pip install -r requirements.txt") from exc

    model = MaskablePPO.load(model_path)
    env = WuwaDpsEnv(
        DATA_DIR,
        selected_character_ids=None if party_id else selected_character_ids,
        party=party_id,
        transition_config=transition_config,
        build_profile_overrides=build_profile_overrides,
    )
    observation, _ = env.reset()
    apply_enemy_settings(env.simulation, settings)
    action_sequence: list[str] = []

    while env.simulation.state.combat_time < env.simulation.combat_duration:
        action, _ = model.predict(observation, deterministic=True, action_masks=env.action_masks())
        observation, _reward, terminated, truncated, info = env.step(int(action))
        action_sequence.append(str(info["action_id"]))
        if terminated or truncated:
            break

    return env.simulation.summary(), action_sequence, env.simulation


def render_simulation(summary: Any, action_sequence: list[str] | None = None, simulation: Simulation | None = None) -> None:
    metric_cols = st.columns(4)
    metric_cols[0].metric("Total damage", f"{summary.total_damage:,.0f}")
    metric_cols[1].metric("DPS", f"{summary.dps:,.0f}")
    metric_cols[2].metric("Final combat time", f"{summary.final_time:.2f}s")
    metric_cols[3].metric("Active character", summary.active_character)
    if simulation is not None:
        party_kind = "Solo party" if len(simulation.selected_party_character_ids) == 1 else "Multi-character party"
        st.caption(
            f"Selected party: {', '.join(simulation.selected_party_character_ids)} | "
            f"Initial active: {simulation.initial_active_character} | "
            f"Policy actions: {len(simulation.policy_actions)} | {party_kind}"
        )
        with st.expander("Policy Action IDs"):
            st.write(simulation.get_policy_action_ids())
        with st.expander("Registered Character Mechanics"):
            st.write({character_id: mechanic.__class__.__name__ for character_id, mechanic in simulation.character_mechanics.items()})
        with st.expander("RL Observation Diagnostics"):
            observation_labels = build_observation_labels()
            observation_values = build_observation_values(simulation)
            channel_mapping = build_observation_channel_mapping(simulation)
            slot_mapping = build_observation_slot_mapping(simulation)
            mornye_runtime_state = simulation.state.character_mechanics_state.get("mornye", {})
            st.write(
                {
                    "observation_shape": simulation_observation_shape(simulation),
                    "observation_version": OBSERVATION_VERSION,
                    "max_party_slots": len(slot_mapping),
                    "slot_mapping": slot_mapping,
                    "channel_mapping": channel_mapping,
                    "enemy_off_tune": f"{summary.enemy_off_tune_current:.1f}/{summary.enemy_off_tune_max:.0f}",
                    "enemy_mistune_active": summary.enemy_mistune_active,
                    "enemy_tune_break_available": summary.enemy_tune_break_available,
                    "enemy_tune_break_cooldown_remaining": summary.enemy_tune_break_cooldown_remaining,
                    "observation_marker_remaining": summary.observation_marker_remaining,
                    "interfered_marker_remaining": summary.interfered_marker_remaining,
                    "interfered_marker_damage_taken_amp": summary.interfered_marker_damage_taken_amp,
                    "syntony_field_remaining": float(mornye_runtime_state.get("syntony_field_remaining", 0.0) or 0.0),
                    "high_syntony_field_remaining": summary.high_syntony_field_remaining,
                    "halo_5set_active": summary.halo_of_starry_radiance_5set_active,
                    "starfield_party_crit_damage_bonus": summary.starfield_calibrator_party_crit_damage_bonus,
                    "starfield_concerto_cooldown_remaining": max(
                        (
                            float(remaining or 0.0)
                            for key, remaining in simulation.state.weapon_effect_cooldowns.items()
                            if ":starfield_calibrator:resonance_skill_concerto_restore" in str(key)
                        ),
                        default=0.0,
                    ),
                    "aemeath_starburst_cooldown_remaining": summary.aemeath_starburst_response_cooldown_remaining,
                    "mornye_particle_jet_cooldown_remaining": summary.mornye_particle_jet_response_cooldown_remaining,
                }
            )
            st.dataframe(
                pd.DataFrame(
                    {"label": observation_labels, "value": observation_values}
                ),
                use_container_width=True,
                hide_index=True,
            )
        with st.expander("Effective Build Profiles"):
            st.write(simulation.active_build_profiles)
            st.write(simulation.effective_build_stats_summary)
            validation = simulation.validate_build_profiles()
            if validation.get("errors"):
                st.error(validation["errors"])
            if validation.get("warnings"):
                st.warning(validation["warnings"])
        with st.expander("Active Team Buffs"):
            st.write([buff.model_dump() for buff in simulation.state.active_buffs])
        with st.expander("Weapon Effects"):
            weapon_rows = []
            for character_id, weapon in (summary.active_weapons or {}).items():
                weapon_rows.append(
                    {
                        "character_id": character_id,
                        "weapon_id": weapon.get("weapon_id"),
                        "weapon_type": weapon.get("weapon_type"),
                        "rank": weapon.get("rank", 1),
                        "static_stats_already_in_profile": weapon.get("static_stats_already_in_profile"),
                        "base_atk_and_crit_already_in_profile": weapon.get("base_atk_and_crit_already_in_profile"),
                        "def_percent_passive_already_in_profile": weapon.get("def_percent_passive_already_in_profile"),
                    }
                )
            if weapon_rows:
                st.dataframe(pd.DataFrame(weapon_rows), use_container_width=True, hide_index=True)
            weapon_cols = st.columns(4)
            weapon_cols[0].metric("Weapon effects", "Enabled" if summary.weapon_effects_enabled else "Disabled")
            weapon_cols[1].metric(
                "Starfield Concerto triggers",
                summary.starfield_calibrator_concerto_restore_trigger_count,
            )
            weapon_cols[2].metric(
                "Starfield Concerto restored",
                f"{summary.starfield_calibrator_concerto_restored_total:.1f}",
            )
            weapon_cols[3].metric(
                "Starfield Crit DMG uptime",
                f"{summary.starfield_calibrator_party_crit_damage_uptime_seconds:.2f}s",
            )
            st.write(
                {
                    "Trigger counts": summary.weapon_effect_trigger_counts,
                    "Cooldown blocked counts": summary.weapon_effect_cooldown_blocked_counts,
                    "Weapon effect source status": summary.weapon_effect_source_status,
                    "Starfield party Crit DMG trigger count": (
                        summary.starfield_calibrator_party_crit_damage_trigger_count
                    ),
                    "Starfield active Crit DMG bonus": summary.starfield_calibrator_party_crit_damage_bonus,
                    "Everbright Polestar equipped": summary.everbright_polestar_equipped,
                    "Everbright Polestar rank": summary.everbright_polestar_rank,
                    "Everbright all attribute DMG bonus": summary.everbright_polestar_all_attribute_damage_bonus,
                    "Everbright penetration trigger count": (
                        summary.everbright_polestar_liberation_penetration_trigger_count
                    ),
                    "Everbright penetration uptime": (
                        f"{summary.everbright_polestar_liberation_penetration_uptime_seconds:.2f}s"
                    ),
                    "Everbright active DEF Ignore": summary.everbright_polestar_def_ignore_bonus,
                    "Everbright active Fusion RES Ignore": summary.everbright_polestar_fusion_res_ignore_bonus,
                    "Everbright buff windows": summary.everbright_polestar_buff_windows,
                    "Everbright trigger event tags": ["tune_rupture_shifting", "fusion_burst"],
                    "Everbright base/crit stats applied at runtime": False,
                    "Discord support": summary.discord_concerto_restore_support_status,
                    "Static weapon stats applied at runtime": False,
                    "Starfield DEF% passive applied at runtime": False,
                }
            )
        if "mornye" in simulation.selected_party_character_ids:
            mornye_state = simulation.state.character_states.get("mornye", {})
            mornye_mechanic = simulation.character_mechanics.get("mornye")
            display_state = mornye_mechanic.get_display_state(mornye_state) if mornye_mechanic else dict(mornye_state)
            display_state["Concerto Energy"] = (
                f"{float(mornye_state.get('concerto_energy', 0.0)):.1f}/"
                f"{float(mornye_state.get('concerto_energy_cap', 100.0)):.0f}"
            )
            display_state["Outro Buff Remaining"] = next(
                (
                    f"{buff.remaining_duration:.1f}s"
                    for buff in simulation.state.active_buffs
                    if buff.buff_id == "mornye_outro_recursion_all_dmg_amp"
                ),
                "0.0s",
            )
            marker_buff = next(
                (
                    buff
                    for buff in simulation.state.active_buffs
                    if buff.buff_id == "mornye_interfered_marker_damage_amp"
                ),
                None,
            )
            display_state["Interfered Marker Remaining"] = (
                f"{marker_buff.remaining_duration:.1f}s" if marker_buff is not None else "0.0s"
            )
            display_state["Interfered Marker Active"] = marker_buff is not None
            with st.expander("Mornye State"):
                st.dataframe(
                    pd.DataFrame(display_state.items(), columns=["Field", "Value"]),
                    use_container_width=True,
                    hide_index=True,
                )
                if display_state.get("Interfered Marker Mode") == "simplified_on_inversion":
                    st.warning(
                        "Mornye Interfered Marker is running in simplified optional mode. "
                        "It applies an enemy DMG Taken amp on Heavy Inversion; full Tune conversion is not implemented."
                    )
            with st.expander("Mornye Echo / Off-Tune"):
                off_tune_cols = st.columns(4)
                off_tune_cols[0].metric(
                    "Base Off-Tune",
                    f"{summary.base_off_tune_buildup_rate * 100:.0f}% / {summary.base_off_tune_buildup_rate:.1f}",
                )
                off_tune_cols[1].metric(
                    "Syntony Bonus",
                    f"+{summary.syntony_field_off_tune_bonus_value * 100:.0f}%"
                    if summary.syntony_field_off_tune_bonus_active
                    else "+0%",
                )
                off_tune_cols[2].metric("C2 Bonus", "+20%" if summary.c2_off_tune_bonus_active else "+0%")
                off_tune_cols[3].metric("Current Off-Tune", f"{summary.current_off_tune_buildup_rate:.1f}")
                halo_cols = st.columns(4)
                halo_cols[0].metric("Halo 5-set", "Enabled" if summary.mornye_halo_of_starry_radiance_5set_enabled else "Disabled")
                halo_cols[1].metric("Team heal events", summary.team_heal_event_count)
                halo_cols[2].metric("Halo triggers", summary.mornye_halo_of_starry_radiance_5set_trigger_count)
                halo_cols[3].metric(
                    "Party ATK% buff",
                    f"{summary.mornye_halo_of_starry_radiance_5set_atk_percent_bonus * 100:.1f}%",
                )
                st.write(
                    {
                        "Formula": "min(current_off_tune_buildup_rate * 0.20, 0.25)",
                        "Heal event mode": summary.mornye_heal_event_mode,
                        "Heal event mode source": summary.mornye_heal_event_mode_source,
                        "Team heal proxy": (
                            "simplified Syntony Field uptime"
                            if summary.mornye_heal_event_mode == "simplified_syntony_field_uptime"
                            else summary.mornye_heal_event_mode
                        ),
                        "Syntony Field uptime maintains Halo proxy": summary.mornye_heal_event_mode
                        == "simplified_syntony_field_uptime",
                        "Halo expected during maintained Syntony uptime": summary.mornye_heal_event_mode
                        == "simplified_syntony_field_uptime",
                        "Mornye constellation": summary.mornye_constellation,
                        "Halo uptime seconds": summary.mornye_halo_of_starry_radiance_5set_uptime_seconds,
                        "Unavailable reason": summary.halo_of_starry_radiance_5set_unavailable_reason,
                        "Energy Regen is Off-Tune": False,
                        "2-set Healing Bonus": "metadata only for DPS",
                        "ATK% affects": "ATK-scaling party members",
                        "Mornye DEF-scaling damage increased by Halo ATK%": False,
                    }
                )
            with st.expander("Excel Tune Break System"):
                tune_cols = st.columns(4)
                tune_cols[0].metric(
                    "Enemy Off-Tune",
                    f"{summary.enemy_off_tune_current:.1f}/{summary.enemy_off_tune_max:.0f}",
                )
                tune_cols[1].metric("Mistune", "Active" if summary.enemy_mistune_active else "Inactive")
                tune_cols[2].metric(
                    "Tune Break",
                    "Available" if summary.enemy_tune_break_available else "Unavailable",
                )
                tune_cols[3].metric("Cooldown", f"{summary.enemy_tune_break_cooldown_remaining:.1f}s")
                marker_cols = st.columns(4)
                marker_cols[0].metric("Tune Break damage", f"{summary.tune_break_damage_total:.0f}")
                marker_cols[1].metric("Tune Break uses", summary.tune_break_action_used_count)
                marker_cols[2].metric("Interfered amp", f"+{summary.interfered_marker_damage_taken_amp * 100:.0f}%")
                marker_cols[3].metric("Marker remaining", f"{summary.interfered_marker_remaining:.1f}s")
                response_cols = st.columns(4)
                response_cols[0].metric("Response damage", f"{summary.tune_response_damage_total:.0f}")
                response_cols[1].metric("Starburst damage", f"{summary.aemeath_starburst_damage_total:.0f}")
                response_cols[2].metric("Particle Jet damage", f"{summary.mornye_particle_jet_damage_total:.0f}")
                response_cols[3].metric(
                    "Response amp rule",
                    "New marker applies"
                    if summary.response_damage_receives_newly_applied_interfered_marker_amp
                    else "Existing marker"
                    if summary.response_damage_receives_existing_interfered_marker_amp
                    else "No marker amp",
                )
                st.write(
                    {
                        "Available Tune Break actions": summary.tune_break_action_available_ids,
                        "Boss Tune Break cooldown seconds": summary.enemy_tune_break_cooldown_seconds,
                        "Boss Tune Break cooldown source": summary.enemy_tune_break_cooldown_source_ref,
                        "Cooldown source status": summary.enemy_tune_break_cooldown_source_status,
                        "Off-Tune cooldown block count": (
                            summary.off_tune_accumulation_blocked_by_tune_break_cooldown_count
                        ),
                        "Mapped Off-Tune action count": summary.mapped_off_tune_action_count,
                        "Unmapped Off-Tune action ids": summary.unmapped_off_tune_action_ids,
                        "Unresolved damaging Off-Tune action ids": summary.unresolved_off_tune_damaging_action_ids,
                        "Off-Tune mapping completeness": summary.off_tune_mapping_completeness_status,
                        "Off-Tune mapping audit": summary.off_tune_value_mapping_source_report,
                        "Target shifting state": summary.target_tune_shift_state,
                        "Target interfered state": summary.target_interfered_state,
                        "Observation Marker remaining": summary.observation_marker_remaining,
                        "Aemeath Starburst response triggers": summary.aemeath_starburst_trigger_count,
                        "Aemeath Starburst cooldown blocked count": (
                            summary.aemeath_starburst_cooldown_blocked_count
                        ),
                        "Aemeath Starburst cooldown remaining": (
                            summary.aemeath_starburst_response_cooldown_remaining
                        ),
                        "Mornye Particle Jet response triggers": summary.mornye_particle_jet_trigger_count,
                        "Mornye Particle Jet cooldown blocked count": (
                            summary.mornye_particle_jet_cooldown_blocked_count
                        ),
                        "Mornye Particle Jet cooldown remaining": (
                            summary.mornye_particle_jet_response_cooldown_remaining
                        ),
                        "Mornye Particle Jet constellation": summary.mornye_constellation,
                        "Response events": summary.tune_response_events,
                        "Tune Break receives newly applied marker amp": (
                            summary.tune_break_damage_receives_new_interfered_marker_amp
                        ),
                        "Response receives any marker amp": (
                            summary.response_damage_receives_interfered_marker_amp
                        ),
                        "Response receives newly applied marker amp": (
                            summary.response_damage_receives_newly_applied_interfered_marker_amp
                        ),
                        "Response receives existing marker amp": (
                            summary.response_damage_receives_existing_interfered_marker_amp
                        ),
                        "Deprecated new-marker alias": (
                            summary.response_damage_receives_new_interfered_marker_amp
                        ),
                        "Response formula source status": summary.tune_response_damage_formula_source_status,
                        "Response event order source status": summary.tune_response_event_order_source_status,
                        "Unresolved response damages": summary.unresolved_response_damage_events,
                        "Assumptions": summary.simplified_assumptions,
                    }
                )
            with st.expander("Mornye High Syntony Field"):
                high_cols = st.columns(4)
                high_cols[0].metric("Status", "Active" if summary.high_syntony_field_active else "Inactive")
                high_cols[1].metric("Remaining", f"{summary.high_syntony_field_remaining:.1f}s")
                high_cols[2].metric(
                    "DEF Bonus",
                    f"+{summary.high_syntony_field_def_percent_bonus * 100:.0f}%"
                    if summary.high_syntony_field_def_bonus_active
                    else "+0%",
                )
                high_cols[3].metric(
                    "Off-Tune",
                    "+50%" if summary.high_syntony_field_off_tune_inherited else "+0%",
                )
                st.write(
                    {
                        "Heal proxy inherited": summary.high_syntony_field_heal_proxy_active,
                        "Healing multiplier bonus": f"+{summary.high_syntony_field_healing_multiplier_bonus * 100:.0f}% metadata only",
                        "Halo maintained through High Syntony": summary.high_syntony_field_heal_proxy_active
                        and summary.halo_of_starry_radiance_5set_active,
                        "Critical Protocol same-action approximation": summary.high_syntony_field_application_timing,
                        "Exact heal amount modeled": False,
                        "Exact heal tick timing modeled": False,
                    }
                )
        if "aemeath" in simulation.selected_party_character_ids:
            with st.expander("Aemeath Resonance Mode Events"):
                event_cols = st.columns(3)
                event_cols[0].metric("Mode", summary.aemeath_resonance_mode)
                event_cols[1].metric("Fusion Burst events", summary.fusion_burst_event_count)
                event_cols[2].metric("Tune Rupture - Shifting events", summary.tune_rupture_shifting_event_count)
                st.caption(
                    "These are source-backed mechanic event emissions. Fusion Burst and Trail damage remain omitted; "
                    "source-confirmed Tune Rupture Seraphic Duet follow-up damage is reported separately as generated "
                    "mechanic damage."
                )
                st.write("Source:", summary.aemeath_resonance_mode_source)
                st.caption(
                    "Aemeath supports fusion_burst and tune_rupture; party presets or manual overrides select the active mode."
                )
                if summary.mechanic_event_unresolved_reason:
                    st.info(summary.mechanic_event_unresolved_reason)
                if summary.mechanic_event_trigger_action_ids:
                    st.write("Damage trigger actions:", summary.mechanic_event_trigger_action_ids)
                if summary.mechanic_event_transition_trigger_action_ids:
                    st.write("Transition trigger actions:", summary.mechanic_event_transition_trigger_action_ids)
                if summary.mechanic_event_emitted_counts:
                    st.dataframe(
                        pd.DataFrame(
                            sorted(summary.mechanic_event_emitted_counts.items()),
                            columns=["event_tag", "count"],
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )
                if summary.unsupported_aemeath_followup_mechanics:
                    st.warning(
                        "Unimplemented follow-up mechanics: "
                        + ", ".join(summary.unsupported_aemeath_followup_mechanics)
                    )
            with st.expander("Aemeath Echo Set - Trailblazing Star"):
                trail_config = (summary.active_echo_sets.get("aemeath") or {}).get("trailblazing_star") or {}
                echo_cols = st.columns(4)
                echo_cols[0].metric("5-set enabled", "Yes" if summary.aemeath_trailblazing_star_5set_enabled else "No")
                echo_cols[1].metric("Trigger count", summary.aemeath_trailblazing_star_5set_trigger_count)
                echo_cols[2].metric("Uptime", f"{summary.aemeath_trailblazing_star_5set_uptime_seconds:.2f}s")
                echo_cols[3].metric(
                    "Active now",
                    "Yes" if "aemeath_trailblazing_star_5set" in summary.echo_set_active_buffs else "No",
                )
                st.caption(
                    "Trailblazing Star 2-set Fusion DMG is already included statically in the selected build profile. "
                    "The 5-set runtime buff grants +20% Crit Rate and +20% Fusion DMG for 8s from the damage that "
                    "inflicts Fusion Burst or Tune Rupture - Shifting. Current action-level aggregate damage treats "
                    "the whole triggering action as receiving the buff."
                )
                st.write("Trigger events:", summary.aemeath_trailblazing_star_5set_trigger_event_tags)
                st.write("Current resonance mode:", summary.aemeath_resonance_mode)
                can_emit = summary.aemeath_resonance_mode in {"fusion_burst", "tune_rupture"}
                st.write("Simulation can emit trigger events:", can_emit)
                if trail_config:
                    st.write("Profile metadata:", trail_config)
                if summary.aemeath_trailblazing_star_5set_enabled and not can_emit:
                    st.info("Trailblazing Star 5-set is enabled, but the current resonance mode does not emit trigger events.")
                if summary.aemeath_trailblazing_star_5set_enabled and summary.aemeath_trailblazing_star_5set_trigger_count == 0:
                    st.info("No Trailblazing Star trigger occurred in this run.")
                if summary.aemeath_trailblazing_star_5set_buff_windows:
                    st.dataframe(
                        pd.DataFrame(summary.aemeath_trailblazing_star_5set_buff_windows),
                        use_container_width=True,
                        hide_index=True,
                    )
        if len(simulation.selected_party_character_ids) > 1 and simulation.has_placeholder_swap_timing:
            st.warning(
                "Generic swap timing is a placeholder for party-structure testing. "
                "It is not sourced from Excel/client data. Real party DPS requires "
                "QTE/Intro/Outro transition modeling."
            )

    if action_sequence is not None:
        st.subheader("Selected action sequence")
        st.write(" -> ".join(action_sequence))
        if simulation is not None:
            resolved_sequence = [entry.resolved_action_id or entry.action_id for entry in summary.timeline]
            st.subheader("Resolved action sequence")
            st.write(" -> ".join(resolved_sequence))
        st.subheader("Action count breakdown")
        st.dataframe(
            pd.DataFrame(sorted(Counter(action_sequence).items()), columns=["action_id", "count"]),
            use_container_width=True,
            hide_index=True,
        )

    timeline_rows = [entry.model_dump() for entry in summary.timeline]
    timeline_df = pd.DataFrame(timeline_rows)
    generated_damage_summary = build_generated_damage_summary(
        summary.timeline,
        total_damage=summary.total_damage,
    )
    preferred_columns = [
        "action_id",
        "selected_action_id",
        "selected_action_name",
        "resolved_action_id",
        "resolved_action_name",
        "action_name",
        "action_type",
        "damage_bonus_category",
        "damage_element",
        "all_dmg_bonus",
        "category_dmg_bonus",
        "element_dmg_bonus",
        "runtime_element_damage_bonus",
        "echo_set_damage_bonus",
        "effective_damage_bonus",
        "crit_rate_before_buffs",
        "crit_rate_after_buffs",
        "crit_damage_before_buffs",
        "crit_damage_after_buffs",
        "runtime_crit_damage_bonus",
        "starfield_calibrator_party_crit_damage_active",
        "starfield_calibrator_party_crit_damage_bonus",
        "everbright_polestar_all_attribute_bonus_active",
        "everbright_polestar_all_attribute_damage_bonus",
        "runtime_all_attribute_damage_bonus",
        "element_damage_bonus_before_weapon",
        "element_damage_bonus_after_weapon",
        "everbright_polestar_liberation_penetration_active",
        "everbright_polestar_liberation_penetration_remaining",
        "def_ignore_before_weapon",
        "everbright_polestar_def_ignore_bonus",
        "total_def_ignore",
        "def_multiplier_before_weapon",
        "def_multiplier_after_weapon",
        "enemy_res_before_weapon",
        "everbright_polestar_fusion_res_ignore_bonus",
        "enemy_res_after_weapon",
        "res_multiplier_before_weapon",
        "res_multiplier_after_weapon",
        "weapon_effects_enabled",
        "weapon_effect_triggered",
        "weapon_id",
        "weapon_rank",
        "weapon_effect_id",
        "weapon_effect_type",
        "weapon_effect_resource",
        "weapon_effect_source_status",
        "concerto_energy_before_weapon_effect",
        "concerto_energy_restored_by_weapon",
        "concerto_energy_after_weapon_effect",
        "weapon_effect_cooldown_seconds",
        "weapon_effect_cooldown_remaining",
        "weapon_effect_cooldown_blocked",
        "weapon_effect_buff_refreshed",
        "weapon_effect_duration_seconds",
        "scaling_stat",
        "scaling_value",
        "stat_component_source",
        "character_base_atk",
        "weapon_base_atk",
        "base_atk_total",
        "base_attack_total",
        "static_atk_percent",
        "static_flat_atk",
        "runtime_atk_percent_bonus",
        "runtime_atk_flat_bonus",
        "runtime_flat_atk_bonus",
        "base_off_tune_buildup_rate",
        "runtime_off_tune_buildup_rate_bonus",
        "current_off_tune_buildup_rate",
        "syntony_field_off_tune_bonus_active",
        "syntony_field_off_tune_bonus_value",
        "c2_off_tune_bonus_active",
        "off_tune_value",
        "off_tune_value_source_status",
        "off_tune_value_source_ref",
        "off_tune_added",
        "off_tune_accumulation_blocked_by_tune_break_cooldown",
        "enemy_off_tune_current_after",
        "enemy_off_tune_max",
        "enemy_mistune_active",
        "enemy_tune_break_available",
        "enemy_tune_break_cooldown_seconds",
        "enemy_tune_break_cooldown_source_status",
        "enemy_tune_break_cooldown_source_ref",
        "enemy_tune_break_cooldown_remaining",
        "tune_break_action_available_ids",
        "target_tune_shift_state",
        "target_interfered_state",
        "observation_marker_remaining",
        "interfered_marker_remaining",
        "interfered_marker_damage_taken_amp",
        "party_response_scan_triggered",
        "aemeath_starburst_triggered",
        "aemeath_starburst_response_damage",
        "aemeath_starburst_response_cooldown_remaining",
        "mornye_particle_jet_triggered",
        "mornye_particle_jet_response_damage",
        "mornye_particle_jet_response_cooldown_remaining",
        "mornye_particle_jet_multiplier_used",
        "mornye_particle_jet_constellation_variant",
        "tune_response_damage",
        "tune_response_damage_total",
        "response_damage_receives_interfered_marker_amp",
        "response_damage_receives_newly_applied_interfered_marker_amp",
        "response_damage_receives_existing_interfered_marker_amp",
        "response_damage_receives_new_interfered_marker_amp",
        "unresolved_response_damage_events",
        "mornye_constellation",
        "mornye_heal_event_mode",
        "mornye_heal_event_mode_source",
        "team_heal_event_triggered",
        "high_syntony_field_active",
        "high_syntony_field_remaining",
        "high_syntony_field_created_count",
        "high_syntony_field_def_bonus_active",
        "high_syntony_field_def_percent_bonus",
        "high_syntony_field_off_tune_inherited",
        "high_syntony_field_heal_proxy_active",
        "high_syntony_field_healing_multiplier_bonus",
        "critical_protocol_high_syntony_created_before_damage",
        "high_syntony_field_same_action_application",
        "high_syntony_field_application_timing",
        "high_syntony_field_unavailable_reason",
        "halo_atk_buff_does_not_affect_mornye_def_damage",
        "halo_of_starry_radiance_5set_active",
        "halo_of_starry_radiance_5set_atk_percent_bonus",
        "halo_of_starry_radiance_5set_unavailable_reason",
        "static_atk",
        "static_attack",
        "effective_atk",
        "effective_attack",
        "character_base_def",
        "weapon_base_def",
        "base_def_total",
        "static_def_percent",
        "static_flat_def",
        "runtime_def_percent_bonus",
        "runtime_def_flat_bonus",
        "static_def",
        "effective_def",
        "final_def_reference",
        "def_reference_delta",
        "def_reference_delta_percent",
        "character_base_hp",
        "weapon_base_hp",
        "base_hp_total",
        "static_hp_percent",
        "static_flat_hp",
        "runtime_hp_percent_bonus",
        "runtime_hp_flat_bonus",
        "static_hp",
        "effective_hp",
        "final_hp_reference",
        "hp_reference_delta",
        "hp_reference_delta_percent",
        "final_attack_reference",
        "attack_reference_delta",
        "attack_reference_delta_percent",
        "profile_completeness_status",
        "implementation_status",
        "emitted_mechanic_event_tags",
        "mechanic_event_triggered",
        "mechanic_event_trigger_id",
        "mechanic_event_cooldown_blocked",
        "aemeath_resonance_mode",
        "aemeath_resonance_mode_source",
        "mechanic_event_source_status",
        "mechanic_event_unresolved_reason",
        "echo_set_triggered_buff_ids",
        "echo_set_buff_refreshed",
        "aemeath_trailblazing_star_5set_active",
        "aemeath_trailblazing_star_5set_applied_before_triggering_damage",
        "trailblazing_star_5set_same_action_application",
        "trailblazing_star_5set_application_timing",
        "raw_skill_category",
        "raw_damage_type",
        "actor_character_id",
        "active_character_before",
        "active_character_after",
        "outgoing_character_id",
        "incoming_character_id",
        "transition_type",
        "transition_reason",
        "outgoing_concerto_before",
        "outgoing_concerto_ready",
        "outgoing_concerto_consumed",
        "outgoing_concerto_after",
        "incoming_qte_candidate_id",
        "incoming_qte_mode",
        "incoming_qte_applied",
        "incoming_qte_damage_bonus_category",
        "incoming_qte_trigger_classification",
        "incoming_qte_source_damage_label",
        "incoming_qte_previous_outro_trigger_frame",
        "incoming_qte_flow_light_metadata_present",
        "incoming_qte_flow_light_applied",
        "incoming_intro_candidate_id",
        "incoming_intro_mode",
        "incoming_intro_applied",
        "incoming_intro_damage_bonus_category",
        "incoming_intro_trigger_classification",
        "incoming_intro_source_damage_label",
        "outgoing_outro_applied",
        "outgoing_outro_event_id",
        "incoming_intro_event_id",
        "fallback_swap_used",
        "swap_timing_is_placeholder",
        "swap_timing_source",
        "transition_events",
        "transition_event_details",
        "transition_warnings",
        "time_start",
        "time_end",
        "action_time",
        "combat_time_start",
        "combat_time_end",
        "combat_time_cost",
        "effective_combat_time_cost",
        "combat_time_cost_source",
        "has_global_time_stop",
        "global_time_stop_frames",
        "time_dilation_type",
        "truncated_by_combat_limit",
        "damage_before_cutoff",
        "damage_after_cutoff_excluded",
        "hit_count",
        "normal_damage",
        "tune_break_damage",
        "generated_mechanic_damage",
        "generated_mechanic_hit_count",
        "aemeath_forte_generated_damage",
        "aemeath_seraphic_duet_followup_triggered",
        "aemeath_seraphic_duet_followup_variant",
        "aemeath_seraphic_duet_followup_repeat_count",
        "aemeath_seraphic_duet_followup_multiplier",
        "aemeath_seraphic_duet_followup_damage",
        "anomaly_tick_damage",
        "total_action_damage",
        "active_anomalies_after",
        "active_buffs",
        "applied_buffs",
        "base_resonance_energy_gain",
        "energy_regen",
        "final_resonance_energy_gain",
        "resonance_energy_gained",
        "resonance_energy_wasted",
        "concerto_gain",
        "base_concerto_gain",
        "passive_concerto_gain",
        "final_concerto_gain",
        "passive_concerto_source",
        "relative_momentum_gain",
        "relative_momentum_gain_source_rows",
        "distributed_array_base_concerto_gain",
        "distributed_array_relative_momentum_gain_per_hit",
        "distributed_array_relative_momentum_gain_total",
        "source_sheet",
        "source_rows",
        "source_status",
        "mornye_er_excess_percent",
        "mornye_liberation_crit_rate_bonus",
        "mornye_liberation_crit_dmg_bonus",
        "mornye_interfered_marker_mode",
        "mornye_interfered_amp",
        "mornye_interfered_marker_applied",
        "mornye_expectation_error_mode",
        "base_policy_action_id",
        "optimal_solution_triggered",
        "optimal_solution_trigger_reason",
        "optimal_solution_candidate_id",
        "gp_success_modeled",
        "implementation_status",
        "total_damage_after",
        "active_character",
        "mornye_mode_after",
        "mornye_rest_mass_after",
        "mornye_wfo_remaining_after",
        "mornye_syntony_field_remaining_after",
        "mornye_high_syntony_field_remaining_after",
        "mechanic_debug_after",
    ]
    visible_columns = []
    for column in preferred_columns:
        if column in timeline_df.columns and column not in visible_columns:
            visible_columns.append(column)

    st.subheader("Timeline")
    st.dataframe(timeline_df[visible_columns] if visible_columns else timeline_df, use_container_width=True, hide_index=True)
    if not timeline_df.empty and "incoming_qte_mode" in timeline_df.columns:
        qte_modes = {
            mode for mode in timeline_df["incoming_qte_mode"].dropna().astype(str).tolist()
            if mode in {"disabled", "dry_run"}
        }
        if qte_modes:
            st.info("QTE candidates in disabled or dry_run mode are logged only and are not included in DPS.")
        if "enabled" in set(timeline_df["incoming_qte_mode"].dropna().astype(str).tolist()):
            st.warning(
                "QTE enabled mode is experimental and uses reviewed candidate data. "
                "Flow Light and E1-QTE follow-up are not implemented."
            )
    if not timeline_df.empty and "incoming_intro_applied" in timeline_df.columns:
        if bool(timeline_df["incoming_intro_applied"].fillna(False).any()):
            st.warning(
                "Mornye Intro enabled mode is experimental. It applies Convergence damage/time "
                "and v1 WFO/Syntony effects, but Tune/Marker/Healing/DEF systems are not implemented."
            )

    if not timeline_df.empty and {"selected_action_id", "resolved_action_id"}.issubset(timeline_df.columns):
        st.subheader("Selected -> Resolved Actions")
        st.dataframe(
            timeline_df[["selected_action_id", "resolved_action_id", "total_action_damage"]],
            use_container_width=True,
            hide_index=True,
        )

    if not timeline_df.empty:
        st.subheader("Generated Mechanic Damage")
        st.caption(
            "Generated mechanic damage is attached to its source action for timing, but it is separated here from "
            "policy-selectable direct action damage. Source-confirmed Aemeath Forte follow-up damage uses "
            "tune_response and is not basic attack damage."
        )
        generated_cols = st.columns(4)
        generated_cols[0].metric(
            "Generated total",
            f"{generated_damage_summary['generated_mechanic_damage_total']:,.0f}",
            f"{generated_damage_summary['generated_mechanic_damage_share_of_total'] * 100:.1f}%",
        )
        generated_cols[1].metric(
            "Aemeath Forte",
            f"{generated_damage_summary['aemeath_forte_generated_damage_total']:,.0f}",
            f"{generated_damage_summary['aemeath_forte_generated_damage_share_of_total'] * 100:.1f}%",
        )
        generated_cols[2].metric(
            "Seraphic Duet follow-up",
            f"{generated_damage_summary['aemeath_seraphic_duet_followup_damage_total']:,.0f}",
            f"{generated_damage_summary['aemeath_seraphic_duet_followup_damage_share_of_total'] * 100:.1f}%",
        )
        generated_cols[3].metric(
            "Follow-up hits",
            generated_damage_summary.get("aemeath_seraphic_duet_followup_total_repeat_count", 0),
        )
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "variant": "normal",
                        "count": generated_damage_summary["aemeath_seraphic_duet_followup_normal_count"],
                        "damage": generated_damage_summary[
                            "aemeath_seraphic_duet_followup_normal_damage_total"
                        ],
                    },
                    {
                        "variant": "enhanced",
                        "count": generated_damage_summary["aemeath_seraphic_duet_followup_enhanced_count"],
                        "damage": generated_damage_summary[
                            "aemeath_seraphic_duet_followup_enhanced_damage_total"
                        ],
                    },
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.write(
            {
                "source_multipliers": generated_damage_summary[
                    "aemeath_seraphic_duet_followup_source_multipliers"
                ],
                "average_followup_damage": generated_damage_summary[
                    "aemeath_seraphic_duet_followup_average_damage"
                ],
                "average_damage_per_hit": generated_damage_summary.get(
                    "aemeath_seraphic_duet_followup_average_damage_per_hit", 0.0
                ),
                "interfered_amp_damage_events": generated_damage_summary[
                    "aemeath_forte_interfered_amp_damage_events"
                ],
                "interfered_amp_damage_total": generated_damage_summary[
                    "aemeath_forte_interfered_amp_damage_total"
                ],
                "interfered_amp_applied_count": generated_damage_summary[
                    "aemeath_forte_interfered_amp_applied_count"
                ],
                "interfered_amp_missing_count": generated_damage_summary[
                    "aemeath_forte_interfered_amp_missing_count"
                ],
            }
        )
        st.caption(generated_damage_summary["aemeath_seraphic_duet_followup_source_multiplier_note"])
        st.caption(generated_damage_summary["aemeath_forte_interfered_amp_note"])

        st.subheader("Damage Category Breakdown")
        st.caption(
            "Selected policy action is the high-level action chosen by the player/PPO. "
            "Resolved action is the internal action after character mechanics. "
            "Legacy source action category tables group total action damage by the source action and include "
            "attached generated mechanic damage for compatibility."
        )
        st.warning(
            "Legacy source action category includes attached generated damage. Generated mechanic damage attached "
            "to Seraphic Duet should not be interpreted as direct action damage."
        )
        breakdown_cols = st.columns(3)
        if {"selected_action_id", "total_action_damage"}.issubset(timeline_df.columns):
            selected_damage = timeline_df.groupby("selected_action_id", as_index=False)["total_action_damage"].sum()
            with breakdown_cols[0]:
                st.write("Selected policy action")
                st.dataframe(selected_damage, use_container_width=True, hide_index=True)
        if {"resolved_action_id", "total_action_damage"}.issubset(timeline_df.columns):
            resolved_damage = timeline_df.groupby("resolved_action_id", as_index=False)["total_action_damage"].sum()
            with breakdown_cols[1]:
                st.write("Resolved action")
                st.dataframe(resolved_damage, use_container_width=True, hide_index=True)
        legacy_source_damage = pd.DataFrame(
            sorted(generated_damage_summary["legacy_damage_by_source_action_category"].items()),
            columns=["source_action_category", "total_action_damage"],
        )
        with breakdown_cols[2]:
            st.write("Legacy source action category, includes attached generated damage")
            st.dataframe(legacy_source_damage, use_container_width=True, hide_index=True)
        if not legacy_source_damage.empty:
            fig = px.bar(
                legacy_source_damage,
                x="source_action_category",
                y="total_action_damage",
                text_auto=".2s",
            )
            fig.update_layout(
                xaxis_title="Legacy source action category, includes attached generated damage",
                yaxis_title="Total damage",
            )
            st.plotly_chart(fig, use_container_width=True)
        direct_breakdown_cols = st.columns(2)
        with direct_breakdown_cols[0]:
            st.write("Direct damage by category, generated damage excluded")
            st.dataframe(
                pd.DataFrame(
                    sorted(generated_damage_summary["direct_damage_by_category"].items()),
                    columns=["category", "direct_damage"],
                ),
                use_container_width=True,
                hide_index=True,
            )
        with direct_breakdown_cols[1]:
            st.write("Effective damage role breakdown")
            st.dataframe(
                pd.DataFrame(
                    sorted(generated_damage_summary["effective_damage_role_breakdown"].items()),
                    columns=["role", "damage"],
                ),
                use_container_width=True,
                hide_index=True,
            )
        generated_breakdown_cols = st.columns(3)
        with generated_breakdown_cols[0]:
            st.write("Hit formula type")
            st.dataframe(
                pd.DataFrame(
                    sorted(generated_damage_summary["damage_by_hit_formula_type"].items()),
                    columns=["formula_type", "damage"],
                ),
                use_container_width=True,
                hide_index=True,
            )
        with generated_breakdown_cols[1]:
            st.write("Generated mechanic source")
            st.dataframe(
                pd.DataFrame(
                    sorted(generated_damage_summary["damage_by_generated_mechanic_source"].items()),
                    columns=["source", "damage"],
                ),
                use_container_width=True,
                hide_index=True,
            )
        with generated_breakdown_cols[2]:
            st.write("Character and source")
            st.dataframe(
                pd.DataFrame(
                    sorted(generated_damage_summary["damage_by_character_and_source"].items()),
                    columns=["character_source", "damage"],
                ),
                use_container_width=True,
                hide_index=True,
            )

    chart_col, resource_col = st.columns([2, 1])

    with chart_col:
        st.subheader("Damage breakdown by resolved action")
        if not timeline_df.empty:
            category_columns = ["normal_damage", "tune_break_damage", "generated_mechanic_damage", "anomaly_tick_damage"]
            damage_df = timeline_df[["action_name", *category_columns]].melt(
                id_vars="action_name",
                var_name="damage_type",
                value_name="damage",
            )
            damage_df = damage_df[damage_df["damage"] > 0.0]
            if not damage_df.empty:
                fig = px.bar(damage_df, x="action_name", y="damage", color="damage_type", text_auto=".2s")
                fig.update_layout(xaxis_title="", yaxis_title="Expected damage")
                st.plotly_chart(fig, use_container_width=True)
            if {"selected_action_id", "total_action_damage"}.issubset(timeline_df.columns):
                selected_damage = timeline_df.groupby("selected_action_id", as_index=False)["total_action_damage"].sum()
                if not selected_damage.empty:
                    st.subheader("Total damage by selected policy action")
                    fig = px.bar(selected_damage, x="selected_action_id", y="total_action_damage", text_auto=".2s")
                    fig.update_layout(xaxis_title="", yaxis_title="Total damage")
                    st.plotly_chart(fig, use_container_width=True)
            if {"resolved_action_id", "total_action_damage"}.issubset(timeline_df.columns):
                resolved_damage = timeline_df.groupby("resolved_action_id", as_index=False)["total_action_damage"].sum()
                if not resolved_damage.empty:
                    st.subheader("Total damage by resolved action")
                    fig = px.bar(resolved_damage, x="resolved_action_id", y="total_action_damage", text_auto=".2s")
                    fig.update_layout(xaxis_title="", yaxis_title="Total damage")
                    st.plotly_chart(fig, use_container_width=True)

    with resource_col:
        st.subheader("Resources")
        st.dataframe(
            pd.DataFrame(summary.resources).T.reset_index(names="character_id"),
            use_container_width=True,
            hide_index=True,
        )

    if simulation is not None:
        with st.expander("Character Mechanics Debug"):
            st.json(
                {
                    "character_mechanics_state": simulation.state.character_mechanics_state,
                    "mechanics": {
                        character_id: mechanic.get_debug_state(simulation.state)
                        for character_id, mechanic in simulation.character_mechanics.items()
                    },
                }
            )


st.set_page_config(page_title="Wuwa DPS RL Simulator Prototype", layout="wide")
st.title("Wuwa DPS RL Simulator Prototype")
mode = st.sidebar.radio("Mode", ["Demo Sequence", "PPO Model", "Character Mechanics"])

if mode == "Character Mechanics":
    mechanics_options = {"aemeath": "Aemeath", "mornye": "Mornye"}
    character_id = st.selectbox(
        "Character",
        options=list(mechanics_options),
        format_func=lambda item: mechanics_options[item],
    )
    render_mechanics_reference(character_id)
else:
    settings = enemy_settings()
    selected_character_ids, party_preset_config, party_id = party_selection()
    build_profile_overrides = build_profile_controls(selected_character_ids, party_preset_config)
    transition_mode_choice = st.sidebar.selectbox(
        "Transition Mode",
        options=["Use Party Preset / Default", "disabled", "dry_run", "enabled"],
        index=0,
    )
    ui_transition_overrides = (
        None
        if transition_mode_choice == "Use Party Preset / Default"
        else build_transition_mode_overrides(transition_mode=transition_mode_choice)
    )
    if "aemeath" in selected_character_ids:
        aemeath_resonance_mode_choice = st.sidebar.selectbox(
            "Aemeath Resonance Mode",
            options=["Use Party Preset / Default", "unresolved", "fusion_burst", "tune_rupture"],
            index=0,
        )
        aemeath_mechanics_overrides = (
            None
            if aemeath_resonance_mode_choice == "Use Party Preset / Default"
            else build_aemeath_resonance_mode_override(aemeath_resonance_mode_choice, source="ui_override")
        )
    else:
        aemeath_resonance_mode_choice = "Use Party Preset / Default"
        aemeath_mechanics_overrides = None
    if "mornye" in selected_character_ids:
        mornye_expectation_error_choice = st.sidebar.selectbox(
            "Mornye Expectation Error Mode",
            options=[
                "Use Party Preset / Default",
                "expectation_error_only",
                "dry_run_success_candidate",
                "always_success",
            ],
            index=0,
        )
        ui_mechanics_overrides = (
            None
            if mornye_expectation_error_choice == "Use Party Preset / Default"
            else build_mornye_expectation_error_mode_override(mornye_expectation_error_choice)
        )
        mornye_heal_event_choice = st.sidebar.selectbox(
            "Mornye Heal Event Mode",
            options=[
                "Use Party Preset / Default",
                "disabled",
                "field_creation_only",
                "simplified_syntony_field_uptime",
            ],
            index=0,
        )
        mornye_heal_event_overrides = (
            None
            if mornye_heal_event_choice == "Use Party Preset / Default"
            else build_mornye_heal_event_mode_override(mornye_heal_event_choice, source="ui_override")
        )
    else:
        mornye_expectation_error_choice = "Use Party Preset / Default"
        ui_mechanics_overrides = None
        mornye_heal_event_choice = "Use Party Preset / Default"
        mornye_heal_event_overrides = None
    ui_overrides = merge_override_blocks(
        ui_transition_overrides,
        aemeath_mechanics_overrides,
        ui_mechanics_overrides,
        mornye_heal_event_overrides,
    )
    effective_transition_config = build_effective_transition_config(
        load_transition_config(DATA_DIR),
        party_preset_config,
        ui_overrides=ui_overrides or None,
    )
    mode_summary = transition_mode_summary(effective_transition_config)
    mechanic_summary = mechanics_mode_summary(effective_transition_config)
    st.sidebar.caption(
        "Effective transition modes: "
        f"Aemeath QTE={mode_summary['aemeath']['intro_qte']}, "
        f"Mornye Intro={mode_summary['mornye']['intro_qte']}, "
        f"Mornye Outro={'enabled' if mode_summary['mornye']['outro'] else 'disabled'}"
    )
    if "aemeath" in selected_character_ids:
        st.sidebar.caption(
            "Aemeath Resonance Mode: "
            f"{mechanic_summary['aemeath']['aemeath_resonance_mode']} "
            f"({mechanic_summary['aemeath']['aemeath_resonance_mode_source']})"
        )
    if "mornye" in selected_character_ids:
        effective_mornye_gp_mode = mechanic_summary["mornye"]["expectation_error_mode"]
        st.sidebar.caption(f"Effective Mornye Expectation Error Mode: {effective_mornye_gp_mode}")
        st.sidebar.caption(
            "Mornye Heal Event Mode: "
            f"{mechanic_summary['mornye']['heal_event_mode']} "
            f"({mechanic_summary['mornye']['heal_event_mode_source']})"
        )
        if effective_mornye_gp_mode == "always_success":
            st.sidebar.warning(
                "Mornye Optimal Solution is being forced by simplified always-success GP modeling. "
                "This is optimistic and not a full game-client implementation."
            )
    if transition_mode_choice == "enabled":
        st.sidebar.warning(
            "Transition enabled mode uses reviewed QTE/Intro candidate data. "
            "Some systems such as Flow Light, E1-QTE follow-up, Tune/Marker/Healing/DEF are not implemented."
        )
    with st.expander("Active Anomaly System"):
        st.write("Actions apply anomaly stacks to enemy-wide combat state. Aero/Spectro/Electro deal tick damage during later action durations. Havoc Bane deals no direct damage and contributes defense reduction while active. Current durations and tick intervals are simplified assumptions.")
    with st.expander("Hit Timing Model"):
        st.write("action_time is internal action lock and hit timing progression. combat_time_cost is the timed-combat timer cost; it defaults to action_time when omitted. Buffs and Havoc Bane are evaluated at each hit time. Animation-only duration and a general cancel system are not modeled.")

if mode == "Demo Sequence":
    preview_sim = Simulation.from_json(
        DATA_DIR,
        selected_character_ids=None if party_id else selected_character_ids,
        party=party_id,
        transition_config=effective_transition_config,
        build_profile_overrides=build_profile_overrides,
    )
    policy_action_ids = preview_sim.get_policy_action_ids()
    valid_policy_action_ids = preview_sim.valid_action_ids()
    default_sequence = [action_id for action_id in valid_policy_action_ids if action_id != "short_wait"][:3] or valid_policy_action_ids
    sequence = st.multiselect(
        "Action sequence",
        options=policy_action_ids,
        default=default_sequence,
    )
    if not sequence:
        sequence = ["short_wait"] if "short_wait" in policy_action_ids else policy_action_ids[:1]
    sim = run_repeating_sequence(
        sequence,
        settings,
        selected_character_ids,
        transition_config=effective_transition_config,
        party_id=party_id,
        build_profile_overrides=build_profile_overrides,
    )
    render_simulation(sim.summary(), simulation=sim)
elif mode == "PPO Model":
    model_path_text = st.text_input("PPO model path", value=str(DEFAULT_PPO_MODEL_PATH))
    model_path = Path(model_path_text)
    if not model_path.exists():
        st.info("No trained PPO model found. Run training first: python rl/train_maskable_ppo.py --timesteps 50000")
    else:
        metadata_path = Path(__file__).parent / "results" / "training_metadata.json"
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            current_sim = Simulation.from_json(
                DATA_DIR,
                selected_character_ids=None if party_id else selected_character_ids,
                party=party_id,
                transition_config=effective_transition_config,
                build_profile_overrides=build_profile_overrides,
            )
            if (
                metadata.get("active_build_profiles") != current_sim.active_build_profiles
                or metadata.get("effective_build_stats_summary") != current_sim.effective_build_stats_summary
            ):
                st.warning(
                    "Selected build profiles or effective stat components differ from training metadata. "
                    "Retrain before comparing PPO results across build assumptions."
                )
                with st.expander("Build profile metadata mismatch"):
                    st.write(
                        {
                            "model_profiles": metadata.get("active_build_profiles"),
                            "current_profiles": current_sim.active_build_profiles,
                            "model_effective_stats": metadata.get("effective_build_stats_summary"),
                            "current_effective_stats": current_sim.effective_build_stats_summary,
                        }
                    )
            observation_mismatch = {
                key: {"model": metadata.get(key), "current": value}
                for key, value in {
                    "observation_shape": simulation_observation_shape(current_sim),
                    "observation_version": OBSERVATION_VERSION,
                }.items()
                if metadata.get(key) != value
            }
            if observation_mismatch:
                st.warning(
                    "PPO observation metadata differs from the current simulator. "
                    "Retrain before evaluating this model with the current observation vector."
                )
                with st.expander("Observation metadata mismatch"):
                    st.write(observation_mismatch)
        try:
            ppo_summary, ppo_actions, ppo_simulation = evaluate_ppo_model(
                model_path,
                settings,
                selected_character_ids,
                transition_config=effective_transition_config,
                party_id=party_id,
                build_profile_overrides=build_profile_overrides,
            )
            render_simulation(ppo_summary, action_sequence=ppo_actions, simulation=ppo_simulation)
        except RuntimeError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Could not evaluate PPO model. Retrain after formula/data changes if needed. Details: {exc}")
