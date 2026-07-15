from __future__ import annotations
import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    value = json.loads((root / "results/mcts_v117_calibration_20k_v118/best_damage_progression.json").read_text(encoding="utf-8"))
    expected = [(1000, 2923979.8335301215), (2000, 3184203.7336018938), (3000, 3498929.9226562413),
                (4000, 3764027.8197907014), (5000, 3916158.19797584), (8000, 4123783.6584580713),
                (12000, 4128137.812582737), (20000, 4128137.812582737)]
    assert [(item["simulation"], item["best_damage"]) for item in value["checkpoints"]] == expected
    assert value["final_best_first_found_simulation"] == 11561
    assert value["simulations_without_improvement_after_best"] == 8439
    assert value["plateau_interpretation"] == "calibration_observation_not_optimum_proof" and not value["global_optimum_proven"]
    print("mcts_v117_20k_progression_smoke_test ok plateau=8439 optimum_proof=false")


if __name__ == "__main__": main()
