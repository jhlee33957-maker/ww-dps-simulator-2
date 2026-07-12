from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPARISON_PATH = ROOT / "results" / "manual_bc_ppo_comparison_v108.json"


def main() -> None:
    comparison = json.loads(COMPARISON_PATH.read_text(encoding="utf-8"))
    assert comparison["schema_version"] == "manual_bc_ppo_comparison_v108"
    assert comparison["objective"] == "final_120_second_total_damage_only"
    assert comparison["winner"] == "bc_model"
    assert comparison["winner_model"] == "models/maskable_ppo_bc_v105.zip"
    assert comparison["ppo_candidate_classification"] == "valid_but_regressed"
    assert comparison["no_global_optimum_claim"] is True
    assert comparison["no_ppo_improvement_claim"] is True
    results = comparison["results"]
    manual_damage = float(results["manual_baseline"]["total_damage"])
    bc_damage = float(results["bc_model"]["total_damage"])
    ppo_damage = float(results["ppo_100k"]["total_damage"])
    assert abs(max(manual_damage, bc_damage, ppo_damage) - bc_damage) <= 1e-6
    assert ppo_damage < bc_damage
    assert comparison["winner_total_damage"] == bc_damage
    assert results["ppo_100k"]["classification"] == "valid_but_regressed"
    assert results["ppo_100k"]["first_selected_action_divergence"] == {
        "zero_based_step": 4,
        "baseline": "aemeath_resonance_skill",
        "ppo": "swap_to_mornye",
    }
    settings = comparison["deterministic_evaluation_settings"]
    assert settings["initial_active_character"] == "aemeath"
    assert settings["curriculum_reset_mode"] == "none"
    assert settings["deterministic_prediction"] is True
    assert settings["combat_time_limit_seconds"] == 120.0
    assert settings["cpu_threads"] == 1
    print("manual_bc_ppo_comparison_smoke_test ok")


if __name__ == "__main__":
    main()
