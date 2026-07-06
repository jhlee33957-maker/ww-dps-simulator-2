from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui.mechanics_reference import (
    REFERENCE_NOTICE,
    _render_dict_field,
    _render_list_field,
    _flatten_rows,
    iter_reference_sections,
    load_mechanics_data,
    render_section,
    render_structured_list,
)


class _FakeContext:
    def __init__(self, fake: "_FakeStreamlit", label: str) -> None:
        self.fake = fake
        self.label = label

    def __enter__(self) -> "_FakeContext":
        self.fake.context_depth += 1
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.fake.context_depth -= 1


class _FakeStreamlit(types.SimpleNamespace):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[tuple[str, Any]] = []
        self.context_depth = 0

    def _record(self, name: str, value: Any = None) -> None:
        self.calls.append((name, value))

    def subheader(self, value: str) -> None:
        self._record("subheader", value)

    def caption(self, value: str) -> None:
        self._record("caption", value)

    def markdown(self, value: str) -> None:
        self._record("markdown", value)

    def dataframe(self, *args: Any, **kwargs: Any) -> None:
        self._record("dataframe", {"args": args, "kwargs": kwargs})

    def table(self, value: Any) -> None:
        self._record("table", value)

    def json(self, value: Any) -> None:
        self._record("json", value)

    def write(self, value: Any) -> None:
        self._record("write", value)

    def expander(self, label: str, expanded: bool = False) -> _FakeContext:
        self._record("expander", {"label": label, "expanded": expanded})
        return _FakeContext(self, label)


def _install_fake_streamlit() -> _FakeStreamlit:
    fake = _FakeStreamlit()
    sys.modules["streamlit"] = fake
    return fake


def main() -> None:
    assert "simulator implementation reference" in REFERENCE_NOTICE

    expected_optional_keys = {
        "echo_sets",
        "weapons",
        "tune_break",
        "off_tune",
        "response_damage",
        "known_runtime_modes",
        "legacy_modes",
        "implementation_status",
        "simplified_assumptions",
        "source_notes",
    }

    for character_id in ("aemeath", "mornye"):
        path = PROJECT_ROOT / "data" / "mechanics" / f"{character_id}_mechanics.json"
        with path.open("r", encoding="utf-8-sig") as file:
            json.load(file)

        data = load_mechanics_data(character_id)
        sections = iter_reference_sections(data)
        rendered_keys = {key for _title, key, _value in sections}
        assert rendered_keys & expected_optional_keys, f"optional sections not rendered for {character_id}"
        assert "known_limitations" in rendered_keys, f"known_limitations missing from render sections for {character_id}"
        if character_id == "mornye":
            assert "timing_model" in data
            assert ("Timing Model", "timing_model", data["timing_model"]) in sections
        if "qte_intro_outro" in data:
            assert ("QTE / Intro / Outro", "qte_intro_outro", data["qte_intro_outro"]) in sections

    mornye = load_mechanics_data("mornye")
    starfield_text = json.dumps(mornye["weapons"], ensure_ascii=False).lower()
    assert "resonance skill concerto restore" in starfield_text
    assert "party crit dmg on healing" in starfield_text
    assert "already reflected in user-entered profile" in starfield_text
    assert "interfered marker duration support" not in starfield_text

    flattened = _flatten_rows(
        [
            {
                "name": "nested row",
                "items": ["a", "b"],
                "mapping": {"x": 1},
            },
            "plain row",
        ]
    )
    assert flattened[0]["items"] == "a\nb"
    assert flattened[0]["mapping"] == "{\"x\": 1}"
    assert flattened[1]["item"] == "plain row"

    fake = _install_fake_streamlit()
    render_section("String List", ["alpha", "beta"])
    render_structured_list(
        "Dict List",
        [
            {
                "name": "Readable Entry",
                "scalar": "value",
                "items": ["one", "two"],
                "mapping": {"nested": "value"},
            }
        ],
    )
    _render_list_field("nested_list", ["one", {"name": "two", "value": 2}])
    _render_dict_field("nested_dict", {"items": ["a", "b"], "mapping": {"x": 1}})
    render_section("Nested Dict", {"items": ["a", "b"], "mapping": {"x": 1}})
    render_section("Mornye Timing Model", mornye["timing_model"])
    call_names = [name for name, _value in fake.calls]
    assert "expander" in call_names, "list[dict] sections should use structured expanders"
    assert "dataframe" not in call_names, "structured rendering should be preferred over dataframe rendering"
    assert "json" in call_names, "raw JSON should remain available in a debug expander"

    print("Mechanics reference render smoke test passed.")


if __name__ == "__main__":
    main()
