from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from characters.aemeath import AemeathMechanic
from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"


def main() -> None:
    sim = Simulation.from_json(DATA_DIR)
    print("Registered mechanics:")
    for character_id, mechanic in sim.character_mechanics.items():
        print(f"- {character_id}: {mechanic.__class__.__name__}")

    print(f"Initial character_mechanics_state: {sim.state.character_mechanics_state}")

    for action_id in ["main_basic_attack", "main_resonance_skill", "swap_to_support", "support_resonance_skill"]:
        if action_id in sim.actions:
            ok = sim.execute_action(action_id)
            print(f"Executed {action_id}: {ok}")

    print(f"Post-action character_mechanics_state: {sim.state.character_mechanics_state}")
    print("Mechanic observation labels and values:")
    for character_id, mechanic in sim.character_mechanics.items():
        print(f"- {character_id} labels: {mechanic.get_observation_labels()}")
        print(f"- {character_id} values: {mechanic.get_observation_values(sim.state)}")
        print(f"- {character_id} debug: {mechanic.get_debug_state(sim.state)}")

    aemeath = AemeathMechanic()
    aemeath.initialize_state(sim.state)
    print(f"Aemeath placeholder labels: {aemeath.get_observation_labels()}")
    print(f"Aemeath placeholder values: {aemeath.get_observation_values(sim.state)}")
    print(f"Aemeath placeholder debug: {aemeath.get_debug_state(sim.state)}")


if __name__ == "__main__":
    main()
