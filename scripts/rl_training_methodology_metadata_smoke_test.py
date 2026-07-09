from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    data_path = ROOT / "data" / "rl_training_methodology.json"
    report_path = ROOT / "reports" / "rl_training_methodology.md"
    assert data_path.exists(), "data/rl_training_methodology.json missing"
    assert report_path.exists(), "reports/rl_training_methodology.md missing"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    for key in (
        "reward_formula",
        "algorithm",
        "action_mask_description",
        "curriculum_modes",
        "evaluation_default",
        "stale_model_warning",
    ):
        assert key in data, f"methodology metadata missing {key}"
    report = report_path.read_text(encoding="utf-8")
    for phrase in (
        "MaskablePPO",
        "damage_this_action / 10000.0",
        "Curriculum reset is training-only",
        "final evaluation default is none",
        "Old PPO models before Lynae fixes are stale",
        "No character-specific usage reward bonus is applied by default",
        "Route demonstrations and behavior-cloning warm-starts",
        "Balanced demonstrations",
        "BC refresh",
    ):
        assert phrase.lower() in report.lower(), f"methodology report missing phrase: {phrase}"
    assert data["no_character_specific_usage_reward_bonus"] is True
    assert data["route_demonstration_warm_start"]["reward_shaping"] is False
    assert data["route_demonstration_warm_start"]["character_usage_bonus"] is False
    assert "manual use-Lynae reward bonus" not in report
    print("rl_training_methodology_metadata_smoke_test ok")


if __name__ == "__main__":
    main()
