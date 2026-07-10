from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from simulator.simulation import Simulation


def first_normal_damage(sim: Simulation, action_id: str) -> float:
    sim.execute_action(action_id)
    return sim.timeline[-1].normal_damage


def main() -> None:
    sim = Simulation.from_json(PROJECT_ROOT / "data", selected_character_ids=["main", "sub", "support"])
    print("Apply aero anomaly:", sim.execute_action("main_aero_erosion"))
    print("After application:", sim.timeline[-1].model_dump())
    sim.execute_action("short_wait")
    print("After short wait:", sim.timeline[-1].model_dump())
    sim.execute_action("main_resonance_skill")
    print("After later action with anomaly ticks:", sim.timeline[-1].model_dump())

    baseline = Simulation.from_json(PROJECT_ROOT / "data", selected_character_ids=["main", "sub", "support"])
    baseline_damage = first_normal_damage(baseline, "main_basic_attack")

    havoc = Simulation.from_json(PROJECT_ROOT / "data", selected_character_ids=["main", "sub", "support"])
    havoc.execute_action("main_havoc_bane")
    boosted_damage = first_normal_damage(havoc, "main_basic_attack")

    print(f"Baseline main basic normal damage: {baseline_damage:.2f}")
    print(f"After Havoc Bane main basic normal damage: {boosted_damage:.2f}")
    print(f"Havoc Bane increased damage: {boosted_damage > baseline_damage}")


if __name__ == "__main__":
    main()
