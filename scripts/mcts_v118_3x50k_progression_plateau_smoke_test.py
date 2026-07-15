from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "results/mcts_v118_production_3x50k_v119/production_progression.json").read_text(encoding="utf-8"))
    expected = {"118001": (30820, 19180), "118002": (38749, 11251), "118003": (11285, 38715)}
    for seed, (found, plateau) in expected.items():
        item = payload["seeds"][seed]
        assert item["best_first_found_simulation"] == found
        assert item["simulations_without_improvement_after_best"] == plateau
        assert item["global_optimum_proven"] is False
    milestones = {row["simulation_count"]: row["best_damage"] for row in payload["seeds"]["118003"]["checkpoints"]}
    assert milestones[1000] == 2480805.7609260054 and milestones[12000] == milestones[50000] == 4647724.703247974
    assert payload["plateau_interpretation"] == "stopping_evidence_not_global_optimum_proof"
    print("mcts_v118_3x50k_progression_plateau_smoke_test ok plateaus=19180,11251,38715 optimum_proof=false")


if __name__ == "__main__": main()
