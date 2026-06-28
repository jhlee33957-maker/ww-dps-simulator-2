from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from simulator.simulation import Simulation
from solver.beam_search import BeamSearchResult, run_beam_search


DATA_DIR = Path(__file__).parent / "data"

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


def render_simulation(summary, action_sequence: list[str] | None = None, explored_nodes: int | None = None) -> None:
    metric_cols = st.columns(4)
    metric_cols[0].metric("Total damage", f"{summary.total_damage:,.0f}")
    metric_cols[1].metric("DPS", f"{summary.dps:,.0f}")
    metric_cols[2].metric("Final combat time", f"{summary.final_time:.2f}s")
    metric_cols[3].metric("Active character", summary.active_character)

    if explored_nodes is not None:
        st.caption(f"Explored nodes: {explored_nodes:,}")

    if action_sequence is not None:
        st.subheader("Selected action sequence")
        st.write(" -> ".join(action_sequence))

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

mode = st.radio("Mode", ["Demo Sequence", "Beam Search"], horizontal=True)

if mode == "Demo Sequence":
    sequence_name = st.selectbox("Action sequence", list(DEMO_SEQUENCES))
    sim = run_repeating_sequence(DEMO_SEQUENCES[sequence_name])
    render_simulation(sim.summary())
else:
    beam_width = st.slider("Beam width", min_value=1, max_value=100, value=20, step=1)
    max_steps = st.slider("Max steps", min_value=1, max_value=200, value=100, step=1)
    result: BeamSearchResult = run_beam_search(
        Simulation.from_json(DATA_DIR),
        beam_width=beam_width,
        max_steps=max_steps,
    )
    render_simulation(
        result.simulation.summary(),
        action_sequence=result.action_sequence,
        explored_nodes=result.explored_nodes,
    )
