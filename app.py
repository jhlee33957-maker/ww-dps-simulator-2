from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from simulator.simulation import Simulation


DATA_DIR = Path(__file__).parent / "data"

DEMO_SEQUENCES: dict[str, list[str]] = {
    "Balanced demo": [
        "support_resonance_skill",
        "support_resonance_liberation",
        "swap_to_sub",
        "sub_resonance_skill",
        "sub_echo_skill",
        "swap_to_main",
        "main_resonance_skill",
        "main_basic_attack",
        "main_resonance_liberation",
        "main_echo_skill",
        "short_wait",
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


st.set_page_config(page_title="Wuwa DPS RL Simulator Prototype", layout="wide")
st.title("Wuwa DPS RL Simulator Prototype")

sequence_name = st.selectbox("Action sequence", list(DEMO_SEQUENCES))
sim = run_repeating_sequence(DEMO_SEQUENCES[sequence_name])
summary = sim.summary()

metric_cols = st.columns(4)
metric_cols[0].metric("Total damage", f"{summary.total_damage:,.0f}")
metric_cols[1].metric("DPS", f"{summary.dps:,.0f}")
metric_cols[2].metric("Final combat time", f"{summary.final_time:.2f}s")
metric_cols[3].metric("Active character", summary.active_character)

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
