from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.simulation import Simulation
from solver.beam_search import run_beam_search


def main() -> None:
    sim = Simulation.from_json(PROJECT_ROOT / "data")
    result = run_beam_search(sim, beam_width=10, max_steps=100)

    print(f"Best total damage: {result.total_damage:.2f}")
    print(f"Best DPS: {result.dps:.2f}")
    print(f"Final time: {result.final_time:.2f}")
    print("Selected action sequence:", ", ".join(result.action_sequence))
    print(f"Explored nodes: {result.explored_nodes}")
    print("First timeline rows:")
    for row in result.timeline[:8]:
        print(row.model_dump())


if __name__ == "__main__":
    main()
