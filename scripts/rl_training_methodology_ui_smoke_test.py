from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    app_text = (ROOT / "app.py").read_text(encoding="utf-8")
    ui_path = ROOT / "ui" / "training_methodology.py"
    assert "render_training_methodology" in app_text
    assert '"Training Methodology"' in app_text
    assert ui_path.exists(), "ui/training_methodology.py missing"
    ui_text = ui_path.read_text(encoding="utf-8")
    for phrase in (
        "damage_this_action / 10000.0",
        "curriculum reset is training-only",
        "final evaluation default is none",
        "not a mathematical proof",
        "No character-specific usage reward bonus is applied by default",
        "Character/route-specific curriculum reset modes may exist",
        "Route demonstrations and behavior-cloning warm-starts",
        "valid source-backed action sequences",
        "Balanced demonstrations",
        "BC refresh",
    ):
        assert phrase.lower() in ui_text.lower(), f"UI methodology text missing phrase: {phrase}"
    assert "manual use-Lynae reward bonus" not in ui_text
    print("rl_training_methodology_ui_smoke_test ok")


if __name__ == "__main__":
    main()
