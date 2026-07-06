from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MECHANICS_DIR = PROJECT_ROOT / "data" / "mechanics"
REFERENCE_NOTICE = "This is a simulator implementation reference, not a full game tooltip reproduction."
REFERENCE_DETAIL = (
    "Runtime behavior is controlled by data/actions, buffs, weapons, party presets, "
    "and mechanics modules."
)

SECTION_PAIRS = [
    ("Resources", "resources"),
    ("States", "states"),
    ("Action Resolution Priority", "action_resolution_priority"),
    ("Timing Model", "timing_model"),
    ("Modes", "modes"),
    ("Actions", "actions"),
    ("Form Switch", "form_switch"),
    ("Heavy Attack", "heavy_attack"),
    ("Sync Strike", "sync_strike"),
    ("Seraphic Duet", "seraphic_duet"),
    ("Overdrive / Finale", "overdrive_finale"),
    ("Echo Set Effects", "echo_sets"),
    ("Weapon Effects", "weapons"),
    ("Tune Break System", "tune_break"),
    ("Off-Tune Level", "off_tune"),
    ("Tune Response Damage", "response_damage"),
    ("Outro", "outro"),
    ("Intro", "intro"),
    ("QTE / Intro / Outro", "qte_intro_outro"),
    ("Syntony Field", "syntony_field"),
    ("Known Runtime Modes", "known_runtime_modes"),
    ("Legacy Modes", "legacy_modes"),
    ("Synchronization Rate Delta Table", "sync_delta_table"),
    ("Aemeath Resonance Mode Mechanic Events", "resonance_mode_mechanic_events"),
    ("Damage Bonus Category / Source Damage Type", "damage_bonus_category_source_damage_type"),
    ("Expectation Error Routing", "expectation_error_routing"),
    ("Energy Regen Scaling", "energy_regen_scaling"),
    ("Interfered Marker", "interfered_marker"),
    ("Build Profile / Damage Type Bonus Notes", "build_profile_damage_type_bonus_notes"),
    ("Simplified Assumptions", "simplified_assumptions"),
    ("Known Limitations", "known_limitations"),
]


def load_mechanics_data(character_id: str) -> dict[str, Any]:
    path = MECHANICS_DIR / f"{character_id}_mechanics.json"
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def _mechanics_path(character_id: str) -> Path:
    return MECHANICS_DIR / f"{character_id}_mechanics.json"


def _format_cell_value(value: Any) -> Any:
    if isinstance(value, list):
        return "\n".join(_format_cell_value(value_item) for value_item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return value


def _flatten_rows(rows: list[Any]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for item in rows:
        if isinstance(item, dict):
            flattened.append(
                {
                    key: _format_cell_value(value)
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


def _label_for_key(key: str) -> str:
    known_labels = {
        "id": "ID",
        "qte": "QTE",
        "dmg": "DMG",
        "def": "DEF",
        "er": "ER",
    }
    parts = key.replace("_", " ").split()
    return " ".join(known_labels.get(part.lower(), part.capitalize()) for part in parts)


def _display_name_for_entry(entry: dict[str, Any]) -> str:
    for key in ("name", "state", "id", "action_id", "selected", "field", "mode", "title"):
        value = entry.get(key)
        if value:
            return str(value)
    return "Entry"


def _render_scalar_field(key: str, value: Any) -> None:
    import streamlit as st

    label = _label_for_key(key)
    st.markdown(f"- **{label}:** {value}")


def _render_list_field(key: str, values: list[Any]) -> None:
    import streamlit as st

    label = _label_for_key(key)
    st.markdown(f"- **{label}:**")
    for value in values:
        if isinstance(value, dict):
            st.markdown(f"  - **{_display_name_for_entry(value)}**")
            for nested_key, nested_value in value.items():
                if nested_key in {"name", "state", "id", "title"}:
                    continue
                if isinstance(nested_value, list):
                    _render_list_field(nested_key, nested_value)
                elif isinstance(nested_value, dict):
                    _render_dict_field(nested_key, nested_value)
                else:
                    st.markdown(f"    - **{_label_for_key(nested_key)}:** {nested_value}")
        else:
            st.markdown(f"  - {value}")


def _render_dict_field(key: str, value: dict[str, Any]) -> None:
    import streamlit as st

    label = _label_for_key(key)
    st.markdown(f"- **{label}:**")
    scalar_rows: list[dict[str, Any]] = []
    for nested_key, nested_value in value.items():
        if isinstance(nested_value, list):
            _render_list_field(nested_key, nested_value)
        elif isinstance(nested_value, dict):
            _render_dict_field(nested_key, nested_value)
        else:
            scalar_rows.append({"Field": _label_for_key(nested_key), "Value": nested_value})

    if scalar_rows:
        st.table(scalar_rows)


def _render_mechanics_card(entry: dict[str, Any], index: int = 0) -> None:
    import streamlit as st

    title = _display_name_for_entry(entry)
    with st.expander(title, expanded=index == 0):
        for key, value in entry.items():
            if key in {"name", "state", "id", "title"}:
                continue
            if isinstance(value, list):
                _render_list_field(key, value)
            elif isinstance(value, dict):
                _render_dict_field(key, value)
            else:
                _render_scalar_field(key, value)


def render_structured_list(title: str, rows: list[Any]) -> None:
    import streamlit as st

    st.subheader(title)
    if not rows:
        st.caption("No entries.")
        return

    if all(isinstance(row, str) for row in rows):
        for row in rows:
            st.markdown(f"- {row}")
        return

    for index, row in enumerate(rows):
        if isinstance(row, dict):
            _render_mechanics_card(row, index=index)
        else:
            st.markdown(f"- {row}")

    with st.expander("Raw JSON", expanded=False):
        st.json(rows)


def iter_reference_sections(data: dict[str, Any]) -> list[tuple[str, str, Any]]:
    sections: list[tuple[str, str, Any]] = []
    seen_keys = {
        "character_id",
        "display_name",
        "implementation_status",
        "scope",
        "source",
        "source_notes",
    }
    for title, key in SECTION_PAIRS:
        seen_keys.add(key)
        value = data.get(key)
        if value:
            sections.append((title, key, value))

    for key, value in data.items():
        if key not in seen_keys and value:
            title = key.replace("_", " ").title()
            sections.append((title, key, value))
    return sections


def _render_mapping(title: str, value: dict[str, Any]) -> None:
    import streamlit as st

    st.subheader(title)
    for key, nested_value in value.items():
        label = _label_for_key(key)
        if isinstance(nested_value, list):
            _render_list_field(key, nested_value)
        elif isinstance(nested_value, dict):
            _render_dict_field(key, nested_value)
        else:
            st.markdown(f"**{label}:** {nested_value}")

    with st.expander("Raw JSON", expanded=False):
        st.json(value)


def render_section(title: str, value: Any) -> None:
    import streamlit as st

    if isinstance(value, list):
        render_structured_list(title, value)
    elif isinstance(value, dict):
        _render_mapping(title, value)
    else:
        st.subheader(title)
        st.write(value)


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
    st.caption(REFERENCE_NOTICE)
    st.caption(REFERENCE_DETAIL)

    st.header(data.get("display_name", character_id))
    scope = data.get("scope", {})
    st.subheader(scope.get("title", "Scope"))
    included_col, excluded_col = st.columns(2)
    with included_col:
        _render_bullets("Modeled", scope.get("included", []))
    with excluded_col:
        _render_bullets("Omitted / Simplified", scope.get("excluded", []))

    top_summary = {
        "Implementation Status": data.get("implementation_status"),
        "Source Notes": data.get("source_notes"),
    }
    if any(top_summary.values()):
        st.subheader("Reference Summary")
        if top_summary["Implementation Status"]:
            st.markdown(f"- **Implementation Status:** {top_summary['Implementation Status']}")
        for note in top_summary.get("Source Notes") or []:
            st.markdown(f"- {note}")

    for title, _key, value in iter_reference_sections(data):
        render_section(title, value)
