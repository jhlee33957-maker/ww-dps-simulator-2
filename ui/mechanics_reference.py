from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MECHANICS_DIR = PROJECT_ROOT / "data" / "mechanics"


def load_mechanics_data(character_id: str) -> dict[str, Any]:
    path = MECHANICS_DIR / f"{character_id}_mechanics.json"
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def _mechanics_path(character_id: str) -> Path:
    return MECHANICS_DIR / f"{character_id}_mechanics.json"


def _flatten_rows(rows: list[Any]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for item in rows:
        if isinstance(item, dict):
            flattened.append(
                {
                    key: "\n".join(str(value_item) for value_item in value)
                    if isinstance(value, list)
                    else value
                    for key, value in item.items()
                }
            )
        else:
            flattened.append({"item": item})
    return flattened


def render_table(title: str, rows: list[Any]) -> None:
    import pandas as pd
    import streamlit as st

    st.subheader(title)
    if not rows:
        st.caption("No entries.")
        return
    st.dataframe(pd.DataFrame(_flatten_rows(rows)), use_container_width=True, hide_index=True)


def _render_bullets(title: str, rows: list[str]) -> None:
    import streamlit as st

    st.subheader(title)
    for row in rows:
        st.markdown(f"- {row}")


def render_mechanics_reference(character_id: str) -> None:
    import streamlit as st

    path = _mechanics_path(character_id)
    if not path.exists():
        st.warning(f"No mechanics reference file found for `{character_id}` at `{path}`.")
        return

    try:
        data = load_mechanics_data(character_id)
    except (OSError, json.JSONDecodeError) as exc:
        st.error(f"Could not load mechanics reference for `{character_id}`: {exc}")
        return

    st.title("Character Mechanics Reference")
    st.caption(
        "This reference describes the simulator's implemented interpretation for DPS comparison. "
        "It does not change simulation results or PPO training."
    )

    st.header(data.get("display_name", character_id))
    scope = data.get("scope", {})
    st.subheader(scope.get("title", "Scope"))
    included_col, excluded_col = st.columns(2)
    with included_col:
        _render_bullets("Modeled", scope.get("included", []))
    with excluded_col:
        _render_bullets("Omitted / Simplified", scope.get("excluded", []))

    render_table("Resources", data.get("resources", []))
    render_table("States", data.get("states", []))
    render_table("Action Resolution Priority", data.get("action_resolution_priority", []))
    render_table("Timing Model", data.get("timing_model", []))

    section_pairs = [
        ("Form Switch", "form_switch"),
        ("Heavy Attack", "heavy_attack"),
        ("Sync Strike", "sync_strike"),
        ("Seraphic Duet", "seraphic_duet"),
        ("Overdrive / Finale", "overdrive_finale"),
    ]
    for title, key in section_pairs:
        rows = data.get(key, [])
        if rows and all(isinstance(row, str) for row in rows):
            _render_bullets(title, rows)
        else:
            render_table(title, rows)

    render_table("Synchronization Rate Delta Table", data.get("sync_delta_table", []))
    _render_bullets("Known Limitations", data.get("known_limitations", []))
