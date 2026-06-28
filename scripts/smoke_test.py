from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.simulation import Simulation


def main() -> None:
    sim = Simulation.from_json(PROJECT_ROOT / "data")
    print("Valid actions at start:", ", ".join(sim.valid_action_ids()))

    sequence = [
        "swap_to_support",
        "support_resonance_skill",
        "support_resonance_liberation",
        "swap_to_sub",
        "sub_resonance_skill",
        "sub_echo_skill",
        "swap_to_main",
        "main_resonance_skill",
        "main_resonance_liberation",
        "main_aero_erosion",
    ]
    for action_id in sequence:
        if not sim.execute_action(action_id):
            print(f"Skipped invalid action: {action_id}")

    summary = sim.summary()
    print(f"Total damage: {summary.total_damage:.2f}")
    print(f"DPS: {summary.dps:.2f}")
    print(f"Final time: {summary.final_time:.2f}")
    print(f"Active character: {summary.active_character}")
    print("Timeline:")
    for row in summary.timeline:
        print(row.model_dump())


if __name__ == "__main__":
    main()
