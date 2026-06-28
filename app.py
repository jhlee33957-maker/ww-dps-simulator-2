from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from simulator.simulation import Simulation


DATA_DIR = Path(__file__).parent / "data"
DEFAULT_PPO_MODEL_PATH = Path(__file__).parent / "models" / "maskable_ppo_wuwa.zip"

DEMO_SEQUENCES: dict[str, list[str]] = {
    "Balanced demo": [
        "swap_to_support",
        "support_resonance_skill",
        "support_resonance_liberation",
        "swap_to_sub",
        "sub_resonance_skill",
        "sub_echo_skill",
        "swap_to_main",
        "main_resonance_skill",
        "main_resonance_liberation",
        "main_aero_erosion",
        "main_basic_attack",
    ],
    "Main DPS focus": [
        "main_resonance_skill",
        "main_basic_attack",
        "main_echo_skill",
        "main_resonance_liberation",
        "main_aero_erosion",
        "short_wait",
    ],
}


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


def apply_enemy_settings(sim: Simulation, settings: dict[str, float | int]) -> None:
    sim.set_enemy_context(
        enemy_level=int(settings["enemy_level"]),
        enemy_res=float(settings["enemy_res"]),
        res_pen=float(settings["res_pen"]),
        def_reduction=float(settings["def_reduction"]),
        dmg_taken=float(settings["dmg_taken"]),
        tune_dmg_bonus=float(settings["tune_dmg_bonus"]),
    )


def run_repeating_sequence(sequence: list[str], settings: dict[str, float | int]) -> Simulation:
    sim = Simulation.from_json(DATA_DIR)
    apply_enemy_settings(sim, settings)
    index = 0

    while sim.state.current_time < sim.combat_duration:
        action_id = sequence[index % len(sequence)]
        if not sim.execute_action(action_id):
            sim.execute_action("short_wait")
        index += 1

    return sim


def evaluate_ppo_model(model_path: Path, settings: dict[str, float | int]) -> tuple[Any, list[str]]:
    try:
        from sb3_contrib import MaskablePPO
        from env.wuwa_env import WuwaDpsEnv
    except ModuleNotFoundError as exc:
        raise RuntimeError("Missing RL dependency. Run: pip install -r requirements.txt") from exc

    model = MaskablePPO.load(model_path)
    env = WuwaDpsEnv(DATA_DIR)
    observation, _ = env.reset()
    apply_enemy_settings(env.simulation, settings)
    action_sequence: list[str] = []

    while env.simulation.state.current_time < env.simulation.combat_duration:
        action, _ = model.predict(observation, deterministic=True, action_masks=env.action_masks())
        observation, _reward, terminated, truncated, info = env.step(int(action))
        action_sequence.append(str(info["action_id"]))
        if terminated or truncated:
            break

    return env.simulation.summary(), action_sequence


def render_simulation(summary: Any, action_sequence: list[str] | None = None) -> None:
    metric_cols = st.columns(4)
    metric_cols[0].metric("Total damage", f"{summary.total_damage:,.0f}")
    metric_cols[1].metric("DPS", f"{summary.dps:,.0f}")
    metric_cols[2].metric("Final combat time", f"{summary.final_time:.2f}s")
    metric_cols[3].metric("Active character", summary.active_character)

    if action_sequence is not None:
        st.subheader("Selected action sequence")
        st.write(" -> ".join(action_sequence))
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
        "action_name",
        "time_start",
        "time_end",
        "normal_damage",
        "tune_break_damage",
        "anomaly_tick_damage",
        "total_action_damage",
        "active_anomalies_after",
        "total_damage_after",
        "active_character",
    ]
    visible_columns = [column for column in preferred_columns if column in timeline_df.columns]

    st.subheader("Timeline")
    st.dataframe(timeline_df[visible_columns] if visible_columns else timeline_df, use_container_width=True, hide_index=True)

    chart_col, resource_col = st.columns([2, 1])

    with chart_col:
        st.subheader("Damage breakdown")
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

    with resource_col:
        st.subheader("Resources")
        st.dataframe(
            pd.DataFrame(summary.resources).T.reset_index(names="character_id"),
            use_container_width=True,
            hide_index=True,
        )


st.set_page_config(page_title="Wuwa DPS RL Simulator Prototype", layout="wide")
st.title("Wuwa DPS RL Simulator Prototype")
settings = enemy_settings()
with st.expander("Active Anomaly System"):
    st.write("Actions apply anomaly stacks to enemy-wide combat state. Aero/Spectro/Electro deal tick damage during later action durations. Havoc Bane deals no direct damage and contributes defense reduction while active. Current durations and tick intervals are simplified assumptions.")

mode = st.radio("Mode", ["Demo Sequence", "PPO Model"], horizontal=True)

if mode == "Demo Sequence":
    sequence_name = st.selectbox("Action sequence", list(DEMO_SEQUENCES))
    sim = run_repeating_sequence(DEMO_SEQUENCES[sequence_name], settings)
    render_simulation(sim.summary())
else:
    model_path_text = st.text_input("PPO model path", value=str(DEFAULT_PPO_MODEL_PATH))
    model_path = Path(model_path_text)
    if not model_path.exists():
        st.info("No trained PPO model found. Run training first: python rl/train_maskable_ppo.py --timesteps 50000")
    else:
        try:
            ppo_summary, ppo_actions = evaluate_ppo_model(model_path, settings)
            render_simulation(ppo_summary, action_sequence=ppo_actions)
        except RuntimeError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Could not evaluate PPO model. Retrain after formula/data changes if needed. Details: {exc}")
