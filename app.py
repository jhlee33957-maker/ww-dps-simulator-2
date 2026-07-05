from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import json
import pandas as pd
import plotly.express as px
import streamlit as st

from simulator.models import CharacterData
from simulator.build_profiles import (
    effective_build_stats_summary,
    get_available_build_profiles,
    load_build_profiles,
    resolve_character_build_stats,
    resolve_party_build_profiles,
)
from simulator.roster import is_dummy_character, parse_character_ids, read_party_presets
from simulator.simulation import Simulation
from simulator.transition_config import (
    build_effective_transition_config,
    build_mornye_expectation_error_mode_override,
    build_transition_mode_overrides,
    load_transition_config,
    mechanics_mode_summary,
    transition_mode_summary,
)
from ui.mechanics_reference import render_mechanics_reference


DATA_DIR = Path(__file__).parent / "data"
DEFAULT_PPO_MODEL_PATH = Path(__file__).parent / "models" / "maskable_ppo_wuwa.zip"

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
        st.write(effective_build_stats_summary(effective_characters))
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
        with st.expander("Effective Build Profiles"):
            st.write(simulation.active_build_profiles)
            st.write(simulation.effective_build_stats_summary)
        with st.expander("Active Team Buffs"):
            st.write([buff.model_dump() for buff in simulation.state.active_buffs])
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
        "effective_damage_bonus",
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
        "mechanic_debug_after",
    ]
    visible_columns = [column for column in preferred_columns if column in timeline_df.columns]

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
        st.subheader("Damage Category Breakdown")
        st.caption(
            "Selected policy action is the high-level action chosen by the player/PPO. "
            "Resolved action is the internal action after character mechanics. "
            "Damage bonus category is the additive DMG Bonus bucket, such as Resonance Liberation DMG Bonus."
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
        if {"damage_bonus_category", "total_action_damage"}.issubset(timeline_df.columns):
            bonus_damage = timeline_df.groupby("damage_bonus_category", as_index=False)["total_action_damage"].sum()
            with breakdown_cols[2]:
                st.write("Damage bonus category")
                st.dataframe(bonus_damage, use_container_width=True, hide_index=True)
            if not bonus_damage.empty:
                fig = px.bar(bonus_damage, x="damage_bonus_category", y="total_action_damage", text_auto=".2s")
                fig.update_layout(xaxis_title="Damage bonus category", yaxis_title="Total damage")
                st.plotly_chart(fig, use_container_width=True)

    chart_col, resource_col = st.columns([2, 1])

    with chart_col:
        st.subheader("Damage breakdown by resolved action")
        if not timeline_df.empty:
            category_columns = ["normal_damage", "tune_break_damage", "anomaly_tick_damage"]
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
    else:
        mornye_expectation_error_choice = "Use Party Preset / Default"
        ui_mechanics_overrides = None
    ui_overrides = {}
    if ui_transition_overrides:
        ui_overrides.update(ui_transition_overrides)
    if ui_mechanics_overrides:
        ui_overrides.update(ui_mechanics_overrides)
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
    if "mornye" in selected_character_ids:
        effective_mornye_gp_mode = mechanic_summary["mornye"]["expectation_error_mode"]
        st.sidebar.caption(f"Effective Mornye Expectation Error Mode: {effective_mornye_gp_mode}")
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
            if metadata.get("active_build_profiles") != current_sim.active_build_profiles:
                st.warning(
                    "Selected build profiles differ from training metadata. "
                    "Retrain before comparing PPO results across build assumptions."
                )
                with st.expander("Build profile metadata mismatch"):
                    st.write({"model": metadata.get("active_build_profiles"), "current": current_sim.active_build_profiles})
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
