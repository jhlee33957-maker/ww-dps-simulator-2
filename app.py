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
        "main_basic_attack",
    ],
    "Main DPS focus": [
        "main_resonance_skill",
        "main_basic_attack",
        "main_basic_attack",
        "main_echo_skill",
        "main_resonance_liberation",
        "short_wait",
    ],
}


def run_repeating_sequence(sequence: list[str]) -> Simulation:
    sim = Simulation.from_json(DATA_DIR)
    index = 0

    while sim.state.current_time < sim.combat_duration:
        action_id = sequence[index % len(sequence)]
        if not sim.execute_action(action_id):
            sim.execute_action("short_wait")
        index += 1

    return sim


def evaluate_ppo_model(model_path: Path) -> tuple[Any, list[str]]:
    try:
        from sb3_contrib import MaskablePPO
        from env.wuwa_env import WuwaDpsEnv
    except ModuleNotFoundError as exc:
        raise RuntimeError("Missing RL dependency. Run: pip install -r requirements.txt") from exc

    model = MaskablePPO.load(model_path)
    env = WuwaDpsEnv(DATA_DIR)
    observation, _ = env.reset()
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
            pd.DataFrame(
                sorted(Counter(action_sequence).items()),
                columns=["action_id", "count"],
            ),
            use_container_width=True,
            hide_index=True,
        )

    timeline_rows = [entry.model_dump() for entry in summary.timeline]
    timeline_df = pd.DataFrame(timeline_rows)

    st.subheader("Timeline")
    st.dataframe(timeline_df, use_container_width=True, hide_index=True)

    chart_col, resource_col = st.columns([2, 1])

    with chart_col:
        st.subheader("Damage by action")
        if not timeline_df.empty:
            damage_df = (
                timeline_df.groupby("action_name", as_index=False)["damage"]
                .sum()
                .sort_values("damage", ascending=False)
            )
            fig = px.bar(damage_df, x="action_name", y="damage", text_auto=".2s")
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

mode = st.radio("Mode", ["Demo Sequence", "PPO Model"], horizontal=True)

if mode == "Demo Sequence":
    sequence_name = st.selectbox("Action sequence", list(DEMO_SEQUENCES))
    sim = run_repeating_sequence(DEMO_SEQUENCES[sequence_name])
    render_simulation(sim.summary())
else:
    model_path_text = st.text_input("PPO model path", value=str(DEFAULT_PPO_MODEL_PATH))
    model_path = Path(model_path_text)
    if not model_path.exists():
        st.info("No trained PPO model found. Run training first: python rl/train_maskable_ppo.py --timesteps 50000")
    else:
        try:
            ppo_summary, ppo_actions = evaluate_ppo_model(model_path)
            render_simulation(ppo_summary, action_sequence=ppo_actions)
        except RuntimeError as exc:
            st.error(str(exc))
