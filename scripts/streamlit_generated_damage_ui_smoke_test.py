from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"


def main() -> None:
    text = APP_PATH.read_text(encoding="utf-8")
    required_phrases = (
        "Effective damage role breakdown",
        "Direct damage by category, generated damage excluded",
        "Generated mechanic damage by source",
        "Debug / legacy source-action category breakdown",
        "This legacy compatibility view groups total action damage by the source action category",
        "Do not use it as the primary damage-role breakdown.",
    )
    for phrase in required_phrases:
        assert phrase in text, f"missing UI phrase: {phrase}"

    damage_breakdown_index = text.index('st.subheader("Damage Breakdown")')
    primary_index = text.index('"Primary: Effective damage role breakdown"')
    direct_index = text.index('"Direct damage by category, generated damage excluded"')
    generated_index = text.index('"Generated mechanic damage by source"')
    expander_index = text.index('with st.expander("Debug / legacy source-action category breakdown")')
    legacy_key_index = text.index('generated_damage_summary["legacy_damage_by_source_action_category"]')
    assert damage_breakdown_index < primary_index < direct_index < generated_index < expander_index < legacy_key_index

    first_plot_after_damage_breakdown = text.index("st.plotly_chart", damage_breakdown_index)
    legacy_plot = text.index("st.plotly_chart", legacy_key_index)
    assert first_plot_after_damage_breakdown < expander_index
    assert legacy_plot > expander_index

    old_visible_title = "Legacy source action category, includes attached generated damage"
    assert old_visible_title not in text
    assert "Resolved action damage composition" in text
    assert "Action usage damage totals" in text
    print("streamlit_generated_damage_ui_smoke_test ok")


if __name__ == "__main__":
    main()
